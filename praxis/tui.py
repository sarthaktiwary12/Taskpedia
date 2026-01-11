"""Textual-based TUI for monitoring task generation quality and progress."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import orjson
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    Log,
    ProgressBar,
    Rule,
    Sparkline,
    Static,
    TabbedContent,
    TabPane,
)

from praxis.cache import LLMCache
from praxis.checkpoint import CheckpointManager
from praxis.config import get_config


class TaskDetailModal(ModalScreen):
    """Modal screen to show task details."""

    CSS = """
    TaskDetailModal {
        align: center middle;
    }

    TaskDetailModal > Vertical {
        width: 80%;
        height: 80%;
        background: $surface;
        border: tall $primary;
        padding: 1 2;
    }

    TaskDetailModal .task-content {
        height: 1fr;
        overflow-y: auto;
    }
    """

    def __init__(self, task: dict[str, Any]) -> None:
        super().__init__()
        self.task = task

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[bold]{self.task.get('name', 'Unknown Task')}[/bold]")
            yield Rule()
            yield ScrollableContainer(
                Static(self._format_task(), classes="task-content")
            )
            yield Rule()
            yield Button("Close", variant="primary", id="close")

    def _format_task(self) -> str:
        """Format task for display."""
        lines = []
        lines.append(f"[bold cyan]ID:[/] {self.task.get('id', 'N/A')}")
        lines.append(f"[bold cyan]Language:[/] {self.task.get('language', 'en')}")
        lines.append("")

        if "completion" in self.task:
            c = self.task["completion"]
            lines.append("[bold green]Completion Criteria:[/]")
            lines.append(f"  [cyan]Precondition:[/] {c.get('precondition', 'N/A')}")
            lines.append(f"  [cyan]Postcondition:[/] {c.get('postcondition', 'N/A')}")
            lines.append(f"  [cyan]Invariants:[/] {c.get('invariants', 'N/A')}")
            lines.append("")

        lines.append(f"[bold yellow]Physical:[/] {self.task.get('physical', 'N/A')}")
        lines.append(f"[bold yellow]Sensing:[/] {self.task.get('sensing', 'N/A')}")
        lines.append(f"[bold yellow]Cognitive:[/] {self.task.get('cognitive', 'N/A')}")
        lines.append(f"[bold yellow]Context:[/] {self.task.get('context', 'N/A')}")
        lines.append("")

        tags = self.task.get("tags", [])
        lines.append(f"[bold magenta]Tags:[/] {', '.join(tags)}")

        confidence = self.task.get("confidence", 0.0)
        lines.append(f"[bold blue]Confidence:[/] {confidence:.2f}")

        if "provenance" in self.task:
            p = self.task["provenance"]
            lines.append("")
            lines.append("[bold]Provenance:[/]")
            lines.append(f"  Method: {p.get('generation_method', 'N/A')}")
            lines.append(f"  Persona: {p.get('persona', 'N/A')}")

        return "\n".join(lines)

    @on(Button.Pressed, "#close")
    def close_modal(self) -> None:
        self.dismiss()


class StatsPanel(Static):
    """Panel showing generation statistics."""

    stats: reactive[dict[str, Any]] = reactive({})

    def compose(self) -> ComposeResult:
        yield Static(id="stats-content")

    def watch_stats(self, stats: dict[str, Any]) -> None:
        """Update display when stats change."""
        content = self.query_one("#stats-content", Static)

        if not stats:
            content.update("[dim]No stats available[/dim]")
            return

        lines = []
        lines.append("[bold]Generation Progress[/bold]")
        lines.append(f"  Total Jobs: {stats.get('total_jobs', 0)}")
        lines.append(f"  Completed: [green]{stats.get('completed_jobs', 0)}[/green]")
        lines.append(f"  Failed: [red]{stats.get('failed_jobs', 0)}[/red]")
        lines.append(f"  Tasks Generated: {stats.get('tasks_generated', 0)}")
        lines.append("")

        elapsed = stats.get("elapsed_seconds", 0)
        lines.append(f"  Elapsed: {elapsed:.1f}s")
        lines.append(f"  Rate: {stats.get('tasks_per_second', 0):.2f} tasks/s")
        lines.append("")

        lines.append("[bold]Cache Performance[/bold]")
        cache = stats.get("cache_stats", {})
        lines.append(f"  Hits: {cache.get('hits', 0)}")
        lines.append(f"  Misses: {cache.get('misses', 0)}")
        lines.append(f"  Hit Rate: {cache.get('hit_rate', 0):.1%}")
        lines.append(f"  Tokens Saved: {cache.get('tokens_saved', 0)}")

        content.update("\n".join(lines))


class TaskBrowser(Static):
    """Widget to browse generated tasks."""

    tasks: reactive[list[dict[str, Any]]] = reactive([])

    def compose(self) -> ComposeResult:
        yield DataTable(id="task-table")

    def on_mount(self) -> None:
        table = self.query_one("#task-table", DataTable)
        table.add_column("ID", width=30)
        table.add_column("Name", width=40)
        table.add_column("Tags", width=30)
        table.add_column("Confidence", width=12)
        table.cursor_type = "row"

    def watch_tasks(self, tasks: list[dict[str, Any]]) -> None:
        """Update table when tasks change."""
        table = self.query_one("#task-table", DataTable)
        table.clear()

        for task in tasks[-100:]:  # Show last 100 tasks
            task_id = task.get("id", "unknown")[:28]
            name = task.get("name", "Unknown")[:38]
            tags = ", ".join(task.get("tags", [])[:3])[:28]
            confidence = task.get("confidence", 0.0)

            table.add_row(
                task_id,
                name,
                tags,
                f"{confidence:.2f}",
                key=task.get("id", ""),
            )

    @on(DataTable.RowSelected)
    def show_task_detail(self, event: DataTable.RowSelected) -> None:
        """Show task detail modal on row selection."""
        if event.row_key:
            # Find the task
            for task in self.tasks:
                if task.get("id") == event.row_key.value:
                    self.app.push_screen(TaskDetailModal(task))
                    break


class DiversityPanel(Static):
    """Panel showing diversity metrics."""

    metrics: reactive[dict[str, Any]] = reactive({})

    def compose(self) -> ComposeResult:
        yield Static(id="diversity-content")

    def watch_metrics(self, metrics: dict[str, Any]) -> None:
        """Update display when metrics change."""
        content = self.query_one("#diversity-content", Static)

        if not metrics:
            content.update("[dim]Diversity analysis not yet run[/dim]")
            return

        lines = []
        lines.append("[bold]Diversity Metrics[/bold]")
        lines.append(f"  Silhouette Score: {metrics.get('silhouette_score', 0):.3f}")
        lines.append(f"  Calinski-Harabasz: {metrics.get('calinski_harabasz', 0):.1f}")
        lines.append(f"  Davies-Bouldin: {metrics.get('davies_bouldin', 0):.3f}")
        lines.append(f"  Coverage Score: {metrics.get('coverage_score', 0):.3f}")
        lines.append("")

        cluster_labels = metrics.get("cluster_labels", {})
        if cluster_labels:
            lines.append("[bold]Top Clusters:[/bold]")
            sizes = metrics.get("cluster_sizes", {})
            sorted_clusters = sorted(
                cluster_labels.items(),
                key=lambda x: sizes.get(x[0], 0),
                reverse=True,
            )[:10]

            for cluster_id, label in sorted_clusters:
                size = sizes.get(cluster_id, 0)
                lines.append(f"  [{cluster_id}] {label} ({size} tasks)")

        content.update("\n".join(lines))


class DomainCoverage(Static):
    """Widget showing domain coverage."""

    coverage: reactive[dict[str, int]] = reactive({})

    def compose(self) -> ComposeResult:
        yield Static(id="coverage-content")

    def watch_coverage(self, coverage: dict[str, int]) -> None:
        """Update display when coverage changes."""
        content = self.query_one("#coverage-content", Static)

        if not coverage:
            content.update("[dim]No domain coverage data[/dim]")
            return

        total = sum(coverage.values())
        lines = ["[bold]Domain Coverage[/bold]", ""]

        for domain, count in sorted(coverage.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total > 0 else 0
            bar_width = int(pct / 5)
            bar = "█" * bar_width + "░" * (20 - bar_width)
            lines.append(f"  {domain:15} [{bar}] {pct:5.1f}% ({count})")

        content.update("\n".join(lines))


class LogPanel(Static):
    """Panel for live logs."""

    def compose(self) -> ComposeResult:
        yield Log(id="log-viewer", auto_scroll=True, max_lines=1000)

    def write(self, message: str) -> None:
        """Write a message to the log."""
        log = self.query_one("#log-viewer", Log)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write_line(f"[{timestamp}] {message}")


class PraxisTUI(App):
    """Main PRAXIS monitoring TUI application."""

    CSS = """
    Screen {
        background: $background;
    }

    #main-container {
        height: 100%;
    }

    #stats-panel {
        width: 30%;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    #content-panel {
        width: 70%;
        height: 100%;
    }

    .panel-title {
        text-style: bold;
        color: $text;
        background: $primary;
        padding: 0 1;
    }

    ProgressBar {
        margin: 1 0;
    }

    #progress-container {
        height: 3;
        padding: 0 1;
    }

    DataTable {
        height: 100%;
    }

    TabPane {
        padding: 1;
    }

    #diversity-content, #coverage-content, #stats-content {
        padding: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("d", "toggle_dark", "Toggle Dark Mode"),
        Binding("a", "analyze", "Run Analysis"),
        Binding("g", "generate", "Start Generation"),
        Binding("s", "stop", "Stop"),
    ]

    # Reactive state
    is_running: reactive[bool] = reactive(False)
    progress: reactive[float] = reactive(0.0)

    def __init__(
        self,
        output_dir: Path | None = None,
        checkpoint_dir: Path | None = None,
    ) -> None:
        super().__init__()
        config = get_config()
        self.output_dir = output_dir or config.output_dir
        self.checkpoint_dir = checkpoint_dir or config.checkpoint_dir

        self._stats: dict[str, Any] = {}
        self._tasks: list[dict[str, Any]] = []
        self._diversity_metrics: dict[str, Any] = {}
        self._domain_coverage: dict[str, int] = {}
        self._refresh_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main-container"):
            with Vertical(id="stats-panel"):
                yield Static("Statistics", classes="panel-title")
                yield StatsPanel(id="stats")
                yield Rule()
                yield Static("Progress", classes="panel-title")
                with Container(id="progress-container"):
                    yield ProgressBar(id="progress-bar", total=100)
                yield Rule()
                yield DomainCoverage(id="domain-coverage")

            with Vertical(id="content-panel"):
                with TabbedContent():
                    with TabPane("Tasks", id="tasks-tab"):
                        yield TaskBrowser(id="task-browser")
                    with TabPane("Diversity", id="diversity-tab"):
                        yield DiversityPanel(id="diversity-panel")
                    with TabPane("Logs", id="logs-tab"):
                        yield LogPanel(id="log-panel")

        yield Footer()

    async def on_mount(self) -> None:
        """Start periodic refresh."""
        self._refresh_task = asyncio.create_task(self._periodic_refresh())
        self.log_message("PRAXIS Monitor started")
        await self._load_initial_data()

    async def _periodic_refresh(self) -> None:
        """Periodically refresh data."""
        while True:
            await asyncio.sleep(2.0)
            await self._refresh_data()

    async def _load_initial_data(self) -> None:
        """Load initial data on startup."""
        await self._refresh_data()

    async def _refresh_data(self) -> None:
        """Refresh all data from files."""
        # Load tasks from output directory
        await self._load_tasks()

        # Update stats
        await self._update_stats()

        # Update domain coverage
        await self._update_domain_coverage()

    async def _load_tasks(self) -> None:
        """Load tasks from output files."""
        if not self.output_dir.exists():
            return

        tasks = []
        task_files = sorted(self.output_dir.glob("tasks_*.jsonl"))

        for task_file in task_files[-5:]:  # Load last 5 files
            try:
                with open(task_file, "rb") as f:
                    for line in f:
                        tasks.append(orjson.loads(line))
            except Exception:
                pass

        self._tasks = tasks[-500:]  # Keep last 500 tasks in memory

        browser = self.query_one("#task-browser", TaskBrowser)
        browser.tasks = self._tasks

    async def _update_stats(self) -> None:
        """Update statistics."""
        stats = {
            "total_jobs": 0,
            "completed_jobs": len(self._tasks),
            "failed_jobs": 0,
            "tasks_generated": len(self._tasks),
            "elapsed_seconds": 0,
            "tasks_per_second": 0,
            "cache_stats": {},
        }

        # Try to load cache stats
        try:
            cache = LLMCache()
            stats["cache_stats"] = cache.get_stats()
            cache.close()
        except Exception:
            pass

        # Try to load checkpoint stats
        sessions = CheckpointManager.list_sessions(self.checkpoint_dir)
        if sessions:
            latest = sessions[0]
            stats["total_jobs"] = latest.get("total_jobs", 0)
            stats["completed_jobs"] = latest.get("completed_jobs", 0)

        self._stats = stats

        stats_panel = self.query_one("#stats", StatsPanel)
        stats_panel.stats = stats

        # Update progress bar
        if stats["total_jobs"] > 0:
            self.progress = (stats["completed_jobs"] / stats["total_jobs"]) * 100
            progress_bar = self.query_one("#progress-bar", ProgressBar)
            progress_bar.update(progress=self.progress)

    async def _update_domain_coverage(self) -> None:
        """Update domain coverage from task personas."""
        coverage: dict[str, int] = {}

        for task in self._tasks:
            provenance = task.get("provenance", {})
            domain = provenance.get("persona_domain", "unknown")
            coverage[domain] = coverage.get(domain, 0) + 1

        self._domain_coverage = coverage

        domain_widget = self.query_one("#domain-coverage", DomainCoverage)
        domain_widget.coverage = coverage

    def log_message(self, message: str) -> None:
        """Log a message to the log panel."""
        try:
            log_panel = self.query_one("#log-panel", LogPanel)
            log_panel.write(message)
        except Exception:
            pass

    def action_refresh(self) -> None:
        """Manual refresh action."""
        asyncio.create_task(self._refresh_data())
        self.log_message("Refreshed data")

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark

    async def action_analyze(self) -> None:
        """Run diversity analysis."""
        self.log_message("Running diversity analysis...")

        try:
            from praxis.diversity import DiversityAnalyzer

            analyzer = DiversityAnalyzer()

            if len(self._tasks) < 10:
                self.log_message("Not enough tasks for analysis (need at least 10)")
                return

            # Run analysis in background
            def run_analysis():
                embeddings = analyzer.compute_embeddings(self._tasks)
                _, metrics = analyzer.cluster(embeddings, n_clusters=min(20, len(self._tasks) // 5))
                return metrics

            loop = asyncio.get_event_loop()
            metrics = await loop.run_in_executor(None, run_analysis)

            self._diversity_metrics = metrics

            diversity_panel = self.query_one("#diversity-panel", DiversityPanel)
            diversity_panel.metrics = metrics

            self.log_message(f"Analysis complete. Silhouette: {metrics.get('silhouette_score', 0):.3f}")

        except Exception as e:
            self.log_message(f"Analysis failed: {e}")

    def action_generate(self) -> None:
        """Start generation (placeholder)."""
        self.log_message("Generation should be started from CLI: praxis generate")

    def action_stop(self) -> None:
        """Stop generation (placeholder)."""
        self.log_message("Use Ctrl+C in the generation terminal to stop")


def run_tui(
    output_dir: Path | None = None,
    checkpoint_dir: Path | None = None,
) -> None:
    """Run the PRAXIS TUI."""
    app = PraxisTUI(output_dir=output_dir, checkpoint_dir=checkpoint_dir)
    app.run()


if __name__ == "__main__":
    run_tui()
