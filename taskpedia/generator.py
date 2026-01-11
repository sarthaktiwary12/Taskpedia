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
import re
import time
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

from taskpedia.hierarchy import NodeType, SeedSource, TaskGraph, TaskNode
from taskpedia.llm import LLMClient, LLMConfig, MockLLMClient
from taskpedia.verbs import ATOMIC_VERBS, get_action_categories_summary
from taskpedia.validation import is_generic_template, is_valid_atomic, GENERIC_NOUNS, GENERIC_VERBS


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

    Note: max_tasks refers to TARGET number of top-level tasks (NodeType.TASK).
    The system auto-counts existing tasks and generates more to reach the target.
    """

    output_dir: Path
    model: str = "models/gemini-2.5-flash"
    max_tasks: int = 100000  # Target top-level TASK count
    max_workers: int = 128
    queue_size: int = 1000
    rpm_limit: int = 1000
    mock: bool = False
    save_interval: int = 200
    tui: bool = True
    validate: bool = True  # Enable validation


class GeneratorCore:
    """Core generation logic - thread-safe."""

    def __init__(self, config: FastGenConfig):
        self.config = config
        self.graph = TaskGraph(config.output_dir)

        # Count existing top-level tasks
        self.initial_task_count = sum(
            1 for n in self.graph.iter_nodes() if n.node_type == NodeType.TASK
        )
        self.tasks_to_generate = max(0, config.max_tasks - self.initial_task_count)

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

        # Status message
        self.status = "Initializing..."
        self._status_lock = threading.Lock()

        # Control
        self._shutdown = threading.Event()
        self._start_time = time.time()
        self._done = False

        self._load_processed()

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
        """Decompose a single node. Thread-safe."""
        self.api_calls.increment()
        self.in_flight.increment()

        try:
            prompt = make_prompt(node)
            response = self._client.generate(prompt, SYSTEM_PROMPT, use_thinking=False)

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
            return {"node_id": node.id, "node": node, "success": True, **result}

        except json.JSONDecodeError as e:
            self.errors.increment()
            return {
                "node_id": node.id,
                "node": node,
                "success": False,
                "error": f"JSON: {str(e)[:50]}",
            }
        except Exception as e:
            self.errors.increment()
            return {"node_id": node.id, "node": node, "success": False, "error": str(e)[:100]}
        finally:
            self.in_flight.increment(-1)

    def _process_result(self, result: dict) -> int:
        """Process a decomposition result with validation."""
        if not result.get("success"):
            return 0

        node_id = result["node_id"]
        node = result["node"]
        is_atomic = result.get("is_atomic", False)
        subtasks = result.get("subtasks", [])

        self.mark_processed(node_id)

        if is_atomic or not subtasks:
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
                    pass  # Duplicate

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
        """Stop when we've generated enough top-level tasks or shutdown requested."""
        current_tasks = self.initial_task_count + self.tasks_generated.value
        return self._shutdown.is_set() or current_tasks >= self.config.max_tasks

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
    print(f"  Validate:     {config.validate}")
    print(f"  Total nodes:  {initial_count:,}")
    print(f"  Top-level:    {core.initial_task_count:,} / {config.max_tasks:,} tasks")
    print(f"  To generate:  {core.tasks_to_generate:,} more tasks")
    print(f"{'='*60}\n")

    pbar = tqdm(total=core.tasks_to_generate, desc="Tasks", unit="tasks")
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

                    # Update progress bar to show tasks generated
                    pbar.n = core.tasks_generated.value
                    pbar.refresh()

                    pbar.set_postfix(
                        {
                            "rpm": f"{core.get_rpm():.0f}",
                            "nodes": core.generated.value,
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
    """Run generation with Textual TUI."""
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, Static, ProgressBar, Label
    from textual.containers import Container

    # Create core outside the app
    core = GeneratorCore(config)
    initial_count = len(list(core.graph.iter_nodes()))
    result_holder = {"result": {}}

    class GeneratorApp(App):
        """Textual app for monitoring generation."""

        CSS = """
        Screen {
            layout: vertical;
        }

        #title {
            text-align: center;
            text-style: bold;
            background: $primary;
            color: $text;
            padding: 1;
        }

        #progress-section {
            height: 4;
            padding: 0 2;
        }

        #flow-section {
            height: 6;
            padding: 1 2;
            border: solid $primary;
            margin: 1;
        }

        #stats-section {
            height: 14;
            padding: 1 2;
            border: solid $secondary;
            margin: 1;
        }

        #status {
            text-align: center;
            background: $surface;
            padding: 1;
        }

        .flow-line {
            height: 1;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("s", "save", "Save Now"),
        ]

        def __init__(self):
            super().__init__()
            self._executor: ThreadPoolExecutor | None = None
            self._worker_thread: threading.Thread | None = None
            self._running = True
            self._graceful_shutdown = False

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("TASK MINING (improved prompts + validation)", id="title")

            with Container(id="progress-section"):
                yield Label(
                    f"Tasks: {core.initial_task_count:,} / {config.max_tasks:,} (need +{core.tasks_to_generate:,})",
                    id="progress-label",
                )
                yield ProgressBar(total=core.tasks_to_generate, show_eta=True, id="progress-bar")

            with Container(id="flow-section"):
                yield Static("─── FLOW ───", id="flow-title")
                yield Static(
                    "Work Queue:   [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]    0",
                    id="work-bar",
                    classes="flow-line",
                )
                yield Static(
                    "In Flight:    [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]    0",
                    id="flight-bar",
                    classes="flow-line",
                )
                yield Static(
                    "Pending Save: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]    0",
                    id="pending-bar",
                    classes="flow-line",
                )

            with Container(id="stats-section"):
                yield Static(self._render_stats(), id="stats")

            yield Static("Starting...", id="status")
            yield Footer()

        def _make_bar(self, label: str, value: int, max_val: int) -> str:
            if max_val == 0:
                pct = 0
            else:
                pct = min(100, (value / max_val) * 100)
            width = 30
            filled = int(width * pct / 100)
            bar = "█" * filled + "░" * (width - filled)
            return f"{label:14}[{bar}] {value:>4}"

        def _render_stats(self) -> str:
            elapsed = core.get_elapsed()
            rpm = core.get_rpm()
            current_tasks = core.initial_task_count + core.tasks_generated.value
            task_rate = core.tasks_generated.value / elapsed if elapsed > 0 else 0

            # ETA based on task generation rate
            if task_rate > 0:
                remaining = core.tasks_to_generate - core.tasks_generated.value
                eta_sec = remaining / task_rate
                if eta_sec > 3600:
                    eta = f"{eta_sec/3600:.1f}h"
                elif eta_sec > 60:
                    eta = f"{eta_sec/60:.0f}m"
                else:
                    eta = f"{eta_sec:.0f}s"
            else:
                eta = "..."

            return f"""─── STATISTICS ───
  Tasks:      {current_tasks:>10,} / {config.max_tasks:,}
  +Generated: {core.tasks_generated.value:>10,}     ETA: {eta}
  All Nodes:  {core.generated.value:>10,}
  Atomic:     {core.atomic_found.value:>10,}
  Decomposed: {core.decomposed.value:>10,}
  Rejected:   {core.rejected.value:>10,}     (validation)
  Errors:     {core.errors.value:>10,}
  ─────────────────
  RPM:        {rpm:>10.0f}
  Elapsed:    {elapsed:>10.0f}s"""

        def on_mount(self) -> None:
            # Start worker thread (NOT daemon - we need graceful shutdown)
            self._worker_thread = threading.Thread(target=self._run_generation, daemon=False)
            self._worker_thread.start()

            # Update UI periodically
            self.set_interval(0.2, self._update_ui)

            # Register signal handlers for graceful shutdown
            import signal
            import atexit

            def graceful_exit(*args):
                if not self._graceful_shutdown:
                    self._graceful_shutdown = True
                    self._running = False
                    core.stop()
                    core.save_pending()

            atexit.register(graceful_exit)
            # Note: signal handlers may not work in all contexts with Textual

        def _update_ui(self) -> None:
            # Progress - track top-level tasks
            current_tasks = core.initial_task_count + core.tasks_generated.value
            self.query_one("#progress-bar", ProgressBar).update(progress=core.tasks_generated.value)
            self.query_one("#progress-label", Label).update(
                f"Tasks: {current_tasks:,} / {config.max_tasks:,} (+{core.tasks_generated.value:,} this session)"
            )

            # Flow bars
            self.query_one("#work-bar", Static).update(
                self._make_bar("Work Queue:", core.work_queued.value, config.queue_size)
            )
            self.query_one("#flight-bar", Static).update(
                self._make_bar("In Flight:", core.in_flight.value, config.max_workers)
            )
            self.query_one("#pending-bar", Static).update(
                self._make_bar("Pending Save:", core.get_pending_count(), config.save_interval)
            )

            # Stats
            self.query_one("#stats", Static).update(self._render_stats())

            # Status
            self.query_one("#status", Static).update(core.get_status())

        def _run_generation(self) -> None:
            """Run generation in background thread."""
            save_counter = 0
            batch_size = min(config.queue_size, 500)  # Use config, cap at 500 for responsiveness

            try:
                with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
                    while self._running and not core.should_stop():
                        nodes = core.iter_decomposable(limit=batch_size)
                        core.work_queued.set(len(nodes))

                        if not nodes:
                            core.save_pending()
                            save_counter = 0
                            core._rebuild_queue()  # Rebuild queue from graph
                            nodes = core.iter_decomposable(limit=batch_size)
                            core.work_queued.set(len(nodes))
                            if not nodes:
                                core.set_status("Hierarchy fully mined! Press Q to exit.")
                                core._done = True
                                break

                        core.set_status(f"Processing {len(nodes)} nodes...")

                        futures = [executor.submit(core._decompose_node, n) for n in nodes]

                        for future in as_completed(futures):
                            if not self._running:
                                break
                            try:
                                result = future.result(timeout=30)
                                core._process_result(result)
                                save_counter += 1
                            except Exception as e:
                                core.errors.increment()

                        if save_counter >= config.save_interval:
                            core.set_status("Saving...")
                            core.save_pending()
                            save_counter = 0

                # Final save
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
                    core.set_status(f"Reached {config.max_tasks:,} tasks! Press Q to exit.")

            except Exception as e:
                core.set_status(f"Error: {e}")

        def action_quit(self) -> None:
            if self._graceful_shutdown:
                return  # Already shutting down
            self._graceful_shutdown = True
            self._running = False
            core.stop()
            core.set_status("Saving and shutting down...")
            # Wait for worker thread to finish current batch (max 5 seconds)
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=5.0)
            core.save_pending()
            self.exit()

        def action_save(self) -> None:
            core.save_pending()
            core.set_status("Saved!")

    # Run the app
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
