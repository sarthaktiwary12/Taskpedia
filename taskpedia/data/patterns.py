"""
Canonical pattern definitions for task quality validation.

This is the SINGLE SOURCE OF TRUTH for all regex patterns used across
the codebase. Do not duplicate these patterns elsewhere.

Usage:
    from taskpedia.patterns import (
        ROBOT_INTERNAL_PATTERNS,
        GENERIC_VERBS,
        GENERIC_NOUNS,
        is_robot_internal,
        is_generic_template,
    )
"""

from __future__ import annotations

import re
from typing import Pattern

# ============================================================================
# ROBOT INTERNAL PATTERNS
# ============================================================================
# These patterns detect low-level robot control that shouldn't be in
# task decomposition. Actions should be observable from video, not internal.
#
# Categories:
#   - Motor/Joint Control
#   - Trajectory/Kinematics
#   - Sensor/Signal Processing
#   - Balance/Posture Control
#   - Muscles/Anatomy
#   - Data/Compute Operations

ROBOT_INTERNAL_PATTERNS: list[str] = [
    # === MOTOR/JOINT CONTROL ===
    r"joint.?torque",
    r"motor.?command",
    r"motor.?output",
    r"motor.?current",
    r"pid.?output",
    r"pid.?control",
    r"impedance.?control",
    r"servo",
    r"flexor.?torque",
    r"extensor.?torque",
    r"corrective.?torque",
    r"joint.?error",
    r"joint.?velocity",
    r"joint.?stiffness",
    r"joint.?damping",
    r"actuator",
    r"control.?law",
    r"control.?algorithm",
    r"torque.?signal",
    r"torque.?value",
    r"torque.?target",
    # === TRAJECTORY/KINEMATICS ===
    r"trajectory.?comput",
    r"gait.?trajectory",
    r"com.?shift",
    r"center.?of.?mass",
    r"inverse.?kinematics",
    r"forward.?kinematics",
    r"jacobian",
    r"end.?effector",
    r"2d.?projection",
    r"ground.?plane",
    r"reference.?frame",
    # === SENSOR/SIGNAL PROCESSING ===
    r"signal.?filter",
    r"sensor.?process",
    r"proprioceptive",
    r"force.?feedback",
    r"capture.?visual.?frame",
    r"capture.?high.?resolution",
    r"visual.?tracker",
    r"pixel.?position",
    r"bitstream",
    r"tx.?buffer",
    r"rx.?buffer",
    # === BALANCE/POSTURE CONTROL ===
    r"postural.?control",
    r"balance.?control",
    r"micro.?adjustment",
    r"pose.?micro",
    r"postural.?shift",
    r"deviation.?metrics",
    r"balance.?correction",
    r"pelvis",
    r"lumbar",
    r"girdle",
    r"pelvic.?tilt",
    r"torso.?shift",
    r"weight.?distribution",
    r"center.?pressure",
    # === BILATERAL/ANATOMICAL ===
    r"bilateral.?hip",
    r"bilateral.?knee",
    r"bilateral.?ankle",
    r"bilateral.?dorsiflexion",
    r"sagittal",
    r"frontal.?ankle",
    r"mcp.?joint",
    r"actuate.?sagittal",
    r"spine.?alignment",
    # === MUSCLES/ANATOMY ===
    r"rectus.?abdominis",
    r"erector.?spinae",
    r"muscle.?activation",
    r"flexion(?!.*(arm|leg|knee|elbow))",  # Avoid false positives
    r"abduction",
    r"adduction",
    r"supination",
    r"pronation",
    r"dorsiflexion",
    r"plantarflexion",
    # === MICRO MOVEMENTS ===
    r"micro.?translate",
    r"micro.?rotate",
    r"incrementally$",
    r"compliant.?retraction",
    # === FORCE/PRESSURE CONTROL ===
    r"exert.?pressure",
    r"tension.?data",
    r"force.?maintenance",
    r"force.?level",
    r"counteract.?slippage",
    r"apply.?tension",
    r"regulate.?force",
    r"contact.?force",
    r"normal.?force",
    r"pressure.?on.?user",
    r"palm.?pressure",
    r"force.?compliance",
    r"compliant.?contact",
    # === DATA/COMPUTE OPERATIONS ===
    r"execute.+calculation",
    r"compute.+projection",
    r"compute.+distribution",
    r"compute.+commands",
    r"compute.+percentage",
    r"compute.+difference",
    r"calculate.+angle",
    r"calculate.+deviation",
    r"calculate.+distribution",
    r"store.+label",
    r"store.+data",
    r"store.+computed",
    r"store.+into",
    r"access.+data",
    r"access.+value",
    r"access.+status",
    r"load.+data",
    r"load.+into",
    r"load.+timestamp",
    r"load.+command",
    r"update.+register",
    r"update.+status",
    r"update.+state",
    r"update.+flag",
    r"initialize.+tracker",
    r"initialize.+visual",
    r"perceive.+status",
    r"perceive.+deviation",
    r"perceive.+state",
    r"acquire.+position",
    r"acquire.+state",
    r"acquire.+target",
    r"check.+threshold",
    r"check.+against",
    r"check.+timer",
    r"track.+duration",
    r"stable.?duration",
    r"timestamp",
    r"interval.+into",
    r"cycle.?count",
    r"gait.?cycle",
    r"termination.?condition",
    r"termination.?state",
    r"logical.?and",
    r"perform.?logical",
    r"subtraction.?on",
    r"estimated.?visual.?state",
    r"internal.?data.?link",
    r"vision.?unit",
    r"storage.?status",
    r"path.?storage",
    r"finger.?alignment",
    r"alignment.?to.?spool",
    r"circular.?sweep",
    r"circular.?path",
    r"arm.?retraction",
    r"coordinated.+retraction",
    r"center.?camera.?on",
]

# Compile patterns once at module load
_ROBOT_INTERNAL_RE: list[Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in ROBOT_INTERNAL_PATTERNS
]


def is_robot_internal(name: str) -> tuple[bool, str | None]:
    """
    Check if this is a robot-internal action (not observable behavior).

    Returns:
        (is_internal, pattern_that_matched)
    """
    for pattern in _ROBOT_INTERNAL_RE:
        if pattern.search(name):
            return True, pattern.pattern
    return False, None


# ============================================================================
# GENERIC TEMPLATE PATTERNS
# ============================================================================
# These detect low-quality template outputs that are too vague.

GENERIC_VERBS: frozenset[str] = frozenset(
    {
        "check",
        "verify",
        "inspect",
        "prepare",
        "gather",
        "secure",
        "adjust",
        "position",
        "clean",
        "move",
        "handle",
        "process",
        "ensure",
        "confirm",
        "validate",
        "assess",
        "evaluate",
        "review",
        "analyze",
        "monitor",
    }
)

GENERIC_NOUNS: frozenset[str] = frozenset(
    {
        "target",
        "source",
        "materials",
        "equipment",
        "tools",
        "surface",
        "container",
        "workspace",
        "components",
        "area",
        "items",
        "objects",
        "things",
        "stuff",
        "resources",
        "supplies",
        "elements",
        "system",
        "setup",
        "environment",
    }
)

# Pattern for "Step N:" descriptions
_STEP_PATTERN = re.compile(r"^step\s+\d+\s*:", re.IGNORECASE)


def is_generic_template(name: str, description: str = "") -> bool:
    """
    Check if this looks like a generic template output.

    Detects:
    - "Step N:" descriptions
    - {generic_verb} {generic_noun} patterns
    - Descriptions that just repeat the name
    """
    name_lower = name.lower().strip()
    desc_lower = description.lower().strip()

    # Reject "Step N:" descriptions
    if _STEP_PATTERN.match(desc_lower):
        return True

    # Reject {generic_verb} {generic_noun} patterns
    words = name_lower.replace("_", " ").replace("-", " ").split()
    if len(words) == 2:
        verb, noun = words
        if verb in GENERIC_VERBS and noun in GENERIC_NOUNS:
            return True

    # Reject very short descriptions that just repeat the name
    if desc_lower and len(desc_lower) < 20:
        if name_lower in desc_lower or desc_lower in name_lower:
            return True

    return False


# ============================================================================
# COGNITIVE VERB PATTERNS
# ============================================================================
# These are mental/internal verbs that aren't directly observable.

COGNITIVE_VERBS: frozenset[str] = frozenset(
    {
        # Memory Operations
        "remember",
        "memorize",
        "recall",
        "forget",
        "recognize",
        # Planning/Reasoning
        "plan",
        "decide",
        "choose",
        "consider",
        "evaluate",
        "predict",
        "anticipate",
        "expect",
        "infer",
        "deduce",
        # Understanding
        "understand",
        "comprehend",
        "realize",
        "interpret",
        # Imagination
        "imagine",
        "visualize",
        "envision",
        "conceive",
        # Beliefs/Knowledge
        "know",
        "believe",
        "think",
        "suspect",
        "assume",
    }
)


def is_cognitive_verb(name: str) -> bool:
    """Check if the action uses a cognitive/mental verb."""
    name_lower = name.lower().replace("_", " ").replace("-", " ")

    for verb in COGNITIVE_VERBS:
        if name_lower.startswith(verb + " ") or name_lower == verb:
            return True

    return False


def is_valid_atomic(name: str) -> bool:
    """
    Check if this is a valid atomic action (starts with atomic verb).

    Uses ATOMIC_VERBS from taskpedia.data.verbs.
    """
    from taskpedia.data.verbs import ATOMIC_VERBS

    name_lower = name.lower().replace("_", " ").replace("-", " ")

    for verb in ATOMIC_VERBS:
        verb_pattern = verb.replace("_", " ")
        if name_lower.startswith(verb_pattern + " ") or name_lower == verb_pattern:
            return True

    return False


# ============================================================================
# COMBINED VALIDATION
# ============================================================================


def validate_task_name(
    name: str,
    description: str = "",
) -> tuple[bool, str | None]:
    """
    Validate a task name against all pattern checks.

    Returns:
        (is_valid, rejection_reason)
    """
    # Check robot internal
    is_internal, pattern = is_robot_internal(name)
    if is_internal:
        return False, f"robot_internal:{pattern}"

    # Check generic template
    if is_generic_template(name, description):
        return False, "generic_template"

    # Check cognitive verb
    if is_cognitive_verb(name):
        return False, "cognitive_verb"

    return True, None
