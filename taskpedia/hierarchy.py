"""
Hierarchical Task Decomposition Engine for PRAXIS.

This module implements a recursive decomposition system that builds a complete
taxonomy of human tasks as a filesystem-based directed acyclic graph (DAG).

The core insight: Human activities form a natural hierarchy where complex tasks
decompose into simpler subtasks until we reach atomic actions. This is not
arbitrary - it reflects how humans actually structure procedural knowledge.

Architecture:
    TaskNode: A node in the task hierarchy (can have children)
    TaskGraph: The full DAG with filesystem-backed persistence
    DecompositionEngine: Recursively expands nodes using LLM + seeds

Seed Sources (priority order):
    1. COIN dataset: 12 domains → 180 tasks → ~800 steps (hierarchical)
    2. BEHAVIOR-1K: 1000 activities with predicate logic definitions
    3. O*NET: 19,000+ occupation-specific task statements
    4. EPIC-KITCHENS: 97 verbs × 300 nouns action annotations
    5. WikiHow: 100k+ procedural articles with steps
    6. ActivityNet: 203 action categories with taxonomy
    7. FrameNet: Semantic frames for verb categorization
    8. VerbNet: 270+ verb classes with thematic roles
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterator

import yaml


class NodeType(str, Enum):
    """Type of node in the task hierarchy."""

    DOMAIN = "domain"  # Top-level category (e.g., "food_preparation")
    TASK = "task"  # Concrete task (e.g., "make_scrambled_eggs")
    SUBTASK = "subtask"  # Component of a task (e.g., "crack_egg")
    ATOMIC = "atomic"  # Indivisible action (e.g., "grasp_egg")


class SeedSource(str, Enum):
    """Source dataset for seed tasks."""

    COIN = "coin"
    BEHAVIOR_1K = "behavior_1k"
    ONET = "onet"
    EPIC_KITCHENS = "epic_kitchens"
    WIKIHOW = "wikihow"
    ACTIVITYNET = "activitynet"
    FRAMENET = "framenet"
    VERBNET = "verbnet"
    LLM_GENERATED = "llm_generated"
    HUMAN_CURATED = "human_curated"


@dataclass
class CompletionSpec:
    """
    Verifiable completion criteria - the defining feature of a task.

    A task is ONLY valid if we can verify its completion. This is what
    distinguishes a task from a vague activity description.
    """

    precondition: str  # Required world state before starting
    postcondition: str  # World state that signifies success
    invariants: str = ""  # Constraints maintained throughout execution

    def to_dict(self) -> dict[str, str]:
        return {
            "precondition": self.precondition,
            "postcondition": self.postcondition,
            "invariants": self.invariants,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompletionSpec:
        return cls(
            precondition=data.get("precondition", ""),
            postcondition=data.get("postcondition", ""),
            invariants=data.get("invariants", ""),
        )


@dataclass
class TaskNode:
    """
    A node in the hierarchical task graph.

    Each node represents a task at some level of abstraction. The hierarchy
    is formed through parent-child relationships stored as IDs.

    File storage: Each node is a YAML file at:
        {root}/{domain}/{path_segments...}/{node_id}.yaml

    The directory structure mirrors the logical hierarchy.
    """

    id: str  # Unique identifier (slug form)
    name: str  # Human-readable name
    node_type: NodeType  # Level in hierarchy

    # Hierarchy
    parent_id: str | None = None  # Parent node ID
    children_ids: list[str] = field(default_factory=list)  # Child node IDs

    # Task specification
    completion: CompletionSpec | None = None  # Verification criteria
    description: str = ""  # What this task accomplishes

    # Embodiment requirements (for leaf nodes)
    physical_requirements: str = ""  # Motor skills needed
    sensing_requirements: str = ""  # Perception capabilities
    cognitive_requirements: str = ""  # Planning/reasoning needs
    typical_duration: str = ""  # Expected time range
    typical_context: str = ""  # Where this is performed

    # Metadata
    language: str = "en"
    aliases: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    # Provenance
    sources: list[SeedSource] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)  # IDs in source datasets
    confidence: float = 1.0

    @staticmethod
    def make_id(name: str, parent_id: str | None = None) -> str:
        """Generate a hierarchical ID from name and parent."""
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        slug = re.sub(r"[-\s]+", "_", slug).strip("_")
        if parent_id:
            # Include parent path for uniqueness
            return f"{parent_id}/{slug}"
        return slug

    def get_path_segments(self) -> list[str]:
        """Get the path segments from the ID."""
        return self.id.split("/")

    def get_depth(self) -> int:
        """Get depth in the hierarchy (0 = root domain)."""
        return len(self.get_path_segments()) - 1

    def is_leaf(self) -> bool:
        """Check if this is a leaf node (no children)."""
        return len(self.children_ids) == 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type.value,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "description": self.description,
            "language": self.language,
            "aliases": self.aliases,
            "tags": self.tags,
            "sources": [s.value for s in self.sources],
            "source_ids": self.source_ids,
            "confidence": self.confidence,
        }

        if self.completion:
            data["completion"] = self.completion.to_dict()

        # Only include embodiment details for leaf-ish nodes
        if self.node_type in (NodeType.SUBTASK, NodeType.ATOMIC):
            data["physical_requirements"] = self.physical_requirements
            data["sensing_requirements"] = self.sensing_requirements
            data["cognitive_requirements"] = self.cognitive_requirements
            data["typical_duration"] = self.typical_duration
            data["typical_context"] = self.typical_context

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskNode:
        """Deserialize from dictionary."""
        completion = None
        if "completion" in data:
            completion = CompletionSpec.from_dict(data["completion"])

        sources = [SeedSource(s) for s in data.get("sources", [])]

        return cls(
            id=data["id"],
            name=data["name"],
            node_type=NodeType(data["node_type"]),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            completion=completion,
            description=data.get("description", ""),
            physical_requirements=data.get("physical_requirements", ""),
            sensing_requirements=data.get("sensing_requirements", ""),
            cognitive_requirements=data.get("cognitive_requirements", ""),
            typical_duration=data.get("typical_duration", ""),
            typical_context=data.get("typical_context", ""),
            language=data.get("language", "en"),
            aliases=data.get("aliases", []),
            tags=data.get("tags", []),
            sources=sources,
            source_ids=data.get("source_ids", []),
            confidence=data.get("confidence", 1.0),
        )

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> TaskNode:
        """Deserialize from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


class TaskGraph:
    """
    Filesystem-backed directed acyclic graph of tasks.

    The graph is stored as a directory tree where:
    - Each node is a YAML file
    - Directory structure mirrors logical hierarchy
    - A manifest file tracks all nodes and their relationships

    Directory structure:
        {root}/
            _manifest.json          # Index of all nodes
            food_preparation/
                _meta.yaml          # Domain node
                cooking/
                    _meta.yaml      # Task category node
                    boiling/
                        _meta.yaml  # Subtask node
                        boil_water.yaml
                        boil_eggs.yaml
    """

    def __init__(self, root_path: Path | str):
        self.root = Path(root_path)
        self.root.mkdir(parents=True, exist_ok=True)

        self._manifest_path = self.root / "_manifest.json"
        self._nodes: dict[str, TaskNode] = {}
        self._load_manifest()

    def _load_manifest(self) -> None:
        """Load the node index from disk."""
        if self._manifest_path.exists():
            try:
                with open(self._manifest_path) as f:
                    manifest = json.load(f)
                    for node_id, node_data in manifest.get("nodes", {}).items():
                        self._nodes[node_id] = TaskNode.from_dict(node_data)
            except json.JSONDecodeError as e:
                print(f"[WARNING] Manifest file corrupted: {e}")
                print("[WARNING] Attempting to rebuild from YAML files...")
                self._rebuild_from_yaml()

    def _rebuild_from_yaml(self) -> None:
        """Rebuild manifest by scanning YAML files."""
        yaml_files = list(self.root.glob("**/*.yaml"))
        print(f"[INFO] Found {len(yaml_files)} YAML files to scan...")

        for yaml_path in yaml_files:
            if yaml_path.name == "_meta.yaml" or yaml_path.suffix == ".yaml":
                try:
                    with open(yaml_path) as f:
                        node = TaskNode.from_yaml(f.read())
                        self._nodes[node.id] = node
                except Exception as e:
                    print(f"[WARNING] Could not load {yaml_path}: {e}")

        print(f"[INFO] Rebuilt manifest with {len(self._nodes)} nodes")
        self._save_manifest()

    def _save_manifest(self) -> None:
        """Save the node index to disk atomically."""
        import tempfile

        manifest = {
            "version": "1.0",
            "node_count": len(self._nodes),
            "nodes": {nid: node.to_dict() for nid, node in self._nodes.items()},
        }

        # Write to temp file first, then atomically rename
        # This prevents corruption if the process is interrupted
        temp_fd, temp_path = tempfile.mkstemp(dir=self.root, prefix="_manifest_", suffix=".json")
        try:
            with os.fdopen(temp_fd, "w") as f:
                json.dump(manifest, f, indent=2)
            # Atomic rename (on POSIX systems)
            os.replace(temp_path, self._manifest_path)
        except Exception:
            # Clean up temp file if something goes wrong
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def _get_node_path(self, node: TaskNode) -> Path:
        """Get the filesystem path for a node."""
        segments = node.get_path_segments()

        if len(segments) == 1:
            # Domain node: {root}/{domain}/_meta.yaml
            return self.root / segments[0] / "_meta.yaml"
        else:
            # Nested node: {root}/{segments...}/_meta.yaml or {leaf}.yaml
            parent_dir = self.root / "/".join(segments[:-1])
            if node.is_leaf() and node.node_type == NodeType.ATOMIC:
                return parent_dir / f"{segments[-1]}.yaml"
            else:
                return parent_dir / segments[-1] / "_meta.yaml"

    def add_node(self, node: TaskNode, save: bool = True) -> None:
        """Add a node to the graph."""
        # Validate parent exists if specified
        if node.parent_id and node.parent_id not in self._nodes:
            raise ValueError(f"Parent node {node.parent_id} does not exist")

        # Update parent's children list
        if node.parent_id:
            parent = self._nodes[node.parent_id]
            if node.id not in parent.children_ids:
                parent.children_ids.append(node.id)

        self._nodes[node.id] = node

        if save:
            self._save_node(node)
            self._save_manifest()

    def _save_node(self, node: TaskNode) -> None:
        """Save a node to its YAML file."""
        path = self._get_node_path(node)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(node.to_yaml())

    def get_node(self, node_id: str) -> TaskNode | None:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_children(self, node_id: str) -> list[TaskNode]:
        """Get all children of a node."""
        node = self._nodes.get(node_id)
        if not node:
            return []
        return [self._nodes[cid] for cid in node.children_ids if cid in self._nodes]

    def get_ancestors(self, node_id: str) -> list[TaskNode]:
        """Get all ancestors of a node (parent, grandparent, etc.)."""
        ancestors = []
        node = self._nodes.get(node_id)
        while node and node.parent_id:
            parent = self._nodes.get(node.parent_id)
            if parent:
                ancestors.append(parent)
                node = parent
            else:
                break
        return ancestors

    def get_leaves(self) -> list[TaskNode]:
        """Get all leaf nodes (no children)."""
        return [n for n in self._nodes.values() if n.is_leaf()]

    def get_by_type(self, node_type: NodeType) -> list[TaskNode]:
        """Get all nodes of a specific type."""
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def get_by_source(self, source: SeedSource) -> list[TaskNode]:
        """Get all nodes from a specific seed source."""
        return [n for n in self._nodes.values() if source in n.sources]

    def iter_nodes(self) -> Iterator[TaskNode]:
        """Iterate over all nodes."""
        yield from self._nodes.values()

    def iter_bfs(self, start_id: str | None = None) -> Iterator[TaskNode]:
        """Breadth-first iteration from a starting node (or all roots)."""
        from collections import deque

        if start_id:
            queue = deque([start_id])
        else:
            # Start from all root nodes (domains)
            queue = deque([n.id for n in self._nodes.values() if n.parent_id is None])

        visited = set()
        while queue:
            node_id = queue.popleft()
            if node_id in visited:
                continue
            visited.add(node_id)

            node = self._nodes.get(node_id)
            if node:
                yield node
                queue.extend(node.children_ids)

    def iter_dfs(self, start_id: str | None = None) -> Iterator[TaskNode]:
        """Depth-first iteration from a starting node (or all roots)."""
        if start_id:
            stack = [start_id]
        else:
            stack = [n.id for n in self._nodes.values() if n.parent_id is None]

        visited = set()
        while stack:
            node_id = stack.pop()
            if node_id in visited:
                continue
            visited.add(node_id)

            node = self._nodes.get(node_id)
            if node:
                yield node
                # Add children in reverse to maintain order
                stack.extend(reversed(node.children_ids))

    def count_nodes(self) -> dict[str, int]:
        """Count nodes by type."""
        counts = {t.value: 0 for t in NodeType}
        for node in self._nodes.values():
            counts[node.node_type.value] += 1
        return counts

    def get_stats(self) -> dict[str, Any]:
        """Get graph statistics."""
        counts = self.count_nodes()
        depths = [n.get_depth() for n in self._nodes.values()]

        return {
            "total_nodes": len(self._nodes),
            "by_type": counts,
            "max_depth": max(depths) if depths else 0,
            "avg_depth": sum(depths) / len(depths) if depths else 0,
            "leaf_count": len(self.get_leaves()),
            "domains": len(self.get_by_type(NodeType.DOMAIN)),
        }

    def save_all(self) -> None:
        """Save all nodes and manifest to disk."""
        for node in self._nodes.values():
            self._save_node(node)
        self._save_manifest()

    def export_flat(self, output_path: Path | str) -> None:
        """Export all nodes to a single JSONL file."""
        output_path = Path(output_path)
        with open(output_path, "w") as f:
            for node in self._nodes.values():
                f.write(json.dumps(node.to_dict()) + "\n")

    def visualize_tree(self, max_depth: int = 3) -> str:
        """Generate a text visualization of the tree structure."""
        lines = []

        def _recurse(node_id: str, prefix: str = "", is_last: bool = True, depth: int = 0):
            if depth > max_depth:
                return

            node = self._nodes.get(node_id)
            if not node:
                return

            # Build the line
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{node.name} [{node.node_type.value}]")

            # Recurse to children
            children = node.children_ids
            for i, child_id in enumerate(children):
                is_last_child = i == len(children) - 1
                new_prefix = prefix + ("    " if is_last else "│   ")
                _recurse(child_id, new_prefix, is_last_child, depth + 1)

        # Start from roots
        roots = [n for n in self._nodes.values() if n.parent_id is None]
        for i, root in enumerate(roots):
            is_last = i == len(roots) - 1
            _recurse(root.id, "", is_last)

        return "\n".join(lines)
