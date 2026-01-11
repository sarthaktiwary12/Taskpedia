"""
Base classes for seed data loaders.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from taskpedia.hierarchy import CompletionSpec, NodeType, SeedSource, TaskNode


@dataclass
class SeedTask:
    """
    A task extracted from a seed dataset.

    This is a normalized intermediate representation that gets
    converted into TaskNode objects for the graph.
    """

    # Identity
    source: SeedSource
    source_id: str  # Original ID in the source dataset
    name: str  # Task name

    # Hierarchy hints
    domain: str = ""  # Top-level domain (if available)
    parent_name: str = ""  # Parent task name (if hierarchical)
    children_names: list[str] = field(default_factory=list)  # Child names
    hierarchy_level: int = 0  # 0=domain, 1=task, 2=subtask, etc.

    # Specification
    description: str = ""
    steps: list[str] = field(default_factory=list)  # Ordered steps
    precondition: str = ""
    postcondition: str = ""

    # Additional metadata
    verbs: list[str] = field(default_factory=list)
    nouns: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    duration_estimate: str = ""
    context: str = ""

    # Quality
    confidence: float = 1.0

    def to_task_node(self, parent_id: str | None = None) -> TaskNode:
        """Convert to a TaskNode."""
        # Determine node type from hierarchy level
        if self.hierarchy_level == 0:
            node_type = NodeType.DOMAIN
        elif self.hierarchy_level == 1:
            node_type = NodeType.TASK
        elif self.hierarchy_level == 2:
            node_type = NodeType.SUBTASK
        else:
            node_type = NodeType.ATOMIC

        # Build completion spec if we have pre/post conditions
        completion = None
        if self.precondition or self.postcondition:
            completion = CompletionSpec(
                precondition=self.precondition,
                postcondition=self.postcondition,
            )

        node_id = TaskNode.make_id(self.name, parent_id)

        return TaskNode(
            id=node_id,
            name=self.name,
            node_type=node_type,
            parent_id=parent_id,
            description=self.description,
            completion=completion,
            typical_duration=self.duration_estimate,
            typical_context=self.context,
            tags=self.tags,
            sources=[self.source],
            source_ids=[self.source_id],
            confidence=self.confidence,
        )


class BaseSeedLoader(ABC):
    """
    Abstract base class for seed dataset loaders.

    Each loader is responsible for:
    1. Downloading/accessing its source dataset
    2. Parsing the dataset into SeedTask objects
    3. Providing iteration over tasks with hierarchy information
    """

    source: SeedSource

    def __init__(self, cache_dir: Path | str | None = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".praxis_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._loaded = False

    @abstractmethod
    def load(self) -> None:
        """Load/download the dataset."""
        pass

    @abstractmethod
    def get_domains(self) -> list[SeedTask]:
        """Get top-level domains/categories."""
        pass

    @abstractmethod
    def get_tasks(self, domain: str | None = None) -> list[SeedTask]:
        """Get tasks, optionally filtered by domain."""
        pass

    @abstractmethod
    def get_subtasks(self, task_id: str) -> list[SeedTask]:
        """Get subtasks/steps for a given task."""
        pass

    def iter_all(self) -> Iterator[SeedTask]:
        """Iterate over all tasks in the dataset."""
        for domain in self.get_domains():
            yield domain
            for task in self.get_tasks(domain.name):
                yield task
                for subtask in self.get_subtasks(task.source_id):
                    yield subtask

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the loaded dataset."""
        domains = self.get_domains()
        tasks = self.get_tasks()

        return {
            "source": self.source.value,
            "domain_count": len(domains),
            "task_count": len(tasks),
            "loaded": self._loaded,
        }
