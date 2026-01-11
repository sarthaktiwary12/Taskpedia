"""
Fast generation pipeline for VLA/VLN training data.

Maximizes throughput to saturate API rate limits while mining deep
into task hierarchies to find atomic actions suitable for robot learning.

Key strategies:
- ThreadPoolExecutor for I/O-bound API calls
- Lock-free atomic counters for stats
- Queue-based result processing (no mutex contention)
- Aggressive decomposition (no skipping short names)
"""

from __future__ import annotations

import json
import time
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import threading

from tqdm import tqdm

from taskpedia.hierarchy import NodeType, SeedSource, TaskGraph, TaskNode
from taskpedia.llm import LLMClient, LLMConfig, MockLLMClient


class AtomicCounter:
    """Lock-free atomic counter using Python's GIL guarantee for simple increments."""

    def __init__(self, initial: int = 0):
        self._value = initial

    def increment(self, delta: int = 1) -> int:
        """Increment and return new value. Thread-safe due to GIL."""
        self._value += delta
        return self._value

    @property
    def value(self) -> int:
        return self._value


@dataclass
class FastGenConfig:
    output_dir: Path
    model: str = "models/gemini-2.5-flash"
    max_tasks: int = 100000
    max_workers: int = 64  # High concurrency
    batch_size: int = 500  # Large batches
    rpm_limit: int = 1000  # Gemini Flash limit
    mock: bool = False
    min_depth: int = 0  # Don't skip based on depth
    save_interval: int = 100  # Save every N decompositions


class FastGenerator:
    """
    Fast task generator optimized for VLA/VLN training data.

    Design goals:
    - Saturate 1000 RPM API limit
    - Mine deep into hierarchies for atomic actions
    - No aggressive skipping - all tasks get decomposed
    - Lock-free design to avoid contention
    """

    def __init__(self, config: FastGenConfig):
        self.config = config
        self.graph = TaskGraph(config.output_dir)

        # Lock-free atomic counters
        self._generated = AtomicCounter(0)
        self._decomposed = AtomicCounter(0)
        self._atomic_found = AtomicCounter(0)
        self._errors = AtomicCounter(0)
        self._api_calls = AtomicCounter(0)

        # Queue for results - processed by main thread only (no locks needed)
        self._result_queue: queue.Queue = queue.Queue()

        # Track processed IDs (only accessed by main thread for reading nodes)
        self._processed_ids: set[str] = set()

        # Start time for RPM calculation
        self._start_time = time.time()

        # Load already processed nodes
        self._load_processed()

        # Create LLM client
        llm_config = LLMConfig(model=config.model, thinking_budget=0)  # No thinking for speed
        if config.mock:
            self._client = MockLLMClient(config=llm_config, delay=0.001)
        else:
            self._client = LLMClient(config=llm_config)

    def _load_processed(self):
        """Load IDs of nodes that already have children (already processed)."""
        for node in self.graph.iter_nodes():
            if node.children_ids:  # Has children = already decomposed
                self._processed_ids.add(node.id)
        print(f"[INFO] Loaded {len(self._processed_ids):,} already-processed nodes")

    def _get_rpm(self) -> float:
        """Calculate current RPM."""
        elapsed = time.time() - self._start_time
        if elapsed < 1:
            return 0
        return (self._api_calls.value / elapsed) * 60

    def _decompose_node(self, node: TaskNode) -> dict:
        """Decompose a single node into subtasks. Thread-safe, no locks."""
        # Increment API call counter (atomic)
        self._api_calls.increment()

        system_prompt = """You are an expert at decomposing human tasks into atomic subtasks for robot learning.

GOAL: Break down tasks until you reach ATOMIC actions that a robot can execute directly.

ATOMIC actions are single, indivisible motor primitives like:
- grasp [object]
- release [object]
- move_to [location]
- push/pull [object]
- rotate [object]
- press [button/switch]
- pour [substance]
- insert [object] into [container]

Return JSON:
{
    "is_atomic": true/false,
    "subtasks": [
        {"name": "action name", "description": "what this does", "is_atomic": true/false}
    ]
}

If the task IS atomic, return {"is_atomic": true, "subtasks": []}
Otherwise, decompose into 3-8 subtasks, going as fine-grained as possible."""

        prompt = f"""Decompose this task for robot execution:

Task: {node.name}
{f'Description: {node.description}' if node.description else ''}
{f'Context: {node.parent_id}' if node.parent_id else ''}

Break it down into the smallest possible subtasks."""

        try:
            response = self._client.generate(prompt, system_prompt, use_thinking=False)

            # Parse JSON
            json_text = response.strip()
            if "```" in json_text:
                # Extract from code block
                parts = json_text.split("```")
                for part in parts:
                    if part.strip().startswith("json"):
                        json_text = part.strip()[4:]
                        break
                    elif part.strip().startswith("{"):
                        json_text = part.strip()
                        break

            result = json.loads(json_text.strip())
            return {"node_id": node.id, "node": node, "success": True, **result}

        except json.JSONDecodeError as e:
            self._errors.increment()
            return {
                "node_id": node.id,
                "node": node,
                "success": False,
                "error": f"JSON parse: {str(e)[:50]}",
            }
        except Exception as e:
            self._errors.increment()
            return {"node_id": node.id, "node": node, "success": False, "error": str(e)[:100]}

    def _process_result(self, result: dict) -> int:
        """Process a decomposition result. Called only from main thread - no locks needed."""
        if not result.get("success"):
            return 0

        node_id = result["node_id"]
        node = result["node"]
        is_atomic = result.get("is_atomic", False)
        subtasks = result.get("subtasks", [])

        # Mark as processed
        self._processed_ids.add(node_id)

        # If atomic, mark it and return
        if is_atomic or not subtasks:
            node.node_type = NodeType.ATOMIC
            self.graph.add_node(node, save=False)
            self._atomic_found.increment()
            return 0

        # Add subtasks as children
        count = 0
        for subtask in subtasks:
            name = subtask.get("name", str(subtask))
            if not name:
                continue

            child_type = NodeType.ATOMIC if subtask.get("is_atomic") else NodeType.SUBTASK

            child = TaskNode(
                id=TaskNode.make_id(name, node.id),
                name=name,
                node_type=child_type,
                parent_id=node.id,
                description=subtask.get("description", ""),
                sources=[SeedSource.LLM_GENERATED],
            )
            try:
                self.graph.add_node(child, save=False)
                count += 1
                if child_type == NodeType.ATOMIC:
                    self._atomic_found.increment()
            except ValueError:
                pass  # Duplicate node

        self._decomposed.increment()
        self._generated.increment(count)

        return count

    def _get_decomposable(self, limit: int) -> list[TaskNode]:
        """Get nodes that need decomposition - no aggressive filtering."""
        nodes = []

        for node in self.graph.get_leaves():
            # Skip if already processed
            if node.id in self._processed_ids:
                continue

            # Skip if already has children
            if node.children_ids:
                self._processed_ids.add(node.id)
                continue

            # Skip DOMAIN nodes (top-level categories)
            if node.node_type == NodeType.DOMAIN:
                continue

            # Skip nodes already marked atomic
            if node.node_type == NodeType.ATOMIC:
                continue

            # Include everything else - let LLM decide if atomic
            nodes.append(node)
            if len(nodes) >= limit:
                break

        return nodes

    def run(self) -> dict:
        """Run fast generation with max throughput."""
        initial_count = len(list(self.graph.iter_nodes()))

        print(f"\n{'='*60}")
        print(f"  FAST VLA/VLN Task Mining")
        print(f"{'='*60}")
        print(f"  Output:      {self.config.output_dir}")
        print(f"  Workers:     {self.config.max_workers}")
        print(f"  Batch size:  {self.config.batch_size}")
        print(f"  RPM limit:   {self.config.rpm_limit}")
        print(f"  Mock:        {self.config.mock}")
        print(f"  Initial:     {initial_count:,} nodes")
        print(f"  Processed:   {len(self._processed_ids):,} already done")
        print(f"{'='*60}\n")

        pbar = tqdm(
            total=self.config.max_tasks,
            desc="Mining tasks",
            unit="tasks",
            dynamic_ncols=True,
        )

        save_counter = 0
        self._start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            while self._generated.value < self.config.max_tasks:
                # Get batch of nodes to process
                nodes = self._get_decomposable(self.config.batch_size)

                if not nodes:
                    print("\n[INFO] No more nodes to decompose - hierarchy fully mined!")
                    break

                # Submit all tasks concurrently
                futures = [executor.submit(self._decompose_node, n) for n in nodes]

                # Process results as they complete (main thread only - no locks)
                for future in as_completed(futures):
                    result = future.result()
                    count = self._process_result(result)
                    pbar.update(count)

                    # Update stats display
                    pbar.set_postfix(
                        {
                            "nodes": self._generated.value,
                            "atomic": self._atomic_found.value,
                            "rpm": f"{self._get_rpm():.0f}",
                            "err": self._errors.value,
                        }
                    )

                    save_counter += 1

                # Save periodically
                if save_counter >= self.config.save_interval:
                    self.graph.save_all()
                    save_counter = 0

        pbar.close()

        # Final save
        self.graph.save_all()

        elapsed = time.time() - self._start_time
        final_count = len(list(self.graph.iter_nodes()))

        print(f"\n{'='*60}")
        print(f"  MINING COMPLETE")
        print(f"{'='*60}")
        print(f"  Generated:    {self._generated.value:,} new tasks")
        print(f"  Atomic found: {self._atomic_found.value:,}")
        print(f"  Decomposed:   {self._decomposed.value:,} nodes")
        print(f"  Errors:       {self._errors.value}")
        print(f"  API calls:    {self._api_calls.value:,}")
        print(f"  Time:         {elapsed:.1f}s")
        print(f"  Avg RPM:      {(self._api_calls.value / elapsed) * 60:.0f}")
        print(f"  Total nodes:  {final_count:,} (was {initial_count:,})")
        print(f"{'='*60}")

        return {
            "generated": self._generated.value,
            "decomposed": self._decomposed.value,
            "atomic_found": self._atomic_found.value,
            "errors": self._errors.value,
            "api_calls": self._api_calls.value,
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fast VLA/VLN task mining")
    parser.add_argument("-o", "--output", default="./task_hierarchy", help="Output directory")
    parser.add_argument("--max-tasks", type=int, default=100000, help="Max tasks to generate")
    parser.add_argument("--workers", type=int, default=64, help="Concurrent workers")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size")
    parser.add_argument("--rpm", type=int, default=1000, help="Rate limit (RPM)")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM")
    args = parser.parse_args()

    config = FastGenConfig(
        output_dir=Path(args.output),
        max_tasks=args.max_tasks,
        max_workers=args.workers,
        batch_size=args.batch_size,
        rpm_limit=args.rpm,
        mock=args.mock,
    )

    gen = FastGenerator(config)
    gen.run()


if __name__ == "__main__":
    main()
