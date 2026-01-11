"""
Recursive Task Decomposition Engine.

This module implements the core algorithm for building a comprehensive
hierarchical taxonomy of human tasks. It combines seed data from multiple
sources with LLM-powered expansion to achieve exhaustive coverage.

Data Sources:
    - O*NET: 18,796 work task statements across 1,016 occupations
    - Life Activities: Personal care, household, caregiving, etc.

Algorithm Overview:
    1. Bootstrap from O*NET (work) and Life Activities (non-work)
    2. For each node, decide if it needs decomposition (is it atomic?)
    3. If not atomic, use LLM to generate subtasks
    4. Recursively process subtasks until reaching atomic level
    5. Persist results to filesystem-backed graph
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from taskpedia.hierarchy import NodeType, SeedSource, TaskGraph, TaskNode
from taskpedia.seeds.onet import ONetDatabase, load_onet
from taskpedia.seeds.taxonomy import (
    SOC_TO_DOMAIN,
    get_categories_for_domain,
    get_domain_name,
    get_life_domains,
)


class DecompositionStrategy(str, Enum):
    """Strategy for decomposing tasks."""

    SEED_ONLY = "seed_only"  # Only use seed data, no LLM
    LLM_ONLY = "llm_only"  # Only use LLM generation
    HYBRID = "hybrid"  # Prefer seeds, fall back to LLM
    INTERACTIVE = "interactive"  # Ask user for decomposition


@dataclass
class DecompositionConfig:
    """Configuration for the decomposition engine."""

    # Strategy
    strategy: DecompositionStrategy = DecompositionStrategy.SEED_ONLY

    # Depth limits
    max_depth: int = 5
    min_children: int = 2
    max_children: int = 20

    # Atomic detection
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
        ]
    )

    # LLM settings (for hybrid/llm_only modes)
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"
    llm_temperature: float = 0.7

    # Output
    output_dir: Path = field(default_factory=lambda: Path("./task_hierarchy"))

    # Processing
    batch_size: int = 10
    save_interval: int = 100


@dataclass
class DecompositionResult:
    """Result of decomposing a single task."""

    parent_node: TaskNode
    children: list[TaskNode]
    source: SeedSource
    is_atomic: bool = False
    reasoning: str = ""


class DecompositionEngine:
    """
    Engine for recursive task decomposition.

    This builds the hierarchical task graph by combining:
    - O*NET data (18,796 work tasks)
    - Life activities taxonomy (personal, household, etc.)
    - Optional LLM expansion
    """

    def __init__(
        self,
        config: DecompositionConfig | None = None,
        llm_client: Any = None,
    ):
        self.config = config or DecompositionConfig()
        self.llm_client = llm_client

        # Initialize graph storage
        self.graph = TaskGraph(self.config.output_dir)

        # O*NET database (loaded lazily)
        self._onet: ONetDatabase | None = None

        # Processing state
        self._queue: deque[str] = deque()
        self._processed: set[str] = set()
        self._stats = {
            "nodes_created": 0,
            "nodes_from_onet": 0,
            "nodes_from_life": 0,
            "nodes_from_llm": 0,
            "atomic_nodes": 0,
        }

    @property
    def onet(self) -> ONetDatabase | None:
        """Lazy load O*NET database (auto-downloads if needed)."""
        if self._onet is None:
            try:
                self._onet = load_onet()  # Auto-downloads
            except Exception as e:
                print(f"Warning: Could not load O*NET data: {e}")
        return self._onet

    def bootstrap(self) -> None:
        """
        Bootstrap the full taxonomy from all seed sources.

        Creates:
        - 23 work domains (from O*NET SOC major groups)
        - 1,016 occupations with 18,796 tasks
        - 12 life domains with activities
        """
        print("Bootstrapping task hierarchy...")
        print()

        # Bootstrap work domains from O*NET
        self._bootstrap_work_domains()

        # Bootstrap life domains
        self._bootstrap_life_domains()

        # Save
        self.graph.save_all()

        print()
        print(f"Bootstrap complete!")
        print(f"  Total nodes: {self._stats['nodes_created']:,}")
        print(f"  From O*NET: {self._stats['nodes_from_onet']:,}")
        print(f"  From Life: {self._stats['nodes_from_life']:,}")

    def _bootstrap_work_domains(self) -> None:
        """Bootstrap work domains from O*NET."""
        if not self.onet:
            print("  Skipping work domains (O*NET data not available)")
            return

        print(f"Loading O*NET: {self.onet.get_stats()}")

        # Create work domain nodes from SOC major groups
        for soc_code, domain in SOC_TO_DOMAIN.items():
            domain_name = get_domain_name(domain)

            # Create domain node
            domain_node = TaskNode(
                id=domain.value,
                name=domain_name,
                node_type=NodeType.DOMAIN,
                description=f"Occupations in {domain_name}",
                sources=[SeedSource.ONET],
                source_ids=[soc_code],
                confidence=1.0,
            )
            self.graph.add_node(domain_node, save=False)
            self._stats["nodes_created"] += 1

            # Add occupations under this domain
            occupations = self.onet.get_occupations_by_major_group(soc_code)

            for occ in occupations:
                # Create occupation node
                occ_node = TaskNode(
                    id=TaskNode.make_id(occ.title, domain.value),
                    name=occ.title,
                    node_type=NodeType.TASK,
                    parent_id=domain.value,
                    description=occ.description[:500] if occ.description else "",
                    sources=[SeedSource.ONET],
                    source_ids=[occ.code],
                    confidence=1.0,
                )
                self.graph.add_node(occ_node, save=False)
                self._stats["nodes_created"] += 1
                self._stats["nodes_from_onet"] += 1

                # Add tasks for this occupation
                tasks = self.onet.get_tasks_for_occupation(occ.code)
                for task in tasks:
                    task_node = TaskNode(
                        id=TaskNode.make_id(task.task[:50], occ_node.id),
                        name=task.task,
                        node_type=NodeType.SUBTASK,
                        parent_id=occ_node.id,
                        sources=[SeedSource.ONET],
                        source_ids=[task.task_id],
                        tags=["core"] if task.task_type == "Core" else ["supplemental"],
                        confidence=1.0,
                    )
                    self.graph.add_node(task_node, save=False)
                    self._stats["nodes_created"] += 1
                    self._stats["nodes_from_onet"] += 1

            print(f"  [{soc_code}] {domain_name}: {len(occupations)} occupations")

    def _bootstrap_life_domains(self) -> None:
        """Bootstrap life domains from taxonomy."""
        print("\nLoading Life Activities...")

        for domain in get_life_domains():
            domain_name = get_domain_name(domain)

            # Create domain node
            domain_node = TaskNode(
                id=domain.value,
                name=domain_name,
                node_type=NodeType.DOMAIN,
                description=f"Personal activities: {domain_name}",
                sources=[SeedSource.HUMAN_CURATED],
                confidence=1.0,
            )
            self.graph.add_node(domain_node, save=False)
            self._stats["nodes_created"] += 1

            # Add activity categories
            categories = get_categories_for_domain(domain)
            for cat in categories:
                cat_node = TaskNode(
                    id=TaskNode.make_id(cat.name, domain.value),
                    name=cat.name,
                    node_type=NodeType.TASK,
                    parent_id=domain.value,
                    description=cat.description,
                    sources=[SeedSource.HUMAN_CURATED],
                    source_ids=[cat.code],
                    confidence=1.0,
                )
                self.graph.add_node(cat_node, save=False)
                self._stats["nodes_created"] += 1
                self._stats["nodes_from_life"] += 1

                # Add example tasks
                for task_name in cat.example_tasks:
                    task_node = TaskNode(
                        id=TaskNode.make_id(task_name, cat_node.id),
                        name=task_name,
                        node_type=NodeType.SUBTASK,
                        parent_id=cat_node.id,
                        sources=[SeedSource.HUMAN_CURATED],
                        confidence=1.0,
                    )
                    self.graph.add_node(task_node, save=False)
                    self._stats["nodes_created"] += 1
                    self._stats["nodes_from_life"] += 1

            task_count = sum(len(c.example_tasks) for c in categories)
            print(
                f"  [{domain.value}] {domain_name}: {len(categories)} categories, {task_count} tasks"
            )

    def get_stats(self) -> dict[str, Any]:
        """Get current statistics."""
        graph_stats = self.graph.get_stats()
        return {
            **self._stats,
            "graph": graph_stats,
        }

    def print_summary(self) -> None:
        """Print a summary of the hierarchy."""
        stats = self.graph.get_stats()

        print("\n" + "=" * 70)
        print("TASK HIERARCHY SUMMARY")
        print("=" * 70)
        print(f"Total nodes:     {stats['total_nodes']:,}")
        print(f"Domains:         {stats['domains']}")
        print(f"Max depth:       {stats['max_depth']}")
        print(f"Leaf nodes:      {stats['leaf_count']:,}")
        print()
        print("By node type:")
        for node_type, count in stats["by_type"].items():
            print(f"  {node_type:12} {count:,}")


def quick_bootstrap(
    output_dir: str | Path = "./task_hierarchy",
) -> TaskGraph:
    """
    Quickly bootstrap a task hierarchy from seed data.

    O*NET data is automatically downloaded on first run.

    Args:
        output_dir: Where to save the hierarchy

    Returns:
        The populated TaskGraph
    """
    config = DecompositionConfig(
        strategy=DecompositionStrategy.SEED_ONLY,
        output_dir=Path(output_dir),
    )

    engine = DecompositionEngine(config)
    engine.bootstrap()
    engine.print_summary()

    return engine.graph
