#!/usr/bin/env python3
"""
Quality Control for Taskpedia - Filter out bad tasks, keep good ones.
"""

import json
import re
from pathlib import Path

# =============================================================================
# BAD TASK PATTERNS - These should be filtered out
# =============================================================================

# Vague/generic terms that make tasks non-actionable
VAGUE_PATTERNS = [
    r"adjust.*based on",
    r"adapt.*to.*conditions",
    r"respond to.*changes",
    r"optimize.*for",
    r"manage.*appropriately",
    r"handle.*as needed",
    r"process.*accordingly",
    # NEW: From user feedback - vague actions without clear substance/tool
    r"^spray\s+\w+$",  # "spray X" without specifying what to spray
    r"^apply\s+to\s+",  # "apply to X" without specifying what to apply
    r"^treat\s+\w+$",   # "treat X" without specifying how
    r"^coat\s+\w+$",    # "coat X" without specifying with what
]

# Locomotion/navigation primitives (built into the platform, not trainable)
LOCOMOTION_PATTERNS = [
    r"^avoid.*obstacle",
    r"^navigate.*to",
    r"^move.*to.*location",
    r"^travel.*to",
    r"^return.*to.*base",
    r"^approach.*target",
    r"adjust.*speed",
    r"change.*direction",
    r"follow.*path",
    r"stop.*when",
    # NEW: From user feedback - non-physical/cognitive tasks (just locomotion)
    r"^attending\s+",
    r"^observing\s+",
    r"^participating\s+in\s+",
    r"^joining\s+",
    r"^watching\s+",
]

# Calibration/setup/internal system tasks (not physically trainable)
INTERNAL_PATTERNS = [
    r"calibrate",
    r"initialize",
    r"configure",
    r"boot.*up",
    r"acquire.*signal",
    r"establish.*connection",
    r"synchronize",
    r"update.*software",
    r"run.*diagnostic",
    r"check.*status",
    r"monitor.*level",
    r"log.*data",
    r"transmit.*data",
    r"receive.*command",
]

# Pure perception without manipulation
PERCEPTION_ONLY_PATTERNS = [
    r"^capture.*image",
    r"^take.*photo",
    r"^scan.*for",
    r"^detect.*presence",
    r"^identify.*type",
    r"^recognize",
    r"^measure.*using.*sensor",
    r"^read.*sensor",
    r"^analyze.*data",
]

# Generic cross-domain tasks (not category-specific)
GENERIC_CROSS_DOMAIN = [
    r"dock.*charging",
    r"recharge.*battery",
    r"enter.*standby",
    r"power.*down",
    r"send.*alert",
    r"notify.*operator",
    r"wait.*for.*instruction",
    r"pause.*operation",
]

# NEW: From user feedback - over-specific equipment modifiers
OVERSPECIFIC_PATTERNS = [
    r"\bcommercial\b",
    r"\bindustrial\b",
    r"\bprofessional-grade\b",
    r"\benterprise\b",
    r"\bheavy-duty\b",
    r"\bhospital-grade\b",
]

# NEW: From user feedback - confusing language patterns
CONFUSING_LANGUAGE = [
    r"over\s+\w+'s\s+",  # "over passenger's seat" - nested possessives
    r"\w+'s\s+\w+\s+of\s+",  # Overly complex possessive chains
]

# Combine all bad patterns
ALL_BAD_PATTERNS = (
    VAGUE_PATTERNS +
    LOCOMOTION_PATTERNS +
    INTERNAL_PATTERNS +
    PERCEPTION_ONLY_PATTERNS +
    GENERIC_CROSS_DOMAIN +
    OVERSPECIFIC_PATTERNS +
    CONFUSING_LANGUAGE
)

# =============================================================================
# GOOD TASK INDICATORS - These are signs of quality tasks
# =============================================================================

# Physical manipulation verbs
GOOD_MANIPULATION_VERBS = [
    "grasp", "grip", "hold", "release", "pick", "place", "lift", "lower",
    "push", "pull", "slide", "rotate", "turn", "twist", "insert", "extract",
    "attach", "detach", "connect", "disconnect", "fasten", "unfasten",
    "screw", "unscrew", "clamp", "unclamp", "press", "squeeze",
    "fold", "unfold", "roll", "unroll", "wrap", "unwrap",
    "cut", "slice", "chop", "peel", "scrape", "brush", "wipe", "scrub",
    "spray", "pour", "dispense", "apply", "spread", "dip", "soak",
    "load", "unload", "stack", "unstack", "arrange", "sort",
    "open", "close", "seal", "unseal",
]

# Tool use indicators
TOOL_INDICATORS = [
    "using a", "with a", "using the", "with the",
    "gripper", "tool", "auger", "probe", "brush", "nozzle",
    "blade", "cutter", "sprayer", "applicator", "injector",
]

# Specific object/target indicators
SPECIFIC_OBJECT_PATTERNS = [
    r"\b(the|a|an)\s+\w+\s+(from|into|onto|off|out of)\b",
    r"\bspecific\b",
    r"\bindividual\b",
    r"\bparticular\b",
]


def is_bad_task(task_name: str) -> tuple[bool, str]:
    """Check if a task matches bad patterns. Returns (is_bad, reason)."""
    task_lower = task_name.lower()

    for pattern in ALL_BAD_PATTERNS:
        if re.search(pattern, task_lower):
            return True, f"Matches bad pattern: {pattern}"

    return False, ""


def is_good_task(task_name: str) -> tuple[bool, list[str]]:
    """Check if a task has good quality indicators. Returns (is_good, reasons)."""
    task_lower = task_name.lower()
    reasons = []

    # Check for manipulation verbs
    for verb in GOOD_MANIPULATION_VERBS:
        if task_lower.startswith(verb) or f" {verb} " in task_lower:
            reasons.append(f"Has manipulation verb: {verb}")
            break

    # Check for tool use
    for tool in TOOL_INDICATORS:
        if tool in task_lower:
            reasons.append(f"Indicates tool use: {tool}")
            break

    # Check for specific objects
    for pattern in SPECIFIC_OBJECT_PATTERNS:
        if re.search(pattern, task_lower):
            reasons.append("References specific object")
            break

    return len(reasons) > 0, reasons


def analyze_task(task_name: str) -> dict:
    """Analyze a task and return quality assessment."""
    is_bad, bad_reason = is_bad_task(task_name)
    is_good, good_reasons = is_good_task(task_name)

    if is_bad:
        quality = "BAD"
        score = 0
    elif is_good:
        quality = "GOOD"
        score = len(good_reasons)
    else:
        quality = "UNCERTAIN"
        score = 0.5

    return {
        "task": task_name,
        "quality": quality,
        "score": score,
        "bad_reason": bad_reason,
        "good_reasons": good_reasons,
    }


def analyze_manifest():
    """Analyze all tasks in the manifest."""
    manifest_path = Path("/home/sarthak/Taskpedia/taskpedia-web/public/data/manifest.json")

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Focus on robotics domains (new hierarchy)
    robotics_nodes = {k: v for k, v in manifest.items() if k.startswith("robotics_")}

    results = {"GOOD": [], "BAD": [], "UNCERTAIN": []}

    for node_id, node in robotics_nodes.items():
        if node.get("node_type") == "subtask":
            analysis = analyze_task(node["name"])
            analysis["id"] = node_id
            analysis["parent"] = node.get("parent_id", "")
            results[analysis["quality"]].append(analysis)

    return results


def print_analysis_report(results: dict):
    """Print a summary report of the analysis."""
    print("=" * 70)
    print("TASKPEDIA QUALITY CONTROL REPORT")
    print("=" * 70)

    total = sum(len(v) for v in results.values())
    print(f"\nTotal tasks analyzed: {total}")
    print(f"  GOOD:      {len(results['GOOD'])} ({100*len(results['GOOD'])//total}%)")
    print(f"  BAD:       {len(results['BAD'])} ({100*len(results['BAD'])//total}%)")
    print(f"  UNCERTAIN: {len(results['UNCERTAIN'])} ({100*len(results['UNCERTAIN'])//total}%)")

    print("\n" + "=" * 70)
    print("SAMPLE BAD TASKS (first 20)")
    print("=" * 70)
    for item in results["BAD"][:20]:
        print(f"\n  Task: {item['task']}")
        print(f"  Reason: {item['bad_reason']}")
        print(f"  Path: {item['id']}")

    print("\n" + "=" * 70)
    print("SAMPLE GOOD TASKS (first 20)")
    print("=" * 70)
    for item in results["GOOD"][:20]:
        print(f"\n  Task: {item['task']}")
        print(f"  Quality indicators: {', '.join(item['good_reasons'])}")

    print("\n" + "=" * 70)
    print("SAMPLE UNCERTAIN TASKS (first 20)")
    print("=" * 70)
    for item in results["UNCERTAIN"][:20]:
        print(f"\n  Task: {item['task']}")
        print(f"  Path: {item['id']}")


def remove_bad_tasks():
    """Remove tasks flagged as BAD from the manifest."""
    manifest_path = Path("/home/sarthak/Taskpedia/taskpedia-web/public/data/manifest.json")

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Find bad tasks
    bad_ids = set()
    for node_id, node in list(manifest.items()):
        if node.get("node_type") == "subtask" and node_id.startswith("robotics_"):
            is_bad, reason = is_bad_task(node["name"])
            if is_bad:
                bad_ids.add(node_id)

    print(f"Found {len(bad_ids)} bad tasks to remove")

    # Remove bad tasks and update parent references
    for bad_id in bad_ids:
        if bad_id in manifest:
            parent_id = manifest[bad_id].get("parent_id")
            if parent_id and parent_id in manifest:
                parent = manifest[parent_id]
                if "children_ids" in parent and bad_id in parent["children_ids"]:
                    parent["children_ids"].remove(bad_id)
            del manifest[bad_id]

    # Save updated manifest
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Removed {len(bad_ids)} bad tasks")
    print(f"Manifest now has {len(manifest)} nodes")

    return len(bad_ids)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--remove":
        remove_bad_tasks()
    else:
        results = analyze_manifest()
        print_analysis_report(results)
        print("\n\nTo remove bad tasks, run: python quality_control.py --remove")
