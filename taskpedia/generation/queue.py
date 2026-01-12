"""
Reusable concurrent LLM request queue with rate limiting.

This module provides primitives for concurrent LLM API calls that can be used
across different use cases (generation, judging, analysis, etc.).

Key features:
- ThreadPoolExecutor-based concurrent execution
- Configurable rate limiting (RPM)
- Automatic retries with exponential backoff
- Result batching and callbacks
- Thread-safe statistics tracking
"""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

from taskpedia.core import RateLimiter
from taskpedia.generation.llm import LLMClient, MockLLMClient

log = logging.getLogger(__name__)

# Type variables for generic queue
T = TypeVar("T")  # Input type
R = TypeVar("R")  # Result type


@dataclass
class LLMRequest(Generic[T]):
    """A single LLM request with context."""

    id: str
    data: T
    prompt: str
    system_prompt: str | None = None
    use_thinking: bool = False
    metadata: dict[str, Any] | None = None


@dataclass
class LLMResponse(Generic[T, R]):
    """Response from an LLM request."""

    request: LLMRequest[T]
    success: bool
    result: R | None = None
    error: str | None = None
    latency_ms: float = 0.0


class LLMQueueStats:
    """Thread-safe statistics for LLM queue operations."""

    def __init__(self):
        self.submitted = 0
        self.in_flight = 0
        self.completed = 0
        self.errors = 0
        self.api_calls = 0
        self.total_latency_ms = 0.0
        self._lock = threading.Lock()
        self._start_time = time.time()

    def submit(self, count: int = 1):
        with self._lock:
            self.submitted += count

    def start(self, count: int = 1):
        with self._lock:
            self.in_flight += count

    def finish(self, count: int = 1, error: bool = False, latency_ms: float = 0.0):
        with self._lock:
            self.in_flight -= count
            self.completed += count
            if error:
                self.errors += count
            self.api_calls += count
            self.total_latency_ms += latency_ms

    def get_rpm(self) -> float:
        """Get current requests per minute."""
        elapsed = time.time() - self._start_time
        if elapsed < 1:
            return 0.0
        return (self.api_calls / elapsed) * 60

    def get_avg_latency_ms(self) -> float:
        """Get average latency in milliseconds."""
        with self._lock:
            if self.api_calls == 0:
                return 0.0
            return self.total_latency_ms / self.api_calls

    def snapshot(self) -> dict[str, Any]:
        """Get a snapshot of current stats."""
        with self._lock:
            return {
                "submitted": self.submitted,
                "in_flight": self.in_flight,
                "completed": self.completed,
                "errors": self.errors,
                "api_calls": self.api_calls,
                "rpm": self.get_rpm(),
                "avg_latency_ms": self.get_avg_latency_ms(),
            }


class LLMQueue(Generic[T, R]):
    """
    Concurrent queue for LLM API calls.

    Generic queue that handles:
    - Concurrent execution with ThreadPoolExecutor
    - Rate limiting (RPM)
    - Automatic retries
    - Result batching
    - Progress callbacks

    Type parameters:
        T: Input data type
        R: Result type

    Usage:
        def process_fn(request: LLMRequest[MyData]) -> MyResult:
            response = client.generate(request.prompt, request.system_prompt)
            return parse_response(response)

        queue = LLMQueue(
            client=client,
            process_fn=process_fn,
            max_workers=64,
            rpm_limit=1000
        )

        # Submit requests
        for item in items:
            queue.submit(LLMRequest(
                id=item.id,
                data=item,
                prompt=make_prompt(item),
                system_prompt=SYSTEM_PROMPT
            ))

        # Process with callback
        def on_result(response: LLMResponse):
            if response.success:
                handle_result(response.result)

        queue.process_all(callback=on_result)
    """

    def __init__(
        self,
        client: LLMClient | MockLLMClient,
        process_fn: Callable[[LLMRequest[T]], R],
        max_workers: int = 64,
        rpm_limit: int = 1000,
    ):
        """
        Initialize LLM queue.

        Args:
            client: LLM client instance
            process_fn: Function to process requests into results
            max_workers: Max concurrent workers
            rpm_limit: Rate limit in requests per minute
        """
        self.client = client
        self.process_fn = process_fn
        self.max_workers = max_workers
        self.rate_limiter = RateLimiter(rpm=rpm_limit)
        self.stats = LLMQueueStats()

        # Request queue
        self._requests: list[LLMRequest[T]] = []
        self._requests_lock = threading.Lock()

    def submit(self, request: LLMRequest[T]):
        """Submit a request to the queue."""
        with self._requests_lock:
            self._requests.append(request)
            self.stats.submit()

    def submit_batch(self, requests: list[LLMRequest[T]]):
        """Submit multiple requests at once."""
        with self._requests_lock:
            self._requests.extend(requests)
            self.stats.submit(len(requests))

    def _execute_request(self, request: LLMRequest[T]) -> LLMResponse[T, R]:
        """Execute a single request with rate limiting."""
        self.stats.start()
        start_time = time.time()

        try:
            # Acquire rate limit token
            self.rate_limiter.acquire()

            # Process request
            result = self.process_fn(request)

            latency_ms = (time.time() - start_time) * 1000
            self.stats.finish(latency_ms=latency_ms)

            return LLMResponse(
                request=request,
                success=True,
                result=result,
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.stats.finish(error=True, latency_ms=latency_ms)

            log.error(f"Error processing request {request.id}: {e}")
            return LLMResponse(
                request=request,
                success=False,
                error=str(e),
                latency_ms=latency_ms,
            )

    def process_all(
        self,
        callback: Callable[[LLMResponse[T, R]], None] | None = None,
        batch_size: int = 100,
    ) -> list[LLMResponse[T, R]]:
        """
        Process all queued requests.

        Args:
            callback: Optional callback for each result
            batch_size: Number of requests to process concurrently

        Returns:
            List of all responses
        """
        all_responses: list[LLMResponse[T, R]] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while True:
                # Get next batch
                with self._requests_lock:
                    if not self._requests:
                        break
                    batch = self._requests[:batch_size]
                    self._requests = self._requests[batch_size:]

                # Submit futures
                futures: dict[Future[LLMResponse[T, R]], LLMRequest[T]] = {
                    executor.submit(self._execute_request, req): req for req in batch
                }

                # Collect results
                for future in as_completed(futures):
                    try:
                        response = future.result(timeout=60)
                        all_responses.append(response)

                        if callback:
                            callback(response)
                    except Exception as e:
                        request = futures[future]
                        log.error(f"Future exception for {request.id}: {e}")
                        error_response = LLMResponse(
                            request=request,
                            success=False,
                            error=str(e),
                        )
                        all_responses.append(error_response)
                        if callback:
                            callback(error_response)

        return all_responses

    def process_streaming(
        self,
        callback: Callable[[LLMResponse[T, R]], None],
        batch_size: int = 100,
        stop_event: threading.Event | None = None,
    ):
        """
        Process requests as they arrive (streaming mode).

        Args:
            callback: Callback for each result
            batch_size: Number of requests to process concurrently
            stop_event: Event to signal stop
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures: dict[Future[LLMResponse[T, R]], LLMRequest[T]] = {}

            while True:
                if stop_event and stop_event.is_set():
                    break

                # Get next batch
                with self._requests_lock:
                    if self._requests:
                        batch = self._requests[:batch_size]
                        self._requests = self._requests[batch_size:]
                    else:
                        batch = []

                # Submit new futures
                for req in batch:
                    future = executor.submit(self._execute_request, req)
                    futures[future] = req

                if not futures:
                    # No work, check if we should continue
                    if stop_event:
                        time.sleep(0.1)
                        continue
                    else:
                        break

                # Collect completed results
                done_futures = [f for f in futures if f.done()]
                for future in done_futures:
                    try:
                        response = future.result()
                        callback(response)
                    except Exception as e:
                        request = futures[future]
                        log.error(f"Future exception for {request.id}: {e}")
                        callback(
                            LLMResponse(
                                request=request,
                                success=False,
                                error=str(e),
                            )
                        )
                    finally:
                        del futures[future]

                time.sleep(0.01)  # Small delay to avoid busy loop

    def clear(self):
        """Clear all pending requests."""
        with self._requests_lock:
            count = len(self._requests)
            self._requests.clear()
            return count

    def pending_count(self) -> int:
        """Get number of pending requests."""
        with self._requests_lock:
            return len(self._requests)
