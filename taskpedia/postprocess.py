"""
Post-processing utilities for cleaning up generated task data.

Usage:
    # Analyze current data quality
    taskpedia postprocess analyze

    # Remove bad nodes (generic templates, Step N descriptions)
    taskpedia postprocess clean --dry-run
    taskpedia postprocess clean

    # Reset nodes for regeneration (mark as not processed)
    taskpedia postprocess reset-bad
"""

import re
from collections import Counter
from pathlib import Path

import yaml

# Import validation from generator
from taskpedia.generate_fast import (
    ATOMIC_VERBS,
    GENERIC_NOUNS,
    GENERIC_VERBS,
    is_generic_template,
    is_valid_atomic,
)


def analyze_quality(task_dir: Path) -> dict:
    """Analyze the quality of generated tasks."""

    stats = {
        "total": 0,
        "llm_generated": 0,
        "generic_step_desc": 0,
        "generic_template": 0,
        "valid_atomic": 0,
        "invalid_atomic": 0,
        "empty_description": 0,
        "good_quality": 0,
    }

    bad_examples = []
    good_examples = []

    for yaml_path in task_dir.glob("**/*.yaml"):
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            if not data or "id" not in data:
                continue

            stats["total"] += 1

            sources = data.get("sources", [])
            if "llm_generated" in sources:
                stats["llm_generated"] += 1
            else:
                continue  # Only analyze LLM-generated

            name = data.get("name", "")
            description = data.get("description", "")
            node_type = data.get("node_type", "")

            # Check for issues
            is_bad = False

            if not description:
                stats["empty_description"] += 1
                is_bad = True

            if description and re.match(r"^Step\s+\d+\s*:", description, re.I):
                stats["generic_step_desc"] += 1
                is_bad = True

            if is_generic_template(name, description):
                stats["generic_template"] += 1
                is_bad = True

            if node_type == "atomic":
                if is_valid_atomic(name):
                    stats["valid_atomic"] += 1
                else:
                    stats["invalid_atomic"] += 1
                    is_bad = True

            if is_bad:
                bad_examples.append(
                    {
                        "name": name,
                        "desc": description[:80] if description else "(empty)",
                        "type": node_type,
                        "path": str(yaml_path),
                    }
                )
            else:
                stats["good_quality"] += 1
                if len(good_examples) < 10:
                    good_examples.append(
                        {
                            "name": name,
                            "desc": description[:80] if description else "",
                            "type": node_type,
                        }
                    )

        except Exception as e:
            pass

    return {
        "stats": stats,
        "bad_examples": bad_examples,
        "good_examples": good_examples,
    }


def find_bad_nodes(task_dir: Path) -> list[Path]:
    """Find all nodes that should be removed or regenerated."""

    bad_paths = []

    for yaml_path in task_dir.glob("**/*.yaml"):
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            if not data or "id" not in data:
                continue

            sources = data.get("sources", [])
            if "llm_generated" not in sources:
                continue  # Don't touch seed data

            name = data.get("name", "")
            description = data.get("description", "")
            node_type = data.get("node_type", "")

            # Check for bad patterns
            is_bad = False

            # Generic "Step N:" description
            if description and re.match(r"^Step\s+\d+\s*:", description, re.I):
                is_bad = True

            # Generic template pattern
            if is_generic_template(name, description):
                is_bad = True

            # Invalid atomic (not a real primitive)
            if node_type == "atomic" and not is_valid_atomic(name):
                is_bad = True

            if is_bad:
                bad_paths.append(yaml_path)

        except Exception:
            pass

    return bad_paths


def remove_nodes(paths: list[Path], dry_run: bool = True) -> int:
    """Remove bad nodes from disk."""

    count = 0
    for path in paths:
        if dry_run:
            print(f"  [dry-run] Would remove: {path}")
        else:
            try:
                path.unlink()
                count += 1
                # Also try to remove empty parent dirs
                parent = path.parent
                if parent.name != "_meta.yaml" and not any(parent.iterdir()):
                    parent.rmdir()
            except Exception as e:
                print(f"  [error] Could not remove {path}: {e}")

    return count if not dry_run else len(paths)


def reset_parent_children(task_dir: Path, removed_ids: set[str]):
    """Update parent nodes to remove references to deleted children."""

    for yaml_path in task_dir.glob("**/*.yaml"):
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            if not data or "id" not in data:
                continue

            children = data.get("children_ids", [])
            if not children:
                continue

            # Filter out removed children
            new_children = [c for c in children if c not in removed_ids]
            if len(new_children) != len(children):
                data["children_ids"] = new_children
                with open(yaml_path, "w") as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        except Exception:
            pass


def rebuild_manifest(task_dir: Path):
    """Rebuild the manifest from YAML files."""
    import json

    nodes = {}
    for yaml_path in task_dir.glob("**/*.yaml"):
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            if data and "id" in data:
                nodes[data["id"]] = data
        except Exception:
            pass

    manifest = {
        "version": "1.0",
        "node_count": len(nodes),
        "nodes": nodes,
    }

    manifest_path = task_dir / "_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return len(nodes)


def cmd_analyze(args):
    """Analyze data quality."""
    task_dir = Path(args.output)
    if not task_dir.exists():
        print(f"Error: {task_dir} not found")
        return

    print(f"Analyzing {task_dir}...\n")
    result = analyze_quality(task_dir)
    stats = result["stats"]

    print("Quality Analysis")
    print("=" * 50)
    print(f"  Total nodes:          {stats['total']:>10,}")
    print(f"  LLM-generated:        {stats['llm_generated']:>10,}")
    print()
    print("Issues found:")
    print(f"  Generic 'Step N' desc: {stats['generic_step_desc']:>9,}")
    print(f"  Generic template:      {stats['generic_template']:>9,}")
    print(f"  Invalid atomic:        {stats['invalid_atomic']:>9,}")
    print(f"  Empty description:     {stats['empty_description']:>9,}")
    print()
    print(f"  Good quality:          {stats['good_quality']:>9,}")
    print(f"  Valid atomic:          {stats['valid_atomic']:>9,}")

    if result["bad_examples"]:
        print("\nBad examples:")
        for ex in result["bad_examples"][:10]:
            print(f"  [{ex['type']}] {ex['name']}")
            print(f"       {ex['desc']}")

    if result["good_examples"]:
        print("\nGood examples:")
        for ex in result["good_examples"][:5]:
            print(f"  [{ex['type']}] {ex['name']}")
            if ex["desc"]:
                print(f"       {ex['desc']}")


def cmd_clean(args):
    """Remove bad nodes."""
    task_dir = Path(args.output)
    if not task_dir.exists():
        print(f"Error: {task_dir} not found")
        return

    print(f"Finding bad nodes in {task_dir}...")
    bad_paths = find_bad_nodes(task_dir)
    print(f"Found {len(bad_paths):,} bad nodes")

    if not bad_paths:
        print("Nothing to clean!")
        return

    if args.dry_run:
        print("\n[DRY RUN] Would remove:")
        for p in bad_paths[:20]:
            print(f"  {p}")
        if len(bad_paths) > 20:
            print(f"  ... and {len(bad_paths) - 20} more")
        print(f"\nRun without --dry-run to actually remove")
    else:
        print(f"\nRemoving {len(bad_paths):,} bad nodes...")

        # Collect IDs for parent update
        removed_ids = set()
        for p in bad_paths:
            try:
                with open(p) as f:
                    data = yaml.safe_load(f)
                if data and "id" in data:
                    removed_ids.add(data["id"])
            except:
                pass

        # Remove files
        count = remove_nodes(bad_paths, dry_run=False)
        print(f"Removed {count:,} files")

        # Update parents
        print("Updating parent references...")
        reset_parent_children(task_dir, removed_ids)

        # Rebuild manifest
        print("Rebuilding manifest...")
        node_count = rebuild_manifest(task_dir)
        print(f"Manifest rebuilt with {node_count:,} nodes")

        print("\nDone!")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Post-process task data")
    parser.add_argument("-o", "--output", default="./task_hierarchy", help="Task directory")

    subparsers = parser.add_subparsers(dest="command")

    # Analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analyze data quality")
    analyze_parser.set_defaults(func=cmd_analyze)

    # Clean
    clean_parser = subparsers.add_parser("clean", help="Remove bad nodes")
    clean_parser.add_argument("--dry-run", action="store_true", help="Don't actually remove")
    clean_parser.set_defaults(func=cmd_clean)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
