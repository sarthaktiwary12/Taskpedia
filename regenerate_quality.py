#!/usr/bin/env python3
"""
Regenerate tasks using improved prompts that focus on physical manipulation.
"""

import json
import os
import re
import time
from pathlib import Path
import google.generativeai as genai

from improved_prompts import get_improved_prompt

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash")

# Categories and subcategories to generate for
CATEGORIES = {
    "household": [
        "kitchen_tasks",
        "laundry_care",
        "cleaning_tasks",
        "organization",
        "appliance_operation",
    ],
    "industrial": [
        "assembly_operations",
        "tool_handling",
        "material_positioning",
        "quality_inspection",
        "packaging",
    ],
    "warehouse": [
        "picking_operations",
        "packing_tasks",
        "labeling",
        "box_assembly",
        "pallet_building",
    ],
    "agriculture": [
        "harvesting",
        "pruning",
        "planting",
        "irrigation_setup",
        "crop_maintenance",
    ],
    "healthcare": [
        "instrument_handling",
        "supply_preparation",
        "patient_care_physical",
        "equipment_setup",
        "sterile_technique",
    ],
    "food_service": [
        "ingredient_prep",
        "cooking_operations",
        "plating",
        "equipment_cleaning",
        "food_assembly",
    ],
    "construction": [
        "tool_operations",
        "material_handling",
        "fastening_tasks",
        "measuring_marking",
        "surface_finishing",
    ],
    "retail": [
        "stocking_shelves",
        "price_tagging",
        "display_arrangement",
        "inventory_handling",
        "checkout_assistance",
    ],
}


def parse_json_array(text: str) -> list:
    """Robustly parse JSON array from LLM response."""
    # Remove markdown code blocks
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

    text = text.strip()

    # Try direct parse
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Handle truncation - find last complete object
    if text.startswith("["):
        last_complete = text.rfind("},")
        if last_complete > 0:
            truncated = text[:last_complete + 1] + "]"
            try:
                result = json.loads(truncated)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        # Try finding last complete object with }]
        last_bracket = text.rfind("}]")
        if last_bracket > 0:
            truncated = text[:last_bracket + 2]
            try:
                result = json.loads(truncated)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

    # Fallback: extract individual task strings
    tasks = []
    pattern = r'"task"\s*:\s*"([^"]+)"'
    matches = re.findall(pattern, text)
    for match in matches:
        tasks.append({"task": match})

    return tasks


def generate_tasks(category: str, subcategory: str, count: int = 25) -> list:
    """Generate tasks for a category/subcategory using improved prompts."""
    prompt = get_improved_prompt(category, subcategory, count)

    try:
        response = model.generate_content(prompt)
        tasks = parse_json_array(response.text)
        return tasks
    except Exception as e:
        print(f"  Error generating: {e}")
        return []


def main():
    output_path = Path("/home/sarthak/Taskpedia/hierarchy_data/quality_tasks.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_data = {}
    total_tasks = 0

    print("=" * 60)
    print("REGENERATING QUALITY TASKS")
    print("=" * 60)

    for category, subcategories in CATEGORIES.items():
        print(f"\n[{category.upper()}]")
        all_data[category] = {
            "name": category.replace("_", " ").title(),
            "subcategories": {}
        }

        for subcat in subcategories:
            print(f"  Generating {subcat}...", end=" ", flush=True)

            tasks = generate_tasks(category, subcat, count=25)
            task_names = [t.get("task", "") for t in tasks if t.get("task")]

            all_data[category]["subcategories"][subcat] = {
                "tasks": task_names
            }

            total_tasks += len(task_names)
            print(f"{len(task_names)} tasks")

            # Rate limiting
            time.sleep(0.5)

    # Save to file
    with open(output_path, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\n{'=' * 60}")
    print("GENERATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Total tasks: {total_tasks}")
    print(f"  Saved to: {output_path}")

    # Show sample of generated tasks
    print(f"\n{'=' * 60}")
    print("SAMPLE QUALITY TASKS")
    print(f"{'=' * 60}")
    for cat, data in list(all_data.items())[:3]:
        print(f"\n[{cat}]")
        for subcat, subdata in list(data["subcategories"].items())[:2]:
            print(f"  {subcat}:")
            for task in subdata["tasks"][:3]:
                print(f"    - {task}")


if __name__ == "__main__":
    main()
