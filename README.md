# TASKPEDIA

A comprehensive hierarchical taxonomy of human tasks for embodied AI and robotics training (VLA/VLN).

## Overview

TASKPEDIA builds a complete dictionary of human activities decomposed into atomic robot-executable actions:

```
Seeds (O*NET + Life Activities)
    → Init (20K nodes)
    → LLM Decomposition (continuous flow)
    → Atomic Actions (grasp, release, move_to, etc.)
    → HuggingFace Dataset
```

## Quick Start

```bash
# Install
uv pip install -e .

# Initialize from seed data (~20K nodes)
taskpedia init -o ./task_hierarchy

# Generate tasks using LLM (with live TUI)
export GEMINI_API_KEY="your-key"
taskpedia generate -n 100000

# View results
taskpedia show stats
taskpedia show tree -d 3
taskpedia show search "grasp"

# Export / Upload
taskpedia export -f jsonl
taskpedia upload --repo org/taskpedia

# Download existing dataset
taskpedia download --repo Sentient-x/taskpedia
```

## CLI Commands

```
taskpedia init              Initialize from O*NET + Life Activities
taskpedia generate          Generate tasks with LLM (live TUI)
taskpedia show stats        View statistics
taskpedia show tree         Display as tree
taskpedia show search       Search for tasks
taskpedia export            Export to jsonl/json/tree
taskpedia upload            Upload to HuggingFace
taskpedia download          Download from HuggingFace
taskpedia cache stats       Show LLM cache stats
taskpedia cache clear       Clear cache
taskpedia qa test           Run QA tests (verb taxonomy, domain coverage)
taskpedia qa analyze        Analyze data quality
taskpedia qa clean          Remove bad nodes
taskpedia qa verbs          Analyze verb taxonomy
taskpedia qa coverage       Check domain coverage
taskpedia diversify         Fill gaps in task tree
```

### Generate Options

```bash
taskpedia generate \
  -n 1000000 \          # Max tasks to generate
  --workers 128 \       # Parallel workers
  --rpm 1000 \          # Rate limit (Gemini Flash = 1000)
  --mock \              # Test without API calls
  --no-tui              # Disable live TUI
```

### Download Options

```bash
taskpedia download \
  --repo org/dataset \  # HuggingFace repo
  --force \             # Force re-download even if up-to-date
  -y                    # Skip confirmation prompts
```

## Seed Data

| Source | Nodes | Description |
|--------|-------|-------------|
| O*NET | 19,812 | U.S. Dept. of Labor occupational tasks |
| Life Activities | 495 | Personal/household from ATUS |
| **Total** | **20,307** | Bootstrap nodes before LLM expansion |

### 35 Domains

**23 Work Domains** (O*NET): Management, Business, Computer, Engineering, Science, Legal, Education, Healthcare, etc.

**12 Life Domains** (ATUS): Personal Care, Household, Caregiving, Education, Social, Sports, Travel, etc.

## Verb Taxonomy

TASKPEDIA includes a comprehensive verb taxonomy for validation:

- **ATOMIC_VERBS**: 3,479 physical action verbs across 80+ categories
- **COGNITIVE_VERBS**: 81 mental/internal verbs

Categories include: Manipulation, Tool Use, Cooking, Locomotion, Perception, Communication, Industrial/Manufacturing, Warehouse/Logistics, Mining, Construction, Electrical, Plumbing, HVAC, Automotive, Agriculture, Food Processing, Safety/PPE, and more.

## Architecture

```
taskpedia/
├── cli.py            # CLI interface
├── hierarchy.py      # TaskNode, TaskGraph (filesystem DAG)
├── generator.py      # Continuous flow generation + TUI
├── verbs.py          # ATOMIC_VERBS, COGNITIVE_VERBS taxonomies
├── validation.py     # Template detection, atomic validation
├── qa.py             # QA tests, domain coverage
├── llm.py            # Gemini 2.5 Flash client
├── utils.py          # RateLimiter, ProgressTracker
├── postprocess.py    # Data cleaning
├── decompose.py      # Bootstrap from seeds
└── seeds/
    ├── onet.py       # O*NET loader
    └── taxonomy.py   # 35-domain taxonomy
```

## Output Format

Tasks are stored as YAML files in a hierarchy:

```
task_hierarchy/
├── _manifest.json
├── work_healthcare/
│   └── nursing/
│       └── administer_medication/
│           ├── _meta.yaml
│           └── prepare_syringe/
│               └── _meta.yaml  # atomic
└── life_household/
    └── cooking/
        └── boil_water.yaml     # atomic
```

Each task includes:
- Completion criteria (precondition, postcondition, invariants)
- Physical/sensing/cognitive requirements
- Hierarchy relationships (parent, children)
- Source provenance (onet, llm_generated, etc.)

## Quality Assurance

Run comprehensive QA tests:

```bash
# Run all tests
taskpedia qa test

# Example output:
# [1] Verb Taxonomy Tests - 8 passed, 0 failed
# [2] Domain Coverage Tests - 23 passed, 0 failed
# [3] Comprehensive Domain Tests - 75 passed, 0 failed
```

## Requirements

- Python 3.11+
- `GEMINI_API_KEY` for LLM generation
- ~1000 RPM API quota (Gemini 2.5 Flash)

## License

Apache 2.0
