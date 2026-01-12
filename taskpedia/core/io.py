"""
File I/O helpers for consistent YAML/JSON handling.

This module provides unified file operations used across the codebase.
Handles errors consistently and provides type-safe operations.

Usage:
    from taskpedia.io import (
        load_yaml,
        save_yaml,
        load_json,
        save_json,
        load_manifest,
        save_manifest,
    )
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, TypeVar

import yaml

log = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# YAML OPERATIONS
# ============================================================================


def load_yaml(path: Path | str) -> dict[str, Any]:
    """
    Load a YAML file.

    Args:
        path: Path to YAML file

    Returns:
        Parsed YAML content as dict

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(data: dict[str, Any], path: Path | str) -> None:
    """
    Save data to a YAML file.

    Args:
        data: Data to save
        path: Path to YAML file
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )


def load_yaml_safe(path: Path | str, default: T = None) -> dict[str, Any] | T:
    """
    Load YAML file, returning default if file doesn't exist or is invalid.

    Args:
        path: Path to YAML file
        default: Value to return on error

    Returns:
        Parsed YAML or default
    """
    try:
        return load_yaml(path)
    except (FileNotFoundError, yaml.YAMLError) as e:
        log.debug(f"Could not load YAML {path}: {e}")
        return default


# ============================================================================
# JSON OPERATIONS
# ============================================================================


def load_json(path: Path | str) -> dict[str, Any]:
    """
    Load a JSON file.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON content

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict[str, Any], path: Path | str, indent: int = 2) -> None:
    """
    Save data to a JSON file.

    Args:
        data: Data to save
        path: Path to JSON file
        indent: Indentation level (default: 2)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_json_safe(path: Path | str, default: T = None) -> dict[str, Any] | T:
    """
    Load JSON file, returning default if file doesn't exist or is invalid.

    Args:
        path: Path to JSON file
        default: Value to return on error

    Returns:
        Parsed JSON or default
    """
    try:
        return load_json(path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log.debug(f"Could not load JSON {path}: {e}")
        return default


# ============================================================================
# JSONL OPERATIONS
# ============================================================================


def append_jsonl(data: dict[str, Any], path: Path | str) -> None:
    """
    Append a single JSON object to a JSONL file.

    Args:
        data: Single record to append
        path: Path to JSONL file
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def load_jsonl(path: Path | str) -> list[dict[str, Any]]:
    """
    Load all records from a JSONL file.

    Args:
        path: Path to JSONL file

    Returns:
        List of parsed JSON objects
    """
    path = Path(path)
    if not path.exists():
        return []

    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def iter_jsonl(path: Path | str):
    """
    Iterate over records in a JSONL file (memory efficient).

    Args:
        path: Path to JSONL file

    Yields:
        Parsed JSON objects
    """
    path = Path(path)
    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


# ============================================================================
# MANIFEST OPERATIONS (specialized for TaskGraph)
# ============================================================================

MANIFEST_FILENAME = "_manifest.json"


def load_manifest(task_dir: Path | str) -> dict[str, Any]:
    """
    Load the task hierarchy manifest.

    Args:
        task_dir: Task hierarchy directory

    Returns:
        Manifest data (nodes dict, metadata)
    """
    path = Path(task_dir) / MANIFEST_FILENAME
    return load_json_safe(path, {"nodes": {}, "version": 1})


def save_manifest(task_dir: Path | str, manifest: dict[str, Any]) -> None:
    """
    Save the task hierarchy manifest.

    Args:
        task_dir: Task hierarchy directory
        manifest: Manifest data to save
    """
    path = Path(task_dir) / MANIFEST_FILENAME
    save_json(manifest, path)


# ============================================================================
# LLM RESPONSE PARSING
# ============================================================================


def parse_json_from_llm(response: str) -> dict[str, Any]:
    """
    Parse JSON from an LLM response, handling markdown code blocks.

    Args:
        response: Raw LLM response text

    Returns:
        Parsed JSON object

    Raises:
        json.JSONDecodeError: If no valid JSON found
    """
    json_text = response.strip()

    # Handle ```json blocks
    if "```json" in json_text:
        parts = json_text.split("```json")
        if len(parts) > 1:
            json_text = parts[1].split("```")[0]
    elif "```" in json_text:
        parts = json_text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("{") or part.startswith("["):
                json_text = part
                break

    return json.loads(json_text.strip())


def parse_json_from_llm_safe(
    response: str,
    default: T = None,
) -> dict[str, Any] | T:
    """
    Parse JSON from LLM response, returning default on failure.

    Args:
        response: Raw LLM response text
        default: Value to return on error

    Returns:
        Parsed JSON or default
    """
    try:
        return parse_json_from_llm(response)
    except (json.JSONDecodeError, IndexError) as e:
        log.debug(f"Could not parse LLM JSON: {e}")
        return default
