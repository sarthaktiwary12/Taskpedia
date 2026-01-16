#!/usr/bin/env python3
"""
Expand Taskpedia with even more domains and categories.
"""

import json
import os
import time
from pathlib import Path

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
MODEL = "gemini-2.5-flash"

# More categories to expand
MORE_CATEGORIES = {
    "railway": [
        "train car cleaning",
        "platform maintenance",
        "ticket gate operations",
        "luggage handling station",
        "track inspection",
        "signal equipment maintenance",
        "train coupling uncoupling",
        "freight car loading",
        "passenger assistance",
        "rail yard operations",
    ],
    "subway_metro": [
        "metro car cleaning",
        "escalator maintenance",
        "turnstile operations",
        "platform edge doors",
        "tunnel ventilation",
        "emergency equipment checks",
        "graffiti removal",
        "track debris clearing",
    ],
    "bus_transit": [
        "bus interior cleaning",
        "bus exterior washing",
        "fare box maintenance",
        "bus stop maintenance",
        "wheelchair ramp operation",
        "luggage compartment loading",
        "fuel depot operations",
        "tire inspection bus",
    ],
    "postal_shipping": [
        "package sorting facility",
        "mail truck loading",
        "parcel weighing measuring",
        "stamp dispensing",
        "PO box maintenance",
        "conveyor sorting",
        "damaged package handling",
        "international customs prep",
    ],
    "photography_studio": [
        "lighting setup photo",
        "backdrop changing",
        "camera equipment handling",
        "prop arrangement photo",
        "equipment storage photo",
        "print processing",
        "frame assembly",
        "studio cleaning",
    ],
    "film_tv_production": [
        "camera dolly operation",
        "boom microphone handling",
        "clapperboard operation",
        "cable management set",
        "craft services setup",
        "wardrobe handling",
        "makeup station setup",
        "green screen setup",
        "lighting rig adjustment",
        "set decoration",
    ],
    "jewelry_making": [
        "metal casting jewelry",
        "gem setting",
        "polishing jewelry",
        "chain assembly",
        "clasp attachment",
        "engraving jewelry",
        "cleaning jewelry pieces",
        "packaging jewelry display",
        "stone cutting",
        "soldering jewelry",
    ],
    "shoe_manufacturing": [
        "leather cutting shoes",
        "sole attachment",
        "stitching uppers",
        "lace hole punching",
        "heel attachment",
        "shoe polishing factory",
        "quality inspection shoes",
        "packaging shoes",
        "insole insertion",
        "shoe lasting",
    ],
    "toy_manufacturing": [
        "plastic molding toys",
        "toy assembly line",
        "paint application toys",
        "sticker application",
        "packaging toys",
        "safety testing toys",
        "battery insertion",
        "plush stuffing",
        "doll hair attachment",
        "wheel attachment toys",
    ],
    "musical_instruments": [
        "guitar string installation",
        "piano tuning assistance",
        "drum assembly",
        "brass instrument polishing",
        "woodwind key adjustment",
        "violin bow rehairing",
        "instrument case handling",
        "reed preparation",
        "percussion head replacement",
        "instrument cleaning maintenance",
    ],
    "boat_building": [
        "hull fiberglass laying",
        "deck hardware installation",
        "mast stepping",
        "rigging setup",
        "engine installation boat",
        "electrical wiring boat",
        "interior fitting boat",
        "antifouling application",
        "sea trial preparation",
        "trailer loading boat",
    ],
    "bicycle_shop": [
        "wheel truing",
        "brake adjustment bike",
        "chain replacement",
        "tire mounting bike",
        "handlebar adjustment",
        "seat adjustment",
        "gear tuning",
        "pedal installation",
        "bike assembly",
        "bike cleaning service",
    ],
    "arcade_gaming": [
        "arcade machine maintenance",
        "prize claw refilling",
        "token machine service",
        "game cabinet cleaning",
        "ticket redemption counting",
        "joystick replacement",
        "screen cleaning arcade",
        "coin collection",
        "prize display stocking",
        "VR equipment sanitizing",
    ],
    "zoo_operations": [
        "animal enclosure cleaning",
        "food preparation zoo",
        "habitat maintenance",
        "enrichment setup animals",
        "water feature cleaning zoo",
        "fence inspection zoo",
        "bedding replacement animals",
        "feeding schedule execution",
        "medical equipment prep zoo",
        "visitor barrier maintenance",
    ],
    "public_aquarium": [
        "tank cleaning aquarium public",
        "filter maintenance aquarium",
        "fish feeding public aquarium",
        "glass cleaning tanks",
        "coral placement",
        "water testing aquarium",
        "exhibit decoration aquarium",
        "quarantine tank handling",
        "pump maintenance aquarium",
        "lighting adjustment aquarium",
    ],
    "botanical_garden": [
        "plant labeling",
        "path maintenance garden",
        "greenhouse ventilation",
        "specimen collection",
        "irrigation system garden",
        "mulching beds",
        "tree support installation",
        "pond maintenance garden",
        "bench maintenance garden",
        "seasonal display setup",
    ],
    "fire_station": [
        "equipment inspection fire",
        "hose rolling storage",
        "truck washing fire",
        "gear maintenance fire",
        "ladder inspection",
        "breathing apparatus check",
        "station cleaning fire",
        "equipment inventory fire",
        "hydrant testing",
        "rescue equipment prep",
    ],
    "police_station": [
        "evidence room organization",
        "vehicle fleet maintenance",
        "equipment locker organization",
        "interview room setup",
        "document filing police",
        "radio equipment check",
        "holding cell cleaning",
        "uniform maintenance police",
        "weapon armory management",
        "patrol car preparation",
    ],
    "ems_ambulance": [
        "ambulance restocking",
        "stretcher maintenance",
        "medical equipment check",
        "oxygen tank replacement",
        "defibrillator check",
        "ambulance cleaning sanitizing",
        "supply inventory ems",
        "gurney operation",
        "medical bag preparation",
        "equipment calibration ems",
    ],
    "oil_gas_refinery": [
        "valve operation refinery",
        "pipe inspection refinery",
        "tank gauging",
        "pump maintenance refinery",
        "filter replacement refinery",
        "sample collection refinery",
        "safety equipment check refinery",
        "flare system maintenance",
        "cooling tower maintenance",
        "catalyst handling",
    ],
    "telecom_infrastructure": [
        "cable splicing",
        "antenna installation",
        "cabinet maintenance telecom",
        "fiber optic handling",
        "tower climbing equipment",
        "signal testing",
        "equipment rack mounting",
        "battery backup maintenance",
        "grounding installation",
        "weatherproofing equipment",
    ],
    "water_park": [
        "slide cleaning",
        "wave pool maintenance",
        "lazy river cleaning",
        "life jacket organization",
        "tube storage handling",
        "filter cleaning water park",
        "deck cleaning water park",
        "locker maintenance",
        "chlorine level management",
        "splash pad maintenance",
    ],
    "ski_resort": [
        "ski lift maintenance",
        "snow grooming",
        "ski rental fitting",
        "boot fitting",
        "pole adjustment",
        "gondola cleaning",
        "trail marking",
        "safety net installation",
        "snow making equipment",
        "lodge cleaning",
    ],
    "golf_course": [
        "green mowing",
        "hole cup changing",
        "bunker raking",
        "cart maintenance golf",
        "ball washer filling",
        "tee marker placement",
        "irrigation golf course",
        "driving range collection",
        "club cleaning service",
        "flagstick placement",
    ],
    "marina_operations": [
        "dock maintenance marina",
        "fuel dock operations",
        "pump out service",
        "boat washing marina",
        "slip assignment prep",
        "mooring maintenance",
        "dock cart handling",
        "shore power connection",
        "ice delivery boats",
        "dinghy dock management",
    ],
    "campground": [
        "fire pit cleaning",
        "picnic table maintenance",
        "restroom cleaning campground",
        "trash collection campground",
        "firewood delivery",
        "site marker maintenance",
        "water spigot check",
        "trail maintenance campground",
        "RV hookup assistance",
        "camp store stocking",
    ],
    "carwash_detailed": [
        "pre-rinse spraying",
        "foam application",
        "brush scrubbing auto",
        "wheel cleaning detailed",
        "undercarriage wash",
        "rinse cycle operation",
        "wax application auto",
        "air drying operation",
        "interior vacuuming detailed",
        "window cleaning auto",
    ],
    "parking_garage": [
        "ticket dispensing",
        "gate arm maintenance",
        "space marking painting",
        "lighting maintenance parking",
        "elevator maintenance parking",
        "payment kiosk service",
        "surface cleaning parking",
        "directional sign maintenance",
        "security camera check",
        "EV charger maintenance",
    ],
    "storage_facility": [
        "unit inspection storage",
        "lock cutting service",
        "cart provision storage",
        "elevator operation storage",
        "loading dock assistance",
        "pest control storage",
        "climate control check",
        "security patrol storage",
        "unit cleaning storage",
        "inventory tagging",
    ],
    "moving_relocation": [
        "furniture wrapping",
        "box assembly moving",
        "loading truck moving",
        "furniture disassembly",
        "appliance dolly operation",
        "stair climbing equipment",
        "unloading truck moving",
        "furniture reassembly",
        "box stacking truck",
        "padding application",
    ],
    "flower_shop": [
        "flower arranging",
        "stem cutting",
        "water changing flowers",
        "wrapping bouquets",
        "ribbon tying",
        "vase preparation",
        "cooler organization flowers",
        "delivery preparation flowers",
        "foam soaking floral",
        "plant care retail",
    ],
    "hardware_store": [
        "key cutting",
        "paint mixing",
        "lumber cutting",
        "pipe threading",
        "glass cutting hardware",
        "chain cutting",
        "rope cutting measuring",
        "screen repair",
        "shelf stocking hardware",
        "propane tank exchange",
    ],
    "appliance_store": [
        "appliance unboxing",
        "display setup appliances",
        "delivery loading appliances",
        "installation assistance",
        "old appliance removal",
        "demonstration setup",
        "accessory stocking",
        "floor model maintenance",
        "warranty paperwork",
        "recycling coordination",
    ],
    "casino_operations": [
        "chip handling",
        "card shuffling machine",
        "slot machine maintenance",
        "table felt replacement",
        "chip rack organization",
        "cage operations",
        "surveillance equipment check",
        "floor cleaning casino",
        "token counting",
        "gaming table setup",
    ],
    "amusement_rides": [
        "ride inspection daily",
        "restraint checking",
        "loading unloading riders",
        "queue management",
        "ride cleaning operations",
        "safety belt testing",
        "emergency stop testing",
        "ride lubrication",
        "control panel check",
        "guest assistance rides",
    ],
    "convention_center": [
        "booth setup convention",
        "carpet laying temporary",
        "signage installation",
        "electrical connection booth",
        "furniture rental setup",
        "registration desk setup",
        "audio visual setup",
        "pipe and drape installation",
        "loading dock coordination",
        "teardown operations",
    ],
}


def generate_tasks_for_domain(category: str, domain: str, existing_names: set):
    """Generate tasks for a specific domain."""
    prompt = f"""Generate 10-12 specific PHYSICAL tasks a robot would perform for: {domain}

Category: {category}

Rules:
- Tasks must be PHYSICAL (manipulation, locomotion, not mental)
- Start each with action verb (pick, place, move, clean, load, grasp, push, pull, etc.)
- Be specific to this domain
- Tasks should be things humans currently do that robots could do

Output JSON array: [{{"name": "verb + object/action"}}]
Example: [{{"name": "pick up package from conveyor"}}, {{"name": "place item on shelf"}}]

Output ONLY valid JSON array."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=2000,
        )
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1].strip()
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        tasks = json.loads(text)
        # Filter duplicates
        unique_tasks = []
        for t in tasks:
            name = t.get("name", "").lower().strip()
            if name and name not in existing_names:
                existing_names.add(name)
                unique_tasks.append(t)
        return unique_tasks
    except:
        if "[" in text:
            start = text.index("[")
            text = text[start:]
            last_brace = text.rfind("}")
            if last_brace > 0:
                text = text[:last_brace+1] + "]"
                try:
                    return json.loads(text)
                except:
                    pass
        return []


def main():
    manifest_path = Path("/home/sarthak/Taskpedia/taskpedia-web/public/data/manifest.json")

    # Load existing manifest
    with open(manifest_path) as f:
        manifest = json.load(f)

    print("=" * 60)
    print("TASKPEDIA EXPANSION - More Domains")
    print("=" * 60)
    print(f"Starting with {len(manifest)} nodes")

    # Build existing names set
    existing_names = set()
    for node_id, node in manifest.items():
        existing_names.add(node.get("name", "").lower().strip())
    print(f"Existing unique names: {len(existing_names)}")

    total_domains = sum(len(doms) for doms in MORE_CATEGORIES.values())
    current = 0
    added_domains = 0
    added_tasks = 0

    for category, domains in MORE_CATEGORIES.items():
        print(f"\n[{category.upper()}]")

        for domain_name in domains:
            current += 1
            domain_id = domain_name.lower().replace(" ", "_").replace("-", "_")

            # Skip if domain already exists
            if domain_id in manifest:
                print(f"  [{current}/{total_domains}] {domain_name}... SKIP (exists)")
                continue

            print(f"  [{current}/{total_domains}] {domain_name}...", end=" ", flush=True)

            try:
                tasks = generate_tasks_for_domain(category, domain_name, existing_names)

                if not tasks:
                    print("0 tasks")
                    continue

                # Create domain node
                domain_node = {
                    "id": domain_id,
                    "name": domain_name.title(),
                    "node_type": "domain",
                    "parent_id": None,
                    "children_ids": []
                }

                # Create task nodes
                for task in tasks:
                    task_name = task.get("name", "")
                    if not task_name:
                        continue

                    task_id = f"{domain_id}/{task_name.lower().replace(' ', '_')[:50]}"

                    # Skip if task already exists
                    if task_id in manifest:
                        continue

                    task_node = {
                        "id": task_id,
                        "name": task_name,
                        "node_type": "task",
                        "parent_id": domain_id,
                        "children_ids": []
                    }

                    manifest[task_id] = task_node
                    domain_node["children_ids"].append(task_id)
                    added_tasks += 1

                manifest[domain_id] = domain_node
                added_domains += 1

                print(f"{len(tasks)} tasks")
                time.sleep(0.2)

            except Exception as e:
                print(f"ERROR: {e}")
                continue

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
    print("EXPANSION COMPLETE")
    print("=" * 60)
    print(f"  New domains:  {added_domains}")
    print(f"  New tasks:    {added_tasks}")
    print(f"  Final manifest: {len(manifest)} nodes")
    print(f"\n  By type:")
    for t, c in types.items():
        print(f"    {t}: {c}")


if __name__ == "__main__":
    main()
