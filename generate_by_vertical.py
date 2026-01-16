#!/usr/bin/env python3
"""
Generate Taskpedia organized by Robotics Company Verticals.

Instead of generic domains, we organize by real market segments
that robotics companies are building for.
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
    """Robustly parse JSON array from LLM response, handling truncation."""
    original = text
    text = text.strip()

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

    # If text is empty after extraction, try to find array directly
    if not text.strip() and "[" in original:
        text = original

    # Find JSON array boundaries
    if "[" not in text:
        return []

    start = text.index("[")

    # Try to parse as-is first
    try:
        return json.loads(text[start:])
    except json.JSONDecodeError:
        pass

    # If that fails, try to find complete JSON objects and truncate
    # Find the last complete object (ends with })
    last_complete = text.rfind("}")
    if last_complete > start:
        # Try progressively shorter substrings ending at }
        for end_pos in range(last_complete, start, -1):
            if text[end_pos] == "}":
                try:
                    candidate = text[start:end_pos + 1] + "]"
                    result = json.loads(candidate)
                    return result
                except json.JSONDecodeError:
                    continue

    return []


# =============================================================================
# ROBOTICS COMPANY VERTICALS
# =============================================================================
# Each vertical represents a real market segment with example companies
# and the environments/contexts where their robots operate.

VERTICALS = {
    "home_robotics": {
        "name": "Home Robotics",
        "description": "Robots for household tasks, elderly care, and daily living assistance",
        "example_companies": ["Sunder Robotics", "Figure", "1X Technologies", "Agility Robotics"],
        "environments": [
            "kitchen",
            "living room",
            "bedroom",
            "bathroom",
            "laundry room",
            "garage",
            "home office",
            "dining room",
            "backyard/patio",
            "entryway/mudroom",
        ],
        "user_contexts": [
            "elderly person living alone",
            "busy family with children",
            "person with mobility limitations",
            "working professional",
        ],
    },

    "warehouse_logistics": {
        "name": "Warehouse & Logistics",
        "description": "Robots for fulfillment centers, distribution, and last-mile delivery",
        "example_companies": ["Amazon Robotics", "Locus Robotics", "6 River Systems", "Fetch Robotics", "Boston Dynamics"],
        "environments": [
            "fulfillment center",
            "distribution warehouse",
            "cold storage facility",
            "cross-dock terminal",
            "sorting facility",
            "returns processing center",
            "loading dock",
            "inventory storage area",
        ],
        "operations": [
            "goods-to-person picking",
            "person-to-goods picking",
            "pallet handling",
            "case picking",
            "each picking",
            "putaway",
            "replenishment",
            "inventory counting",
            "shipping preparation",
        ],
    },

    "manufacturing": {
        "name": "Manufacturing & Assembly",
        "description": "Robots for factory automation, assembly lines, and production",
        "example_companies": ["Fanuc", "ABB", "KUKA", "Universal Robots", "Rethink Robotics"],
        "environments": [
            "automotive assembly line",
            "electronics manufacturing",
            "food processing plant",
            "pharmaceutical production",
            "metal fabrication shop",
            "plastics molding facility",
            "textile factory",
            "packaging line",
            "quality control station",
            "machine tending cell",
        ],
        "processes": [
            "component assembly",
            "welding",
            "painting/coating",
            "machine loading/unloading",
            "inspection",
            "packaging",
            "material handling",
            "dispensing/adhesive application",
        ],
    },

    "agriculture": {
        "name": "Agriculture & Farming",
        "description": "Robots for crop management, harvesting, and farm operations",
        "example_companies": ["John Deere", "Agrobot", "Iron Ox", "FarmWise", "Abundant Robotics"],
        "environments": [
            "open field crops",
            "greenhouse",
            "orchard",
            "vineyard",
            "vertical farm",
            "dairy farm",
            "poultry farm",
            "livestock operation",
            "nursery",
            "grain storage facility",
        ],
        "operations": [
            "planting/seeding",
            "harvesting",
            "weeding",
            "pruning",
            "spraying/fertilizing",
            "irrigation management",
            "crop monitoring",
            "animal feeding",
            "milking",
        ],
    },

    "healthcare": {
        "name": "Healthcare & Medical",
        "description": "Robots for hospitals, clinics, surgery, and patient care",
        "example_companies": ["Intuitive Surgical", "Diligent Robotics", "Aethon", "Savioke"],
        "environments": [
            "hospital room",
            "operating room",
            "pharmacy",
            "laboratory",
            "nursing station",
            "rehabilitation center",
            "elderly care facility",
            "clinic waiting room",
            "medical supply room",
            "sterilization area",
        ],
        "operations": [
            "patient transport assistance",
            "medication delivery",
            "supply delivery",
            "surgical assistance",
            "disinfection",
            "sample transport",
            "physical therapy assistance",
            "patient monitoring",
        ],
    },

    "food_service": {
        "name": "Food Service & Hospitality",
        "description": "Robots for restaurants, hotels, and food preparation",
        "example_companies": ["Miso Robotics", "Bear Robotics", "Starship Technologies", "Nuro"],
        "environments": [
            "commercial kitchen",
            "fast food restaurant",
            "hotel kitchen",
            "cafeteria",
            "coffee shop",
            "bar",
            "food truck",
            "catering facility",
            "hotel lobby",
            "room service",
        ],
        "operations": [
            "food preparation",
            "cooking",
            "plating",
            "serving",
            "bussing tables",
            "dishwashing",
            "inventory management",
            "food delivery",
        ],
    },

    "construction": {
        "name": "Construction & Infrastructure",
        "description": "Robots for building, demolition, and site work",
        "example_companies": ["Built Robotics", "Boston Dynamics", "Dusty Robotics", "Canvas"],
        "environments": [
            "construction site",
            "building interior (in progress)",
            "road construction",
            "bridge construction",
            "demolition site",
            "excavation site",
            "concrete pour area",
            "steel structure",
        ],
        "operations": [
            "bricklaying",
            "drywall installation",
            "painting",
            "welding structural steel",
            "concrete finishing",
            "site surveying",
            "material transport",
            "debris removal",
            "excavation",
        ],
    },

    "retail": {
        "name": "Retail & Customer Service",
        "description": "Robots for stores, inventory, and customer assistance",
        "example_companies": ["Simbe Robotics", "Bossa Nova", "Fellow Robots", "SoftBank Robotics"],
        "environments": [
            "grocery store",
            "department store",
            "electronics store",
            "pharmacy",
            "warehouse club",
            "convenience store",
            "shopping mall",
            "stockroom",
        ],
        "operations": [
            "shelf scanning",
            "inventory counting",
            "price verification",
            "out-of-stock detection",
            "customer guidance",
            "floor cleaning",
            "restocking shelves",
            "cart retrieval",
        ],
    },

    "cleaning_maintenance": {
        "name": "Cleaning & Facility Maintenance",
        "description": "Robots for commercial cleaning and building maintenance",
        "example_companies": ["Brain Corp", "Avidbots", "iRobot", "Gaussian Robotics"],
        "environments": [
            "office building",
            "airport terminal",
            "shopping mall",
            "hospital",
            "school",
            "hotel",
            "convention center",
            "sports stadium",
            "parking garage",
        ],
        "operations": [
            "floor scrubbing",
            "vacuuming",
            "window cleaning",
            "restroom cleaning",
            "trash collection",
            "disinfection",
            "carpet cleaning",
            "outdoor sweeping",
        ],
    },

    "security_surveillance": {
        "name": "Security & Surveillance",
        "description": "Robots for patrol, monitoring, and security operations",
        "example_companies": ["Knightscope", "Cobalt Robotics", "Turing Video"],
        "environments": [
            "corporate campus",
            "parking lot",
            "data center",
            "warehouse",
            "shopping center",
            "residential community",
            "airport",
            "industrial facility",
        ],
        "operations": [
            "patrol routes",
            "perimeter monitoring",
            "visitor check-in",
            "anomaly detection",
            "license plate reading",
            "thermal scanning",
            "access point monitoring",
            "incident documentation",
        ],
    },

    "oil_gas_energy": {
        "name": "Oil, Gas & Energy",
        "description": "Robots for inspection, maintenance, and hazardous environments",
        "example_companies": ["ANYbotics", "ExRobotics", "Sarcos", "Oceaneering"],
        "environments": [
            "oil rig platform",
            "refinery",
            "pipeline corridor",
            "power plant",
            "solar farm",
            "wind turbine",
            "substation",
            "tank farm",
            "offshore platform",
        ],
        "operations": [
            "visual inspection",
            "thermal imaging",
            "gas leak detection",
            "valve operation",
            "gauge reading",
            "corrosion monitoring",
            "equipment maintenance",
            "emergency response",
        ],
    },

    "mining": {
        "name": "Mining & Extraction",
        "description": "Robots for underground and surface mining operations",
        "example_companies": ["Caterpillar", "Komatsu", "Sandvik", "Rio Tinto"],
        "environments": [
            "underground mine",
            "open pit mine",
            "processing plant",
            "ore stockpile",
            "conveyor system",
            "crushing facility",
            "tailings area",
            "mine shaft",
        ],
        "operations": [
            "drilling",
            "blasting preparation",
            "ore extraction",
            "material hauling",
            "rock bolting",
            "surveying/mapping",
            "ventilation maintenance",
            "equipment inspection",
        ],
    },

    "marine_underwater": {
        "name": "Marine & Underwater",
        "description": "Robots for underwater inspection, maintenance, and exploration",
        "example_companies": ["Oceaneering", "Saab Seaeye", "ECA Group", "Deep Trekker"],
        "environments": [
            "ship hull",
            "underwater pipeline",
            "offshore platform legs",
            "dam structure",
            "port infrastructure",
            "aquaculture pen",
            "coral reef",
            "shipwreck",
        ],
        "operations": [
            "hull inspection",
            "pipeline inspection",
            "cleaning/scrubbing",
            "cutting/welding",
            "sample collection",
            "structure measurement",
            "debris removal",
            "cable/rope work",
        ],
    },

    "last_mile_delivery": {
        "name": "Last-Mile Delivery",
        "description": "Robots for package and food delivery to end consumers",
        "example_companies": ["Starship Technologies", "Nuro", "Amazon Scout", "Kiwibot"],
        "environments": [
            "residential sidewalk",
            "apartment complex",
            "office building lobby",
            "college campus",
            "suburban neighborhood",
            "urban street",
            "hotel",
            "hospital",
        ],
        "operations": [
            "package pickup",
            "route navigation",
            "obstacle avoidance",
            "customer notification",
            "secure compartment access",
            "package handoff",
            "return to base",
            "charging station docking",
        ],
    },
}


def generate_tasks_for_environment(vertical_name: str, vertical_info: dict, environment: str):
    """Generate all relevant tasks for a specific environment within a vertical."""

    prompt = f"""You are creating a comprehensive task database for robotics companies building autonomous robots.

VERTICAL: {vertical_info['name']}
DESCRIPTION: {vertical_info['description']}
EXAMPLE COMPANIES: {', '.join(vertical_info['example_companies'])}

SPECIFIC ENVIRONMENT: {environment}

Generate ALL physical tasks a robot could perform in this environment. Be exhaustive - think about:
- What would a human worker do here that a robot could automate?
- What are the repetitive physical actions?
- What are the manipulation tasks (grasping, placing, moving objects)?
- What are the navigation/mobility tasks?
- What are the inspection/monitoring tasks?
- What cleaning or maintenance tasks exist?

Rules:
- Every task must be a PHYSICAL action (observable, involves movement or manipulation)
- Start each task with an action verb (pick, place, move, grasp, push, pull, wipe, scan, etc.)
- Be specific to this exact environment
- Include both common and edge-case tasks
- Do NOT include mental tasks (decide, plan, analyze, think)

Output as JSON array: [{{"task": "verb + specific action in this environment"}}]

Be comprehensive. Include every task you can think of."""

    response = None
    try:
        print(f"    Calling API...", flush=True)
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                max_output_tokens=4000,
            )
        )
        print(f"    Got response", flush=True)

        text = response.text
        print(f"    Text extracted, length: {len(text)}", flush=True)

        if not text or not text.strip():
            print(f"    Warning: Empty API response", flush=True)
            return []

        result = parse_json_array(text)
        print(f"    Parsed {len(result)} tasks", flush=True)
        return result
    except Exception as e:
        import traceback
        print(f"    Error: {e}", flush=True)
        print(f"    Traceback: {traceback.format_exc()}", flush=True)
        if response and hasattr(response, 'text') and response.text:
            print(f"    Response preview: {response.text[:200]}", flush=True)
        return []


def generate_subtasks(task_name: str, environment: str, vertical_name: str):
    """Generate subtasks for a task - no fixed numbers."""

    prompt = f"""Break down this robot task into its sequential physical steps.

TASK: {task_name}
ENVIRONMENT: {environment}
VERTICAL: {vertical_name}

Generate the sequential physical steps a robot would perform to complete this task.
Each step should be:
- A specific physical action
- Part of a logical sequence
- Observable and executable by a robot

Output as JSON array: [{{"step": "physical action"}}]

Include all necessary steps from start to finish."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2000,
            )
        )

        return parse_json_array(response.text)
    except Exception as e:
        return []


def generate_atomic_actions(subtask_name: str, context: str):
    """Generate atomic robot primitives for a subtask."""

    prompt = f"""Break down this subtask into atomic robot primitives.

SUBTASK: {subtask_name}
CONTEXT: {context}

Atomic primitives are the smallest executable robot actions:
- move_to(location)
- grasp(object)
- release(object)
- rotate(direction, degrees)
- push(object, direction)
- pull(object, direction)
- lift(object)
- lower(object)
- slide(object, direction)
- press(button/surface)
- turn(handle/knob)
- open(door/lid/container)
- close(door/lid/container)
- align(object, target)
- insert(object, slot)
- extract(object, slot)

Output as JSON array: [{{"action": "primitive(parameters)"}}]"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.6,
                max_output_tokens=1500,
            )
        )

        return parse_json_array(response.text)
    except Exception as e:
        return []


def main():
    import sys

    output_dir = Path("/home/sarthak/Taskpedia/verticals")
    output_dir.mkdir(exist_ok=True)

    print("=" * 70, flush=True)
    print("TASKPEDIA - Generation by Robotics Verticals", flush=True)
    print("=" * 70, flush=True)
    print(f"\nTotal verticals: {len(VERTICALS)}", flush=True)

    # Accept command line argument or default to home_robotics
    vertical_keys = list(VERTICALS.keys())

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "all":
            selected_verticals = list(VERTICALS.items())
        elif arg in VERTICALS:
            selected_verticals = [(arg, VERTICALS[arg])]
        elif arg.isdigit():
            idx = int(arg) - 1
            selected_verticals = [list(VERTICALS.items())[idx]]
        else:
            print(f"Unknown vertical: {arg}")
            print(f"Available: {', '.join(vertical_keys)}")
            return
    else:
        # Default to home_robotics
        selected_verticals = [("home_robotics", VERTICALS["home_robotics"])]

    total_tasks = 0

    for vertical_key, vertical_info in selected_verticals:
        print(f"\n{'='*60}", flush=True)
        print(f"VERTICAL: {vertical_info['name']}", flush=True)
        print(f"{'='*60}", flush=True)

        vertical_data = {
            "vertical": vertical_key,
            "name": vertical_info["name"],
            "description": vertical_info["description"],
            "example_companies": vertical_info["example_companies"],
            "environments": {}
        }

        environments = vertical_info.get("environments", [])

        for env_idx, environment in enumerate(environments, 1):
            print(f"\n  [{env_idx}/{len(environments)}] Environment: {environment}", flush=True)

            # Generate tasks for this environment
            tasks = generate_tasks_for_environment(vertical_key, vertical_info, environment)

            if not tasks:
                print(f"    -> 0 tasks", flush=True)
                continue

            print(f"    -> {len(tasks)} tasks generated", flush=True)
            total_tasks += len(tasks)

            env_data = {
                "environment": environment,
                "tasks": []
            }

            # For each task, generate subtasks
            for task in tasks[:20]:  # Limit for initial run
                task_name = task.get("task", "")
                if not task_name:
                    continue

                task_entry = {
                    "task": task_name,
                    "subtasks": []
                }

                subtasks = generate_subtasks(task_name, environment, vertical_info["name"])

                for st in subtasks:
                    step = st.get("step", "")
                    if step:
                        task_entry["subtasks"].append({"step": step})

                env_data["tasks"].append(task_entry)
                time.sleep(0.1)

            vertical_data["environments"][environment] = env_data
            time.sleep(0.2)

        # Save vertical data
        output_file = output_dir / f"{vertical_key}.json"
        with open(output_file, "w") as f:
            json.dump(vertical_data, f, indent=2)

        print(f"\n  Saved to: {output_file}", flush=True)

    print(f"\n{'='*60}", flush=True)
    print("GENERATION COMPLETE", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"Total tasks generated: {total_tasks}", flush=True)


if __name__ == "__main__":
    main()
