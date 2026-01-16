#!/usr/bin/env python3
"""
Deepen Taskpedia hierarchy by adding subtasks and atomic actions.
"""

import json
import os
import time
import random
from pathlib import Path

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
MODEL = "gemini-2.5-flash"

def generate_subtasks(task_name: str, domain_name: str):
    """Generate subtasks for a task."""
    prompt = f"""Break down this physical task into 4-6 sequential subtasks:

Task: {task_name}
Domain: {domain_name}

Rules:
- Each subtask must be a PHYSICAL action (manipulation, movement, not mental)
- Start each with action verb (grasp, move, position, align, insert, press, etc.)
- Subtasks should be sequential steps to complete the main task
- Be specific and concrete

Output JSON array: [{{"name": "verb + specific action"}}]
Example: [{{"name": "grasp handle with right gripper"}}, {{"name": "pull door toward body"}}]

Output ONLY valid JSON array."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1500,
            )
        )

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()

        return json.loads(text)
    except:
        return []


def generate_atomics(subtask_name: str, task_context: str):
    """Generate atomic actions for a subtask."""
    prompt = f"""Break down this subtask into 2-4 atomic robot actions:

Subtask: {subtask_name}
Context: {task_context}

Rules:
- Atomic actions are the SMALLEST physical movements a robot can execute
- Use verbs like: grasp, release, move_to, rotate, push, pull, lift, lower, align, insert, press, turn, slide
- Each atomic should take 1-3 seconds to execute
- Be very specific about the motion

Output JSON array: [{{"name": "atomic_verb + target"}}]
Example: [{{"name": "move_gripper_to handle_position"}}, {{"name": "close_gripper on handle"}}]

Output ONLY valid JSON array."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1000,
            )
        )

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()

        return json.loads(text)
    except:
        return []


def main():
    manifest_path = Path("/home/sarthak/Taskpedia/taskpedia-web/public/data/manifest.json")

    with open(manifest_path) as f:
        manifest = json.load(f)

    print("=" * 60)
    print("DEEPENING HIERARCHY - Subtasks & Atomic Actions")
    print("=" * 60)
    print(f"Starting with {len(manifest)} nodes")

    # Build existing names set for deduplication
    existing_names = set()
    for node in manifest.values():
        existing_names.add(node.get("name", "").lower().strip())

    # Find tasks that have no children (leaf tasks needing subtasks)
    tasks_needing_subtasks = []
    for node_id, node in manifest.items():
        if node.get("node_type") == "task" and not node.get("children_ids"):
            tasks_needing_subtasks.append((node_id, node))

    # Find subtasks that have no children (needing atomics)
    subtasks_needing_atomics = []
    for node_id, node in manifest.items():
        if node.get("node_type") == "subtask" and not node.get("children_ids"):
            subtasks_needing_atomics.append((node_id, node))

    print(f"Tasks needing subtasks: {len(tasks_needing_subtasks)}")
    print(f"Subtasks needing atomics: {len(subtasks_needing_atomics)}")

    # Shuffle and limit to process in batches
    random.shuffle(tasks_needing_subtasks)
    random.shuffle(subtasks_needing_atomics)

    # Process up to 500 tasks for subtasks
    tasks_to_process = tasks_needing_subtasks[:500]
    subtasks_to_process = subtasks_needing_atomics[:500]

    added_subtasks = 0
    added_atomics = 0

    # PHASE 1: Add subtasks to tasks
    print(f"\n[PHASE 1] Adding subtasks to {len(tasks_to_process)} tasks...")

    for i, (task_id, task) in enumerate(tasks_to_process):
        task_name = task.get("name", "")
        parent_id = task.get("parent_id", "")
        domain_name = manifest.get(parent_id, {}).get("name", "unknown")

        print(f"  [{i+1}/{len(tasks_to_process)}] {task_name[:50]}...", end=" ", flush=True)

        try:
            subtasks = generate_subtasks(task_name, domain_name)

            if not subtasks:
                print("0 subtasks")
                continue

            count = 0
            for st in subtasks:
                st_name = st.get("name", "")
                if not st_name or st_name.lower().strip() in existing_names:
                    continue

                st_id = f"{task_id}/{st_name.lower().replace(' ', '_')[:40]}"
                if st_id in manifest:
                    continue

                subtask_node = {
                    "id": st_id,
                    "name": st_name,
                    "node_type": "subtask",
                    "parent_id": task_id,
                    "children_ids": []
                }

                manifest[st_id] = subtask_node
                manifest[task_id]["children_ids"].append(st_id)
                existing_names.add(st_name.lower().strip())
                added_subtasks += 1
                count += 1

            print(f"{count} subtasks")
            time.sleep(0.15)

        except Exception as e:
            print(f"ERROR: {e}")
            continue

    print(f"\nPhase 1 complete. Added {added_subtasks} subtasks")

    # Refresh subtasks needing atomics (include newly added ones)
    subtasks_needing_atomics = []
    for node_id, node in manifest.items():
        if node.get("node_type") == "subtask" and not node.get("children_ids"):
            subtasks_needing_atomics.append((node_id, node))

    random.shuffle(subtasks_needing_atomics)
    subtasks_to_process = subtasks_needing_atomics[:800]

    # PHASE 2: Add atomics to subtasks
    print(f"\n[PHASE 2] Adding atomics to {len(subtasks_to_process)} subtasks...")

    for i, (subtask_id, subtask) in enumerate(subtasks_to_process):
        subtask_name = subtask.get("name", "")
        parent_id = subtask.get("parent_id", "")
        task_name = manifest.get(parent_id, {}).get("name", "unknown")

        print(f"  [{i+1}/{len(subtasks_to_process)}] {subtask_name[:45]}...", end=" ", flush=True)

        try:
            atomics = generate_atomics(subtask_name, task_name)

            if not atomics:
                print("0 atomics")
                continue

            count = 0
            for at in atomics:
                at_name = at.get("name", "")
                if not at_name or at_name.lower().strip() in existing_names:
                    continue

                at_id = f"{subtask_id}/{at_name.lower().replace(' ', '_')[:40]}"
                if at_id in manifest:
                    continue

                atomic_node = {
                    "id": at_id,
                    "name": at_name,
                    "node_type": "atomic",
                    "parent_id": subtask_id,
                    "children_ids": []
                }

                manifest[at_id] = atomic_node
                manifest[subtask_id]["children_ids"].append(at_id)
                existing_names.add(at_name.lower().strip())
                added_atomics += 1
                count += 1

            print(f"{count} atomics")
            time.sleep(0.15)

        except Exception as e:
            print(f"ERROR: {e}")
            continue

    print(f"\nPhase 2 complete. Added {added_atomics} atomics")

    # Save manifest
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Update stats
    types = {"domain": 0, "task": 0, "subtask": 0, "atomic": 0}
    for node in manifest.values():
        t = node.get("node_type", "")
        if t in types:
            types[t] += 1

    stats = {
        "trainable": {
            "total": len(manifest),
            "by_type": types
        },
        "non_trainable": {"total": 1609},
        "ambiguous": {"total": 484}
    }

    with open("/home/sarthak/Taskpedia/taskpedia-web/public/data/stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print("\n" + "=" * 60)
    print("DEEPENING COMPLETE")
    print("=" * 60)
    print(f"  New subtasks:  {added_subtasks}")
    print(f"  New atomics:   {added_atomics}")
    print(f"  TOTAL ADDED:   {added_subtasks + added_atomics}")
    print(f"\n  Final manifest: {len(manifest)} nodes")
    print(f"\n  By type:")
    for t, c in types.items():
        print(f"    {t}: {c:,}")


if __name__ == "__main__":
    main()
