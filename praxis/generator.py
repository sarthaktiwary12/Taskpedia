"""Ray-based parallel task generator with streaming and checkpointing."""

from __future__ import annotations

import hashlib
import itertools
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator

import orjson
import ray
import structlog
from ray.util.queue import Queue as RayQueue

from praxis.cache import get_cache
from praxis.checkpoint import CheckpointManager, JobItem, JobStatus, TaskWriter
from praxis.config import PraxisConfig, get_config
from praxis.llm import LLMClient, LLMRequest, create_client
from praxis.sources import (
    NounEntry,
    PersonaEntry,
    VerbEntry,
    get_noun_source,
    get_persona_source,
    get_verb_source,
)

logger = structlog.get_logger()


# Prompt templates for task generation
SYSTEM_PROMPT = """You are an expert in human task analysis for robotics and embodied AI systems.
You generate precise, structured task definitions that can be used to train humanoid robots.
Focus on physical, observable, and verifiable task specifications."""

TASK_GENERATION_PROMPT = """Generate a complete task definition for the following:

Verb: {verb}
Noun: {noun}
Persona perspective: {persona_title} - {persona_description}

Generate a JSON object with this exact structure:
{{
    "name": "the task name (verb + noun phrase)",
    "completion": {{
        "precondition": "What must be true before the task starts",
        "postcondition": "What must be true when the task is complete",
        "invariants": "What must remain true throughout the task"
    }},
    "physical": "Physical requirements: body parts, forces, movements, tools",
    "sensing": "Sensing requirements: visual, tactile, proprioceptive feedback",
    "cognitive": "Cognitive requirements: planning, sequencing, error detection",
    "context": "Typical environment and situational context",
    "tags": ["list", "of", "relevant", "tags"],
    "confidence": 0.0 to 1.0
}}

Be specific and precise. Focus on observable, measurable criteria.
Respond with ONLY the JSON object, no additional text."""

TASK_DECOMPOSITION_PROMPT = """Decompose this task into 2-5 subtasks:

Task: {task_name}
Precondition: {precondition}
Postcondition: {postcondition}

Generate a JSON array of subtask objects, each with the same structure as the parent.
Subtasks should be:
- Ordered sequentially
- Each with clear precondition/postcondition handoff
- Together achieving the parent postcondition

Respond with ONLY the JSON array."""

TASK_EVOLUTION_PROMPT = """Evolve this task by applying the mutation: {mutation_type}

Original Task:
{task_json}

Mutation types:
- add_constraint: Make more specific or challenging
- change_context: Different environment or situation
- add_tool: Require a specific tool
- add_person: Make collaborative
- time_pressure: Add urgency
- precision_increase: Require more accuracy

Generate the evolved task as a JSON object with the same structure.
Respond with ONLY the JSON object."""

VALIDATION_PROMPT = """Evaluate this task definition for quality:

{task_json}

Score each criterion from 0.0 to 1.0:
1. completion_clarity: Are precondition/postcondition clear and verifiable?
2. precondition_completeness: Does precondition capture all requirements?
3. postcondition_specificity: Is the postcondition observable and measurable?
4. invariant_necessity: Are invariants meaningful constraints?
5. physical_accuracy: Is the physical description realistic?
6. tag_accuracy: Are tags appropriate and complete?
7. is_real_task: Is this a genuine human task?

Respond with ONLY a JSON object:
{{"completion_clarity": 0.0, "precondition_completeness": 0.0, ...}}"""


class MutationType(str, Enum):
    """Types of task evolution mutations."""

    ADD_CONSTRAINT = "add_constraint"
    CHANGE_CONTEXT = "change_context"
    ADD_TOOL = "add_tool"
    ADD_PERSON = "add_person"
    TIME_PRESSURE = "time_pressure"
    PRECISION_INCREASE = "precision_increase"


@dataclass
class GenerationResult:
    """Result of a task generation attempt."""

    success: bool
    task: dict[str, Any] | None = None
    error: str | None = None
    prompt_hash: str = ""
    raw_response: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0


@dataclass
class GenerationStats:
    """Statistics for generation progress."""

    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    cached_responses: int = 0
    tokens_used: int = 0
    tasks_generated: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    @property
    def tasks_per_second(self) -> float:
        elapsed = self.elapsed_seconds
        return self.tasks_generated / elapsed if elapsed > 0 else 0.0

    @property
    def progress_percent(self) -> float:
        return (self.completed_jobs / max(1, self.total_jobs)) * 100


def parse_json_response(response: str) -> dict[str, Any] | list[Any] | None:
    """Parse JSON from LLM response, handling common issues."""
    # Try direct parsing first
    try:
        return orjson.loads(response)
    except orjson.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        if end > start:
            try:
                return orjson.loads(response[start:end].strip())
            except orjson.JSONDecodeError:
                pass

    if "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        if end > start:
            try:
                return orjson.loads(response[start:end].strip())
            except orjson.JSONDecodeError:
                pass

    # Try to find JSON object or array
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = response.find(start_char)
        if start >= 0:
            depth = 0
            for i, c in enumerate(response[start:], start):
                if c == start_char:
                    depth += 1
                elif c == end_char:
                    depth -= 1
                    if depth == 0:
                        try:
                            return orjson.loads(response[start : i + 1])
                        except orjson.JSONDecodeError:
                            break

    return None


@ray.remote
class TaskGeneratorWorker:
    """
    Ray actor for parallel task generation.

    Each worker has its own LLM client and processes jobs from the queue.
    """

    def __init__(self, worker_id: int, config_dict: dict[str, Any]) -> None:
        self.worker_id = worker_id
        self.config = PraxisConfig(**config_dict)
        self.client = create_client(self.config)
        self._stats = {
            "jobs_processed": 0,
            "tasks_generated": 0,
            "errors": 0,
        }
        logger.info("worker_initialized", worker_id=worker_id)

    def process_job(self, job: dict[str, Any]) -> dict[str, Any]:
        """Process a single generation job."""
        job_item = JobItem.from_dict(job)
        self._stats["jobs_processed"] += 1

        try:
            if job_item.job_type == "verb_noun":
                result = self._generate_from_verb_noun(job_item.input_data)
            elif job_item.job_type == "decomposition":
                result = self._decompose_task(job_item.input_data)
            elif job_item.job_type == "evolution":
                result = self._evolve_task(job_item.input_data)
            elif job_item.job_type == "validation":
                result = self._validate_task(job_item.input_data)
            else:
                result = GenerationResult(
                    success=False,
                    error=f"Unknown job type: {job_item.job_type}",
                )

            if result.success:
                self._stats["tasks_generated"] += 1
                return {
                    "job_id": job_item.job_id,
                    "status": JobStatus.COMPLETED.value,
                    "result": result.task,
                    "prompt_hash": result.prompt_hash,
                    "tokens_used": result.tokens_used,
                }
            else:
                self._stats["errors"] += 1
                return {
                    "job_id": job_item.job_id,
                    "status": JobStatus.FAILED.value,
                    "error": result.error,
                }

        except Exception as e:
            self._stats["errors"] += 1
            logger.error("job_processing_error", error=str(e), job_id=job_item.job_id)
            return {
                "job_id": job_item.job_id,
                "status": JobStatus.FAILED.value,
                "error": str(e),
            }

    def _generate_from_verb_noun(self, data: dict[str, Any]) -> GenerationResult:
        """Generate a task from verb-noun pair."""
        prompt = TASK_GENERATION_PROMPT.format(
            verb=data["verb"],
            noun=data["noun"],
            persona_title=data.get("persona_title", "General user"),
            persona_description=data.get("persona_description", "Everyday task performer"),
        )

        request = LLMRequest(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            temperature=self.config.temperature,
            metadata={"verb": data["verb"], "noun": data["noun"]},
        )

        start = time.time()
        response = self.client.complete(request)
        latency = (time.time() - start) * 1000

        parsed = parse_json_response(response.content)
        if parsed and isinstance(parsed, dict):
            # Add provenance
            parsed["id"] = f"en_{data['verb']}_{data['noun']}".replace(" ", "_").lower()
            parsed["language"] = "en"
            parsed["provenance"] = {
                "generation_method": "verb_noun_matrix",
                "prompt_hash": response.prompt_hash,
                "persona": data.get("persona_title"),
            }

            return GenerationResult(
                success=True,
                task=parsed,
                prompt_hash=response.prompt_hash,
                raw_response=response.content,
                tokens_used=response.tokens_input + response.tokens_output,
                latency_ms=latency,
            )

        return GenerationResult(
            success=False,
            error="Failed to parse JSON response",
            raw_response=response.content,
        )

    def _decompose_task(self, data: dict[str, Any]) -> GenerationResult:
        """Decompose a task into subtasks."""
        prompt = TASK_DECOMPOSITION_PROMPT.format(
            task_name=data["name"],
            precondition=data["completion"]["precondition"],
            postcondition=data["completion"]["postcondition"],
        )

        request = LLMRequest(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            temperature=self.config.temperature,
        )

        response = self.client.complete(request)
        parsed = parse_json_response(response.content)

        if parsed and isinstance(parsed, list):
            return GenerationResult(
                success=True,
                task={"subtasks": parsed},
                prompt_hash=response.prompt_hash,
                tokens_used=response.tokens_input + response.tokens_output,
            )

        return GenerationResult(
            success=False,
            error="Failed to parse subtasks",
            raw_response=response.content,
        )

    def _evolve_task(self, data: dict[str, Any]) -> GenerationResult:
        """Evolve a task with a mutation."""
        task_json = orjson.dumps(data["task"], option=orjson.OPT_INDENT_2).decode()
        prompt = TASK_EVOLUTION_PROMPT.format(
            mutation_type=data["mutation_type"],
            task_json=task_json,
        )

        request = LLMRequest(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            temperature=self.config.temperature,
        )

        response = self.client.complete(request)
        parsed = parse_json_response(response.content)

        if parsed and isinstance(parsed, dict):
            parsed["provenance"] = {
                "generation_method": "evolution",
                "parent_task": data["task"].get("id"),
                "mutation_type": data["mutation_type"],
            }
            return GenerationResult(
                success=True,
                task=parsed,
                prompt_hash=response.prompt_hash,
                tokens_used=response.tokens_input + response.tokens_output,
            )

        return GenerationResult(success=False, error="Failed to parse evolved task")

    def _validate_task(self, data: dict[str, Any]) -> GenerationResult:
        """Validate a task using LLM-as-judge."""
        task_json = orjson.dumps(data["task"], option=orjson.OPT_INDENT_2).decode()
        prompt = VALIDATION_PROMPT.format(task_json=task_json)

        request = LLMRequest(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            temperature=0.0,  # Deterministic for validation
        )

        response = self.client.complete(request)
        parsed = parse_json_response(response.content)

        if parsed and isinstance(parsed, dict):
            return GenerationResult(
                success=True,
                task={"validation_scores": parsed},
                prompt_hash=response.prompt_hash,
                tokens_used=response.tokens_input + response.tokens_output,
            )

        return GenerationResult(success=False, error="Failed to parse validation scores")

    def get_stats(self) -> dict[str, Any]:
        """Get worker statistics."""
        return {
            "worker_id": self.worker_id,
            **self._stats,
            "llm_stats": self.client.get_stats(),
        }


class ParallelTaskGenerator:
    """
    Orchestrates parallel task generation using Ray.

    Features:
    - Automatic work distribution across workers
    - Checkpoint-based crash recovery
    - Streaming results to disk
    - Progress tracking and monitoring
    """

    def __init__(
        self,
        session_id: str | None = None,
        config: PraxisConfig | None = None,
    ) -> None:
        self.config = config or get_config()
        self.session_id = session_id or str(uuid.uuid4())[:8]

        # Initialize Ray if needed
        if not ray.is_initialized():
            ray.init(
                num_cpus=self.config.ray_num_cpus,
                object_store_memory=self.config.ray_object_store_memory,
                ignore_reinit_error=True,
            )

        # Create checkpoint manager
        self.checkpoint = CheckpointManager(
            session_id=self.session_id,
            checkpoint_dir=self.config.checkpoint_dir,
        )

        # Create task writer
        self.writer = TaskWriter(output_dir=self.config.output_dir)

        # Statistics
        self.stats = GenerationStats()

        # Data sources
        self.verb_source = get_verb_source()
        self.noun_source = get_noun_source()
        self.persona_source = get_persona_source()

        # Workers (lazy initialization)
        self._workers: list[ray.ObjectRef] | None = None

        logger.info(
            "parallel_generator_initialized",
            session_id=self.session_id,
            num_cpus=ray.cluster_resources().get("CPU", 0),
        )

    def _ensure_workers(self) -> list[ray.ObjectRef]:
        """Ensure workers are initialized."""
        if self._workers is None:
            num_workers = int(
                ray.cluster_resources().get("CPU", 4) * self.config.workers_per_cpu
            )
            config_dict = self.config.model_dump()

            self._workers = [
                TaskGeneratorWorker.remote(i, config_dict) for i in range(num_workers)
            ]
            logger.info("workers_created", count=len(self._workers))

        return self._workers

    def generate_verb_noun_jobs(
        self,
        max_jobs: int | None = None,
        sample_verbs: int | None = None,
        sample_nouns: int | None = None,
        balanced_personas: bool = True,
    ) -> Iterator[JobItem]:
        """Generate jobs for verb-noun matrix generation."""
        verbs = self.verb_source.get_verbs()
        nouns = self.noun_source.get_nouns()
        personas = self.persona_source.sample_personas(10, balanced=balanced_personas)

        if sample_verbs:
            verbs = self.verb_source.sample_verbs(sample_verbs)
        if sample_nouns:
            nouns = self.noun_source.sample_nouns(sample_nouns)

        job_count = 0
        for verb, noun in itertools.product(verbs, nouns):
            # Rotate through personas for diversity
            persona = personas[job_count % len(personas)]

            job = JobItem(
                job_id=f"vn_{verb.verb}_{noun.noun}_{job_count}",
                job_type="verb_noun",
                input_data={
                    "verb": verb.verb,
                    "noun": noun.noun,
                    "verb_category": verb.category,
                    "noun_category": noun.category,
                    "persona_title": persona.title,
                    "persona_description": persona.description,
                    "persona_domain": persona.domain.value,
                },
            )

            yield job
            job_count += 1

            if max_jobs and job_count >= max_jobs:
                return

    def run(
        self,
        jobs: Iterator[JobItem] | list[JobItem],
        batch_size: int = 100,
    ) -> GenerationStats:
        """
        Run parallel task generation.

        Args:
            jobs: Iterator or list of jobs to process
            batch_size: Number of jobs to process in parallel

        Returns:
            Final generation statistics
        """
        workers = self._ensure_workers()
        num_workers = len(workers)

        # Initialize session
        session = self.checkpoint.initialize_session(
            config_snapshot=self.config.model_dump(),
        )

        # Check for pending jobs from previous run
        pending = self.checkpoint.get_pending_jobs(limit=batch_size)
        if pending:
            logger.info("resuming_pending_jobs", count=len(pending))
            jobs = itertools.chain(pending, jobs)

        # Process in batches
        job_batch: list[JobItem] = []
        futures: list[ray.ObjectRef] = []
        future_to_job: dict[ray.ObjectRef, JobItem] = {}

        for job in jobs:
            # Check if already completed
            existing = self.checkpoint.get_job(job.job_id)
            if existing and existing.status == JobStatus.COMPLETED:
                self.stats.completed_jobs += 1
                continue

            # Add to checkpoint
            self.checkpoint.add_job(job)
            job_batch.append(job)
            self.stats.total_jobs += 1

            if len(job_batch) >= batch_size:
                # Submit batch
                self._submit_batch(workers, job_batch, futures, future_to_job)
                job_batch = []

            # Process completed futures
            if len(futures) >= num_workers * 2:
                self._process_completed(futures, future_to_job)

        # Submit remaining jobs
        if job_batch:
            self._submit_batch(workers, job_batch, futures, future_to_job)

        # Wait for all to complete
        while futures:
            self._process_completed(futures, future_to_job, wait=True)

        # Finalize
        self.writer.flush()
        self.checkpoint.flush()

        logger.info(
            "generation_complete",
            total_jobs=self.stats.total_jobs,
            completed=self.stats.completed_jobs,
            failed=self.stats.failed_jobs,
            tasks_generated=self.stats.tasks_generated,
            elapsed_seconds=self.stats.elapsed_seconds,
        )

        return self.stats

    def _submit_batch(
        self,
        workers: list[ray.ObjectRef],
        jobs: list[JobItem],
        futures: list[ray.ObjectRef],
        future_to_job: dict[ray.ObjectRef, JobItem],
    ) -> None:
        """Submit a batch of jobs to workers."""
        for i, job in enumerate(jobs):
            worker = workers[i % len(workers)]
            future = worker.process_job.remote(job.to_dict())
            futures.append(future)
            future_to_job[future] = job

    def _process_completed(
        self,
        futures: list[ray.ObjectRef],
        future_to_job: dict[ray.ObjectRef, JobItem],
        wait: bool = False,
    ) -> None:
        """Process completed futures."""
        if wait:
            ready, remaining = ray.wait(futures, num_returns=len(futures), timeout=60)
        else:
            ready, remaining = ray.wait(futures, num_returns=1, timeout=0.1)

        futures.clear()
        futures.extend(remaining)

        for future in ready:
            try:
                result = ray.get(future)
                job = future_to_job.pop(future)

                if result["status"] == JobStatus.COMPLETED.value:
                    self.stats.completed_jobs += 1
                    self.stats.tasks_generated += 1
                    self.stats.tokens_used += result.get("tokens_used", 0)

                    # Write task
                    task = result["result"]
                    self.writer.write(task)
                    self.checkpoint.store_task(task.get("id", job.job_id), task)

                    # Update checkpoint
                    self.checkpoint.update_job(
                        job.job_id,
                        JobStatus.COMPLETED,
                        result=result["result"],
                    )
                else:
                    self.stats.failed_jobs += 1
                    self.checkpoint.update_job(
                        job.job_id,
                        JobStatus.FAILED,
                        error=result.get("error"),
                    )

            except Exception as e:
                logger.error("future_processing_error", error=str(e))
                if future in future_to_job:
                    job = future_to_job.pop(future)
                    self.stats.failed_jobs += 1
                    self.checkpoint.update_job(job.job_id, JobStatus.FAILED, error=str(e))

    def get_progress(self) -> dict[str, Any]:
        """Get current progress."""
        return {
            **self.stats.__dict__,
            "checkpoint_progress": self.checkpoint.get_progress(),
            "cache_stats": get_cache().get_stats(),
            "writer_stats": self.writer.get_stats(),
        }

    def shutdown(self) -> None:
        """Shutdown the generator and cleanup."""
        self.writer.close()
        self.checkpoint.close()

        if self._workers:
            for worker in self._workers:
                ray.kill(worker)
            self._workers = None

        logger.info("generator_shutdown", session_id=self.session_id)


def generate_tasks(
    max_tasks: int = 1000,
    sample_verbs: int | None = None,
    sample_nouns: int | None = None,
    session_id: str | None = None,
    config: PraxisConfig | None = None,
) -> GenerationStats:
    """
    Convenience function to generate tasks.

    Args:
        max_tasks: Maximum number of tasks to generate
        sample_verbs: Number of verbs to sample (None = all)
        sample_nouns: Number of nouns to sample (None = all)
        session_id: Session ID for checkpointing
        config: Configuration override

    Returns:
        Generation statistics
    """
    generator = ParallelTaskGenerator(session_id=session_id, config=config)

    try:
        jobs = generator.generate_verb_noun_jobs(
            max_jobs=max_tasks,
            sample_verbs=sample_verbs,
            sample_nouns=sample_nouns,
        )
        return generator.run(jobs)
    finally:
        generator.shutdown()
