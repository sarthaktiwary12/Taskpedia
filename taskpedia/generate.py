"""
Synthetic Data Generation Pipeline for TASKPEDIA.

Uses:
- Ray for parallel task processing
- Tenacity for retry logic
- Diskcache for LLM response caching

Usage:
    from taskpedia.generate import TaskGenerator

    generator = TaskGenerator(output_dir="./task_hierarchy")
    generator.run(max_tasks=10000)
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import ray
from diskcache import Cache
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tqdm import tqdm

from taskpedia.hierarchy import NodeType, SeedSource, TaskGraph, TaskNode
from taskpedia.llm import LLMClient, LLMConfig

# Cache configuration
CACHE_DIR = Path("./.taskpedia_cache")
CACHE_SIZE_LIMIT = 10 * 1024 * 1024 * 1024  # 10GB


@dataclass
class GenerationConfig:
    """Configuration for the generation pipeline."""

    # Output
    output_dir: Path = field(default_factory=lambda: Path("./task_hierarchy"))
    cache_dir: Path = field(default_factory=lambda: CACHE_DIR)

    # LLM settings
    model: str = "models/gemini-2.5-flash"
    temperature: float = 0.7
    thinking_budget: int = 1024

    # Generation limits
    max_tasks: int = 10000
    max_depth: int = 5

    # Parallelization
    num_workers: int = 4
    batch_size: int = 50

    # Rate limiting (requests per minute)
    rpm_limit: int = 60

    # Retry settings
    max_retries: int = 3

    # Atomic detection keywords
    atomic_keywords: list[str] = field(
        default_factory=lambda: [
            "grasp",
            "release",
            "press",
            "push",
            "pull",
            "twist",
            "turn",
            "lift",
            "lower",
            "reach",
            "point",
            "touch",
            "tap",
            "click",
            "look",
            "listen",
            "wait",
            "hold",
            "squeeze",
            "open",
            "close",
        ]
    )


def get_cache_key(prompt: str, model: str) -> str:
    """Generate a cache key for an LLM request."""
    content = f"{model}:{prompt}"
    return hashlib.sha256(content.encode()).hexdigest()


class CachedLLMClient:
    """LLM client with disk-based caching and retry logic."""

    def __init__(self, config: GenerationConfig):
        self.config = config
        self.cache = Cache(
            str(config.cache_dir),
            size_limit=CACHE_SIZE_LIMIT,
        )
        self._client: LLMClient | None = None
        self._last_request_time = 0.0
        self._min_interval = 60.0 / config.rpm_limit

    @property
    def client(self) -> LLMClient:
        """Lazy-load the LLM client."""
        if self._client is None:
            llm_config = LLMConfig(
                model=self.config.model,
                temperature=self.config.temperature,
                thinking_budget=self.config.thinking_budget,
            )
            self._client = LLMClient(config=llm_config)
        return self._client

    def _rate_limit(self):
        """Apply rate limiting."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((Exception,)),
    )
    def _call_llm(self, prompt: str, system_prompt: str) -> str:
        """Make an LLM call with retry logic."""
        self._rate_limit()
        return self.client.generate(prompt, system_prompt, use_thinking=True)

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate with caching."""
        cache_key = get_cache_key(f"{system_prompt}\n{prompt}", self.config.model)

        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Call LLM
        response = self._call_llm(prompt, system_prompt)

        # Cache response
        self.cache.set(cache_key, response)

        return response

    def generate_json(self, prompt: str, system_prompt: str = "") -> dict[str, Any]:
        """Generate and parse JSON response."""
        response = self.generate(prompt, system_prompt)

        # Extract JSON from response
        json_text = response.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        elif json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]

        return json.loads(json_text.strip())

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "volume": self.cache.volume(),
        }


# Ray remote function for parallel decomposition
@ray.remote
def decompose_task_remote(
    node_data: dict,
    parent_context: str,
    config_dict: dict,
) -> dict[str, Any]:
    """Decompose a task into subtasks (Ray remote function)."""

    # Reconstruct config and client inside worker
    config = GenerationConfig(**config_dict)
    llm = CachedLLMClient(config)

    system_prompt = """You are an expert at analyzing human tasks and breaking them down into logical subtasks.

Rules:
1. Each subtask should be a distinct, meaningful action
2. Subtasks should be ordered logically
3. A task with 1-2 very simple actions is ATOMIC (cannot be decomposed)
4. Return 3-10 subtasks for non-atomic tasks
5. Be concrete and specific

Output JSON:
{
    "is_atomic": boolean,
    "reasoning": "brief explanation",
    "confidence": 0.0-1.0,
    "subtasks": [{"name": "subtask name", "description": "what it does"}]
}"""

    prompt = f"""Decompose this task:

Task: {node_data['name']}
Description: {node_data.get('description', '')}
Context: {parent_context}

Return JSON."""

    try:
        result = llm.generate_json(prompt, system_prompt)
        return {
            "node_id": node_data["id"],
            "success": True,
            "is_atomic": result.get("is_atomic", False),
            "subtasks": result.get("subtasks", []),
            "confidence": result.get("confidence", 0.8),
        }
    except Exception as e:
        return {
            "node_id": node_data["id"],
            "success": False,
            "error": str(e),
        }


@ray.remote
def expand_domain_remote(
    domain_data: dict,
    existing_tasks: list[str],
    config_dict: dict,
) -> dict[str, Any]:
    """Expand a domain with new tasks (Ray remote function)."""

    config = GenerationConfig(**config_dict)
    llm = CachedLLMClient(config)

    system_prompt = """You are an expert at identifying human tasks within specific domains.
Generate diverse, concrete tasks that humans perform.

Rules:
1. Tasks should be specific and actionable
2. Avoid duplicating existing tasks
3. Cover different aspects of the domain
4. Tasks should be verifiable

Output JSON:
{
    "tasks": [{"name": "task name", "description": "what it does", "tags": ["tag1"]}]
}"""

    existing_sample = existing_tasks[:30]
    prompt = f"""Generate 10 new tasks for this domain:

Domain: {domain_data['name']}
Description: {domain_data.get('description', '')}

Existing tasks (avoid duplicates):
{chr(10).join(f'- {t}' for t in existing_sample)}

Return JSON with 10 new unique tasks."""

    try:
        result = llm.generate_json(prompt, system_prompt)
        return {
            "domain_id": domain_data["id"],
            "success": True,
            "tasks": result.get("tasks", []),
        }
    except Exception as e:
        return {
            "domain_id": domain_data["id"],
            "success": False,
            "error": str(e),
        }


class TaskGenerator:
    """
    Main synthetic data generation pipeline.

    Uses Ray for parallelization, tenacity for retries,
    and diskcache for caching LLM responses.
    """

    def __init__(self, config: GenerationConfig | None = None):
        self.config = config or GenerationConfig()
        self.graph = TaskGraph(self.config.output_dir)
        self.llm = CachedLLMClient(self.config)

        self._stats = {
            "tasks_generated": 0,
            "decompositions": 0,
            "expansions": 0,
            "cache_hits": 0,
            "errors": 0,
        }

    def _is_likely_atomic(self, node: TaskNode) -> bool:
        """Check if a node is likely atomic."""
        name_lower = node.name.lower()

        for keyword in self.config.atomic_keywords:
            if keyword in name_lower:
                return True

        if len(node.name.split()) <= 2:
            return True

        if len(node.children_ids) >= 3:
            return True

        return False

    def _get_decomposable_nodes(self, limit: int = 100) -> list[TaskNode]:
        """Get nodes that can be decomposed."""
        nodes = []
        for node in self.graph.get_leaves():
            if node.node_type in (NodeType.TASK, NodeType.SUBTASK):
                if not self._is_likely_atomic(node):
                    nodes.append(node)
                    if len(nodes) >= limit:
                        break
        return nodes

    def _process_decomposition_results(self, results: list[dict]) -> int:
        """Process decomposition results and add new nodes."""
        new_count = 0

        for result in results:
            if not result.get("success"):
                self._stats["errors"] += 1
                continue

            node_id = result["node_id"]
            node = self.graph.get_node(node_id)
            if not node:
                continue

            if result.get("is_atomic"):
                node.node_type = NodeType.ATOMIC
                self.graph.add_node(node)
                continue

            subtasks = result.get("subtasks", [])
            for subtask in subtasks:
                name = subtask.get("name", str(subtask))
                child = TaskNode(
                    id=TaskNode.make_id(name, node.id),
                    name=name,
                    node_type=NodeType.SUBTASK,
                    parent_id=node.id,
                    description=subtask.get("description", ""),
                    sources=[SeedSource.LLM_GENERATED],
                    confidence=result.get("confidence", 0.8),
                )
                self.graph.add_node(child)
                new_count += 1

            self._stats["decompositions"] += 1

        self._stats["tasks_generated"] += new_count
        return new_count

    def _process_expansion_results(self, results: list[dict]) -> int:
        """Process expansion results and add new nodes."""
        new_count = 0

        for result in results:
            if not result.get("success"):
                self._stats["errors"] += 1
                continue

            domain_id = result["domain_id"]
            domain = self.graph.get_node(domain_id)
            if not domain:
                continue

            existing_names = {c.name.lower() for c in self.graph.get_children(domain_id)}

            for task in result.get("tasks", []):
                name = task.get("name", str(task))
                if name.lower() in existing_names:
                    continue

                child = TaskNode(
                    id=TaskNode.make_id(name, domain_id),
                    name=name,
                    node_type=NodeType.TASK,
                    parent_id=domain_id,
                    description=task.get("description", ""),
                    tags=task.get("tags", []),
                    sources=[SeedSource.LLM_GENERATED],
                    confidence=0.8,
                )
                self.graph.add_node(child)
                new_count += 1

            self._stats["expansions"] += 1

        self._stats["tasks_generated"] += new_count
        return new_count

    def run(
        self,
        max_tasks: int | None = None,
        expand_domains: bool = True,
        callback: Callable[[dict], None] | None = None,
    ) -> dict[str, Any]:
        """
        Run the generation pipeline.

        Args:
            max_tasks: Maximum tasks to generate
            expand_domains: Whether to expand domains with new tasks
            callback: Progress callback

        Returns:
            Generation statistics
        """
        max_tasks = max_tasks or self.config.max_tasks

        # Initialize Ray
        if not ray.is_initialized():
            ray.init(num_cpus=self.config.num_workers, ignore_reinit_error=True)

        print(f"TASKPEDIA Generation Pipeline")
        print(f"=" * 60)
        print(f"Output:      {self.config.output_dir}")
        print(f"Model:       {self.config.model}")
        print(f"Max tasks:   {max_tasks}")
        print(f"Workers:     {self.config.num_workers}")
        print(f"Cache:       {self.llm.get_cache_stats()}")
        print()

        config_dict = {
            "output_dir": str(self.config.output_dir),
            "cache_dir": str(self.config.cache_dir),
            "model": self.config.model,
            "temperature": self.config.temperature,
            "thinking_budget": self.config.thinking_budget,
            "rpm_limit": self.config.rpm_limit,
            "max_retries": self.config.max_retries,
        }

        pbar = tqdm(total=max_tasks, desc="Generating tasks")

        while self._stats["tasks_generated"] < max_tasks:
            # Get batch of nodes to decompose
            nodes = self._get_decomposable_nodes(limit=self.config.batch_size)

            if not nodes and not expand_domains:
                print("No more nodes to decompose.")
                break

            # Submit decomposition jobs
            if nodes:
                futures = []
                for node in nodes:
                    ancestors = self.graph.get_ancestors(node.id)
                    context = " > ".join([a.name for a in reversed(ancestors)])

                    future = decompose_task_remote.remote(
                        node.to_dict(),
                        context,
                        config_dict,
                    )
                    futures.append(future)

                # Wait for results
                results = ray.get(futures)
                new_count = self._process_decomposition_results(results)
                pbar.update(new_count)

            # Optionally expand domains
            if expand_domains and self._stats["tasks_generated"] < max_tasks:
                domains = self.graph.get_by_type(NodeType.DOMAIN)[:5]
                if domains:
                    futures = []
                    for domain in domains:
                        children = self.graph.get_children(domain.id)
                        existing = [c.name for c in children]

                        future = expand_domain_remote.remote(
                            domain.to_dict(),
                            existing,
                            config_dict,
                        )
                        futures.append(future)

                    results = ray.get(futures)
                    new_count = self._process_expansion_results(results)
                    pbar.update(new_count)

            # Save periodically
            self.graph.save_all()

            if callback:
                callback(self._stats.copy())

        pbar.close()

        # Final save
        self.graph.save_all()

        # Final stats
        self._stats["graph_stats"] = self.graph.get_stats()
        self._stats["cache_stats"] = self.llm.get_cache_stats()

        print()
        print("=" * 60)
        print("GENERATION COMPLETE")
        print("=" * 60)
        print(f"Tasks generated:  {self._stats['tasks_generated']}")
        print(f"Decompositions:   {self._stats['decompositions']}")
        print(f"Expansions:       {self._stats['expansions']}")
        print(f"Errors:           {self._stats['errors']}")
        print(f"Cache size:       {self._stats['cache_stats']['size']}")

        return self._stats


def run_generation(
    output_dir: str = "./task_hierarchy",
    max_tasks: int = 1000,
    model: str = "gemini-2.5-flash",
    num_workers: int = 4,
) -> dict[str, Any]:
    """
    Convenience function to run generation.

    Args:
        output_dir: Where to save the hierarchy
        max_tasks: Maximum tasks to generate
        model: LLM model to use
        num_workers: Number of parallel workers

    Returns:
        Generation statistics
    """
    config = GenerationConfig(
        output_dir=Path(output_dir),
        model=model,
        max_tasks=max_tasks,
        num_workers=num_workers,
    )

    generator = TaskGenerator(config=config)
    return generator.run()
