"""Click-based CLI for PRAXIS task generation."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import click
import structlog
from rich.console import Console
from rich.table import Table

from praxis import __version__
from praxis.config import (
    ExecutionMode,
    LLMProvider,
    PraxisConfig,
    set_config,
)

console = Console()


def setup_logging(verbose: bool, structured: bool) -> None:
    """Configure structured logging."""
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if structured:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    import logging

    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG if verbose else logging.INFO,
        stream=sys.stderr,
    )


@click.group()
@click.version_option(version=__version__, prog_name="praxis")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("--json-logs", is_flag=True, help="Use JSON structured logging")
@click.pass_context
def main(ctx: click.Context, verbose: bool, json_logs: bool) -> None:
    """PRAXIS: Generate comprehensive task dictionaries for embodied AI."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose, json_logs)


@main.command()
@click.option(
    "--max-tasks",
    "-n",
    default=1000,
    type=int,
    help="Maximum number of tasks to generate",
)
@click.option(
    "--sample-verbs",
    type=int,
    default=None,
    help="Number of verbs to sample (default: all)",
)
@click.option(
    "--sample-nouns",
    type=int,
    default=None,
    help="Number of nouns to sample (default: all)",
)
@click.option(
    "--session-id",
    type=str,
    default=None,
    help="Session ID for checkpointing (auto-generated if not provided)",
)
@click.option(
    "--provider",
    type=click.Choice(["anthropic", "mock"]),
    default="mock",
    help="LLM provider to use",
)
@click.option(
    "--model",
    type=str,
    default="claude-sonnet-4-20250514",
    help="Model to use for generation",
)
@click.option(
    "--batch-mode",
    is_flag=True,
    help="Use batch API for 50% discount (Anthropic only)",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("output"),
    help="Output directory for generated tasks",
)
@click.option(
    "--workers",
    type=int,
    default=None,
    help="Number of parallel workers (default: auto)",
)
def generate(
    max_tasks: int,
    sample_verbs: int | None,
    sample_nouns: int | None,
    session_id: str | None,
    provider: str,
    model: str,
    batch_mode: bool,
    output_dir: Path,
    workers: int | None,
) -> None:
    """Generate tasks using the verb-noun matrix approach."""
    from praxis.generator import generate_tasks

    config = PraxisConfig(
        llm_provider=LLMProvider(provider),
        llm_model=model,
        execution_mode=ExecutionMode.BATCH if batch_mode else ExecutionMode.REALTIME,
        output_dir=output_dir,
        ray_num_cpus=workers,
    )
    set_config(config)
    config.ensure_dirs()

    console.print(f"[bold blue]PRAXIS Task Generator[/bold blue]")
    console.print(f"Provider: {provider}")
    console.print(f"Model: {model}")
    console.print(f"Max tasks: {max_tasks}")
    console.print(f"Output: {output_dir}")
    console.print()

    with console.status("[bold green]Generating tasks...") as status:
        stats = generate_tasks(
            max_tasks=max_tasks,
            sample_verbs=sample_verbs,
            sample_nouns=sample_nouns,
            session_id=session_id,
            config=config,
        )

    # Display results
    table = Table(title="Generation Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Jobs", str(stats.total_jobs))
    table.add_row("Completed", str(stats.completed_jobs))
    table.add_row("Failed", str(stats.failed_jobs))
    table.add_row("Tasks Generated", str(stats.tasks_generated))
    table.add_row("Elapsed Time", f"{stats.elapsed_seconds:.1f}s")
    table.add_row("Tasks/Second", f"{stats.tasks_per_second:.2f}")
    table.add_row("Tokens Used", str(stats.tokens_used))

    console.print(table)


@main.command()
@click.option(
    "--checkpoint-dir",
    type=click.Path(path_type=Path, exists=True),
    default=Path(".praxis_checkpoints"),
    help="Checkpoint directory to scan",
)
def resume(checkpoint_dir: Path) -> None:
    """Resume a previous generation session."""
    from praxis.checkpoint import CheckpointManager

    sessions = CheckpointManager.list_sessions(checkpoint_dir)

    if not sessions:
        console.print("[yellow]No sessions found to resume.[/yellow]")
        return

    table = Table(title="Available Sessions")
    table.add_column("Session ID", style="cyan")
    table.add_column("Started", style="white")
    table.add_column("Progress", style="green")

    for session in sessions:
        progress = f"{session['completed_jobs']}/{session['total_jobs']}"
        table.add_row(
            session["session_id"],
            str(session["started_at"]),
            progress,
        )

    console.print(table)

    # Prompt to resume
    session_id = click.prompt("Enter session ID to resume", default=sessions[0]["session_id"])

    console.print(f"[bold]Resuming session: {session_id}[/bold]")

    from praxis.generator import ParallelTaskGenerator

    generator = ParallelTaskGenerator(session_id=session_id)

    try:
        # Get pending jobs from checkpoint
        pending_jobs = list(generator.checkpoint.iter_jobs())
        console.print(f"Found {len(pending_jobs)} pending jobs")

        stats = generator.run(iter([]))  # Will pick up pending from checkpoint
        console.print(f"[green]Completed {stats.completed_jobs} jobs[/green]")
    finally:
        generator.shutdown()


@main.command()
@click.argument("output_dir", type=click.Path(path_type=Path, exists=True))
@click.option("--format", "fmt", type=click.Choice(["summary", "detailed"]), default="summary")
def stats(output_dir: Path, fmt: str) -> None:
    """Show statistics for generated tasks."""
    import orjson

    task_files = list(output_dir.glob("tasks_*.jsonl"))

    if not task_files:
        console.print("[yellow]No task files found.[/yellow]")
        return

    total_tasks = 0
    tag_counts: dict[str, int] = {}
    verb_counts: dict[str, int] = {}
    confidence_sum = 0.0

    for task_file in task_files:
        with open(task_file, "rb") as f:
            for line in f:
                task = orjson.loads(line)
                total_tasks += 1

                # Count tags
                for tag in task.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

                # Extract verb from name
                name = task.get("name", "")
                if name:
                    verb = name.split()[0] if name else ""
                    verb_counts[verb] = verb_counts.get(verb, 0) + 1

                # Confidence
                confidence_sum += task.get("confidence", 0.5)

    console.print(f"[bold]Task Statistics[/bold]")
    console.print(f"Total tasks: {total_tasks}")
    console.print(f"Average confidence: {confidence_sum / max(1, total_tasks):.2f}")
    console.print(f"Unique tags: {len(tag_counts)}")
    console.print(f"Unique verbs: {len(verb_counts)}")

    if fmt == "detailed":
        console.print("\n[bold]Top Tags:[/bold]")
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:20]:
            console.print(f"  {tag}: {count}")

        console.print("\n[bold]Top Verbs:[/bold]")
        for verb, count in sorted(verb_counts.items(), key=lambda x: -x[1])[:20]:
            console.print(f"  {verb}: {count}")


@main.command()
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, exists=True),
    default=Path("output"),
    help="Directory with generated tasks",
)
@click.option(
    "--sample-size",
    type=int,
    default=5000,
    help="Number of tasks to sample for analysis",
)
@click.option(
    "--n-clusters",
    type=int,
    default=50,
    help="Number of clusters for diversity analysis",
)
def analyze(output_dir: Path, sample_size: int, n_clusters: int) -> None:
    """Analyze task diversity using clustering."""
    from praxis.diversity import DiversityAnalyzer

    console.print("[bold]Analyzing task diversity...[/bold]")

    analyzer = DiversityAnalyzer()

    with console.status("Loading tasks..."):
        tasks = analyzer.load_tasks(output_dir, sample_size=sample_size)
        console.print(f"Loaded {len(tasks)} tasks")

    with console.status("Computing embeddings..."):
        embeddings = analyzer.compute_embeddings(tasks)
        console.print(f"Computed embeddings: {embeddings.shape}")

    with console.status("Clustering..."):
        labels, metrics = analyzer.cluster(embeddings, n_clusters=n_clusters)

    # Display results
    table = Table(title="Diversity Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Silhouette Score", f"{metrics['silhouette_score']:.3f}")
    table.add_row("Calinski-Harabasz", f"{metrics['calinski_harabasz']:.1f}")
    table.add_row("Davies-Bouldin", f"{metrics['davies_bouldin']:.3f}")
    table.add_row("Coverage Score", f"{metrics['coverage_score']:.3f}")

    console.print(table)

    # Show cluster labels
    console.print("\n[bold]Cluster Labels:[/bold]")
    for cluster_id, label in sorted(metrics.get("cluster_labels", {}).items()):
        size = metrics.get("cluster_sizes", {}).get(cluster_id, 0)
        console.print(f"  Cluster {cluster_id} ({size} tasks): {label}")


@main.command()
def monitor() -> None:
    """Launch the interactive TUI monitor."""
    from praxis.tui import PraxisTUI

    app = PraxisTUI()
    app.run()


@main.command()
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path),
    default=Path(".praxis_cache"),
    help="Cache directory",
)
def cache_stats(cache_dir: Path) -> None:
    """Show LLM response cache statistics."""
    from praxis.cache import LLMCache

    cache = LLMCache(cache_dir=cache_dir)
    stats = cache.get_stats()

    table = Table(title="Cache Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Entries", str(stats["entries"]))
    table.add_row("Cache Hits", str(stats["hits"]))
    table.add_row("Cache Misses", str(stats["misses"]))
    table.add_row("Hit Rate", f"{stats['hit_rate']:.1%}")
    table.add_row("Tokens Saved", str(stats["tokens_saved"]))
    table.add_row("Size (MB)", f"{stats['size_bytes'] / 1024 / 1024:.1f}")

    console.print(table)
    cache.close()


@main.command()
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path),
    default=Path(".praxis_cache"),
    help="Cache directory",
)
@click.confirmation_option(prompt="Are you sure you want to clear the cache?")
def cache_clear(cache_dir: Path) -> None:
    """Clear the LLM response cache."""
    from praxis.cache import LLMCache

    cache = LLMCache(cache_dir=cache_dir)
    cache.clear()
    console.print("[green]Cache cleared.[/green]")
    cache.close()


@main.command()
def sources() -> None:
    """Show available data sources and their sizes."""
    from praxis.sources import (
        get_noun_source,
        get_persona_source,
        get_verb_source,
        TaskDomain,
    )

    verb_source = get_verb_source()
    noun_source = get_noun_source()
    persona_source = get_persona_source()

    table = Table(title="Data Sources")
    table.add_column("Source", style="cyan")
    table.add_column("Count", style="green")

    table.add_row("Verbs", str(len(verb_source.get_verbs())))
    table.add_row("Nouns", str(len(noun_source.get_nouns())))
    table.add_row("Personas", str(len(persona_source.get_personas())))

    console.print(table)

    # Verb categories
    console.print("\n[bold]Verb Categories:[/bold]")
    categories = {}
    for v in verb_source.get_verbs():
        categories[v.category] = categories.get(v.category, 0) + 1
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        console.print(f"  {cat}: {count}")

    # Personas by domain
    console.print("\n[bold]Personas by Domain:[/bold]")
    for domain in TaskDomain:
        count = len(persona_source.get_personas_by_domain(domain))
        console.print(f"  {domain.value}: {count}")


@main.command()
@click.option(
    "--verbs",
    type=int,
    default=10,
    help="Number of verbs to sample",
)
@click.option(
    "--nouns",
    type=int,
    default=10,
    help="Number of nouns to sample",
)
def sample(verbs: int, nouns: int) -> None:
    """Sample verbs and nouns for preview."""
    from praxis.sources import get_noun_source, get_verb_source

    verb_source = get_verb_source()
    noun_source = get_noun_source()

    sampled_verbs = verb_source.sample_verbs(verbs)
    sampled_nouns = noun_source.sample_nouns(nouns)

    console.print("[bold]Sampled Verbs:[/bold]")
    for v in sampled_verbs:
        console.print(f"  {v.verb} ({v.category})")

    console.print("\n[bold]Sampled Nouns:[/bold]")
    for n in sampled_nouns:
        console.print(f"  {n.noun} ({n.category})")

    console.print(f"\n[bold]Potential combinations: {verbs * nouns}[/bold]")


@main.command()
@click.argument("verb")
@click.argument("noun")
@click.option(
    "--provider",
    type=click.Choice(["anthropic", "mock"]),
    default="mock",
    help="LLM provider to use",
)
def preview(verb: str, noun: str, provider: str) -> None:
    """Preview task generation for a single verb-noun pair."""
    from praxis.config import LLMProvider, PraxisConfig, set_config
    from praxis.generator import (
        SYSTEM_PROMPT,
        TASK_GENERATION_PROMPT,
        parse_json_response,
    )
    from praxis.llm import LLMRequest, create_client

    config = PraxisConfig(llm_provider=LLMProvider(provider))
    set_config(config)

    client = create_client(config)

    prompt = TASK_GENERATION_PROMPT.format(
        verb=verb,
        noun=noun,
        persona_title="General user",
        persona_description="Everyday task performer",
    )

    console.print(f"[bold]Generating task for: {verb} {noun}[/bold]\n")

    request = LLMRequest(prompt=prompt, system=SYSTEM_PROMPT)
    response = client.complete(request)

    parsed = parse_json_response(response.content)

    if parsed:
        import json

        console.print("[bold green]Generated Task:[/bold green]")
        console.print(json.dumps(parsed, indent=2))
    else:
        console.print("[red]Failed to parse response:[/red]")
        console.print(response.content)


if __name__ == "__main__":
    main()
