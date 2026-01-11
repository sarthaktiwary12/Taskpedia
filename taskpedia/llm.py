"""
LLM Client for PRAXIS Task Decomposition.

Uses Google's Gemini 2.5 Flash for task decomposition and expansion.
The model's thinking capabilities are particularly useful for reasoning
about task hierarchies.

Usage:
    from taskpedia.llm import LLMClient

    client = LLMClient()
    result = client.decompose_task("make breakfast")

Environment Variables:
    GEMINI_API_KEY or GOOGLE_API_KEY: API key for Gemini
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Iterator

from google import genai
from google.genai import types

# Default model - Gemini 2.5 Flash
DEFAULT_MODEL = "models/gemini-2.5-flash"

# Preview model with latest improvements
PREVIEW_MODEL = "models/gemini-2.5-flash-preview-09-2025"


@dataclass
class LLMConfig:
    """Configuration for the LLM client."""

    model: str = DEFAULT_MODEL
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 8192

    # Thinking budget (0 = off, higher = more reasoning)
    # Gemini 2.5 Flash supports thinking for complex tasks
    thinking_budget: int = 1024

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class DecompositionResult:
    """Result of decomposing a task into subtasks."""

    task_name: str
    subtasks: list[dict[str, Any]]
    is_atomic: bool = False
    reasoning: str = ""
    confidence: float = 1.0
    raw_response: str = ""


class LLMClient:
    """
    Client for interacting with Gemini 2.5 Flash.

    Provides methods for task decomposition and expansion using
    the model's reasoning capabilities.
    """

    def __init__(self, config: LLMConfig | None = None, api_key: str | None = None):
        self.config = config or LLMConfig()

        # Get API key from parameter or environment
        self._api_key = (
            api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        )
        if not self._api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable, "
                "or pass api_key parameter."
            )

        # Initialize client
        self._client = genai.Client(api_key=self._api_key)

    def _get_generation_config(self, use_thinking: bool = True) -> types.GenerateContentConfig:
        """Build generation config with optional thinking."""
        config_dict = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
            "max_output_tokens": self.config.max_output_tokens,
        }

        # Add thinking config for complex reasoning tasks
        if use_thinking and self.config.thinking_budget > 0:
            config_dict["thinking_config"] = types.ThinkingConfig(
                thinking_budget=self.config.thinking_budget
            )

        return types.GenerateContentConfig(**config_dict)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        use_thinking: bool = True,
    ) -> str:
        """
        Generate a response from the model.

        Args:
            prompt: The user prompt
            system_prompt: Optional system instruction
            use_thinking: Whether to enable thinking mode

        Returns:
            The model's text response
        """
        contents = []

        if system_prompt:
            contents.append(
                types.Content(
                    role="user", parts=[types.Part.from_text(text=f"System: {system_prompt}")]
                )
            )
            contents.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part.from_text(text="Understood. I will follow these instructions.")
                    ],
                )
            )

        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        response = self._client.models.generate_content(
            model=self.config.model,
            contents=contents,
            config=self._get_generation_config(use_thinking),
        )

        return response.text

    def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        use_thinking: bool = True,
    ) -> dict[str, Any]:
        """
        Generate a JSON response from the model.

        Args:
            prompt: The user prompt (should ask for JSON output)
            system_prompt: Optional system instruction
            use_thinking: Whether to enable thinking mode

        Returns:
            Parsed JSON response
        """
        response_text = self.generate(prompt, system_prompt, use_thinking)

        # Extract JSON from response (handle markdown code blocks)
        json_text = response_text.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        elif json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        json_text = json_text.strip()

        return json.loads(json_text)

    def decompose_task(
        self,
        task_name: str,
        task_description: str = "",
        parent_context: str = "",
        depth: int = 0,
    ) -> DecompositionResult:
        """
        Decompose a task into subtasks.

        Uses the model's reasoning capabilities to break down
        a task into logical subtasks that together achieve the goal.

        Args:
            task_name: Name of the task to decompose
            task_description: Optional description of the task
            parent_context: Context from parent tasks in hierarchy
            depth: Current depth in the hierarchy

        Returns:
            DecompositionResult with subtasks
        """
        system_prompt = """You are an expert at analyzing human tasks and breaking them down into logical subtasks.
Your goal is to decompose tasks into their component parts that together achieve the task's goal.

Rules:
1. Each subtask should be a distinct, meaningful action
2. Subtasks should be ordered logically (temporal or dependency order)
3. A task with 1-2 very simple actions is ATOMIC (cannot be decomposed further)
4. Return 3-10 subtasks for non-atomic tasks
5. Include brief descriptions for each subtask
6. Be concrete and specific, not vague

Output JSON format:
{
    "is_atomic": boolean,
    "reasoning": "brief explanation of your decomposition logic",
    "confidence": 0.0-1.0,
    "subtasks": [
        {
            "name": "subtask name",
            "description": "what this subtask accomplishes",
            "is_likely_atomic": boolean
        }
    ]
}"""

        prompt = f"""Decompose this task into subtasks:

Task: {task_name}
{f'Description: {task_description}' if task_description else ''}
{f'Context: {parent_context}' if parent_context else ''}
Current depth: {depth}

Analyze whether this is an atomic task (cannot be meaningfully decomposed) or can be broken into subtasks.
Return your analysis as JSON."""

        try:
            result = self.generate_json(prompt, system_prompt, use_thinking=True)

            return DecompositionResult(
                task_name=task_name,
                subtasks=result.get("subtasks", []),
                is_atomic=result.get("is_atomic", False),
                reasoning=result.get("reasoning", ""),
                confidence=result.get("confidence", 0.8),
                raw_response=json.dumps(result),
            )
        except Exception as e:
            # Return as atomic on error
            return DecompositionResult(
                task_name=task_name,
                subtasks=[],
                is_atomic=True,
                reasoning=f"Error during decomposition: {e}",
                confidence=0.0,
            )

    def expand_domain(
        self,
        domain_name: str,
        existing_tasks: list[str],
        count: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Generate additional tasks for a domain.

        Args:
            domain_name: Name of the domain to expand
            existing_tasks: List of tasks already in this domain
            count: Number of new tasks to generate

        Returns:
            List of new task dictionaries
        """
        system_prompt = """You are an expert at identifying human tasks within specific domains.
Generate diverse, concrete tasks that humans perform in the given domain.

Rules:
1. Tasks should be specific and actionable
2. Avoid duplicating existing tasks
3. Cover different aspects of the domain
4. Include both common and specialized tasks
5. Tasks should be verifiable (clear completion criteria)

Output JSON format:
{
    "tasks": [
        {
            "name": "task name",
            "description": "what this task accomplishes",
            "typical_context": "where/when this is performed",
            "tags": ["tag1", "tag2"]
        }
    ]
}"""

        existing_sample = existing_tasks[:20] if len(existing_tasks) > 20 else existing_tasks

        prompt = f"""Generate {count} new tasks for this domain:

Domain: {domain_name}

Existing tasks (avoid duplicates):
{chr(10).join(f'- {t}' for t in existing_sample)}

Generate {count} diverse new tasks that are NOT in the existing list.
Return as JSON."""

        try:
            result = self.generate_json(prompt, system_prompt, use_thinking=True)
            return result.get("tasks", [])
        except Exception as e:
            print(f"Error expanding domain: {e}")
            return []

    def generate_completion_criteria(
        self,
        task_name: str,
        task_description: str = "",
    ) -> dict[str, str]:
        """
        Generate completion criteria for a task.

        Args:
            task_name: Name of the task
            task_description: Optional description

        Returns:
            Dictionary with precondition, postcondition, invariants
        """
        system_prompt = """You are an expert at defining precise, verifiable completion criteria for tasks.
For any task, you identify:
1. Preconditions: What must be true BEFORE starting
2. Postconditions: What must be true AFTER successful completion
3. Invariants: What must remain true THROUGHOUT execution

Be specific and measurable. Focus on observable states, not intentions.

Output JSON format:
{
    "precondition": "required initial state",
    "postcondition": "required final state for success",
    "invariants": "constraints that must hold throughout"
}"""

        prompt = f"""Define completion criteria for this task:

Task: {task_name}
{f'Description: {task_description}' if task_description else ''}

What are the preconditions, postconditions, and invariants?
Return as JSON."""

        try:
            return self.generate_json(prompt, system_prompt, use_thinking=False)
        except Exception as e:
            return {
                "precondition": "",
                "postcondition": "",
                "invariants": "",
            }

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """
        Stream a response from the model.

        Args:
            prompt: The user prompt
            system_prompt: Optional system instruction

        Yields:
            Text chunks as they are generated
        """
        contents = []

        if system_prompt:
            contents.append(
                types.Content(
                    role="user", parts=[types.Part.from_text(text=f"System: {system_prompt}")]
                )
            )
            contents.append(
                types.Content(role="model", parts=[types.Part.from_text(text="Understood.")])
            )

        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        # Note: Streaming with thinking may behave differently
        config = self._get_generation_config(use_thinking=False)

        for chunk in self._client.models.generate_content_stream(
            model=self.config.model,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text

    def close(self):
        """Close the client and release resources."""
        if hasattr(self._client, "close"):
            self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# Convenience function
def get_client(
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    **kwargs,
) -> LLMClient:
    """
    Get an LLM client with the specified configuration.

    Args:
        model: Model to use (default: gemini-2.5-flash)
        api_key: Optional API key
        **kwargs: Additional config options

    Returns:
        Configured LLMClient
    """
    config = LLMConfig(model=model, **kwargs)
    return LLMClient(config=config, api_key=api_key)
