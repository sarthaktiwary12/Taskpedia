"""
Domain coverage definitions for quality assurance.

This is the SINGLE SOURCE OF TRUTH for domain coverage testing.
Defines expected verbs/actions for each domain to verify the taxonomy is working.

Usage:
    from taskpedia.domains import (
        DOMAIN_COVERAGE,
        get_expected_verbs,
        check_domain_coverage,
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DomainCoverage:
    """Expected verb coverage for a domain."""

    name: str
    description: str
    expected_verbs: list[str]
    min_count: int = 5  # Minimum expected verbs from this domain

    def check(self, actual_verbs: set[str]) -> tuple[bool, list[str], list[str]]:
        """
        Check if actual verbs meet expectations.

        Returns:
            (is_passing, found_verbs, missing_verbs)
        """
        found = [v for v in self.expected_verbs if v in actual_verbs]
        missing = [v for v in self.expected_verbs if v not in actual_verbs]
        is_passing = len(found) >= self.min_count
        return is_passing, found, missing


# Domain coverage expectations
# Each domain lists verbs that SHOULD be present for good coverage
DOMAIN_COVERAGE: dict[str, DomainCoverage] = {
    # === MANIPULATION ===
    "manipulation_basic": DomainCoverage(
        name="Basic Manipulation",
        description="Core grasping and releasing actions",
        expected_verbs=[
            "grasp",
            "grip",
            "hold",
            "clutch",
            "pinch",
            "squeeze",
            "release",
            "let_go",
            "drop",
            "loosen",
        ],
    ),
    "manipulation_pick_place": DomainCoverage(
        name="Pick & Place",
        description="Picking up and placing objects",
        expected_verbs=[
            "pick_up",
            "put_down",
            "place",
            "set_down",
            "lay_down",
            "deposit",
            "retrieve",
            "fetch",
            "gather",
            "collect",
        ],
    ),
    "manipulation_push_pull": DomainCoverage(
        name="Push/Pull/Slide",
        description="Pushing, pulling, sliding actions",
        expected_verbs=[
            "push",
            "pull",
            "drag",
            "slide",
            "glide",
            "shove",
            "nudge",
            "tap",
        ],
    ),
    "manipulation_rotation": DomainCoverage(
        name="Rotation/Orientation",
        description="Rotating and orienting objects",
        expected_verbs=[
            "rotate",
            "twist",
            "turn",
            "spin",
            "flip",
            "invert",
            "tilt",
            "pivot",
            "orient",
            "align",
        ],
    ),
    # === LOCOMOTION ===
    "locomotion_basic": DomainCoverage(
        name="Basic Locomotion",
        description="Walking and running",
        expected_verbs=[
            "walk",
            "walk_to",
            "run",
            "jog",
            "sprint",
            "move_to",
            "go_to",
            "travel_to",
            "approach",
            "advance",
        ],
    ),
    "locomotion_vertical": DomainCoverage(
        name="Vertical Movement",
        description="Climbing and descending",
        expected_verbs=[
            "climb",
            "climb_up",
            "climb_down",
            "ascend",
            "descend",
            "go_up",
            "go_down",
            "step_up",
            "step_down",
        ],
    ),
    "locomotion_posture": DomainCoverage(
        name="Body Position",
        description="Sitting, standing, kneeling",
        expected_verbs=[
            "sit",
            "stand",
            "kneel",
            "crouch",
            "squat",
            "lie_down",
            "lean",
            "bend",
            "bow",
        ],
    ),
    # === PERCEPTION ===
    "perception_visual": DomainCoverage(
        name="Visual Perception",
        description="Looking and seeing",
        expected_verbs=[
            "look_at",
            "gaze_at",
            "focus_on",
            "track_visually",
            "watch",
            "scan",
            "survey",
            "observe",
            "inspect",
        ],
    ),
    "perception_search": DomainCoverage(
        name="Search/Find",
        description="Searching and locating",
        expected_verbs=[
            "search_for",
            "look_for",
            "seek",
            "hunt_for",
            "locate",
            "find",
            "spot",
            "detect",
        ],
    ),
    # === COMMUNICATION ===
    "communication_verbal": DomainCoverage(
        name="Verbal Communication",
        description="Speaking and talking",
        expected_verbs=[
            "say",
            "speak",
            "talk",
            "tell",
            "announce",
            "ask",
            "answer",
            "explain",
            "confirm",
        ],
    ),
    "communication_nonverbal": DomainCoverage(
        name="Non-verbal Communication",
        description="Gestures and body language",
        expected_verbs=[
            "gesture",
            "point_at",
            "wave",
            "nod",
            "shake_head",
            "shrug",
            "bow",
            "smile",
            "make_eye_contact",
        ],
    ),
    # === TOOL USE ===
    "tool_hand": DomainCoverage(
        name="Hand Tools",
        description="Using hand tools",
        expected_verbs=[
            "hammer",
            "saw",
            "drill",
            "screw",
            "wrench",
            "tighten",
            "loosen",
            "pry",
            "lever",
        ],
    ),
    "tool_kitchen": DomainCoverage(
        name="Kitchen Tools",
        description="Kitchen utensil usage",
        expected_verbs=[
            "peel",
            "chop",
            "slice",
            "dice",
            "grate",
            "stir",
            "whisk",
            "pour",
            "measure",
        ],
    ),
    "tool_cleaning": DomainCoverage(
        name="Cleaning Tools",
        description="Cleaning equipment usage",
        expected_verbs=[
            "vacuum",
            "mop",
            "sweep",
            "dust",
            "scrub",
            "wipe",
            "rinse",
            "spray",
        ],
    ),
    # === COOKING ===
    "cooking_heat": DomainCoverage(
        name="Heat Application",
        description="Cooking with heat",
        expected_verbs=[
            "heat",
            "boil",
            "simmer",
            "fry",
            "saute",
            "bake",
            "roast",
            "grill",
            "steam",
            "microwave",
        ],
    ),
    "cooking_prep": DomainCoverage(
        name="Food Preparation",
        description="Preparing food",
        expected_verbs=[
            "wash_produce",
            "chop",
            "slice",
            "dice",
            "peel",
            "mix",
            "stir",
            "blend",
            "knead",
        ],
    ),
    # === CONSTRUCTION/INDUSTRIAL ===
    "construction": DomainCoverage(
        name="Construction",
        description="Building and construction",
        expected_verbs=[
            "measure",
            "cut",
            "saw",
            "nail",
            "screw",
            "glue",
            "sand",
            "paint",
            "tile",
            "grout",
        ],
    ),
    "industrial": DomainCoverage(
        name="Industrial/Manufacturing",
        description="Factory and manufacturing",
        expected_verbs=[
            "assemble",
            "weld",
            "machine",
            "drill",
            "grind",
            "inspect_part",
            "quality_check",
            "palletize",
        ],
    ),
    # === PERSONAL CARE ===
    "personal_hygiene": DomainCoverage(
        name="Personal Hygiene",
        description="Self-care activities",
        expected_verbs=[
            "wash_hands",
            "brush_teeth",
            "shower",
            "bathe",
            "shave",
            "comb_hair",
            "apply_lotion",
        ],
    ),
    "dressing": DomainCoverage(
        name="Dressing",
        description="Getting dressed",
        expected_verbs=[
            "dress",
            "undress",
            "put_on",
            "take_off",
            "button",
            "zip",
            "tie",
            "buckle",
        ],
    ),
    # === HEALTHCARE ===
    "medical": DomainCoverage(
        name="Medical Care",
        description="Healthcare activities",
        expected_verbs=[
            "bandage",
            "inject",
            "take_pulse",
            "check_vitals",
            "administer",
            "apply_ointment",
            "massage",
        ],
    ),
    # === SPORTS/EXERCISE ===
    "sports": DomainCoverage(
        name="Sports",
        description="Athletic activities",
        expected_verbs=[
            "throw",
            "catch",
            "kick",
            "hit",
            "swing",
            "dribble",
            "shoot",
            "pass_ball",
        ],
    ),
    "exercise": DomainCoverage(
        name="Exercise",
        description="Fitness activities",
        expected_verbs=[
            "stretch",
            "lift_weight",
            "squat",
            "lunge",
            "run",
            "jog",
            "swim",
            "cycle",
        ],
    ),
    # === ARTS ===
    "art_visual": DomainCoverage(
        name="Visual Arts",
        description="Creating visual art",
        expected_verbs=[
            "draw",
            "paint",
            "sketch",
            "sculpt",
            "write",
            "trace",
            "mark",
        ],
    ),
    "art_music": DomainCoverage(
        name="Music",
        description="Making music",
        expected_verbs=[
            "play",
            "strum",
            "pluck",
            "bow",
            "press_key",
            "beat_drum",
            "sing",
        ],
    ),
    # === TEXTILE ===
    "textile": DomainCoverage(
        name="Textile/Sewing",
        description="Working with fabric",
        expected_verbs=[
            "sew",
            "stitch",
            "hem",
            "cut_fabric",
            "pin",
            "iron",
            "fold",
        ],
    ),
    # === AGRICULTURE ===
    "agriculture": DomainCoverage(
        name="Agriculture/Gardening",
        description="Farming and gardening",
        expected_verbs=[
            "plant",
            "dig",
            "rake",
            "hoe",
            "water",
            "prune",
            "harvest",
            "weed",
        ],
    ),
    # === VEHICLE ===
    "vehicle": DomainCoverage(
        name="Vehicle Operation",
        description="Driving and vehicle control",
        expected_verbs=[
            "steer",
            "accelerate",
            "brake",
            "shift_gear",
            "park",
            "reverse",
            "signal_turn",
        ],
    ),
    # === SAFETY ===
    "safety": DomainCoverage(
        name="Safety/Emergency",
        description="Safety actions",
        expected_verbs=[
            "evacuate",
            "extinguish",
            "rescue",
            "protect",
            "shield",
            "call_emergency",
        ],
    ),
}


def get_expected_verbs(domain_key: str) -> list[str]:
    """Get expected verbs for a domain."""
    coverage = DOMAIN_COVERAGE.get(domain_key)
    if coverage:
        return coverage.expected_verbs
    return []


def get_all_expected_verbs() -> set[str]:
    """Get all expected verbs across all domains."""
    all_verbs = set()
    for coverage in DOMAIN_COVERAGE.values():
        all_verbs.update(coverage.expected_verbs)
    return all_verbs


def check_domain_coverage(
    actual_verbs: set[str],
) -> dict[str, dict[str, Any]]:
    """
    Check coverage across all domains.

    Returns:
        Dict mapping domain_key to {passing, found, missing, coverage}
    """
    results = {}

    for key, coverage in DOMAIN_COVERAGE.items():
        is_passing, found, missing = coverage.check(actual_verbs)
        results[key] = {
            "name": coverage.name,
            "passing": is_passing,
            "found": found,
            "missing": missing,
            "found_count": len(found),
            "expected_count": len(coverage.expected_verbs),
            "coverage_pct": len(found) / len(coverage.expected_verbs) * 100
            if coverage.expected_verbs
            else 0,
        }

    return results


def run_coverage_report(actual_verbs: set[str]) -> str:
    """Generate a coverage report."""
    results = check_domain_coverage(actual_verbs)

    lines = []
    lines.append("=" * 70)
    lines.append("DOMAIN COVERAGE REPORT")
    lines.append("=" * 70)

    passing = sum(1 for r in results.values() if r["passing"])
    total = len(results)
    lines.append(f"\nOverall: {passing}/{total} domains passing\n")

    # Group by pass/fail
    failing = [(k, v) for k, v in results.items() if not v["passing"]]
    passing_domains = [(k, v) for k, v in results.items() if v["passing"]]

    if failing:
        lines.append("FAILING DOMAINS:")
        lines.append("-" * 40)
        for key, result in failing:
            lines.append(f"\n  {result['name']} ({key})")
            lines.append(
                f"    Coverage: {result['found_count']}/{result['expected_count']} ({result['coverage_pct']:.0f}%)"
            )
            if result["missing"]:
                lines.append(f"    Missing: {', '.join(result['missing'][:5])}")
                if len(result["missing"]) > 5:
                    lines.append(f"             ...and {len(result['missing']) - 5} more")

    if passing_domains:
        lines.append("\n\nPASSING DOMAINS:")
        lines.append("-" * 40)
        for key, result in passing_domains:
            lines.append(f"  {result['name']}: {result['coverage_pct']:.0f}%")

    lines.append("\n" + "=" * 70)
    return "\n".join(lines)
