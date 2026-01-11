"""
Dataset Loaders for Seed Tasks.

This module provides loaders for external datasets that serve as seeds
for hierarchical task decomposition. Each loader normalizes its source
data into a common format (SeedTask) for unified processing.

Available Datasets (in priority order):

1. Anthropic Economic Index - O*NET task mappings (HuggingFace)
2. WikiHow Goal-Step - Procedural knowledge (HuggingFace)
3. COIN - Hierarchical instructional videos (GitHub)
4. EPIC-KITCHENS - Verb-noun action pairs (GitHub)
5. ActivityNet - Hierarchical action taxonomy (JSON)

Each loader follows the pattern:
    1. Download/cache the dataset
    2. Parse into SeedTask objects
    3. Provide domain/task/subtask iterators
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

from taskpedia.hierarchy import SeedSource
from taskpedia.seeds.base import BaseSeedLoader, SeedTask


class ONetTaskLoader(BaseSeedLoader):
    """
    Load O*NET task statements from Anthropic Economic Index dataset.

    This provides 19,000+ occupation-specific task statements covering
    all 923 O*NET occupations. Tasks are organized by occupation.

    Source: https://huggingface.co/datasets/Anthropic/EconomicIndex
    """

    source = SeedSource.ONET

    def __init__(self, cache_dir: Path | str | None = None):
        super().__init__(cache_dir)
        self._tasks: list[dict] = []
        self._occupations: dict[str, list[dict]] = {}

    def load(self) -> None:
        """Load the O*NET tasks from HuggingFace."""
        if self._loaded:
            return

        try:
            from datasets import load_dataset

            # Load the Anthropic Economic Index dataset
            dataset = load_dataset(
                "Anthropic/EconomicIndex",
                cache_dir=str(self.cache_dir),
            )

            # The dataset has task statements in the main split
            if "train" in dataset:
                for item in dataset["train"]:
                    task_data = {
                        "task": item.get("task", ""),
                        "occupation": item.get("occupation", ""),
                        "occupation_code": item.get("o_net_soc_code", ""),
                    }
                    self._tasks.append(task_data)

                    # Organize by occupation
                    occ = task_data["occupation"]
                    if occ not in self._occupations:
                        self._occupations[occ] = []
                    self._occupations[occ].append(task_data)

            self._loaded = True

        except Exception as e:
            print(f"Warning: Could not load O*NET dataset: {e}")
            self._loaded = True  # Mark as loaded to avoid retry

    def get_domains(self) -> list[SeedTask]:
        """Get occupation categories as domains."""
        self.load()

        # Group occupations by their major category (first 2 digits of SOC code)
        categories = {}
        for occ, tasks in self._occupations.items():
            if tasks:
                code = tasks[0].get("occupation_code", "00-0000")
                major = code.split("-")[0] if "-" in code else code[:2]
                if major not in categories:
                    categories[major] = []
                categories[major].append(occ)

        domains = []
        for major_code, occupations in categories.items():
            domains.append(
                SeedTask(
                    source=self.source,
                    source_id=f"soc_{major_code}",
                    name=f"Occupation Group {major_code}",
                    domain="occupational",
                    hierarchy_level=0,
                    children_names=occupations[:10],  # Limit for sanity
                )
            )

        return domains

    def get_tasks(self, domain: str | None = None) -> list[SeedTask]:
        """Get tasks (occupations)."""
        self.load()

        tasks = []
        for occupation, task_list in self._occupations.items():
            task_names = [t["task"] for t in task_list if t["task"]]
            tasks.append(
                SeedTask(
                    source=self.source,
                    source_id=task_list[0].get("occupation_code", occupation),
                    name=occupation,
                    domain="occupational",
                    hierarchy_level=1,
                    children_names=task_names[:20],  # Top 20 tasks
                    description=f"Tasks performed by {occupation}",
                )
            )

        return tasks

    def get_subtasks(self, task_id: str) -> list[SeedTask]:
        """Get individual task statements for an occupation."""
        self.load()

        subtasks = []
        for occupation, task_list in self._occupations.items():
            if task_list and task_list[0].get("occupation_code") == task_id:
                for i, task_data in enumerate(task_list):
                    subtasks.append(
                        SeedTask(
                            source=self.source,
                            source_id=f"{task_id}_{i}",
                            name=task_data["task"],
                            domain="occupational",
                            parent_name=occupation,
                            hierarchy_level=2,
                        )
                    )
                break

        return subtasks


class WikiHowLoader(BaseSeedLoader):
    """
    Load procedural knowledge from WikiHow Goal-Step dataset.

    This provides ~187k goal descriptions with ordered steps,
    making it ideal for task decomposition.

    Source: https://huggingface.co/datasets/tasksource/goal-step-wikihow
    """

    source = SeedSource.WIKIHOW

    def __init__(self, cache_dir: Path | str | None = None):
        super().__init__(cache_dir)
        self._goals: list[dict] = []
        self._steps: dict[str, list[str]] = {}

    def load(self) -> None:
        """Load WikiHow data from HuggingFace."""
        if self._loaded:
            return

        try:
            from datasets import load_dataset

            # Load the goal-step dataset
            dataset = load_dataset(
                "tasksource/goal-step-wikihow",
                "goal",  # The goal subset
                cache_dir=str(self.cache_dir),
            )

            if "train" in dataset:
                for item in dataset["train"]:
                    goal = item.get("goal", "")
                    self._goals.append(
                        {
                            "goal": goal,
                            "label": item.get("label", 0),
                        }
                    )

            # Also load steps
            step_dataset = load_dataset(
                "tasksource/goal-step-wikihow",
                "step",
                cache_dir=str(self.cache_dir),
            )

            if "train" in step_dataset:
                for item in step_dataset["train"]:
                    goal = item.get("goal", "")
                    step = item.get("step", "")
                    if goal not in self._steps:
                        self._steps[goal] = []
                    self._steps[goal].append(step)

            self._loaded = True

        except Exception as e:
            print(f"Warning: Could not load WikiHow dataset: {e}")
            self._loaded = True

    def get_domains(self) -> list[SeedTask]:
        """WikiHow doesn't have explicit domains, return broad categories."""
        # Infer domains from goal keywords
        domain_keywords = {
            "food_cooking": ["cook", "make", "bake", "prepare", "recipe"],
            "home_garden": ["clean", "organize", "decorate", "garden", "plant"],
            "health_fitness": ["exercise", "workout", "diet", "health", "sleep"],
            "personal_care": ["hair", "skin", "makeup", "grooming"],
            "technology": ["computer", "phone", "internet", "software", "app"],
            "relationships": ["friend", "dating", "relationship", "family"],
            "education": ["study", "learn", "school", "college", "exam"],
            "career": ["job", "work", "interview", "resume", "career"],
            "finance": ["money", "budget", "save", "invest", "tax"],
            "hobbies": ["craft", "art", "music", "game", "hobby"],
        }

        domains = []
        for domain_name, keywords in domain_keywords.items():
            domains.append(
                SeedTask(
                    source=self.source,
                    source_id=f"wikihow_{domain_name}",
                    name=domain_name.replace("_", " ").title(),
                    domain=domain_name,
                    hierarchy_level=0,
                    description=f"WikiHow articles related to {domain_name.replace('_', ' ')}",
                )
            )

        return domains

    def get_tasks(self, domain: str | None = None) -> list[SeedTask]:
        """Get goals as tasks."""
        self.load()

        tasks = []
        seen = set()

        for goal_data in self._goals:
            goal = goal_data["goal"]
            if goal in seen:
                continue
            seen.add(goal)

            steps = self._steps.get(goal, [])
            tasks.append(
                SeedTask(
                    source=self.source,
                    source_id=f"wikihow_goal_{len(tasks)}",
                    name=goal,
                    domain="procedural",
                    hierarchy_level=1,
                    steps=steps[:10],  # Limit steps
                    children_names=steps[:10],
                )
            )

        return tasks[:5000]  # Limit for sanity

    def get_subtasks(self, task_id: str) -> list[SeedTask]:
        """Get steps for a goal."""
        self.load()

        # Find the goal by task_id
        idx = int(task_id.replace("wikihow_goal_", ""))
        if idx >= len(self._goals):
            return []

        goal = self._goals[idx]["goal"]
        steps = self._steps.get(goal, [])

        subtasks = []
        for i, step in enumerate(steps):
            subtasks.append(
                SeedTask(
                    source=self.source,
                    source_id=f"{task_id}_step_{i}",
                    name=step,
                    domain="procedural",
                    parent_name=goal,
                    hierarchy_level=2,
                )
            )

        return subtasks


class COINLoader(BaseSeedLoader):
    """
    Load hierarchical task data from COIN dataset.

    COIN provides the cleanest hierarchical structure:
    12 domains → 180 tasks → ~800 steps

    Source: https://github.com/coin-dataset/annotations
    """

    source = SeedSource.COIN

    # COIN taxonomy (hardcoded since it's static)
    COIN_TAXONOMY = {
        "nursing_caring": {
            "name": "Nursing & Caring",
            "tasks": [
                "take care of plants",
                "make the bed",
                "change diaper",
                "change bed sheets",
                "fold clothes",
                "bathe a baby",
            ],
        },
        "vehicles": {
            "name": "Vehicles",
            "tasks": [
                "change a tire",
                "jump start a car",
                "replace wiper blades",
                "check tire pressure",
                "add windshield washer fluid",
                "replace car battery",
                "change engine oil",
            ],
        },
        "leisure_performance": {
            "name": "Leisure & Performance",
            "tasks": [
                "play badminton",
                "play basketball",
                "play baseball",
                "do gymnastics",
                "do archery",
                "play bowling",
            ],
        },
        "gadgets": {
            "name": "Gadgets",
            "tasks": [
                "charge a phone",
                "use a laptop",
                "set up wifi router",
                "replace phone screen",
                "clean phone",
                "pair bluetooth",
            ],
        },
        "electric_appliances": {
            "name": "Electric Appliances",
            "tasks": [
                "replace a bulb",
                "install ceiling fan",
                "use vacuum cleaner",
                "use washing machine",
                "use microwave",
                "use blender",
            ],
        },
        "household_items": {
            "name": "Household Items",
            "tasks": [
                "hang a picture",
                "assemble furniture",
                "fix a door",
                "unclog a drain",
                "fix a leaky faucet",
                "paint a wall",
            ],
        },
        "science_craft": {
            "name": "Science & Craft",
            "tasks": [
                "do origami",
                "make slime",
                "tie-dye a shirt",
                "make a candle",
                "do pottery",
                "knit a scarf",
            ],
        },
        "plants_fruits": {
            "name": "Plants & Fruits",
            "tasks": [
                "plant a seed",
                "transplant a plant",
                "prune a tree",
                "harvest vegetables",
                "water plants",
                "fertilize soil",
            ],
        },
        "snacks_drinks": {
            "name": "Snacks & Drinks",
            "tasks": [
                "make coffee",
                "make tea",
                "make a smoothie",
                "make popcorn",
                "make lemonade",
                "make a milkshake",
            ],
        },
        "dishes": {
            "name": "Dishes",
            "tasks": [
                "make pasta",
                "make a salad",
                "grill steak",
                "bake cookies",
                "make soup",
                "fry eggs",
                "make sandwich",
                "cook rice",
                "roast chicken",
            ],
        },
        "sports": {
            "name": "Sports",
            "tasks": [
                "swing a golf club",
                "throw a football",
                "serve in tennis",
                "shoot a basketball",
                "kick a soccer ball",
            ],
        },
        "housework": {
            "name": "Housework",
            "tasks": [
                "sweep the floor",
                "mop the floor",
                "clean windows",
                "do laundry",
                "iron clothes",
                "organize closet",
                "take out trash",
                "wash dishes",
            ],
        },
    }

    def __init__(self, cache_dir: Path | str | None = None):
        super().__init__(cache_dir)

    def load(self) -> None:
        """COIN taxonomy is hardcoded, just mark as loaded."""
        self._loaded = True

    def get_domains(self) -> list[SeedTask]:
        """Get COIN domains."""
        domains = []
        for domain_id, domain_data in self.COIN_TAXONOMY.items():
            domains.append(
                SeedTask(
                    source=self.source,
                    source_id=f"coin_{domain_id}",
                    name=domain_data["name"],
                    domain=domain_id,
                    hierarchy_level=0,
                    children_names=domain_data["tasks"],
                )
            )
        return domains

    def get_tasks(self, domain: str | None = None) -> list[SeedTask]:
        """Get COIN tasks."""
        tasks = []

        for domain_id, domain_data in self.COIN_TAXONOMY.items():
            if domain and domain != domain_id:
                continue

            for task_name in domain_data["tasks"]:
                tasks.append(
                    SeedTask(
                        source=self.source,
                        source_id=f"coin_{domain_id}_{task_name.replace(' ', '_')}",
                        name=task_name,
                        domain=domain_id,
                        parent_name=domain_data["name"],
                        hierarchy_level=1,
                    )
                )

        return tasks

    def get_subtasks(self, task_id: str) -> list[SeedTask]:
        """COIN steps would need video annotation parsing."""
        # For now, return empty - steps would need full dataset
        return []


class EpicKitchensLoader(BaseSeedLoader):
    """
    Load verb-noun action pairs from EPIC-KITCHENS.

    Provides fine-grained kitchen actions:
    97 verb classes × 300 noun classes

    Source: https://github.com/epic-kitchens/epic-kitchens-100-annotations
    """

    source = SeedSource.EPIC_KITCHENS

    # Core verb classes from EPIC-KITCHENS
    VERBS = [
        "take",
        "put",
        "open",
        "close",
        "wash",
        "cut",
        "mix",
        "pour",
        "move",
        "remove",
        "insert",
        "turn-on",
        "turn-off",
        "throw",
        "dry",
        "shake",
        "squeeze",
        "peel",
        "scoop",
        "spread",
        "flip",
        "fold",
        "press",
        "check",
        "adjust",
        "fill",
        "empty",
        "scrape",
    ]

    # Core noun classes organized by category
    NOUNS = {
        "containers": [
            "pan",
            "pot",
            "bowl",
            "plate",
            "cup",
            "mug",
            "glass",
            "jar",
            "bottle",
            "container",
            "lid",
            "tray",
            "bag",
        ],
        "utensils": [
            "knife",
            "fork",
            "spoon",
            "spatula",
            "ladle",
            "whisk",
            "tongs",
            "peeler",
            "grater",
            "scissors",
            "brush",
        ],
        "appliances": [
            "fridge",
            "freezer",
            "oven",
            "microwave",
            "toaster",
            "kettle",
            "blender",
            "mixer",
            "dishwasher",
            "tap",
        ],
        "food": [
            "egg",
            "bread",
            "butter",
            "cheese",
            "milk",
            "water",
            "oil",
            "salt",
            "pepper",
            "sugar",
            "flour",
            "rice",
            "pasta",
            "meat",
            "chicken",
            "fish",
            "vegetable",
            "fruit",
            "onion",
            "tomato",
            "potato",
            "carrot",
            "lettuce",
        ],
        "surfaces": [
            "counter",
            "table",
            "sink",
            "stove",
            "cutting-board",
            "drawer",
            "cupboard",
            "shelf",
        ],
    }

    def __init__(self, cache_dir: Path | str | None = None):
        super().__init__(cache_dir)

    def load(self) -> None:
        """Mark as loaded (using hardcoded data)."""
        self._loaded = True

    def get_domains(self) -> list[SeedTask]:
        """Kitchen is the single domain."""
        return [
            SeedTask(
                source=self.source,
                source_id="epic_kitchen",
                name="Kitchen Activities",
                domain="kitchen",
                hierarchy_level=0,
                description="Fine-grained kitchen actions from EPIC-KITCHENS",
            )
        ]

    def get_tasks(self, domain: str | None = None) -> list[SeedTask]:
        """Generate verb-noun combinations as tasks."""
        tasks = []

        for verb in self.VERBS:
            for noun_category, nouns in self.NOUNS.items():
                for noun in nouns:
                    task_name = f"{verb} {noun}"
                    tasks.append(
                        SeedTask(
                            source=self.source,
                            source_id=f"epic_{verb}_{noun}",
                            name=task_name,
                            domain="kitchen",
                            hierarchy_level=1,
                            verbs=[verb],
                            nouns=[noun],
                            tags=[noun_category],
                        )
                    )

        return tasks

    def get_subtasks(self, task_id: str) -> list[SeedTask]:
        """EPIC-KITCHENS doesn't have explicit subtasks."""
        return []


class ActivityNetLoader(BaseSeedLoader):
    """
    Load hierarchical action taxonomy from ActivityNet.

    Provides 203 action categories with parent-child relationships.

    Source: http://activity-net.org/
    """

    source = SeedSource.ACTIVITYNET

    # ActivityNet taxonomy (simplified)
    TAXONOMY = {
        "eating_drinking": {
            "name": "Eating and Drinking",
            "activities": [
                "drinking coffee",
                "eating a meal",
                "drinking beer",
                "eating ice cream",
                "eating cake",
            ],
        },
        "personal_care": {
            "name": "Personal Care",
            "activities": [
                "brushing teeth",
                "washing hands",
                "taking a shower",
                "applying makeup",
                "shaving",
                "blow drying hair",
            ],
        },
        "housework": {
            "name": "Housework",
            "activities": [
                "vacuuming floor",
                "mopping floor",
                "washing dishes",
                "doing laundry",
                "ironing clothes",
                "cleaning windows",
            ],
        },
        "sports": {
            "name": "Sports and Exercise",
            "activities": [
                "playing basketball",
                "playing soccer",
                "playing tennis",
                "running",
                "swimming",
                "cycling",
                "yoga",
                "weightlifting",
            ],
        },
        "music": {
            "name": "Playing Music",
            "activities": [
                "playing piano",
                "playing guitar",
                "playing drums",
                "playing violin",
                "singing",
            ],
        },
        "cooking": {
            "name": "Cooking",
            "activities": [
                "making a sandwich",
                "cooking pasta",
                "baking cookies",
                "grilling",
                "making coffee",
                "chopping vegetables",
            ],
        },
        "outdoor": {
            "name": "Outdoor Activities",
            "activities": [
                "gardening",
                "mowing lawn",
                "walking dog",
                "camping",
                "hiking",
                "fishing",
            ],
        },
        "social": {
            "name": "Social Activities",
            "activities": [
                "having a conversation",
                "giving a speech",
                "attending party",
                "dancing",
            ],
        },
    }

    def __init__(self, cache_dir: Path | str | None = None):
        super().__init__(cache_dir)

    def load(self) -> None:
        self._loaded = True

    def get_domains(self) -> list[SeedTask]:
        """Get ActivityNet categories as domains."""
        domains = []
        for cat_id, cat_data in self.TAXONOMY.items():
            domains.append(
                SeedTask(
                    source=self.source,
                    source_id=f"activitynet_{cat_id}",
                    name=cat_data["name"],
                    domain=cat_id,
                    hierarchy_level=0,
                    children_names=cat_data["activities"],
                )
            )
        return domains

    def get_tasks(self, domain: str | None = None) -> list[SeedTask]:
        """Get activities as tasks."""
        tasks = []
        for cat_id, cat_data in self.TAXONOMY.items():
            if domain and domain != cat_id:
                continue

            for activity in cat_data["activities"]:
                tasks.append(
                    SeedTask(
                        source=self.source,
                        source_id=f"activitynet_{cat_id}_{activity.replace(' ', '_')}",
                        name=activity,
                        domain=cat_id,
                        parent_name=cat_data["name"],
                        hierarchy_level=1,
                    )
                )
        return tasks

    def get_subtasks(self, task_id: str) -> list[SeedTask]:
        return []


# ============================================================================
# Seed Aggregator - Combines all loaders
# ============================================================================


class SeedAggregator:
    """
    Aggregates all seed data loaders into a unified interface.

    This is the main entry point for accessing seed data.
    """

    def __init__(self, cache_dir: Path | str | None = None):
        cache_path = Path(cache_dir) if cache_dir else Path.home() / ".praxis_cache"

        self.loaders = {
            SeedSource.ONET: ONetTaskLoader(cache_path),
            SeedSource.WIKIHOW: WikiHowLoader(cache_path),
            SeedSource.COIN: COINLoader(cache_path),
            SeedSource.EPIC_KITCHENS: EpicKitchensLoader(cache_path),
            SeedSource.ACTIVITYNET: ActivityNetLoader(cache_path),
        }

    def load_all(self) -> None:
        """Load all datasets."""
        for loader in self.loaders.values():
            try:
                loader.load()
            except Exception as e:
                print(f"Warning: Failed to load {loader.source}: {e}")

    def get_all_domains(self) -> list[SeedTask]:
        """Get domains from all sources."""
        domains = []
        for loader in self.loaders.values():
            try:
                domains.extend(loader.get_domains())
            except Exception as e:
                print(f"Warning: Failed to get domains from {loader.source}: {e}")
        return domains

    def get_all_tasks(self) -> list[SeedTask]:
        """Get tasks from all sources."""
        tasks = []
        for loader in self.loaders.values():
            try:
                tasks.extend(loader.get_tasks())
            except Exception as e:
                print(f"Warning: Failed to get tasks from {loader.source}: {e}")
        return tasks

    def get_tasks_by_source(self, source: SeedSource) -> list[SeedTask]:
        """Get tasks from a specific source."""
        loader = self.loaders.get(source)
        if loader:
            return loader.get_tasks()
        return []

    def iter_all(self) -> Iterator[SeedTask]:
        """Iterate over all seed tasks from all sources."""
        for loader in self.loaders.values():
            try:
                yield from loader.iter_all()
            except Exception as e:
                print(f"Warning: Failed to iterate {loader.source}: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about all loaded datasets."""
        stats = {}
        for source, loader in self.loaders.items():
            try:
                stats[source.value] = loader.get_stats()
            except Exception as e:
                stats[source.value] = {"error": str(e)}
        return stats
