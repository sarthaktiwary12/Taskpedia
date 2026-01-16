#!/usr/bin/env python3
"""
Merge the quality-regenerated tasks into the manifest.
"""

import json
from pathlib import Path


def main():
    manifest_path = Path("/home/sarthak/Taskpedia/taskpedia-web/public/data/manifest.json")
    quality_path = Path("/home/sarthak/Taskpedia/hierarchy_data/quality_tasks.json")
    stats_path = Path("/home/sarthak/Taskpedia/taskpedia-web/public/data/stats.json")

    # Load existing manifest
    with open(manifest_path) as f:
        manifest = json.load(f)

    # Load quality tasks
    with open(quality_path) as f:
        quality_data = json.load(f)

    print("=" * 60)
    print("MERGING QUALITY TASKS INTO MANIFEST")
    print("=" * 60)
    print(f"Existing manifest: {len(manifest)} nodes")

    # Build set of existing task names for deduplication
    existing_names = set()
    for node in manifest.values():
        existing_names.add(node.get("name", "").lower().strip())

    added_domains = 0
    added_subcats = 0
    added_tasks = 0

    for cat_key, cat_data in quality_data.items():
        cat_name = cat_data["name"]
        cat_id = f"robotics_{cat_key}_v2"  # v2 to avoid conflict with existing

        print(f"\n[{cat_name}]")

        # Check if domain already exists (without v2)
        existing_cat_id = f"robotics_{cat_key}"

        # If the existing domain exists, we'll add tasks there
        if existing_cat_id in manifest:
            cat_id = existing_cat_id
            domain_node = manifest[cat_id]
        else:
            # Create new domain
            domain_node = {
                "id": cat_id,
                "name": cat_name,
                "node_type": "domain",
                "parent_id": None,
                "children_ids": []
            }
            manifest[cat_id] = domain_node
            added_domains += 1

        # Process subcategories
        for subcat_key, subcat_data in cat_data.get("subcategories", {}).items():
            subcat_id = f"{cat_id}/{subcat_key}_quality"  # Add _quality suffix
            subcat_name = subcat_key.replace("_", " ").title() + " (Quality)"

            # Create subcategory node
            subcat_node = {
                "id": subcat_id,
                "name": subcat_name,
                "node_type": "task",
                "parent_id": cat_id,
                "children_ids": []
            }

            tasks_added = 0
            for task_name in subcat_data.get("tasks", []):
                # Skip duplicates
                if task_name.lower().strip() in existing_names:
                    continue

                task_slug = task_name.lower().replace(" ", "_").replace(".", "").replace(",", "")[:50]
                task_id = f"{subcat_id}/{task_slug}"

                if task_id in manifest:
                    continue

                task_node = {
                    "id": task_id,
                    "name": task_name,
                    "node_type": "subtask",
                    "parent_id": subcat_id,
                    "children_ids": []
                }

                manifest[task_id] = task_node
                subcat_node["children_ids"].append(task_id)
                existing_names.add(task_name.lower().strip())
                tasks_added += 1
                added_tasks += 1

            if tasks_added > 0:
                manifest[subcat_id] = subcat_node
                if subcat_id not in domain_node["children_ids"]:
                    domain_node["children_ids"].append(subcat_id)
                added_subcats += 1
                print(f"  {subcat_name}: {tasks_added} tasks")

    # Save updated manifest
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

    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n{'='*60}")
    print("MERGE COMPLETE")
    print(f"{'='*60}")
    print(f"  New domains:      {added_domains}")
    print(f"  New subcategories:{added_subcats}")
    print(f"  New tasks:        {added_tasks}")
    print(f"  TOTAL ADDED:      {added_domains + added_subcats + added_tasks}")
    print(f"\n  Final manifest:   {len(manifest)} nodes")
    print(f"\n  By type:")
    for t, c in types.items():
        print(f"    {t}: {c:,}")


if __name__ == "__main__":
    main()
