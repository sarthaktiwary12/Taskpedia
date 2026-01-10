# PRAXIS

**A Comprehensive Dictionary of Human Tasks for Embodied AI**

---

## Overview

PRAXIS is a large-scale, multilingual dictionary of human tasks designed for training and evaluating embodied AI systems, particularly humanoid robots. Unlike existing task datasets that sample from human activity, PRAXIS aims for **exhaustive coverage**—treating task documentation like lexicography rather than corpus collection.

### Key Principles

1. **Completion Criteria Define Tasks** — A task exists if and only if it has verifiable completion criteria (precondition, postcondition, invariants)

2. **Cultural Tasks as First-Class Entities** — Tasks in different languages are distinct entries, not translations. "泡茶" (Chinese tea) and "make tea" (British) are different tasks with different procedures.

3. **Dictionary, Not Corpus** — Comprehensive coverage of everything humans *can* do, including rare tasks underrepresented in naturalistic data.

4. **Compositional Structure** — Tasks form a directed acyclic graph from atomic actions to complex behaviors.

## Project Structure

```
praxis/
├── src/
│   ├── schema.py          # Core task schema and data models
│   ├── config.py          # Pipeline configuration
│   ├── seeds.py           # Seed verbs, nouns, and existing tasks
│   ├── generator.py       # Task generation with LLM integration
│   ├── validator.py       # Validation and quality control
│   └── storage.py         # Task storage and retrieval
├── data/
│   ├── seeds/             # Seed data from existing sources
│   └── generated/         # Generated task definitions
│       └── tasks/         # Task files organized by language
│           ├── en/
│           ├── zh/
│           └── ...
├── configs/               # Generation configurations
├── scripts/               # Utility scripts
└── paper/                 # Paper draft and figures
```

## Task Schema

Each PRAXIS task entry contains:

```yaml
id: en_crack_an_egg
name: "crack an egg"
language: en

completion:
  precondition: |
    Intact egg available. Target container positioned.
  postcondition: |
    Eggshell separated. Contents in container. Yolk intact.
  invariants: |
    Shell fragments don't contaminate contents.

physical: "Bimanual task. Controlled impact. Pinch grip..."
sensing: "Tactile: grip pressure. Visual: targeting..."
cognitive: "Low planning horizon. Error detection..."
context: "Kitchen, counter height. Cooking activity."

tags: [bimanual, fragile_object, food_preparation, tool_free]

relationships:
  part_of: [en_make_scrambled_eggs, en_bake_a_cake]
  composed_of: [en_grasp_egg, en_strike_egg, en_separate_shell]
  requires_ability: [en_pinch_grasp, en_bimanual_coordination]
```

## Generation Pipeline

PRAXIS uses a multi-stage generation pipeline:

1. **Seed Extraction** — Bootstrap from BEHAVIOR-1K, O*NET, ADL/IADL literature
2. **Verb-Noun Matrix** — Systematic combination of action verbs with object nouns
3. **LLM Generation** — Structured prompts to generate full task definitions
4. **Recursive Decomposition** — Break complex tasks into subtasks
5. **Evol-Instruct Evolution** — Mutations for diversity (add constraint, change context, etc.)
6. **Cultural Adaptation** — Adapt tasks to different languages/cultures
7. **Validation** — Self-consistency, LLM-as-judge, deduplication, human spot-check

## Quick Start

```python
from src.schema import Task
from src.generator import create_generator

# Create a generator
generator = create_generator()

# Generate tasks from verb-noun matrix
for result in generator.generate_verb_noun_matrix(language="en", max_tasks=100):
    if result.success:
        task = result.task
        print(f"Generated: {task.name}")
        print(f"  Postcondition: {task.completion.postcondition[:100]}...")
```

## Supported Languages

PRAXIS targets 20+ languages with emphasis on cultural specificity:

| Language | Code | Cultural Focus |
|----------|------|----------------|
| English | en | British, American, Australian variants |
| Chinese | zh | Mainland, Taiwanese, Cantonese practices |
| Spanish | es | Spain, Mexico, South American variants |
| Hindi | hi | North Indian cultural context |
| Japanese | ja | Traditional and modern practices |
| Arabic | ar | Regional variants across Middle East |
| ... | ... | ... |

## Citation

```bibtex
@article{praxis2026,
  title={PRAXIS: A Comprehensive Dictionary of Human Tasks for Embodied AI},
  author={...},
  journal={...},
  year={2026}
}
```

## License

[License to be determined — considering responsible use provisions]

## Contributing

We welcome contributions to expand coverage, especially:
- Tasks from underrepresented languages and cultures
- Specialized professional/occupational tasks
- Traditional crafts and practices
- Validation and quality improvement

---

*PRAXIS: From Greek πρᾶξις (praxis) — action, practice, the process of doing*
