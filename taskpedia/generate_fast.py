"""
Fast generation pipeline for VLA/VLN training data.

Continuous flow architecture with Textual TUI for monitoring.
- ThreadPoolExecutor for concurrent API calls
- Main thread processes results
- Atomic file saves only on completion
- Live flow visualization with Textual
"""

from __future__ import annotations

import json
import time
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

from taskpedia.hierarchy import NodeType, SeedSource, TaskGraph, TaskNode
from taskpedia.llm import LLMClient, LLMConfig, MockLLMClient


class AtomicCounter:
    """Thread-safe counter."""

    def __init__(self, initial: int = 0):
        self._value = initial
        self._lock = threading.Lock()

    def increment(self, delta: int = 1) -> int:
        with self._lock:
            self._value += delta
            return self._value

    def set(self, value: int) -> None:
        with self._lock:
            self._value = value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value


@dataclass
class FastGenConfig:
    output_dir: Path
    model: str = "models/gemini-2.5-flash"
    max_tasks: int = 100000
    max_workers: int = 128
    queue_size: int = 1000
    rpm_limit: int = 1000
    mock: bool = False
    save_interval: int = 200
    tui: bool = True


class GeneratorCore:
    """Core generation logic - thread-safe."""

    def __init__(self, config: FastGenConfig):
        self.config = config
        self.graph = TaskGraph(config.output_dir)

        # Stats
        self.generated = AtomicCounter(0)
        self.decomposed = AtomicCounter(0)
        self.atomic_found = AtomicCounter(0)
        self.errors = AtomicCounter(0)
        self.api_calls = AtomicCounter(0)
        self.in_flight = AtomicCounter(0)
        self.work_queued = AtomicCounter(0)

        # Track processed
        self._processed_ids: set[str] = set()
        self._processed_lock = threading.Lock()

        # Pending nodes to save
        self._pending_nodes: list[TaskNode] = []
        self._pending_lock = threading.Lock()

        # Status message
        self.status = "Initializing..."
        self._status_lock = threading.Lock()

        # Control
        self._shutdown = threading.Event()
        self._start_time = time.time()
        self._done = False

        self._load_processed()

        # LLM client
        llm_config = LLMConfig(model=config.model, thinking_budget=0)
        if config.mock:
            self._client = MockLLMClient(config=llm_config, delay=0.05)
        else:
            self._client = LLMClient(config=llm_config)

        self.set_status("Ready")

    def set_status(self, msg: str):
        with self._status_lock:
            self.status = msg

    def get_status(self) -> str:
        with self._status_lock:
            return self.status

    def _load_processed(self):
        count = 0
        for node in self.graph.iter_nodes():
            if node.children_ids:
                self._processed_ids.add(node.id)
                count += 1
        self.set_status(f"Loaded {count:,} processed nodes")

    def get_rpm(self) -> float:
        elapsed = time.time() - self._start_time
        if elapsed < 1:
            return 0
        return (self.api_calls.value / elapsed) * 60

    def get_elapsed(self) -> float:
        return time.time() - self._start_time

    def is_processed(self, node_id: str) -> bool:
        with self._processed_lock:
            return node_id in self._processed_ids

    def mark_processed(self, node_id: str):
        with self._processed_lock:
            self._processed_ids.add(node_id)

    def get_pending_count(self) -> int:
        with self._pending_lock:
            return len(self._pending_nodes)

    def _decompose_node(self, node: TaskNode) -> dict:
        """Decompose a single node. Thread-safe."""
        self.api_calls.increment()
        self.in_flight.increment()

        try:
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

            response = self._client.generate(prompt, system_prompt, use_thinking=False)

            # Parse JSON
            json_text = response.strip()
            if "```" in json_text:
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
            self.errors.increment()
            return {
                "node_id": node.id,
                "node": node,
                "success": False,
                "error": f"JSON: {str(e)[:50]}",
            }
        except Exception as e:
            self.errors.increment()
            return {"node_id": node.id, "node": node, "success": False, "error": str(e)[:100]}
        finally:
            self.in_flight.increment(-1)

    def _process_result(self, result: dict) -> int:
        """Process a decomposition result. Returns count of new nodes."""
        if not result.get("success"):
            return 0

        node_id = result["node_id"]
        node = result["node"]
        is_atomic = result.get("is_atomic", False)
        subtasks = result.get("subtasks", [])

        self.mark_processed(node_id)

        if is_atomic or not subtasks:
            node.node_type = NodeType.ATOMIC
            with self._pending_lock:
                self._pending_nodes.append(node)
            self.atomic_found.increment()
            return 0

        count = 0

        with self._pending_lock:
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
                    self._pending_nodes.append(child)
                    count += 1
                    if child_type == NodeType.ATOMIC:
                        self.atomic_found.increment()
                except ValueError:
                    pass  # Duplicate

        self.decomposed.increment()
        self.generated.increment(count)
        return count

    def save_pending(self):
        """Save all pending nodes to disk."""
        with self._pending_lock:
            if not self._pending_nodes:
                return
            for node in self._pending_nodes:
                self.graph._save_node(node)
            self._pending_nodes.clear()
        self.graph._save_manifest()

    def iter_decomposable(self, limit: int = 500):
        """Yield nodes that need decomposition."""
        count = 0
        for node in self.graph.get_leaves():
            if count >= limit:
                break
            if self.is_processed(node.id):
                continue
            if node.children_ids:
                self.mark_processed(node.id)
                continue
            if node.node_type == NodeType.DOMAIN:
                continue
            if node.node_type == NodeType.ATOMIC:
                continue
            yield node
            count += 1

    def should_stop(self) -> bool:
        return self._shutdown.is_set() or self.generated.value >= self.config.max_tasks

    def stop(self):
        self._shutdown.set()


def run_without_tui(config: FastGenConfig) -> dict:
    """Run generation without TUI - simple progress output."""
    from tqdm import tqdm

    core = GeneratorCore(config)
    initial_count = len(list(core.graph.iter_nodes()))

    print(f"\n{'='*60}")
    print(f"  Task Mining (no TUI)")
    print(f"{'='*60}")
    print(f"  Output:    {config.output_dir}")
    print(f"  Workers:   {config.max_workers}")
    print(f"  Initial:   {initial_count:,} nodes")
    print(f"{'='*60}\n")

    pbar = tqdm(total=config.max_tasks, desc="Mining", unit="tasks")
    save_counter = 0

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        while not core.should_stop():
            nodes = list(core.iter_decomposable(limit=config.queue_size))

            if not nodes:
                core.save_pending()
                nodes = list(core.iter_decomposable(limit=config.queue_size))
                if not nodes:
                    print("\n[INFO] No more nodes to decompose")
                    break

            futures = [executor.submit(core._decompose_node, n) for n in nodes]

            for future in as_completed(futures):
                if core.should_stop():
                    break
                try:
                    result = future.result(timeout=60)
                    count = core._process_result(result)
                    pbar.update(count)
                    save_counter += count

                    pbar.set_postfix(
                        {
                            "rpm": f"{core.get_rpm():.0f}",
                            "atomic": core.atomic_found.value,
                            "err": core.errors.value,
                        }
                    )
                except Exception:
                    core.errors.increment()

            if save_counter >= config.save_interval:
                core.save_pending()
                save_counter = 0

    pbar.close()
    core.save_pending()

    elapsed = core.get_elapsed()
    final_count = len(list(core.graph.iter_nodes()))

    print(f"\n{'='*60}")
    print(f"  COMPLETE")
    print(f"{'='*60}")
    print(f"  Generated: {core.generated.value:,}")
    print(f"  Atomic:    {core.atomic_found.value:,}")
    print(f"  Errors:    {core.errors.value}")
    print(f"  Time:      {elapsed:.0f}s")
    print(f"  Avg RPM:   {core.get_rpm():.0f}")
    print(f"  Nodes:     {final_count:,} (was {initial_count:,})")
    print(f"{'='*60}\n")

    return {
        "generated": core.generated.value,
        "atomic_found": core.atomic_found.value,
        "errors": core.errors.value,
        "api_calls": core.api_calls.value,
    }


def run_with_tui(config: FastGenConfig) -> dict:
    """Run generation with Textual TUI."""
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, Static, ProgressBar, Label, RichLog
    from textual.containers import Container

    # Create core outside the app
    core = GeneratorCore(config)
    initial_count = len(list(core.graph.iter_nodes()))
    result_holder = {"result": {}}

    class GeneratorApp(App):
        """Textual app for monitoring generation."""

        CSS = """
        Screen {
            layout: vertical;
        }

        #title {
            text-align: center;
            text-style: bold;
            background: $primary;
            color: $text;
            padding: 1;
        }

        #progress-section {
            height: 4;
            padding: 0 2;
        }

        #flow-section {
            height: 6;
            padding: 1 2;
            border: solid $primary;
            margin: 1;
        }

        #stats-section {
            height: 12;
            padding: 1 2;
            border: solid $secondary;
            margin: 1;
        }

        #status {
            text-align: center;
            background: $surface;
            padding: 1;
        }

        .flow-line {
            height: 1;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("s", "save", "Save Now"),
        ]

        def __init__(self):
            super().__init__()
            self._executor: ThreadPoolExecutor | None = None
            self._worker_thread: threading.Thread | None = None
            self._running = True

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("🚀 CONTINUOUS FLOW TASK MINING", id="title")

            with Container(id="progress-section"):
                yield Label(f"Progress: 0 / {config.max_tasks:,}", id="progress-label")
                yield ProgressBar(total=config.max_tasks, show_eta=True, id="progress-bar")

            with Container(id="flow-section"):
                yield Static("─── FLOW ───", id="flow-title")
                yield Static(
                    "Work Queue:   [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]    0",
                    id="work-bar",
                    classes="flow-line",
                )
                yield Static(
                    "In Flight:    [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]    0",
                    id="flight-bar",
                    classes="flow-line",
                )
                yield Static(
                    "Pending Save: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]    0",
                    id="pending-bar",
                    classes="flow-line",
                )

            with Container(id="stats-section"):
                yield Static(self._render_stats(), id="stats")

            yield Static("Starting...", id="status")
            yield Footer()

        def _make_bar(self, label: str, value: int, max_val: int) -> str:
            if max_val == 0:
                pct = 0
            else:
                pct = min(100, (value / max_val) * 100)
            width = 30
            filled = int(width * pct / 100)
            bar = "█" * filled + "░" * (width - filled)
            return f"{label:14}[{bar}] {value:>4}"

        def _render_stats(self) -> str:
            elapsed = core.get_elapsed()
            rpm = core.get_rpm()
            rate = core.generated.value / elapsed if elapsed > 0 else 0

            # ETA
            if rate > 0:
                remaining = config.max_tasks - core.generated.value
                eta_sec = remaining / rate
                if eta_sec > 3600:
                    eta = f"{eta_sec/3600:.1f}h"
                elif eta_sec > 60:
                    eta = f"{eta_sec/60:.0f}m"
                else:
                    eta = f"{eta_sec:.0f}s"
            else:
                eta = "..."

            return f"""─── STATISTICS ───
  Generated:  {core.generated.value:>10,}     ETA: {eta}
  Atomic:     {core.atomic_found.value:>10,}
  Decomposed: {core.decomposed.value:>10,}
  Errors:     {core.errors.value:>10,}
  API Calls:  {core.api_calls.value:>10,}
  ─────────────────
  RPM:        {rpm:>10.0f}
  Rate:       {rate:>10.1f} tasks/s
  Elapsed:    {elapsed:>10.0f}s"""

        def on_mount(self) -> None:
            # Start worker thread
            self._worker_thread = threading.Thread(target=self._run_generation, daemon=True)
            self._worker_thread.start()

            # Update UI periodically
            self.set_interval(0.2, self._update_ui)

        def _update_ui(self) -> None:
            # Progress
            self.query_one("#progress-bar", ProgressBar).update(progress=core.generated.value)
            self.query_one("#progress-label", Label).update(
                f"Progress: {core.generated.value:,} / {config.max_tasks:,}"
            )

            # Flow bars
            self.query_one("#work-bar", Static).update(
                self._make_bar("Work Queue:", core.work_queued.value, config.queue_size)
            )
            self.query_one("#flight-bar", Static).update(
                self._make_bar("In Flight:", core.in_flight.value, config.max_workers)
            )
            self.query_one("#pending-bar", Static).update(
                self._make_bar("Pending Save:", core.get_pending_count(), config.save_interval)
            )

            # Stats
            self.query_one("#stats", Static).update(self._render_stats())

            # Status
            self.query_one("#status", Static).update(core.get_status())

        def _run_generation(self) -> None:
            """Run generation in background thread."""
            save_counter = 0

            try:
                with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
                    while self._running and not core.should_stop():
                        nodes = list(core.iter_decomposable(limit=200))
                        core.work_queued.set(len(nodes))

                        if not nodes:
                            core.save_pending()
                            save_counter = 0
                            time.sleep(0.1)
                            nodes = list(core.iter_decomposable(limit=200))
                            core.work_queued.set(len(nodes))
                            if not nodes:
                                core.set_status("✅ Hierarchy fully mined! Press Q to exit.")
                                core._done = True
                                break

                        core.set_status(f"Processing {len(nodes)} nodes...")

                        futures = [executor.submit(core._decompose_node, n) for n in nodes]

                        for future in as_completed(futures):
                            if not self._running:
                                break
                            try:
                                result = future.result(timeout=30)
                                core._process_result(result)
                                save_counter += 1
                            except Exception as e:
                                core.errors.increment()

                        if save_counter >= config.save_interval:
                            core.set_status("💾 Saving...")
                            core.save_pending()
                            save_counter = 0

                # Final save
                core.save_pending()

                result_holder["result"] = {
                    "generated": core.generated.value,
                    "atomic_found": core.atomic_found.value,
                    "decomposed": core.decomposed.value,
                    "errors": core.errors.value,
                    "api_calls": core.api_calls.value,
                }

                if core.generated.value >= config.max_tasks:
                    core.set_status(f"✅ Reached {config.max_tasks:,} tasks! Press Q to exit.")

            except Exception as e:
                core.set_status(f"❌ Error: {e}")

        def action_quit(self) -> None:
            self._running = False
            core.stop()
            core.save_pending()
            self.exit()

        def action_save(self) -> None:
            core.save_pending()
            core.set_status("💾 Saved!")

    # Run the app
    app = GeneratorApp()
    app.run()

    # Print final summary
    elapsed = core.get_elapsed()
    final_count = len(list(core.graph.iter_nodes()))

    print(f"\n{'='*60}")
    print(f"  COMPLETE")
    print(f"{'='*60}")
    print(f"  Generated: {core.generated.value:,}")
    print(f"  Atomic:    {core.atomic_found.value:,}")
    print(f"  Errors:    {core.errors.value}")
    print(f"  Time:      {elapsed:.0f}s")
    print(f"  Avg RPM:   {core.get_rpm():.0f}")
    print(f"  Nodes:     {final_count:,} (was {initial_count:,})")
    print(f"{'='*60}\n")

    return result_holder["result"]


def run(config: FastGenConfig) -> dict:
    """Run generation with or without TUI."""
    import sys

    if config.tui and sys.stdout.isatty():
        try:
            return run_with_tui(config)
        except ImportError as e:
            print(f"[WARN] Textual not available ({e}), using simple mode")
            return run_without_tui(config)
    else:
        return run_without_tui(config)


# For backwards compatibility
class FastGenerator:
    def __init__(self, config: FastGenConfig):
        self.config = config

    def run(self) -> dict:
        return run(self.config)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fast VLA/VLN task mining")
    parser.add_argument("-o", "--output", default="./task_hierarchy", help="Output directory")
    parser.add_argument("--max-tasks", type=int, default=100000, help="Max tasks to generate")
    parser.add_argument("--workers", type=int, default=128, help="Concurrent workers")
    parser.add_argument("--queue-size", type=int, default=1000, help="Work queue size")
    parser.add_argument("--rpm", type=int, default=1000, help="Rate limit (RPM)")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM")
    parser.add_argument("--no-tui", action="store_true", help="Disable TUI")
    args = parser.parse_args()

    config = FastGenConfig(
        output_dir=Path(args.output),
        max_tasks=args.max_tasks,
        max_workers=args.workers,
        queue_size=args.queue_size,
        rpm_limit=args.rpm,
        mock=args.mock,
        tui=not args.no_tui,
    )

    run(config)


if __name__ == "__main__":
    main()
