#!/usr/bin/env python3
"""
Fast task generation - just high-level tasks, no subtasks.
Builds the hierarchy quickly across all verticals.
"""

import json
import os
import time
from pathlib import Path

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
MODEL = "gemini-2.5-flash"


def parse_json_array(text: str) -> list:
    """Robustly parse JSON array from LLM response."""
    text = text.strip()

    if "```json" in text:
        after_json = text.split("```json")[1]
        if "```" in after_json:
            text = after_json.split("```")[0].strip()
        else:
            text = after_json.strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1].strip()

    if "[" not in text:
        return []

    start = text.index("[")

    try:
        return json.loads(text[start:])
    except json.JSONDecodeError:
        pass

    # Handle truncated JSON
    last_complete = text.rfind("}")
    if last_complete > start:
        for end_pos in range(last_complete, start, -1):
            if text[end_pos] == "}":
                try:
                    candidate = text[start:end_pos + 1] + "]"
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
    return []


# Hierarchical structure for robotics tasks
HIERARCHY = {
    "household": {
        "name": "Household & Home",
        "description": "Tasks in residential environments",
        "subcategories": [
            "kitchen_tasks",
            "cleaning_tasks",
            "laundry_tasks",
            "organization_tasks",
            "maintenance_tasks",
            "outdoor_home_tasks",
            "elderly_care_tasks",
            "childcare_tasks",
        ]
    },
    "industrial": {
        "name": "Industrial & Manufacturing",
        "description": "Factory and production tasks",
        "subcategories": [
            "assembly_line_tasks",
            "welding_tasks",
            "material_handling",
            "quality_inspection",
            "machine_tending",
            "packaging_tasks",
            "painting_coating",
        ]
    },
    "warehouse": {
        "name": "Warehouse & Logistics",
        "description": "Storage and distribution tasks",
        "subcategories": [
            "picking_tasks",
            "packing_tasks",
            "palletizing_tasks",
            "inventory_tasks",
            "loading_unloading",
            "sorting_tasks",
        ]
    },
    "hospitality": {
        "name": "Hospitality & Food Service",
        "description": "Hotels, restaurants, and service tasks",
        "subcategories": [
            "food_preparation",
            "cooking_tasks",
            "serving_tasks",
            "table_service",
            "room_service",
            "housekeeping_hotel",
        ]
    },
    "healthcare": {
        "name": "Healthcare & Medical",
        "description": "Hospital and clinical tasks",
        "subcategories": [
            "patient_care_tasks",
            "medical_delivery",
            "lab_tasks",
            "surgical_assist",
            "rehabilitation_tasks",
            "pharmacy_tasks",
        ]
    },
    "agriculture": {
        "name": "Agriculture & Farming",
        "description": "Farming and crop management tasks",
        "subcategories": [
            "harvesting_tasks",
            "planting_tasks",
            "crop_monitoring",
            "irrigation_tasks",
            "livestock_tasks",
            "greenhouse_tasks",
        ]
    },
    "construction": {
        "name": "Construction & Building",
        "description": "Construction site tasks",
        "subcategories": [
            "bricklaying_tasks",
            "painting_construction",
            "material_transport",
            "site_inspection",
            "demolition_tasks",
        ]
    },
    "retail": {
        "name": "Retail & Commerce",
        "description": "Store and shopping tasks",
        "subcategories": [
            "shelf_stocking",
            "inventory_retail",
            "customer_assist",
            "checkout_tasks",
            "store_cleaning",
        ]
    },
    "delivery": {
        "name": "Delivery & Last-Mile",
        "description": "Package and food delivery tasks",
        "subcategories": [
            "package_delivery",
            "food_delivery",
            "mail_delivery",
        ]
    },
}


def generate_tasks(category: str, subcategory: str) -> list:
    """Generate tasks for a subcategory."""
    prompt = f"""Generate ALL physical tasks a robot would perform for: {subcategory.replace('_', ' ')}

Category: {category}

Rules:
- Every task must be PHYSICAL (manipulation, movement, observable action)
- Start each with action verb (pick, place, grasp, push, pull, wipe, scan, move, lift, etc.)
- Be specific and concrete
- Include common tasks and edge cases

Output as JSON: [{{"task": "action verb + specific object/target"}}]

Generate comprehensive list of tasks."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                max_output_tokens=4000,
            )
        )
        return parse_json_array(response.text)
    except Exception as e:
        print(f"      Error: {e}", flush=True)
        return []


def main():
    output_dir = Path("/home/sarthak/Taskpedia/hierarchy_data")
    output_dir.mkdir(exist_ok=True)

    print("=" * 70, flush=True)
    print("TASKPEDIA - Hierarchical Task Generation", flush=True)
    print("=" * 70, flush=True)

    all_data = {}
    total_tasks = 0

    for cat_key, cat_info in HIERARCHY.items():
        print(f"\n[{cat_info['name'].upper()}]", flush=True)

        cat_data = {
            "name": cat_info["name"],
            "description": cat_info["description"],
            "subcategories": {}
        }

        for subcat in cat_info["subcategories"]:
            print(f"  {subcat.replace('_', ' ')}...", end=" ", flush=True)

            tasks = generate_tasks(cat_info["name"], subcat)

            task_list = []
            for t in tasks:
                task_name = t.get("task", "")
                if task_name:
                    task_list.append(task_name)

            cat_data["subcategories"][subcat] = {
                "tasks": task_list
            }

            print(f"{len(task_list)} tasks", flush=True)
            total_tasks += len(task_list)
            time.sleep(0.2)

        all_data[cat_key] = cat_data

        # Save after each category
        with open(output_dir / "tasks_hierarchy.json", "w") as f:
            json.dump(all_data, f, indent=2)

    print(f"\n{'='*70}", flush=True)
    print(f"COMPLETE: {total_tasks} total tasks across {len(HIERARCHY)} categories", flush=True)
    print(f"Saved to: {output_dir / 'tasks_hierarchy.json'}", flush=True)


if __name__ == "__main__":
    main()
