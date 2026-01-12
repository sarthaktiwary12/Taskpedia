"""
Thread-safe primitives for concurrent operations.

This module provides reusable thread-safe building blocks used across
the codebase for generation, logging, and statistics tracking.

Usage:
    from taskpedia.concurrent import (
        AtomicCounter,
        AtomicBuffer,
        ThreadSafeStats,
    )
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")


# ============================================================================
# ATOMIC COUNTER
# ============================================================================


class AtomicCounter:
    """
    Thread-safe counter with atomic operations.

    Usage:
        counter = AtomicCounter()
        counter.increment()
        counter.increment(5)
        current = counter.value
    """

    def __init__(self, initial: int = 0):
        self._value = initial
        self._lock = threading.Lock()

    def increment(self, delta: int = 1) -> int:
        """Atomically increment and return new value."""
        with self._lock:
            self._value += delta
            return self._value

    def decrement(self, delta: int = 1) -> int:
        """Atomically decrement and return new value."""
        return self.increment(-delta)

    def set(self, value: int) -> None:
        """Set the counter value."""
        with self._lock:
            self._value = value

    def get(self) -> int:
        """Get the current value."""
        with self._lock:
            return self._value

    @property
    def value(self) -> int:
        """Property alias for get()."""
        return self.get()

    def __repr__(self) -> str:
        return f"AtomicCounter({self.value})"


# ============================================================================
# ATOMIC BUFFER
# ============================================================================


class AtomicBuffer(Generic[T]):
    """
    Thread-safe buffer with automatic flushing.

    Buffers items and flushes when threshold is reached or manually triggered.

    Usage:
        def flush_fn(items):
            for item in items:
                save_to_disk(item)

        buffer = AtomicBuffer(flush_fn, threshold=100)
        buffer.add(item)  # Auto-flushes at 100 items
        buffer.flush()    # Manual flush
    """

    def __init__(
        self,
        flush_fn: Callable[[list[T]], None],
        threshold: int = 100,
    ):
        self._items: list[T] = []
        self._lock = threading.Lock()
        self._flush_fn = flush_fn
        self._threshold = threshold
        self._total_flushed = 0

    def add(self, item: T) -> bool:
        """
        Add item to buffer. Returns True if buffer was flushed.
        """
        with self._lock:
            self._items.append(item)
            if len(self._items) >= self._threshold:
                self._do_flush()
                return True
            return False

    def add_batch(self, items: list[T]) -> bool:
        """Add multiple items. Returns True if buffer was flushed."""
        with self._lock:
            self._items.extend(items)
            if len(self._items) >= self._threshold:
                self._do_flush()
                return True
            return False

    def flush(self) -> int:
        """Manually flush buffer. Returns number of items flushed."""
        with self._lock:
            return self._do_flush()

    def _do_flush(self) -> int:
        """Internal flush (must hold lock)."""
        if not self._items:
            return 0

        count = len(self._items)
        items_to_flush = self._items.copy()
        self._items.clear()
        self._total_flushed += count

        # Release lock before calling flush function
        # (allows concurrent adds during slow I/O)
        try:
            self._flush_fn(items_to_flush)
        except Exception:
            # Re-add items if flush fails
            self._items.extend(items_to_flush)
            self._total_flushed -= count
            raise

        return count

    @property
    def pending_count(self) -> int:
        """Number of items waiting to be flushed."""
        with self._lock:
            return len(self._items)

    @property
    def total_flushed(self) -> int:
        """Total items flushed since creation."""
        with self._lock:
            return self._total_flushed

    def __repr__(self) -> str:
        return f"AtomicBuffer(pending={self.pending_count}, flushed={self.total_flushed})"


# ============================================================================
# THREAD-SAFE STATS
# ============================================================================


@dataclass
class ThreadSafeStats:
    """
    Thread-safe statistics tracker.

    Tracks multiple named counters and timing information.

    Usage:
        stats = ThreadSafeStats()
        stats.increment("processed")
        stats.increment("errors")
        stats.add_timing("api_call", 150.5)  # ms

        print(stats.snapshot())
    """

    _counters: dict[str, int] = field(default_factory=dict)
    _timings: dict[str, list[float]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _start_time: float = field(default_factory=time.time)

    def increment(self, name: str, delta: int = 1) -> int:
        """Increment a named counter."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = 0
            self._counters[name] += delta
            return self._counters[name]

    def get(self, name: str, default: int = 0) -> int:
        """Get counter value."""
        with self._lock:
            return self._counters.get(name, default)

    def set(self, name: str, value: int) -> None:
        """Set counter value."""
        with self._lock:
            self._counters[name] = value

    def add_timing(self, name: str, duration_ms: float) -> None:
        """Record a timing measurement."""
        with self._lock:
            if name not in self._timings:
                self._timings[name] = []
            self._timings[name].append(duration_ms)
            # Keep only last 1000 timings to avoid memory growth
            if len(self._timings[name]) > 1000:
                self._timings[name] = self._timings[name][-1000:]

    def get_avg_timing(self, name: str) -> float:
        """Get average timing for a metric."""
        with self._lock:
            timings = self._timings.get(name, [])
            if not timings:
                return 0.0
            return sum(timings) / len(timings)

    def elapsed_seconds(self) -> float:
        """Get elapsed time since creation."""
        return time.time() - self._start_time

    def rate_per_minute(self, name: str) -> float:
        """Calculate rate per minute for a counter."""
        elapsed = self.elapsed_seconds()
        if elapsed < 1:
            return 0.0
        count = self.get(name)
        return (count / elapsed) * 60

    def snapshot(self) -> dict[str, Any]:
        """Get a snapshot of all stats."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "timings": {
                    name: {
                        "count": len(values),
                        "avg_ms": sum(values) / len(values) if values else 0,
                        "min_ms": min(values) if values else 0,
                        "max_ms": max(values) if values else 0,
                    }
                    for name, values in self._timings.items()
                },
                "elapsed_s": self.elapsed_seconds(),
            }

    def reset(self) -> None:
        """Reset all stats."""
        with self._lock:
            self._counters.clear()
            self._timings.clear()
            self._start_time = time.time()


# ============================================================================
# THREAD-SAFE SET
# ============================================================================


class AtomicSet(Generic[T]):
    """
    Thread-safe set for tracking processed items.

    Usage:
        processed = AtomicSet()
        if not processed.contains(item_id):
            process(item)
            processed.add(item_id)
    """

    def __init__(self, initial: set[T] | None = None):
        self._items: set[T] = set(initial) if initial else set()
        self._lock = threading.Lock()

    def add(self, item: T) -> bool:
        """Add item. Returns True if item was new."""
        with self._lock:
            if item in self._items:
                return False
            self._items.add(item)
            return True

    def contains(self, item: T) -> bool:
        """Check if item is in set."""
        with self._lock:
            return item in self._items

    def remove(self, item: T) -> bool:
        """Remove item. Returns True if item was present."""
        with self._lock:
            if item in self._items:
                self._items.remove(item)
                return True
            return False

    def clear(self) -> int:
        """Clear all items. Returns count removed."""
        with self._lock:
            count = len(self._items)
            self._items.clear()
            return count

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)

    def __contains__(self, item: T) -> bool:
        return self.contains(item)

    def copy(self) -> set[T]:
        """Get a copy of the set."""
        with self._lock:
            return self._items.copy()


# ============================================================================
# THREAD-SAFE QUEUE WITH STATS
# ============================================================================


class WorkQueue(Generic[T]):
    """
    Thread-safe work queue with statistics.

    Usage:
        queue = WorkQueue()
        queue.put(item)
        queue.put_batch([item1, item2, item3])

        while not queue.empty():
            batch = queue.get_batch(limit=10)
            process(batch)
    """

    def __init__(self):
        self._items: list[T] = []
        self._lock = threading.Lock()
        self._total_added = 0
        self._total_removed = 0

    def put(self, item: T) -> None:
        """Add single item to queue."""
        with self._lock:
            self._items.append(item)
            self._total_added += 1

    def put_batch(self, items: list[T]) -> None:
        """Add multiple items to queue."""
        with self._lock:
            self._items.extend(items)
            self._total_added += len(items)

    def get(self) -> T | None:
        """Get single item from queue."""
        with self._lock:
            if not self._items:
                return None
            item = self._items.pop(0)
            self._total_removed += 1
            return item

    def get_batch(self, limit: int = 100) -> list[T]:
        """Get up to `limit` items from queue."""
        with self._lock:
            batch = self._items[:limit]
            self._items = self._items[limit:]
            self._total_removed += len(batch)
            return batch

    def empty(self) -> bool:
        """Check if queue is empty."""
        with self._lock:
            return len(self._items) == 0

    def size(self) -> int:
        """Get current queue size."""
        with self._lock:
            return len(self._items)

    @property
    def pending(self) -> int:
        """Alias for size()."""
        return self.size()

    @property
    def total_added(self) -> int:
        with self._lock:
            return self._total_added

    @property
    def total_removed(self) -> int:
        with self._lock:
            return self._total_removed

    def stats(self) -> dict[str, int]:
        """Get queue statistics."""
        with self._lock:
            return {
                "pending": len(self._items),
                "total_added": self._total_added,
                "total_removed": self._total_removed,
            }


# ============================================================================
# PROGRESS TRACKER
# ============================================================================


class ProgressTracker:
    """
    Thread-safe progress tracker for concurrent operations.

    Tracks completed items and provides RPM calculations.

    Usage:
        tracker = ProgressTracker(total=1000)
        for item in items:
            process(item)
            completed, rpm = tracker.increment()
            print(tracker.format_progress())
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
