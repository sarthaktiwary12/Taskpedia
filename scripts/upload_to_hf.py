#!/usr/bin/env python3
"""
Upload TASKPEDIA hierarchy to HuggingFace as a dataset.

Usage:
    # First time: login to HuggingFace
    huggingface-cli login

    # Upload (private by default)
    python scripts/upload_to_hf.py --task-dir ./task_hierarchy --repo sentient-x/taskpedia

    # Upload as public
    python scripts/upload_to_hf.py --task-dir ./task_hierarchy --repo sentient-x/taskpedia --public

Requirements:
    pip install datasets huggingface_hub
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import yaml
from datasets import Dataset, DatasetDict, Features, Sequence, Value
from huggingface_hub import HfApi


def load_task_hierarchy(task_dir: Path) -> list[dict]:
    """Load all tasks from YAML files in the hierarchy."""
    tasks = []

    yaml_files = list(task_dir.glob("**/*.yaml"))
    print(f"Found {len(yaml_files):,} YAML files")

    for yaml_path in yaml_files:
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)

            if not data or "id" not in data:
                continue

            # Flatten completion criteria
            completion = data.get("completion", {}) or {}

            task = {
                "id": data.get("id", ""),
                "name": data.get("name", ""),
                "node_type": data.get("node_type", ""),
                "parent_id": data.get("parent_id", "") or "",
                "children_ids": data.get("children_ids", []) or [],
                "description": data.get("description", "") or "",
                # Completion criteria (key for VLA/VLN)
                "precondition": completion.get("precondition", "") or "",
                "postcondition": completion.get("postcondition", "") or "",
                "invariants": completion.get("invariants", "") or "",
                # Embodiment requirements
                "physical_requirements": data.get("physical_requirements", "") or "",
                "sensing_requirements": data.get("sensing_requirements", "") or "",
                "cognitive_requirements": data.get("cognitive_requirements", "") or "",
                "typical_duration": data.get("typical_duration", "") or "",
                "typical_context": data.get("typical_context", "") or "",
                # Metadata
                "language": data.get("language", "en"),
                "aliases": data.get("aliases", []) or [],
                "tags": data.get("tags", []) or [],
                "sources": data.get("sources", []) or [],
                "source_ids": data.get("source_ids", []) or [],
                "confidence": float(data.get("confidence", 1.0)),
                # Hierarchy info
                "depth": len(data.get("id", "").split("/")),
                "is_leaf": len(data.get("children_ids", []) or []) == 0,
                "is_atomic": data.get("node_type") == "atomic",
            }

            tasks.append(task)

        except Exception as e:
            print(f"Warning: Could not load {yaml_path}: {e}")

    return tasks


def create_dataset(tasks: list[dict]) -> DatasetDict:
    """Create a HuggingFace Dataset from tasks."""

    # Define features explicitly for better schema
    features = Features(
        {
            "id": Value("string"),
            "name": Value("string"),
            "node_type": Value("string"),
            "parent_id": Value("string"),
            "children_ids": Sequence(Value("string")),
            "description": Value("string"),
            # Completion criteria
            "precondition": Value("string"),
            "postcondition": Value("string"),
            "invariants": Value("string"),
            # Embodiment
            "physical_requirements": Value("string"),
            "sensing_requirements": Value("string"),
            "cognitive_requirements": Value("string"),
            "typical_duration": Value("string"),
            "typical_context": Value("string"),
            # Metadata
            "language": Value("string"),
            "aliases": Sequence(Value("string")),
            "tags": Sequence(Value("string")),
            "sources": Sequence(Value("string")),
            "source_ids": Sequence(Value("string")),
            "confidence": Value("float32"),
            # Hierarchy
            "depth": Value("int32"),
            "is_leaf": Value("bool"),
            "is_atomic": Value("bool"),
        }
    )

    # Create dataset
    dataset = Dataset.from_list(tasks, features=features)

    # Split into train (for convenience, though this is a taxonomy not training data)
    # We keep it as a single split since it's a knowledge base
    return DatasetDict({"full": dataset})


def compute_stats(tasks: list[dict]) -> dict:
    """Compute dataset statistics for the README."""
    from collections import Counter

    node_types = Counter(t["node_type"] for t in tasks)
    sources = Counter(s for t in tasks for s in t["sources"])
    depths = Counter(t["depth"] for t in tasks)

    atomic_count = sum(1 for t in tasks if t["is_atomic"])
    leaf_count = sum(1 for t in tasks if t["is_leaf"])
    with_completion = sum(1 for t in tasks if t["precondition"] or t["postcondition"])

    return {
        "total_tasks": len(tasks),
        "atomic_tasks": atomic_count,
        "leaf_tasks": leaf_count,
        "with_completion_criteria": with_completion,
        "node_types": dict(node_types),
        "sources": dict(sources),
        "max_depth": max(depths.keys()) if depths else 0,
        "avg_depth": sum(t["depth"] for t in tasks) / len(tasks) if tasks else 0,
    }


def generate_readme(stats: dict, repo_id: str) -> str:
    """Generate README for the dataset."""
    return f"""---
license: apache-2.0
task_categories:
  - robotics
  - text-generation
language:
  - en
tags:
  - robotics
  - embodied-ai
  - task-decomposition
  - VLA
  - VLN
  - hierarchical
size_categories:
  - 10K<n<100K
---

# TASKPEDIA: Hierarchical Task Decomposition for Embodied AI

A comprehensive taxonomy of human tasks decomposed into atomic actions suitable for Vision-Language-Action (VLA) and Vision-Language-Navigation (VLN) model training.

## Dataset Description

TASKPEDIA provides a hierarchical decomposition of human activities, from high-level goals down to atomic motor primitives that robots can execute. Each task includes:

- **Completion Criteria**: Preconditions, postconditions, and invariants for verifiable task completion
- **Hierarchy**: Parent-child relationships forming a directed acyclic graph (DAG)
- **Atomic Actions**: Leaf nodes representing indivisible robot primitives (grasp, release, move_to, etc.)

## Statistics

| Metric | Value |
|--------|-------|
| Total Tasks | {stats["total_tasks"]:,} |
| Atomic Actions | {stats["atomic_tasks"]:,} |
| Leaf Nodes | {stats["leaf_tasks"]:,} |
| With Completion Criteria | {stats["with_completion_criteria"]:,} |
| Max Hierarchy Depth | {stats["max_depth"]} |
| Avg Hierarchy Depth | {stats["avg_depth"]:.2f} |

### By Node Type
{chr(10).join(f"- **{k}**: {v:,}" for k, v in stats["node_types"].items())}

### By Source
{chr(10).join(f"- **{k}**: {v:,}" for k, v in stats["sources"].items())}

## Schema

Each task contains:

```python
{{
    "id": "food_preparation/cooking/boiling/boil_water",  # Hierarchical ID
    "name": "boil water",
    "node_type": "subtask",  # domain | task | subtask | atomic
    "parent_id": "food_preparation/cooking/boiling",
    "children_ids": ["...", "..."],

    # Completion criteria (key for robot execution)
    "precondition": "Water in kettle. Kettle on heat source.",
    "postcondition": "Water at 100C with visible bubbles.",
    "invariants": "Kettle remains upright. No spillage.",

    # Embodiment requirements
    "physical_requirements": "...",
    "sensing_requirements": "...",
    "cognitive_requirements": "...",

    # Metadata
    "sources": ["onet", "llm_generated"],
    "is_atomic": false,
    "is_leaf": false,
    "depth": 4,
}}
```

## Usage

```python
from datasets import load_dataset

# Load the dataset
dataset = load_dataset("{repo_id}")

# Get all atomic actions
atomic_actions = dataset["full"].filter(lambda x: x["is_atomic"])
print(f"{{len(atomic_actions):,}} atomic actions")

# Get tasks with completion criteria
with_criteria = dataset["full"].filter(lambda x: x["precondition"] != "")

# Build hierarchy
tasks_by_id = {{t["id"]: t for t in dataset["full"]}}
def get_children(task_id):
    task = tasks_by_id.get(task_id)
    if not task:
        return []
    return [tasks_by_id[cid] for cid in task["children_ids"] if cid in tasks_by_id]
```

## Citation

```bibtex
@misc{{taskpedia2025,
    title={{TASKPEDIA: A Hierarchical Taxonomy of Human Tasks for Embodied AI}},
    author={{Sentient-X}},
    year={{2025}},
    howpublished={{\\url{{https://huggingface.co/datasets/{repo_id}}}}}
}}
```

## License

Apache 2.0
"""


def upload_to_huggingface(
    task_dir: Path,
    repo_id: str,
    private: bool = True,
    token: str | None = None,
):
    """Upload task hierarchy to HuggingFace."""

    print(f"Loading tasks from {task_dir}...")
    tasks = load_task_hierarchy(task_dir)
    print(f"Loaded {len(tasks):,} tasks")

    if not tasks:
        print("No tasks found!")
        return

    # Compute stats
    print("Computing statistics...")
    stats = compute_stats(tasks)
    print(f"  Total: {stats['total_tasks']:,}")
    print(f"  Atomic: {stats['atomic_tasks']:,}")
    print(f"  With completion criteria: {stats['with_completion_criteria']:,}")

    # Create dataset
    print("Creating HuggingFace dataset...")
    dataset_dict = create_dataset(tasks)
    print(f"  Dataset size: {len(dataset_dict['full']):,} rows")

    # Generate README
    readme_content = generate_readme(stats, repo_id)

    # Create repo first
    api = HfApi(token=token)

    print(f"Creating dataset repo: {repo_id} (private={private})...")
    try:
        repo_url = api.create_repo(
            repo_id=repo_id,
            repo_type="dataset",
            private=private,
            exist_ok=True,
        )
        print(f"Repo ready: {repo_url}")
    except Exception as e:
        print(f"Error creating repo: {e}")
        print("\nMake sure:")
        print("  1. You're logged in: huggingface-cli login")
        print("  2. Your token has write permissions")
        print(f"  3. You have access to the org in: {repo_id}")
        raise

    # Push dataset (repo already exists, so this just uploads)
    print(f"Uploading dataset to {repo_id}...")
    dataset_dict.push_to_hub(
        repo_id=repo_id,
        private=private,
        token=token,
        create_pr=False,
    )

    # Upload README
    print("Uploading README...")
    api.upload_file(
        path_or_fileobj=readme_content.encode(),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="dataset",
    )

    print(f"\nUploaded successfully!")
    print(f"  URL: https://huggingface.co/datasets/{repo_id}")
    print(f"  Private: {private}")
    print(f"  Tasks: {len(tasks):,}")


def main():
    parser = argparse.ArgumentParser(description="Upload TASKPEDIA to HuggingFace")
    parser.add_argument(
        "--task-dir",
        type=Path,
        default=Path("./task_hierarchy"),
        help="Path to task hierarchy directory",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="Sentient-x/taskpedia",
        help="HuggingFace repo ID (e.g., org/dataset-name)",
    )
    parser.add_argument(
        "--public",
        action="store_true",
        help="Make dataset public (default: private)",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="HuggingFace token (or use HF_TOKEN env var)",
    )

    args = parser.parse_args()

    upload_to_huggingface(
        task_dir=args.task_dir,
        repo_id=args.repo,
        private=not args.public,
        token=args.token,
    )


if __name__ == "__main__":
    main()
