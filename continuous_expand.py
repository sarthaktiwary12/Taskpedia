#!/usr/bin/env python3
"""
Continuous expansion - adds domains, tasks, subtasks, and atomic actions.
Deduplicates and ensures physical/robot-executable tasks only.
"""

import json
import os
import time
import re
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
MODEL = "gemini-2.5-flash"

MANIFEST_PATH = Path("/home/sarthak/Taskpedia/taskpedia-web/public/data/manifest.json")

# More categories to add
MORE_CATEGORIES = {
    "maritime": [
        "ship deck operations", "cargo ship loading", "fishing vessel operations",
        "cruise ship housekeeping", "port container handling", "marine equipment maintenance",
        "boat cleaning and detailing", "dock line handling", "anchor handling",
        "lifeboat maintenance", "ship painting", "hull cleaning",
    ],
    "aviation": [
        "aircraft cleaning interior", "aircraft cleaning exterior", "baggage loading aircraft",
        "cargo loading aircraft", "aircraft catering", "runway debris removal",
        "aircraft de-icing", "aircraft refueling assistance", "aircraft towing",
        "luggage cart operations", "jet bridge operations",
    ],
    "mining": [
        "ore sorting", "equipment maintenance underground", "material transport mining",
        "drilling assistance", "blasting preparation", "ventilation maintenance",
        "conveyor belt maintenance", "rock bolting", "shotcreting",
    ],
    "textile_detailed": [
        "fabric cutting", "sewing machine operation", "garment pressing",
        "button attachment", "zipper installation", "quality inspection garments",
        "fabric folding", "thread trimming", "label attachment",
        "packaging garments", "pattern laying",
    ],
    "printing": [
        "paper loading", "ink cartridge replacement", "print quality inspection",
        "paper cutting", "binding operations", "laminating", "collating",
        "packaging printed materials", "press cleaning", "roller maintenance",
    ],
    "beverage_production": [
        "bottle washing", "bottle filling", "capping operations",
        "labeling bottles", "case packing", "keg handling",
        "quality sampling", "tank cleaning", "ingredient mixing",
        "pasteurization monitoring", "cold room stocking",
    ],
    "meat_processing": [
        "carcass handling", "meat cutting", "deboning",
        "grinding operations", "sausage making", "packaging meat",
        "cold storage handling meat", "sanitation meat facility",
        "quality inspection meat", "marinating",
    ],
    "bakery_detailed": [
        "dough mixing", "dough kneading", "dough shaping",
        "bread loading oven", "bread unloading oven", "cooling rack handling",
        "bread slicing", "packaging bread", "decorating pastries",
        "filling pastries", "glazing", "proofing tray handling",
    ],
    "dairy_processing": [
        "milk tank handling", "cheese cutting", "cheese packaging",
        "yogurt filling", "butter packaging", "ice cream production",
        "quality testing dairy", "pasteurization operations", "cold chain handling dairy",
    ],
    "furniture_manufacturing": [
        "wood cutting", "wood sanding", "assembly furniture",
        "upholstery work", "finishing wood", "hardware installation furniture",
        "packaging furniture", "quality inspection furniture", "veneer application",
    ],
    "glass_manufacturing": [
        "glass cutting", "glass polishing", "glass tempering handling",
        "window assembly", "glass inspection", "glass packaging",
        "glass loading kiln", "glass unloading kiln",
    ],
    "ceramics": [
        "clay preparation", "pottery wheel operation", "glazing ceramics",
        "kiln loading ceramics", "kiln unloading ceramics", "quality inspection ceramics",
        "packaging ceramics", "tile cutting", "tile laying preparation",
    ],
    "recycling": [
        "sorting recyclables", "baling operations", "crushing cans",
        "shredding paper", "plastic sorting", "glass sorting",
        "e-waste disassembly", "metal sorting", "contamination removal",
        "compacting materials", "loading recycled materials",
    ],
    "waste_management": [
        "bin collection", "dumpster emptying", "street sweeping",
        "litter picking", "hazardous waste handling", "composting operations",
        "landfill operations", "waste compaction", "bin cleaning",
    ],
    "solar_energy": [
        "solar panel installation", "solar panel cleaning", "wiring solar systems",
        "inverter installation", "mounting structure assembly", "panel inspection",
        "roof preparation solar", "cable management solar",
    ],
    "wind_energy": [
        "turbine blade inspection", "nacelle maintenance", "tower climbing assistance",
        "bolt tightening turbine", "lubrication wind turbine", "cable handling wind",
    ],
    "water_treatment": [
        "filter replacement water", "chemical dosing", "sludge handling",
        "pump maintenance water", "valve operation water", "tank cleaning water",
        "sample collection water", "pipe maintenance water",
    ],
    "laundromat": [
        "loading washing machines", "unloading washing machines", "loading dryers",
        "unloading dryers", "folding laundry commercial", "sorting laundry commercial",
        "dry cleaning handling", "pressing clothes commercial", "stain treatment",
        "packaging cleaned clothes",
    ],
    "pet_services": [
        "pet bathing", "pet grooming brushing", "nail trimming pets",
        "pet drying", "cage cleaning pets", "feeding pets commercial",
        "walking dogs", "pet waste cleanup", "aquarium maintenance",
        "terrarium maintenance",
    ],
    "salon_spa": [
        "hair washing", "towel handling salon", "station cleaning salon",
        "tool sterilization salon", "product restocking salon", "laundry salon",
        "massage table preparation", "hot stone handling", "facial preparation",
    ],
    "dental_clinic": [
        "instrument sterilization dental", "chair preparation dental",
        "supply restocking dental", "x-ray positioning", "impression handling",
        "tool passing dental", "suction operation", "cleanup dental procedure",
    ],
    "veterinary": [
        "animal restraint assistance", "cage cleaning vet", "instrument sterilization vet",
        "medication preparation vet", "bandage application animal", "feeding hospitalized animals",
        "surgical prep animal", "recovery monitoring setup",
    ],
    "funeral_services": [
        "casket handling", "flower arrangement setup", "chair setup funeral",
        "hearse loading", "cemetery preparation", "memorial setup",
    ],
    "car_dealership": [
        "vehicle positioning showroom", "vehicle cleaning dealership", "lot organization",
        "key management", "vehicle transport lot", "detail preparation",
        "accessory installation", "plate mounting",
    ],
    "library": [
        "book shelving", "book sorting", "cart pushing library",
        "shelf reading", "book repair", "media sorting",
        "return processing", "hold shelf management",
    ],
    "museum_detailed": [
        "artifact handling", "display case cleaning", "exhibit installation",
        "artwork hanging", "pedestal positioning", "lighting adjustment exhibit",
        "storage organization museum", "crate unpacking museum",
    ],
    "theater_detailed": [
        "set construction", "set painting", "prop handling",
        "costume organization", "quick change assistance", "stage sweeping",
        "curtain operation", "spotlight operation", "fog machine operation",
    ],
    "sports_facility": [
        "field marking", "goal setup", "net installation",
        "equipment storage sports", "locker room cleaning", "towel service sports",
        "ice resurfacing", "pool cleaning facility", "gym equipment sanitizing",
    ],
    "school_detailed": [
        "classroom setup", "desk arrangement", "whiteboard cleaning",
        "cafeteria serving", "tray collection", "playground equipment setup",
        "science lab preparation", "art supply organization", "gym equipment setup school",
    ],
    "prison_facility": [
        "cell inspection", "meal distribution prison", "laundry handling prison",
        "common area cleaning prison", "equipment maintenance prison",
    ],
    "military_base": [
        "barracks cleaning", "mess hall operations", "equipment maintenance military",
        "vehicle maintenance military", "supply handling military",
        "ammunition handling", "weapon cleaning",
    ],
    "data_center": [
        "server rack installation", "cable management data center", "hardware replacement",
        "cooling system maintenance", "battery replacement ups", "equipment monitoring rounds",
        "tape library operations", "drive replacement",
    ],
    "cleanroom": [
        "gowning assistance", "material transfer cleanroom", "equipment wipedown",
        "particle monitoring", "tool handling cleanroom", "waste removal cleanroom",
    ],
    "greenhouse_detailed": [
        "plant watering greenhouse", "seedling transplanting", "pruning greenhouse",
        "harvesting greenhouse", "pest inspection", "climate control adjustment",
        "grow light adjustment", "nutrient solution mixing", "pot filling",
    ],
    "aquaculture": [
        "fish feeding", "tank cleaning aquaculture", "water quality testing fish",
        "net handling fish", "harvesting fish", "grading fish",
        "equipment maintenance aquaculture", "aeration system maintenance",
    ],
    "beekeeping": [
        "hive inspection", "frame handling", "honey extraction",
        "hive assembly", "feeding bees", "swarm capture",
    ],
}


def load_manifest():
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def save_manifest(manifest):
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f)


def get_existing_names(manifest):
    """Get set of existing task names for deduplication."""
    names = set()
    for node in manifest.values():
        name = node.get("name", "").lower().strip()
        if name:
            names.add(name)
    return names


def slugify(text):
    """Convert text to valid ID slug."""
    slug = text.lower().strip()
    slug = re.sub(r'[^a-z0-9\s_]', '', slug)
    slug = re.sub(r'\s+', '_', slug)
    return slug[:80]


def generate_tasks(category, subdomain):
    """Generate physical tasks for a subdomain."""
    prompt = f"""Generate 12 specific PHYSICAL tasks a robot would perform for: {subdomain}
Category: {category}

Rules:
- ONLY physical manipulation or movement tasks
- Start with action verb: pick, place, move, push, pull, lift, load, clean, cut, pour, etc.
- NO mental tasks (analyze, plan, decide, monitor, supervise)
- Be specific to this subdomain

Output JSON: [{{"name": "action verb + specific object"}}]
Output ONLY valid JSON array."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=2000)
    )

    text = response.text.strip()
    if "```" in text:
        text = text.split("```")[1].replace("json", "").strip()

    try:
        return json.loads(text)
    except:
        if "[" in text:
            start = text.index("[")
            end = text.rfind("}") + 1
            if end > start:
                return json.loads(text[start:end] + "]")
        return []


def generate_subtasks(task_name, domain_name):
    """Generate subtasks for a task."""
    prompt = f"""Decompose this robot task into 4-6 sequential physical subtasks:

Domain: {domain_name}
Task: {task_name}

Each subtask must:
- Be a physical action (manipulation, movement)
- Start with action verb
- Be specific and executable by robot

Output JSON: [{{"name": "action subtask"}}]
Output ONLY valid JSON."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.6, max_output_tokens=1500)
    )

    text = response.text.strip()
    if "```" in text:
        text = text.split("```")[1].replace("json", "").strip()

    try:
        return json.loads(text)
    except:
        return []


def generate_atomics(subtask_name):
    """Generate atomic actions for a subtask."""
    prompt = f"""Break this subtask into 2-4 atomic robot primitives:

Subtask: {subtask_name}

Atomic primitives: grasp, release, pick_up, place, push, pull, rotate, press, walk_to, approach, look_at, pour, cut, slide, open, close, insert, lift, lower

Output JSON: [{{"name": "primitive target/object"}}]
Output ONLY valid JSON."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.5, max_output_tokens=800)
    )

    text = response.text.strip()
    if "```" in text:
        text = text.split("```")[1].replace("json", "").strip()

    try:
        return json.loads(text)
    except:
        return []


def main():
    print("=" * 60)
    print("CONTINUOUS EXPANSION - Domains, Tasks, Subtasks, Atomics")
    print("=" * 60)

    manifest = load_manifest()
    existing_names = get_existing_names(manifest)

    print(f"Starting with {len(manifest)} nodes")
    print(f"Existing unique names: {len(existing_names)}")

    total_added = {"domains": 0, "tasks": 0, "subtasks": 0, "atomics": 0}

    # Phase 1: Add new domains and tasks
    print("\n[PHASE 1] Adding new domains and tasks...")

    total_subdomains = sum(len(subs) for subs in MORE_CATEGORIES.values())
    current = 0

    for category, subdomains in MORE_CATEGORIES.items():
        print(f"\n[{category.upper()}]")

        for subdomain in subdomains:
            current += 1
            domain_id = f"exp_{category}/{slugify(subdomain)}"

            # Skip if domain exists
            if domain_id in manifest:
                print(f"  [{current}/{total_subdomains}] {subdomain} (exists, skipping)")
                continue

            print(f"  [{current}/{total_subdomains}] {subdomain}...", end=" ", flush=True)

            try:
                tasks = generate_tasks(category, subdomain)

                # Filter duplicates
                new_tasks = []
                for t in tasks:
                    name = t.get("name", "").lower().strip()
                    if name and name not in existing_names:
                        new_tasks.append(t)
                        existing_names.add(name)

                if not new_tasks:
                    print("0 new (all duplicates)")
                    continue

                # Add domain
                manifest[domain_id] = {
                    "id": domain_id,
                    "name": subdomain.title(),
                    "node_type": "domain",
                    "parent_id": None,
                    "children_ids": [],
                    "category": category
                }
                total_added["domains"] += 1

                # Add tasks
                for task in new_tasks:
                    task_id = f"{domain_id}/{slugify(task['name'])}"
                    if task_id not in manifest:
                        manifest[task_id] = {
                            "id": task_id,
                            "name": task["name"],
                            "node_type": "task",
                            "parent_id": domain_id,
                            "children_ids": []
                        }
                        manifest[domain_id]["children_ids"].append(task_id)
                        total_added["tasks"] += 1

                print(f"{len(new_tasks)} tasks")
                time.sleep(0.3)

            except Exception as e:
                print(f"ERROR: {e}")

    # Save after phase 1
    save_manifest(manifest)
    print(f"\nPhase 1 complete. Added {total_added['domains']} domains, {total_added['tasks']} tasks")

    # Phase 2: Add subtasks to new tasks (sample)
    print("\n[PHASE 2] Adding subtasks to new tasks...")

    new_tasks = [
        (nid, n) for nid, n in manifest.items()
        if n.get("node_type") == "task"
        and nid.startswith("exp_")
        and len(n.get("children_ids", [])) == 0
    ][:100]  # First 100 new tasks without subtasks

    for i, (task_id, task) in enumerate(new_tasks):
        print(f"  [{i+1}/{len(new_tasks)}] {task['name'][:50]}...", end=" ", flush=True)

        try:
            domain_name = manifest.get(task.get("parent_id", ""), {}).get("name", "")
            subtasks = generate_subtasks(task["name"], domain_name)

            added = 0
            for st in subtasks:
                st_name = st.get("name", "").lower().strip()
                if st_name and st_name not in existing_names:
                    st_id = f"{task_id}/{slugify(st_name)}"
                    if st_id not in manifest:
                        manifest[st_id] = {
                            "id": st_id,
                            "name": st["name"],
                            "node_type": "subtask",
                            "parent_id": task_id,
                            "children_ids": []
                        }
                        manifest[task_id]["children_ids"].append(st_id)
                        existing_names.add(st_name)
                        total_added["subtasks"] += 1
                        added += 1

            print(f"{added} subtasks")
            time.sleep(0.2)

        except Exception as e:
            print(f"ERROR: {e}")

    # Save after phase 2
    save_manifest(manifest)
    print(f"\nPhase 2 complete. Added {total_added['subtasks']} subtasks")

    # Phase 3: Add atomic actions to new subtasks (sample)
    print("\n[PHASE 3] Adding atomic actions...")

    new_subtasks = [
        (nid, n) for nid, n in manifest.items()
        if n.get("node_type") == "subtask"
        and nid.startswith("exp_")
        and len(n.get("children_ids", [])) == 0
    ][:150]  # First 150 new subtasks without atomics

    for i, (subtask_id, subtask) in enumerate(new_subtasks):
        print(f"  [{i+1}/{len(new_subtasks)}] {subtask['name'][:40]}...", end=" ", flush=True)

        try:
            atomics = generate_atomics(subtask["name"])

            added = 0
            for a in atomics:
                a_name = a.get("name", "").lower().strip()
                if a_name and a_name not in existing_names:
                    a_id = f"{subtask_id}/{slugify(a_name)}"
                    if a_id not in manifest:
                        manifest[a_id] = {
                            "id": a_id,
                            "name": a["name"],
                            "node_type": "atomic",
                            "parent_id": subtask_id,
                            "children_ids": []
                        }
                        manifest[subtask_id]["children_ids"].append(a_id)
                        existing_names.add(a_name)
                        total_added["atomics"] += 1
                        added += 1

            print(f"{added} atomics")
            time.sleep(0.15)

        except Exception as e:
            print(f"ERROR: {e}")

    # Final save
    save_manifest(manifest)

    # Summary
    print("\n" + "=" * 60)
    print("EXPANSION COMPLETE")
    print("=" * 60)
    print(f"  New domains:  {total_added['domains']}")
    print(f"  New tasks:    {total_added['tasks']}")
    print(f"  New subtasks: {total_added['subtasks']}")
    print(f"  New atomics:  {total_added['atomics']}")
    print(f"  TOTAL ADDED:  {sum(total_added.values())}")
    print(f"\n  Final manifest: {len(manifest)} nodes")

    # Update stats
    stats = {"trainable": {"total": len(manifest), "by_type": {}}}
    for n in manifest.values():
        t = n.get("node_type", "unknown")
        stats["trainable"]["by_type"][t] = stats["trainable"]["by_type"].get(t, 0) + 1

    with open(MANIFEST_PATH.parent / "stats.json", "w") as f:
        json.dump(stats, f, indent=2)


if __name__ == "__main__":
    main()
