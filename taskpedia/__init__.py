"""
TASKPEDIA: Hierarchical Decomposition of Human Tasks.

A comprehensive taxonomy of ALL human activities, built as a
filesystem-backed directed acyclic graph (DAG).

Submodules:
    core - Thread-safe primitives, I/O helpers, rate limiting
    data - Patterns, domains, verb taxonomies
    quality - Task quality judging (regex + LLM)
    generation - LLM client, request queue

Legacy modules (being refactored):
    hierarchy - TaskNode, TaskGraph data structures
    generator - Fast synthetic data generation
    validation - Task validation utilities
    qa - QA tests and domain coverage
    cli - Command-line interface
"""

__version__ = "0.4.0"

# Re-export from submodules for backward compatibility
from taskpedia.core import (
    AtomicBuffer,
    AtomicCounter,
    AtomicSet,
    RateLimiter,
    ThreadSafeStats,
    WorkQueue,
    append_jsonl,
    load_json,
    load_jsonl,
    load_yaml,
    parse_json_from_llm,
    save_json,
    save_yaml,
)
from taskpedia.data import (
    ATOMIC_VERBS,
    COGNITIVE_VERBS,
    DOMAIN_COVERAGE,
    GENERIC_NOUNS,
    GENERIC_VERBS,
    ROBOT_INTERNAL_PATTERNS,
    is_cognitive_verb,
    is_generic_template,
    is_robot_internal,
    validate_task_name,
)

# Legacy imports (still at root level, to be moved)
from taskpedia.hierarchy import NodeType, SeedSource, TaskGraph, TaskNode

# Lazy imports for modules with external dependencies (google-genai)
# These are imported on first access to avoid ImportError when deps missing

_generation_exports = None
_quality_exports = None


def __getattr__(name):
    """Lazy import for modules with external dependencies."""
    global _generation_exports, _quality_exports

    # Generation module exports (requires google-genai)
    generation_names = {
        "LLMClient",
        "LLMConfig",
        "LLMQueue",
        "LLMRequest",
        "LLMResponse",
        "MockLLMClient",
    }
    if name in generation_names:
        if _generation_exports is None:
            from taskpedia.generation import (
                LLMClient,
                LLMConfig,
                LLMQueue,
                LLMRequest,
                LLMResponse,
                MockLLMClient,
            )

            _generation_exports = {
                "LLMClient": LLMClient,
                "LLMConfig": LLMConfig,
                "LLMQueue": LLMQueue,
                "LLMRequest": LLMRequest,
                "LLMResponse": LLMResponse,
                "MockLLMClient": MockLLMClient,
            }
        return _generation_exports[name]

    # Quality module exports (depends on generation)
    quality_names = {
        "RegexJudge",
        "LLMJudge",
        "HybridJudge",
        "Rejection",
        "RejectLog",
        "get_reject_log",
    }
    if name in quality_names:
        if _quality_exports is None:
            from taskpedia.quality import (
                HybridJudge,
                LLMJudge,
                RegexJudge,
                Rejection,
                RejectLog,
                get_reject_log,
            )

            from taskpedia.quality import (
                HybridJudge,
                LLMJudge,
                RegexJudge,
                Rejection,
                RejectLog,
                get_reject_log,
            )
            _quality_exports = {
                "RegexJudge": RegexJudge,
                "LLMJudge": LLMJudge,
                "HybridJudge": HybridJudge,
                "Rejection": Rejection,
                "RejectLog": RejectLog,
                "get_reject_log": get_reject_log,
            }
        return _quality_exports[name]

    raise AttributeError(f"module 'taskpedia' has no attribute {name!r}")


__all__ = [
    # Core primitives
    "AtomicCounter",
    "AtomicBuffer",
    "AtomicSet",
    "ThreadSafeStats",
    "WorkQueue",
    "RateLimiter",
    # I/O helpers
    "load_yaml",
    "save_yaml",
    "load_json",
    "save_json",
    "load_jsonl",
    "append_jsonl",
    "parse_json_from_llm",
    # Data patterns
    "ROBOT_INTERNAL_PATTERNS",
    "GENERIC_VERBS",
    "GENERIC_NOUNS",
    "COGNITIVE_VERBS",
    "ATOMIC_VERBS",
    "DOMAIN_COVERAGE",
    "is_robot_internal",
    "is_generic_template",
    "is_cognitive_verb",
    "validate_task_name",
    # Quality (lazy)
    "RegexJudge",
    "LLMJudge",
    "HybridJudge",
    "Rejection",
    "RejectLog",
    "get_reject_log",
    # Generation (lazy)
    "LLMClient",
    "LLMConfig",
    "MockLLMClient",
    "LLMQueue",
    "LLMRequest",
    "LLMResponse",
    # Hierarchy
    "TaskNode",
    "TaskGraph",
    "NodeType",
    "SeedSource",
]
