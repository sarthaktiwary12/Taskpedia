"""
LLM Client for TASKPEDIA Task Decomposition.

Uses Google's Gemini 2.5 Flash for task decomposition and expansion.
The model's thinking capabilities are particularly useful for reasoning
about task hierarchies.

Usage:
    from taskpedia.llm import LLMClient

    client = LLMClient()
    result = client.decompose_task("make breakfast")

    # For testing without API calls:
    from taskpedia.llm import MockLLMClient
    client = MockLLMClient()

Environment Variables:
    GEMINI_API_KEY or GOOGLE_API_KEY: API key for Gemini
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from diskcache import Cache
from google import genai
from google.genai import types

# ============================================================================
# LLM Response Cache
# ============================================================================

# Cache directory
CACHE_DIR = Path("./.taskpedia_cache")

# Cache TTL (365 days - LLM responses don't expire)
CACHE_TTL = 365 * 24 * 60 * 60


def _get_cache_key(
    prompt: str,
    system_prompt: str | None,
    model: str,
    temperature: float,
    use_thinking: bool,
) -> str:
    """Generate a unique cache key for an LLM request."""
    key_data = json.dumps(
        {
            "prompt": prompt,
            "system_prompt": system_prompt or "",
            "model": model,
            "temperature": temperature,
            "use_thinking": use_thinking,
        },
        sort_keys=True,
    )
    return hashlib.sha256(key_data.encode()).hexdigest()


class LLMCache:
    """
    Disk-based cache for LLM responses.

    Caches responses keyed by (prompt, system_prompt, model, temperature, use_thinking).
    Saves significant API costs by avoiding redundant calls.
    """

    def __init__(self, cache_dir: Path | str = CACHE_DIR, enabled: bool = True):
        self.enabled = enabled
        self.cache_dir = Path(cache_dir)
        self._cache: Cache | None = None
        self.hits = 0
        self.misses = 0

    @property
    def cache(self) -> Cache:
        """Lazy-initialize the cache."""
        if self._cache is None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache = Cache(str(self.cache_dir))
        return self._cache

    def get(
        self,
        prompt: str,
        system_prompt: str | None,
        model: str,
        temperature: float,
        use_thinking: bool,
    ) -> str | None:
        """Get cached response if available."""
        if not self.enabled:
            return None

        key = _get_cache_key(prompt, system_prompt, model, temperature, use_thinking)
        result = self.cache.get(key)

        if result is not None:
            self.hits += 1
        else:
            self.misses += 1

        return result

    def set(
        self,
        prompt: str,
        system_prompt: str | None,
        model: str,
        temperature: float,
        use_thinking: bool,
        response: str,
    ) -> None:
        """Cache a response."""
        if not self.enabled:
            return

        key = _get_cache_key(prompt, system_prompt, model, temperature, use_thinking)
        self.cache.set(key, response, expire=CACHE_TTL)

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate": hit_rate,
            "entries": len(self.cache) if self._cache else 0,
            "size_mb": self.cache.volume() / 1024 / 1024 if self._cache else 0,
        }

    def clear(self) -> int:
        """Clear all cached responses. Returns number of entries cleared."""
        if self._cache:
            count = len(self._cache)
            self._cache.clear()
            return count
        return 0

    def close(self):
        """Close the cache."""
        if self._cache:
            self._cache.close()
            self._cache = None


# Global cache instance
_global_cache: LLMCache | None = None


def get_cache(enabled: bool = True) -> LLMCache:
    """Get or create the global LLM cache."""
    global _global_cache
    if _global_cache is None:
        _global_cache = LLMCache(enabled=enabled)
    return _global_cache


# Default model - Gemini 2.5 Flash
DEFAULT_MODEL = "models/gemini-2.5-flash"

# Preview model with latest improvements
PREVIEW_MODEL = "models/gemini-2.5-flash-preview-09-2025"

# Gemini 2.5 Flash pricing (as of Jan 2025)
# Input: $0.075 per 1M tokens, Output: $0.30 per 1M tokens
# Thinking: $0.075 per 1M tokens
PRICING = {
    "models/gemini-2.5-flash": {
        "input_per_1m": 0.075,
        "output_per_1m": 0.30,
        "thinking_per_1m": 0.075,
    },
    "models/gemini-2.5-pro": {
        "input_per_1m": 1.25,
        "output_per_1m": 10.00,
        "thinking_per_1m": 1.25,
    },
}


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

    # Cache settings
    cache_enabled: bool = True
    cache_dir: str = "./.taskpedia_cache"


@dataclass
class DecompositionResult:
    """Result of decomposing a task into subtasks."""

    task_name: str
    subtasks: list[dict[str, Any]]
    is_atomic: bool = False
    reasoning: str = ""
    confidence: float = 1.0
    raw_response: str = ""


@dataclass
class UsageStats:
    """Token usage and cost statistics."""

    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    requests: int = 0

    def add(self, input_tokens: int, output_tokens: int, thinking_tokens: int = 0):
        """Add usage from a request."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.thinking_tokens += thinking_tokens
        self.requests += 1

    def get_cost(self, model: str = DEFAULT_MODEL) -> float:
        """Calculate total cost in USD."""
        pricing = PRICING.get(model, PRICING[DEFAULT_MODEL])
        input_cost = (self.input_tokens / 1_000_000) * pricing["input_per_1m"]
        output_cost = (self.output_tokens / 1_000_000) * pricing["output_per_1m"]
        thinking_cost = (self.thinking_tokens / 1_000_000) * pricing["thinking_per_1m"]
        return input_cost + output_cost + thinking_cost

    def __str__(self) -> str:
        return (
            f"Tokens: {self.input_tokens:,} in, {self.output_tokens:,} out, "
            f"{self.thinking_tokens:,} thinking | Requests: {self.requests:,}"
        )


class LLMClient:
    """
    Client for interacting with Gemini 2.5 Flash.

    Provides methods for task decomposition and expansion using
    the model's reasoning capabilities.

    Features:
    - Automatic response caching to reduce API costs
    - Token usage tracking with cost estimation
    - Thinking mode for complex reasoning tasks
    """

    def __init__(self, config: LLMConfig | None = None, api_key: str | None = None):
        self.config = config or LLMConfig()
        self.usage = UsageStats()

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

        # Initialize cache
        self._cache = LLMCache(
            cache_dir=self.config.cache_dir,
            enabled=self.config.cache_enabled,
        )

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
        # Check cache first
        cached = self._cache.get(
            prompt=prompt,
            system_prompt=system_prompt,
            model=self.config.model,
            temperature=self.config.temperature,
            use_thinking=use_thinking,
        )
        if cached is not None:
            return cached

        # Build request
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

        # Track token usage if available
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            self.usage.add(
                input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
                output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
                thinking_tokens=getattr(usage, "thoughts_token_count", 0) or 0,
            )

        # Cache the response
        response_text = response.text
        self._cache.set(
            prompt=prompt,
            system_prompt=system_prompt,
            model=self.config.model,
            temperature=self.config.temperature,
            use_thinking=use_thinking,
            response=response_text,
        )

        return response_text

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

    @property
    def cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return self._cache.stats()

    def close(self):
        """Close the client and release resources."""
        if hasattr(self._client, "close"):
            self._client.close()
        self._cache.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class MockLLMClient:
    """
    Mock LLM client for testing the pipeline without API calls.

    Generates realistic-looking but fake responses for decomposition,
    expansion, and completion criteria tasks.

    Usage:
        client = MockLLMClient()
        result = client.generate_json(prompt, system_prompt)
    """

    # Sample subtask templates for decomposition
    SUBTASK_TEMPLATES = [
        "prepare {item}",
        "gather {item}",
        "check {item}",
        "position {item}",
        "adjust {item}",
        "verify {item}",
        "clean {item}",
        "inspect {item}",
        "move {item}",
        "secure {item}",
    ]

    ITEMS = [
        "materials",
        "equipment",
        "workspace",
        "components",
        "tools",
        "surface",
        "container",
        "target",
        "source",
        "area",
    ]

    def __init__(self, config: LLMConfig | None = None, delay: float = 0.1):
        self.config = config or LLMConfig()
        self.usage = UsageStats()
        self.delay = delay  # Simulated API delay

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        use_thinking: bool = True,
    ) -> str:
        """Generate a mock response."""
        time.sleep(self.delay)

        # Simulate token usage
        input_tokens = len(prompt.split()) * 2
        output_tokens = random.randint(100, 300)
        thinking_tokens = random.randint(50, 200) if use_thinking else 0
        self.usage.add(input_tokens, output_tokens, thinking_tokens)

        # Generate appropriate mock response based on prompt content
        if "decompose" in prompt.lower() or "subtask" in prompt.lower():
            return self._mock_decomposition_response(prompt)
        elif "completion criteria" in prompt.lower() or "precondition" in prompt.lower():
            return self._mock_completion_response(prompt)
        elif "generate" in prompt.lower() and "task" in prompt.lower():
            return self._mock_expansion_response(prompt)
        else:
            return '{"result": "mock response"}'

    def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        use_thinking: bool = True,
    ) -> dict[str, Any]:
        """Generate and parse mock JSON response."""
        response = self.generate(prompt, system_prompt, use_thinking)
        return json.loads(response)

    def _mock_decomposition_response(self, prompt: str) -> str:
        """Generate mock decomposition response."""
        # Extract task name from prompt
        task_name = "task"
        if "Task:" in prompt:
            lines = prompt.split("\n")
            for line in lines:
                if line.startswith("Task:"):
                    task_name = line.replace("Task:", "").strip()
                    break

        # Determine if atomic (short tasks are more likely atomic)
        is_atomic = len(task_name.split()) <= 2 and random.random() < 0.3

        if is_atomic:
            return json.dumps(
                {
                    "is_atomic": True,
                    "reasoning": f"'{task_name}' is a fundamental action that cannot be meaningfully decomposed.",
                    "confidence": round(random.uniform(0.8, 0.95), 2),
                    "subtasks": [],
                }
            )

        # Generate 4-8 subtasks
        num_subtasks = random.randint(4, 8)
        subtasks = []
        used_templates = random.sample(
            self.SUBTASK_TEMPLATES, min(num_subtasks, len(self.SUBTASK_TEMPLATES))
        )

        for i, template in enumerate(used_templates[:num_subtasks]):
            item = random.choice(self.ITEMS)
            subtask_name = template.format(item=item)
            subtasks.append(
                {
                    "name": subtask_name,
                    "description": f"Step {i+1}: {subtask_name} for {task_name}",
                    "is_likely_atomic": random.random() < 0.4,
                }
            )

        return json.dumps(
            {
                "is_atomic": False,
                "reasoning": f"'{task_name}' can be broken down into {num_subtasks} sequential steps.",
                "confidence": round(random.uniform(0.75, 0.95), 2),
                "subtasks": subtasks,
            }
        )

    def _mock_completion_response(self, prompt: str) -> str:
        """Generate mock completion criteria response."""
        task_name = "task"
        if "Task:" in prompt:
            lines = prompt.split("\n")
            for line in lines:
                if line.startswith("Task:"):
                    task_name = line.replace("Task:", "").strip()
                    break

        return json.dumps(
            {
                "precondition": f"Required materials and workspace available for {task_name}. Area is clear and safe.",
                "postcondition": f"{task_name.capitalize()} completed successfully. Result meets quality standards.",
                "invariants": "Safety protocols maintained. No damage to equipment or materials.",
            }
        )

    def _mock_expansion_response(self, prompt: str) -> str:
        """Generate mock domain expansion response."""
        # Extract domain from prompt
        domain = "general"
        if "Domain:" in prompt:
            lines = prompt.split("\n")
            for line in lines:
                if line.startswith("Domain:"):
                    domain = line.replace("Domain:", "").strip()
                    break

        tasks = []
        task_verbs = ["perform", "complete", "execute", "handle", "manage", "process", "conduct"]
        task_objects = [
            "routine check",
            "maintenance",
            "inspection",
            "preparation",
            "cleanup",
            "setup",
            "review",
        ]

        for i in range(random.randint(5, 10)):
            verb = random.choice(task_verbs)
            obj = random.choice(task_objects)
            tasks.append(
                {
                    "name": f"{verb} {obj} ({i+1})",
                    "description": f"A task in the {domain} domain involving {obj}",
                    "typical_context": f"Performed during regular {domain.lower()} activities",
                    "tags": [domain.lower().replace(" ", "_"), "mock"],
                }
            )

        return json.dumps({"tasks": tasks})

    def close(self):
        """No-op for mock client."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


# Convenience function
def get_client(
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    mock: bool = False,
    cache_enabled: bool = True,
    **kwargs,
) -> LLMClient | MockLLMClient:
    """
    Get an LLM client with the specified configuration.

    Args:
        model: Model to use (default: gemini-2.5-flash)
        api_key: Optional API key
        mock: If True, return a MockLLMClient for testing
        cache_enabled: Whether to enable response caching (default: True)
        **kwargs: Additional config options

    Returns:
        Configured LLMClient or MockLLMClient
    """
    config = LLMConfig(model=model, cache_enabled=cache_enabled, **kwargs)
    if mock:
        return MockLLMClient(config=config)
    return LLMClient(config=config, api_key=api_key)
