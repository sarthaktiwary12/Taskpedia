#!/usr/bin/env python3
"""
Domain Expansion Script v2 - Generate domains by category for better coverage.
"""

import json
import os
import time
from pathlib import Path

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
MODEL = "gemini-2.5-flash"

# Categories to expand
CATEGORIES = {
    "industrial": [
        "manufacturing assembly lines",
        "welding and fabrication",
        "painting and coating",
        "quality inspection",
        "packaging and palletizing",
        "CNC machine tending",
        "electronics assembly",
        "automotive manufacturing",
        "pharmaceutical production",
        "food processing plants",
        "textile manufacturing",
        "chemical processing",
        "plastics and injection molding",
        "metal stamping and forming",
        "3D printing and additive manufacturing",
    ],
    "warehouse": [
        "order picking",
        "packing stations",
        "inventory management",
        "goods receiving",
        "shipping and dispatch",
        "cold storage handling",
        "hazmat material handling",
        "returns processing",
        "cross-docking",
        "bin stocking",
    ],
    "retail": [
        "shelf stocking",
        "price tag updating",
        "inventory counting",
        "shopping cart retrieval",
        "floor cleaning",
        "product arrangement",
        "backroom organization",
        "checkout assistance",
        "fitting room management",
        "display setup",
    ],
    "food_service": [
        "commercial kitchen cooking",
        "food prep stations",
        "dishwashing operations",
        "restaurant table service",
        "bar beverage preparation",
        "cafeteria food serving",
        "fast food assembly",
        "bakery production",
        "pizza making",
        "coffee and barista",
        "ice cream serving",
        "buffet management",
    ],
    "hospitality": [
        "hotel room cleaning",
        "bed making and linen change",
        "lobby maintenance",
        "luggage handling",
        "room service delivery",
        "laundry operations",
        "pool and spa maintenance",
        "conference room setup",
        "mini bar restocking",
        "check-in assistance",
    ],
    "healthcare": [
        "patient transport",
        "medical supply delivery",
        "surgical instrument handling",
        "pharmacy dispensing",
        "specimen transport",
        "hospital bed making",
        "sanitization and disinfection",
        "physical therapy assistance",
        "rehabilitation exercises",
        "elderly care assistance",
        "vital signs monitoring setup",
        "wheelchair assistance",
    ],
    "residential": [
        "floor vacuuming and mopping",
        "window cleaning",
        "laundry folding",
        "dish loading and unloading",
        "cooking assistance",
        "grocery unpacking",
        "trash and recycling",
        "lawn mowing",
        "garden watering",
        "pool cleaning",
        "pet feeding",
        "elderly home assistance",
        "childcare assistance",
        "home organization",
    ],
    "construction": [
        "bricklaying",
        "drywall installation",
        "painting walls and ceilings",
        "tile laying",
        "concrete pouring",
        "rebar tying",
        "material transport on site",
        "demolition",
        "scaffolding setup",
        "roofing assistance",
        "plumbing assistance",
        "electrical wiring assistance",
        "insulation installation",
        "flooring installation",
    ],
    "agriculture": [
        "crop harvesting",
        "fruit picking",
        "vegetable sorting",
        "planting and seeding",
        "weeding",
        "irrigation management",
        "greenhouse operations",
        "livestock feeding",
        "egg collection",
        "dairy milking assistance",
        "barn cleaning",
        "crop spraying",
        "pruning and trimming",
        "soil preparation",
    ],
    "logistics": [
        "truck loading",
        "truck unloading",
        "container handling",
        "last-mile delivery",
        "parcel sorting",
        "airport baggage handling",
        "mail sorting",
        "dock operations",
        "freight consolidation",
        "vehicle loading optimization",
    ],
    "maintenance": [
        "HVAC filter replacement",
        "light bulb changing",
        "plumbing repairs",
        "electrical repairs",
        "appliance maintenance",
        "elevator maintenance",
        "escalator maintenance",
        "solar panel cleaning",
        "gutter cleaning",
        "pressure washing",
        "equipment lubrication",
        "belt and chain replacement",
    ],
    "laboratory": [
        "sample handling",
        "pipetting",
        "centrifuge loading",
        "microscope slide preparation",
        "chemical mixing",
        "lab equipment cleaning",
        "specimen storage",
        "test tube handling",
        "plate handling",
        "autoclave loading",
    ],
    "entertainment": [
        "stadium cleaning",
        "event setup",
        "event teardown",
        "concert equipment handling",
        "theater prop management",
        "museum exhibit handling",
        "amusement park operations",
        "sports equipment management",
        "gym equipment maintenance",
        "bowling alley operations",
    ],
    "automotive": [
        "car washing",
        "vehicle detailing",
        "tire changing",
        "oil changing",
        "parts retrieval",
        "battery replacement",
        "windshield installation",
        "paint touch-up",
        "vehicle inspection",
        "car parking (valet)",
    ],
    "office": [
        "mail and package delivery",
        "document shredding",
        "supply restocking",
        "meeting room setup",
        "office cleaning",
        "plant watering",
        "recycling collection",
        "desk sanitization",
        "printer maintenance",
        "IT equipment handling",
    ],
}


def generate_tasks_for_subdomain(category: str, subdomain: str):
    """Generate tasks for a specific subdomain."""
    prompt = f"""Generate 10-15 specific PHYSICAL tasks a robot would perform for: {subdomain}

Category: {category}

Rules:
- Tasks must be PHYSICAL (manipulation, locomotion, not mental)
- Start each with action verb (pick, place, move, clean, load, etc.)
- Be specific to this subdomain

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
        return json.loads(text)
    except:
        # Try to salvage partial JSON
        if "[" in text:
            start = text.index("[")
            text = text[start:]
            # Find last complete object
            last_brace = text.rfind("}")
            if last_brace > 0:
                text = text[:last_brace+1] + "]"
                return json.loads(text)
        return []


def main():
    output_dir = Path("/home/sarthak/Taskpedia/generated_domains")
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("TASKPEDIA DOMAIN EXPANSION v2")
    print("=" * 60)

    all_data = {
        "domains": [],
        "tasks": {}
    }

    total_domains = sum(len(subs) for subs in CATEGORIES.values())
    current = 0

    for category, subdomains in CATEGORIES.items():
        print(f"\n[{category.upper()}]")

        for subdomain in subdomains:
            current += 1
            domain_id = subdomain.lower().replace(" ", "_").replace("-", "_")

            print(f"  [{current}/{total_domains}] {subdomain}...", end=" ", flush=True)

            try:
                tasks = generate_tasks_for_subdomain(category, subdomain)

                domain = {
                    "id": domain_id,
                    "name": subdomain.title(),
                    "category": category,
                }
                all_data["domains"].append(domain)
                all_data["tasks"][domain_id] = tasks

                print(f"{len(tasks)} tasks")
                time.sleep(0.3)  # Rate limit

            except Exception as e:
                print(f"ERROR: {e}")
                continue

    # Save everything
    with open(output_dir / "expanded_domains.json", "w") as f:
        json.dump(all_data, f, indent=2)

    # Summary
    total_tasks = sum(len(t) for t in all_data["tasks"].values())
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Categories: {len(CATEGORIES)}")
    print(f"  Domains:    {len(all_data['domains'])}")
    print(f"  Tasks:      {total_tasks}")
    print(f"\n  Output: {output_dir}/expanded_domains.json")

    # Category breakdown
    print("\n  By category:")
    for cat in CATEGORIES:
        count = len([d for d in all_data["domains"] if d["category"] == cat])
        task_count = sum(len(all_data["tasks"].get(d["id"], [])) for d in all_data["domains"] if d["category"] == cat)
        print(f"    {cat}: {count} domains, {task_count} tasks")


if __name__ == "__main__":
    main()
