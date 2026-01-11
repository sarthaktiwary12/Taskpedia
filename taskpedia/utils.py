"""
Shared utilities for TASKPEDIA.

Provides common functionality like rate limiting, retries, and parallel execution
that can be used across all modules.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# ============================================================================
# Rate Limiting
# ============================================================================

# Default rate limits
DEFAULT_RPM = 800  # Requests per minute
DEFAULT_MAX_RETRIES = 5


class RateLimiter:
    """
    Thread-safe rate limiter for API calls.

    Enforces a maximum requests-per-minute (RPM) limit across all threads.
    Uses a sliding window approach with token bucket algorithm.

    Usage:
        limiter = RateLimiter(rpm=800)

        # In any thread:
        limiter.acquire()  # Blocks if rate limit exceeded
        response = api_call()
    """

    def __init__(self, rpm: int = DEFAULT_RPM):
        """
        Initialize rate limiter.

        Args:
            rpm: Maximum requests per minute (default: 800)
        """
        self.rpm = rpm
        self.min_interval = 60.0 / rpm  # Minimum seconds between requests
        self.last_request_time = 0.0
        self._lock = threading.Lock()
        self._request_count = 0
        self._start_time = time.time()

    def acquire(self) -> float:
        """
        Acquire permission to make a request.

        Blocks if necessary to maintain rate limit.

        Returns:
            Time waited (in seconds)
        """
        with self._lock:
            now = time.time()
            elapsed = now - self.last_request_time
            wait_time = 0.0

            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                time.sleep(wait_time)

            self.last_request_time = time.time()
            self._request_count += 1
            return wait_time

    @property
    def current_rpm(self) -> float:
        """Get the current effective RPM."""
        elapsed = time.time() - self._start_time
        if elapsed <= 0:
            return 0.0
        return (self._request_count / elapsed) * 60

    @property
    def request_count(self) -> int:
        """Get total number of requests made."""
        return self._request_count

    def reset_stats(self):
        """Reset the request counter and start time."""
        with self._lock:
            self._request_count = 0
            self._start_time = time.time()


# Global rate limiter instance
_global_rate_limiter: RateLimiter | None = None
_rate_limiter_lock = threading.Lock()


def get_rate_limiter(rpm: int = DEFAULT_RPM) -> RateLimiter:
    """
    Get or create the global rate limiter.

    Args:
        rpm: Requests per minute limit (only used on first call)

    Returns:
        The global RateLimiter instance
    """
    global _global_rate_limiter
    with _rate_limiter_lock:
        if _global_rate_limiter is None:
            _global_rate_limiter = RateLimiter(rpm=rpm)
        return _global_rate_limiter


def reset_rate_limiter(rpm: int = DEFAULT_RPM) -> RateLimiter:
    """
    Reset the global rate limiter with new settings.

    Args:
        rpm: New requests per minute limit

    Returns:
        The new RateLimiter instance
    """
    global _global_rate_limiter
    with _rate_limiter_lock:
        _global_rate_limiter = RateLimiter(rpm=rpm)
        return _global_rate_limiter


# ============================================================================
# Retry Decorators with Tenacity
# ============================================================================

# Common retryable exceptions
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
)


T = TypeVar("T")


def with_retry(
    max_attempts: int = DEFAULT_MAX_RETRIES,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    multiplier: float = 2.0,
    retryable_exceptions: tuple = RETRYABLE_EXCEPTIONS,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying functions with exponential backoff.

    Uses tenacity for robust retry logic.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        multiplier: Multiplier for exponential backoff
        retryable_exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic

    Usage:
        @with_retry(max_attempts=3)
        def api_call():
            return requests.get(url)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(retryable_exceptions),
            reraise=True,
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def with_rate_limit_and_retry(
    rate_limiter: RateLimiter | None = None,
    max_attempts: int = DEFAULT_MAX_RETRIES,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    multiplier: float = 2.0,
    retryable_exceptions: tuple = RETRYABLE_EXCEPTIONS,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator combining rate limiting and retry logic.

    Acquires rate limit token before each attempt, then retries
    with exponential backoff on failure.

    Args:
        rate_limiter: RateLimiter instance (uses global if None)
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        multiplier: Multiplier for exponential backoff
        retryable_exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with rate limiting and retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            limiter = rate_limiter or get_rate_limiter()

            last_exception = None
            for attempt in range(max_attempts):
                # Acquire rate limit token
                limiter.acquire()

                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        # Exponential backoff
                        wait_time = min(min_wait * (multiplier**attempt), max_wait)
                        time.sleep(wait_time)
                    continue
                except Exception:
                    # Non-retryable exception, re-raise immediately
                    raise

            # All retries exhausted
            if last_exception:
                raise last_exception
            raise RuntimeError("All retry attempts exhausted")

        return wrapper

    return decorator


def rate_limited_call(
    func: Callable[..., T],
    *args: Any,
    rate_limiter: RateLimiter | None = None,
    max_attempts: int = DEFAULT_MAX_RETRIES,
    **kwargs: Any,
) -> T:
    """
    Execute a function with rate limiting and retry logic.

    Convenience function for one-off rate-limited calls.

    Args:
        func: Function to call
        *args: Positional arguments for func
        rate_limiter: RateLimiter instance (uses global if None)
        max_attempts: Maximum retry attempts
        **kwargs: Keyword arguments for func

    Returns:
        Result of func(*args, **kwargs)
    """
    limiter = rate_limiter or get_rate_limiter()

    last_exception = None
    for attempt in range(max_attempts):
        limiter.acquire()

        try:
            return func(*args, **kwargs)
        except RETRYABLE_EXCEPTIONS as e:
            last_exception = e
            if attempt < max_attempts - 1:
                wait_time = min(1.0 * (2.0**attempt), 60.0)
                time.sleep(wait_time)
            continue
        except Exception:
            raise

    if last_exception:
        raise last_exception
    raise RuntimeError("All retry attempts exhausted")


# ============================================================================
# Progress Tracking
# ============================================================================


class ProgressTracker:
    """
    Thread-safe progress tracker for concurrent operations.

    Tracks completed items and provides RPM calculations.
    """

    def __init__(self, total: int):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items to process
        """
        self.total = total
        self.completed = 0
        self.errors = 0
        self.start_time = time.time()
        self._lock = threading.Lock()

    def increment(self, error: bool = False) -> tuple[int, float]:
        """
        Increment the completed count.

        Args:
            error: Whether this completion was an error

        Returns:
            Tuple of (completed_count, current_rpm)
        """
        with self._lock:
            self.completed += 1
            if error:
                self.errors += 1
            elapsed = time.time() - self.start_time
            rpm = (self.completed / elapsed * 60) if elapsed > 0 else 0.0
            return self.completed, rpm

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    @property
    def rpm(self) -> float:
        """Get current requests per minute."""
        elapsed = self.elapsed
        return (self.completed / elapsed * 60) if elapsed > 0 else 0.0

    @property
    def eta_seconds(self) -> float:
        """Get estimated time remaining in seconds."""
        if self.completed == 0:
            return float("inf")
        rate = self.completed / self.elapsed
        remaining = self.total - self.completed
        return remaining / rate if rate > 0 else float("inf")

    def format_progress(self, item_name: str = "") -> str:
        """
        Format a progress string.

        Args:
            item_name: Optional name of current item

        Returns:
            Formatted progress string
        """
        pct = (self.completed / self.total * 100) if self.total > 0 else 0
        eta = self.eta_seconds
        eta_str = f"{eta:.0f}s" if eta < float("inf") else "?"

        base = f"[{self.completed}/{self.total}] {pct:.1f}% | {self.rpm:.0f} RPM | ETA: {eta_str}"
        if item_name:
            base = f"{base} | {item_name}"
        if self.errors > 0:
            base = f"{base} | {self.errors} errors"
        return base
