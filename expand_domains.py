#!/usr/bin/env python3
"""
Domain Expansion Script for TASKPEDIA

Uses Gemini to generate comprehensive robot task domains and decompose them.
"""

import json
import os
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
MODEL = "gemini-2.5-flash"

def parse_json_safely(text: str):
    """Parse JSON with fallback for truncated responses."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to fix truncated arrays
        if text.startswith("["):
            # Find last complete object
            depth = 0
            last_complete = 0
            in_string = False
            escape = False

            for i, c in enumerate(text):
                if escape:
                    escape = False
                    continue
                if c == '\\':
                    escape = True
                    continue
                if c == '"' and not escape:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        last_complete = i + 1

            if last_complete > 0:
                truncated = text[:last_complete] + "]"
                return json.loads(truncated)
        raise


def generate_domains():
    """Generate comprehensive list of robot deployment domains."""

    prompt = """Generate 40 domains where robots physically assist humans.

Output JSON array. Each domain:
{"id": "snake_case", "name": "Name", "category": "industrial|commercial|residential|healthcare|hospitality|agriculture|construction|transportation|retail|entertainment", "description": "Brief desc"}

Cover: manufacturing, warehouses, retail, restaurants, hotels, hospitals, homes, offices, farms, construction, airports, schools, gyms, events, automotive, labs, kitchens, laundry, cleaning, security, delivery, elderly care, childcare, pet care, gardening, maintenance, repair, recycling, food processing, textile, pharmaceutical, electronics assembly, vehicle assembly, mining, oil/gas, renewable energy, data centers, museums, theaters, stadiums.

Output ONLY valid JSON array."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=4000,
        )
    )

    return parse_json_safely(response.text)


def generate_tasks_for_domain(domain: dict):
    """Generate physical tasks for a domain."""

    prompt = f"""You are an expert in robotics task decomposition.

Domain: {domain['name']}
Description: {domain['description']}
Category: {domain['category']}

Generate a comprehensive list of PHYSICAL tasks a robot would perform in this domain.

Rules:
- Tasks must be PHYSICAL and OBSERVABLE (not mental, planning, or communication-only)
- Each task should start with an action verb (pick, place, move, clean, assemble, etc.)
- Tasks should be specific enough to decompose into sub-tasks
- Include both common and edge-case tasks

Output a JSON array of tasks:
[
  {{"id": "task_id", "name": "Task name starting with verb", "description": "Brief description"}}
]

Generate 15-30 distinct physical tasks. Output ONLY valid JSON array."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=4000,
        )
    )

    return parse_json_safely(response.text)


def generate_subtasks(domain: dict, task: dict):
    """Generate subtasks for a task."""

    prompt = f"""Decompose this robot task into sequential subtasks.

Domain: {domain['name']}
Task: {task['name']}

Break this task into 3-8 sequential subtasks that a robot would perform.
Each subtask should:
- Start with a physical action verb
- Be specific and executable
- Lead to the next subtask logically

Output JSON array:
[
  {{"id": "subtask_id", "name": "Subtask name", "order": 1}}
]

Output ONLY valid JSON array."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.6,
            max_output_tokens=2000,
        )
    )

    return parse_json_safely(response.text)


def generate_atomic_actions(domain: dict, task: dict, subtask: dict):
    """Generate atomic actions for a subtask."""

    prompt = f"""Decompose this subtask into atomic robot actions.

Domain: {domain['name']}
Task: {task['name']}
Subtask: {subtask['name']}

Generate 2-5 atomic actions. Atomic actions are the smallest physical primitives:
- Manipulation: grasp, release, pick_up, place, push, pull, rotate, press, insert
- Locomotion: walk_to, approach, step, turn
- Perception: look_at, scan, inspect
- Communication: say, signal

Output JSON array:
[
  {{"name": "atomic_action object/target"}}
]

Examples:
- "grasp door_handle"
- "walk_to kitchen_counter"
- "press power_button"
- "place item on shelf"

Output ONLY valid JSON array."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.5,
            max_output_tokens=1000,
        )
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    return json.loads(text)


def main():
    output_dir = Path("/home/sarthak/Taskpedia/generated_domains")
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("TASKPEDIA DOMAIN EXPANSION")
    print("=" * 60)

    # Step 1: Generate domains
    print("\n[1/4] Generating comprehensive domain list...")
    domains = generate_domains()
    print(f"      Generated {len(domains)} domains")

    # Save domains
    with open(output_dir / "domains.json", "w") as f:
        json.dump(domains, f, indent=2)

    # Show domains
    print("\n      Domains by category:")
    by_category = {}
    for d in domains:
        cat = d.get("category", "other")
        by_category.setdefault(cat, []).append(d["name"])
    for cat, names in sorted(by_category.items()):
        print(f"        {cat}: {len(names)}")

    # Step 2: Generate tasks for each domain
    print("\n[2/4] Generating tasks for each domain...")
    all_tasks = {}

    for i, domain in enumerate(domains):
        print(f"      [{i+1}/{len(domains)}] {domain['name']}...", end=" ", flush=True)
        try:
            tasks = generate_tasks_for_domain(domain)
            all_tasks[domain["id"]] = {
                "domain": domain,
                "tasks": tasks
            }
            print(f"{len(tasks)} tasks")
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"ERROR: {e}")
            continue

    # Save tasks
    with open(output_dir / "tasks.json", "w") as f:
        json.dump(all_tasks, f, indent=2)

    total_tasks = sum(len(v["tasks"]) for v in all_tasks.values())
    print(f"\n      Total tasks: {total_tasks}")

    # Step 3: Generate subtasks (sample for now)
    print("\n[3/4] Generating subtasks (first 10 domains)...")
    all_subtasks = {}

    for domain_id, data in list(all_tasks.items())[:10]:
        domain = data["domain"]
        print(f"      {domain['name']}:")

        for task in data["tasks"][:5]:  # First 5 tasks per domain
            print(f"        - {task['name']}...", end=" ", flush=True)
            try:
                subtasks = generate_subtasks(domain, task)
                key = f"{domain_id}/{task['id']}"
                all_subtasks[key] = {
                    "domain": domain,
                    "task": task,
                    "subtasks": subtasks
                }
                print(f"{len(subtasks)} subtasks")
                time.sleep(0.3)
            except Exception as e:
                print(f"ERROR: {e}")

    # Save subtasks
    with open(output_dir / "subtasks.json", "w") as f:
        json.dump(all_subtasks, f, indent=2)

    # Step 4: Generate atomic actions (sample)
    print("\n[4/4] Generating atomic actions (sample)...")
    all_atomics = []

    for key, data in list(all_subtasks.items())[:5]:
        for subtask in data["subtasks"][:3]:
            print(f"        {subtask['name']}...", end=" ", flush=True)
            try:
                atomics = generate_atomic_actions(data["domain"], data["task"], subtask)
                all_atomics.append({
                    "path": f"{key}/{subtask['id']}",
                    "domain": data["domain"]["name"],
                    "task": data["task"]["name"],
                    "subtask": subtask["name"],
                    "atomics": atomics
                })
                print(f"{len(atomics)} atomics")
                time.sleep(0.2)
            except Exception as e:
                print(f"ERROR: {e}")

    # Save atomics
    with open(output_dir / "atomics.json", "w") as f:
        json.dump(all_atomics, f, indent=2)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Domains:  {len(domains)}")
    print(f"  Tasks:    {total_tasks}")
    print(f"  Subtasks: {sum(len(v['subtasks']) for v in all_subtasks.values())}")
    print(f"  Atomics:  {sum(len(a['atomics']) for a in all_atomics)}")
    print(f"\n  Output:   {output_dir}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
