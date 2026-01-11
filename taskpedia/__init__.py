"""
TASKPEDIA: Hierarchical Decomposition of Human Tasks.

A comprehensive taxonomy of ALL human activities, built as a
filesystem-backed directed acyclic graph (DAG).

Core modules:
    hierarchy - TaskNode, TaskGraph data structures
    generate - Synthetic data generation pipeline
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

from taskpedia.generate import GenerationConfig, TaskGenerator, run_generation
from taskpedia.hierarchy import NodeType, SeedSource, TaskGraph, TaskNode
from taskpedia.llm import LLMClient, LLMConfig

__all__ = [
    # Core data structures
    "TaskNode",
    "TaskGraph",
    "NodeType",
    "SeedSource",
    # Generation
    "TaskGenerator",
    "GenerationConfig",
    "run_generation",
    # LLM
    "LLMClient",
    "LLMConfig",
]
