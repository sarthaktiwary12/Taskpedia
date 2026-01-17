#!/usr/bin/env python3
"""
Interactive Quality Control System for Taskpedia.

Allows manual review and approval/rejection of generated tasks.
Feedback is used to improve future generation.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional
import sys


class InteractiveQC:
    """Interactive quality control for manual task review."""

    def __init__(self, manifest_path: str = "taskpedia-web/public/data/manifest.json"):
        self.manifest_path = Path(manifest_path)
        self.manifest = self._load_manifest()

        # Feedback files
        self.approved_file = Path("user_approved_tasks.jsonl")
        self.rejected_file = Path("user_rejected_tasks.jsonl")
        self.feedback_file = Path("user_feedback_patterns.json")

        # Load existing feedback
        self.approved_count = self._count_lines(self.approved_file)
        self.rejected_count = self._count_lines(self.rejected_file)

    def _load_manifest(self) -> Dict:
        """Load task manifest."""
        if not self.manifest_path.exists():
            print(f"❌ Manifest not found: {self.manifest_path}")
            sys.exit(1)
        return json.loads(self.manifest_path.read_text())

    def _count_lines(self, filepath: Path) -> int:
        """Count lines in a file."""
        if not filepath.exists():
            return 0
        with open(filepath) as f:
            return sum(1 for _ in f)

    def _save_feedback(self, task_id: str, task: Dict, approved: bool, reason: str = ""):
        """Save user feedback."""
        feedback = {
            "task_id": task_id,
            "name": task["name"],
            "type": task["node_type"],
            "parent_id": task.get("parent_id", ""),
            "approved": approved,
            "reason": reason,
        }

        target_file = self.approved_file if approved else self.rejected_file
        with open(target_file, "a") as f:
            f.write(json.dumps(feedback) + "\n")

        if approved:
            self.approved_count += 1
        else:
            self.rejected_count += 1

    def _update_feedback_patterns(self):
        """Analyze feedback to extract patterns."""
        if not self.rejected_file.exists():
            return

        patterns = {
            "rejected_keywords": {},
            "rejected_patterns": [],
            "common_reasons": {},
        }

        with open(self.rejected_file) as f:
            for line in f:
                entry = json.loads(line)
                name = entry["name"].lower()
                reason = entry.get("reason", "")

                # Track keywords in rejected tasks
                for word in name.split():
                    if len(word) > 3:  # Skip short words
                        patterns["rejected_keywords"][word] = \
                            patterns["rejected_keywords"].get(word, 0) + 1

                # Track reasons
                if reason:
                    patterns["common_reasons"][reason] = \
                        patterns["common_reasons"].get(reason, 0) + 1

        # Save patterns
        self.feedback_file.write_text(json.dumps(patterns, indent=2))
        print(f"\n💾 Feedback patterns saved to: {self.feedback_file}")

    def review_session(self, num_tasks: int = 50, node_type: Optional[str] = None):
        """Start an interactive review session."""
        print("\n" + "="*80)
        print("🔍 INTERACTIVE QUALITY CONTROL SESSION")
        print("="*80)
        print(f"\nYou will review {num_tasks} tasks")
        print(f"Current stats: ✅ {self.approved_count} approved | ❌ {self.rejected_count} rejected")
        print("\nInstructions:")
        print("  'a' or 'y' = Approve")
        print("  'r' or 'n' = Reject")
        print("  's' = Skip")
        print("  'q' = Quit and save")
        print("\n" + "="*80 + "\n")

        # Filter tasks
        candidates = []
        for task_id, task in self.manifest.items():
            if node_type and task.get("node_type") != node_type:
                continue
            # Prefer newly generated tasks (LLM_GENERATED source)
            if "llm_generated" in str(task.get("sources", [])).lower():
                candidates.append((task_id, task))

        if not candidates:
            candidates = list(self.manifest.items())

        # Random sample
        sample = random.sample(candidates, min(num_tasks, len(candidates)))

        reviewed = 0
        for task_id, task in sample:
            reviewed += 1

            # Display task
            print(f"\n[{reviewed}/{num_tasks}] Task: {task['name']}")
            print(f"  Type: {task['node_type']}")
            print(f"  ID: {task_id}")

            if task.get("parent_id"):
                parent = self.manifest.get(task["parent_id"], {})
                print(f"  Parent: {parent.get('name', 'unknown')}")

            if task.get("children_ids"):
                print(f"  Children: {len(task['children_ids'])}")

            # Get user decision
            while True:
                decision = input("\n  Decision [a/r/s/q]: ").strip().lower()

                if decision in ['a', 'y']:
                    self._save_feedback(task_id, task, approved=True)
                    print("  ✅ Approved")
                    break

                elif decision in ['r', 'n']:
                    reason = input("  Why reject? (optional): ").strip()
                    self._save_feedback(task_id, task, approved=False, reason=reason)
                    print("  ❌ Rejected")
                    break

                elif decision == 's':
                    print("  ⏭️  Skipped")
                    break

                elif decision == 'q':
                    print("\n✅ Session ended. Saving feedback...")
                    self._update_feedback_patterns()
                    self._print_summary()
                    return

                else:
                    print("  Invalid input. Use: a/r/s/q")

        # Session complete
        print("\n" + "="*80)
        print("✅ REVIEW SESSION COMPLETE")
        print("="*80)
        self._update_feedback_patterns()
        self._print_summary()

    def _print_summary(self):
        """Print summary of feedback."""
        total = self.approved_count + self.rejected_count
        if total == 0:
            return

        approval_rate = (self.approved_count / total) * 100

        print(f"\n📊 Feedback Summary:")
        print(f"  Total reviewed: {total}")
        print(f"  ✅ Approved: {self.approved_count} ({approval_rate:.1f}%)")
        print(f"  ❌ Rejected: {self.rejected_count} ({100-approval_rate:.1f}%)")
        print(f"\n💾 Feedback saved to:")
        print(f"  - {self.approved_file}")
        print(f"  - {self.rejected_file}")
        print(f"  - {self.feedback_file}")

    def batch_review_by_type(self):
        """Review tasks organized by type."""
        print("\n🔍 Batch Review by Node Type\n")
        print("Choose a node type to review:")
        print("  1. Atomic tasks")
        print("  2. Subtasks")
        print("  3. Tasks")
        print("  4. Domains")
        print("  5. All types (mixed)")

        choice = input("\nYour choice [1-5]: ").strip()

        type_map = {
            "1": "atomic",
            "2": "subtask",
            "3": "task",
            "4": "domain",
            "5": None,
        }

        node_type = type_map.get(choice)
        if choice not in type_map:
            print("Invalid choice")
            return

        num_tasks = input("How many tasks to review? [default: 50]: ").strip()
        num_tasks = int(num_tasks) if num_tasks.isdigit() else 50

        self.review_session(num_tasks=num_tasks, node_type=node_type)

    def show_feedback_stats(self):
        """Display feedback statistics."""
        if not self.feedback_file.exists():
            print("No feedback patterns yet. Complete a review session first.")
            return

        patterns = json.loads(self.feedback_file.read_text())

        print("\n" + "="*80)
        print("📊 FEEDBACK ANALYSIS")
        print("="*80)

        # Top rejected keywords
        if patterns.get("rejected_keywords"):
            print("\n🔴 Most common words in rejected tasks:")
            sorted_keywords = sorted(
                patterns["rejected_keywords"].items(),
                key=lambda x: -x[1]
            )[:10]
            for word, count in sorted_keywords:
                print(f"  {count:3d}x  {word}")

        # Top rejection reasons
        if patterns.get("common_reasons"):
            print("\n💭 Most common rejection reasons:")
            sorted_reasons = sorted(
                patterns["common_reasons"].items(),
                key=lambda x: -x[1]
            )
            for reason, count in sorted_reasons:
                if reason:
                    print(f"  {count:3d}x  {reason}")

        print("\n" + "="*80)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Interactive Quality Control")
    parser.add_argument("--batch", action="store_true", help="Batch review by type")
    parser.add_argument("--stats", action="store_true", help="Show feedback stats")
    parser.add_argument("-n", "--num", type=int, default=50, help="Number of tasks to review")
    parser.add_argument("--type", choices=["atomic", "subtask", "task", "domain"],
                       help="Filter by node type")

    args = parser.parse_args()

    qc = InteractiveQC()

    if args.stats:
        qc.show_feedback_stats()
    elif args.batch:
        qc.batch_review_by_type()
    else:
        qc.review_session(num_tasks=args.num, node_type=args.type)


if __name__ == "__main__":
    main()
