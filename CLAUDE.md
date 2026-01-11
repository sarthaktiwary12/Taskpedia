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
├── verbs.py          # ATOMIC_VERBS (3,479), COGNITIVE_VERBS taxonomies
├── validation.py     # is_generic_template, is_valid_atomic
├── qa.py             # QA tests, domain coverage checks
├── llm.py            # Gemini 2.5 Flash client
├── utils.py          # RateLimiter, ProgressTracker (shared utilities)
├── postprocess.py    # Data cleaning commands
├── decompose.py      # Bootstrap from seed data
└── seeds/
    ├── onet.py       # O*NET database loader
    └── taxonomy.py   # 35-domain taxonomy
```

### Key Files

| File | Purpose |
|------|---------|
| `generator.py` | Main generator - ThreadPoolExecutor, Textual TUI, atomic saves |
| `verbs.py` | ATOMIC_VERBS (3,479 verbs), COGNITIVE_VERBS, category utilities |
| `validation.py` | Template detection, atomic action validation |
| `qa.py` | Test suites for verb taxonomy and domain coverage |
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

**Key classes**:
- `FastGenConfig`: Configuration dataclass
- `GeneratorCore`: Generation logic (thread-safe)
- `GeneratorApp`: Textual app for TUI
- `AtomicCounter`: Thread-safe counter

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
