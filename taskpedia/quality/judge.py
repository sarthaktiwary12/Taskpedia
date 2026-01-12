"""
Task quality judge system (regex + LLM judge).

Two-stage judging:
1. Fast regex patterns for obvious failures (robot internals, templates)
2. LLM judge for nuanced cases (optional, slower but more accurate)

All rejections are logged for prompt improvement analysis.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from taskpedia.core import append_jsonl, load_jsonl, parse_json_from_llm
from taskpedia.data import (
    is_generic_template,
    is_robot_internal,
)
from taskpedia.generation import LLMClient, MockLLMClient

log = logging.getLogger(__name__)

# ============================================================================
# REJECT LOG - For self-improvement
# ============================================================================

REJECT_LOG_PATH = Path("./taskpedia_rejects.jsonl")


@dataclass
class Rejection:
    """Record of a rejected task."""

    name: str
    description: str
    reason: str  # regex_robot_internal | regex_generic | llm_judge
    pattern: str | None  # Which regex pattern matched (if regex)
    judge_reasoning: str | None  # LLM judge explanation (if LLM)
    parent_context: str | None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "reason": self.reason,
            "pattern": self.pattern,
            "judge_reasoning": self.judge_reasoning,
            "parent_context": self.parent_context,
            "timestamp": self.timestamp,
        }


class RejectLog:
    """Thread-safe reject log for quality analysis."""

    def __init__(self, log_path: Path = REJECT_LOG_PATH):
        self.log_path = log_path
        self._lock = threading.Lock()
        self._buffer: list[Rejection] = []
        self._buffer_size = 100  # Flush every 100 rejects

    def log_reject(self, rejection: Rejection):
        """Log a rejection."""
        with self._lock:
            self._buffer.append(rejection)
            if len(self._buffer) >= self._buffer_size:
                self._flush()

    def _flush(self):
        """Write buffer to disk."""
        if not self._buffer:
            return

        for rejection in self._buffer:
            append_jsonl(rejection.to_dict(), self.log_path)
        self._buffer.clear()

    def flush(self):
        """Public flush method."""
        with self._lock:
            self._flush()

    def read_all(self) -> list[Rejection]:
        """Read all rejections from log."""
        records = load_jsonl(self.log_path)
        return [
            Rejection(
                name=data["name"],
                description=data.get("description", ""),
                reason=data["reason"],
                pattern=data.get("pattern"),
                judge_reasoning=data.get("judge_reasoning"),
                parent_context=data.get("parent_context"),
                timestamp=data["timestamp"],
            )
            for data in records
        ]

    def analyze(self) -> dict[str, Any]:
        """Analyze reject patterns."""
        rejections = self.read_all()
        if not rejections:
            return {"total": 0}

        # Count by reason
        reason_counts: dict[str, int] = {}
        pattern_counts: dict[str, int] = {}

        for r in rejections:
            reason_counts[r.reason] = reason_counts.get(r.reason, 0) + 1
            if r.pattern:
                pattern_counts[r.pattern] = pattern_counts.get(r.pattern, 0) + 1

        # Most common rejected patterns
        top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Sample rejected names
        samples = [r.name for r in rejections[-20:]]

        return {
            "total": len(rejections),
            "by_reason": reason_counts,
            "top_patterns": top_patterns,
            "recent_samples": samples,
        }

    def clear(self):
        """Clear the log file."""
        if self.log_path.exists():
            self.log_path.unlink()
        with self._lock:
            self._buffer.clear()


# Global reject log
_reject_log: RejectLog | None = None


def get_reject_log() -> RejectLog:
    """Get or create global reject log."""
    global _reject_log
    if _reject_log is None:
        _reject_log = RejectLog()
    return _reject_log


# ============================================================================
# REGEX JUDGE - Fast pattern matching
# ============================================================================
# NOTE: Pattern definitions are in taskpedia/patterns.py (single source of truth)


class RegexJudge:
    """Fast regex-based task quality judge."""

    def __init__(self, log_rejects: bool = True):
        self.log_rejects = log_rejects
        self.reject_log = get_reject_log() if log_rejects else None

    def judge(
        self,
        name: str,
        description: str = "",
        parent_context: str | None = None,
    ) -> tuple[bool, str | None]:
        """
        Judge task quality using regex patterns.

        Uses patterns from taskpedia.patterns (single source of truth).

        Returns:
            (is_valid, rejection_reason)
        """
        # Check robot-internal (uses patterns.is_robot_internal)
        internal, pattern = is_robot_internal(name)
        if internal:
            if self.log_rejects and self.reject_log:
                self.reject_log.log_reject(
                    Rejection(
                        name=name,
                        description=description,
                        reason="regex_robot_internal",
                        pattern=pattern,
                        judge_reasoning=None,
                        parent_context=parent_context,
                    )
                )
            return False, f"robot_internal: {pattern}"

        # Check generic template (uses patterns.is_generic_template)
        if is_generic_template(name, description):
            if self.log_rejects and self.reject_log:
                self.reject_log.log_reject(
                    Rejection(
                        name=name,
                        description=description,
                        reason="regex_generic",
                        pattern="generic_template",
                        judge_reasoning=None,
                        parent_context=parent_context,
                    )
                )
            return False, "generic_template"

        return True, None


# ============================================================================
# LLM JUDGE - Nuanced quality assessment
# ============================================================================

LLM_JUDGE_PROMPT = """You are a task quality judge for robot training data.

Evaluate if this task is suitable for training embodied AI from video demonstrations.

VALID tasks:
- Observable actions recordable on video (reach, grasp, walk, look, speak)
- Human-demonstrable motions
- Physical interactions with objects
- Navigation and movement
- Perception actions (look at, scan, read)
- Communication (say, point, gesture)

INVALID tasks:
- Robot control internals (joint torques, motor commands, trajectories)
- Body mechanics (muscle activation, joint angles, force calculations)
- Abstract mental operations not observable in video
- Generic templates ("check equipment", "prepare materials")
- Data processing or computation steps

Return JSON:
{
    "valid": true/false,
    "reasoning": "brief explanation",
    "confidence": 0.0-1.0
}"""


class LLMJudge:
    """LLM-based task quality judge."""

    def __init__(
        self,
        client: LLMClient | MockLLMClient,
        log_rejects: bool = True,
    ):
        self.client = client
        self.log_rejects = log_rejects
        self.reject_log = get_reject_log() if log_rejects else None

    def judge(
        self,
        name: str,
        description: str = "",
        parent_context: str | None = None,
    ) -> tuple[bool, str | None, str | None]:
        """
        Judge task quality using LLM.

        Returns:
            (is_valid, rejection_reason, reasoning)
        """
        prompt = f"""Task: {name}
Description: {description}
Context: {parent_context or 'None'}

Is this task valid for robot training?
Return JSON."""

        try:
            response = self.client.generate(prompt, LLM_JUDGE_PROMPT, use_thinking=False)
            result = parse_json_from_llm(response)
            is_valid = result.get("valid", True)
            reasoning = result.get("reasoning", "")

            if not is_valid and self.log_rejects:
                self.reject_log.log_reject(
                    Rejection(
                        name=name,
                        description=description,
                        reason="llm_judge",
                        pattern=None,
                        judge_reasoning=reasoning,
                        parent_context=parent_context,
                    )
                )

            return is_valid, None if is_valid else "llm_judge", reasoning

        except Exception as e:
            log.error(f"LLM judge error: {e}")
            # On error, accept (fail open)
            return True, None, f"judge_error: {e}"


# ============================================================================
# HYBRID JUDGE - Regex + LLM
# ============================================================================


class HybridJudge:
    """
    Two-stage judge: fast regex first, then optional LLM.

    Usage:
        judge = HybridJudge(client, use_llm=True)
        is_valid, reason = judge.judge("grasp object", "pick up the cup")
    """

    def __init__(
        self,
        client: LLMClient | MockLLMClient | None = None,
        use_llm: bool = False,
        log_rejects: bool = True,
    ):
        self.regex_judge = RegexJudge(log_rejects=log_rejects)
        self.llm_judge = LLMJudge(client, log_rejects=log_rejects) if (use_llm and client) else None
        self.use_llm = use_llm and client is not None

    def judge(
        self,
        name: str,
        description: str = "",
        parent_context: str | None = None,
    ) -> tuple[bool, str | None]:
        """
        Judge task quality.

        Returns:
            (is_valid, rejection_reason)
        """
        # Stage 1: Regex (fast)
        is_valid, reason = self.regex_judge.judge(name, description, parent_context)
        if not is_valid:
            return False, reason

        # Stage 2: LLM (optional, slower but more accurate)
        if self.use_llm and self.llm_judge:
            is_valid, reason, _reasoning = self.llm_judge.judge(name, description, parent_context)
            return is_valid, reason

        return True, None
