# TASKPEDIA

A comprehensive hierarchical taxonomy of human tasks for embodied AI and humanoid robots.

## Overview

TASKPEDIA builds a complete dictionary of human activities by:
1. **Bootstrapping** from authoritative seed data (O*NET, ATUS)
2. **Expanding** through LLM-powered decomposition and generation
3. **Storing** as a filesystem-backed directed acyclic graph (DAG)

```
Seeds (O*NET + Life) 
    → Bootstrap (20K nodes)
    → Ray Workers (parallel decomposition)
    → Tenacity (retry on failure)
    → Diskcache (avoid duplicate API calls)
    → TaskGraph (filesystem storage)
```

## Quick Start

```bash
# Install
uv pip install -e .

# Bootstrap from seed data (creates ~20K nodes)
taskpedia bootstrap -o ./task_hierarchy

# Generate more tasks using LLM
export GEMINI_API_KEY="your-key"
taskpedia generate -o ./task_hierarchy --max-tasks 1000

# Explore
taskpedia stats -o ./task_hierarchy
taskpedia search "welding" -o ./task_hierarchy
taskpedia tree -o ./task_hierarchy -d 3
```

## Seed Data

| Source | Nodes | Description |
|--------|-------|-------------|
| **O*NET** | 19,812 | U.S. Dept. of Labor occupational database |
| **Life Activities** | 495 | Personal/household/caregiving from ATUS |
| **Total** | **20,307** | Bootstrap nodes before LLM expansion |

### 35 Domains

**23 Work Domains** (from O*NET SOC major groups):
- Management, Business/Financial, Computer/Math, Architecture/Engineering
- Science, Community/Social, Legal, Education, Arts/Media
- Healthcare (Practitioners + Support), Protective Service
- Food Service, Building/Grounds, Personal Service, Sales
- Office/Admin, Farming/Fishing, Construction, Installation/Repair
- Production, Transportation, Military

**12 Life Domains** (from ATUS):
- Personal Care, Household, Caregiving, Consumer
- Education, Civic/Religious, Volunteer, Social/Leisure
- Sports/Exercise, Arts/Entertainment, Travel, Healthcare

## CLI Commands

```bash
taskpedia bootstrap    # Bootstrap from seed data
taskpedia generate     # Generate synthetic tasks with LLM
taskpedia tree         # Display hierarchy as tree
taskpedia stats        # Show statistics
taskpedia search       # Search for tasks
taskpedia export       # Export to JSONL/JSON
taskpedia taxonomy     # Show domain taxonomy
taskpedia cache-stats  # Show LLM cache stats
taskpedia cache-clear  # Clear LLM cache
```

## Architecture

```
taskpedia/
├── hierarchy.py    # TaskNode, TaskGraph (filesystem DAG)
├── generate.py     # Ray-parallel generation pipeline
├── llm.py          # Gemini 2.5 Flash client + caching
├── decompose.py    # Bootstrap from seeds
├── cli.py          # CLI interface
└── seeds/
    ├── onet.py     # O*NET database loader
    └── taxonomy.py # 35-domain taxonomy
```

## Requirements

- Python 3.11+
- `GEMINI_API_KEY` for LLM generation

## License

MIT
