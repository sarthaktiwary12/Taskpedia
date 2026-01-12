"""
Post-processing utilities for cleaning up generated task data.

Usage:
    # Analyze current data quality
    taskpedia qa analyze

    # Remove bad nodes (generic templates, Step N descriptions)
    taskpedia qa clean --dry-run
    taskpedia qa clean

    # Analyze verb coverage and find gaps
    taskpedia qa verbs

    # Find duplicates in ATOMIC_VERBS
    taskpedia qa duplicates

    # Check for ambiguous/problematic verbs
    taskpedia qa problems
"""

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

# Import from refactored modules
from taskpedia.data import (
    ATOMIC_VERBS,
    COGNITIVE_VERBS,
    GENERIC_NOUNS,
    GENERIC_VERBS,
    is_generic_template,
    is_valid_atomic,
)
from taskpedia.qa import (
    analyze_verb_duplicates,
    analyze_verb_stems,
    check_domain_coverage,
    find_ambiguous_verbs,
    find_problematic_verbs,
    get_verb_statistics,
    run_all_tests,
    run_comprehensive_domain_tests,
    run_domain_coverage_tests,
    run_generated_data_tests,
    run_verb_taxonomy_tests,
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


# ============================================================================
# CLI COMMANDS
# ============================================================================


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


def cmd_verbs(args):
    """Analyze verb taxonomy."""
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

    # Verb stems with many variants
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


def cmd_duplicates(args):
    """Show duplicate verbs in detail."""
    print("Duplicate Verbs in ATOMIC_VERBS")
    print("=" * 60)

    dups = analyze_verb_duplicates()
    if not dups:
        print("\nNo duplicates found!")
        return

    print(f"\nFound {len(dups)} duplicates:\n")
    for verb, count in sorted(dups.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {verb}: appears {count}x")


def cmd_problems(args):
    """Show problematic verbs."""
    print("Problematic Verbs in ATOMIC_VERBS")
    print("=" * 60)

    problems = find_problematic_verbs()
    if not problems:
        print("\nNo problematic verbs found!")
        return

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


def cmd_coverage(args):
    """Show detailed domain coverage."""
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


def cmd_test(args):
    """Run all data quality tests."""
    print("Running Data Quality Tests")
    print("=" * 60)

    task_dir = Path(args.output) if hasattr(args, "output") else None

    # Run verb taxonomy tests
    print("\n[1] Verb Taxonomy Tests")
    print("-" * 40)
    verb_results = run_verb_taxonomy_tests(args.verbose if hasattr(args, "verbose") else False)
    for status, msg in verb_results["details"]:
        icon = "✓" if status == "PASS" else "△" if status == "WARN" else "✗"
        print(f"  {icon} {msg}")

    # Run domain coverage tests
    print("\n[2] Domain Coverage Tests")
    print("-" * 40)
    coverage_results = run_domain_coverage_tests(
        args.verbose if hasattr(args, "verbose") else False
    )
    for status, msg in coverage_results["details"]:
        icon = "✓" if status == "PASS" else "△" if status == "WARN" else "✗"
        print(f"  {icon} {msg}")

    # Run comprehensive domain tests
    print("\n[3] Comprehensive Domain Tests")
    print("-" * 40)
    comprehensive_results = run_comprehensive_domain_tests(
        args.verbose if hasattr(args, "verbose") else False
    )
    # Only show failures and warnings unless verbose
    shown = 0
    for status, msg in comprehensive_results["details"]:
        if status != "PASS" or (hasattr(args, "verbose") and args.verbose):
            icon = "✓" if status == "PASS" else "△" if status == "WARN" else "✗"
            print(f"  {icon} {msg}")
            shown += 1
    if shown == 0:
        print(f"  ✓ All {len(comprehensive_results['details'])} domain tests passed")

    # Run generated data tests if directory exists
    if task_dir and task_dir.exists():
        print("\n[4] Generated Data Tests")
        print("-" * 40)
        data_results = run_generated_data_tests(
            task_dir, args.verbose if hasattr(args, "verbose") else False
        )
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


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Post-process task data and QA")
    parser.add_argument("-o", "--output", default="./task_hierarchy", help="Task directory")

    subparsers = parser.add_subparsers(dest="command")

    # Analyze generated data quality
    analyze_parser = subparsers.add_parser("analyze", help="Analyze generated data quality")
    analyze_parser.set_defaults(func=cmd_analyze)

    # Clean bad nodes
    clean_parser = subparsers.add_parser("clean", help="Remove bad nodes")
    clean_parser.add_argument("--dry-run", action="store_true", help="Don't actually remove")
    clean_parser.set_defaults(func=cmd_clean)

    # Verb taxonomy analysis
    verbs_parser = subparsers.add_parser("verbs", help="Analyze verb taxonomy")
    verbs_parser.add_argument("-v", "--verbose", action="store_true", help="Show details")
    verbs_parser.set_defaults(func=cmd_verbs)

    # Duplicates
    dup_parser = subparsers.add_parser("duplicates", help="Show duplicate verbs")
    dup_parser.set_defaults(func=cmd_duplicates)

    # Problems
    prob_parser = subparsers.add_parser("problems", help="Show problematic verbs")
    prob_parser.set_defaults(func=cmd_problems)

    # Coverage
    cov_parser = subparsers.add_parser("coverage", help="Show domain coverage")
    cov_parser.set_defaults(func=cmd_coverage)

    # Test - run all data tests
    test_parser = subparsers.add_parser("test", help="Run all data quality tests")
    test_parser.add_argument("-v", "--verbose", action="store_true", help="Show all details")
    test_parser.set_defaults(func=cmd_test)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
