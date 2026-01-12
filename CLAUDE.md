# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project Overview

TASKPEDIA is a hierarchical task decomposition system for embodied AI. It decomposes human activities into atomic robot-executable actions (grasp, release, move_to, etc.) suitable for VLA/VLN training.

**Goal**: Generate millions of atomic task nodes from seed data using LLM decomposition.

## Generation Pipeline

```
Seeds (O*NET + Life)
    → Init (20K nodes)
    → ThreadPoolExecutor (128 workers)
    → Gemini 2.5 Flash (1000 RPM)
    → Atomic Actions
    → YAML files + HuggingFace
```

## Commands

```bash
# Setup
uv pip install -e .

# Initialize hierarchy from seeds
taskpedia init -o ./task_hierarchy

# Generate with live TUI
taskpedia generate -n 1000000

# Generate without TUI
taskpedia generate -n 1000000 --no-tui

# Mock mode (no API calls)
taskpedia generate -n 1000 --mock

# View hierarchy
taskpedia show stats
taskpedia show tree -d 4
taskpedia show search "grasp"

# Export
taskpedia export -f jsonl
taskpedia export -f json

# Upload to HuggingFace
taskpedia upload --repo Sentient-x/taskpedia --public

# Download from HuggingFace
taskpedia download --repo Sentient-x/taskpedia
taskpedia download --force    # Force re-download
taskpedia download -y         # Skip confirmation

# Quality Judge (analyze and improve)
taskpedia judge analyze       # Analyze rejection patterns
taskpedia judge improve       # Suggest prompt improvements
taskpedia judge improve --apply  # Generate improved prompt
taskpedia judge clear         # Clear reject log

# Cache management
taskpedia cache stats
taskpedia cache clear

# Quality Assurance
taskpedia qa test             # Run all QA tests
taskpedia qa analyze          # Analyze data quality
taskpedia qa clean            # Remove bad nodes
taskpedia qa verbs            # Analyze verb taxonomy
taskpedia qa coverage         # Check domain coverage

# Diversify (fill gaps in tree)
taskpedia diversify --max-tasks 1000
```

## Architecture

```
taskpedia/
├── cli.py            # CLI entry point (hierarchical subcommands)
├── hierarchy.py      # TaskNode, TaskGraph (filesystem DAG)
├── generator.py      # Continuous flow generator + Textual TUI
│
├── # === SHARED PRIMITIVES ===
├── patterns.py       # SINGLE SOURCE: robot patterns, generic templates
├── domains.py        # SINGLE SOURCE: domain coverage definitions
├── io.py             # File I/O helpers (YAML/JSON/JSONL)
├── concurrent.py     # Thread-safe primitives (AtomicCounter, AtomicBuffer)
├── llm_queue.py      # Reusable concurrent LLM request queue
├── utils.py          # RateLimiter, ProgressTracker
│
├── # === QUALITY CONTROL ===
├── judge.py          # Quality judge (regex + LLM) with reject logging
├── improve.py        # Self-improvement using reject log analysis
├── qa.py             # QA tests, domain coverage checks
│
├── # === CORE ===
├── verbs.py          # ATOMIC_VERBS (3,479), COGNITIVE_VERBS taxonomies
├── llm.py            # Gemini 2.5 Flash client
├── postprocess.py    # Data cleaning commands
├── decompose.py      # Bootstrap from seed data
└── seeds/
    ├── onet.py       # O*NET database loader
    └── taxonomy.py   # 35-domain taxonomy
```

### Key Files

| File | Purpose |
|------|---------|
| **Shared Primitives** | |
| `patterns.py` | SINGLE SOURCE for robot patterns, generic templates, cognitive verbs |
| `domains.py` | SINGLE SOURCE for domain coverage definitions |
| `io.py` | File I/O helpers: `load_yaml`, `save_json`, `parse_json_from_llm` |
| `concurrent.py` | Thread-safe: `AtomicCounter`, `AtomicBuffer`, `ThreadSafeStats`, `WorkQueue` |
| `llm_queue.py` | Reusable LLM queue - concurrent execution with rate limiting |
| **Quality Control** | |
| `judge.py` | Quality judge - regex + LLM validation with reject logging |
| `improve.py` | Self-improvement - analyzes rejects, suggests prompt improvements |
| `qa.py` | Test suites for verb taxonomy and domain coverage |
| **Core** | |
| `generator.py` | Main generator - ThreadPoolExecutor, Textual TUI, atomic saves |
| `verbs.py` | ATOMIC_VERBS (3,479 verbs), COGNITIVE_VERBS, category utilities |
| `hierarchy.py` | TaskNode dataclass, TaskGraph (filesystem-backed DAG) |
| `llm.py` | LLMClient for Gemini, MockLLMClient for testing |
| `utils.py` | RateLimiter (800 RPM default), ProgressTracker with tenacity |
| `cli.py` | CLI with subcommand groups |

### Data Model

```python
TaskNode(
    id="food_prep/cooking/boil_water",  # Hierarchical path
    name="boil water",
    node_type=NodeType.SUBTASK,  # DOMAIN | TASK | SUBTASK | ATOMIC
    parent_id="food_prep/cooking",
    children_ids=["food_prep/cooking/boil_water/fill_kettle", ...],
    sources=[SeedSource.LLM_GENERATED],
)
```

### Storage Format

```
task_hierarchy/
├── _manifest.json           # Node index
├── work_healthcare/
│   └── nursing/
│       └── administer_med/
│           └── _meta.yaml   # Task node
└── life_household/
    └── cooking/
        └── boil_water.yaml  # Atomic action
```

## Generator Design (generator.py)

**Continuous flow architecture**:
- `GeneratorCore`: Thread-safe core with atomic counters
- `ThreadPoolExecutor`: 128 workers for concurrent API calls
- `Textual TUI`: Live flow visualization (work queue, in-flight, pending)
- **Atomic saves**: Nodes buffered in memory, written to disk in batches
- **Quality judge**: Validates tasks with regex + optional LLM

**Key classes**:
- `FastGenConfig`: Configuration dataclass
- `GeneratorCore`: Generation logic (thread-safe)
- `GeneratorApp`: Textual app for TUI
- `AtomicCounter`: Thread-safe counter

## Judge System (judge.py)

**Two-stage quality validation**:
1. **Regex judge** (fast): Pattern matching for obvious failures
   - Robot internals (joint torques, motor commands, trajectories)
   - Generic templates ("check equipment", "prepare materials")
   - ~20 regex patterns covering common failure modes

2. **LLM judge** (optional, slower but accurate): Nuanced assessment
   - Used when `--llm-judge` flag is set
   - Catches edge cases that regex misses
   - Same client as generator (prompt caching)

**Reject logging**:
- All rejections logged to `taskpedia_rejects.jsonl`
- Includes: name, description, reason, pattern, parent context, timestamp
- Used for self-improvement analysis

**Key classes**:
- `RegexJudge`: Fast pattern-based validation
- `LLMJudge`: LLM-based nuanced validation
- `HybridJudge`: Combines both (regex first, then optional LLM)
- `RejectLog`: Thread-safe logging and analysis

## Self-Improvement (improve.py)

**Analyzes rejects to improve prompts**:
1. Reads reject log and identifies patterns
2. Groups by rejection reason
3. Finds most common failure patterns
4. Uses LLM to suggest prompt improvements
5. Optionally rewrites prompt with improvements

**Usage**:
```bash
# After running generation with rejects
taskpedia judge analyze               # See what's being rejected
taskpedia judge improve               # Get suggestions
taskpedia judge improve --apply       # Generate improved prompt
# Review improved_prompt.txt and manually update generator.py
```

## LLM Queue (llm_queue.py)

**Reusable concurrent LLM request primitives**:
- Generic queue for any LLM use case (generation, judging, analysis)
- ThreadPoolExecutor-based concurrent execution
- Built-in rate limiting (RPM)
- Automatic retries with exponential backoff
- Result batching and callbacks
- Thread-safe statistics tracking

**Can be used for**:
- Task generation
- LLM-as-judge validation
- Batch analysis
- Any concurrent LLM workflow

## Shared Primitives

### patterns.py - SINGLE SOURCE OF TRUTH

All regex patterns for task validation. **Never duplicate these elsewhere.**

```python
from taskpedia.patterns import (
    is_robot_internal,      # Check if task is robot-internal
    is_generic_template,    # Check for generic templates
    validate_task_name,     # Combined validation
    ROBOT_INTERNAL_PATTERNS,  # Raw patterns (if needed)
    GENERIC_VERBS,          # Generic verb set
    GENERIC_NOUNS,          # Generic noun set
)

# Usage
is_internal, pattern = is_robot_internal("joint_torque_control")
# -> (True, "joint.?torque")

is_generic = is_generic_template("check equipment", "Step 1: ...")
# -> True
```

### domains.py - Domain Coverage

Shared domain coverage definitions for QA testing.

```python
from taskpedia.domains import (
    DOMAIN_COVERAGE,        # All domain definitions
    check_domain_coverage,  # Run coverage check
    run_coverage_report,    # Generate report
)

# Usage
results = check_domain_coverage(actual_verbs)
print(run_coverage_report(actual_verbs))
```

### io.py - File I/O Helpers

Consistent file operations across the codebase.

```python
from taskpedia.io import (
    load_yaml, save_yaml,       # YAML operations
    load_json, save_json,       # JSON operations
    load_jsonl, append_jsonl,   # JSONL operations
    load_manifest, save_manifest,  # TaskGraph manifest
    parse_json_from_llm,        # Parse LLM JSON responses
)
```

### concurrent.py - Thread-Safe Primitives

Reusable thread-safe building blocks.

```python
from taskpedia.concurrent import (
    AtomicCounter,      # Thread-safe counter
    AtomicBuffer,       # Auto-flushing buffer
    ThreadSafeStats,    # Named counters + timings
    AtomicSet,          # Thread-safe set
    WorkQueue,          # Thread-safe queue with stats
)

# Usage
counter = AtomicCounter()
counter.increment()
print(counter.value)

buffer = AtomicBuffer(flush_fn=save_batch, threshold=100)
buffer.add(item)  # Auto-flushes at 100 items

stats = ThreadSafeStats()
stats.increment("processed")
stats.add_timing("api_call", 150.0)
print(stats.snapshot())
```

## Verb Taxonomy (verbs.py)

- **ATOMIC_VERBS**: 3,479 physical action verbs organized by domain
- **COGNITIVE_VERBS**: 81 mental/internal verbs (not directly observable)
- Categories: Manipulation, Tool Use, Cooking, Locomotion, Perception, Communication, Industrial, Warehouse, Mining, Construction, and 70+ more

## Defaults

- Model: `models/gemini-2.5-flash`
- Workers: 128
- Queue size: 1000
- RPM limit: 1000 (generator), 800 (diversify)
- Save interval: 200 nodes

## Environment Variables

- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: Required for generation

## Testing

```bash
# Run tests
pytest

# Run QA tests
taskpedia qa test

# Test generation without API
taskpedia generate -n 1000 --mock

# Check TUI works
taskpedia generate -n 100 --mock
```

## Common Tasks

### Adding a new CLI command

1. Add command function in `cli.py`: `def cmd_mycommand(args):`
2. Add subparser in `main()`
3. Set `parser.set_defaults(func=cmd_mycommand)`

### Modifying generation prompts

Edit `SYSTEM_PROMPT` in `generator.py` - defines what "atomic" means for robot training.

### Changing the task schema

1. Update `TaskNode` in `hierarchy.py`
2. Update `to_dict()` and `from_dict()` methods
3. Update upload schema in `cli.py` `cmd_upload()`

### Adding new verbs

1. Add verbs to appropriate category section in `verbs.py` ATOMIC_VERBS
2. Run `taskpedia qa test` to verify no duplicates
3. Update domain coverage tests in `qa.py` if adding new domains

## Notes

- Task IDs are hierarchical paths: `domain/task/subtask/atomic`
- Atomic actions are leaf nodes with `node_type=ATOMIC`
- Files are only written on save (no partial files)
- TUI requires terminal; falls back to tqdm if not TTY
- HuggingFace upload/download requires `datasets` and `huggingface_hub` packages
- Download caches SHA to skip re-download if local copy is up-to-date
