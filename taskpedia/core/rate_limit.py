"""
Rate limiting utilities.

Thread-safe rate limiter for API calls with configurable RPM limits.
"""

from __future__ import annotations

import threading
import time

# Default rate limits
DEFAULT_RPM = 800  # Requests per minute


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
