#!/usr/bin/env python3
"""
Value Assessment System - Judge tasks by their value to robotics companies.

Scoring Criteria:
1. Market Value - Would customers pay for this capability?
2. Technical Impressiveness - Would spectators be impressed?
3. Practical Utility - Does this solve a real problem?
4. Difficulty/Sophistication - Does this demonstrate advanced capability?
5. Generalizability - Can this skill transfer to other tasks?

Focus: Tasks that make robots MARKETABLE and IMPRESSIVE
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class ValueScore:
    """Value assessment for a task."""
    task_id: str
    name: str
    node_type: str

    # Scores (0-10)
    market_value: int = 0
    impressiveness: int = 0
    practical_utility: int = 0
    technical_difficulty: int = 0
    generalizability: int = 0

    # Computed
    total_score: int = 0
    tier: str = ""  # PREMIUM, HIGH, MEDIUM, LOW, TRASH

    # Context
    parent_id: str = ""
    domain: str = ""

    # Reasoning
    value_reasoning: str = ""

    def compute_total(self):
        """Compute weighted total score."""
        # Market value and impressiveness weighted higher
        self.total_score = (
            self.market_value * 3 +
            self.impressiveness * 3 +
            self.practical_utility * 2 +
            self.technical_difficulty * 1 +
            self.generalizability * 1
        )

        # Assign tier
        if self.total_score >= 80:
            self.tier = "PREMIUM"  # Top 5% - Wow factor tasks
        elif self.total_score >= 60:
            self.tier = "HIGH"     # Top 20% - Very valuable
        elif self.total_score >= 40:
            self.tier = "MEDIUM"   # Useful but not exciting
        elif self.total_score >= 20:
            self.tier = "LOW"      # Marginal value
        else:
            self.tier = "TRASH"    # Delete these

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'name': self.name,
            'node_type': self.node_type,
            'scores': {
                'market_value': self.market_value,
                'impressiveness': self.impressiveness,
                'practical_utility': self.practical_utility,
                'technical_difficulty': self.technical_difficulty,
                'generalizability': self.generalizability,
            },
            'total_score': self.total_score,
            'tier': self.tier,
            'parent_id': self.parent_id,
            'domain': self.domain,
            'value_reasoning': self.value_reasoning,
        }


# =============================================================================
# HIGH VALUE TASK PATTERNS
# =============================================================================

# Tasks that would make customers say "SHUT UP AND TAKE MY MONEY"
PREMIUM_VALUE_PATTERNS = {
    # Home/Hospitality
    'coffee': ['make coffee', 'brew coffee', 'espresso', 'latte', 'cappuccino'],
    'cooking': ['cook meal', 'prepare dish', 'plate food', 'garnish'],
    'cleaning_impressive': ['pick up broken glass', 'clean up spill', 'vacuum carpet', 'mop floor'],
    'laundry': ['fold clothes', 'hang clothes', 'iron shirt', 'sort laundry'],
    'dishes': ['load dishwasher', 'wash dishes', 'dry dishes', 'put away dishes'],
    'bed_making': ['make bed', 'change sheets', 'fluff pillows'],

    # Healthcare (High value + regulatory moat)
    'patient_care': ['transfer patient', 'position patient', 'assist walking', 'help patient sit'],
    'medication': ['dispense medication', 'prepare medication', 'deliver medication'],
    'hygiene_assist': ['help patient bathe', 'brush patient teeth', 'comb patient hair'],

    # Manufacturing (Clear ROI)
    'assembly': ['assemble component', 'insert part', 'tighten fastener', 'align parts'],
    'quality_inspection': ['inspect surface', 'measure dimension', 'check alignment'],
    'packaging': ['pack box', 'seal package', 'apply label', 'stack pallets'],

    # Warehouse/Logistics (Huge market)
    'picking': ['pick item', 'grasp product', 'retrieve object'],
    'sorting': ['sort package', 'organize items', 'categorize products'],
    'inventory': ['count items', 'scan barcode', 'track inventory'],

    # Agriculture (Specialized + valuable)
    'harvesting': ['pick fruit', 'harvest vegetable', 'collect crop'],
    'planting': ['plant seed', 'transplant seedling', 'dig hole'],
    'crop_care': ['prune plant', 'water plant', 'remove weeds'],

    # Food Service (High visibility)
    'food_prep': ['chop vegetable', 'slice meat', 'mix ingredients', 'knead dough'],
    'plating': ['plate dish', 'garnish plate', 'portion food'],
    'serving': ['serve food', 'pour drink', 'carry tray'],

    # Retail (Customer-facing)
    'stocking': ['stock shelf', 'organize display', 'arrange products'],
    'checkout': ['scan item', 'bag groceries', 'handle payment'],
}

# Tasks that are technically impressive (demo/marketing value)
IMPRESSIVE_DEMONSTRATIONS = [
    'pick up broken glass',  # Delicate + dangerous
    'thread needle',         # Precision
    'origami',              # Complex manipulation
    'juggle',               # Dynamic coordination
    'solve rubik cube',     # Problem solving + dexterity
    'play instrument',      # Fine motor control
    'paint',                # Creative + precise
    'calligraphy',         # Precision + aesthetics
    'arrange flowers',      # Aesthetic + delicate
    'crack egg',           # Common but tricky
    'flip pancake',        # Timing + coordination
    'pour without spilling', # Precision
    'stack blocks',        # Stability + precision
    'tie shoelace',        # Complex manipulation
    'button shirt',        # Fine motor + common
]

# Low value patterns (delete these)
TRASH_PATTERNS = [
    r'calibrate', r'initialize', r'configure',  # Setup tasks
    r'check.*status', r'monitor.*level',        # Passive monitoring
    r'wait for', r'pause', r'standby',          # Waiting
    r'generic', r'template', r'placeholder',    # Templates
    r'test', r'debug', r'troubleshoot',         # Dev tasks
    r'document', r'report', r'log',             # Administrative
    r'plan', r'schedule', r'coordinate',        # Planning (not physical)
    r'analyze', r'evaluate', r'assess',         # Analysis (not physical)
]


class ValueAssessor:
    """Assess value of tasks from robotics company POV."""

    def __init__(self, manifest_path: Path):
        with open(manifest_path) as f:
            self.manifest = json.load(f)

    def assess_task(self, task_id: str, task: Dict) -> ValueScore:
        """Assess a single task's value."""
        score = ValueScore(
            task_id=task_id,
            name=task.get('name', ''),
            node_type=task.get('node_type', ''),
            parent_id=task.get('parent_id', ''),
            domain=self._extract_domain(task_id),
        )

        name_lower = score.name.lower()

        # Quick trash check
        import re
        for pattern in TRASH_PATTERNS:
            if re.search(pattern, name_lower):
                score.market_value = 0
                score.impressiveness = 0
                score.practical_utility = 0
                score.technical_difficulty = 0
                score.generalizability = 0
                score.value_reasoning = f"Trash: matches pattern '{pattern}'"
                score.compute_total()
                return score

        # Check premium patterns
        for category, patterns in PREMIUM_VALUE_PATTERNS.items():
            for pattern in patterns:
                if pattern in name_lower:
                    score.market_value = 8
                    score.impressiveness = 7
                    score.practical_utility = 8
                    score.technical_difficulty = 6
                    score.generalizability = 7
                    score.value_reasoning = f"Premium: {category} - {pattern}"
                    score.compute_total()
                    return score

        # Check impressive demonstrations
        for demo in IMPRESSIVE_DEMONSTRATIONS:
            if demo in name_lower:
                score.market_value = 9
                score.impressiveness = 10
                score.practical_utility = 5
                score.technical_difficulty = 8
                score.generalizability = 6
                score.value_reasoning = f"Impressive demo: {demo}"
                score.compute_total()
                return score

        # Default: needs manual review
        score.market_value = 5
        score.impressiveness = 5
        score.practical_utility = 5
        score.technical_difficulty = 5
        score.generalizability = 5
        score.value_reasoning = "Needs manual review"
        score.compute_total()
        return score

    def assess_all_tasks(self) -> Dict[str, List[ValueScore]]:
        """Assess all tasks and group by tier."""
        results = {
            'PREMIUM': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': [],
            'TRASH': [],
        }

        # Focus on TASK level (not atomic, not subtask)
        for task_id, task in self.manifest.items():
            node_type = task.get('node_type', '')

            # Prioritize tasks, but also assess subtasks and atomic
            if node_type in ['task', 'subtask', 'atomic']:
                score = self.assess_task(task_id, task)
                results[score.tier].append(score)

        # Sort each tier by score
        for tier in results:
            results[tier].sort(key=lambda x: x.total_score, reverse=True)

        return results

    def _extract_domain(self, task_id: str) -> str:
        """Extract domain from task ID."""
        parts = task_id.split('/')
        return parts[0] if parts else 'unknown'

    def generate_report(self, results: Dict[str, List[ValueScore]]) -> str:
        """Generate value assessment report."""
        report = []
        report.append("=" * 80)
        report.append("TASKPEDIA VALUE ASSESSMENT REPORT")
        report.append("=" * 80)
        report.append("")

        for tier in ['PREMIUM', 'HIGH', 'MEDIUM', 'LOW', 'TRASH']:
            tasks = results[tier]
            report.append(f"\n{tier} TIER: {len(tasks)} tasks")
            report.append("-" * 80)

            # Show top 20 from each tier
            for score in tasks[:20]:
                report.append(f"\n  [{score.total_score:3d}] {score.name}")
                report.append(f"       Type: {score.node_type} | Domain: {score.domain}")
                report.append(f"       Market:{score.market_value} Impress:{score.impressiveness} Utility:{score.practical_utility} Difficulty:{score.technical_difficulty} General:{score.generalizability}")
                report.append(f"       Reasoning: {score.value_reasoning}")

        report.append("\n" + "=" * 80)
        report.append("SUMMARY")
        report.append("=" * 80)
        for tier in ['PREMIUM', 'HIGH', 'MEDIUM', 'LOW', 'TRASH']:
            count = len(results[tier])
            pct = 100 * count / sum(len(v) for v in results.values())
            report.append(f"{tier:10s}: {count:6d} tasks ({pct:5.1f}%)")

        return "\n".join(report)

    def export_tiered_dataset(self, results: Dict[str, List[ValueScore]], output_dir: Path):
        """Export dataset split by value tier."""
        output_dir.mkdir(exist_ok=True)

        for tier in ['PREMIUM', 'HIGH', 'MEDIUM', 'LOW', 'TRASH']:
            output_file = output_dir / f"{tier.lower()}_tasks.json"

            tier_data = [score.to_dict() for score in results[tier]]

            with open(output_file, 'w') as f:
                json.dump(tier_data, f, indent=2)

            print(f"Exported {len(tier_data)} {tier} tasks to {output_file}")


def main():
    manifest_path = Path("/workspaces/Taskpedia/taskpedia-web/public/data/manifest.json")

    print("Loading manifest...")
    assessor = ValueAssessor(manifest_path)

    print("Assessing task values...")
    results = assessor.assess_all_tasks()

    print("\nGenerating report...")
    report = assessor.generate_report(results)
    print(report)

    # Save report
    report_path = Path("/workspaces/Taskpedia/value_assessment_report.txt")
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\nReport saved to {report_path}")

    # Export tiered datasets
    print("\nExporting tiered datasets...")
    output_dir = Path("/workspaces/Taskpedia/tiered_datasets")
    assessor.export_tiered_dataset(results, output_dir)

    print("\n✅ Value assessment complete!")
    print(f"   PREMIUM: {len(results['PREMIUM'])} tasks (WOW factor)")
    print(f"   HIGH:    {len(results['HIGH'])} tasks (Very valuable)")
    print(f"   MEDIUM:  {len(results['MEDIUM'])} tasks (Useful)")
    print(f"   LOW:     {len(results['LOW'])} tasks (Marginal)")
    print(f"   TRASH:   {len(results['TRASH'])} tasks (DELETE)")


if __name__ == '__main__':
    main()
