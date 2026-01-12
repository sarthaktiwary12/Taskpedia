#!/usr/bin/env python3
"""
TASKPEDIA CLI - Hierarchical Task Decomposition for Embodied AI.

Commands are organized into groups:
    taskpedia init          Initialize/bootstrap the hierarchy
    taskpedia generate      Generate tasks with LLM
    taskpedia show          View hierarchy (tree, stats, search)
    taskpedia export        Export to various formats
    taskpedia upload        Upload to HuggingFace
    taskpedia download      Download from HuggingFace
    taskpedia cache         Manage LLM cache
"""

import argparse
import sys
from pathlib import Path

# Default paths
DEFAULT_OUTPUT = "./task_hierarchy"


def cmd_init(args):
    """Initialize the task hierarchy from seed data."""
    from taskpedia.decompose import quick_bootstrap

    print(f"Initializing task hierarchy: {args.output}")
    print()

    graph = quick_bootstrap(args.output)

    print()
    print("=" * 50)
    print("INITIALIZATION COMPLETE")
    print("=" * 50)

    stats = graph.get_stats()
    print(f"  Nodes:    {stats['total_nodes']:,}")
    print(f"  Domains:  {stats['domains']}")
    print(f"  Depth:    {stats['max_depth']}")
    print()
    print("Next: Run 'taskpedia generate' to expand with LLM")


def cmd_generate(args):
    """Generate tasks using LLM decomposition."""
    from taskpedia.generator import FastGenConfig, run

    output_path = Path(args.output)

    if not output_path.exists():
        print(f"Error: {output_path} does not exist.")
        print("Run 'taskpedia init' first.")
        sys.exit(1)

    config = FastGenConfig(
        output_dir=output_path,
        model=args.model,
        max_tasks=args.max_tasks,
        max_workers=args.workers,
        queue_size=args.queue_size,
        rpm_limit=args.rpm,
        mock=args.mock,
        tui=not args.no_tui,
        use_judge=not getattr(args, "no_judge", False),
        use_llm_judge=getattr(args, "llm_judge", False),
    )

    run(config)


def cmd_show_tree(args):
    """Display hierarchy as a tree."""
    from taskpedia.hierarchy import TaskGraph

    output_path = Path(args.output)
    if not output_path.exists():
        print(f"Error: {output_path} not found. Run 'taskpedia init' first.")
        sys.exit(1)

    graph = TaskGraph(output_path)
    print(graph.visualize_tree(max_depth=args.depth))


def cmd_show_stats(args):
    """Show hierarchy statistics."""
    from taskpedia.hierarchy import TaskGraph

    output_path = Path(args.output)
    if not output_path.exists():
        print(f"Error: {output_path} not found. Run 'taskpedia init' first.")
        sys.exit(1)

    graph = TaskGraph(output_path)
    stats = graph.get_stats()

    print()
    print("TASKPEDIA Statistics")
    print("=" * 40)
    print(f"  Total nodes:   {stats['total_nodes']:>10,}")
    print(f"  Domains:       {stats['domains']:>10}")
    print(f"  Max depth:     {stats['max_depth']:>10}")
    print(f"  Avg depth:     {stats['avg_depth']:>10.1f}")
    print(f"  Leaf nodes:    {stats['leaf_count']:>10,}")
    print()
    print("By Type:")
    for node_type, count in stats["by_type"].items():
        pct = count / stats["total_nodes"] * 100 if stats["total_nodes"] > 0 else 0
        print(f"  {node_type:12} {count:>8,} ({pct:>5.1f}%)")
    print()


def cmd_show_search(args):
    """Search for tasks."""
    from taskpedia.hierarchy import TaskGraph

    output_path = Path(args.output)
    if not output_path.exists():
        print(f"Error: {output_path} not found.")
        sys.exit(1)

    graph = TaskGraph(output_path)
    query = args.query.lower()

    matches = [n for n in graph.iter_nodes() if query in n.name.lower()]

    print(f"\nFound {len(matches)} matches for '{args.query}':\n")

    for node in matches[: args.limit]:
        ancestors = graph.get_ancestors(node.id)
        path = " > ".join([a.name for a in reversed(ancestors)] + [node.name])
        print(f"  [{node.node_type.value}] {path}")
        if node.description:
            desc = node.description[:70] + "..." if len(node.description) > 70 else node.description
            print(f"      {desc}")
    print()


def cmd_export(args):
    """Export hierarchy to file."""
    import json

    from taskpedia.hierarchy import TaskGraph

    output_path = Path(args.output)
    if not output_path.exists():
        print(f"Error: {output_path} not found.")
        sys.exit(1)

    graph = TaskGraph(output_path)
    export_path = Path(args.file) if args.file else output_path / f"export.{args.format}"

    if args.format == "jsonl":
        graph.export_flat(export_path)
    elif args.format == "tree":
        export_path = export_path.with_suffix(".txt")
        with open(export_path, "w") as f:
            f.write(graph.visualize_tree(max_depth=10))
    elif args.format == "json":

        def to_nested(node_id):
            node = graph.get_node(node_id)
            if not node:
                return None
            data = node.to_dict()
            children = graph.get_children(node_id)
            if children:
                data["children"] = [to_nested(c.id) for c in children]
            return data

        roots = [n for n in graph.iter_nodes() if n.parent_id is None]
        nested = [to_nested(r.id) for r in roots]

        export_path = export_path.with_suffix(".json")
        with open(export_path, "w") as f:
            json.dump(nested, f, indent=2)

    print(f"Exported {graph.get_stats()['total_nodes']:,} nodes to: {export_path}")


def cmd_upload(args):
    """Upload to HuggingFace."""
    from datetime import datetime

    import yaml

    try:
        from datasets import Dataset, DatasetDict, Features, Sequence, Value
        from huggingface_hub import HfApi
    except ImportError:
        print("Error: Upload requires 'datasets' and 'huggingface_hub' packages.")
        print("Install with: pip install datasets huggingface_hub")
        sys.exit(1)

    task_dir = Path(args.output)
    if not task_dir.exists():
        print(f"Error: {task_dir} not found.")
        sys.exit(1)

    # Load tasks
    print(f"Loading tasks from {task_dir}...")
    tasks = []
    for yaml_path in task_dir.glob("**/*.yaml"):
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            if not data or "id" not in data:
                continue

            completion = data.get("completion", {}) or {}
            tasks.append(
                {
                    "id": data.get("id", ""),
                    "name": data.get("name", ""),
                    "node_type": data.get("node_type", ""),
                    "parent_id": data.get("parent_id", "") or "",
                    "children_ids": data.get("children_ids", []) or [],
                    "description": data.get("description", "") or "",
                    "precondition": completion.get("precondition", "") or "",
                    "postcondition": completion.get("postcondition", "") or "",
                    "invariants": completion.get("invariants", "") or "",
                    "physical_requirements": data.get("physical_requirements", "") or "",
                    "sensing_requirements": data.get("sensing_requirements", "") or "",
                    "cognitive_requirements": data.get("cognitive_requirements", "") or "",
                    "language": data.get("language", "en"),
                    "aliases": data.get("aliases", []) or [],
                    "tags": data.get("tags", []) or [],
                    "sources": data.get("sources", []) or [],
                    "confidence": float(data.get("confidence", 1.0)),
                    "depth": len(data.get("id", "").split("/")),
                    "is_leaf": len(data.get("children_ids", []) or []) == 0,
                    "is_atomic": data.get("node_type") == "atomic",
                }
            )
        except Exception as e:
            pass

    if not tasks:
        print("No tasks found!")
        sys.exit(1)

    print(f"Loaded {len(tasks):,} tasks")

    # Create dataset
    features = Features(
        {
            "id": Value("string"),
            "name": Value("string"),
            "node_type": Value("string"),
            "parent_id": Value("string"),
            "children_ids": Sequence(Value("string")),
            "description": Value("string"),
            "precondition": Value("string"),
            "postcondition": Value("string"),
            "invariants": Value("string"),
            "physical_requirements": Value("string"),
            "sensing_requirements": Value("string"),
            "cognitive_requirements": Value("string"),
            "language": Value("string"),
            "aliases": Sequence(Value("string")),
            "tags": Sequence(Value("string")),
            "sources": Sequence(Value("string")),
            "confidence": Value("float32"),
            "depth": Value("int32"),
            "is_leaf": Value("bool"),
            "is_atomic": Value("bool"),
        }
    )

    dataset = Dataset.from_list(tasks, features=features)
    dataset_dict = DatasetDict({"full": dataset})

    # Stats for README
    atomic_count = sum(1 for t in tasks if t["is_atomic"])
    leaf_count = sum(1 for t in tasks if t["is_leaf"])
    from collections import Counter

    node_types = Counter(t["node_type"] for t in tasks)
    sources = Counter(s for t in tasks for s in t["sources"])

    # Upload
    repo_id = args.repo
    private = not args.public

    api = HfApi()
    print(f"Creating repo: {repo_id} (private={private})...")

    try:
        api.create_repo(repo_id=repo_id, repo_type="dataset", private=private, exist_ok=True)
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure you're logged in: huggingface-cli login")
        sys.exit(1)

    print("Uploading dataset...")
    dataset_dict.push_to_hub(repo_id=repo_id, private=private)

    # README
    readme = f"""---
license: apache-2.0
task_categories:
  - robotics
tags:
  - embodied-ai
  - task-decomposition
  - VLA
  - VLN
---

# TASKPEDIA

Hierarchical task decomposition for embodied AI. {len(tasks):,} tasks, {atomic_count:,} atomic actions.

## Stats
- Total: {len(tasks):,}
- Atomic: {atomic_count:,}
- Leaf: {leaf_count:,}

## Usage
```python
from datasets import load_dataset
ds = load_dataset("{repo_id}")
atomic = ds["full"].filter(lambda x: x["is_atomic"])
```
"""

    api.upload_file(
        path_or_fileobj=readme.encode(),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="dataset",
    )

    print(f"\nUploaded to: https://huggingface.co/datasets/{repo_id}")


def cmd_download(args):
    """Download from HuggingFace and lay out in filesystem."""
    import hashlib
    import json
    from datetime import datetime

    try:
        from datasets import load_dataset
        from huggingface_hub import HfApi, hf_hub_download
    except ImportError:
        print("Error: Download requires 'datasets' and 'huggingface_hub' packages.")
        print("Install with: pip install datasets huggingface_hub")
        sys.exit(1)

    output_dir = Path(args.output)
    repo_id = args.repo

    # Check if output directory exists
    if output_dir.exists():
        # Check for metadata to see if we have a local copy
        meta_file = output_dir / ".taskpedia_meta.json"
        if meta_file.exists() and not args.force:
            with open(meta_file) as f:
                meta = json.load(f)

            # Check if repo matches
            if meta.get("repo_id") == repo_id:
                # Get remote dataset info to compare
                try:
                    api = HfApi()
                    repo_info = api.dataset_info(repo_id)
                    remote_sha = repo_info.sha

                    if meta.get("sha") == remote_sha:
                        print(f"Local copy is up-to-date (sha: {remote_sha[:8]})")
                        print(f"Use --force to re-download anyway")
                        return
                    else:
                        print(
                            f"Remote has been updated (local: {meta.get('sha', 'unknown')[:8]}, remote: {remote_sha[:8]})"
                        )
                except Exception as e:
                    print(f"Warning: Could not check remote version: {e}")

            # Ask before overwriting
            if not args.yes:
                response = input(f"Directory {output_dir} already exists. Overwrite? [y/N]: ")
                if response.lower() not in ("y", "yes"):
                    print("Aborted.")
                    return

    # Download dataset
    print(f"Downloading from: https://huggingface.co/datasets/{repo_id}")
    try:
        ds = load_dataset(repo_id, split="full")
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        sys.exit(1)

    print(f"Downloaded {len(ds):,} tasks")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert to filesystem layout
    print(f"Writing to {output_dir}...")
    written = 0
    skipped = 0

    for task in ds:
        task_id = task["id"]
        if not task_id:
            skipped += 1
            continue

        # Create path from ID (e.g., "work/cooking/chop_onion" -> work/cooking/chop_onion.yaml)
        task_path = output_dir / f"{task_id}.yaml"
        task_path.parent.mkdir(parents=True, exist_ok=True)

        # Build task dict
        task_data = {
            "id": task["id"],
            "name": task["name"],
            "node_type": task["node_type"],
            "description": task["description"] or None,
            "parent_id": task["parent_id"] or None,
            "children_ids": list(task["children_ids"]) if task["children_ids"] else [],
            "completion": {
                "precondition": task["precondition"] or None,
                "postcondition": task["postcondition"] or None,
                "invariants": task["invariants"] or None,
            }
            if any([task["precondition"], task["postcondition"], task["invariants"]])
            else None,
            "physical_requirements": task["physical_requirements"] or None,
            "sensing_requirements": task["sensing_requirements"] or None,
            "cognitive_requirements": task["cognitive_requirements"] or None,
            "language": task["language"],
            "aliases": list(task["aliases"]) if task["aliases"] else [],
            "tags": list(task["tags"]) if task["tags"] else [],
            "sources": list(task["sources"]) if task["sources"] else [],
            "confidence": float(task["confidence"]),
        }

        # Remove None values for cleaner YAML
        task_data = {k: v for k, v in task_data.items() if v is not None}
        if "completion" in task_data:
            task_data["completion"] = {
                k: v for k, v in task_data["completion"].items() if v is not None
            }
            if not task_data["completion"]:
                del task_data["completion"]

        # Write YAML
        try:
            import yaml

            with open(task_path, "w") as f:
                yaml.safe_dump(
                    task_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False
                )
            written += 1
        except Exception as e:
            print(f"  Error writing {task_path}: {e}")
            skipped += 1

    # Save metadata for future sync checks
    try:
        api = HfApi()
        repo_info = api.dataset_info(repo_id)
        remote_sha = repo_info.sha
    except:
        remote_sha = None

    meta = {
        "repo_id": repo_id,
        "sha": remote_sha,
        "downloaded_at": datetime.now().isoformat(),
        "task_count": written,
    }
    with open(output_dir / ".taskpedia_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    # Create manifest
    manifest_path = output_dir / "manifest.json"
    manifest = {"nodes": [task["id"] for task in ds if task["id"]]}
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    print(f"\nDownload complete!")
    print(f"  Written: {written:,} tasks")
    if skipped:
        print(f"  Skipped: {skipped:,}")
    print(f"  Output:  {output_dir}")


def cmd_qa_analyze(args):
    """Analyze data quality."""
    from taskpedia.postprocess import analyze_quality

    task_dir = Path(args.output)
    if not task_dir.exists():
        print(f"Error: {task_dir} not found")
        sys.exit(1)

    print(f"Analyzing {task_dir}...\n")
    result = analyze_quality(task_dir)
    stats = result["stats"]

    print("Quality Analysis")
    print("=" * 50)
    print(f"  Total nodes:           {stats['total']:>10,}")
    print(f"  LLM-generated:         {stats['llm_generated']:>10,}")
    print()
    print("Issues found:")
    print(f"  Generic 'Step N' desc: {stats['generic_step_desc']:>10,}")
    print(f"  Generic template:      {stats['generic_template']:>10,}")
    print(f"  Invalid atomic:        {stats['invalid_atomic']:>10,}")
    print(f"  Empty description:     {stats['empty_description']:>10,}")
    print()
    print(f"  Good quality:          {stats['good_quality']:>10,}")
    print(f"  Valid atomic:          {stats['valid_atomic']:>10,}")

    if result["bad_examples"]:
        print("\nBad examples:")
        for ex in result["bad_examples"][:10]:
            print(f"  [{ex['type']}] {ex['name']}")
            print(f"       {ex['desc']}")

    if result["good_examples"]:
        print("\nGood examples:")
        for ex in result["good_examples"][:5]:
            print(f"  [{ex['type']}] {ex['name']}")
            if ex["desc"]:
                print(f"       {ex['desc']}")


def cmd_qa_clean(args):
    """Remove bad nodes."""
    import yaml

    from taskpedia.postprocess import (
        find_bad_nodes,
        rebuild_manifest,
        remove_nodes,
        reset_parent_children,
    )

    task_dir = Path(args.output)
    if not task_dir.exists():
        print(f"Error: {task_dir} not found")
        sys.exit(1)

    print(f"Finding bad nodes in {task_dir}...")
    bad_paths = find_bad_nodes(task_dir)
    print(f"Found {len(bad_paths):,} bad nodes")

    if not bad_paths:
        print("Nothing to clean!")
        return

    if args.dry_run:
        print("\n[DRY RUN] Would remove:")
        for p in bad_paths[:20]:
            print(f"  {p}")
        if len(bad_paths) > 20:
            print(f"  ... and {len(bad_paths) - 20} more")
        print(f"\nRun without --dry-run to actually remove")
    else:
        print(f"\nRemoving {len(bad_paths):,} bad nodes...")

        # Collect IDs for parent update
        removed_ids = set()
        for p in bad_paths:
            try:
                with open(p) as f:
                    data = yaml.safe_load(f)
                if data and "id" in data:
                    removed_ids.add(data["id"])
            except:
                pass

        # Remove files
        count = remove_nodes(bad_paths, dry_run=False)
        print(f"Removed {count:,} files")

        # Update parents
        print("Updating parent references...")
        reset_parent_children(task_dir, removed_ids)

        # Rebuild manifest
        print("Rebuilding manifest...")
        node_count = rebuild_manifest(task_dir)
        print(f"Manifest rebuilt with {node_count:,} nodes")

        print("\nDone!")


def cmd_qa_verbs(args):
    """Analyze verb taxonomy."""
    from taskpedia.postprocess import (
        analyze_verb_stems,
        check_domain_coverage,
        get_verb_statistics,
    )

    print("Verb Taxonomy Analysis")
    print("=" * 60)

    stats = get_verb_statistics()
    print(f"\nTotal ATOMIC_VERBS:    {stats['total_atomic']:,}")
    print(f"Unique ATOMIC_VERBS:   {stats['unique_atomic']:,}")
    print(f"Total COGNITIVE_VERBS: {stats['total_cognitive']:,}")
    print(f"Unique COGNITIVE_VERBS:{stats['unique_cognitive']:,}")

    # Duplicates
    dups = stats["duplicates"]
    if dups:
        print(f"\nDuplicates ({len(dups)}):")
        for v, count in sorted(dups.items(), key=lambda x: -x[1])[:15]:
            print(f"  {v}: {count}x")
        if len(dups) > 15:
            print(f"  ... and {len(dups) - 15} more")
    else:
        print("\nNo duplicates found!")

    # Verb stems
    stems = analyze_verb_stems()
    print(f"\nVerb stems with 3+ variants: {len(stems)}")
    top_stems = sorted(stems.items(), key=lambda x: -len(x[1]))[:10]
    for stem, variants in top_stems:
        print(f"  {stem}: {len(variants)} variants")

    # Domain coverage
    print("\nDomain Coverage:")
    coverage = check_domain_coverage()
    for domain, data in coverage.items():
        found = len(data["found"])
        total = len(data["expected"])
        missing = data["missing"]
        status = "✓" if not missing else "△"
        print(f"  {status} {domain}: {found}/{total}")
        if missing and args.verbose:
            print(f"      Missing: {', '.join(missing)}")


def cmd_qa_problems(args):
    """Show problematic verbs."""
    from taskpedia.postprocess import find_ambiguous_verbs, find_problematic_verbs

    print("Problematic Verbs in ATOMIC_VERBS")
    print("=" * 60)

    problems = find_problematic_verbs()
    if not problems:
        print("\nNo problematic verbs found!")
    else:
        for issue_type, verbs in problems.items():
            print(f"\n{issue_type.replace('_', ' ').title()} ({len(verbs)}):")
            for v in sorted(verbs)[:20]:
                print(f"  - {v}")
            if len(verbs) > 20:
                print(f"  ... and {len(verbs) - 20} more")

    # Ambiguous verbs
    ambiguous = find_ambiguous_verbs()
    if ambiguous:
        print(f"\nAmbiguous single words ({len(ambiguous)}):")
        for word, disambiguated in sorted(ambiguous.items())[:15]:
            if disambiguated:
                print(f"  {word} -> has {len(disambiguated)} disambiguated versions")
            else:
                print(f"  {word} -> NEEDS DISAMBIGUATION")
        if len(ambiguous) > 15:
            print(f"  ... and {len(ambiguous) - 15} more")


def cmd_qa_prune_internals(args):
    """Remove robot-internal nodes (joint torques, actuators, etc.)."""
    import json
    import re

    task_dir = Path(args.output)
    manifest_path = task_dir / "_manifest.json"

    if not manifest_path.exists():
        print(f"Error: {manifest_path} not found")
        sys.exit(1)

    print(f"Loading manifest from {manifest_path}...")
    with open(manifest_path) as f:
        data = json.load(f)

    nodes = data.get("nodes", {})
    print(f"Total nodes: {len(nodes):,}")

    # Patterns that indicate robot-internal control (not observable behavior)
    ROBOT_INTERNAL_PATTERNS = [
        # Joint/motor control
        r"joint.?torque",
        r"motor.?command",
        r"motor.?output",
        r"motor.?current",
        r"pid.?output",
        r"pid.?control",
        r"impedance.?control",
        r"flexor.?torque",
        r"extensor.?torque",
        r"corrective.?torque",
        r"apply.+torque(?!.*wrench)",
        r"compute.+torque",
        r"joint.?error",
        r"joint.?velocity",
        r"actuator.?command",
        r"actuator.?state",
        r"actuator.?torque",
        r"servo.?command",
        r"control.?law",
        r"control.?algorithm",
        r"torque.?signal",
        r"torque.?value",
        r"torque.?target",
        r"spool.?alignment",
        # Trajectory/path
        r"trajectory.?comput",
        r"gait.?trajectory",
        r"com.?shift",
        r"center.?of.?mass",
        # Sensor processing
        r"signal.?filter",
        r"sensor.?process",
        r"proprioceptive.?feedback",
        r"force.?feedback.?loop",
        # Balance/posture control
        r"postural.?control",
        r"balance.?control",
        r"micro.?adjustment",
        r"pose.?micro",
        # Body part + actuator/motor
        r"limb.?actuator",
        r"arm.?actuator",
        r"leg.?actuator",
        r"spine.?actuator",
        r"neck.?actuator",
        r"torso.?actuator",
        r"head.?actuator",
        r"hand.?actuator",
        r"facial.?actuator",
        r"body.?motor",
        r"arm.?motor",
        r"hand.?motor",
        # Specific joint torques
        r"ankle.?joint.?torque",
        r"hip.?joint.?torque",
        r"knee.?joint.?torque",
        r"shoulder.?joint.?torque",
        r"elbow.?joint.?torque",
        r"wrist.?joint.?torque",
        r"spine.?joint.?torque",
        r"neck.?joint.?torque",
        # Postural/balance internals
        r"postural.?shift",
        r"regulate.?contact.?force",
        r"contact.?force.?to.?target",
        r"normal.?force.?on",
        r"maintain.?stance",
        r"deviation.?metrics",
        r"pelvis.?deviation",
        r"pelvis.?position",
        r"lumbar.?posture",
        r"lumbar.?spine.?joints",
        r"sitting.?hip.?joints",
        r"tense.?abdominal",
        r"engage.?core.?muscles",
        r"pelvic.?tilt",
        r"shoulder.?girdle.?posture",
        r"trunk.?for.?balance",
        r"hips.?and.?trunk",
        r"balance.?corrections",
        r"position.?deltas",
        r"compliant.?contact",
        r"stabilize.?initial.?arm.?pose",
        r"palm.?contact",
        r"maintain.?position.?in.?zone",
        r"interacting.?limb",
        r"imbalance.?kinematics",
        # General low-level body control
        r"adjust.+joints?$",
        r"sense.+posture",
        r"sense.+deviation",
        r"sense.+kinematics",
        r"maintain.+posture",
        r"stabilize.+pose",
        r"execute.+corrections",
        r"regulate.+force",
        r"compliant.+retraction",
        r"force.?compliance",
        r"contact.?optimization",
        r"pose.?adjustments",
        r"girdle.?posture",
        r"spinal.?deviation",
        r"spine.?angles",
        r"spine.?alignment",
        r"balance.?deviation",
        r"balance.?response",
        # More low-level control
        r"actuate.?sagittal",
        r"actuate.?frontal",
        r"bilateral.?dorsiflexion",
        r"bilateral.?plantarflexion",
        r"bilateral.?hip",
        r"bilateral.?knee",
        r"bilateral.?ankle",
        r"sagittal.?ankle",
        r"frontal.?ankle",
        r"rectus.?abdominis",
        r"erector.?spinae",
        r"oblique.?activation",
        r"muscle.?activation",
        r"muscle.?tension",
        r"tendon.?tension",
        r"joint.?stiffness",
        r"joint.?damping",
        r"contact.?point",
        r"force.?vector",
        r"torque.?vector",
        r"velocity.?profile",
        r"acceleration.?profile",
        r"position.?profile",
        r"reference.?frame",
        r"coordinate.?transform",
        r"inverse.?kinematics",
        r"forward.?kinematics",
        r"jacobian",
        r"end.?effector.?pose",
        r"workspace.?limit",
        r"singularity",
        r"collision.?check",
        r"self.?collision",
    ]

    patterns = [re.compile(p, re.IGNORECASE) for p in ROBOT_INTERNAL_PATTERNS]

    robot_internal = set()
    for node_id, node in nodes.items():
        text = f"{node_id} {node.get('name', '')}"
        for pattern in patterns:
            if pattern.search(text):
                robot_internal.add(node_id)
                break

    print(f"Found {len(robot_internal):,} robot-internal nodes")

    if not robot_internal:
        print("Nothing to prune!")
        return

    # Get all descendants
    to_remove = set(robot_internal)
    changed = True
    while changed:
        changed = False
        for nid, node in nodes.items():
            if nid in to_remove:
                continue
            parent = node.get("parent_id", "")
            if parent in to_remove:
                to_remove.add(nid)
                changed = True

    print(f"Including descendants: {len(to_remove):,}")

    if args.dry_run:
        print("\n[DRY RUN] Would remove:")
        for n in sorted(to_remove)[:30]:
            print(f"  {n}")
        if len(to_remove) > 30:
            print(f"  ... and {len(to_remove) - 30} more")
        print(f"\nRun without --dry-run to actually remove")
        return

    # Remove nodes
    for nid in to_remove:
        if nid in nodes:
            del nodes[nid]

    # Update parent references
    for nid, node in nodes.items():
        if "children_ids" in node:
            node["children_ids"] = [c for c in node["children_ids"] if c not in to_remove]

    data["nodes"] = nodes

    print(f"Remaining nodes: {len(nodes):,}")
    print("Saving manifest...")
    with open(manifest_path, "w") as f:
        json.dump(data, f)

    print(f"Done! Removed {len(to_remove):,} robot-internal nodes")


def cmd_qa_coverage(args):
    """Show detailed domain coverage."""
    from taskpedia.postprocess import check_domain_coverage

    print("Domain Coverage Analysis")
    print("=" * 60)

    coverage = check_domain_coverage()

    for domain, data in sorted(coverage.items()):
        found = data["found"]
        missing = data["missing"]
        total = len(data["expected"])
        pct = (len(found) / total * 100) if total > 0 else 0

        print(f"\n{domain} ({len(found)}/{total} = {pct:.0f}%)")
        print("-" * 40)

        if found:
            print(f"  Found: {', '.join(sorted(found))}")
        if missing:
            print(f"  MISSING: {', '.join(sorted(missing))}")


def cmd_qa_test(args):
    """Run all data quality tests."""
    from taskpedia.postprocess import (
        run_comprehensive_domain_tests,
        run_domain_coverage_tests,
        run_generated_data_tests,
        run_verb_taxonomy_tests,
    )

    print("Running Data Quality Tests")
    print("=" * 60)

    task_dir = Path(args.output)

    # Run verb taxonomy tests
    print("\n[1] Verb Taxonomy Tests")
    print("-" * 40)
    verb_results = run_verb_taxonomy_tests(args.verbose)
    for status, msg in verb_results["details"]:
        icon = "✓" if status == "PASS" else "△" if status == "WARN" else "✗"
        print(f"  {icon} {msg}")

    # Run domain coverage tests
    print("\n[2] Domain Coverage Tests")
    print("-" * 40)
    coverage_results = run_domain_coverage_tests(args.verbose)
    for status, msg in coverage_results["details"]:
        icon = "✓" if status == "PASS" else "△" if status == "WARN" else "✗"
        print(f"  {icon} {msg}")

    # Run comprehensive domain tests
    print("\n[3] Comprehensive Domain Tests")
    print("-" * 40)
    comprehensive_results = run_comprehensive_domain_tests(args.verbose)
    # Only show failures and warnings unless verbose
    shown = 0
    for status, msg in comprehensive_results["details"]:
        if status != "PASS" or args.verbose:
            icon = "✓" if status == "PASS" else "△" if status == "WARN" else "✗"
            print(f"  {icon} {msg}")
            shown += 1
    if shown == 0:
        print(f"  ✓ All {len(comprehensive_results['details'])} domain tests passed")

    # Run generated data tests if directory exists
    if task_dir.exists():
        print("\n[4] Generated Data Tests")
        print("-" * 40)
        data_results = run_generated_data_tests(task_dir, args.verbose)
        for status, msg in data_results["details"]:
            icon = "✓" if status == "PASS" else "△" if status == "WARN" else "✗"
            print(f"  {icon} {msg}")
    else:
        data_results = {"passed": 0, "failed": 0, "warnings": 0}
        print("\n[4] Generated Data Tests")
        print("-" * 40)
        print("  (skipped - no task directory)")

    # Summary
    total_passed = (
        verb_results["passed"]
        + coverage_results["passed"]
        + comprehensive_results["passed"]
        + data_results["passed"]
    )
    total_failed = (
        verb_results["failed"]
        + coverage_results["failed"]
        + comprehensive_results["failed"]
        + data_results["failed"]
    )
    total_warnings = (
        verb_results["warnings"]
        + coverage_results["warnings"]
        + comprehensive_results["warnings"]
        + data_results["warnings"]
    )

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Passed:   {total_passed}")
    print(f"  Warnings: {total_warnings}")
    print(f"  Failed:   {total_failed}")

    if total_failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total_failed} test(s) failed")
        return 1


def cmd_cache_stats(args):
    """Show cache statistics."""
    try:
        from diskcache import Cache
    except ImportError:
        print("diskcache not installed")
        return

    cache_dir = Path("./.taskpedia_cache")
    if not cache_dir.exists():
        print("No cache found.")
        return

    cache = Cache(str(cache_dir))
    entries = len(cache)
    size_mb = cache.volume() / 1024 / 1024

    print(f"\nLLM Response Cache: {cache_dir}")
    print("=" * 40)
    print(f"  Entries:     {entries:>10,}")
    print(f"  Size:        {size_mb:>10.1f} MB")

    if entries > 0:
        # Estimate savings (avg ~2K tokens per cached response at $0.30/1M output)
        estimated_savings = entries * 2000 * 0.30 / 1_000_000
        print(f"  Est. savings:   ${estimated_savings:>7.2f}")

    print()


def cmd_cache_clear(args):
    """Clear the cache."""
    import shutil

    cache_dir = Path("./.taskpedia_cache")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print("Cache cleared.")
    else:
        print("No cache to clear.")


# ============================================================================
# DIVERSIFY - Tree gap finding and filling
# ============================================================================

DIVERSIFY_SYSTEM_PROMPT = """You are an expert at analyzing task hierarchies for embodied AI and humanoid robots.
Your goal is to identify GAPS in task coverage - missing activities that humans commonly perform.

You will be shown a tree structure of existing tasks. Analyze it and suggest NEW tasks that are:
1. NOT already covered (even implicitly)
2. Distinct from existing tasks
3. Concrete and actionable for robots
4. Representative of real human activities

Focus on:
- Missing everyday activities
- Cultural variations (different ways to do similar things)
- Professional/work tasks not covered
- Edge cases and less common but important tasks
- Activities for different contexts (home, work, outdoors, social)

Return JSON with suggested additions at each level."""


def analyze_tree_structure(task_dir: Path) -> dict:
    """Analyze the task hierarchy tree structure."""
    from taskpedia.hierarchy import NodeType, TaskGraph

    graph = TaskGraph(task_dir)

    # Build tree structure
    structure = {
        "domains": {},
        "stats": {
            "total_nodes": 0,
            "domains": 0,
            "tasks": 0,
            "subtasks": 0,
            "atomics": 0,
            "max_depth": 0,
            "sparse_branches": [],  # Branches with few children
            "deep_branches": [],  # Branches that go very deep
        },
    }

    # Analyze each domain
    for node in graph.iter_nodes():
        if node.node_type == NodeType.DOMAIN:
            domain_name = node.name
            children = graph.get_children(node.id)

            # Get task categories under this domain
            categories = {}
            for child in children:
                if child.node_type == NodeType.TASK:
                    cat_children = graph.get_children(child.id)
                    categories[child.name] = {
                        "count": len(cat_children),
                        "children": [c.name for c in cat_children[:10]],  # Sample
                    }

            structure["domains"][domain_name] = {
                "task_count": len(children),
                "categories": categories,
            }
            structure["stats"]["domains"] += 1

    # Count by type
    for node in graph.iter_nodes():
        structure["stats"]["total_nodes"] += 1
        if node.node_type == NodeType.TASK:
            structure["stats"]["tasks"] += 1
        elif node.node_type == NodeType.SUBTASK:
            structure["stats"]["subtasks"] += 1
        elif node.node_type == NodeType.ATOMIC:
            structure["stats"]["atomics"] += 1

    # Find sparse branches (domains/tasks with < 5 children)
    for node in graph.iter_nodes():
        if node.node_type in (NodeType.DOMAIN, NodeType.TASK):
            children = graph.get_children(node.id)
            if 0 < len(children) < 5:
                structure["stats"]["sparse_branches"].append(
                    {
                        "name": node.name,
                        "type": node.node_type.value,
                        "children": len(children),
                    }
                )

    return structure


def get_tree_text(task_dir: Path, max_depth: int = 5) -> str:
    """Get a text representation of the tree structure (directories only, no yaml)."""
    import subprocess

    result = subprocess.run(
        ["tree", str(task_dir), "-L", str(max_depth), "-d", "--noreport"],
        capture_output=True,
        text=True,
    )
    return result.stdout


def cmd_diversify(args):
    """Analyze tree for gaps and generate new tasks to fill them."""
    import json
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from taskpedia.core import ProgressTracker, RateLimiter
    from taskpedia.data import get_action_categories_summary
    from taskpedia.generation import LLMClient, LLMConfig, MockLLMClient
    from taskpedia.hierarchy import NodeType, SeedSource, TaskGraph, TaskNode

    task_dir = Path(args.output)
    if not task_dir.exists():
        print(f"Error: {task_dir} not found. Run 'taskpedia init' first.")
        sys.exit(1)

    print("=" * 60)
    print("  TREE DIVERSIFICATION & GAP FILLING")
    print("=" * 60)

    # Get action categories for seeding prompts
    action_categories = get_action_categories_summary()

    # Step 1: Analyze current structure
    print("\n[1] Analyzing current tree structure...")
    structure = analyze_tree_structure(task_dir)
    tree_text = get_tree_text(task_dir, max_depth=2)  # L2 tree for context

    print(f"    Domains:  {structure['stats']['domains']}")
    print(f"    Tasks:    {structure['stats']['tasks']:,}")
    print(f"    Subtasks: {structure['stats']['subtasks']:,}")
    print(f"    Atomics:  {structure['stats']['atomics']:,}")
    print(f"    Sparse branches: {len(structure['stats']['sparse_branches'])}")

    # Step 2: Identify gaps using LLM
    print("\n[2] Identifying gaps in coverage...")

    # Concurrency settings
    max_workers = getattr(args, "workers", 32)
    rpm_limit = getattr(args, "rpm", 800)

    # Initialize rate limiter from shared utilities
    rate_limiter = RateLimiter(rpm=rpm_limit)

    if args.mock:
        client = MockLLMClient(delay=0.1)
    else:
        llm_config = LLMConfig(model=args.model, thinking_budget=0)
        client = LLMClient(config=llm_config)

    # Show cache status
    if hasattr(client, "_cache") and client._cache:
        stats = client.cache_stats
        print(f"    Cache: {stats.get('hits', 0)} hits, {stats.get('misses', 0)} misses")

    print(f"    Rate limit: {rpm_limit} RPM | Workers: {max_workers}")

    graph = TaskGraph(task_dir)

    # Thread-safe counters
    nodes_created = [0]
    gaps_found = []
    print_lock = threading.Lock()

    def rate_limited_generate(prompt, system_prompt, max_retries=5):
        """Generate with rate limiting and retries using tenacity-style logic."""
        last_exception = None
        for attempt in range(max_retries):
            rate_limiter.acquire()
            try:
                return client.generate(prompt, system_prompt, use_thinking=False)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    import time

                    wait_time = min(1.0 * (2.0**attempt), 60.0)
                    time.sleep(wait_time)
                continue
        if last_exception:
            raise last_exception
        return None

    # Get domains to analyze
    domains = [n for n in graph.iter_nodes() if n.node_type == NodeType.DOMAIN]

    if args.domain:
        # Filter to specific domain
        domains = [d for d in domains if args.domain.lower() in d.name.lower()]

    print(f"    Analyzing {len(domains)} domains with {max_workers} workers...")
    print(f"    (Ctrl-C is safe - LLM responses are cached)\n")

    def parse_json_response(response: str) -> dict:
        """Parse JSON from LLM response."""
        json_text = response.strip()
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0]
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0]
        return json.loads(json_text.strip())

    def analyze_domain(domain):
        """Analyze a single domain for gaps (runs in thread)."""
        domain_tasks = graph.get_children(domain.id)
        task_names = [t.name for t in domain_tasks]

        prompt = f"""Analyze this domain for MISSING tasks that humans commonly do:

DOMAIN: {domain.name}
EXISTING TASKS ({len(task_names)}):
{chr(10).join(f'  - {name}' for name in task_names[:50])}
{'  ... and more' if len(task_names) > 50 else ''}

CURRENT TREE STRUCTURE (L2 depth - to avoid overlaps with other domains):
{tree_text}

ACTION VERB CATEGORIES (use these to inspire task ideas):
{action_categories}

What important human activities are MISSING from this domain?
IMPORTANT: Check the tree structure above to avoid suggesting tasks that belong to OTHER domains.

Consider activities involving:
- Different action types from the categories above
- Everyday activities most people do
- Professional/work variations
- Cultural/regional variations
- Activities for different demographics (children, elderly, etc.)
- Seasonal or occasional activities
- Technology-related modern activities

Return JSON:
{{
    "domain": "{domain.name}",
    "analysis": "brief gap analysis",
    "missing_tasks": [
        {{
            "name": "task name (lowercase_with_underscores)",
            "description": "what this task involves",
            "why_important": "why this gap matters for robot training"
        }}
    ]
}}

Return 5-15 missing tasks that would significantly improve coverage."""

        try:
            response = rate_limited_generate(prompt, DIVERSIFY_SYSTEM_PROMPT)
            result = parse_json_response(response)
            missing = result.get("missing_tasks", [])
            return {
                "domain": domain,
                "domain_tasks": domain_tasks,
                "missing": missing,
                "error": None,
            }
        except Exception as e:
            return {"domain": domain, "domain_tasks": [], "missing": [], "error": str(e)}

    def analyze_sparse_branch(branch_info):
        """Analyze a sparse branch for expansion (runs in thread)."""
        branch_name = branch_info["name"]

        # Find the node
        node = None
        for n in graph.iter_nodes():
            if n.name == branch_name:
                node = n
                break

        if not node:
            return {"branch": branch_info, "node": None, "missing": [], "error": "not found"}

        existing_children = graph.get_children(node.id)
        child_names = [c.name for c in existing_children]

        prompt = f"""This task branch has very few subtasks and needs expansion:

TASK: {node.name}
PARENT TYPE: {node.node_type.value}
EXISTING SUBTASKS ({len(child_names)}):
{chr(10).join(f'  - {name}' for name in child_names)}

ACTION VERB CATEGORIES (use these to inspire subtask ideas):
{action_categories}

What subtasks are MISSING? Break down "{node.name}" into more specific steps/variations.
Consider different action types from the categories above.

Return JSON:
{{
    "task": "{node.name}",
    "missing_subtasks": [
        {{
            "name": "subtask name (lowercase_with_underscores)",
            "description": "what this involves",
            "is_atomic": false
        }}
    ]
}}

Return 5-10 missing subtasks."""

        try:
            response = rate_limited_generate(prompt, DIVERSIFY_SYSTEM_PROMPT)
            result = parse_json_response(response)
            missing = result.get("missing_subtasks", [])
            return {
                "branch": branch_info,
                "node": node,
                "child_names": child_names,
                "missing": missing,
                "error": None,
            }
        except Exception as e:
            return {
                "branch": branch_info,
                "node": node,
                "child_names": [],
                "missing": [],
                "error": str(e),
            }

    # Process domains concurrently
    domain_progress = ProgressTracker(total=len(domains))
    domain_results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_domain, d): d for d in domains}

        for future in as_completed(futures):
            result = future.result()
            domain = result["domain"]

            with print_lock:
                count, rpm = domain_progress.increment(error=bool(result["error"]))

                if result["error"]:
                    print(
                        f"    [{count}/{len(domains)}] {domain.name}... ERROR: {result['error']} ({rpm:.0f} RPM)",
                        flush=True,
                    )
                else:
                    print(
                        f"    [{count}/{len(domains)}] {domain.name}... found {len(result['missing'])} gaps ({rpm:.0f} RPM)",
                        flush=True,
                    )

            domain_results.append(result)

    # Process domain results (create nodes) - sequential to avoid race conditions
    print(f"\n    Creating task nodes...")
    for result in domain_results:
        if result["error"] or not result["missing"]:
            continue

        domain = result["domain"]
        domain_tasks = result["domain_tasks"]
        existing = [t.name for t in domain_tasks]

        if not args.dry_run:
            for task_info in result["missing"][: args.max_per_domain]:
                task_name = task_info.get("name", "").strip()
                if not task_name:
                    continue

                task_name = task_name.lower().replace(" ", "_").replace("-", "_")
                if task_name in existing:
                    continue

                new_task = TaskNode(
                    id=TaskNode.make_id(task_name, domain.id),
                    name=task_name,
                    node_type=NodeType.TASK,
                    parent_id=domain.id,
                    description=task_info.get("description", ""),
                    sources=[SeedSource.LLM_GENERATED],
                    tags=["gap_filled", "diversification"],
                )

                try:
                    graph.add_node(new_task)
                    nodes_created[0] += 1
                    gaps_found.append(
                        {
                            "domain": domain.name,
                            "task": task_name,
                            "description": task_info.get("description", ""),
                        }
                    )
                except ValueError:
                    pass

    # Step 3: Analyze sparse branches concurrently
    print(f"\n[3] Analyzing sparse branches...")
    sparse = structure["stats"]["sparse_branches"][:20]

    if not sparse:
        print("    No sparse branches found.")
    else:
        sparse_progress = ProgressTracker(total=len(sparse))
        sparse_results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(analyze_sparse_branch, b): b for b in sparse}

            for future in as_completed(futures):
                result = future.result()
                branch = result["branch"]

                with print_lock:
                    count, rpm = sparse_progress.increment(error=bool(result["error"]))

                    if result["error"]:
                        print(
                            f"    [{count}/{len(sparse)}] {branch['name']}... {result['error']} ({rpm:.0f} RPM)",
                            flush=True,
                        )
                    else:
                        print(
                            f"    [{count}/{len(sparse)}] {branch['name']}... found {len(result['missing'])} ({rpm:.0f} RPM)",
                            flush=True,
                        )

                sparse_results.append(result)

        # Process sparse branch results
        print(f"\n    Creating subtask nodes...")
        for result in sparse_results:
            if result["error"] or not result["missing"] or not result["node"]:
                continue

            node = result["node"]
            child_names = result.get("child_names", [])

            if not args.dry_run:
                for subtask_info in result["missing"][:5]:
                    subtask_name = subtask_info.get("name", "").strip()
                    if not subtask_name:
                        continue

                    subtask_name = subtask_name.lower().replace(" ", "_").replace("-", "_")
                    if subtask_name in child_names:
                        continue

                    child_type = (
                        NodeType.ATOMIC if subtask_info.get("is_atomic") else NodeType.SUBTASK
                    )

                    new_subtask = TaskNode(
                        id=TaskNode.make_id(subtask_name, node.id),
                        name=subtask_name,
                        node_type=child_type,
                        parent_id=node.id,
                        description=subtask_info.get("description", ""),
                        sources=[SeedSource.LLM_GENERATED],
                        tags=["gap_filled", "sparse_expansion"],
                    )

                    try:
                        graph.add_node(new_subtask)
                        nodes_created[0] += 1
                    except ValueError:
                        pass

    # Step 4: Diversify domains (suggest new top-level domains)
    new_domains_suggested = []
    if getattr(args, "diversify_domains", False):
        print(f"\n[4] Analyzing for missing domains...")

        # Get all existing domain names
        existing_domain_names = [d.name for d in domains]

        domain_diversify_prompt = f"""Analyze this task hierarchy for MISSING TOP-LEVEL DOMAINS.

CURRENT TREE STRUCTURE (L2 depth):
{tree_text}

EXISTING DOMAINS ({len(existing_domain_names)}):
{chr(10).join(f'  - {name}' for name in existing_domain_names)}

ACTION VERB CATEGORIES (use these to identify gaps):
{action_categories}

What major categories of human activity are COMPLETELY MISSING as top-level domains?

Consider:
- Activities not covered by any existing domain
- Professional domains (specific industries/trades)
- Life stage activities (childhood, elderly care)
- Cultural/regional activities
- Modern technology-related domains
- Recreational/hobby domains
- Emergency/crisis response domains

IMPORTANT: Only suggest domains that are truly DISTINCT from existing ones.
Do NOT suggest domains that would overlap with existing ones.

Return JSON:
{{
    "analysis": "brief analysis of domain coverage gaps",
    "missing_domains": [
        {{
            "name": "domain_name (lowercase_with_underscores)",
            "description": "what this domain covers",
            "why_distinct": "why this doesn't overlap with existing domains",
            "example_tasks": ["task1", "task2", "task3"]
        }}
    ]
}}

Return 3-8 truly distinct missing domains."""

        try:
            response = rate_limited_generate(domain_diversify_prompt, DIVERSIFY_SYSTEM_PROMPT)
            result = parse_json_response(response)
            new_domains_suggested = result.get("missing_domains", [])

            print(f"    Found {len(new_domains_suggested)} potential new domains")

            if not args.dry_run:
                for domain_info in new_domains_suggested:
                    domain_name = domain_info.get("name", "").strip()
                    if not domain_name:
                        continue

                    domain_name = domain_name.lower().replace(" ", "_").replace("-", "_")
                    if domain_name in existing_domain_names:
                        continue

                    new_domain = TaskNode(
                        id=TaskNode.make_id(domain_name, "root"),
                        name=domain_name,
                        node_type=NodeType.DOMAIN,
                        parent_id="root",
                        description=domain_info.get("description", ""),
                        sources=[SeedSource.LLM_GENERATED],
                        tags=["gap_filled", "domain_diversification"],
                    )

                    try:
                        graph.add_node(new_domain)
                        nodes_created[0] += 1
                        print(f"      + {domain_name}")
                    except ValueError:
                        pass

        except Exception as e:
            print(f"    Error analyzing domains: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("  DIVERSIFICATION COMPLETE")
    print("=" * 60)
    print(f"  Domains analyzed: {len(domains)}")
    print(f"  Sparse branches:  {len(sparse)}")
    print(f"  New domains suggested: {len(new_domains_suggested)}")
    print(f"  Nodes created:    {nodes_created[0]}")

    if args.dry_run:
        print("\n  [DRY RUN - no changes made]")

    if gaps_found and args.verbose:
        print("\n  Sample gaps filled:")
        for gap in gaps_found[:10]:
            print(f"    [{gap['domain']}] {gap['task']}")

    print("\n  Next: Run 'taskpedia qa test' to verify coverage")
    print("        Run 'taskpedia generate' to decompose new tasks")


def cmd_judge_analyze(args):
    """Analyze reject log to identify patterns."""
    from taskpedia.quality import get_reject_log

    log = get_reject_log()
    analysis = log.analyze()

    print("\n" + "=" * 60)
    print("  REJECT LOG ANALYSIS")
    print("=" * 60)
    print(f"  Total rejects: {analysis.get('total', 0):,}")

    if analysis.get("total", 0) == 0:
        print("\n  No rejections logged yet.")
        print("  Run generation with judge enabled to collect data.")
        return

    print("\n  By Reason:")
    for reason, count in analysis.get("by_reason", {}).items():
        print(f"    {reason:25} {count:>8,}")

    if analysis.get("top_patterns"):
        print("\n  Top Rejection Patterns:")
        for pattern, count in analysis["top_patterns"]:
            print(f"    {pattern[:50]:50} {count:>8,}x")

    if analysis.get("recent_samples"):
        print("\n  Recent Rejects (sample):")
        for sample in analysis["recent_samples"][:10]:
            print(f"    - {sample}")

    print("\n  Next: Run 'taskpedia judge improve' to get prompt suggestions")


def cmd_judge_improve(args):
    """Suggest prompt improvements based on reject log."""
    from taskpedia.generation import LLMClient, LLMConfig, MockLLMClient
    from taskpedia.generator import SYSTEM_PROMPT
    from taskpedia.quality import PromptImprover, get_reject_log

    log = get_reject_log()
    analysis = log.analyze()

    if analysis.get("total", 0) == 0:
        print("No rejections logged yet. Run generation first.")
        return

    print("\n" + "=" * 60)
    print("  PROMPT IMPROVEMENT ANALYSIS")
    print("=" * 60)
    print(f"  Analyzing {analysis['total']:,} rejections...")

    # Initialize LLM
    if args.mock:
        client = MockLLMClient()
    else:
        llm_config = LLMConfig(model=args.model, thinking_budget=1024)
        client = LLMClient(config=llm_config)

    improver = PromptImprover(client, log)

    print("\n  Generating suggestions (this may take a moment)...\n")
    suggestions = improver.suggest_improvements(SYSTEM_PROMPT)

    print("=" * 60)
    print(suggestions)
    print("=" * 60)

    if args.apply:
        print("\n  Generating improved prompt...")
        improved = improver.generate_improved_prompt(SYSTEM_PROMPT, apply_suggestions=True)

        output_file = Path(args.output) / "improved_prompt.txt"
        output_file.write_text(improved)
        print(f"\n  Improved prompt saved to: {output_file}")
        print("  Review and manually update generator.py if appropriate.")


def cmd_judge_clear(args):
    """Clear reject log."""
    from taskpedia.quality import get_reject_log

    log = get_reject_log()

    if not args.yes:
        response = input("Clear all rejection logs? [y/N] ")
        if response.lower() not in ("y", "yes"):
            print("Cancelled.")
            return

    log.clear()
    print("Reject log cleared.")


def main():
    parser = argparse.ArgumentParser(
        prog="taskpedia",
        description="TASKPEDIA - Hierarchical Task Decomposition for Embodied AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  taskpedia init                    # Initialize from O*NET + Life Activities
  taskpedia generate -n 100000      # Generate 100K tasks with LLM
  taskpedia judge analyze           # Analyze rejection patterns
  taskpedia judge improve           # Get prompt improvement suggestions
  taskpedia show stats              # View statistics
  taskpedia show tree               # View as tree
  taskpedia export --format jsonl   # Export to JSONL
  taskpedia upload --repo org/name  # Upload to HuggingFace
""",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Task hierarchy directory (default: {DEFAULT_OUTPUT})",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # ─── INIT ───────────────────────────────────────────────
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize hierarchy from seed data (O*NET + Life Activities)",
    )
    init_parser.set_defaults(func=cmd_init)

    # ─── GENERATE ───────────────────────────────────────────
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate tasks using LLM decomposition",
    )
    gen_parser.add_argument(
        "-n",
        "--max-tasks",
        type=int,
        default=100000,
        help="Max new nodes to generate this session (default: 100000)",
    )
    gen_parser.add_argument(
        "--model",
        default="models/gemini-2.5-flash",
        help="LLM model (default: gemini-2.5-flash)",
    )
    gen_parser.add_argument(
        "--workers",
        type=int,
        default=64,
        help="Parallel workers (default: 64)",
    )
    gen_parser.add_argument(
        "--queue-size",
        type=int,
        default=500,
        help="Work queue size (default: 500)",
    )
    gen_parser.add_argument(
        "--rpm",
        type=int,
        default=1000,
        help="Rate limit RPM (default: 1000)",
    )
    gen_parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock LLM (no API calls)",
    )
    gen_parser.add_argument(
        "--no-tui",
        action="store_true",
        help="Disable TUI, use simple progress",
    )
    gen_parser.add_argument(
        "--no-judge",
        action="store_true",
        help="Disable quality judge (not recommended)",
    )
    gen_parser.add_argument(
        "--llm-judge",
        action="store_true",
        help="Use LLM judge in addition to regex (slower but more accurate)",
    )
    gen_parser.set_defaults(func=cmd_generate)

    # ─── SHOW (subcommands) ─────────────────────────────────
    show_parser = subparsers.add_parser(
        "show",
        help="View hierarchy (tree, stats, search)",
    )
    show_sub = show_parser.add_subparsers(dest="show_cmd", metavar="what")

    # show tree
    tree_parser = show_sub.add_parser("tree", help="Display as tree")
    tree_parser.add_argument(
        "-d",
        "--depth",
        type=int,
        default=3,
        help="Max depth (default: 3)",
    )
    tree_parser.set_defaults(func=cmd_show_tree)

    # show stats
    stats_parser = show_sub.add_parser("stats", help="Show statistics")
    stats_parser.set_defaults(func=cmd_show_stats)

    # show search
    search_parser = show_sub.add_parser("search", help="Search tasks")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=20,
        help="Max results (default: 20)",
    )
    search_parser.set_defaults(func=cmd_show_search)

    # ─── EXPORT ─────────────────────────────────────────────
    export_parser = subparsers.add_parser(
        "export",
        help="Export to file (jsonl, json, tree)",
    )
    export_parser.add_argument(
        "-f",
        "--format",
        choices=["jsonl", "json", "tree"],
        default="jsonl",
        help="Format (default: jsonl)",
    )
    export_parser.add_argument(
        "--file",
        help="Output file path",
    )
    export_parser.set_defaults(func=cmd_export)

    # ─── UPLOAD ─────────────────────────────────────────────
    upload_parser = subparsers.add_parser(
        "upload",
        help="Upload to HuggingFace",
    )
    upload_parser.add_argument(
        "--repo",
        default="Sentient-x/taskpedia",
        help="HuggingFace repo (default: Sentient-x/taskpedia)",
    )
    upload_parser.add_argument(
        "--public",
        action="store_true",
        help="Make public (default: private)",
    )
    upload_parser.set_defaults(func=cmd_upload)

    # ─── DOWNLOAD ───────────────────────────────────────────
    download_parser = subparsers.add_parser(
        "download",
        help="Download from HuggingFace",
    )
    download_parser.add_argument(
        "--repo",
        default="Sentient-x/taskpedia",
        help="HuggingFace repo (default: Sentient-x/taskpedia)",
    )
    download_parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if local copy is up-to-date",
    )
    download_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompts (auto-yes)",
    )
    download_parser.set_defaults(func=cmd_download)

    # ─── JUDGE (subcommands) ────────────────────────────────
    judge_parser = subparsers.add_parser(
        "judge",
        help="Quality judge (analyze rejects, improve prompts)",
    )
    judge_sub = judge_parser.add_subparsers(dest="judge_cmd", metavar="action")

    judge_analyze = judge_sub.add_parser("analyze", help="Analyze rejection patterns")
    judge_analyze.set_defaults(func=cmd_judge_analyze)

    judge_improve = judge_sub.add_parser("improve", help="Suggest prompt improvements")
    judge_improve.add_argument(
        "--model",
        default="models/gemini-2.5-flash",
        help="LLM model (default: gemini-2.5-flash)",
    )
    judge_improve.add_argument(
        "--mock",
        action="store_true",
        help="Use mock LLM",
    )
    judge_improve.add_argument(
        "--apply",
        action="store_true",
        help="Generate rewritten prompt (saved to improved_prompt.txt)",
    )
    judge_improve.set_defaults(func=cmd_judge_improve)

    judge_clear = judge_sub.add_parser("clear", help="Clear reject log")
    judge_clear.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation",
    )
    judge_clear.set_defaults(func=cmd_judge_clear)

    # ─── CACHE (subcommands) ────────────────────────────────
    cache_parser = subparsers.add_parser(
        "cache",
        help="Manage LLM cache",
    )
    cache_sub = cache_parser.add_subparsers(dest="cache_cmd", metavar="action")

    cache_stats = cache_sub.add_parser("stats", help="Show cache stats")
    cache_stats.set_defaults(func=cmd_cache_stats)

    cache_clear = cache_sub.add_parser("clear", help="Clear cache")
    cache_clear.set_defaults(func=cmd_cache_clear)

    # ─── QA (subcommands) ───────────────────────────────────
    qa_parser = subparsers.add_parser(
        "qa",
        help="Quality assurance (analyze, clean, verbs, problems, coverage)",
    )
    qa_sub = qa_parser.add_subparsers(dest="qa_cmd", metavar="action")

    # qa analyze
    qa_analyze = qa_sub.add_parser("analyze", help="Analyze generated data quality")
    qa_analyze.set_defaults(func=cmd_qa_analyze)

    # qa clean
    qa_clean = qa_sub.add_parser("clean", help="Remove bad nodes")
    qa_clean.add_argument("--dry-run", action="store_true", help="Preview without removing")
    qa_clean.set_defaults(func=cmd_qa_clean)

    # qa verbs
    qa_verbs = qa_sub.add_parser("verbs", help="Analyze verb taxonomy")
    qa_verbs.add_argument("-v", "--verbose", action="store_true", help="Show details")
    qa_verbs.set_defaults(func=cmd_qa_verbs)

    # qa problems
    qa_problems = qa_sub.add_parser("problems", help="Show problematic verbs")
    qa_problems.set_defaults(func=cmd_qa_problems)

    # qa coverage
    qa_coverage = qa_sub.add_parser("coverage", help="Show domain coverage")
    qa_coverage.set_defaults(func=cmd_qa_coverage)

    # qa test
    qa_test = qa_sub.add_parser("test", help="Run all data quality tests")
    qa_test.add_argument("-v", "--verbose", action="store_true", help="Show all details")
    qa_test.set_defaults(func=cmd_qa_test)

    # qa prune-internals
    qa_prune = qa_sub.add_parser(
        "prune-internals", help="Remove robot-internal nodes (torques, actuators, etc.)"
    )
    qa_prune.add_argument("--dry-run", action="store_true", help="Preview without removing")
    qa_prune.set_defaults(func=cmd_qa_prune_internals)

    # ─── DIVERSIFY ──────────────────────────────────────────
    diversify_parser = subparsers.add_parser(
        "diversify",
        help="Analyze tree for gaps and generate tasks to fill them",
    )
    diversify_parser.add_argument(
        "--domain",
        help="Only analyze specific domain (partial match)",
    )
    diversify_parser.add_argument(
        "--max-per-domain",
        type=int,
        default=15,
        help="Max new tasks per domain (default: 15)",
    )
    diversify_parser.add_argument(
        "--model",
        default="models/gemini-2.5-flash",
        help="LLM model (default: gemini-2.5-flash)",
    )
    diversify_parser.add_argument(
        "--workers",
        type=int,
        default=32,
        help="Parallel workers for LLM calls (default: 32)",
    )
    diversify_parser.add_argument(
        "--rpm",
        type=int,
        default=800,
        help="Rate limit RPM (default: 800)",
    )
    diversify_parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock LLM (no API calls)",
    )
    diversify_parser.add_argument(
        "--diversify-domains",
        action="store_true",
        help="Also suggest new domains based on gaps",
    )
    diversify_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze only, don't create nodes",
    )
    diversify_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed progress",
    )
    diversify_parser.set_defaults(func=cmd_diversify)

    # ─── PARSE & RUN ────────────────────────────────────────
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Handle subcommand groups
    if args.command == "show":
        if not args.show_cmd:
            show_parser.print_help()
            sys.exit(0)
    elif args.command == "judge":
        if not args.judge_cmd:
            judge_parser.print_help()
            sys.exit(0)
    elif args.command == "cache":
        if not args.cache_cmd:
            cache_parser.print_help()
            sys.exit(0)
    elif args.command == "qa":
        if not args.qa_cmd:
            qa_parser.print_help()
            sys.exit(0)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
