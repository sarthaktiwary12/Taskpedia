"""
Self-improvement system using reject log analysis.

Analyzes rejected tasks to identify patterns and suggest prompt improvements.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from taskpedia.generation import LLMClient, MockLLMClient
from taskpedia.quality.judge import RejectLog, get_reject_log

log = logging.getLogger(__name__)

IMPROVE_SYSTEM_PROMPT = """You are an expert at analyzing failed LLM outputs and improving prompts.

Given a log of rejected task decompositions, identify patterns in the failures
and suggest specific improvements to the system prompt.

Focus on:
1. Common error patterns (e.g., always generates robot internals for certain task types)
2. Ambiguous instructions that lead to wrong outputs
3. Missing examples or clarifications
4. Overly broad or narrow constraints

Return specific, actionable prompt improvements."""


class PromptImprover:
    """
    Analyzes reject logs and suggests prompt improvements.

    Usage:
        improver = PromptImprover(client)
        suggestions = improver.analyze_and_suggest()
        print(suggestions)
    """

    def __init__(
        self,
        client: LLMClient | MockLLMClient,
        reject_log: RejectLog | None = None,
    ):
        self.client = client
        self.reject_log = reject_log or get_reject_log()

    def analyze_patterns(self) -> dict[str, Any]:
        """Analyze rejection patterns."""
        rejections = self.reject_log.read_all()
        if not rejections:
            return {"error": "No rejections to analyze"}

        # Count by reason
        reason_counts = Counter(r.reason for r in rejections)

        # Most common patterns
        pattern_counts = Counter(r.pattern for r in rejections if r.pattern)

        # Sample names by reason
        samples_by_reason: dict[str, list[str]] = {}
        for r in rejections:
            if r.reason not in samples_by_reason:
                samples_by_reason[r.reason] = []
            if len(samples_by_reason[r.reason]) < 10:
                samples_by_reason[r.reason].append(r.name)

        # LLM judge reasonings
        llm_rejections = [r for r in rejections if r.reason == "llm_judge"]
        llm_reasonings = [r.judge_reasoning for r in llm_rejections if r.judge_reasoning][:20]

        return {
            "total_rejects": len(rejections),
            "by_reason": dict(reason_counts),
            "top_patterns": pattern_counts.most_common(10),
            "samples_by_reason": samples_by_reason,
            "llm_reasonings": llm_reasonings,
        }

    def suggest_improvements(self, current_prompt: str) -> str:
        """
        Suggest prompt improvements based on reject log.

        Args:
            current_prompt: The current system prompt

        Returns:
            Suggested improvements as text
        """
        analysis = self.analyze_patterns()
        if "error" in analysis:
            return "Not enough data for analysis."

        # Build analysis report
        report = f"""Rejection Analysis:
- Total rejections: {analysis['total_rejects']}
- By reason: {analysis['by_reason']}

Top rejection patterns:
{self._format_patterns(analysis['top_patterns'])}

Sample rejected names by reason:
{self._format_samples(analysis['samples_by_reason'])}

LLM judge reasonings (recent):
{self._format_reasonings(analysis['llm_reasonings'])}

Current system prompt:
{current_prompt}

Based on these rejections, what specific changes should be made to the system prompt
to reduce these failure modes? Provide concrete suggestions."""

        try:
            suggestions = self.client.generate(report, IMPROVE_SYSTEM_PROMPT, use_thinking=True)
            return suggestions
        except Exception as e:
            log.error(f"Error generating suggestions: {e}")
            return f"Error: {e}"

    def _format_patterns(self, patterns: list[tuple[str, int]]) -> str:
        """Format pattern counts."""
        if not patterns:
            return "  (none)"
        return "\n".join(f"  - {pattern}: {count}x" for pattern, count in patterns)

    def _format_samples(self, samples: dict[str, list[str]]) -> str:
        """Format sample names."""
        lines = []
        for reason, names in samples.items():
            lines.append(f"  {reason}:")
            for name in names[:5]:
                lines.append(f"    - {name}")
        return "\n".join(lines) if lines else "  (none)"

    def _format_reasonings(self, reasonings: list[str]) -> str:
        """Format LLM reasonings."""
        if not reasonings:
            return "  (none)"
        return "\n".join(f"  - {r}" for r in reasonings[:10])

    def generate_improved_prompt(self, current_prompt: str, apply_suggestions: bool = False) -> str:
        """
        Generate an improved version of the prompt.

        Args:
            current_prompt: Current system prompt
            apply_suggestions: If True, use LLM to rewrite prompt with suggestions

        Returns:
            Improved prompt (or just suggestions if apply_suggestions=False)
        """
        suggestions = self.suggest_improvements(current_prompt)

        if not apply_suggestions:
            return suggestions

        # Use LLM to rewrite prompt incorporating suggestions
        rewrite_prompt = f"""Current system prompt:
{current_prompt}

Suggested improvements:
{suggestions}

Rewrite the system prompt incorporating these improvements.
Keep the same structure but fix the identified issues.
Return only the rewritten prompt, no commentary."""

        try:
            improved = self.client.generate(
                rewrite_prompt,
                "You rewrite prompts to incorporate feedback.",
                use_thinking=True,
            )
            return improved
        except Exception as e:
            log.error(f"Error rewriting prompt: {e}")
            return suggestions


def analyze_rejects(
    client: LLMClient | MockLLMClient,
    current_prompt: str,
    apply_suggestions: bool = False,
) -> str:
    """
    Convenience function to analyze rejects and suggest improvements.

    Args:
        client: LLM client
        current_prompt: Current system prompt
        apply_suggestions: If True, generate rewritten prompt

    Returns:
        Suggestions or improved prompt
    """
    improver = PromptImprover(client)
    return improver.generate_improved_prompt(current_prompt, apply_suggestions)
