"""
QA (Quality Assurance) tests for verb taxonomy and generated data.

This module provides:
- Verb taxonomy analysis (duplicates, stems, ambiguous verbs)
- Domain coverage checks
- Test suites for verb taxonomy, domain coverage, and generated data
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

from taskpedia.data import (
    ATOMIC_VERBS,
    COGNITIVE_VERBS,
    is_generic_template,
    is_valid_atomic,
)

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
        # === INDUSTRIAL/WORKPLACE DOMAINS ===
        "Factory/Manufacturing": {
            "expected": [
                "assemble",
                "weld",
                "solder",
                "rivet",
                "machine",
                "mill",
                "lathe",
                "grind",
                "polish",
                "stamp",
                "press",
                "forge",
                "cast",
                "mold",
                "extrude",
                "cut",
                "drill",
                "tap",
                "thread",
                "inspect",
                "calibrate",
                "operate_cnc",
                "load_machine",
                "unload_machine",
                "quality_check",
            ],
            "found": [],
            "missing": [],
        },
        "Construction": {
            "expected": [
                "frame",
                "nail",
                "hammer",
                "screw",
                "bolt",
                "pour_concrete",
                "mix_concrete",
                "lay_brick",
                "mortar",
                "plaster",
                "drywall",
                "insulate",
                "roof",
                "shingle",
                "excavate",
                "grade",
                "level",
                "plumb",
                "wire",
                "pipe",
                "solder_pipe",
                "scaffold",
                "hoist",
                "crane",
                "demolish",
            ],
            "found": [],
            "missing": [],
        },
        "Mining/Extraction": {
            "expected": [
                "drill",
                "blast",
                "excavate",
                "haul",
                "crush",
                "screen",
                "separate",
                "process_ore",
                "tunnel",
                "shore",
                "ventilate",
                "sample",
                "assay",
                "extract",
            ],
            "found": [],
            "missing": [],
        },
        "Warehouse/Logistics": {
            "expected": [
                "palletize",
                "stack",
                "load",
                "unload",
                "forklift",
                "scan_barcode",
                "pick",
                "pack",
                "sort",
                "label",
                "shrink_wrap",
                "stage",
                "dispatch",
                "receive",
                "inventory",
                "bin",
                "shelve",
            ],
            "found": [],
            "missing": [],
        },
        "Agriculture": {
            "expected": [
                "plow",
                "till",
                "seed",
                "plant",
                "irrigate",
                "fertilize",
                "spray",
                "harvest",
                "thresh",
                "bale",
                "prune",
                "graft",
                "milk",
                "shear",
                "herd",
                "fence",
            ],
            "found": [],
            "missing": [],
        },
        "Heavy Equipment": {
            "expected": [
                "operate_crane",
                "operate_forklift",
                "operate_excavator",
                "operate_bulldozer",
                "operate_loader",
                "rig",
                "lift",
                "hoist",
                "winch",
                "tow",
                "haul",
            ],
            "found": [],
            "missing": [],
        },
        "Electrical/Wiring": {
            "expected": [
                "wire",
                "splice",
                "terminate",
                "crimp",
                "solder",
                "insulate",
                "ground",
                "test_circuit",
                "trace",
                "install_outlet",
                "pull_wire",
                "conduit",
            ],
            "found": [],
            "missing": [],
        },
        "Plumbing": {
            "expected": [
                "pipe",
                "solder_pipe",
                "sweat",
                "thread_pipe",
                "ream",
                "deburr",
                "flare",
                "braze",
                "snake",
                "flush",
                "valve",
                "gasket",
            ],
            "found": [],
            "missing": [],
        },
        "HVAC": {
            "expected": [
                "braze",
                "charge_refrigerant",
                "evacuate",
                "pressurize",
                "duct",
                "insulate",
                "balance",
                "commission",
                "diagnose_hvac",
            ],
            "found": [],
            "missing": [],
        },
        "Automotive/Mechanic": {
            "expected": [
                "diagnose",
                "jack",
                "lift_vehicle",
                "torque",
                "bleed_brakes",
                "align",
                "balance_tire",
                "mount_tire",
                "change_oil",
                "flush",
                "tune",
                "time",
            ],
            "found": [],
            "missing": [],
        },
        "Food Processing": {
            "expected": [
                "butcher",
                "debone",
                "fillet",
                "grind_meat",
                "package",
                "pasteurize",
                "can",
                "freeze",
                "smoke",
                "cure",
                "ferment",
                "bottle",
            ],
            "found": [],
            "missing": [],
        },
        "Textile/Garment": {
            "expected": [
                "sew",
                "stitch",
                "hem",
                "cut_fabric",
                "press",
                "iron",
                "steam",
                "dye",
                "weave",
                "knit",
                "spin",
                "embroider",
            ],
            "found": [],
            "missing": [],
        },
        "Safety/PPE": {
            "expected": [
                "don_ppe",
                "doff_ppe",
                "inspect_ppe",
                "harness",
                "lockout",
                "tagout",
                "barrier",
                "cordon",
                "signal",
                "spot",
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
# TEST SUITES
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

    if yaml is None:
        results["warnings"] += 1
        results["details"].append(("WARN", "PyYAML not installed, skipping generated data tests"))
        return results

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
        # === DOMESTIC/PERSONAL ===
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
        # === INDUSTRIAL/MANUFACTURING ===
        "Assembly Line": ["assemble", "insert", "attach", "fasten", "secure", "align_parts"],
        "Welding": ["weld", "tack_weld", "mig_weld", "tig_weld", "arc_weld", "spot_weld"],
        "Machining": ["machine", "mill", "lathe", "drill", "bore", "ream", "tap", "thread"],
        "Metal Fabrication": ["cut_metal", "bend", "form", "stamp", "punch", "shear", "brake"],
        "Casting/Molding": ["cast", "mold", "pour", "inject", "extrude", "die_cast"],
        "Finishing": ["grind", "sand", "polish", "buff", "deburr", "coat", "plate", "anodize"],
        "Quality Control": ["inspect", "measure", "gauge", "calibrate", "test", "verify"],
        "CNC Operations": ["program_cnc", "setup_cnc", "operate_cnc", "load_tool", "zero_machine"],
        # === CONSTRUCTION ===
        "Framing": ["frame", "nail", "screw", "bolt", "brace", "sheathe", "truss"],
        "Concrete Work": ["pour_concrete", "mix_concrete", "screed", "float", "trowel", "cure"],
        "Masonry": ["lay_brick", "mortar", "point", "grout", "set_block", "cut_stone"],
        "Drywall": ["hang_drywall", "tape", "mud", "sand_drywall", "texture", "finish"],
        "Roofing": ["shingle", "flash", "seal", "tar", "membrane", "underlayment"],
        "Excavation": ["excavate", "dig", "trench", "grade", "compact", "backfill"],
        "Scaffolding": ["erect_scaffold", "plank", "brace_scaffold", "tie_off", "dismantle"],
        # === TRADES ===
        "Electrical Work": [
            "wire",
            "splice",
            "terminate",
            "pull_cable",
            "fish_wire",
            "install_box",
        ],
        "Plumbing Work": ["sweat_pipe", "thread_pipe", "solder_joint", "glue_pvc", "crimp_pex"],
        "HVAC Work": ["braze", "charge_system", "evacuate", "pressurize", "install_duct"],
        "Carpentry": ["saw", "plane", "chisel", "joint", "dado", "rabbet", "mortise", "tenon"],
        # === WAREHOUSE/LOGISTICS ===
        "Warehousing": [
            "receive_shipment",
            "palletize",
            "stack",
            "bin",
            "pick_order",
            "pack_order",
        ],
        "Forklift Operations": [
            "operate_forklift",
            "lift_pallet",
            "transport_load",
            "stack_pallets",
        ],
        "Shipping/Receiving": [
            "load_truck",
            "unload_truck",
            "stage_shipment",
            "manifest",
            "dispatch",
        ],
        "Inventory": [
            "count_inventory",
            "scan_barcode",
            "label",
            "track",
            "replenish",
            "cycle_count",
        ],
        # === MINING/EXTRACTION ===
        "Mining Operations": ["drill_rock", "blast", "muck", "haul", "shore", "ventilate_mine"],
        "Ore Processing": ["crush", "screen", "separate", "concentrate", "smelt", "refine"],
        # === AGRICULTURE ===
        "Field Work": ["plow", "till", "seed", "plant", "cultivate", "irrigate", "harvest"],
        "Livestock": ["herd", "corral", "brand", "tag", "vaccinate", "milk", "shear"],
        "Equipment Operation": [
            "operate_tractor",
            "operate_combine",
            "operate_baler",
            "operate_sprayer",
        ],
        "Meat Processing": ["slaughter", "butcher", "debone", "fillet", "grind", "portion"],
        "Food Packaging": ["package", "seal", "label", "date", "palletize_product"],
        "Food Safety": ["sanitize", "pasteurize", "sterilize", "test_sample", "haccp_check"],
        # === TEXTILE/GARMENT ===
        "Sewing": ["sew", "stitch", "hem", "seam", "dart", "pleat", "gather"],
        "Fabric Handling": ["cut_pattern", "lay_fabric", "pin", "mark", "press", "steam"],
        "Industrial Sewing": ["overlock", "serge", "bind", "topstitch", "bartack"],
        # === SAFETY/COMPLIANCE ===
        "PPE Usage": ["don_ppe", "doff_ppe", "inspect_ppe", "fit_test", "decontaminate"],
        "Lockout/Tagout": ["lockout", "tagout", "verify_isolation", "clear_lockout"],
        "Hazmat": ["contain_spill", "neutralize", "dispose_hazmat", "ventilate_area"],
        # === VLA/VLN/WBC SPECIFIC ===
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
