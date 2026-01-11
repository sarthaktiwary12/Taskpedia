# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TASKPEDIA is a large-scale, multilingual task generation system designed to create a comprehensive dictionary of human tasks for embodied AI and humanoid robots. Unlike typical datasets, TASKPEDIA aims for **exhaustive coverage** treating task documentation like lexicography rather than corpus collection.

**Core Principle**: Tasks are defined by verifiable completion criteria (precondition, postcondition, invariants) and are treated as cultural artifacts - e.g., "泡茶" (Chinese tea) and "make tea" (British) are distinct tasks.

## Generation Pipeline

```
Seeds (O*NET + Life) 
    → Bootstrap (20K nodes)
    → Ray Workers (parallel decomposition)
    → Tenacity (retry on failure)
    → Diskcache (avoid duplicate API calls)
    → TaskGraph (filesystem storage)
```

## Development Commands

### Setup and Installation

```bash
# Install dependencies using uv
uv pip install -e .

# Install development dependencies
uv pip install -e ".[dev]"
```

### Running the CLI

```bash
# Bootstrap from seed data (O*NET + Life Activities)
taskpedia bootstrap -o ./task_hierarchy

# Generate synthetic tasks using LLM
taskpedia generate -o ./task_hierarchy --max-tasks 1000

# Generate with custom settings
taskpedia generate -o ./task_hierarchy --max-tasks 10000 --workers 8 --rpm 100

# View the hierarchy
taskpedia tree -o ./task_hierarchy

# Show statistics
taskpedia stats -o ./task_hierarchy

# Search for tasks
taskpedia search "welding" -o ./task_hierarchy

# Export to JSONL
taskpedia export -o ./task_hierarchy --format jsonl

# Show taxonomy (35 domains)
taskpedia taxonomy

# Show cache statistics
taskpedia cache-stats

# Clear the cache
taskpedia cache-clear
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=taskpedia --cov-report=html

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
mypy taskpedia/
```

## Architecture Overview

### Core Data Model

The fundamental unit is a **TaskNode** (defined in `taskpedia/hierarchy.py`):

```python
TaskNode(
    id="work_healthcare_practitioners/registered_nurses/administer_medications",
    name="Administer medications to patients and monitor patients for reactions",
    node_type=NodeType.SUBTASK,
    parent_id="work_healthcare_practitioners/registered_nurses",
    sources=[SeedSource.ONET],
    source_ids=["29-1141.00"],
    confidence=1.0,
)
```

### Hierarchy Structure

```
35 Domains
├── 23 Work Domains (from O*NET SOC major occupation groups)
│   ├── 1,016 Occupations
│   └── 18,796 Task Statements
└── 12 Life Domains (from ATUS categories)
    ├── 41 Activity Categories  
    └── 454 Example Tasks
```

### Key Components

| File | Purpose |
|------|---------|
| `taskpedia/hierarchy.py` | TaskNode, TaskGraph data structures |
| `taskpedia/generate.py` | Ray-based parallel generation pipeline |
| `taskpedia/llm.py` | Gemini 2.5 Flash client with caching |
| `taskpedia/decompose.py` | Bootstrap from seed data |
| `taskpedia/seeds/onet.py` | O*NET database loader |
| `taskpedia/seeds/taxonomy.py` | 35-domain taxonomy |
| `taskpedia/cli.py` | CLI interface |

### Generation Pipeline

Uses battle-tested libraries:

- **Ray**: Parallel task processing with `@ray.remote` workers
- **Tenacity**: Retry logic with exponential backoff
- **Diskcache**: Persistent LLM response caching

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60),
)
def _call_llm(self, prompt: str, system_prompt: str) -> str:
    self._rate_limit()
    return self.client.generate(prompt, system_prompt)
```

### Task Storage

Tasks are stored as a filesystem-backed DAG:

```
task_hierarchy/
├── _manifest.json              # Index of all nodes
├── work_management/
│   ├── _meta.yaml              # Domain node
│   ├── chief_executives/
│   │   ├── _meta.yaml          # Occupation node
│   │   └── direct_or_coordinate_activities/
│   │       └── _meta.yaml      # Task node
└── life_household/
    ├── _meta.yaml
    └── cooking/
        └── _meta.yaml
```

## Key Constants and Defaults

- **Default model**: `models/gemini-2.5-flash`
- **Default temperature**: 0.7
- **Thinking budget**: 1024 tokens
- **Max output tokens**: 8192
- **Workers**: 4 (parallel)
- **Rate limit**: 60 RPM
- **LLM cache**: `~/.taskpedia_cache/` (10GB limit)
- **O*NET cache**: `~/.cache/taskpedia/onet/` (auto-downloaded)

## Environment Variables

- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: Required for LLM generation

## Dependencies

Core:
- `google-genai>=1.0.0` - Gemini API client
- `ray[default]>=2.9.0` - Parallelization
- `tenacity>=8.2.0` - Retry logic
- `diskcache>=5.6.0` - LLM response caching
- `pyyaml>=6.0` - YAML serialization
- `tqdm>=4.66.0` - Progress bars

Data:
- `datasets>=2.16.0` - HuggingFace datasets
- `huggingface-hub>=0.20.0` - Dataset downloading

Development:
- `pytest>=8.0.0` - Testing
- `ruff>=0.1.0` - Linting and formatting
- `mypy>=1.8.0` - Type checking

## File Reference

### taskpedia/ Package
- `__init__.py` - Package exports
- `hierarchy.py` - TaskNode, TaskGraph, NodeType, SeedSource
- `generate.py` - TaskGenerator, GenerationConfig, Ray workers
- `llm.py` - LLMClient, LLMConfig, CachedLLMClient
- `decompose.py` - DecompositionEngine, quick_bootstrap
- `cli.py` - CLI commands
- `seeds/` - Seed data loaders
  - `onet.py` - O*NET database (18,796 tasks)
  - `taxonomy.py` - 35-domain taxonomy
  - `base.py` - Base loader classes
  - `loaders.py` - Additional dataset loaders

### Data (auto-downloaded)
- `~/.cache/taskpedia/onet/` - O*NET 30.1 database (auto-downloaded on first bootstrap)

## Notes for Future Development

- Task IDs are hierarchical paths (e.g., `domain/task/subtask`)
- Completion criteria are the defining feature - if you can't verify completion, it's not a valid task
- Cultural specificity matters - translations are not adaptations
- The task graph enables curriculum learning and transfer learning research
- Use `taskpedia bootstrap` before `taskpedia generate` to seed the hierarchy
