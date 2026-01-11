"""
Fast generation pipeline for VLA/VLN training data.

Continuous flow architecture with Textual TUI for monitoring.
- ThreadPoolExecutor for concurrent API calls
- Improved prompts for true atomic actions
- Validation to reject generic/template outputs
- Coverage for VLN, perception, manipulation, social
"""

from __future__ import annotations

import json
import logging
import re
import time
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

# Setup logging - file only to avoid polluting TUI
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
_file_handler = logging.FileHandler("taskpedia_debug.log")
_file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
log.addHandler(_file_handler)
log.propagate = False  # Don't propagate to root logger

from taskpedia.hierarchy import NodeType, SeedSource, TaskGraph, TaskNode
from taskpedia.llm import LLMClient, LLMConfig, MockLLMClient
from taskpedia.verbs import ATOMIC_VERBS, get_action_categories_summary
from taskpedia.validation import is_generic_template, is_valid_atomic, GENERIC_NOUNS, GENERIC_VERBS
from taskpedia.utils import RateLimiter


def _is_rate_limit_error(exception: Exception) -> bool:
    """Check if exception is a transient rate limit error (not quota exhaustion)."""
    error_str = str(exception)
    # Don't retry on quota exhaustion (daily limit) - only on transient rate limits
    if "quota" in error_str.lower() and "per_day" in error_str.lower():
        return False  # Daily quota - don't retry
    return "429" in error_str or "RESOURCE_EXHAUSTED" in error_str


# ============================================================================
# SYSTEM PROMPT - Optimized for VLA/VLN/WBC Training
# ============================================================================

SYSTEM_PROMPT = """You are decomposing human tasks into training data for humanoid robots (VLA/VLN/Whole-Body Control).

## GOAL
Break tasks into ATOMIC ACTIONS that a robot can learn from demonstrations or execute via learned policies.

## WHAT MAKES A GOOD ATOMIC ACTION (for robot training)
1. **Observable**: Can be demonstrated and recorded (video/mocap)
2. **Executable**: Single motor primitive with clear start/end states
3. **Groundable**: References SPECIFIC objects/locations, not abstractions
4. **Repeatable**: Same action structure applies across contexts

## ATOMIC ACTION CATEGORIES

**Manipulation (arm/hand control):**
- grasp <specific_object> - close gripper/hand on object
- release <object> - open gripper, let go
- pick_up <object> from <surface/container>
- place <object> on/in <target_location>
- push/pull <object> <direction/distance>
- rotate/twist <object> <angle/direction>
- insert <object> into <receptacle>
- pour <substance> from <source> into <target>
- open/close <door/drawer/lid/container>
- press/push <button/switch/key>
- turn <knob/dial/handle> <direction>
- slide <object> <direction>
- flip/toss <object>
- catch <object>
- hold <object> while <other_action> (bimanual)
- stabilize <object> with <hand>

**Locomotion/Navigation (VLN - whole body):**
- walk_to <specific_location/object>
- approach <target> until <distance>
- navigate_around <obstacle>
- enter/exit <room/door/area>
- climb/descend <stairs/ladder/step>
- turn_to_face <direction/object>
- step <direction> <distance>
- crouch/stand/kneel
- lean <direction> to <reach/see>
- balance_on <surface>

**Active Perception (head/gaze/sensors):**
- look_at <target_object/location>
- scan <area> for <object_type>
- track <moving_object> visually
- read <text/display/label>
- inspect <object> for <property>
- listen_for <sound_type>
- feel/probe <surface> for <property>
- measure <dimension> of <object>

**Communication/Social (for HRI):**
- say "<utterance>"
- gesture <type> toward <target>
- point_at <object/direction>
- nod/shake_head
- make_eye_contact with <person>
- hand_over <object> to <person>
- receive <object> from <person>

## OUTPUT FORMAT
```json
{
    "is_atomic": boolean,
    "subtasks": [
        {
            "name": "<verb> <specific_object/location>",
            "description": "Physical execution: <how body moves>. Sensing: <what to perceive>. Success: <end state>.",
            "is_atomic": boolean,
            "category": "manipulation|locomotion|perception|communication"
        }
    ]
}
```

## RULES FOR VLA/VLN TRAINING UTILITY
1. **Specific objects**: "grasp the red mug" not "grasp object" - robots need grounded references
2. **Physical descriptions**: Include body parts, forces, directions - "extend right arm forward, close fingers around handle"
3. **Clear success criteria**: "until fingers contact surface" or "until object is 10cm above table"
4. **Sensing modalities**: Specify visual/tactile/proprioceptive feedback needed
5. **No abstractions**: Decompose cognitive tasks (decide, plan, think) into observable actions
6. **Reusable primitives**: "pick_up mug from table" is reusable; "do the mug thing" is not
7. **3-8 subtasks**: Enough granularity without over-fragmentation

## ANTI-PATTERNS (reject these)
- "Step 1: prepare materials" - generic, not trainable
- "check equipment" - what sensing? what equipment?
- "handle the situation" - not executable
- "process the items" - not physical"""


def make_prompt(node: TaskNode) -> str:
    """Create the decomposition prompt for VLA/VLN training."""
    context_parts = []
    if node.description:
        context_parts.append(f"Description: {node.description}")
    if node.parent_id:
        parent_parts = node.parent_id.split("/")
        if len(parent_parts) >= 2:
            context_parts.append(f"Domain: {parent_parts[0].replace('_', ' ')}")
        if len(parent_parts) >= 3:
            context_parts.append(f"Parent task: {parent_parts[-1].replace('_', ' ')}")

    context = "\n".join(context_parts) if context_parts else ""

    return f"""Decompose into atomic actions for humanoid robot training:

**Task:** {node.name}
{context}

For each subtask, specify:
- The PHYSICAL motion (which body parts, what trajectory)
- The SENSING required (visual, tactile, proprioceptive)
- The SUCCESS condition (how robot knows it's done)

Output JSON with specific, trainable actions."""


# ============================================================================
# CORE GENERATOR
# ============================================================================


class AtomicCounter:
    """Thread-safe counter."""

    def __init__(self, initial: int = 0):
        self._value = initial
        self._lock = threading.Lock()

    def increment(self, delta: int = 1) -> int:
        with self._lock:
            self._value += delta
            return self._value

    def set(self, value: int) -> None:
        with self._lock:
            self._value = value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value


@dataclass
class FastGenConfig:
    """Configuration for fast generation.

    Note: max_tasks refers to NEW nodes to generate this session.
    """

    output_dir: Path
    model: str = "models/gemini-2.5-flash"
    max_tasks: int = 100000  # New nodes to generate this session
    max_workers: int = 64  # Good for Tier 1 (1000+ RPM)
    queue_size: int = 500
    rpm_limit: int = 1000  # Tier 1 allows ~1500 RPM
    mock: bool = False
    save_interval: int = 200
    tui: bool = True
    validate: bool = True  # Enable validation


class GeneratorCore:
    """Core generation logic - thread-safe."""

    def __init__(self, config: FastGenConfig):
        self.config = config
        self.graph = TaskGraph(config.output_dir)

        # Count existing nodes
        all_nodes = list(self.graph.iter_nodes())
        self.initial_node_count = len(all_nodes)
        self.initial_task_count = sum(1 for n in all_nodes if n.node_type == NodeType.TASK)
        self.nodes_to_generate = max(0, config.max_tasks - self.initial_node_count)

        # Stats
        self.generated = AtomicCounter(0)  # All nodes generated this session
        self.tasks_generated = AtomicCounter(0)  # Top-level TASKs generated this session
        self.decomposed = AtomicCounter(0)
        self.atomic_found = AtomicCounter(0)
        self.errors = AtomicCounter(0)
        self.api_calls = AtomicCounter(0)
        self.in_flight = AtomicCounter(0)
        self.work_queued = AtomicCounter(0)
        self.rejected = AtomicCounter(0)  # Validation rejections

        # Track processed
        self._processed_ids: set[str] = set()
        self._processed_lock = threading.Lock()

        # Pending nodes to save
        self._pending_nodes: list[TaskNode] = []
        self._pending_lock = threading.Lock()

        # Additional counters for debugging
        self.duplicates = AtomicCounter(0)
        self.empty_responses = AtomicCounter(0)

        # Status message
        self.status = "Initializing..."
        self._status_lock = threading.Lock()

        # Recent errors for debugging
        self._recent_errors: list[str] = []
        self._errors_lock = threading.Lock()

        # Control
        self._shutdown = threading.Event()
        self._start_time = time.time()
        self._done = False

        self._load_processed()

        # Rate limiter
        self._rate_limiter = RateLimiter(rpm=config.rpm_limit)

        # LLM client
        llm_config = LLMConfig(model=config.model, thinking_budget=0)
        if config.mock:
            self._client = MockLLMClient(config=llm_config, delay=0.05)
        else:
            self._client = LLMClient(config=llm_config)

        # Pre-build decomposable queue (avoid O(N) scans)
        self._decomposable_queue: list[TaskNode] = []
        self._queue_lock = threading.Lock()
        self._rebuild_queue()

        self.set_status("Ready")

    def _rebuild_queue(self):
        """Rebuild the decomposable node queue. Called once at start and when queue empties."""
        with self._queue_lock:
            self._decomposable_queue = []
            for node in self.graph._nodes.values():
                if node.id in self._processed_ids:
                    continue
                if node.children_ids:
                    continue
                if node.node_type == NodeType.DOMAIN:
                    continue
                if node.node_type == NodeType.ATOMIC:
                    continue
                self._decomposable_queue.append(node)
            self.set_status(f"Queue rebuilt: {len(self._decomposable_queue):,} nodes")

    def set_status(self, msg: str):
        with self._status_lock:
            self.status = msg

    def get_status(self) -> str:
        with self._status_lock:
            return self.status

    def get_recent_errors(self) -> list[str]:
        with self._errors_lock:
            return list(self._recent_errors)

    def _load_processed(self):
        count = 0
        for node in self.graph.iter_nodes():
            if node.children_ids:
                self._processed_ids.add(node.id)
                count += 1
        self.set_status(f"Loaded {count:,} processed nodes")

    def get_rpm(self) -> float:
        elapsed = time.time() - self._start_time
        if elapsed < 1:
            return 0
        return (self.api_calls.value / elapsed) * 60

    def get_elapsed(self) -> float:
        return time.time() - self._start_time

    def is_processed(self, node_id: str) -> bool:
        with self._processed_lock:
            return node_id in self._processed_ids

    def mark_processed(self, node_id: str):
        with self._processed_lock:
            self._processed_ids.add(node_id)

    def get_pending_count(self) -> int:
        with self._pending_lock:
            return len(self._pending_nodes)

    def _decompose_node(self, node: TaskNode) -> dict:
        """Decompose a single node. Thread-safe with tenacity retry."""
        self.in_flight.increment()
        try:
            return self._call_llm_with_retry(node)
        finally:
            self.in_flight.increment(-1)

    @retry(
        retry=retry_if_exception(_is_rate_limit_error),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _call_llm_with_retry(self, node: TaskNode) -> dict:
        """Call LLM with tenacity retry on rate limits."""
        self._rate_limiter.acquire()
        self.api_calls.increment()

        try:
            prompt = make_prompt(node)
            log.debug(f"Calling LLM for node: {node.id[:50]}...")
            response = self._client.generate(prompt, SYSTEM_PROMPT, use_thinking=False)
            log.debug(f"LLM response length: {len(response)} chars")

            # Parse JSON
            json_text = response.strip()
            if "```" in json_text:
                parts = json_text.split("```")
                for part in parts:
                    if part.strip().startswith("json"):
                        json_text = part.strip()[4:]
                        break
                    elif part.strip().startswith("{"):
                        json_text = part.strip()
                        break

            result = json.loads(json_text.strip())
            log.debug(
                f"Parsed result: is_atomic={result.get('is_atomic')}, subtasks={len(result.get('subtasks', []))}"
            )
            return {"node_id": node.id, "node": node, "success": True, **result}

        except json.JSONDecodeError as e:
            log.error(f"JSON decode error: {e}")
            log.error(f"Raw response: {response[:500] if response else 'None'}")
            self.errors.increment()
            error_msg = f"JSON: {str(e)[:50]}"
            self._record_error(error_msg)
            return {"node_id": node.id, "node": node, "success": False, "error": error_msg}
        except Exception as e:
            log.error(f"Exception in LLM call: {type(e).__name__}: {e}")
            if _is_rate_limit_error(e):
                raise  # Let tenacity retry
            self.errors.increment()
            error_msg = f"{type(e).__name__}: {str(e)[:80]}"
            self._record_error(error_msg)
            return {"node_id": node.id, "node": node, "success": False, "error": error_msg}

    def _record_error(self, error_msg: str) -> None:
        """Record an error message for display."""
        with self._errors_lock:
            self._recent_errors.append(error_msg)
            if len(self._recent_errors) > 10:
                self._recent_errors.pop(0)

    def _process_result(self, result: dict) -> int:
        """Process a decomposition result with validation."""
        if not result.get("success"):
            log.debug(f"Skipping failed result: {result.get('error', 'unknown')}")
            return 0

        node_id = result["node_id"]
        node = result["node"]
        is_atomic = result.get("is_atomic", False)
        subtasks = result.get("subtasks", [])

        log.debug(
            f"Processing result for {node_id[:40]}: is_atomic={is_atomic}, subtasks={len(subtasks)}"
        )
        self.mark_processed(node_id)

        if is_atomic or not subtasks:
            self.empty_responses.increment()
            log.debug(f"Node {node_id[:40]} is atomic or has no subtasks")
            # Validate atomic
            if self.config.validate and not is_valid_atomic(node.name):
                # Don't mark as atomic if it doesn't look like one
                # Just skip - it will be reprocessed or stay as subtask
                self.rejected.increment()
                return 0

            node.node_type = NodeType.ATOMIC
            with self._pending_lock:
                self._pending_nodes.append(node)
            self.atomic_found.increment()
            return 0

        count = 0

        with self._pending_lock:
            for subtask in subtasks:
                name = subtask.get("name", str(subtask))
                if not name:
                    continue

                description = subtask.get("description", "")

                # Validate: reject generic templates
                if self.config.validate and is_generic_template(name, description):
                    self.rejected.increment()
                    continue

                # Determine child type based on parent
                if node.node_type == NodeType.DOMAIN:
                    # Children of domains are TASKs
                    child_type = NodeType.TASK
                elif subtask.get("is_atomic"):
                    child_type = NodeType.ATOMIC
                else:
                    child_type = NodeType.SUBTASK

                # Extra validation for atomic claims
                if child_type == NodeType.ATOMIC and self.config.validate:
                    if not is_valid_atomic(name):
                        child_type = NodeType.SUBTASK  # Downgrade to subtask

                child = TaskNode(
                    id=TaskNode.make_id(name, node.id),
                    name=name,
                    node_type=child_type,
                    parent_id=node.id,
                    description=description,
                    sources=[SeedSource.LLM_GENERATED],
                )

                # Add category as tag if provided
                category = subtask.get("category", "")
                if category:
                    child.tags = [category]

                try:
                    self.graph.add_node(child, save=False)
                    self._pending_nodes.append(child)
                    count += 1
                    if child_type == NodeType.TASK:
                        self.tasks_generated.increment()
                    elif child_type == NodeType.ATOMIC:
                        self.atomic_found.increment()
                    else:
                        # Add subtasks to decomposable queue for further processing
                        with self._queue_lock:
                            self._decomposable_queue.append(child)
                except ValueError:
                    self.duplicates.increment()  # Track duplicates

        self.decomposed.increment()
        self.generated.increment(count)
        return count

    def save_pending(self):
        """Save all pending nodes to disk."""
        with self._pending_lock:
            if not self._pending_nodes:
                return
            for node in self._pending_nodes:
                self.graph._save_node(node)
            self._pending_nodes.clear()
        self.graph._save_manifest()

    def iter_decomposable(self, limit: int = 500):
        """Yield nodes that need decomposition. Uses pre-built queue for O(1) access."""
        with self._queue_lock:
            # Pop from queue (fast)
            result = []
            while self._decomposable_queue and len(result) < limit:
                node = self._decomposable_queue.pop()
                if node.id in self._processed_ids:
                    continue
                if node.children_ids:
                    continue
                result.append(node)
            return result

    def should_stop(self) -> bool:
        """Stop when we've generated enough new nodes this session or shutdown requested."""
        # max_tasks is the number of NEW nodes to generate this session
        return self._shutdown.is_set() or self.generated.value >= self.config.max_tasks

    def stop(self):
        self._shutdown.set()


# ============================================================================
# RUNNERS
# ============================================================================


def run_without_tui(config: FastGenConfig) -> dict:
    """Run generation without TUI - simple progress output."""
    from tqdm import tqdm

    core = GeneratorCore(config)
    initial_count = len(list(core.graph.iter_nodes()))

    print(f"\n{'='*60}")
    print(f"  Task Mining (improved prompts + validation)")
    print(f"{'='*60}")
    print(f"  Output:       {config.output_dir}")
    print(f"  Workers:      {config.max_workers}")
    print(f"  RPM limit:    {config.rpm_limit}")
    print(f"  Validate:     {config.validate}")
    print(f"  Existing:     {initial_count:,} nodes")
    print(f"  To generate:  {config.max_tasks:,} new nodes")
    print(f"{'='*60}\n")

    pbar = tqdm(total=config.max_tasks, desc="Nodes", unit="nodes")
    save_counter = 0

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        while not core.should_stop():
            nodes = core.iter_decomposable(limit=config.queue_size)

            if not nodes:
                core.save_pending()
                core._rebuild_queue()  # Rebuild queue from graph
                nodes = core.iter_decomposable(limit=config.queue_size)
                if not nodes:
                    print("\n[INFO] No more nodes to decompose")
                    break

            futures = [executor.submit(core._decompose_node, n) for n in nodes]

            for future in as_completed(futures):
                if core.should_stop():
                    break
                try:
                    result = future.result(timeout=60)
                    count = core._process_result(result)
                    save_counter += count

                    # Update progress bar to show nodes generated
                    pbar.n = core.generated.value
                    pbar.refresh()

                    pbar.set_postfix(
                        {
                            "rpm": f"{core.get_rpm():.0f}",
                            "atomic": core.atomic_found.value,
                            "rej": core.rejected.value,
                        }
                    )
                except Exception:
                    core.errors.increment()

            if save_counter >= config.save_interval:
                core.save_pending()
                save_counter = 0

    pbar.close()
    core.save_pending()

    elapsed = core.get_elapsed()
    final_count = len(list(core.graph.iter_nodes()))

    final_tasks = core.initial_task_count + core.tasks_generated.value

    print(f"\n{'='*60}")
    print(f"  COMPLETE")
    print(f"{'='*60}")
    print(
        f"  Top-level tasks: {final_tasks:,} (was {core.initial_task_count:,}, +{core.tasks_generated.value:,})"
    )
    print(f"  All nodes:       {core.generated.value:,} generated")
    print(f"  Atomic:          {core.atomic_found.value:,}")
    print(f"  Rejected:  {core.rejected.value:,}")
    print(f"  Errors:    {core.errors.value}")
    print(f"  Time:      {elapsed:.0f}s")
    print(f"  Avg RPM:   {core.get_rpm():.0f}")
    print(f"  Nodes:     {final_count:,} (was {initial_count:,})")
    print(f"{'='*60}\n")

    return {
        "generated": core.generated.value,
        "atomic_found": core.atomic_found.value,
        "rejected": core.rejected.value,
        "errors": core.errors.value,
        "api_calls": core.api_calls.value,
    }


def run_with_tui(config: FastGenConfig) -> dict:
    """Run generation with Textual TUI - htop/neovim inspired design."""
    from collections import deque
    from textual.app import App, ComposeResult
    from textual.widgets import Static
    from textual.containers import Horizontal, Vertical
    from rich.text import Text

    # Try to import plotext, fall back to no graph
    try:
        from textual_plotext import PlotextPlot

        HAS_PLOTEXT = True
    except ImportError:
        HAS_PLOTEXT = False
        PlotextPlot = None

    # Create core outside the app
    core = GeneratorCore(config)
    initial_count = len(list(core.graph.iter_nodes()))
    result_holder = {"result": {}}

    # Track recent files for preview (thread-safe deque)
    recent_files: deque[tuple[str, str, str]] = deque(maxlen=100)  # (name, type, path)
    recent_lock = threading.Lock()

    # Time series for RPM graph
    rpm_history: deque[tuple[float, float]] = deque(maxlen=60)  # (elapsed, rpm)
    rpm_lock = threading.Lock()

    class GeneratorApp(App):
        """htop-inspired task mining TUI."""

        TITLE = "taskpedia"

        CSS = """
        Screen {
            background: #0d1117;
        }

        #header-bar {
            height: 1;
            background: #238636;
            color: #ffffff;
            text-align: center;
            text-style: bold;
        }

        #main-container {
            height: 1fr;
        }

        #left-panel {
            width: 1fr;
            min-width: 50;
        }

        #right-panel {
            width: 45;
            border-left: solid #30363d;
        }

        #progress-box {
            height: 5;
            padding: 0 1;
            border: solid #30363d;
            background: #161b22;
            margin: 0 1 0 1;
        }

        #meters-box {
            height: 6;
            padding: 0 1;
            border: solid #30363d;
            background: #161b22;
            margin: 0 1;
        }

        #graph-box {
            height: 10;
            border: solid #30363d;
            background: #161b22;
            margin: 0 1;
        }

        #stats-box {
            height: 1fr;
            padding: 0 1;
            border: solid #30363d;
            background: #161b22;
            margin: 0 1;
        }

        #files-header {
            height: 1;
            background: #21262d;
            color: #8b949e;
            padding: 0 1;
            text-style: bold;
        }

        #files-list {
            height: 1fr;
            padding: 0 1;
            background: #0d1117;
            overflow-y: auto;
        }

        PlotextPlot {
            background: #161b22;
        }

        #status-bar {
            height: 1;
            background: #21262d;
            color: #8b949e;
            padding: 0 1;
        }

        #keybinds {
            height: 1;
            background: #161b22;
            color: #58a6ff;
            padding: 0 1;
        }

        ProgressBar {
            padding: 0;
        }

        ProgressBar > .bar--bar {
            color: #238636;
        }

        ProgressBar > .bar--complete {
            color: #238636;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("s", "save", "Save"),
            ("c", "clear_files", "Clear"),
        ]

        def __init__(self):
            super().__init__()
            self._worker_thread: threading.Thread | None = None
            self._running = True
            self._graceful_shutdown = False

        def compose(self) -> ComposeResult:
            yield Static(
                f" TASKPEDIA  Task Mining Pipeline  {config.output_dir}",
                id="header-bar",
            )

            with Horizontal(id="main-container"):
                with Vertical(id="left-panel"):
                    yield Static(id="progress-box")
                    yield Static(id="meters-box")
                    if HAS_PLOTEXT:
                        yield PlotextPlot(id="graph-box")
                    yield Static(id="stats-box")

                with Vertical(id="right-panel"):
                    yield Static("  RECENT FILES", id="files-header")
                    yield Static("", id="files-list")

            yield Static("", id="status-bar")
            yield Static(
                "  Q:Quit  S:Save  C:Clear",
                id="keybinds",
            )

        def _format_time(self, seconds: float) -> str:
            """Format seconds to human readable."""
            if seconds < 60:
                return f"{seconds:.0f}s"
            elif seconds < 3600:
                return f"{seconds/60:.0f}m {seconds%60:.0f}s"
            else:
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                return f"{h}h {m}m"

        def _make_meter(self, label: str, value: int, max_val: int, color: str = "green") -> Text:
            """Create an htop-style meter bar with pipe chars."""
            if max_val == 0:
                pct = 0
            else:
                pct = min(100, (value / max_val) * 100)

            width = 25
            filled = int(width * pct / 100)
            empty = width - filled

            text = Text()
            text.append(f"{label:12}", style="bold white")
            text.append("[", style="dim white")
            text.append("|" * filled, style=color)
            text.append("-" * empty, style="dim #30363d")
            text.append("]", style="dim white")
            text.append(f" {value:>5}", style="white")
            return text

        def _render_progress(self) -> Text:
            """Render progress section."""
            generated = core.generated.value
            total_nodes = core.initial_node_count + generated
            pct = (generated / config.max_tasks * 100) if config.max_tasks > 0 else 0

            # Calculate ETA
            elapsed = core.get_elapsed()
            node_rate = generated / elapsed if elapsed > 0 else 0
            if node_rate > 0 and generated < config.max_tasks:
                remaining = config.max_tasks - generated
                eta_sec = remaining / node_rate
                eta = self._format_time(eta_sec)
            else:
                eta = "--:--"

            text = Text()
            text.append("\n")
            text.append(" Progress ", style="bold #58a6ff")
            text.append(f"{generated:,}", style="bold #238636")
            text.append(f" / {config.max_tasks:,}", style="dim white")
            text.append(f"  ({pct:.1f}%)", style="dim #8b949e")
            text.append(f"  ETA: {eta}", style="#f0883e")
            text.append("\n")
            text.append(f" Total nodes: {total_nodes:,}", style="dim #8b949e")
            text.append(f"  (started with {core.initial_node_count:,})", style="dim #6e7681")
            return text

        def _render_meters(self) -> Text:
            """Render meter bars."""
            text = Text()
            text.append("\n")
            text.append(
                self._make_meter("Queue", core.work_queued.value, config.queue_size, "#58a6ff")
            )
            text.append("\n")
            text.append(
                self._make_meter("Workers", core.in_flight.value, config.max_workers, "#f0883e")
            )
            text.append("\n")
            text.append(
                self._make_meter(
                    "Pending", core.get_pending_count(), config.save_interval, "#a371f7"
                )
            )
            text.append("\n")
            return text

        def _render_stats(self) -> Text:
            """Render statistics panel."""
            elapsed = core.get_elapsed()
            rpm = core.get_rpm()
            generated = core.generated.value
            rate = generated / elapsed if elapsed > 0 else 0

            text = Text()
            text.append("\n")
            text.append(" Statistics\n", style="bold #58a6ff")
            text.append("─" * 38, style="dim #30363d")
            text.append("\n")

            # Main stats
            stats = [
                ("Generated", f"{generated:,}", "#238636"),
                ("Atomic", f"{core.atomic_found.value:,}", "#a371f7"),
                ("Decomposed", f"{core.decomposed.value:,}", "#58a6ff"),
                ("Empty/Atomic", f"{core.empty_responses.value:,}", "#8b949e"),
                ("Duplicates", f"{core.duplicates.value:,}", "#f0883e"),
                ("Rejected", f"{core.rejected.value:,}", "#f85149"),
                ("Errors", f"{core.errors.value:,}", "#f85149" if core.errors.value > 0 else "dim"),
            ]

            for label, value, color in stats:
                text.append(f" {label:12}", style="dim white")
                text.append(f"{value:>12}\n", style=color)

            text.append("─" * 38, style="dim #30363d")
            text.append("\n")
            text.append(" Performance\n", style="bold #58a6ff")
            text.append(f" {'RPM':12}", style="dim white")
            text.append(f"{rpm:>12.0f}\n", style="#f0883e")
            text.append(f" {'Rate':12}", style="dim white")
            text.append(f"{rate:>9.1f}/s\n", style="#f0883e")
            text.append(f" {'Elapsed':12}", style="dim white")
            text.append(f"{self._format_time(elapsed):>12}\n", style="#8b949e")
            text.append(f" {'API Calls':12}", style="dim white")
            text.append(f"{core.api_calls.value:>12,}\n", style="#8b949e")

            # Show last error if any
            recent_errors = core.get_recent_errors()
            if recent_errors:
                text.append("─" * 38 + "\n", style="dim #30363d")
                text.append(" Last Error\n", style="bold #f85149")
                last_err = recent_errors[-1][:36]
                text.append(f" {last_err}\n", style="#f85149")

            return text

        def _render_files(self) -> Text:
            """Render recent files list."""
            text = Text()

            with recent_lock:
                files = list(recent_files)

            if not files:
                text.append("\n  Waiting for files...", style="dim #6e7681")
                return text

            # Show most recent at top
            for name, node_type, path in reversed(files):
                # Truncate long names
                display_name = name[:38] if len(name) > 38 else name

                # Color by type
                if node_type == "ATOMIC":
                    type_style = "#a371f7"
                    icon = ""
                elif node_type == "TASK":
                    type_style = "#238636"
                    icon = ""
                else:
                    type_style = "#58a6ff"
                    icon = ""

                text.append(f" {icon} ", style=type_style)
                text.append(f"{display_name}\n", style="white")

            return text

        def _update_graph(self) -> None:
            """Update the RPM graph."""
            if not HAS_PLOTEXT:
                return
            try:
                # Sample current RPM
                elapsed = core.get_elapsed()
                rpm = core.get_rpm()
                with rpm_lock:
                    rpm_history.append((elapsed, rpm))
                    data = list(rpm_history)

                if len(data) < 2:
                    return

                plot_widget = self.query_one("#graph-box", PlotextPlot)
                plt = plot_widget.plt

                times = [d[0] for d in data]
                rpms = [d[1] for d in data]

                plt.clear_figure()
                plt.theme("dark")
                plt.plot(times, rpms, marker="braille")
                plt.title("RPM")
                plt.xlabel("Time (s)")
                max_rpm = max(rpms) if rpms else 1000
                plt.ylim(0, max(max_rpm * 1.2, 100))

                plot_widget.refresh()
            except Exception:
                pass

        def on_mount(self) -> None:
            self._worker_thread = threading.Thread(target=self._run_generation, daemon=False)
            self._worker_thread.start()
            self.set_interval(0.2, self._update_ui)
            self.set_interval(1.0, self._update_graph)

        def _update_ui(self) -> None:
            try:
                self.query_one("#progress-box", Static).update(self._render_progress())
                self.query_one("#meters-box", Static).update(self._render_meters())
                self.query_one("#stats-box", Static).update(self._render_stats())
                self.query_one("#files-list", Static).update(self._render_files())
                self.query_one("#status-bar", Static).update(f" {core.get_status()}")
            except Exception:
                pass  # UI not ready yet

        def _run_generation(self) -> None:
            """Run generation in background thread."""
            save_counter = 0
            batch_size = min(config.queue_size, 500)

            try:
                with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
                    while self._running and not core.should_stop():
                        nodes = core.iter_decomposable(limit=batch_size)
                        core.work_queued.set(len(nodes))

                        if not nodes:
                            core.save_pending()
                            save_counter = 0
                            core._rebuild_queue()
                            nodes = core.iter_decomposable(limit=batch_size)
                            core.work_queued.set(len(nodes))
                            if not nodes:
                                core.set_status("Complete! Press Q to exit.")
                                core._done = True
                                break

                        core.set_status(f"Processing {len(nodes)} nodes...")
                        futures = [executor.submit(core._decompose_node, n) for n in nodes]

                        for future in as_completed(futures):
                            if not self._running:
                                break
                            try:
                                result = future.result(timeout=30)
                                log.debug(f"Future completed: success={result.get('success')}")
                                count = core._process_result(result)
                                log.debug(f"Processed result: count={count}")

                                # Track generated files for preview
                                if result.get("success") and count > 0:
                                    node = result.get("node")
                                    if node:
                                        with recent_lock:
                                            recent_files.append(
                                                (
                                                    node.name,
                                                    node.node_type.name,
                                                    str(node.id),
                                                )
                                            )

                                save_counter += 1
                            except Exception as e:
                                log.error(f"Future exception: {type(e).__name__}: {e}")
                                core.errors.increment()

                        if save_counter >= config.save_interval:
                            core.set_status("Saving...")
                            core.save_pending()
                            save_counter = 0

                core.save_pending()

                result_holder["result"] = {
                    "generated": core.generated.value,
                    "atomic_found": core.atomic_found.value,
                    "decomposed": core.decomposed.value,
                    "rejected": core.rejected.value,
                    "errors": core.errors.value,
                    "api_calls": core.api_calls.value,
                }

                if core.generated.value >= config.max_tasks:
                    core.set_status(f"Target reached! Press Q to exit.")

            except Exception as e:
                core.set_status(f"Error: {e}")

        def action_quit(self) -> None:
            if self._graceful_shutdown:
                return
            self._graceful_shutdown = True
            self._running = False
            core.stop()
            core.set_status("Shutting down...")
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=5.0)
            core.save_pending()
            self.exit()

        def action_save(self) -> None:
            core.save_pending()
            core.set_status("Saved!")

        def action_clear_files(self) -> None:
            with recent_lock:
                recent_files.clear()

    app = GeneratorApp()
    app.run()

    # Print final summary
    elapsed = core.get_elapsed()
    final_count = len(list(core.graph.iter_nodes()))

    print(f"\n{'='*60}")
    print(f"  COMPLETE")
    print(f"{'='*60}")
    print(f"  Generated: {core.generated.value:,}")
    print(f"  Atomic:    {core.atomic_found.value:,}")
    print(f"  Rejected:  {core.rejected.value:,}")
    print(f"  Errors:    {core.errors.value}")
    print(f"  Time:      {elapsed:.0f}s")
    print(f"  Avg RPM:   {core.get_rpm():.0f}")
    print(f"  Nodes:     {final_count:,} (was {initial_count:,})")
    print(f"{'='*60}\n")

    return result_holder["result"]


def run(config: FastGenConfig) -> dict:
    """Run generation with or without TUI."""
    import sys

    if config.tui and sys.stdout.isatty():
        try:
            return run_with_tui(config)
        except ImportError as e:
            print(f"[WARN] Textual not available ({e}), using simple mode")
            return run_without_tui(config)
    else:
        return run_without_tui(config)


# For backwards compatibility
class FastGenerator:
    def __init__(self, config: FastGenConfig):
        self.config = config

    def run(self) -> dict:
        return run(self.config)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fast VLA/VLN task mining")
    parser.add_argument("-o", "--output", default="./task_hierarchy", help="Output directory")
    parser.add_argument(
        "--max-tasks",
        "-n",
        type=int,
        default=100000,
        help="Target number of top-level tasks (auto-counts existing)",
    )
    parser.add_argument("--workers", type=int, default=128, help="Concurrent workers")
    parser.add_argument("--queue-size", type=int, default=1000, help="Work queue size")
    parser.add_argument("--rpm", type=int, default=1000, help="Rate limit (RPM)")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM")
    parser.add_argument("--no-tui", action="store_true", help="Disable TUI")
    parser.add_argument("--no-validate", action="store_true", help="Disable output validation")
    args = parser.parse_args()

    config = FastGenConfig(
        output_dir=Path(args.output),
        max_tasks=args.max_tasks,
        max_workers=args.workers,
        queue_size=args.queue_size,
        rpm_limit=args.rpm,
        mock=args.mock,
        tui=not args.no_tui,
        validate=not args.no_validate,
    )

    run(config)


if __name__ == "__main__":
    main()
