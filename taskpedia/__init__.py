"""
TASKPEDIA: Hierarchical Decomposition of Human Tasks.

A comprehensive taxonomy of ALL human activities, built as a
filesystem-backed directed acyclic graph (DAG).

Core modules:
    hierarchy - TaskNode, TaskGraph data structures
    generator - Fast synthetic data generation (ThreadPool-based)
    verbs - Verb taxonomies (ATOMIC_VERBS, COGNITIVE_VERBS)
    validation - Task validation utilities
    qa - QA tests and domain coverage
    llm - LLM client (Gemini 2.5 Flash)
    seeds - Seed data from O*NET, ATUS, etc.
    cli - Command-line interface

Quick start:
    # Bootstrap from seed data
    taskpedia bootstrap -o ./tasks

    # Generate synthetic tasks
    taskpedia generate -o ./tasks --max-tasks 1000

    # View hierarchy
    taskpedia tree -o ./tasks
"""

__version__ = "0.3.0"

from taskpedia.generator import FastGenConfig, FastGenerator
from taskpedia.hierarchy import NodeType, SeedSource, TaskGraph, TaskNode
from taskpedia.llm import LLMClient, LLMConfig
from taskpedia.validation import is_generic_template, is_valid_atomic
from taskpedia.verbs import ATOMIC_VERBS, COGNITIVE_VERBS

__all__ = [
    # Core data structures
    "TaskNode",
    "TaskGraph",
    "NodeType",
    "SeedSource",
    # Verbs
    "ATOMIC_VERBS",
    "COGNITIVE_VERBS",
    # Validation
    "is_generic_template",
    "is_valid_atomic",
    # Generation
    "FastGenerator",
    "FastGenConfig",
    # LLM
    "LLMClient",
    "LLMConfig",
]
