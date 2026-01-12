"""
Data definitions and taxonomies.

This module contains:
- Validation patterns (robot internals, generic templates)
- Domain coverage definitions
- Verb taxonomies (atomic, cognitive)
- Activity taxonomies (life domains, work domains)
"""

from taskpedia.data.domains import (
    DOMAIN_COVERAGE,
    DomainCoverage,
    check_domain_coverage,
    get_all_expected_verbs,
    get_expected_verbs,
    run_coverage_report,
)
from taskpedia.data.patterns import (
    COGNITIVE_VERBS,
    GENERIC_NOUNS,
    GENERIC_VERBS,
    ROBOT_INTERNAL_PATTERNS,
    is_cognitive_verb,
    is_generic_template,
    is_robot_internal,
    is_valid_atomic,
    validate_task_name,
)
from taskpedia.data.verbs import (
    ATOMIC_VERBS,
    get_action_categories_summary,
    get_atomic_verb_categories,
)

__all__ = [
    # Patterns
    "ROBOT_INTERNAL_PATTERNS",
    "GENERIC_VERBS",
    "GENERIC_NOUNS",
    "COGNITIVE_VERBS",
    "is_robot_internal",
    "is_generic_template",
    "is_cognitive_verb",
    "is_valid_atomic",
    "validate_task_name",
    # Domains
    "DOMAIN_COVERAGE",
    "DomainCoverage",
    "get_expected_verbs",
    "get_all_expected_verbs",
    "check_domain_coverage",
    "run_coverage_report",
    # Verbs
    "ATOMIC_VERBS",
    "get_atomic_verb_categories",
    "get_action_categories_summary",
]
