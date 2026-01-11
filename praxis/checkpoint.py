"""Checkpoint and recovery system for crash resilience."""

from __future__ import annotations

import atexit
import signal
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterator

import orjson
import structlog
from sqlitedict import SqliteDict

from praxis.config import get_config

logger = structlog.get_logger()


class JobStatus(str, Enum):
    """Status of a generation job."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class JobItem:
    """A single item in the generation queue."""

    job_id: str
    job_type: str  # "verb_noun", "decomposition", "expansion", "evolution", "cultural"
    input_data: dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    attempts: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "input_data": self.input_data,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "attempts": self.attempts,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JobItem:
        """Create from dictionary."""
        return cls(
            job_id=data["job_id"],
            job_type=data["job_type"],
            input_data=data["input_data"],
            status=JobStatus(data["status"]),
            result=data.get("result"),
            error=data.get("error"),
            attempts=data.get("attempts", 0),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )


@dataclass
class SessionState:
    """State of a generation session."""

    session_id: str
    started_at: float
    config_snapshot: dict[str, Any]
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    last_checkpoint: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "config_snapshot": self.config_snapshot,
            "total_jobs": self.total_jobs,
            "completed_jobs": self.completed_jobs,
            "failed_jobs": self.failed_jobs,
            "last_checkpoint": self.last_checkpoint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionState:
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            started_at=data["started_at"],
            config_snapshot=data["config_snapshot"],
            total_jobs=data.get("total_jobs", 0),
            completed_jobs=data.get("completed_jobs", 0),
            failed_jobs=data.get("failed_jobs", 0),
            last_checkpoint=data.get("last_checkpoint", time.time()),
        )


class CheckpointManager:
    """
    Manages checkpoints for crash recovery.

    Uses SQLite for ACID guarantees and efficient querying.
    Automatically registers signal handlers for graceful shutdown.
    """

    def __init__(
        self,
        session_id: str,
        checkpoint_dir: Path | None = None,
        auto_checkpoint_interval: int = 100,
    ) -> None:
        config = get_config()
        self.session_id = session_id
        self.checkpoint_dir = checkpoint_dir or config.checkpoint_dir
        self.auto_checkpoint_interval = auto_checkpoint_interval

        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self.checkpoint_dir / f"{session_id}.sqlite"

        # Initialize database
        self._jobs = SqliteDict(str(self._db_path), tablename="jobs", autocommit=True)
        self._meta = SqliteDict(str(self._db_path), tablename="metadata", autocommit=True)
        self._tasks = SqliteDict(str(self._db_path), tablename="tasks", autocommit=True)

        # Operation counter for auto-checkpointing
        self._ops_since_checkpoint = 0

        # Register cleanup handlers
        self._register_handlers()

        logger.info(
            "checkpoint_manager_initialized",
            session_id=session_id,
            db_path=str(self._db_path),
        )

    def _register_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        atexit.register(self._cleanup)

        def signal_handler(signum: int, frame: Any) -> None:
            logger.warning("signal_received", signal=signum)
            self._cleanup()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def _cleanup(self) -> None:
        """Cleanup handler for shutdown."""
        try:
            self.flush()
            self.close()
        except Exception as e:
            logger.error("cleanup_error", error=str(e))

    def initialize_session(
        self,
        config_snapshot: dict[str, Any],
        total_jobs: int = 0,
    ) -> SessionState:
        """Initialize or resume a session."""
        existing = self._meta.get("session")
        if existing:
            state = SessionState.from_dict(existing)
            logger.info(
                "session_resumed",
                session_id=state.session_id,
                completed=state.completed_jobs,
                total=state.total_jobs,
            )
            return state

        state = SessionState(
            session_id=self.session_id,
            started_at=time.time(),
            config_snapshot=config_snapshot,
            total_jobs=total_jobs,
        )
        self._meta["session"] = state.to_dict()
        logger.info("session_initialized", session_id=self.session_id)
        return state

    def get_session(self) -> SessionState | None:
        """Get current session state."""
        data = self._meta.get("session")
        return SessionState.from_dict(data) if data else None

    def update_session(
        self,
        completed_delta: int = 0,
        failed_delta: int = 0,
        total_jobs: int | None = None,
    ) -> None:
        """Update session statistics."""
        session = self._meta.get("session")
        if session:
            session["completed_jobs"] += completed_delta
            session["failed_jobs"] += failed_delta
            if total_jobs is not None:
                session["total_jobs"] = total_jobs
            session["last_checkpoint"] = time.time()
            self._meta["session"] = session

    def add_job(self, job: JobItem) -> None:
        """Add a job to the queue."""
        self._jobs[job.job_id] = job.to_dict()
        self._maybe_checkpoint()

    def add_jobs_batch(self, jobs: list[JobItem]) -> None:
        """Add multiple jobs efficiently."""
        for job in jobs:
            self._jobs[job.job_id] = job.to_dict()
        self._ops_since_checkpoint += len(jobs)
        self._maybe_checkpoint()
        logger.debug("jobs_batch_added", count=len(jobs))

    def get_job(self, job_id: str) -> JobItem | None:
        """Get a job by ID."""
        data = self._jobs.get(job_id)
        return JobItem.from_dict(data) if data else None

    def update_job(
        self,
        job_id: str,
        status: JobStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Update a job's status and result."""
        data = self._jobs.get(job_id)
        if data:
            data["status"] = status.value
            data["result"] = result
            data["error"] = error
            data["attempts"] = data.get("attempts", 0) + 1
            data["updated_at"] = time.time()
            self._jobs[job_id] = data

            # Update session stats
            if status == JobStatus.COMPLETED:
                self.update_session(completed_delta=1)
            elif status == JobStatus.FAILED:
                self.update_session(failed_delta=1)

        self._maybe_checkpoint()

    def get_pending_jobs(self, limit: int = 100) -> list[JobItem]:
        """Get pending jobs for processing."""
        pending = []
        for job_id, data in self._jobs.items():
            if data["status"] == JobStatus.PENDING.value:
                pending.append(JobItem.from_dict(data))
                if len(pending) >= limit:
                    break
        return pending

    def get_failed_jobs(self, max_attempts: int = 3) -> list[JobItem]:
        """Get failed jobs that can be retried."""
        failed = []
        for job_id, data in self._jobs.items():
            if (
                data["status"] == JobStatus.FAILED.value
                and data.get("attempts", 0) < max_attempts
            ):
                failed.append(JobItem.from_dict(data))
        return failed

    def iter_jobs(
        self,
        status: JobStatus | None = None,
        job_type: str | None = None,
    ) -> Iterator[JobItem]:
        """Iterate over jobs with optional filtering."""
        for job_id, data in self._jobs.items():
            if status and data["status"] != status.value:
                continue
            if job_type and data["job_type"] != job_type:
                continue
            yield JobItem.from_dict(data)

    def store_task(self, task_id: str, task_data: dict[str, Any]) -> None:
        """Store a generated task."""
        self._tasks[task_id] = task_data
        self._maybe_checkpoint()

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Get a stored task."""
        return self._tasks.get(task_id)

    def iter_tasks(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """Iterate over all stored tasks."""
        for task_id, data in self._tasks.items():
            yield task_id, data

    def task_count(self) -> int:
        """Get the number of stored tasks."""
        return len(self._tasks)

    def get_progress(self) -> dict[str, Any]:
        """Get current progress statistics."""
        session = self.get_session()
        if not session:
            return {}

        # Count jobs by status
        status_counts: dict[str, int] = {}
        for data in self._jobs.values():
            status = data["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "session_id": session.session_id,
            "started_at": session.started_at,
            "elapsed_seconds": time.time() - session.started_at,
            "total_jobs": session.total_jobs,
            "completed_jobs": session.completed_jobs,
            "failed_jobs": session.failed_jobs,
            "tasks_generated": len(self._tasks),
            "jobs_by_status": status_counts,
            "progress_percent": (
                (session.completed_jobs / max(1, session.total_jobs)) * 100
            ),
        }

    def _maybe_checkpoint(self) -> None:
        """Check if we should create a checkpoint."""
        self._ops_since_checkpoint += 1
        if self._ops_since_checkpoint >= self.auto_checkpoint_interval:
            self.flush()
            self._ops_since_checkpoint = 0

    def flush(self) -> None:
        """Force flush all data to disk."""
        self._jobs.commit()
        self._meta.commit()
        self._tasks.commit()
        logger.debug("checkpoint_flushed", session_id=self.session_id)

    def close(self) -> None:
        """Close all database connections."""
        self._jobs.close()
        self._meta.close()
        self._tasks.close()
        logger.info("checkpoint_manager_closed", session_id=self.session_id)

    def __enter__(self) -> CheckpointManager:
        return self

    def __exit__(self, *args: Any) -> None:
        self.flush()
        self.close()

    @classmethod
    def list_sessions(cls, checkpoint_dir: Path | None = None) -> list[dict[str, Any]]:
        """List all available sessions for recovery."""
        config = get_config()
        checkpoint_dir = checkpoint_dir or config.checkpoint_dir

        if not checkpoint_dir.exists():
            return []

        sessions = []
        for db_file in checkpoint_dir.glob("*.sqlite"):
            try:
                meta = SqliteDict(str(db_file), tablename="metadata", flag="r")
                session_data = meta.get("session")
                if session_data:
                    sessions.append(
                        {
                            "session_id": session_data["session_id"],
                            "db_file": str(db_file),
                            "started_at": session_data["started_at"],
                            "completed_jobs": session_data.get("completed_jobs", 0),
                            "total_jobs": session_data.get("total_jobs", 0),
                        }
                    )
                meta.close()
            except Exception as e:
                logger.warning("session_scan_error", file=str(db_file), error=str(e))

        return sorted(sessions, key=lambda x: x["started_at"], reverse=True)


class TaskWriter:
    """
    Efficient task writer with minimal memory footprint.

    Writes tasks to JSONL files with periodic flushing.
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        buffer_size: int = 100,
    ) -> None:
        config = get_config()
        self.output_dir = output_dir or config.output_dir
        self.buffer_size = buffer_size

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._buffer: list[dict[str, Any]] = []
        self._file_counter = 0
        self._task_counter = 0
        self._tasks_per_file = 10000

    def write(self, task: dict[str, Any]) -> None:
        """Write a task to the buffer."""
        self._buffer.append(task)
        self._task_counter += 1

        if len(self._buffer) >= self.buffer_size:
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Flush buffer to disk."""
        if not self._buffer:
            return

        # Determine which file(s) to write to
        while self._buffer:
            current_file = self.output_dir / f"tasks_{self._file_counter:06d}.jsonl"

            # Count existing lines if file exists
            existing_lines = 0
            if current_file.exists():
                with open(current_file, "rb") as f:
                    existing_lines = sum(1 for _ in f)

            remaining_in_file = self._tasks_per_file - existing_lines

            if remaining_in_file <= 0:
                self._file_counter += 1
                continue

            # Write what fits
            to_write = self._buffer[:remaining_in_file]
            self._buffer = self._buffer[remaining_in_file:]

            with open(current_file, "ab") as f:
                for task in to_write:
                    f.write(orjson.dumps(task) + b"\n")

            if len(to_write) == remaining_in_file:
                self._file_counter += 1

        logger.debug("buffer_flushed", tasks_written=self._task_counter)

    def flush(self) -> None:
        """Force flush all buffered tasks."""
        self._flush_buffer()

    def get_stats(self) -> dict[str, Any]:
        """Get writer statistics."""
        return {
            "tasks_written": self._task_counter,
            "files_created": self._file_counter + 1,
            "buffer_size": len(self._buffer),
        }

    def close(self) -> None:
        """Close the writer, flushing any remaining tasks."""
        self.flush()
        logger.info("task_writer_closed", total_tasks=self._task_counter)

    def __enter__(self) -> TaskWriter:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
