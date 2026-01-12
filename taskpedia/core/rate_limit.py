"""
Rate limiting utilities.

Provides both:
1. Direct re-exports from `ratelimit` library for decorator-based limiting
2. A thin RateLimiter class for imperative .acquire() pattern
"""

from __future__ import annotations

import threading
import time

from ratelimit import RateLimitException, limits, sleep_and_retry

__all__ = [
    # Library re-exports (preferred for new code)
    "limits",
    "sleep_and_retry",
    "RateLimitException",
    # Imperative wrapper (for existing code)
    "RateLimiter",
]

# Default rate limits
DEFAULT_RPM = 800


class RateLimiter:
    """
    Thin wrapper around `ratelimit` library for imperative .acquire() pattern.

    For new code, prefer using @sleep_and_retry @limits decorators directly:

        from taskpedia.core import sleep_and_retry, limits

        @sleep_and_retry
        @limits(calls=1000, period=60)
        def call_api():
            return requests.get(url)

    This class exists for backward compatibility with code that uses:

        limiter = RateLimiter(rpm=1000)
        limiter.acquire()
        response = call_api()
    """

    def __init__(self, rpm: int = DEFAULT_RPM):
        self.rpm = rpm
        self._lock = threading.Lock()
        self._request_count = 0
        self._start_time = time.time()

        # Create rate-limited no-op using the library
        @sleep_and_retry
        @limits(calls=rpm, period=60)
        def _acquire():
            pass

        self._acquire = _acquire

    def acquire(self) -> float:
        """Block until rate limit allows, return wait time."""
        start = time.time()
        self._acquire()
        with self._lock:
            self._request_count += 1
        return time.time() - start

    @property
    def request_count(self) -> int:
        with self._lock:
            return self._request_count

    @property
    def current_rpm(self) -> float:
        elapsed = time.time() - self._start_time
        if elapsed <= 0:
            return 0.0
        with self._lock:
            return (self._request_count / elapsed) * 60
