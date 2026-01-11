"""
Validation utilities for task quality control.

This module provides functions to detect generic/template outputs
and validate atomic action naming.
"""

from __future__ import annotations

import re

from taskpedia.verbs import ATOMIC_VERBS, COGNITIVE_VERBS

# ============================================================================
# GENERIC PATTERNS - Indicators of low-quality template outputs
# ============================================================================

# Generic nouns that indicate template outputs
GENERIC_NOUNS = {
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
}

# Generic verbs that are too vague
GENERIC_VERBS = {
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
}


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def is_generic_template(name: str, description: str) -> bool:
    """Check if this looks like a generic template output."""
    name_lower = name.lower().strip()
    desc_lower = description.lower().strip()

    # Reject "Step N:" descriptions
    if re.match(r"^step\s+\d+\s*:", desc_lower):
        return True

    # Reject {generic_verb} {generic_noun} patterns
    words = name_lower.replace("_", " ").split()
    if len(words) == 2:
        verb, noun = words
        if verb in GENERIC_VERBS and noun in GENERIC_NOUNS:
            return True

    # Reject very short descriptions that just repeat the name
    if desc_lower and len(desc_lower) < 20:
        if name_lower in desc_lower or desc_lower in name_lower:
            return True

    return False


def is_valid_atomic(name: str) -> bool:
    """Check if this is a valid atomic action."""
    name_lower = name.lower().replace("_", " ").replace("-", " ")

    # Check if starts with a valid atomic verb
    for verb in ATOMIC_VERBS:
        verb_pattern = verb.replace("_", " ")
        if name_lower.startswith(verb_pattern + " ") or name_lower == verb_pattern:
            return True

    return False


def is_cognitive_verb(name: str) -> bool:
    """Check if the action uses a cognitive/mental verb."""
    name_lower = name.lower().replace("_", " ").replace("-", " ")

    for verb in COGNITIVE_VERBS:
        verb_pattern = verb.replace("_", " ")
        if name_lower.startswith(verb_pattern + " ") or name_lower == verb_pattern:
            return True

    return False
