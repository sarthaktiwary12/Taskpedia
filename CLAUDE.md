# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PRAXIS is a large-scale, multilingual task generation system designed to create a comprehensive dictionary of human tasks for embodied AI and humanoid robots. Unlike typical datasets, PRAXIS aims for **exhaustive coverage** treating task documentation like lexicography rather than corpus collection.

**Core Principle**: Tasks are defined by verifiable completion criteria (precondition, postcondition, invariants) and are treated as cultural artifacts - e.g., "泡茶" (Chinese tea) and "make tea" (British) are distinct tasks.

## Development Commands

### Setup and Installation

```bash
# Install dependencies using pip
pip install -e .

# Or using uv (faster)
uv pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Running the CLI

```bash
# Generate tasks using the CLI
praxis generate --max-tasks 1000 --provider mock --output-dir output/

# Generate with Anthropic API (requires ANTHROPIC_API_KEY)
praxis generate --max-tasks 100 --provider anthropic --model claude-sonnet-4-20250514

# Use batch mode for 50% API cost savings
praxis generate --max-tasks 10000 --provider anthropic --batch-mode

# Preview a single task generation
praxis preview "crack" "egg" --provider mock

# Show available data sources
praxis sources

# Analyze task diversity
praxis analyze --output-dir output/ --sample-size 5000

# Monitor generation progress (TUI)
praxis monitor

# Resume a previous session
praxis resume --checkpoint-dir .praxis_checkpoints

# Show cache statistics
praxis cache-stats

# Clear the cache
praxis cache-clear
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=praxis --cov-report=html

# Run specific test file
pytest tests/test_generator.py

# Run with verbose output
pytest -v
```

### Linting and Formatting

```bash
# Run ruff linter
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code
ruff format .

# Type checking
mypy praxis/
```

## Architecture Overview

### Dual Module Structure

PRAXIS has **two parallel implementations**:

1. **`praxis/` package** - Modern Python package with Ray-based parallelization, advanced caching, checkpointing
2. **Root-level files** (`generator.py`, `schema.py`, `seeds.py`) - Standalone/legacy implementation

Both share the same core concepts but differ in execution model. The `praxis/` package is production-ready with proper dependency management, while root files are reference implementations.

### Core Data Model

The fundamental unit is a **Task** (defined in `schema.py` and `praxis/schema.py`):

```python
Task(
    id="en_crack_an_egg",
    name="crack an egg",
    language="en",
    completion=CompletionCriteria(
        precondition="Intact egg available. Target container positioned.",
        postcondition="Eggshell separated. Contents in container. Yolk intact.",
        invariants="Shell fragments don't contaminate contents."
    ),
    physical="Bimanual task. Controlled impact...",
    sensing="Tactile: grip pressure. Visual: targeting...",
    cognitive="Low planning horizon. Error detection...",
    context="Kitchen, counter height.",
    tags=["bimanual", "fragile_object", "food_preparation"],
    relationships=Relationships(
        part_of=["en_make_scrambled_eggs"],
        composed_of=["en_grasp_egg", "en_strike_egg"],
        requires_ability=["en_pinch_grasp"]
    )
)
```

### Generation Pipeline (praxis/ package)

The modern implementation uses Ray for parallelization:

```
Seed Data → Verb-Noun Matrix → LLM Generation → Validation → Storage
    ↓            ↓                    ↓              ↓          ↓
sources.py   generator.py        llm.py       diversity.py  checkpoint.py
```

**Key components**:

- **`sources.py`**: Provides seed verbs, nouns, and personas from various data sources (VerbNet, WordNet, O*NET)
- **`generator.py`**: `ParallelTaskGenerator` orchestrates Ray workers, manages job queue, handles checkpointing
- **`llm.py`**: `LLMClient` abstraction supporting Anthropic API (realtime + batch modes) with retry logic
- **`cache.py`**: Disk-based LLM response cache to avoid redundant API calls
- **`checkpoint.py`**: Crash recovery via SQLite-backed job tracking
- **`diversity.py`**: Embedding-based clustering to measure task coverage
- **`cli.py`**: Click-based CLI interface
- **`tui.py`**: Textual-based terminal UI for monitoring

### Configuration System

Configuration uses Pydantic Settings with environment variable support:

```python
# Configuration hierarchy
PraxisConfig (main settings in praxis/config.py)
├── LLM settings (provider, model, temperature)
├── Execution mode (realtime vs batch)
├── Parallelization (Ray workers, CPU allocation)
├── Storage (cache, checkpoint, output dirs)
└── Quality thresholds (confidence, self-consistency)

DataSourceConfig (data sources)
├── Enable/disable external datasets
└── Domain coverage weights
```

**Environment variables**: Prefix with `PRAXIS_` (e.g., `PRAXIS_ANTHROPIC_API_KEY`, `PRAXIS_LLM_PROVIDER=anthropic`)

### Generation Methods

Tasks are generated through multiple strategies (see `GenerationMethod` enum):

1. **VERB_NOUN_MATRIX**: Systematic combination of verbs × nouns from seed data
2. **LLM_DECOMPOSITION**: Break complex tasks into subtasks recursively
3. **LLM_EXPANSION**: Generate similar/related tasks for coverage
4. **EVOLVED**: Evol-Instruct style mutations (add constraint, change context, etc.)
5. **CULTURAL_ADAPTATION**: Cross-language/culture variants
6. **SEED_EXTRACTED**: Bootstrap from existing datasets (BEHAVIOR-1K, O*NET)

### Task Storage and Organization

Tasks are stored in JSONL format:

```
output/
└── tasks_20260111_123045.jsonl  # Timestamped batch files
```

Each line is a complete Task JSON object. Files are organized by generation session with timestamps.

### Checkpointing and Crash Recovery

The system maintains crash recovery state:

```
.praxis_checkpoints/
├── {session_id}/
│   ├── jobs.db           # SQLite database of all jobs
│   ├── tasks.db          # Generated tasks
│   └── metadata.json     # Session metadata
```

Sessions can be resumed with `praxis resume` to continue incomplete generation runs.

### Quality Control

Multiple validation layers:

1. **Prompt-time validation**: LLM returns `is_valid_task` boolean and `confidence` score
2. **Self-consistency**: Generate same task multiple times, verify consistency
3. **LLM-as-judge**: Separate validation pass scoring completion criteria quality
4. **Diversity analysis**: Embedding-based clustering to detect redundancy

## Important Implementation Details

### Prompt Engineering

Prompts are carefully structured (see `generator.py` and `praxis/generator.py`):

- System prompts establish expert persona
- Few-shot examples are NOT used (to avoid bias toward common tasks)
- JSON schema is explicitly specified in prompts
- Persona rotation provides perspective diversity

### Parallelization Strategy

Ray workers process jobs concurrently:

```python
# Workers pull from job queue
# Each worker has own LLM client instance
# Results stream back through Ray futures
# Checkpoint updated on completion

workers = [TaskGeneratorWorker.remote(i, config) for i in range(num_workers)]
futures = [worker.process_job.remote(job) for job, worker in zip(jobs, workers)]
```

### Caching Layer

Three-tier caching:

1. **LLM response cache** (`cache.py`): Keyed by prompt hash, TTL-based expiry
2. **Task deduplication**: Track seen task IDs to avoid regenerating identical tasks
3. **Data source caching**: HuggingFace datasets cached locally

### API Cost Management

For Anthropic API:

- **Realtime mode**: Direct API calls, immediate results
- **Batch mode**: 50% cost discount, 24h latency (use `--batch-mode`)
- Cache hit rate typically 30-40% on continued runs
- Estimate: ~4K tokens per task, Claude Sonnet 4 costs apply

## Common Workflows

### Adding a New Generation Strategy

1. Add new `GenerationMethod` enum value to `schema.py`
2. Implement generation logic in `TaskGeneratorWorker.process_job()` in `praxis/generator.py`
3. Create new prompt template at top of `generator.py`
4. Add CLI command in `cli.py` if needed

### Extending Supported Languages

1. Add language code to `SUPPORTED_LANGUAGES` in `schema.py`
2. Add seed verbs/nouns for that language in `sources.py`
3. Update cultural adaptation prompts to handle new language
4. Ensure task ID normalization handles Unicode properly

### Modifying Task Schema

1. Update `Task` dataclass in `schema.py` (both root and `praxis/`)
2. Update serialization methods (`to_dict()`, `from_dict()`)
3. Update generation prompts to include new fields
4. Update validation logic if needed
5. Maintain backward compatibility by providing defaults

### Debugging Generation Issues

1. Use `praxis preview "verb" "noun"` to test single generation
2. Check `.praxis_cache/` for cached responses
3. Enable verbose logging: `praxis -v generate ...`
4. Use `--json-logs` for structured logging
5. Check checkpoint database: `sqlite3 .praxis_checkpoints/{session_id}/jobs.db`

## File Reference

### Root Level
- `generator.py` - Standalone task generator implementation
- `schema.py` - Task data model definition (standalone version)
- `seeds.py` - Seed verbs and nouns (extensive lists)
- `pyproject.toml` - Package metadata, dependencies, tool configuration

### praxis/ Package
- `__init__.py` - Package version
- `schema.py` - Task data model (package version)
- `config.py` - Pydantic settings and configuration
- `generator.py` - Ray-based parallel task generator
- `llm.py` - LLM client abstraction with retry logic
- `cache.py` - Disk cache for LLM responses
- `checkpoint.py` - SQLite-based crash recovery
- `sources.py` - Seed data from external sources (VerbNet, WordNet, O*NET)
- `diversity.py` - Embedding-based diversity analysis
- `cli.py` - Click CLI interface
- `tui.py` - Textual TUI for monitoring

## Key Constants and Defaults

- **Default model**: `claude-sonnet-4-20250514`
- **Default temperature**: 0.7
- **Max tokens**: 4096
- **Workers per CPU**: 2
- **Batch size**: 100 jobs
- **Confidence threshold**: 0.7
- **Cache TTL**: 365 days
- **Supported languages**: 30 (see `SUPPORTED_LANGUAGES`)
- **Canonical tags**: ~60 tags (see `CANONICAL_TAGS`)

## Dependencies

Core:
- `pydantic>=2.5.0` - Configuration and validation
- `ray[default]>=2.9.0` - Parallelization
- `anthropic>=0.39.0` - LLM API client
- `click>=8.1.0` - CLI framework
- `textual>=0.89.0` - TUI framework

Development:
- `pytest>=8.0.0` - Testing
- `ruff>=0.1.0` - Linting and formatting
- `mypy>=1.8.0` - Type checking

## Notes for Future Development

- The project supports both standalone scripts and the `praxis/` package - prefer working in `praxis/` for production features
- Task IDs must be globally unique across languages (format: `{lang}_{normalized_name}`)
- Completion criteria are the defining feature - if you can't verify completion, it's not a valid task
- Cultural specificity matters - translations are not adaptations
- Tags are factual properties, not subjective categories
- The task graph (relationships) enables curriculum learning and transfer learning research
