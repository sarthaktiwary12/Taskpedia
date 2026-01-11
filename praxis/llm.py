"""LLM client with tenacity retry logic and batch API support."""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import orjson
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from praxis.cache import BatchRequestStore, LLMCache, get_cache
from praxis.config import ExecutionMode, LLMProvider, PraxisConfig, get_config

logger = structlog.get_logger()


@dataclass
class LLMRequest:
    """A request to the LLM."""

    prompt: str
    system: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.7
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """A response from the LLM."""

    content: str
    request_id: str
    model: str
    tokens_input: int
    tokens_output: int
    cached: bool = False
    prompt_hash: str = ""
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class RateLimitError(Exception):
    """Rate limit exceeded."""

    pass


class APIError(Exception):
    """General API error."""

    pass


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse:
        """Complete a single request."""
        pass

    @abstractmethod
    def complete_batch(self, requests: list[LLMRequest]) -> list[LLMResponse]:
        """Complete a batch of requests (for discounted pricing)."""
        pass

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get client statistics."""
        pass


class AnthropicClient(LLMClient):
    """
    Anthropic Claude client with:
    - Automatic caching of responses
    - Tenacity retry with exponential backoff
    - Batch API support for 50% discount
    """

    def __init__(
        self,
        config: PraxisConfig | None = None,
        cache: LLMCache | None = None,
    ) -> None:
        self.config = config or get_config()
        self.cache = cache or get_cache()

        if not self.config.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for AnthropicClient")

        self._client = httpx.Client(
            base_url="https://api.anthropic.com/v1",
            headers={
                "x-api-key": self.config.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            timeout=httpx.Timeout(300.0, connect=10.0),
        )

        self._batch_store = BatchRequestStore()

        # Statistics
        self._stats = {
            "requests": 0,
            "cache_hits": 0,
            "tokens_input": 0,
            "tokens_output": 0,
            "errors": 0,
            "retries": 0,
        }

        logger.info(
            "anthropic_client_initialized",
            model=self.config.llm_model,
            mode=self.config.execution_mode.value,
        )

    def _make_retry_decorator(self) -> Any:
        """Create a tenacity retry decorator with current config."""
        return retry(
            retry=retry_if_exception_type((RateLimitError, httpx.TimeoutException)),
            stop=stop_after_attempt(self.config.retry_max_attempts),
            wait=wait_exponential(
                multiplier=self.config.retry_min_wait,
                max=self.config.retry_max_wait,
                exp_base=self.config.retry_exponential_base,
            ),
            before_sleep=lambda retry_state: logger.warning(
                "retry_attempt",
                attempt=retry_state.attempt_number,
                wait=retry_state.next_action.sleep,
            ),
        )

    def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Complete a single request with caching and retry logic.
        """
        self._stats["requests"] += 1

        # Check cache first
        prompt_hash = LLMCache.compute_hash(
            prompt=request.prompt,
            model=self.config.llm_model,
            temperature=request.temperature,
            system=request.system,
        )

        cached = self.cache.get(prompt_hash)
        if cached:
            self._stats["cache_hits"] += 1
            logger.debug("cache_hit", request_id=request.request_id)
            return LLMResponse(
                content=cached.response,
                request_id=request.request_id,
                model=cached.model,
                tokens_input=0,
                tokens_output=0,
                cached=True,
                prompt_hash=prompt_hash,
                metadata=cached.metadata,
            )

        # Make the API call with retry
        response = self._call_api_with_retry(request, prompt_hash)

        # Cache the response
        self.cache.put(
            prompt_hash=prompt_hash,
            response=response.content,
            model=response.model,
            tokens_used=response.tokens_input + response.tokens_output,
            metadata=request.metadata,
        )

        return response

    def _call_api_with_retry(
        self,
        request: LLMRequest,
        prompt_hash: str,
    ) -> LLMResponse:
        """Call the API with retry logic."""
        retry_decorator = self._make_retry_decorator()

        @retry_decorator
        def _call() -> LLMResponse:
            return self._call_api(request, prompt_hash)

        try:
            return _call()
        except Exception as e:
            self._stats["errors"] += 1
            raise

    def _call_api(self, request: LLMRequest, prompt_hash: str) -> LLMResponse:
        """Make the actual API call."""
        start_time = time.time()

        messages = [{"role": "user", "content": request.prompt}]
        payload: dict[str, Any] = {
            "model": self.config.llm_model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": messages,
        }

        if request.system:
            payload["system"] = request.system

        try:
            response = self._client.post("/messages", json=payload)

            if response.status_code == 429:
                self._stats["retries"] += 1
                raise RateLimitError("Rate limit exceeded")

            if response.status_code >= 400:
                raise APIError(f"API error: {response.status_code} - {response.text}")

            data = response.json()
            content = data["content"][0]["text"]
            usage = data.get("usage", {})

            latency_ms = (time.time() - start_time) * 1000
            tokens_input = usage.get("input_tokens", 0)
            tokens_output = usage.get("output_tokens", 0)

            self._stats["tokens_input"] += tokens_input
            self._stats["tokens_output"] += tokens_output

            return LLMResponse(
                content=content,
                request_id=request.request_id,
                model=self.config.llm_model,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cached=False,
                prompt_hash=prompt_hash,
                latency_ms=latency_ms,
                metadata=request.metadata,
            )

        except httpx.TimeoutException:
            self._stats["retries"] += 1
            raise
        except Exception as e:
            logger.error("api_call_error", error=str(e), request_id=request.request_id)
            raise

    def complete_batch(self, requests: list[LLMRequest]) -> list[LLMResponse]:
        """
        Submit requests as a batch for 50% discounted pricing.

        This uses the Anthropic Message Batches API.
        """
        if self.config.execution_mode != ExecutionMode.BATCH:
            # Fall back to individual requests
            return [self.complete(req) for req in requests]

        batch_id = str(uuid.uuid4())
        logger.info("batch_submit_start", batch_id=batch_id, count=len(requests))

        # Prepare batch requests, checking cache first
        batch_requests = []
        cached_responses: dict[str, LLMResponse] = {}

        for req in requests:
            prompt_hash = LLMCache.compute_hash(
                prompt=req.prompt,
                model=self.config.llm_model,
                temperature=req.temperature,
                system=req.system,
            )

            cached = self.cache.get(prompt_hash)
            if cached:
                self._stats["cache_hits"] += 1
                cached_responses[req.request_id] = LLMResponse(
                    content=cached.response,
                    request_id=req.request_id,
                    model=cached.model,
                    tokens_input=0,
                    tokens_output=0,
                    cached=True,
                    prompt_hash=prompt_hash,
                    metadata=cached.metadata,
                )
            else:
                batch_requests.append(
                    {
                        "custom_id": req.request_id,
                        "params": {
                            "model": self.config.llm_model,
                            "max_tokens": req.max_tokens,
                            "temperature": req.temperature,
                            "messages": [{"role": "user", "content": req.prompt}],
                            **({"system": req.system} if req.system else {}),
                        },
                    }
                )

        if not batch_requests:
            # All cached
            return [cached_responses[req.request_id] for req in requests]

        # Submit batch
        try:
            response = self._client.post(
                "/messages/batches",
                json={"requests": batch_requests},
            )

            if response.status_code >= 400:
                raise APIError(f"Batch API error: {response.status_code}")

            batch_data = response.json()
            api_batch_id = batch_data["id"]
            self._batch_store.update_batch_status(batch_id, "processing", api_batch_id)

            # Poll for completion
            results = self._poll_batch(api_batch_id, batch_id)

            # Combine with cached responses
            all_responses = []
            result_map = {r["custom_id"]: r for r in results}

            for req in requests:
                if req.request_id in cached_responses:
                    all_responses.append(cached_responses[req.request_id])
                elif req.request_id in result_map:
                    result = result_map[req.request_id]
                    content = result["result"]["message"]["content"][0]["text"]
                    usage = result["result"]["message"].get("usage", {})

                    prompt_hash = LLMCache.compute_hash(
                        prompt=req.prompt,
                        model=self.config.llm_model,
                        temperature=req.temperature,
                        system=req.system,
                    )

                    # Cache the result
                    self.cache.put(
                        prompt_hash=prompt_hash,
                        response=content,
                        model=self.config.llm_model,
                        tokens_used=usage.get("input_tokens", 0)
                        + usage.get("output_tokens", 0),
                        metadata=req.metadata,
                    )

                    all_responses.append(
                        LLMResponse(
                            content=content,
                            request_id=req.request_id,
                            model=self.config.llm_model,
                            tokens_input=usage.get("input_tokens", 0),
                            tokens_output=usage.get("output_tokens", 0),
                            cached=False,
                            prompt_hash=prompt_hash,
                            metadata=req.metadata,
                        )
                    )

            return all_responses

        except Exception as e:
            logger.error("batch_submit_error", error=str(e), batch_id=batch_id)
            raise

    def _poll_batch(
        self,
        api_batch_id: str,
        local_batch_id: str,
    ) -> list[dict[str, Any]]:
        """Poll for batch completion."""
        while True:
            time.sleep(self.config.batch_poll_interval)

            response = self._client.get(f"/messages/batches/{api_batch_id}")
            if response.status_code >= 400:
                raise APIError(f"Batch poll error: {response.status_code}")

            data = response.json()
            status = data["processing_status"]

            logger.info(
                "batch_poll",
                api_batch_id=api_batch_id,
                status=status,
                succeeded=data.get("request_counts", {}).get("succeeded", 0),
            )

            if status == "ended":
                # Fetch results
                results_response = self._client.get(
                    f"/messages/batches/{api_batch_id}/results"
                )
                if results_response.status_code >= 400:
                    raise APIError("Failed to fetch batch results")

                results = []
                for line in results_response.text.strip().split("\n"):
                    results.append(orjson.loads(line))

                self._batch_store.store_batch_results(local_batch_id, results)
                return results

    def get_stats(self) -> dict[str, Any]:
        """Get client statistics."""
        cache_stats = self.cache.get_stats()
        return {
            **self._stats,
            "cache_hit_rate": cache_stats["hit_rate"],
            "tokens_saved": cache_stats["tokens_saved"],
            "cache_entries": cache_stats["entries"],
        }

    def close(self) -> None:
        """Close the client."""
        self._client.close()
        self._batch_store.close()


class MockLLMClient(LLMClient):
    """
    Mock LLM client for testing and diversity validation.

    Generates deterministic responses based on input hashing.
    """

    def __init__(self, config: PraxisConfig | None = None) -> None:
        self.config = config or get_config()
        self._stats = {
            "requests": 0,
            "tokens_simulated": 0,
        }

        logger.info("mock_llm_client_initialized")

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate a mock response."""
        self._stats["requests"] += 1

        # Generate deterministic mock response
        content = self._generate_mock_response(request)
        tokens = len(content.split())

        self._stats["tokens_simulated"] += tokens

        return LLMResponse(
            content=content,
            request_id=request.request_id,
            model="mock-model",
            tokens_input=len(request.prompt.split()),
            tokens_output=tokens,
            cached=False,
            prompt_hash=LLMCache.compute_hash(
                request.prompt, "mock", request.temperature
            ),
        )

    def complete_batch(self, requests: list[LLMRequest]) -> list[LLMResponse]:
        """Process batch of mock requests."""
        return [self.complete(req) for req in requests]

    def _generate_mock_response(self, request: LLMRequest) -> str:
        """Generate a structured mock response for testing."""
        # Extract verb and noun from prompt if possible
        prompt_lower = request.prompt.lower()

        # Try to extract task info
        verb = "perform"
        noun = "task"

        if "verb:" in prompt_lower:
            start = prompt_lower.find("verb:") + 5
            end = prompt_lower.find("\n", start)
            if end > start:
                verb = prompt_lower[start:end].strip()

        if "noun:" in prompt_lower:
            start = prompt_lower.find("noun:") + 5
            end = prompt_lower.find("\n", start)
            if end > start:
                noun = prompt_lower[start:end].strip()

        # Generate mock task definition
        mock_response = orjson.dumps(
            {
                "name": f"{verb} {noun}",
                "completion": {
                    "precondition": f"The {noun} is available and accessible.",
                    "postcondition": f"The {verb} action on {noun} is complete.",
                    "invariants": f"The {noun} remains undamaged during the process.",
                },
                "physical": f"This is a mock physical description for {verb} {noun}.",
                "sensing": f"Visual and tactile feedback required for {verb} {noun}.",
                "cognitive": f"Low cognitive load task involving {verb} {noun}.",
                "context": f"Typical environment for {verb} {noun} operations.",
                "tags": ["mock_generated", "test_data"],
                "confidence": 0.85,
            },
            option=orjson.OPT_INDENT_2,
        ).decode()

        return mock_response

    def get_stats(self) -> dict[str, Any]:
        """Get mock client statistics."""
        return self._stats


def create_client(config: PraxisConfig | None = None) -> LLMClient:
    """Factory function to create the appropriate LLM client."""
    config = config or get_config()

    if config.llm_provider == LLMProvider.MOCK:
        return MockLLMClient(config)
    elif config.llm_provider == LLMProvider.ANTHROPIC:
        return AnthropicClient(config)
    else:
        raise ValueError(f"Unknown LLM provider: {config.llm_provider}")
