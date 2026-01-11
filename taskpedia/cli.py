#!/usr/bin/env python3
"""
TASKPEDIA CLI - Hierarchical Task Decomposition for Embodied AI.

Commands are organized into groups:
    taskpedia init          Initialize/bootstrap the hierarchy
    taskpedia generate      Generate tasks with LLM
    taskpedia show          View hierarchy (tree, stats, search)
    taskpedia export        Export to various formats
    taskpedia upload        Upload to HuggingFace
    taskpedia cache         Manage LLM cache
"""

import argparse
import sys
from pathlib import Path

# Default paths
DEFAULT_OUTPUT = "./task_hierarchy"


def cmd_init(args):
    """Initialize the task hierarchy from seed data."""
    from taskpedia.decompose import quick_bootstrap

    print(f"Initializing task hierarchy: {args.output}")
    print()

    graph = quick_bootstrap(args.output)

    print()
    print("=" * 50)
    print("INITIALIZATION COMPLETE")
    print("=" * 50)

    stats = graph.get_stats()
    print(f"  Nodes:    {stats['total_nodes']:,}")
    print(f"  Domains:  {stats['domains']}")
    print(f"  Depth:    {stats['max_depth']}")
    print()
    print("Next: Run 'taskpedia generate' to expand with LLM")


def cmd_generate(args):
    """Generate tasks using LLM decomposition."""
    from taskpedia.generate_fast import FastGenConfig, run

    output_path = Path(args.output)

    if not output_path.exists():
        print(f"Error: {output_path} does not exist.")
        print("Run 'taskpedia init' first.")
        sys.exit(1)

    config = FastGenConfig(
        output_dir=output_path,
        model=args.model,
        max_tasks=args.max_tasks,
        max_workers=args.workers,
        queue_size=args.queue_size,
        rpm_limit=args.rpm,
        mock=args.mock,
        tui=not args.no_tui,
    )

    run(config)


def cmd_show_tree(args):
    """Display hierarchy as a tree."""
    from taskpedia.hierarchy import TaskGraph

    output_path = Path(args.output)
    if not output_path.exists():
        print(f"Error: {output_path} not found. Run 'taskpedia init' first.")
        sys.exit(1)

    graph = TaskGraph(output_path)
    print(graph.visualize_tree(max_depth=args.depth))


def cmd_show_stats(args):
    """Show hierarchy statistics."""
    from taskpedia.hierarchy import TaskGraph

    output_path = Path(args.output)
    if not output_path.exists():
        print(f"Error: {output_path} not found. Run 'taskpedia init' first.")
        sys.exit(1)

    graph = TaskGraph(output_path)
    stats = graph.get_stats()

    print()
    print("TASKPEDIA Statistics")
    print("=" * 40)
    print(f"  Total nodes:   {stats['total_nodes']:>10,}")
    print(f"  Domains:       {stats['domains']:>10}")
    print(f"  Max depth:     {stats['max_depth']:>10}")
    print(f"  Avg depth:     {stats['avg_depth']:>10.1f}")
    print(f"  Leaf nodes:    {stats['leaf_count']:>10,}")
    print()
    print("By Type:")
    for node_type, count in stats["by_type"].items():
        pct = count / stats["total_nodes"] * 100 if stats["total_nodes"] > 0 else 0
        print(f"  {node_type:12} {count:>8,} ({pct:>5.1f}%)")
    print()


def cmd_show_search(args):
    """Search for tasks."""
    from taskpedia.hierarchy import TaskGraph

    output_path = Path(args.output)
    if not output_path.exists():
        print(f"Error: {output_path} not found.")
        sys.exit(1)

    graph = TaskGraph(output_path)
    query = args.query.lower()

    matches = [n for n in graph.iter_nodes() if query in n.name.lower()]

    print(f"\nFound {len(matches)} matches for '{args.query}':\n")

    for node in matches[: args.limit]:
        ancestors = graph.get_ancestors(node.id)
        path = " > ".join([a.name for a in reversed(ancestors)] + [node.name])
        print(f"  [{node.node_type.value}] {path}")
        if node.description:
            desc = node.description[:70] + "..." if len(node.description) > 70 else node.description
            print(f"      {desc}")
    print()


def cmd_export(args):
    """Export hierarchy to file."""
    import json
    from taskpedia.hierarchy import TaskGraph

    output_path = Path(args.output)
    if not output_path.exists():
        print(f"Error: {output_path} not found.")
        sys.exit(1)

    graph = TaskGraph(output_path)
    export_path = Path(args.file) if args.file else output_path / f"export.{args.format}"

    if args.format == "jsonl":
        graph.export_flat(export_path)
    elif args.format == "tree":
        export_path = export_path.with_suffix(".txt")
        with open(export_path, "w") as f:
            f.write(graph.visualize_tree(max_depth=10))
    elif args.format == "json":

        def to_nested(node_id):
            node = graph.get_node(node_id)
            if not node:
                return None
            data = node.to_dict()
            children = graph.get_children(node_id)
            if children:
                data["children"] = [to_nested(c.id) for c in children]
            return data

        roots = [n for n in graph.iter_nodes() if n.parent_id is None]
        nested = [to_nested(r.id) for r in roots]

        export_path = export_path.with_suffix(".json")
        with open(export_path, "w") as f:
            json.dump(nested, f, indent=2)

    print(f"Exported {graph.get_stats()['total_nodes']:,} nodes to: {export_path}")


def cmd_upload(args):
    """Upload to HuggingFace."""
    from datetime import datetime
    import yaml

    try:
        from datasets import Dataset, DatasetDict, Features, Sequence, Value
        from huggingface_hub import HfApi
    except ImportError:
        print("Error: Upload requires 'datasets' and 'huggingface_hub' packages.")
        print("Install with: pip install datasets huggingface_hub")
        sys.exit(1)

    task_dir = Path(args.output)
    if not task_dir.exists():
        print(f"Error: {task_dir} not found.")
        sys.exit(1)

    # Load tasks
    print(f"Loading tasks from {task_dir}...")
    tasks = []
    for yaml_path in task_dir.glob("**/*.yaml"):
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            if not data or "id" not in data:
                continue

            completion = data.get("completion", {}) or {}
            tasks.append(
                {
                    "id": data.get("id", ""),
                    "name": data.get("name", ""),
                    "node_type": data.get("node_type", ""),
                    "parent_id": data.get("parent_id", "") or "",
                    "children_ids": data.get("children_ids", []) or [],
                    "description": data.get("description", "") or "",
                    "precondition": completion.get("precondition", "") or "",
                    "postcondition": completion.get("postcondition", "") or "",
                    "invariants": completion.get("invariants", "") or "",
                    "physical_requirements": data.get("physical_requirements", "") or "",
                    "sensing_requirements": data.get("sensing_requirements", "") or "",
                    "cognitive_requirements": data.get("cognitive_requirements", "") or "",
                    "language": data.get("language", "en"),
                    "aliases": data.get("aliases", []) or [],
                    "tags": data.get("tags", []) or [],
                    "sources": data.get("sources", []) or [],
                    "confidence": float(data.get("confidence", 1.0)),
                    "depth": len(data.get("id", "").split("/")),
                    "is_leaf": len(data.get("children_ids", []) or []) == 0,
                    "is_atomic": data.get("node_type") == "atomic",
                }
            )
        except Exception as e:
            pass

    if not tasks:
        print("No tasks found!")
        sys.exit(1)

    print(f"Loaded {len(tasks):,} tasks")

    # Create dataset
    features = Features(
        {
            "id": Value("string"),
            "name": Value("string"),
            "node_type": Value("string"),
            "parent_id": Value("string"),
            "children_ids": Sequence(Value("string")),
            "description": Value("string"),
            "precondition": Value("string"),
            "postcondition": Value("string"),
            "invariants": Value("string"),
            "physical_requirements": Value("string"),
            "sensing_requirements": Value("string"),
            "cognitive_requirements": Value("string"),
            "language": Value("string"),
            "aliases": Sequence(Value("string")),
            "tags": Sequence(Value("string")),
            "sources": Sequence(Value("string")),
            "confidence": Value("float32"),
            "depth": Value("int32"),
            "is_leaf": Value("bool"),
            "is_atomic": Value("bool"),
        }
    )

    dataset = Dataset.from_list(tasks, features=features)
    dataset_dict = DatasetDict({"full": dataset})

    # Stats for README
    atomic_count = sum(1 for t in tasks if t["is_atomic"])
    leaf_count = sum(1 for t in tasks if t["is_leaf"])
    from collections import Counter

    node_types = Counter(t["node_type"] for t in tasks)
    sources = Counter(s for t in tasks for s in t["sources"])

    # Upload
    repo_id = args.repo
    private = not args.public

    api = HfApi()
    print(f"Creating repo: {repo_id} (private={private})...")

    try:
        api.create_repo(repo_id=repo_id, repo_type="dataset", private=private, exist_ok=True)
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you're logged in: huggingface-cli login")
        sys.exit(1)

    print("Uploading dataset...")
    dataset_dict.push_to_hub(repo_id=repo_id, private=private)

    # README
    readme = f"""---
license: apache-2.0
task_categories:
  - robotics
tags:
  - embodied-ai
  - task-decomposition
  - VLA
  - VLN
---

# TASKPEDIA

Hierarchical task decomposition for embodied AI. {len(tasks):,} tasks, {atomic_count:,} atomic actions.

## Stats
- Total: {len(tasks):,}
- Atomic: {atomic_count:,}
- Leaf: {leaf_count:,}

## Usage
```python
from datasets import load_dataset
ds = load_dataset("{repo_id}")
atomic = ds["full"].filter(lambda x: x["is_atomic"])
```
"""

    api.upload_file(
        path_or_fileobj=readme.encode(),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="dataset",
    )

    print(f"\nUploaded to: https://huggingface.co/datasets/{repo_id}")


def cmd_qa_analyze(args):
    """Analyze data quality."""
    from taskpedia.postprocess import analyze_quality

    task_dir = Path(args.output)
    if not task_dir.exists():
        print(f"Error: {task_dir} not found")
        sys.exit(1)

    print(f"Analyzing {task_dir}...\n")
    result = analyze_quality(task_dir)
    stats = result["stats"]

    print("Quality Analysis")
    print("=" * 50)
    print(f"  Total nodes:           {stats['total']:>10,}")
    print(f"  LLM-generated:         {stats['llm_generated']:>10,}")
    print()
    print("Issues found:")
    print(f"  Generic 'Step N' desc: {stats['generic_step_desc']:>10,}")
    print(f"  Generic template:      {stats['generic_template']:>10,}")
    print(f"  Invalid atomic:        {stats['invalid_atomic']:>10,}")
    print(f"  Empty description:     {stats['empty_description']:>10,}")
    print()
    print(f"  Good quality:          {stats['good_quality']:>10,}")
    print(f"  Valid atomic:          {stats['valid_atomic']:>10,}")

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


def cmd_qa_clean(args):
    """Remove bad nodes."""
    from taskpedia.postprocess import (
        find_bad_nodes,
        remove_nodes,
        reset_parent_children,
        rebuild_manifest,
    )
    import yaml

    task_dir = Path(args.output)
    if not task_dir.exists():
        print(f"Error: {task_dir} not found")
        sys.exit(1)

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


def cmd_qa_verbs(args):
    """Analyze verb taxonomy."""
    from taskpedia.postprocess import (
        get_verb_statistics,
        analyze_verb_stems,
        check_domain_coverage,
    )

    print("Verb Taxonomy Analysis")
    print("=" * 60)

    stats = get_verb_statistics()
    print(f"\nTotal ATOMIC_VERBS:    {stats['total_atomic']:,}")
    print(f"Unique ATOMIC_VERBS:   {stats['unique_atomic']:,}")
    print(f"Total COGNITIVE_VERBS: {stats['total_cognitive']:,}")
    print(f"Unique COGNITIVE_VERBS:{stats['unique_cognitive']:,}")

    # Duplicates
    dups = stats["duplicates"]
    if dups:
        print(f"\nDuplicates ({len(dups)}):")
        for v, count in sorted(dups.items(), key=lambda x: -x[1])[:15]:
            print(f"  {v}: {count}x")
        if len(dups) > 15:
            print(f"  ... and {len(dups) - 15} more")
    else:
        print("\nNo duplicates found!")

    # Verb stems
    stems = analyze_verb_stems()
    print(f"\nVerb stems with 3+ variants: {len(stems)}")
    top_stems = sorted(stems.items(), key=lambda x: -len(x[1]))[:10]
    for stem, variants in top_stems:
        print(f"  {stem}: {len(variants)} variants")

    # Domain coverage
    print("\nDomain Coverage:")
    coverage = check_domain_coverage()
    for domain, data in coverage.items():
        found = len(data["found"])
        total = len(data["expected"])
        missing = data["missing"]
        status = "✓" if not missing else "△"
        print(f"  {status} {domain}: {found}/{total}")
        if missing and args.verbose:
            print(f"      Missing: {', '.join(missing)}")


def cmd_qa_problems(args):
    """Show problematic verbs."""
    from taskpedia.postprocess import find_problematic_verbs, find_ambiguous_verbs

    print("Problematic Verbs in ATOMIC_VERBS")
    print("=" * 60)

    problems = find_problematic_verbs()
    if not problems:
        print("\nNo problematic verbs found!")
    else:
        for issue_type, verbs in problems.items():
            print(f"\n{issue_type.replace('_', ' ').title()} ({len(verbs)}):")
            for v in sorted(verbs)[:20]:
                print(f"  - {v}")
            if len(verbs) > 20:
                print(f"  ... and {len(verbs) - 20} more")

    # Ambiguous verbs
    ambiguous = find_ambiguous_verbs()
    if ambiguous:
        print(f"\nAmbiguous single words ({len(ambiguous)}):")
        for word, disambiguated in sorted(ambiguous.items())[:15]:
            if disambiguated:
                print(f"  {word} -> has {len(disambiguated)} disambiguated versions")
            else:
                print(f"  {word} -> NEEDS DISAMBIGUATION")
        if len(ambiguous) > 15:
            print(f"  ... and {len(ambiguous) - 15} more")


def cmd_qa_coverage(args):
    """Show detailed domain coverage."""
    from taskpedia.postprocess import check_domain_coverage

    print("Domain Coverage Analysis")
    print("=" * 60)

    coverage = check_domain_coverage()

    for domain, data in sorted(coverage.items()):
        found = data["found"]
        missing = data["missing"]
        total = len(data["expected"])
        pct = (len(found) / total * 100) if total > 0 else 0

        print(f"\n{domain} ({len(found)}/{total} = {pct:.0f}%)")
        print("-" * 40)

        if found:
            print(f"  Found: {', '.join(sorted(found))}")
        if missing:
            print(f"  MISSING: {', '.join(sorted(missing))}")


def cmd_qa_test(args):
    """Run all data quality tests."""
    from taskpedia.postprocess import (
        run_verb_taxonomy_tests,
        run_domain_coverage_tests,
        run_comprehensive_domain_tests,
        run_generated_data_tests,
    )

    print("Running Data Quality Tests")
    print("=" * 60)

    task_dir = Path(args.output)

    # Run verb taxonomy tests
    print("\n[1] Verb Taxonomy Tests")
    print("-" * 40)
    verb_results = run_verb_taxonomy_tests(args.verbose)
    for status, msg in verb_results["details"]:
        icon = "✓" if status == "PASS" else "△" if status == "WARN" else "✗"
        print(f"  {icon} {msg}")

    # Run domain coverage tests
    print("\n[2] Domain Coverage Tests")
    print("-" * 40)
    coverage_results = run_domain_coverage_tests(args.verbose)
    for status, msg in coverage_results["details"]:
        icon = "✓" if status == "PASS" else "△" if status == "WARN" else "✗"
        print(f"  {icon} {msg}")

    # Run comprehensive domain tests
    print("\n[3] Comprehensive Domain Tests")
    print("-" * 40)
    comprehensive_results = run_comprehensive_domain_tests(args.verbose)
    # Only show failures and warnings unless verbose
    shown = 0
    for status, msg in comprehensive_results["details"]:
        if status != "PASS" or args.verbose:
            icon = "✓" if status == "PASS" else "△" if status == "WARN" else "✗"
            print(f"  {icon} {msg}")
            shown += 1
    if shown == 0:
        print(f"  ✓ All {len(comprehensive_results['details'])} domain tests passed")

    # Run generated data tests if directory exists
    if task_dir.exists():
        print("\n[4] Generated Data Tests")
        print("-" * 40)
        data_results = run_generated_data_tests(task_dir, args.verbose)
        for status, msg in data_results["details"]:
            icon = "✓" if status == "PASS" else "△" if status == "WARN" else "✗"
            print(f"  {icon} {msg}")
    else:
        data_results = {"passed": 0, "failed": 0, "warnings": 0}
        print("\n[4] Generated Data Tests")
        print("-" * 40)
        print("  (skipped - no task directory)")

    # Summary
    total_passed = (
        verb_results["passed"]
        + coverage_results["passed"]
        + comprehensive_results["passed"]
        + data_results["passed"]
    )
    total_failed = (
        verb_results["failed"]
        + coverage_results["failed"]
        + comprehensive_results["failed"]
        + data_results["failed"]
    )
    total_warnings = (
        verb_results["warnings"]
        + coverage_results["warnings"]
        + comprehensive_results["warnings"]
        + data_results["warnings"]
    )

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Passed:   {total_passed}")
    print(f"  Warnings: {total_warnings}")
    print(f"  Failed:   {total_failed}")

    if total_failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total_failed} test(s) failed")
        return 1


def cmd_cache_stats(args):
    """Show cache statistics."""
    try:
        from diskcache import Cache
    except ImportError:
        print("diskcache not installed")
        return

    cache_dir = Path("./.taskpedia_cache")
    if not cache_dir.exists():
        print("No cache found.")
        return

    cache = Cache(str(cache_dir))
    entries = len(cache)
    size_mb = cache.volume() / 1024 / 1024

    print(f"\nLLM Response Cache: {cache_dir}")
    print("=" * 40)
    print(f"  Entries:     {entries:>10,}")
    print(f"  Size:        {size_mb:>10.1f} MB")

    if entries > 0:
        # Estimate savings (avg ~2K tokens per cached response at $0.30/1M output)
        estimated_savings = entries * 2000 * 0.30 / 1_000_000
        print(f"  Est. savings:   ${estimated_savings:>7.2f}")

    print()


def cmd_cache_clear(args):
    """Clear the cache."""
    import shutil

    cache_dir = Path("./.taskpedia_cache")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print("Cache cleared.")
    else:
        print("No cache to clear.")


def main():
    parser = argparse.ArgumentParser(
        prog="taskpedia",
        description="TASKPEDIA - Hierarchical Task Decomposition for Embodied AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  taskpedia init                    # Initialize from O*NET + Life Activities
  taskpedia generate -n 100000      # Generate 100K tasks with LLM
  taskpedia show stats              # View statistics
  taskpedia show tree               # View as tree
  taskpedia export --format jsonl   # Export to JSONL
  taskpedia upload --repo org/name  # Upload to HuggingFace
""",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Task hierarchy directory (default: {DEFAULT_OUTPUT})",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # ─── INIT ───────────────────────────────────────────────
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize hierarchy from seed data (O*NET + Life Activities)",
    )
    init_parser.set_defaults(func=cmd_init)

    # ─── GENERATE ───────────────────────────────────────────
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate tasks using LLM decomposition",
    )
    gen_parser.add_argument(
        "-n",
        "--max-tasks",
        type=int,
        default=10000,
        help="Max tasks to generate (default: 10000)",
    )
    gen_parser.add_argument(
        "--model",
        default="models/gemini-2.5-flash",
        help="LLM model (default: gemini-2.5-flash)",
    )
    gen_parser.add_argument(
        "--workers",
        type=int,
        default=64,
        help="Parallel workers (default: 64)",
    )
    gen_parser.add_argument(
        "--queue-size",
        type=int,
        default=1000,
        help="Work queue size (default: 1000)",
    )
    gen_parser.add_argument(
        "--rpm",
        type=int,
        default=1000,
        help="Rate limit RPM (default: 1000)",
    )
    gen_parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock LLM (no API calls)",
    )
    gen_parser.add_argument(
        "--no-tui",
        action="store_true",
        help="Disable TUI, use simple progress",
    )
    gen_parser.set_defaults(func=cmd_generate)

    # ─── SHOW (subcommands) ─────────────────────────────────
    show_parser = subparsers.add_parser(
        "show",
        help="View hierarchy (tree, stats, search)",
    )
    show_sub = show_parser.add_subparsers(dest="show_cmd", metavar="what")

    # show tree
    tree_parser = show_sub.add_parser("tree", help="Display as tree")
    tree_parser.add_argument(
        "-d",
        "--depth",
        type=int,
        default=3,
        help="Max depth (default: 3)",
    )
    tree_parser.set_defaults(func=cmd_show_tree)

    # show stats
    stats_parser = show_sub.add_parser("stats", help="Show statistics")
    stats_parser.set_defaults(func=cmd_show_stats)

    # show search
    search_parser = show_sub.add_parser("search", help="Search tasks")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=20,
        help="Max results (default: 20)",
    )
    search_parser.set_defaults(func=cmd_show_search)

    # ─── EXPORT ─────────────────────────────────────────────
    export_parser = subparsers.add_parser(
        "export",
        help="Export to file (jsonl, json, tree)",
    )
    export_parser.add_argument(
        "-f",
        "--format",
        choices=["jsonl", "json", "tree"],
        default="jsonl",
        help="Format (default: jsonl)",
    )
    export_parser.add_argument(
        "--file",
        help="Output file path",
    )
    export_parser.set_defaults(func=cmd_export)

    # ─── UPLOAD ─────────────────────────────────────────────
    upload_parser = subparsers.add_parser(
        "upload",
        help="Upload to HuggingFace",
    )
    upload_parser.add_argument(
        "--repo",
        default="Sentient-x/taskpedia",
        help="HuggingFace repo (default: Sentient-x/taskpedia)",
    )
    upload_parser.add_argument(
        "--public",
        action="store_true",
        help="Make public (default: private)",
    )
    upload_parser.set_defaults(func=cmd_upload)

    # ─── CACHE (subcommands) ────────────────────────────────
    cache_parser = subparsers.add_parser(
        "cache",
        help="Manage LLM cache",
    )
    cache_sub = cache_parser.add_subparsers(dest="cache_cmd", metavar="action")

    cache_stats = cache_sub.add_parser("stats", help="Show cache stats")
    cache_stats.set_defaults(func=cmd_cache_stats)

    cache_clear = cache_sub.add_parser("clear", help="Clear cache")
    cache_clear.set_defaults(func=cmd_cache_clear)

    # ─── QA (subcommands) ───────────────────────────────────
    qa_parser = subparsers.add_parser(
        "qa",
        help="Quality assurance (analyze, clean, verbs, problems, coverage)",
    )
    qa_sub = qa_parser.add_subparsers(dest="qa_cmd", metavar="action")

    # qa analyze
    qa_analyze = qa_sub.add_parser("analyze", help="Analyze generated data quality")
    qa_analyze.set_defaults(func=cmd_qa_analyze)

    # qa clean
    qa_clean = qa_sub.add_parser("clean", help="Remove bad nodes")
    qa_clean.add_argument("--dry-run", action="store_true", help="Preview without removing")
    qa_clean.set_defaults(func=cmd_qa_clean)

    # qa verbs
    qa_verbs = qa_sub.add_parser("verbs", help="Analyze verb taxonomy")
    qa_verbs.add_argument("-v", "--verbose", action="store_true", help="Show details")
    qa_verbs.set_defaults(func=cmd_qa_verbs)

    # qa problems
    qa_problems = qa_sub.add_parser("problems", help="Show problematic verbs")
    qa_problems.set_defaults(func=cmd_qa_problems)

    # qa coverage
    qa_coverage = qa_sub.add_parser("coverage", help="Show domain coverage")
    qa_coverage.set_defaults(func=cmd_qa_coverage)

    # qa test
    qa_test = qa_sub.add_parser("test", help="Run all data quality tests")
    qa_test.add_argument("-v", "--verbose", action="store_true", help="Show all details")
    qa_test.set_defaults(func=cmd_qa_test)

    # ─── PARSE & RUN ────────────────────────────────────────
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Handle subcommand groups
    if args.command == "show":
        if not args.show_cmd:
            show_parser.print_help()
            sys.exit(0)
    elif args.command == "cache":
        if not args.cache_cmd:
            cache_parser.print_help()
            sys.exit(0)
    elif args.command == "qa":
        if not args.qa_cmd:
            qa_parser.print_help()
            sys.exit(0)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
