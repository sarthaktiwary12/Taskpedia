#!/usr/bin/env python3
"""
Comprehensive Dataset Improvement Pipeline for Taskpedia.

This script orchestrates:
1. Quality assessment of existing tasks
2. Cleaning of low-quality tasks
3. Expansion across all domains with improved prompts
4. Continuous quality monitoring
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set

# Import quality control patterns
from quality_control import ALL_BAD_PATTERNS, GOOD_MANIPULATION_VERBS
import re


class DatasetImprover:
    """Orchestrates dataset quality improvement and expansion."""

    def __init__(self, manifest_path: str = "taskpedia-web/public/data/manifest.json"):
        self.manifest_path = Path(manifest_path)
        self.manifest = self._load_manifest()
        self.bad_tasks: Set[str] = set()
        self.quality_issues: Dict[str, List[str]] = {}

    def _load_manifest(self) -> Dict:
        """Load the task manifest."""
        if not self.manifest_path.exists():
            print(f"❌ Manifest not found at {self.manifest_path}")
            sys.exit(1)
        return json.loads(self.manifest_path.read_text())

    def assess_quality(self) -> Dict:
        """Assess quality of all tasks in the manifest."""
        print("\n" + "="*80)
        print("PHASE 1: QUALITY ASSESSMENT")
        print("="*80 + "\n")

        stats = {
            "total": len(self.manifest),
            "by_type": {},
            "quality_issues": {},
            "bad_tasks": [],
        }

        # Compile patterns
        bad_patterns = [(p, re.compile(p, re.IGNORECASE)) for p in ALL_BAD_PATTERNS]

        for task_id, task in self.manifest.items():
            node_type = task.get("node_type", "unknown")
            stats["by_type"][node_type] = stats["by_type"].get(node_type, 0) + 1

            name = task.get("name", "").lower()

            # Check against bad patterns
            issues = []
            for pattern_str, pattern_re in bad_patterns:
                if pattern_re.search(name):
                    issues.append(f"Matches bad pattern: {pattern_str}")

            # Check if it lacks good manipulation verbs (for atomic/subtask nodes)
            if node_type in ["atomic", "subtask"]:
                has_good_verb = any(verb in name for verb in GOOD_MANIPULATION_VERBS)
                if not has_good_verb and node_type == "atomic":
                    issues.append("Atomic task lacks manipulation verb")

            # Track issues
            if issues:
                self.bad_tasks.add(task_id)
                self.quality_issues[task_id] = issues
                for issue in issues:
                    stats["quality_issues"][issue] = stats["quality_issues"].get(issue, 0) + 1
                stats["bad_tasks"].append({
                    "id": task_id,
                    "name": task["name"],
                    "type": node_type,
                    "issues": issues
                })

        # Print summary
        print(f"📊 Total tasks analyzed: {stats['total']:,}")
        print(f"\n📈 Breakdown by type:")
        for t, count in sorted(stats["by_type"].items()):
            print(f"   {t:12s}: {count:,}")

        print(f"\n⚠️  Quality issues found: {len(self.bad_tasks):,} tasks ({len(self.bad_tasks)/stats['total']*100:.1f}%)")
        print(f"\n🔍 Top issues:")
        for issue, count in sorted(stats["quality_issues"].items(), key=lambda x: -x[1])[:10]:
            print(f"   {count:5,}x  {issue}")

        # Save bad tasks for review
        bad_tasks_file = Path("bad_tasks_identified.json")
        bad_tasks_file.write_text(json.dumps(stats["bad_tasks"], indent=2))
        print(f"\n💾 Bad tasks saved to: {bad_tasks_file}")

        return stats

    def clean_dataset(self, dry_run: bool = True):
        """Remove tasks that fail quality checks."""
        print("\n" + "="*80)
        print("PHASE 2: DATASET CLEANING")
        print("="*80 + "\n")

        if not self.bad_tasks:
            print("✅ No bad tasks to clean!")
            return

        print(f"🗑️  Found {len(self.bad_tasks):,} tasks to remove")

        if dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made")
            print("\nTo actually clean, run with: dry_run=False")
            return

        # Create cleaned manifest
        cleaned = {k: v for k, v in self.manifest.items() if k not in self.bad_tasks}

        # Update children references
        for task_id, task in cleaned.items():
            if "children_ids" in task:
                task["children_ids"] = [
                    child_id for child_id in task["children_ids"]
                    if child_id not in self.bad_tasks
                ]

        # Save cleaned manifest
        backup_path = self.manifest_path.with_suffix(".backup.json")
        self.manifest_path.rename(backup_path)
        print(f"💾 Backup saved to: {backup_path}")

        self.manifest_path.write_text(json.dumps(cleaned, indent=2))
        print(f"✅ Cleaned manifest saved: {len(cleaned):,} tasks remaining")

        # Update stats
        self._update_stats(cleaned)

    def _update_stats(self, manifest: Dict):
        """Update stats.json with new counts."""
        stats_path = self.manifest_path.parent / "stats.json"
        stats = {
            "trainable": {
                "total": len(manifest),
                "by_type": {}
            }
        }

        for task in manifest.values():
            node_type = task.get("node_type", "unknown")
            stats["trainable"]["by_type"][node_type] = \
                stats["trainable"]["by_type"].get(node_type, 0) + 1

        stats_path.write_text(json.dumps(stats, indent=2))
        print(f"📊 Stats updated: {stats_path}")

    def expand_dataset(self, target_tasks: int = 100000, domains: List[str] = None):
        """Expand dataset with high-quality robot-relevant tasks."""
        print("\n" + "="*80)
        print("PHASE 3: DATASET EXPANSION")
        print("="*80 + "\n")

        current_count = len(self.manifest)
        tasks_needed = target_tasks - current_count

        print(f"📈 Current tasks: {current_count:,}")
        print(f"🎯 Target tasks: {target_tasks:,}")
        print(f"➕ Need to generate: {tasks_needed:,}")

        if tasks_needed <= 0:
            print("✅ Already at target!")
            return

        # Check if we need to initialize
        hierarchy_dir = Path("task_hierarchy")
        if not hierarchy_dir.exists():
            print("\n🚀 Initializing task hierarchy...")
            subprocess.run(["taskpedia", "init", "-o", str(hierarchy_dir)], check=True)

        # Set up environment
        if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
            print("\n⚠️  WARNING: No GEMINI_API_KEY or GOOGLE_API_KEY found!")
            print("Set your API key: export GEMINI_API_KEY='your-key'")
            return

        print("\n🤖 Starting generation with improved quality controls...")
        print(f"   - Workers: 128 (high parallelism)")
        print(f"   - RPM limit: 1000 (Gemini Flash Tier 1)")
        print(f"   - Quality judge: ENABLED (regex + patterns)")
        print(f"   - Validation: ENABLED (verb taxonomy)")
        print(f"   - Max depth: 5 (prevents over-decomposition)")

        # Run generation
        cmd = [
            "taskpedia", "generate",
            "-n", str(tasks_needed),
            "--workers", "128",
            "--rpm", "1000",
            "-o", str(hierarchy_dir)
        ]

        print(f"\n🔧 Command: {' '.join(cmd)}")
        print("\nStarting generation... (Press Ctrl+C to stop gracefully)\n")

        try:
            subprocess.run(cmd, check=False)  # Don't fail on interrupt
        except KeyboardInterrupt:
            print("\n⚠️  Generation interrupted by user")

        print("\n✅ Generation phase complete!")
        print("Next: Run 'taskpedia export -f json' to update web UI data")

    def continuous_quality_monitor(self):
        """Set up continuous quality monitoring."""
        print("\n" + "="*80)
        print("PHASE 4: CONTINUOUS QUALITY MONITORING")
        print("="*80 + "\n")

        reject_log = Path("taskpedia_rejects.jsonl")

        if reject_log.exists():
            print(f"📋 Reject log found: {reject_log}")

            # Analyze rejects
            print("\n🔍 Analyzing rejection patterns...")
            subprocess.run(["taskpedia", "judge", "analyze"], check=False)

            # Get improvement suggestions
            print("\n💡 Getting prompt improvement suggestions...")
            subprocess.run(["taskpedia", "judge", "improve"], check=False)

            print("\n✅ Quality monitoring setup complete!")
            print("\nTo apply improvements:")
            print("  1. Review suggestions above")
            print("  2. Update generator.py SYSTEM_PROMPT manually")
            print("  3. Run: taskpedia judge clear  (to start fresh)")
        else:
            print("ℹ️  No reject log yet - will be created during generation")
            print("   Run 'taskpedia judge analyze' after generation to review")

    def run_full_pipeline(self, clean: bool = False, expand: bool = True, target: int = 100000):
        """Run the complete improvement pipeline."""
        print("\n" + "="*80)
        print("🚀 TASKPEDIA COMPREHENSIVE IMPROVEMENT PIPELINE")
        print("="*80)

        # Phase 1: Assess quality
        stats = self.assess_quality()

        # Phase 2: Clean (optional)
        if clean:
            self.clean_dataset(dry_run=False)
        else:
            print("\n⚠️  Skipping cleaning phase (set clean=True to clean)")

        # Phase 3: Expand
        if expand:
            self.expand_dataset(target_tasks=target)
        else:
            print("\n⚠️  Skipping expansion phase (set expand=True to expand)")

        # Phase 4: Monitor
        self.continuous_quality_monitor()

        print("\n" + "="*80)
        print("✅ PIPELINE COMPLETE!")
        print("="*80 + "\n")

        print("Next steps:")
        print("  1. Review bad_tasks_identified.json")
        print("  2. Run export: taskpedia export -f json")
        print("  3. Update web UI: npm run export-data (in taskpedia-web/)")
        print("  4. Check quality: taskpedia qa test")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Improve Taskpedia dataset")
    parser.add_argument("--assess", action="store_true", help="Only run quality assessment")
    parser.add_argument("--clean", action="store_true", help="Clean bad tasks (removes them)")
    parser.add_argument("--expand", action="store_true", default=True, help="Expand dataset")
    parser.add_argument("--target", type=int, default=100000, help="Target number of tasks")
    parser.add_argument("--monitor", action="store_true", help="Only run quality monitoring")
    parser.add_argument("--full", action="store_true", help="Run full pipeline")

    args = parser.parse_args()

    improver = DatasetImprover()

    if args.assess:
        improver.assess_quality()
    elif args.monitor:
        improver.continuous_quality_monitor()
    elif args.full:
        improver.run_full_pipeline(clean=args.clean, expand=args.expand, target=args.target)
    else:
        # Default: assess only
        improver.assess_quality()
        print("\nTo run full pipeline: python comprehensive_improvement.py --full")


if __name__ == "__main__":
    main()
