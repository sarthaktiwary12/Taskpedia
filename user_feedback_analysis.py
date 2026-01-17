#!/usr/bin/env python3
"""
Analyze user feedback and update generation patterns.
"""

import json
from pathlib import Path

# Your feedback
feedback = {
    "approved": 42,
    "rejected": 4,
    "rejection_patterns": []
}

# Analyze rejections
rejections = [
    {
        "name": "spray machine handle",
        "reason": "Spray what on what machine handle? It's too vague.",
        "pattern": "VAGUE_OBJECT_ACTION"
    },
    {
        "name": "push vacuum cleaner over passenger's seat",
        "reason": "Confusing- the language is creating confusion on what the task is.",
        "pattern": "CONFUSING_LANGUAGE"
    },
    {
        "name": "Reattach the clean mixing paddle to a commercial stand mixer",
        "reason": "Commercial stand mixer is way too specific",
        "pattern": "OVER_SPECIFIC_EQUIPMENT"
    },
    {
        "name": "attending sports practice",
        "reason": "Non physical task- just locomotion needed.",
        "pattern": "NON_PHYSICAL_COGNITIVE"
    }
]

# Extract improved rules
IMPROVED_RULES = """
=============================================================================
USER FEEDBACK-BASED QUALITY IMPROVEMENTS
=============================================================================

Based on 46 manual reviews (42 approved, 4 rejected = 91.3% approval rate):

REJECT PATTERNS TO ADD:
-----------------------

1. VAGUE ACTIONS (NEW)
   - "spray [thing]" without specifying what substance
   - "[action] [thing]" without clear tool/substance
   - Missing critical context about what/how

   Examples to REJECT:
   - "spray machine handle" (spray what?)
   - "apply to surface" (apply what?)
   - "treat equipment" (treat how?)

2. CONFUSING LANGUAGE (NEW)
   - Nested possessives ("passenger's seat" in "car floor")
   - Contradictory hierarchy (parent="vacuum_car_floor", child="vacuum_car_interior")
   - Unclear spatial relationships

   Examples to REJECT:
   - Tasks where parent/child naming creates confusion
   - Ambiguous spatial references

3. OVER-SPECIFIC EQUIPMENT (NEW)
   - Brand names or very specific models
   - "Commercial [X]" when just "[X]" would work
   - Overly detailed equipment specifications

   Examples to REJECT:
   - "commercial stand mixer" → use "stand mixer"
   - "industrial conveyor belt system" → use "conveyor"
   - Avoid: "Commercial", "Industrial", "Professional-grade"

4. NON-PHYSICAL/COGNITIVE TASKS (NEW)
   - "Attending [event]" - requires no physical training
   - "Observing [activity]" - perception only
   - Tasks that are just locomotion + being present

   Examples to REJECT:
   - "attending sports practice"
   - "observing meeting"
   - "participating in conference"

APPROVE PATTERNS (GOOD TASKS):
-------------------------------

✅ Clear, specific physical actions:
   - "open storage container"
   - "close kitchen pass-through window"
   - "cut tree"
   - "place recyclables in bin"

✅ Tool use with clear objects:
   - "rotate the channel selector knob through all available channels"
   - "tilt the bin to drain dirty water"
   - "drill holes and cut or carve moldings"

✅ Manipulation with specific endpoints:
   - "secure safety restraint for guest in ride vehicle"
   - "attach blood pressure cuff tubing to monitor port"
   - "snap off glass cap of medication ampoule"

✅ Physical therapy/care tasks:
   - "insert suppository into patient" (edge case but trainable)
   - "floss patient's teeth to remove plaque"
   - "secure safety strap around patient in standing frame"

QUALITY METRICS:
---------------
Approval Rate: 91.3% (42/46)
Main Issues: Vagueness (25%), Over-specificity (25%), Non-physical (25%), Confusing language (25%)

ACTION ITEMS:
-------------
1. Add vague action detection (missing substance/tool)
2. Filter "commercial", "industrial", "professional-grade" modifiers
3. Detect cognitive-only tasks (attending, observing, participating)
4. Check parent-child naming consistency
"""

# Save analysis
Path("user_feedback_improvements.txt").write_text(IMPROVED_RULES)

print(IMPROVED_RULES)
print("\n✅ Feedback analysis saved to: user_feedback_improvements.txt")
print("\n📊 Summary:")
print(f"  Approval Rate: 91.3% (42/46)")
print(f"  Key Issues: Vagueness, Over-specificity, Non-physical, Confusing language")
print(f"  Action: Add 4 new rejection patterns to quality judge")
