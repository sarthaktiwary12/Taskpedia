"""Caching layer for LLM outputs to prevent waste and enable crash recovery."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import orjson
import structlog
import xxhash
from diskcache import Cache, Disk
from sqlitedict import SqliteDict

from praxis.config import get_config

logger = structlog.get_logger()


@dataclass
class CacheEntry:
    """A cached LLM response entry."""

    prompt_hash: str
    response: str
    model: str
    timestamp: float
    tokens_used: int
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "prompt_hash": self.prompt_hash,
            "response": self.response,
            "model": self.model,
            "timestamp": self.timestamp,
            "tokens_used": self.tokens_used,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheEntry:
        """Create from dictionary."""
        return cls(
            prompt_hash=data["prompt_hash"],
            response=data["response"],
            model=data["model"],
            timestamp=data["timestamp"],
            tokens_used=data["tokens_used"],
            metadata=data.get("metadata", {}),
        )


class OrjsonDisk(Disk):
    """Custom disk serializer using orjson for better performance."""

    def __init__(self, directory: str | Path, **kwargs: Any) -> None:
        super().__init__(directory, **kwargs)

    def store(self, value: Any, read: bool, key: str = "") -> tuple[int, int, str | bytes]:
        """Store value with orjson serialization."""
        if not read:
            data = orjson.dumps(value)
            return 0, len(data), data
        return super().store(value, read, key)

    def fetch(self, mode: int, filename: str, value: bytes, read: bool) -> Any:
        """Fetch value with orjson deserialization."""
        if mode == 0:
            return orjson.loads(value)
        return super().fetch(mode, filename, value, read)


class LLMCache:
    """
    Disk-based cache for LLM responses.

    Uses xxhash for fast hashing and diskcache for persistent storage.
    Designed for high throughput with minimal memory usage.
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        ttl_days: int | None = None,
    ) -> None:
        config = get_config()
        self.cache_dir = cache_dir or config.cache_dir
        self.ttl_seconds = (ttl_days or config.cache_ttl_days) * 86400

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Main response cache with custom serializer
        self._cache = Cache(
            str(self.cache_dir / "responses"),
            disk=OrjsonDisk,
            size_limit=10 * 1024 * 1024 * 1024,  # 10 GB
            eviction_policy="least-recently-used",
        )

        # Statistics tracking
        self._stats = SqliteDict(
            str(self.cache_dir / "stats.sqlite"),
            autocommit=True,
        )
        self._init_stats()

        logger.info(
            "llm_cache_initialized",
            cache_dir=str(self.cache_dir),
            entries=len(self._cache),
        )

    def _init_stats(self) -> None:
        """Initialize cache statistics."""
        if "hits" not in self._stats:
            self._stats["hits"] = 0
        if "misses" not in self._stats:
            self._stats["misses"] = 0
        if "tokens_saved" not in self._stats:
            self._stats["tokens_saved"] = 0
        if "total_cached" not in self._stats:
            self._stats["total_cached"] = 0

    @staticmethod
    def compute_hash(
        prompt: str,
        model: str,
        temperature: float,
        system: str | None = None,
    ) -> str:
        """
        Compute a stable hash for a prompt configuration.

        Uses xxhash for speed (10x faster than SHA256).
        """
        hasher = xxhash.xxh128()
        hasher.update(prompt.encode("utf-8"))
        hasher.update(model.encode("utf-8"))
        hasher.update(str(temperature).encode("utf-8"))
        if system:
            hasher.update(system.encode("utf-8"))
        return hasher.hexdigest()

    def get(self, prompt_hash: str) -> CacheEntry | None:
        """
        Retrieve a cached response.

        Returns None if not found or expired.
        """
        try:
            data = self._cache.get(prompt_hash)
            if data is None:
                self._stats["misses"] = self._stats.get("misses", 0) + 1
                return None

            entry = CacheEntry.from_dict(data)

            # Check expiration
            if time.time() - entry.timestamp > self.ttl_seconds:
                self._cache.delete(prompt_hash)
                self._stats["misses"] = self._stats.get("misses", 0) + 1
                logger.debug("cache_entry_expired", prompt_hash=prompt_hash[:16])
                return None

            self._stats["hits"] = self._stats.get("hits", 0) + 1
            self._stats["tokens_saved"] = self._stats.get("tokens_saved", 0) + entry.tokens_used
            logger.debug("cache_hit", prompt_hash=prompt_hash[:16])
            return entry

        except Exception as e:
            logger.warning("cache_get_error", error=str(e), prompt_hash=prompt_hash[:16])
            return None

    def put(
        self,
        prompt_hash: str,
        response: str,
        model: str,
        tokens_used: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store a response in the cache."""
        entry = CacheEntry(
            prompt_hash=prompt_hash,
            response=response,
            model=model,
            timestamp=time.time(),
            tokens_used=tokens_used,
            metadata=metadata or {},
        )

        try:
            self._cache.set(prompt_hash, entry.to_dict())
            self._stats["total_cached"] = self._stats.get("total_cached", 0) + 1
            logger.debug("cache_put", prompt_hash=prompt_hash[:16], tokens=tokens_used)
        except Exception as e:
            logger.warning("cache_put_error", error=str(e), prompt_hash=prompt_hash[:16])

    def contains(self, prompt_hash: str) -> bool:
        """Check if a hash exists in the cache (without loading the value)."""
        return prompt_hash in self._cache

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "hits": self._stats.get("hits", 0),
            "misses": self._stats.get("misses", 0),
            "tokens_saved": self._stats.get("tokens_saved", 0),
            "total_cached": self._stats.get("total_cached", 0),
            "hit_rate": (
                self._stats.get("hits", 0)
                / max(1, self._stats.get("hits", 0) + self._stats.get("misses", 0))
            ),
            "size_bytes": self._cache.volume(),
            "entries": len(self._cache),
        }

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._init_stats()
        logger.info("cache_cleared")

    def close(self) -> None:
        """Close the cache and flush to disk."""
        self._cache.close()
        self._stats.close()
        logger.info("cache_closed")

    def __enter__(self) -> LLMCache:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class BatchRequestStore:
    """
    Storage for batch API requests and results.

    Manages the lifecycle of batch jobs for the 50% discounted pricing.
    """

    def __init__(self, store_dir: Path | None = None) -> None:
        config = get_config()
        self.store_dir = store_dir or config.cache_dir / "batches"
        self.store_dir.mkdir(parents=True, exist_ok=True)

        self._db = SqliteDict(
            str(self.store_dir / "batch_jobs.sqlite"),
            autocommit=True,
        )

    def create_batch(self, batch_id: str, requests: list[dict[str, Any]]) -> Path:
        """
        Create a batch file for submission.

        Returns the path to the JSONL file.
        """
        batch_file = self.store_dir / f"{batch_id}.jsonl"

        with open(batch_file, "wb") as f:
            for req in requests:
                f.write(orjson.dumps(req) + b"\n")

        self._db[batch_id] = {
            "status": "pending",
            "file": str(batch_file),
            "created_at": time.time(),
            "request_count": len(requests),
            "completed_count": 0,
        }

        logger.info("batch_created", batch_id=batch_id, requests=len(requests))
        return batch_file

    def update_batch_status(
        self,
        batch_id: str,
        status: str,
        api_batch_id: str | None = None,
    ) -> None:
        """Update the status of a batch job."""
        if batch_id in self._db:
            data = self._db[batch_id]
            data["status"] = status
            if api_batch_id:
                data["api_batch_id"] = api_batch_id
            data["updated_at"] = time.time()
            self._db[batch_id] = data

    def store_batch_results(
        self,
        batch_id: str,
        results: list[dict[str, Any]],
    ) -> None:
        """Store results from a completed batch."""
        results_file = self.store_dir / f"{batch_id}_results.jsonl"

        with open(results_file, "wb") as f:
            for result in results:
                f.write(orjson.dumps(result) + b"\n")

        if batch_id in self._db:
            data = self._db[batch_id]
            data["status"] = "completed"
            data["results_file"] = str(results_file)
            data["completed_count"] = len(results)
            data["completed_at"] = time.time()
            self._db[batch_id] = data

        logger.info("batch_results_stored", batch_id=batch_id, results=len(results))

    def get_pending_batches(self) -> list[dict[str, Any]]:
        """Get all pending batch jobs."""
        pending = []
        for batch_id, data in self._db.items():
            if data.get("status") in ("pending", "processing"):
                pending.append({"batch_id": batch_id, **data})
        return pending

    def get_batch(self, batch_id: str) -> dict[str, Any] | None:
        """Get batch job details."""
        return self._db.get(batch_id)

    def load_batch_results(self, batch_id: str) -> list[dict[str, Any]]:
        """Load results from a completed batch."""
        data = self._db.get(batch_id)
        if not data or "results_file" not in data:
            return []

        results = []
        with open(data["results_file"], "rb") as f:
            for line in f:
                results.append(orjson.loads(line))
        return results

    def close(self) -> None:
        """Close the store."""
        self._db.close()


# Global cache instance
_cache: LLMCache | None = None


def get_cache() -> LLMCache:
    """Get or create the global cache instance."""
    global _cache
    if _cache is None:
        _cache = LLMCache()
    return _cache


def reset_cache() -> None:
    """Reset the global cache instance."""
    global _cache
    if _cache is not None:
        _cache.close()
    _cache = None
