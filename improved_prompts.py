#!/usr/bin/env python3
"""
Improved prompts for generating high-quality physical robot tasks.

These prompts are designed to generate tasks that:
1. Are physically trainable with real-world demonstration data
2. Involve manipulation (not just navigation or perception)
3. Are specific and actionable
4. Use concrete objects and tools
"""

# =============================================================================
# THE CORE PROMPT TEMPLATE
# =============================================================================

TASK_GENERATION_PROMPT = """You are generating training data for physical robot manipulation.

CONTEXT: {category} - {subcategory}

Generate tasks that a robot would physically perform. Each task MUST be:

1. PHYSICAL MANIPULATION - involves touching, grasping, moving, or manipulating objects
2. TRAINABLE - can be learned from real-world demonstration videos
3. SPECIFIC - names a concrete object and action (not vague)
4. NOVEL - things a human might not immediately think of

EXCLUDE these types:
- Navigation only ("move to location", "approach target")
- Pure perception ("scan for", "detect", "identify", "recognize")
- Calibration/setup ("calibrate", "initialize", "configure")
- Vague conditionals ("adjust based on", "respond to conditions")
- Internal system ("monitor levels", "check status", "transmit data")

GOOD EXAMPLES:
- "Grasp a ripe tomato from the vine without crushing it"
- "Insert a seed into a pre-drilled hole in the soil"
- "Attach a drip irrigation emitter to the main line"
- "Fold a pizza box along its creases"
- "Thread a needle through fabric"

BAD EXAMPLES (DO NOT GENERATE):
- "Navigate to the field" (navigation only)
- "Scan crop for disease" (perception only)
- "Adjust speed based on terrain" (vague)
- "Calibrate sensors" (setup)
- "Monitor soil moisture" (internal)

Generate {count} unique physical manipulation tasks.
Output as JSON: [{{"task": "action verb + specific object + context"}}]

Focus on:
- Tool use (using specific tools/implements)
- Object manipulation (grasping, placing, orienting)
- Assembly/disassembly actions
- Material handling (specific materials)
- Fine motor tasks (precise movements)
"""

# =============================================================================
# CATEGORY-SPECIFIC PROMPTS
# =============================================================================

CATEGORY_PROMPTS = {
    "household": {
        "focus": """
Focus on home tasks that require physical dexterity:
- Handling fragile items (glasses, dishes, eggs)
- Fabric manipulation (folding, hanging, sorting)
- Food preparation (cutting, peeling, mixing)
- Cleaning with tools (brushes, mops, sponges)
- Operating home appliances (buttons, doors, drawers)
""",
        "examples": [
            "Crack an egg into a bowl without getting shell fragments",
            "Fold a fitted sheet into a compact rectangle",
            "Thread a needle and tie a knot at the end",
            "Uncork a wine bottle using a corkscrew",
            "Separate stuck pages of a wet book",
        ]
    },

    "industrial": {
        "focus": """
Focus on manufacturing tasks that require precision:
- Assembly operations (inserting, fastening, aligning)
- Tool changes and handling
- Material positioning and fixturing
- Quality-related physical actions (measuring with tools)
- Packaging operations
""",
        "examples": [
            "Insert a snap-fit connector into its housing",
            "Torque a bolt to a specific tightness using feel",
            "Apply a bead of adhesive along a seam",
            "Position a gasket precisely on a flange",
            "Remove a burr from a machined edge with a file",
        ]
    },

    "warehouse": {
        "focus": """
Focus on logistics tasks with physical handling:
- Item picking from various container types
- Packing items securely with padding
- Label application and handling
- Box assembly and sealing
- Pallet building and wrapping
""",
        "examples": [
            "Slide a fragile item into a padded mailer",
            "Apply a shipping label straight on a box",
            "Interleave cardboard between stacked plates",
            "Pull stretch wrap around a pallet corner",
            "Insert a packing slip into a pouch on a box",
        ]
    },

    "agriculture": {
        "focus": """
Focus on crop/plant handling that requires dexterity:
- Harvesting specific produce types
- Pruning and trimming operations
- Planting and transplanting
- Fruit/vegetable handling without damage
- Tool use (shears, trowels, sprayers)
""",
        "examples": [
            "Snip a grape cluster from the vine without crushing grapes",
            "Transplant a seedling from tray to soil",
            "Thin excess fruit from a branch to improve yield",
            "Remove a sucker shoot from a tomato plant",
            "Wrap a grafting tape around a tree splice",
        ]
    },

    "healthcare": {
        "focus": """
Focus on clinical tasks with physical components:
- Instrument handling and passing
- Supply preparation and organization
- Patient-adjacent physical tasks
- Equipment setup (physical, not electronic)
- Sterile technique physical actions
""",
        "examples": [
            "Open a sterile package without contaminating contents",
            "Pass a surgical instrument handle-first to a surgeon",
            "Squeeze air bubbles from an IV line",
            "Roll a patient's sleeve up for blood draw",
            "Apply a blood pressure cuff snugly on an arm",
        ]
    },

    "food_service": {
        "focus": """
Focus on food handling and kitchen operations:
- Ingredient preparation (cutting, portioning)
- Plating and presentation
- Equipment operation (physical, not programming)
- Cleaning specific items
- Food assembly tasks
""",
        "examples": [
            "Flip a pancake without breaking it",
            "Pipe frosting in a decorative pattern",
            "Julienne a carrot into uniform strips",
            "Crack a lobster claw to extract meat",
            "Roll sushi tightly with a bamboo mat",
        ]
    },
}

# =============================================================================
# ATOMIC ACTION DECOMPOSITION PROMPT
# =============================================================================

ATOMIC_DECOMPOSITION_PROMPT = """Break down this task into atomic robot primitives.

TASK: {task_name}
CONTEXT: {context}

Decompose into the smallest physical actions. Each atomic action should be:
- A single motion/movement
- ~1-3 seconds duration
- Observable and repeatable

Use these primitive types:
- grasp(object, grip_type) - close gripper on object
- release(object) - open gripper
- move_to(target_position) - move end effector
- rotate(axis, angle) - rotate gripper/object
- push(object, direction, force)
- pull(object, direction, force)
- insert(object_a, slot_b)
- extract(object, from_slot)
- press(surface, force)
- slide(object, direction, distance)
- pour(container, target, amount)
- squeeze(object, force)
- pinch(object)
- hook(object)

Output as JSON: [{{"action": "primitive(params)", "description": "what this does"}}]

Include ALL steps from approach to completion.
"""


def get_improved_prompt(category: str, subcategory: str, count: int = 20) -> str:
    """Generate an improved prompt for a specific category/subcategory."""
    base_prompt = TASK_GENERATION_PROMPT.format(
        category=category,
        subcategory=subcategory,
        count=count
    )

    # Add category-specific guidance if available
    cat_key = category.lower().replace(" ", "_").replace("&", "").replace("  ", "_")
    if cat_key in CATEGORY_PROMPTS:
        cat_info = CATEGORY_PROMPTS[cat_key]
        base_prompt += f"\n{cat_info['focus']}"
        base_prompt += "\n\nMore good examples for this category:\n"
        for ex in cat_info["examples"]:
            base_prompt += f"- \"{ex}\"\n"

    return base_prompt


if __name__ == "__main__":
    # Print example prompt
    print("=" * 70)
    print("EXAMPLE IMPROVED PROMPT")
    print("=" * 70)
    prompt = get_improved_prompt("Agriculture", "Harvesting Tasks", 15)
    print(prompt)
