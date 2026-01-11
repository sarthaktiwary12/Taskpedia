#!/usr/bin/env python3
"""
CLI for TASKPEDIA - Hierarchical Task Decomposition.

Usage:
    # Bootstrap from seed data (O*NET + Life Activities)
    taskpedia bootstrap -o ./tasks

    # Generate synthetic tasks using LLM
    taskpedia generate -o ./tasks --max-tasks 1000

    # View the hierarchy
    taskpedia tree -o ./tasks

    # Statistics
    taskpedia stats -o ./tasks

    # Search for tasks
    taskpedia search "cook" -o ./tasks

    # Export to JSONL
    taskpedia export -o ./tasks --format jsonl

    # Show taxonomy
    taskpedia taxonomy
"""

import argparse
import json
import sys
from pathlib import Path


def cmd_bootstrap(args):
    """Bootstrap the task hierarchy from seed data (auto-downloads O*NET)."""
    from taskpedia.decompose import quick_bootstrap

    print(f"Bootstrapping task hierarchy to: {args.output}")
    print()

    graph = quick_bootstrap(args.output)

    print()
    print("=" * 60)
    print("BOOTSTRAP COMPLETE")
    print("=" * 60)

    stats = graph.get_stats()
    print(f"Total nodes:    {stats['total_nodes']:,}")
    print(f"Domains:        {stats['domains']}")
    print(f"Max depth:      {stats['max_depth']}")
    print(f"Leaf nodes:     {stats['leaf_count']:,}")


def cmd_generate(args):
    """Generate synthetic tasks using LLM."""
    from taskpedia.generate import GenerationConfig, TaskGenerator

    output_path = Path(args.output)

    # Check if bootstrapped
    if not output_path.exists():
        print(f"Error: {output_path} does not exist.")
        print("Run 'taskpedia bootstrap' first to create seed hierarchy.")
        sys.exit(1)

    config = GenerationConfig(
        output_dir=output_path,
        model=args.model,
        max_tasks=args.max_tasks,
        num_workers=args.workers,
        rpm_limit=args.rpm,
    )

    generator = TaskGenerator(config=config)
    stats = generator.run(
        max_tasks=args.max_tasks,
        expand_domains=not args.no_expand,
    )

    return stats


def cmd_tree(args):
    """Display the task hierarchy as a tree."""
    from taskpedia.hierarchy import TaskGraph

    output_path = Path(args.output)

    if not output_path.exists():
        print(f"Error: {output_path} does not exist. Run 'bootstrap' first.")
        sys.exit(1)

    graph = TaskGraph(output_path)

    print(f"Task Hierarchy (max depth: {args.depth})")
    print("=" * 60)
    print()
    print(graph.visualize_tree(max_depth=args.depth))


def cmd_stats(args):
    """Show statistics about the task hierarchy."""
    from taskpedia.hierarchy import NodeType, TaskGraph
    from taskpedia.seeds.taxonomy import LifeDomain

    output_path = Path(args.output)

    if not output_path.exists():
        print(f"Error: {output_path} does not exist. Run 'bootstrap' first.")
        sys.exit(1)

    graph = TaskGraph(output_path)
    stats = graph.get_stats()

    print("Task Hierarchy Statistics")
    print("=" * 60)
    print()
    print(f"Total nodes:    {stats['total_nodes']:,}")
    print(f"Domains:        {stats['domains']}")
    print(f"Max depth:      {stats['max_depth']}")
    print(f"Average depth:  {stats['avg_depth']:.2f}")
    print(f"Leaf nodes:     {stats['leaf_count']:,}")
    print()
    print("By node type:")
    for node_type, count in stats["by_type"].items():
        pct = count / stats["total_nodes"] * 100 if stats["total_nodes"] > 0 else 0
        print(f"  {node_type:12} {count:6,} ({pct:.1f}%)")


def cmd_search(args):
    """Search for tasks in the hierarchy."""
    from taskpedia.hierarchy import TaskGraph

    output_path = Path(args.output)

    if not output_path.exists():
        print(f"Error: {output_path} does not exist.")
        sys.exit(1)

    graph = TaskGraph(output_path)
    query = args.query.lower()

    matches = []
    for node in graph.iter_nodes():
        if query in node.name.lower():
            matches.append(node)

    print(f"Found {len(matches)} matches for '{args.query}':")
    print()

    for node in matches[: args.limit]:
        ancestors = graph.get_ancestors(node.id)
        path = " > ".join([a.name for a in reversed(ancestors)] + [node.name])
        print(f"  [{node.node_type.value}] {path}")
        if node.description:
            desc = node.description[:80] + "..." if len(node.description) > 80 else node.description
            print(f"    {desc}")
        print()


def cmd_export(args):
    """Export the hierarchy to various formats."""
    from taskpedia.hierarchy import TaskGraph

    output_path = Path(args.output)

    if not output_path.exists():
        print(f"Error: {output_path} does not exist. Run 'bootstrap' first.")
        sys.exit(1)

    graph = TaskGraph(output_path)
    export_path = Path(args.file) if args.file else output_path / "export.jsonl"

    if args.format == "jsonl":
        graph.export_flat(export_path)
        print(f"Exported {graph.get_stats()['total_nodes']:,} nodes to: {export_path}")

    elif args.format == "tree":
        tree_path = export_path.with_suffix(".txt")
        with open(tree_path, "w") as f:
            f.write(graph.visualize_tree(max_depth=10))
        print(f"Exported tree to: {tree_path}")

    elif args.format == "json":

        def node_to_nested(node_id):
            node = graph.get_node(node_id)
            if not node:
                return None
            data = node.to_dict()
            children = graph.get_children(node_id)
            if children:
                data["children"] = [node_to_nested(c.id) for c in children]
            return data

        roots = [n for n in graph.iter_nodes() if n.parent_id is None]
        nested = [node_to_nested(r.id) for r in roots]

        json_path = export_path.with_suffix(".json")
        with open(json_path, "w") as f:
            json.dump(nested, f, indent=2)
        print(f"Exported nested JSON to: {json_path}")


def cmd_taxonomy(args):
    """Show the full taxonomy."""
    from taskpedia.seeds.taxonomy import print_taxonomy_summary

    print_taxonomy_summary()


def cmd_cache_stats(args):
    """Show LLM cache statistics."""
    from diskcache import Cache

    cache_dir = Path("./.taskpedia_cache")
    if not cache_dir.exists():
        print("No cache found.")
        return

    cache = Cache(str(cache_dir))
    print("LLM Response Cache")
    print("=" * 60)
    print(f"Entries:  {len(cache):,}")
    print(f"Size:     {cache.volume() / 1024 / 1024:.1f} MB")


def cmd_cache_clear(args):
    """Clear the LLM cache."""
    import shutil

    from diskcache import Cache

    cache_dir = Path("./.taskpedia_cache")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print("Cache cleared.")
    else:
        print("No cache to clear.")


def add_output_arg(parser):
    """Add the common -o/--output argument."""
    parser.add_argument(
        "-o",
        "--output",
        default="./task_hierarchy",
        help="Output directory for the task hierarchy (default: ./task_hierarchy)",
    )


def main():
    parser = argparse.ArgumentParser(
        description="TASKPEDIA - Hierarchical Task Decomposition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Bootstrap command
    boot_parser = subparsers.add_parser(
        "bootstrap",
        help="Bootstrap hierarchy from O*NET + Life Activities (auto-downloads)",
    )
    add_output_arg(boot_parser)
    boot_parser.set_defaults(func=cmd_bootstrap)

    # Generate command
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate synthetic tasks using LLM",
    )
    add_output_arg(gen_parser)
    gen_parser.add_argument(
        "-n",
        "--max-tasks",
        type=int,
        default=1000,
        help="Maximum tasks to generate (default: 1000)",
    )
    gen_parser.add_argument(
        "--model",
        default="models/gemini-2.5-flash",
        help="LLM model to use (default: models/gemini-2.5-flash)",
    )
    gen_parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)",
    )
    gen_parser.add_argument(
        "--rpm",
        type=int,
        default=60,
        help="Rate limit: requests per minute (default: 60)",
    )
    gen_parser.add_argument(
        "--no-expand",
        action="store_true",
        help="Don't expand domains with new tasks, only decompose",
    )
    gen_parser.set_defaults(func=cmd_generate)

    # Tree command
    tree_parser = subparsers.add_parser(
        "tree",
        help="Display the hierarchy as a tree",
    )
    add_output_arg(tree_parser)
    tree_parser.add_argument(
        "-d",
        "--depth",
        type=int,
        default=3,
        help="Maximum depth to display (default: 3)",
    )
    tree_parser.set_defaults(func=cmd_tree)

    # Stats command
    stats_parser = subparsers.add_parser(
        "stats",
        help="Show hierarchy statistics",
    )
    add_output_arg(stats_parser)
    stats_parser.set_defaults(func=cmd_stats)

    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search for tasks",
    )
    add_output_arg(search_parser)
    search_parser.add_argument(
        "query",
        help="Search query",
    )
    search_parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=20,
        help="Maximum results (default: 20)",
    )
    search_parser.set_defaults(func=cmd_search)

    # Export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export hierarchy to file",
    )
    add_output_arg(export_parser)
    export_parser.add_argument(
        "-f",
        "--format",
        choices=["jsonl", "json", "tree"],
        default="jsonl",
        help="Export format (default: jsonl)",
    )
    export_parser.add_argument(
        "--file",
        help="Output file path",
    )
    export_parser.set_defaults(func=cmd_export)

    # Taxonomy command
    tax_parser = subparsers.add_parser(
        "taxonomy",
        help="Show the full taxonomy (23 work + 12 life domains)",
    )
    tax_parser.set_defaults(func=cmd_taxonomy)

    # Cache commands
    cache_stats_parser = subparsers.add_parser(
        "cache-stats",
        help="Show LLM cache statistics",
    )
    cache_stats_parser.set_defaults(func=cmd_cache_stats)

    cache_clear_parser = subparsers.add_parser(
        "cache-clear",
        help="Clear the LLM cache",
    )
    cache_clear_parser.set_defaults(func=cmd_cache_clear)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
