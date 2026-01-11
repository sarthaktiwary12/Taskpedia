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

# Import validation from generator
from taskpedia.generate_fast import (
    ATOMIC_VERBS,
    COGNITIVE_VERBS,
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


# ============================================================================
# VERB TAXONOMY QA FUNCTIONS
# ============================================================================


def analyze_verb_duplicates() -> dict[str, int]:
    """Find duplicate verbs in ATOMIC_VERBS."""
    all_verbs = list(ATOMIC_VERBS)
    counts = Counter(all_verbs)
    duplicates = {v: c for v, c in counts.items() if c > 1}
    return duplicates


def analyze_verb_stems() -> dict[str, list[str]]:
    """Group verbs by their stem (first word before underscore)."""
    stems = defaultdict(list)
    for verb in ATOMIC_VERBS:
        stem = verb.split("_")[0]
        stems[stem].append(verb)
    # Return only stems with multiple variants
    return {k: sorted(v) for k, v in stems.items() if len(v) >= 3}


def find_ambiguous_verbs() -> dict[str, list[str]]:
    """Find single-word verbs that could have multiple meanings."""
    ambiguous_words = [
        "run",
        "set",
        "play",
        "lead",
        "scale",
        "face",
        "head",
        "park",
        "spring",
        "iron",
        "register",
        "file",
        "punch",
        "drum",
        "time",
        "bow",
        "conduct",
        "seal",
        "index",
        "pilot",
        "plant",
        "press",
        "match",
        "board",
        "block",
        "check",
        "clip",
        "close",
        "coast",
        "contract",
        "counter",
        "cover",
        "draft",
        "draw",
        "drive",
        "drop",
        "flag",
        "flat",
        "floor",
        "fly",
        "fold",
        "fork",
        "frame",
        "ground",
        "handle",
        "hang",
        "key",
        "lap",
        "last",
        "left",
        "level",
        "lift",
        "light",
        "line",
        "list",
        "lock",
        "log",
        "lot",
        "mark",
        "master",
        "match",
        "matter",
        "model",
        "mount",
        "net",
        "note",
        "order",
        "pack",
        "page",
        "paint",
        "paper",
        "part",
        "pass",
        "patch",
        "pen",
        "pick",
        "pile",
        "pin",
        "pitch",
        "place",
        "plan",
        "plate",
        "plug",
        "point",
        "pool",
        "pop",
        "port",
        "post",
        "pot",
        "power",
        "prime",
        "print",
        "process",
        "program",
        "project",
        "pump",
        "push",
        "rack",
        "range",
        "rank",
        "rate",
        "record",
        "rest",
        "return",
        "ring",
        "rock",
        "roll",
        "root",
        "round",
        "row",
        "rule",
        "rush",
        "sample",
        "sand",
        "saw",
        "school",
        "score",
        "screen",
        "seat",
        "second",
        "section",
        "seed",
        "service",
        "shade",
        "shape",
        "share",
        "sheet",
        "shell",
        "shift",
        "ship",
        "shop",
        "shore",
        "short",
        "shoulder",
        "show",
        "side",
        "sign",
        "signal",
        "size",
        "skin",
        "slide",
        "slip",
        "slot",
        "snap",
        "sort",
        "sound",
        "space",
        "spare",
        "speed",
        "spin",
        "split",
        "spot",
        "spread",
        "spring",
        "square",
        "stable",
        "stack",
        "staff",
        "stage",
        "stake",
        "stamp",
        "stand",
        "star",
        "start",
        "state",
        "station",
        "stay",
        "steam",
        "steel",
        "stem",
        "step",
        "stick",
        "stock",
        "stone",
        "stop",
        "store",
        "storm",
        "story",
        "strain",
        "strap",
        "stream",
        "stress",
        "stretch",
        "strike",
        "string",
        "strip",
        "stroke",
        "stuff",
        "style",
        "suit",
        "sum",
        "supply",
        "support",
        "surface",
        "survey",
        "swing",
        "switch",
        "table",
        "tail",
        "tank",
        "tap",
        "tape",
        "target",
        "tax",
        "team",
        "term",
        "test",
        "thread",
        "throw",
        "tie",
        "tile",
        "tip",
        "title",
        "toast",
        "tone",
        "tool",
        "top",
        "total",
        "touch",
        "tour",
        "tower",
        "trace",
        "track",
        "trade",
        "trail",
        "train",
        "trap",
        "travel",
        "treat",
        "tree",
        "trial",
        "trick",
        "trigger",
        "trim",
        "trip",
        "trouble",
        "truck",
        "trust",
        "tube",
        "tune",
        "turn",
        "type",
        "value",
        "voice",
        "wait",
        "wake",
        "walk",
        "wall",
        "watch",
        "water",
        "wave",
        "way",
        "weather",
        "weight",
        "wheel",
        "wire",
        "witness",
        "wonder",
        "word",
        "work",
        "wrap",
        "zone",
    ]

    found = {}
    for word in ambiguous_words:
        if word in ATOMIC_VERBS:
            # Check if we have disambiguated versions
            disambiguated = [v for v in ATOMIC_VERBS if v.startswith(f"{word}_")]
            found[word] = disambiguated
    return found


def find_problematic_verbs() -> dict[str, list[str]]:
    """Find potentially problematic verb patterns."""
    issues = {
        "state_predicates": [],  # is_X verbs
        "abstract_cognitive": [],  # memory/thinking verbs still in ATOMIC
        "vague_starters": [],  # do_, use_, make_, get_, be_
        "too_long": [],  # > 40 chars
        "contains_space": [],  # should use underscore
    }

    cognitive_stems = {
        "remember",
        "memorize",
        "forget",
        "recall",
        "think",
        "mental",
        "imagine",
        "believe",
        "know",
        "understand",
    }

    for verb in ATOMIC_VERBS:
        # State predicates
        if verb.startswith("is_"):
            issues["state_predicates"].append(verb)

        # Cognitive verbs that should be in COGNITIVE_VERBS
        stem = verb.split("_")[0]
        if stem in cognitive_stems:
            issues["abstract_cognitive"].append(verb)

        # Vague starters
        if verb.startswith(("do_", "use_", "make_", "get_", "be_")):
            issues["vague_starters"].append(verb)

        # Too long
        if len(verb) > 40:
            issues["too_long"].append(verb)

        # Contains space
        if " " in verb:
            issues["contains_space"].append(verb)

    return {k: v for k, v in issues.items() if v}


def check_domain_coverage() -> dict[str, dict[str, list[str]]]:
    """Check coverage of different action domains."""
    domain_checks = {
        "Art/Craft": {
            "expected": [
                "sculpt",
                "carve",
                "paint",
                "draw",
                "etch",
                "engrave",
                "glaze",
                "kiln",
                "fire_pottery",
                "throw_clay",
                "whittle",
            ],
            "found": [],
            "missing": [],
        },
        "Music": {
            "expected": [
                "strum",
                "pluck",
                "bow",
                "blow",
                "press_key",
                "finger",
                "tune",
                "mute",
                "dampen",
            ],
            "found": [],
            "missing": [],
        },
        "Digital/Computer": {
            "expected": [
                "type",
                "click",
                "swipe",
                "scroll",
                "pinch_zoom",
                "double_click",
                "right_click",
                "long_press",
                "hover",
                "drag_drop",
            ],
            "found": [],
            "missing": [],
        },
        "Animal Handling": {
            "expected": [
                "pet",
                "groom",
                "feed",
                "walk_dog",
                "leash",
                "unleash",
                "saddle",
                "bridle",
                "milk",
                "shear",
            ],
            "found": [],
            "missing": [],
        },
        "Child Care": {
            "expected": [
                "rock",
                "cradle",
                "burp",
                "swaddle",
                "diaper",
                "soothe",
                "feed",
                "bathe",
                "dress",
            ],
            "found": [],
            "missing": [],
        },
        "Outdoor/Nature": {
            "expected": [
                "fish",
                "cast",
                "reel",
                "bait",
                "net",
                "trap",
                "snare",
                "forage",
                "hike",
                "camp",
            ],
            "found": [],
            "missing": [],
        },
        "Cleaning": {
            "expected": [
                "scrub",
                "mop",
                "vacuum",
                "dust",
                "wipe",
                "disinfect",
                "sanitize",
                "deodorize",
                "stain_remove",
            ],
            "found": [],
            "missing": [],
        },
        "Repair": {
            "expected": [
                "repair",
                "fix",
                "mend",
                "patch",
                "restore",
                "refurbish",
                "troubleshoot",
                "debug",
                "diagnose",
            ],
            "found": [],
            "missing": [],
        },
        "Packaging": {
            "expected": [
                "wrap",
                "box",
                "tape",
                "seal",
                "label",
                "address",
                "ship",
                "unpack",
                "bubble_wrap",
            ],
            "found": [],
            "missing": [],
        },
        "Office": {
            "expected": [
                "file",
                "sort",
                "organize",
                "staple",
                "clip",
                "punch_hole",
                "bind",
                "laminate",
                "shred",
                "photocopy",
            ],
            "found": [],
            "missing": [],
        },
    }

    for domain, data in domain_checks.items():
        for verb in data["expected"]:
            # Check if verb or variant exists
            if verb in ATOMIC_VERBS or any(verb in v for v in ATOMIC_VERBS):
                data["found"].append(verb)
            else:
                data["missing"].append(verb)

    return domain_checks


def get_verb_statistics() -> dict[str, Any]:
    """Get comprehensive statistics about the verb taxonomy."""
    return {
        "total_atomic": len(ATOMIC_VERBS),
        "unique_atomic": len(set(ATOMIC_VERBS)),
        "total_cognitive": len(COGNITIVE_VERBS),
        "unique_cognitive": len(set(COGNITIVE_VERBS)),
        "duplicates": analyze_verb_duplicates(),
        "stems_with_variants": len(analyze_verb_stems()),
        "ambiguous_found": len(find_ambiguous_verbs()),
        "problems": find_problematic_verbs(),
    }


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


# ============================================================================
# DATA TESTS - Automated validation checks
# ============================================================================


def run_all_tests(task_dir: Path | None = None, verbose: bool = False) -> dict[str, Any]:
    """
    Run all data quality tests and return results.

    Returns dict with:
        - passed: number of tests passed
        - failed: number of tests failed
        - warnings: number of warnings
        - results: detailed results per test
    """
    results = {
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "results": {},
    }

    # Run verb taxonomy tests
    verb_tests = run_verb_taxonomy_tests(verbose)
    results["results"]["verb_taxonomy"] = verb_tests
    results["passed"] += verb_tests["passed"]
    results["failed"] += verb_tests["failed"]
    results["warnings"] += verb_tests["warnings"]

    # Run domain coverage tests
    coverage_tests = run_domain_coverage_tests(verbose)
    results["results"]["domain_coverage"] = coverage_tests
    results["passed"] += coverage_tests["passed"]
    results["failed"] += coverage_tests["failed"]
    results["warnings"] += coverage_tests["warnings"]

    # Run generated data tests if task_dir provided
    if task_dir and task_dir.exists():
        data_tests = run_generated_data_tests(task_dir, verbose)
        results["results"]["generated_data"] = data_tests
        results["passed"] += data_tests["passed"]
        results["failed"] += data_tests["failed"]
        results["warnings"] += data_tests["warnings"]

    return results


def run_verb_taxonomy_tests(verbose: bool = False) -> dict[str, Any]:
    """Run tests on the ATOMIC_VERBS taxonomy."""
    results = {"passed": 0, "failed": 0, "warnings": 0, "details": []}

    # Test 1: No duplicates in ATOMIC_VERBS
    duplicates = analyze_verb_duplicates()
    if not duplicates:
        results["passed"] += 1
        results["details"].append(("PASS", "No duplicate verbs in ATOMIC_VERBS"))
    else:
        results["failed"] += 1
        results["details"].append(
            ("FAIL", f"Found {len(duplicates)} duplicate verbs: {list(duplicates.keys())[:5]}...")
        )

    # Test 2: Minimum verb count
    verb_count = len(ATOMIC_VERBS)
    if verb_count >= 2000:
        results["passed"] += 1
        results["details"].append(("PASS", f"ATOMIC_VERBS has {verb_count:,} verbs (>= 2000)"))
    else:
        results["failed"] += 1
        results["details"].append(
            ("FAIL", f"ATOMIC_VERBS only has {verb_count:,} verbs (need >= 2000)")
        )

    # Test 3: COGNITIVE_VERBS exists and has content
    cog_count = len(COGNITIVE_VERBS)
    if cog_count >= 50:
        results["passed"] += 1
        results["details"].append(("PASS", f"COGNITIVE_VERBS has {cog_count} verbs (>= 50)"))
    else:
        results["warnings"] += 1
        results["details"].append(
            ("WARN", f"COGNITIVE_VERBS only has {cog_count} verbs (expected >= 50)")
        )

    # Test 4: No overlap between ATOMIC and COGNITIVE
    overlap = ATOMIC_VERBS & COGNITIVE_VERBS
    if not overlap:
        results["passed"] += 1
        results["details"].append(("PASS", "No overlap between ATOMIC_VERBS and COGNITIVE_VERBS"))
    else:
        results["warnings"] += 1
        results["details"].append(
            ("WARN", f"Found {len(overlap)} verbs in both sets: {list(overlap)[:5]}...")
        )

    # Test 5: All verbs use underscore format (no spaces)
    verbs_with_spaces = [v for v in ATOMIC_VERBS if " " in v]
    if not verbs_with_spaces:
        results["passed"] += 1
        results["details"].append(("PASS", "All verbs use underscore format (no spaces)"))
    else:
        results["failed"] += 1
        results["details"].append(
            (
                "FAIL",
                f"Found {len(verbs_with_spaces)} verbs with spaces: {verbs_with_spaces[:5]}...",
            )
        )

    # Test 6: No empty or very short verbs
    short_verbs = [v for v in ATOMIC_VERBS if len(v) < 2]
    if not short_verbs:
        results["passed"] += 1
        results["details"].append(("PASS", "No empty or single-character verbs"))
    else:
        results["failed"] += 1
        results["details"].append(
            ("FAIL", f"Found {len(short_verbs)} very short verbs: {short_verbs}")
        )

    # Test 7: No excessively long verbs (> 50 chars)
    long_verbs = [v for v in ATOMIC_VERBS if len(v) > 50]
    if not long_verbs:
        results["passed"] += 1
        results["details"].append(("PASS", "No excessively long verbs (> 50 chars)"))
    else:
        results["warnings"] += 1
        results["details"].append(
            ("WARN", f"Found {len(long_verbs)} very long verbs: {long_verbs[:3]}...")
        )

    # Test 8: Key action categories present
    required_stems = [
        "grasp",
        "walk",
        "look",
        "say",
        "push",
        "pull",
        "open",
        "close",
        "pick",
        "place",
    ]
    missing_stems = []
    for stem in required_stems:
        if not any(v.startswith(stem) for v in ATOMIC_VERBS):
            missing_stems.append(stem)

    if not missing_stems:
        results["passed"] += 1
        results["details"].append(("PASS", "All key action categories present"))
    else:
        results["failed"] += 1
        results["details"].append(("FAIL", f"Missing key action stems: {missing_stems}"))

    return results


def run_domain_coverage_tests(verbose: bool = False) -> dict[str, Any]:
    """Run tests on domain coverage."""
    results = {"passed": 0, "failed": 0, "warnings": 0, "details": []}

    coverage = check_domain_coverage()

    # Test: Each domain has >= 80% coverage
    for domain, data in coverage.items():
        found = len(data["found"])
        total = len(data["expected"])
        pct = (found / total * 100) if total > 0 else 0

        if pct >= 100:
            results["passed"] += 1
            results["details"].append(("PASS", f"{domain}: {pct:.0f}% coverage"))
        elif pct >= 80:
            results["warnings"] += 1
            results["details"].append(
                ("WARN", f"{domain}: {pct:.0f}% coverage (missing: {data['missing']})")
            )
        else:
            results["failed"] += 1
            results["details"].append(
                ("FAIL", f"{domain}: {pct:.0f}% coverage (missing: {data['missing']})")
            )

    return results


def run_generated_data_tests(task_dir: Path, verbose: bool = False) -> dict[str, Any]:
    """Run tests on generated task data."""
    results = {"passed": 0, "failed": 0, "warnings": 0, "details": []}

    # Collect stats
    total_nodes = 0
    llm_generated = 0
    generic_step_count = 0
    generic_template_count = 0
    empty_desc_count = 0
    invalid_atomic_count = 0
    valid_atomic_count = 0

    for yaml_path in task_dir.glob("**/*.yaml"):
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            if not data or "id" not in data:
                continue

            total_nodes += 1
            sources = data.get("sources", [])
            if "llm_generated" not in sources:
                continue

            llm_generated += 1
            name = data.get("name", "")
            description = data.get("description", "")
            node_type = data.get("node_type", "")

            if not description:
                empty_desc_count += 1

            if description and re.match(r"^Step\s+\d+\s*:", description, re.I):
                generic_step_count += 1

            if is_generic_template(name, description):
                generic_template_count += 1

            if node_type == "atomic":
                if is_valid_atomic(name):
                    valid_atomic_count += 1
                else:
                    invalid_atomic_count += 1

        except Exception:
            pass

    # Test 1: Has generated data
    if total_nodes > 0:
        results["passed"] += 1
        results["details"].append(("PASS", f"Found {total_nodes:,} total nodes"))
    else:
        results["warnings"] += 1
        results["details"].append(("WARN", "No nodes found in task directory"))
        return results

    # Test 2: Generic step descriptions < 10%
    if llm_generated > 0:
        generic_step_pct = (generic_step_count / llm_generated) * 100
        if generic_step_pct < 10:
            results["passed"] += 1
            results["details"].append(
                ("PASS", f"Generic 'Step N' descriptions: {generic_step_pct:.1f}% (< 10%)")
            )
        elif generic_step_pct < 20:
            results["warnings"] += 1
            results["details"].append(
                (
                    "WARN",
                    f"Generic 'Step N' descriptions: {generic_step_pct:.1f}% (should be < 10%)",
                )
            )
        else:
            results["failed"] += 1
            results["details"].append(
                ("FAIL", f"Generic 'Step N' descriptions: {generic_step_pct:.1f}% (too high!)")
            )

    # Test 3: Generic templates < 10%
    if llm_generated > 0:
        generic_template_pct = (generic_template_count / llm_generated) * 100
        if generic_template_pct < 10:
            results["passed"] += 1
            results["details"].append(
                ("PASS", f"Generic templates: {generic_template_pct:.1f}% (< 10%)")
            )
        elif generic_template_pct < 20:
            results["warnings"] += 1
            results["details"].append(
                ("WARN", f"Generic templates: {generic_template_pct:.1f}% (should be < 10%)")
            )
        else:
            results["failed"] += 1
            results["details"].append(
                ("FAIL", f"Generic templates: {generic_template_pct:.1f}% (too high!)")
            )

    # Test 4: Empty descriptions < 5%
    if llm_generated > 0:
        empty_pct = (empty_desc_count / llm_generated) * 100
        if empty_pct < 5:
            results["passed"] += 1
            results["details"].append(("PASS", f"Empty descriptions: {empty_pct:.1f}% (< 5%)"))
        elif empty_pct < 15:
            results["warnings"] += 1
            results["details"].append(
                ("WARN", f"Empty descriptions: {empty_pct:.1f}% (should be < 5%)")
            )
        else:
            results["failed"] += 1
            results["details"].append(("FAIL", f"Empty descriptions: {empty_pct:.1f}% (too high!)"))

    # Test 5: Valid atomics > 50% of all atomics
    total_atomics = valid_atomic_count + invalid_atomic_count
    if total_atomics > 0:
        valid_pct = (valid_atomic_count / total_atomics) * 100
        if valid_pct >= 50:
            results["passed"] += 1
            results["details"].append(("PASS", f"Valid atomics: {valid_pct:.1f}% (>= 50%)"))
        elif valid_pct >= 30:
            results["warnings"] += 1
            results["details"].append(
                ("WARN", f"Valid atomics: {valid_pct:.1f}% (should be >= 50%)")
            )
        else:
            results["failed"] += 1
            results["details"].append(("FAIL", f"Valid atomics: {valid_pct:.1f}% (too low!)"))

    return results


def run_comprehensive_domain_tests(verbose: bool = False) -> dict[str, Any]:
    """
    Run comprehensive domain coverage tests against full human activity taxonomy.
    """
    results = {"passed": 0, "failed": 0, "warnings": 0, "details": []}

    # Comprehensive domain check
    domains = {
        "Laundry": ["sort_laundry", "load_washer", "fold_laundry", "iron_shirt", "hang_clothes"],
        "Dishes": ["load_dishwasher", "scrape_plate", "put_away_dishes", "dry_dish"],
        "Bed Making": ["make_bed", "tuck_sheet", "arrange_pillows", "fluff_pillow"],
        "Home Maintenance": ["change_lightbulb", "hang_picture", "unclog_drain", "patch_drywall"],
        "Grooming": ["braid_hair", "apply_mascara", "apply_lipstick", "trim_nails"],
        "Bathing": ["shampoo_hair", "exfoliate_skin", "apply_deodorant", "lather_soap"],
        "Beverages": ["brew_coffee", "steep_tea", "froth_milk", "muddle_ingredients"],
        "Table Service": ["set_table", "clear_table", "light_candle", "fold_napkin"],
        "Dining": ["chew_food", "swallow_food", "sip_drink", "cut_bite"],
        "Meal Prep Advanced": ["chiffonade", "debone_fish", "truss_poultry", "temper_chocolate"],
        "Driving": ["merge_traffic", "parallel_park", "check_blind_spot", "signal_turn"],
        "Vehicle Maintenance": ["change_tire", "jack_up_car", "wax_car", "check_oil_level"],
        "Gym/Exercise": ["do_plank", "do_burpee", "use_elliptical", "roll_foam_roller"],
        "Ball Sports": ["head_ball", "trap_ball", "spike_volleyball", "shoot_basketball"],
        "Racquet Sports": ["hit_forehand", "hit_backhand", "hit_lob", "serve_tennis"],
        "First Aid": ["perform_cpr", "use_aed", "perform_heimlich", "apply_tourniquet"],
        "Medication": ["take_pill", "use_inhaler", "check_blood_sugar", "apply_eye_drops"],
        "Shopping": ["add_to_cart", "bag_groceries", "put_away_groceries", "compare_items"],
        "Social Greetings": ["hug_person", "fist_bump", "high_five", "shake_hands"],
        "Computer Work": ["log_in", "forward_email", "share_screen", "mute_microphone"],
        "Writing/Docs": ["draft_document", "track_changes", "add_comment", "proofread_document"],
        "Meetings": [
            "distribute_handout",
            "facilitate_discussion",
            "set_deadline",
            "take_meeting_notes",
        ],
        "Photography": ["frame_shot", "adjust_aperture", "meter_light", "edit_photo"],
        "Lawn Care": ["mow_lawn", "dethatch_lawn", "spread_mulch", "aerate_lawn"],
        "Knitting": ["cast_on_stitches", "yarn_over", "bind_off", "purl_stitch"],
        # VLA/VLN/WBC specific
        "Manipulation Core": ["grasp", "release", "pick_up", "place", "push", "pull"],
        "Navigation/VLN": ["walk_to", "navigate_to", "approach", "enter", "exit", "climb"],
        "Perception": ["look_at", "scan", "search_for", "locate", "detect", "identify"],
        "Force Control": ["apply_force", "squeeze", "press_firmly", "resist", "dampen"],
        "Bimanual": ["hold_while", "coordinate_hands", "handoff_between_hands"],
        "Failure Recovery": ["retry", "recover_from", "unjam", "regrasp_slipped"],
        "Safety": ["avoid_hazard", "emergency_stop", "warn_others", "handle_carefully"],
    }

    total_domains = len(domains)
    passed_domains = 0

    for domain, expected_verbs in domains.items():
        found = 0
        missing = []
        for verb in expected_verbs:
            if verb in ATOMIC_VERBS or any(verb in v for v in ATOMIC_VERBS):
                found += 1
            else:
                missing.append(verb)

        pct = (found / len(expected_verbs)) * 100 if expected_verbs else 0

        if pct >= 80:
            passed_domains += 1
            if pct == 100:
                results["passed"] += 1
                results["details"].append(("PASS", f"{domain}: 100%"))
            else:
                results["warnings"] += 1
                results["details"].append(("WARN", f"{domain}: {pct:.0f}% (missing: {missing})"))
        else:
            results["failed"] += 1
            results["details"].append(("FAIL", f"{domain}: {pct:.0f}% (missing: {missing})"))

    # Overall domain coverage test
    overall_pct = (passed_domains / total_domains) * 100
    if overall_pct >= 90:
        results["passed"] += 1
        results["details"].append(
            ("PASS", f"Overall: {passed_domains}/{total_domains} domains pass ({overall_pct:.0f}%)")
        )
    else:
        results["failed"] += 1
        results["details"].append(
            ("FAIL", f"Overall: {passed_domains}/{total_domains} domains pass ({overall_pct:.0f}%)")
        )

    return results


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
