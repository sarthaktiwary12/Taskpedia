"""
Core primitives for taskpedia.

This module contains reusable building blocks:
- Thread-safe primitives (AtomicCounter, AtomicBuffer, etc.)
- File I/O helpers (YAML, JSON, JSONL)
- Rate limiting and retries
"""

from taskpedia.core.concurrent import (
    AtomicBuffer,
    AtomicCounter,
    AtomicSet,
    ProgressTracker,
    ThreadSafeStats,
    WorkQueue,
)
from taskpedia.core.io import (
    append_jsonl,
    iter_jsonl,
    load_json,
    load_json_safe,
    load_jsonl,
    load_manifest,
    load_yaml,
    load_yaml_safe,
    parse_json_from_llm,
    parse_json_from_llm_safe,
    save_json,
    save_manifest,
    save_yaml,
)
from taskpedia.core.rate_limit import (
    RateLimiter,
    RateLimitException,
    limits,
    sleep_and_retry,
)

__all__ = [
    # Concurrent primitives
    "AtomicCounter",
    "AtomicBuffer",
    "AtomicSet",
    "ProgressTracker",
    "ThreadSafeStats",
    "WorkQueue",
    # I/O helpers
    "load_yaml",
    "save_yaml",
    "load_yaml_safe",
    "load_json",
    "save_json",
    "load_json_safe",
    "load_jsonl",
    "append_jsonl",
    "iter_jsonl",
    "load_manifest",
    "save_manifest",
    "parse_json_from_llm",
    "parse_json_from_llm_safe",
    # Rate limiting (from ratelimit library)
    "limits",
    "sleep_and_retry",
    "RateLimitException",
    "RateLimiter",  # thin wrapper for .acquire() pattern
]
