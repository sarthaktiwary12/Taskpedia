"""
Fast generation pipeline for VLA/VLN training data.

Continuous flow architecture with Textual TUI for monitoring.
- ThreadPoolExecutor for concurrent API calls
- Improved prompts for true atomic actions
- Validation to reject generic/template outputs
- Coverage for VLN, perception, manipulation, social
"""

from __future__ import annotations

import json
import re
import time
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

from taskpedia.hierarchy import NodeType, SeedSource, TaskGraph, TaskNode
from taskpedia.llm import LLMClient, LLMConfig, MockLLMClient


# ============================================================================
# VALIDATION: Reject low-quality outputs
# ============================================================================

# Generic nouns that indicate template outputs
GENERIC_NOUNS = {
    "target",
    "source",
    "materials",
    "equipment",
    "tools",
    "surface",
    "container",
    "workspace",
    "components",
    "area",
    "items",
    "objects",
    "things",
    "stuff",
    "resources",
    "supplies",
    "elements",
}

# Generic verbs that are too vague
GENERIC_VERBS = {
    "check",
    "verify",
    "inspect",
    "prepare",
    "gather",
    "secure",
    "adjust",
    "position",
    "clean",
    "move",
    "handle",
    "process",
}

# ============================================================================
# COGNITIVE VERBS - Internal mental processes (for reasoning training)
# These are NOT directly observable but useful for planning/reasoning tasks
# ============================================================================
COGNITIVE_VERBS = {
    # Memory Operations
    "remember",
    "memorize",
    "commit_to_memory",
    "store_information",
    "recall",
    "retrieve_memory",
    "recollect",
    "bring_to_mind",
    "forget",
    "discard_information",
    "clear_memory",
    "hold_in_mind",
    "maintain_in_memory",
    "mentally_rehearse",
    "refresh_memory",
    "update_memory",
    "overwrite",
    "replace_memory",
    "remember_location",
    "remember_state",
    "remember_sequence",
    "remember_path",
    "mental_map",
    "update_map",
    "orient_mentally",
    "remember_event",
    "recall_sequence",
    "replay_mentally",
    "remember_outcome",
    "learn_from_experience",
    "encode",
    "learn_fact",
    "associate",
    "link_information",
    # Planning/Reasoning
    "plan",
    "strategize",
    "deliberate",
    "consider",
    "decide",
    "choose",
    "select_option",
    "weigh_options",
    "predict",
    "anticipate",
    "expect",
    "forecast",
    "infer",
    "deduce",
    "conclude",
    "reason",
    "hypothesize",
    "assume",
    "suppose",
    "conjecture",
    "evaluate_mentally",
    "judge_internally",
    "assess_mentally",
    # Understanding
    "understand",
    "comprehend",
    "grasp_concept",
    "realize",
    "interpret_meaning",
    "make_sense_of",
    "figure_out",
    "recognize_pattern",
    "see_connection",
    "relate",
    # Imagination/Simulation
    "imagine",
    "visualize",
    "picture_mentally",
    "simulate_mentally",
    "envision",
    "conceive",
    "mental_rehearsal",
    # Beliefs/Knowledge
    "know",
    "believe",
    "think",
    "suspect",
    "update_belief",
    "revise_understanding",
    "learn",
}

# Valid atomic action verbs (robot primitives) - Comprehensive taxonomy
# NOTE: Disambiguated verbs use suffixes like _body, _tool, _instrument
ATOMIC_VERBS = {
    # =========================================================================
    # MANIPULATION (arm/hand control)
    # =========================================================================
    # Grasping & Releasing
    "grasp",
    "grip",
    "hold",
    "clutch",
    "clamp",
    "pinch",
    "squeeze",
    "release",
    "let_go",
    "drop",
    "unclamp",
    "loosen",
    # Pick & Place
    "pick_up",
    "put_down",
    "place",
    "set_down",
    "lay_down",
    "deposit",
    "retrieve",
    "fetch",
    "gather",
    "collect",
    # Push/Pull/Slide
    "push",
    "pull",
    "drag",
    "slide",
    "glide",
    "shove",
    "nudge",
    "tap",
    # Rotation/Orientation
    "rotate",
    "twist",
    "turn",
    "spin",
    "flip",
    "invert",
    "tilt",
    "pivot",
    "orient",
    "align",
    "angle",
    "swivel",
    # Lifting/Lowering
    "lift",
    "raise",
    "elevate",
    "hoist",
    "lower",
    "drop_slowly",
    # Carrying/Moving
    "carry",
    "transport",
    "move",
    "transfer",
    "shift",
    "reposition",
    "relocate",
    "hand_over",
    "pass",
    # Insertion/Removal
    "insert",
    "remove",
    "extract",
    "withdraw",
    "pull_out",
    "push_in",
    "slot_in",
    "eject",
    "pop_out",
    # Open/Close
    "open",
    "close",
    "shut",
    "seal",
    "unseal",
    "unlock",
    "lock",
    "latch",
    "unlatch",
    "fasten",
    "unfasten",
    # Pouring/Dispensing
    "pour",
    "fill",
    "empty",
    "drain",
    "dispense",
    "drip",
    "drizzle",
    "stream",
    "spray",
    "squirt",
    "pump",
    "siphon",
    # Cutting/Separating
    "cut",
    "slice",
    "chop",
    "dice",
    "mince",
    "trim",
    "snip",
    "shear",
    "sever",
    "split",
    "halve",
    "quarter",
    "carve",
    "fillet",
    "tear",
    "rip",
    "break",
    "snap",
    "crack",
    "shatter",
    "crush",
    # Folding/Wrapping
    "fold",
    "unfold",
    "crease",
    "pleat",
    "wrap",
    "unwrap",
    "roll_up",
    "unroll",
    "bundle",
    "unbundle",
    "coil",
    "uncoil",
    # Tying/Fastening
    "tie",
    "untie",
    "knot",
    "unknot",
    "loop",
    "bind",
    "unbind",
    "strap",
    "unstrap",
    "buckle",
    "unbuckle",
    "zip",
    "unzip",
    "button",
    "unbutton",
    "snap",
    "unsnap",
    "velcro",
    "unvelcro",
    "lace",
    "unlace",
    "thread",
    "unthread",
    # Mixing/Stirring
    "stir",
    "mix",
    "blend",
    "whisk",
    "beat",
    "fold_in",
    "knead",
    "mash",
    "puree",
    "whip",
    "cream",
    "emulsify",
    "shake",
    "swirl",
    "agitate",
    "toss",
    # Cleaning/Surface Treatment
    "wipe",
    "scrub",
    "brush",
    "polish",
    "buff",
    "sand",
    "scrape",
    "sweep",
    "dust",
    "mop",
    "sponge",
    "squeegee",
    "rinse",
    "wash",
    "dry",
    "towel",
    "blot",
    "dab",
    # Assembly/Disassembly
    "screw",
    "unscrew",
    "bolt",
    "unbolt",
    "nail",
    "hammer",
    "plug",
    "unplug",
    "socket",
    "connect",
    "disconnect",
    "attach",
    "detach",
    "mount",
    "unmount",
    "install",
    "uninstall",
    "assemble",
    "disassemble",
    "fit",
    "unfit",
    "snap_on",
    "snap_off",
    "clip",
    "unclip",
    "hook",
    "unhook",
    "link",
    "unlink",
    # Pressing/Activating
    "press",
    "depress",
    "push_button",
    "click",
    "tap_button",
    "toggle",
    "switch",
    "flip_switch",
    "dial",
    "adjust_dial",
    "slide_control",
    "touch",
    "swipe",
    # Writing/Drawing/Marking
    "write",
    "draw",
    "sketch",
    "trace",
    "mark",
    "label",
    "stamp",
    "sign",
    "print",
    "type",
    "erase",
    "cross_out",
    "underline",
    "highlight",
    "circle",
    # =========================================================================
    # TOOL OPERATION
    # =========================================================================
    # Hand Tools
    "hammer",
    "chisel",
    "file",
    "rasp",
    "plane",
    "saw",
    "drill",
    "bore",
    "punch",
    "awl",
    "clamp",
    "vise",
    "wrench",
    "tighten",
    "loosen",
    "torque",
    "plier",
    "crimp",
    "strip",
    "cut_wire",
    "screwdriver",
    "pry",
    "lever",
    "wedge",
    # Power Tools
    "power_drill",
    "power_saw",
    "grind",
    "sand_machine",
    "route",
    "lathe",
    "mill",
    "weld",
    "solder",
    "braze",
    # Kitchen Tools
    "peel",
    "core",
    "pit",
    "zest",
    "grate",
    "shred",
    "julienne",
    "mandoline",
    "food_process",
    "blend_food",
    "measure_ingredient",
    "sift",
    "strain",
    "colander",
    "baste",
    "glaze",
    "season",
    "marinate",
    # Garden Tools
    "dig",
    "shovel",
    "rake",
    "hoe",
    "till",
    "cultivate",
    "prune",
    "trim_plant",
    "shear_hedge",
    "mow",
    "edge",
    "water",
    "spray_water",
    "fertilize",
    "mulch",
    "plant",
    "transplant",
    "uproot",
    "weed",
    # Cleaning Tools
    "vacuum",
    "steam_clean",
    "pressure_wash",
    "hose",
    "plunge",
    "snake",
    "unclog",
    # Sewing/Textile Tools
    "sew",
    "stitch",
    "hem",
    "seam",
    "darn",
    "patch",
    "pin",
    "unpin",
    "baste_stitch",
    "backstitch",
    "embroider",
    "knit",
    "purl",
    "crochet",
    "weave",
    "iron",
    "press_fabric",
    "steam",
    "crease_fabric",
    # Medical/Care Tools
    "bandage",
    "wrap_wound",
    "apply_bandage",
    "tape",
    "inject",
    "draw_blood",
    "take_pulse",
    "take_temperature",
    "apply_ointment",
    "apply_cream",
    "massage",
    "compress",
    # =========================================================================
    # COOKING/FOOD PREPARATION
    # =========================================================================
    # Heat Application
    "heat",
    "warm",
    "boil",
    "simmer",
    "poach",
    "blanch",
    "fry",
    "saute",
    "pan_fry",
    "deep_fry",
    "stir_fry",
    "bake",
    "roast",
    "broil",
    "grill",
    "char",
    "sear",
    "toast",
    "brown",
    "caramelize",
    "steam",
    "pressure_cook",
    "slow_cook",
    "microwave",
    "reheat",
    # Cooling
    "cool",
    "chill",
    "refrigerate",
    "freeze",
    "ice",
    "defrost",
    "thaw",
    # Food Prep
    "rinse_food",
    "wash_produce",
    "dry_food",
    "crack_egg",
    "separate_egg",
    "beat_egg",
    "tenderize",
    "pound",
    "flatten",
    "stuff",
    "fill_food",
    "layer",
    "stack_food",
    "garnish",
    "plate",
    "arrange_food",
    "drizzle_sauce",
    # =========================================================================
    # LOCOMOTION / NAVIGATION (VLN - whole body)
    # =========================================================================
    # Basic Movement
    "walk",
    "walk_to",
    "run",
    "run_to",
    "jog",
    "sprint",
    "move_to",
    "go_to",
    "travel_to",
    "head_to",
    "approach",
    "advance",
    "proceed",
    # Directional Movement
    "turn_left",
    "turn_right",
    "turn_around",
    "face",
    "face_toward",
    "step_forward",
    "step_back",
    "step_left",
    "step_right",
    "sidestep",
    "backstep",
    "shuffle",
    # Entry/Exit
    "enter",
    "exit",
    "pass_through",
    "go_through",
    "come_in",
    "go_out",
    "leave",
    "depart",
    "arrive",
    # Vertical Movement
    "climb",
    "climb_up",
    "climb_down",
    "ascend",
    "descend",
    "go_up",
    "go_down",
    "scale",
    "clamber",
    "step_up",
    "step_down",
    "hop_up",
    "hop_down",
    # Following/Leading
    "follow",
    "trail",
    "shadow",
    "pursue",
    "lead",
    "guide",
    "escort",
    "accompany",
    # Avoidance/Navigation
    "avoid",
    "dodge",
    "evade",
    "maneuver_around",
    "navigate_around",
    "circumvent",
    "detour",
    "navigate_to",
    "path_find",
    "explore",
    "search_area",
    "patrol",
    # Stopping/Waiting
    "stop",
    "halt",
    "freeze",
    "wait",
    "pause",
    "stand_still",
    # Body Position Changes
    "sit",
    "sit_down",
    "stand",
    "stand_up",
    "rise",
    "kneel",
    "kneel_down",
    "crouch",
    "squat",
    "lie_down",
    "recline",
    "lean",
    "bend",
    "bow",
    "straighten",
    "stretch",
    # Balance/Stability
    "balance",
    "balance_on",
    "steady",
    "stabilize_body",
    # Jumping/Hopping
    "jump",
    "hop",
    "leap",
    "bound",
    "skip",
    "vault",
    # Crawling/Low Movement
    "crawl",
    "creep",
    "inch",
    "slither",
    "slide_under",
    # Swimming
    "swim",
    "paddle",
    "float",
    "dive",
    "surface",
    "tread_water",
    # =========================================================================
    # PERCEPTION / ACTIVE SENSING
    # =========================================================================
    # Visual Perception
    "look_at",
    "gaze_at",
    "focus_on",
    "stare_at",
    "glance_at",
    "track_visually",
    "follow_visually",
    "watch",
    "scan",
    "survey",
    "observe",
    "view",
    "examine",
    "inspect",
    "search_for",
    "look_for",
    "seek",
    "hunt_for",
    "locate",
    "find",
    "spot",
    "notice",
    "detect",
    "recognize",
    "identify",
    "distinguish",
    "differentiate",
    "compare_visually",
    "match",
    # Reading/Text Perception
    "read",
    "read_text",
    "read_label",
    "read_display",
    "read_sign",
    "interpret",
    "decode",
    "parse",
    # Measurement Perception
    "measure",
    "gauge",
    "assess",
    "evaluate",
    "estimate",
    "weigh",
    "scale",
    "count",
    "tally",
    "quantify",
    "time",
    "clock",
    "check_time",
    "check_temperature",
    # Auditory Perception
    "listen",
    "listen_for",
    "hear",
    "detect_sound",
    "localize_sound",
    "recognize_voice",
    "distinguish_sound",
    # Tactile Perception
    "feel",
    "touch_sense",
    "sense_contact",
    "sense_pressure",
    "sense_force",
    "sense_texture",
    "sense_temperature",
    "probe",
    "palpate",
    # Olfactory Perception
    "smell",
    "sniff",
    "detect_odor",
    # Taste Perception
    "taste",
    "sample",
    # =========================================================================
    # COMMUNICATION / SOCIAL INTERACTION
    # =========================================================================
    # Speech/Verbal
    "say",
    "speak",
    "talk",
    "tell",
    "announce",
    "call_out",
    "shout",
    "whisper",
    "murmur",
    "mumble",
    "ask",
    "question",
    "inquire",
    "query",
    "answer",
    "respond",
    "reply",
    "explain",
    "describe",
    "confirm",
    "acknowledge",
    "agree",
    "disagree",
    "greet",
    "welcome",
    "introduce",
    "farewell",
    "thank",
    "apologize",
    "excuse",
    "request",
    "order",
    "command",
    "instruct",
    "direct",
    "warn",
    "alert",
    "notify",
    "inform",
    "report",
    "suggest",
    "recommend",
    "advise",
    # Non-verbal Communication
    "gesture",
    "gesticulate",
    "motion",
    "point_at",
    "point_to",
    "indicate",
    "show_direction",
    "wave",
    "wave_hello",
    "wave_goodbye",
    "beckon",
    "nod",
    "nod_yes",
    "shake_head",
    "shake_no",
    "shrug",
    "bow",
    "curtsy",
    "smile",
    "frown",
    "wince",
    "grimace",
    "make_eye_contact",
    "avert_gaze",
    # Demonstration
    "show",
    "demonstrate",
    "display",
    "present",
    "exhibit",
    "model",
    "mime",
    "act_out",
    "role_play",
    "signal",
    "sign",
    "sign_language",
    # =========================================================================
    # HUMAN CARE / MEDICAL
    # =========================================================================
    # Physical Care
    "wash_hands",
    "wash_face",
    "bathe",
    "shower",
    "brush_teeth",
    "floss",
    "rinse_mouth",
    "brush_hair",
    "comb_hair",
    "style_hair",
    "shave",
    "trim_beard",
    "trim_nails",
    "file_nails",
    "apply_makeup",
    "remove_makeup",
    "apply_lotion",
    "apply_sunscreen",
    # Dressing
    "dress",
    "undress",
    "put_on",
    "take_off",
    "wear",
    "don",
    "doff",
    "tuck_in",
    "roll_up_sleeves",
    "adjust_clothing",
    # Medical Care
    "administer",
    "give_medication",
    "apply_medicine",
    "check_vitals",
    "monitor",
    "clean_wound",
    "disinfect",
    "sterilize",
    "suture",
    "stitch_wound",
    "splint",
    "immobilize",
    "brace",
    "perform_cpr",
    "rescue_breathe",
    # Assistance
    "assist",
    "help",
    "support",
    "steady_person",
    "lift_person",
    "transfer_person",
    "feed",
    "spoon_feed",
    "give_water",
    # =========================================================================
    # SAFETY / EMERGENCY
    # =========================================================================
    "evacuate",
    "escape",
    "flee",
    "extinguish",
    "smother",
    "douse",
    "block",
    "barricade",
    "seal_off",
    "protect",
    "shield",
    "cover",
    "rescue",
    "save",
    "retrieve_person",
    "call_emergency",
    "dial_911",
    "alert_authorities",
    "administer_first_aid",
    # =========================================================================
    # FINANCIAL / TRANSACTION
    # =========================================================================
    "pay",
    "hand_payment",
    "insert_card",
    "swipe_card",
    "tap_card",
    "enter_pin",
    "sign_receipt",
    "receive_change",
    "receive_receipt",
    "scan_item",
    "scan_barcode",
    "bag_item",
    "count_money",
    "make_change",
    # =========================================================================
    # VEHICLE / EQUIPMENT OPERATION
    # =========================================================================
    # Vehicle Control
    "steer",
    "turn_wheel",
    "accelerate",
    "brake",
    "decelerate",
    "shift_gear",
    "clutch",
    "park",
    "reverse",
    "start_engine",
    "stop_engine",
    "ignite",
    "signal_turn",
    "honk",
    "flash_lights",
    # Equipment Operation
    "operate",
    "control",
    "pilot",
    "drive",
    "start_machine",
    "stop_machine",
    "power_on",
    "power_off",
    "set_controls",
    "adjust_settings",
    "load_machine",
    "unload_machine",
    "refuel",
    "recharge",
    # =========================================================================
    # AGRICULTURE / GARDENING
    # =========================================================================
    "sow",
    "seed",
    "germinate",
    "irrigate",
    "drip_water",
    "harvest",
    "pick_fruit",
    "gather_crop",
    "thresh",
    "winnow",
    "husk",
    "compost",
    "turn_soil",
    "aerate",
    "graft",
    "propagate",
    "pollinate",
    # =========================================================================
    # TEXTILE / FABRIC
    # =========================================================================
    "cut_fabric",
    "measure_fabric",
    "mark_fabric",
    "pin_fabric",
    "baste",
    "tack",
    "sew_seam",
    "overlock",
    "serge",
    "gather_fabric",
    "ruffle",
    "pleat_fabric",
    "applique",
    "quilt",
    "felt",
    "dye",
    "bleach",
    "starch",
    # =========================================================================
    # CONSTRUCTION / BUILDING
    # =========================================================================
    "measure_dimension",
    "mark_line",
    "level",
    "cut_material",
    "saw_wood",
    "miter",
    "nail_in",
    "screw_in",
    "glue",
    "adhesive",
    "sand_surface",
    "prime",
    "paint",
    "coat",
    "tile",
    "grout",
    "caulk",
    "seal",
    "wire",
    "splice",
    "terminate",
    "pipe",
    "solder_pipe",
    "braze_pipe",
    "insulate",
    "wrap_insulation",
    # =========================================================================
    # SPORTS / EXERCISE
    # =========================================================================
    "throw",
    "catch",
    "kick",
    "hit",
    "strike",
    "swing",
    "dribble",
    "pass_ball",
    "shoot",
    "block_ball",
    "serve",
    "volley",
    "rally",
    "punch",
    "jab",
    "hook",
    "tackle",
    "grapple",
    "pin",
    "lift_weight",
    "curl",
    "press_weight",
    "squat_weight",
    "row",
    "paddle_boat",
    "cycle",
    "pedal",
    # =========================================================================
    # MUSIC / PERFORMANCE
    # =========================================================================
    "play",
    "strum",
    "pluck",
    "pick_string",
    "bow",
    "finger",
    "fret",
    "press_key",
    "strike_key",
    "blow",
    "embouchure",
    "beat_drum",
    "strike_percussion",
    "conduct",
    "cue",
    "sing",
    "vocalize",
    "hum",
    "dance",
    "choreograph",
    # =========================================================================
    # WHOLE-BODY CONTROL / DYNAMIC MOTION
    # =========================================================================
    # Dynamic Full-Body
    "lunge",
    "pivot_body",
    "twist_body",
    "rotate_body",
    "shift_weight",
    "transfer_weight",
    "lean_forward",
    "lean_back",
    "duck",
    "dodge_body",
    "weave",
    "sway",
    "roll_body",
    "tumble",
    "somersault",
    "cartwheel",
    "spin_body",
    "pirouette",
    "twirl",
    # Contact/Support
    "brace_against",
    "lean_on",
    "lean_against",
    "rest_on",
    "push_off",
    "push_off_from",
    "spring_from",
    "support_on",
    "prop_against",
    # Reaching/Extending
    "reach",
    "reach_for",
    "reach_toward",
    "extend_arm",
    "stretch_toward",
    "overreach",
    "reach_across",
    "reach_behind",
    "reach_overhead",
    "reach_under",
    "reach_around",
    # Ground Interaction
    "kneel_on",
    "sit_on",
    "lie_on",
    "stand_on",
    "step_on",
    "step_over",
    "step_around",
    "straddle",
    "span",
    "bridge",
    # Posture Transitions
    "rise_from",
    "lower_to",
    "transition_to",
    "get_up_from",
    "get_down_to",
    "roll_over",
    "turn_over",
    "flip_over",
    # =========================================================================
    # FORCE / COMPLIANCE CONTROL
    # =========================================================================
    # Force Application
    "apply_force",
    "exert_force",
    "press_firmly",
    "press_gently",
    "push_hard",
    "push_softly",
    "apply_pressure",
    "release_pressure",
    # Force Modulation
    "increase_force",
    "decrease_force",
    "modulate_force",
    "maintain_force",
    "sustain_pressure",
    # Resistance/Compliance
    "resist",
    "oppose",
    "counter",
    "withstand",
    "yield",
    "give_way",
    "comply",
    "accommodate",
    "dampen",
    "absorb",
    "cushion",
    "buffer",
    "absorb_impact",
    "soften_landing",
    # Tension Control
    "tension",
    "tighten_grip",
    "loosen_grip",
    "pull_taut",
    "slacken",
    "release_tension",
    # =========================================================================
    # BIMANUAL COORDINATION
    # =========================================================================
    # Simultaneous Actions
    "hold_with_left",
    "hold_with_right",
    "grasp_with_both",
    "release_both",
    "coordinate_hands",
    "synchronize_hands",
    # Asymmetric Bimanual
    "hold_while",
    "stabilize_while",
    "support_while",
    "hold_and_manipulate",
    "steady_and_cut",
    "anchor_and_pull",
    "brace_and_twist",
    # Hand-to-Hand Transfer
    "handoff_between_hands",
    "transfer_hand_to_hand",
    "pass_left_to_right",
    "pass_right_to_left",
    "regrasp",
    "adjust_grip",
    # Cooperative Manipulation
    "pull_apart",
    "push_together",
    "spread_open",
    "compress_between_hands",
    "stretch_between_hands",
    "tear_with_both",
    "fold_with_both",
    # =========================================================================
    # SPATIAL / RELATIONAL POSITIONING
    # =========================================================================
    # Relative Positioning
    "position_relative_to",
    "place_relative_to",
    "align_with",
    "align_to",
    "align_parallel",
    "align_perpendicular",
    "orient_toward",
    "orient_away",
    "face_toward",
    "center_on",
    "center_over",
    "center_in",
    # Spatial Relations
    "place_next_to",
    "place_beside",
    "place_behind",
    "place_in_front",
    "place_above",
    "place_below",
    "place_between",
    "place_inside",
    "place_outside",
    "place_around",
    "stack_on",
    "stack_under",
    "nest_in",
    "nest_within",
    # Distance/Proximity
    "move_closer",
    "move_away",
    "move_toward",
    "move_from",
    "bring_together",
    "separate",
    "space_apart",
    "spread_out",
    "close_gap",
    "widen_gap",
    "maintain_distance",
    # Geometric Operations
    "rotate_around",
    "orbit",
    "revolve_around",
    "mirror",
    "reflect",
    "symmetrize",
    "offset",
    "displace",
    "translate",
    # =========================================================================
    # TEMPORAL / SEQUENTIAL CONTROL
    # =========================================================================
    # Duration Control
    "hold_for",
    "maintain_for",
    "sustain_for",
    "wait_for",
    "pause_for",
    "delay_for",
    "continue_for",
    "persist_for",
    # Conditional Actions
    "wait_until",
    "hold_until",
    "continue_until",
    "repeat_until",
    "retry_until",
    "stop_when",
    "pause_when",
    "resume_when",
    # Repetition
    "repeat",
    "iterate",
    "cycle",
    "loop",
    "alternate",
    "oscillate",
    "reciprocate",
    # Timing/Synchronization
    "synchronize_with",
    "coordinate_with",
    "time_with",
    "trigger_on",
    "respond_to",
    "react_to",
    # Sequential Flow
    "start",
    "begin",
    "initiate",
    "finish",
    "complete",
    "finalize",
    "end",
    "proceed_to",
    "advance_to",
    "transition_to",
    # =========================================================================
    # STATE VERIFICATION / OBSERVABLE REASONING
    # =========================================================================
    # Visual Verification
    "verify",
    "verify_that",
    "check_if",
    "check_whether",
    "confirm",
    "confirm_that",
    "ensure",
    "ensure_that",
    "validate",
    "validate_that",
    # State Checking
    "check_state",
    "check_position",
    "check_alignment",
    "check_level",
    "check_temperature",
    "check_pressure",
    "is_open",
    "is_closed",
    "is_locked",
    "is_unlocked",
    "is_on",
    "is_off",
    "is_full",
    "is_empty",
    # Comparison
    "compare",
    "compare_to",
    "compare_with",
    "match_to",
    "match_with",
    "matches",
    "differs_from",
    "equals",
    # Condition Assessment
    "assess",
    "evaluate",
    "judge",
    "determine",
    "test",
    "test_if",
    "probe_for",
    "sense_if",
    "detect_if",
    "detect_whether",
    # Error Detection
    "check_for_error",
    "detect_fault",
    "identify_problem",
    "notice_discrepancy",
    "spot_issue",
    # Success Criteria
    "confirm_complete",
    "verify_success",
    "check_result",
    "validate_outcome",
    "ensure_correct",
    # =========================================================================
    # COLLABORATIVE / SOCIAL MANIPULATION
    # =========================================================================
    # Joint Manipulation
    "hand_to",
    "receive_from",
    "accept_from",
    "give_to",
    "offer_to",
    "present_to",
    "pass_to",
    "take_from",
    # Coordinated Actions
    "lift_together",
    "carry_together",
    "move_together",
    "hold_together",
    "support_together",
    "push_together_with",
    "pull_together_with",
    # Turn-Taking
    "wait_for_turn",
    "take_turn",
    "yield_turn",
    "signal_ready",
    "signal_done",
    "signal_wait",
    # Attention Direction
    "direct_attention",
    "redirect_attention",
    "call_attention_to",
    "draw_attention_to",
    # =========================================================================
    # FINE MOTOR / DEXTEROUS MANIPULATION
    # =========================================================================
    # Finger Control
    "pinch_grip",
    "precision_grip",
    "power_grip",
    "fingertip_grasp",
    "palmar_grasp",
    "lateral_pinch",
    "index_point",
    "thumb_press",
    "finger_tap",
    # Dexterous Actions
    "roll_between_fingers",
    "spin_between_fingers",
    "flip_with_fingers",
    "flick",
    "snap_fingers",
    "rub",
    "stroke",
    "caress",
    # Small Object Manipulation
    "pick_up_small",
    "place_precisely",
    "position_finely",
    "insert_precisely",
    "thread_needle",
    "lace_through",
    # Texture Interaction
    "feel_texture",
    "sense_surface",
    "detect_edge",
    "trace_edge",
    "trace_contour",
    "follow_edge",
    # =========================================================================
    # SAFETY / PROTECTIVE ACTIONS
    # =========================================================================
    # Hazard Avoidance
    "avoid_hazard",
    "steer_clear_of",
    "keep_away_from",
    "maintain_safe_distance",
    "watch_out_for",
    "be_aware_of",
    "anticipate_danger",
    # Protective Actions
    "shield_from",
    "protect_from",
    "guard_against",
    "cover_from",
    "block_hazard",
    "deflect",
    "intercept_danger",
    "wear_protection",
    "don_ppe",
    "put_on_gloves",
    "put_on_goggles",
    # Safe Handling
    "handle_carefully",
    "handle_gently",
    "handle_with_care",
    "move_slowly",
    "move_cautiously",
    "proceed_carefully",
    "lift_safely",
    "carry_safely",
    "set_down_gently",
    # Boundary Respect
    "stay_within_bounds",
    "respect_boundary",
    "maintain_clearance",
    "keep_clear_of",
    "stay_behind",
    "stay_back",
    # Stabilization/Securing
    "stabilize_load",
    "secure_object",
    "anchor_safely",
    "lock_in_place",
    "immobilize_safely",
    "prevent_movement",
    # Emergency Stop
    "emergency_stop",
    "halt_immediately",
    "freeze_motion",
    "kill_power",
    "cut_power",
    "disengage",
    # Warning Actions
    "warn_others",
    "signal_danger",
    "alert_nearby",
    "sound_alarm",
    "flash_warning",
    "display_caution",
    # =========================================================================
    # FAILURE DETECTION / ERROR HANDLING
    # =========================================================================
    # Failure Detection
    "detect_failure",
    "detect_error",
    "detect_anomaly",
    "notice_problem",
    "spot_malfunction",
    "identify_fault",
    "sense_slip",
    "sense_drop",
    "detect_jam",
    "detect_stuck",
    "detect_collision",
    "sense_impact",
    "feel_resistance",
    # Error Classification
    "classify_error",
    "diagnose_problem",
    "identify_cause",
    "determine_failure_type",
    "assess_damage",
    "evaluate_severity",
    # Failure Acknowledgment
    "acknowledge_error",
    "register_failure",
    "log_incident",
    "report_malfunction",
    "flag_issue",
    "mark_as_failed",
    # =========================================================================
    # FAILURE RECOVERY / RETRY
    # =========================================================================
    # Basic Recovery
    "recover",
    "recover_from",
    "recover_from_failure",
    "retry",
    "retry_action",
    "try_again",
    "reattempt",
    "redo",
    "redo_step",
    "restart_action",
    # State Recovery
    "reset",
    "reset_to_initial",
    "return_to_start",
    "restore_state",
    "revert_to",
    "rollback",
    "clear_error",
    "clear_fault",
    "reset_system",
    # Object Recovery
    "retrieve_dropped",
    "pick_up_fallen",
    "recover_object",
    "catch_falling",
    "intercept_drop",
    "save_from_falling",
    "regrasp_slipped",
    "re_acquire",
    "regain_hold",
    # Position Recovery
    "reposition",
    "realign",
    "recenter",
    "readjust",
    "correct_position",
    "fix_alignment",
    "straighten",
    # Unjamming/Unsticking
    "unjam",
    "unstick",
    "free_stuck",
    "clear_obstruction",
    "dislodge",
    "wiggle_free",
    "work_loose",
    "unclog",
    "unblock",
    "clear_blockage",
    # Untangling
    "untangle",
    "unravel",
    "unknot",
    "unsnarl",
    "separate_tangled",
    "free_from_tangle",
    # =========================================================================
    # ADAPTIVE / JUGAAD STRATEGIES
    # =========================================================================
    # Alternative Approaches
    "try_alternative",
    "use_workaround",
    "find_another_way",
    "improvise",
    "adapt_approach",
    "modify_strategy",
    "use_different_method",
    "switch_technique",
    # Substitution
    "substitute",
    "use_substitute",
    "replace_with",
    "use_instead",
    "swap_for",
    "interchange",
    "make_do_with",
    "use_available",
    # Repurposing
    "repurpose",
    "use_as",
    "convert_to",
    "adapt_for",
    "use_creatively",
    "find_alternative_use",
    # Makeshift Solutions
    "improvise_tool",
    "create_makeshift",
    "fashion_temporary",
    "rig_up",
    "jury_rig",
    "cobble_together",
    "use_as_lever",
    "use_as_wedge",
    "use_as_support",
    # Force Alternatives
    "apply_more_force",
    "apply_less_force",
    "try_different_angle",
    "approach_from_different_side",
    "change_grip",
    "use_leverage",
    "use_momentum",
    "use_gravity",
    # Multi-Attempt Strategies
    "try_multiple_times",
    "persist",
    "keep_trying",
    "attempt_variations",
    "cycle_through_options",
    # =========================================================================
    # CONSTRAINT HANDLING / PROBLEM SOLVING
    # =========================================================================
    # Constraint Detection
    "detect_constraint",
    "identify_limitation",
    "find_obstacle",
    "recognize_restriction",
    "notice_blockage",
    "assess_constraint",
    "evaluate_limitation",
    # Constraint Navigation
    "work_around",
    "navigate_constraint",
    "bypass_obstacle",
    "avoid_restriction",
    "circumvent_limitation",
    "find_path_around",
    "route_around",
    # Space Constraints
    "fit_into",
    "squeeze_into",
    "maneuver_through",
    "navigate_tight_space",
    "work_in_confined_area",
    "reach_into",
    "extend_into",
    "access_restricted",
    # Force/Resistance Constraints
    "overcome_resistance",
    "push_through",
    "break_through",
    "force_past",
    "power_through",
    "work_against",
    "counter_resistance",
    # Sequence Constraints
    "reorder",
    "change_sequence",
    "skip_step",
    "combine_steps",
    "parallelize",
    "serialize",
    "do_first",
    "do_after",
    "do_before",
    # Resource Constraints
    "conserve",
    "minimize_use",
    "optimize_usage",
    "ration",
    "allocate_efficiently",
    "prioritize",
    # =========================================================================
    # GRACEFUL DEGRADATION / PARTIAL SUCCESS
    # =========================================================================
    # Partial Completion
    "complete_partially",
    "do_partial",
    "achieve_partial",
    "accomplish_minimum",
    "meet_minimum_requirement",
    "do_best_effort",
    "do_what_possible",
    # Fallback Actions
    "fall_back_to",
    "use_fallback",
    "resort_to",
    "default_to",
    "switch_to_backup",
    "use_simpler_method",
    "use_basic_approach",
    # Graceful Stop
    "stop_gracefully",
    "halt_safely",
    "pause_safely",
    "leave_in_safe_state",
    "secure_before_stopping",
    "complete_current_step",
    "finish_safely",
    # Handoff
    "hand_off_to_human",
    "request_assistance",
    "call_for_help",
    "escalate",
    "defer_to",
    "ask_for_help",
    "signal_need_help",
    "indicate_stuck",
    # =========================================================================
    # PREVENTIVE / PROACTIVE ACTIONS
    # =========================================================================
    # Prevention
    "prevent",
    "prevent_from",
    "stop_before",
    "preempt",
    "head_off",
    "forestall",
    "avoid_beforehand",
    "anticipate_and_prevent",
    # Pre-checking
    "pre_check",
    "verify_before",
    "confirm_before",
    "test_before",
    "validate_before",
    "ensure_before",
    "check_prerequisites",
    "verify_conditions",
    # Preparation for Failure
    "prepare_for_failure",
    "set_up_fallback",
    "create_backup",
    "establish_recovery_point",
    "save_state",
    "position_for_recovery",
    "enable_undo",
    # Monitoring
    "monitor_continuously",
    "watch_for_problems",
    "track_progress",
    "observe_for_anomaly",
    "check_periodically",
    "sense_continuously",
    "maintain_awareness",
    # =========================================================================
    # ENVIRONMENTAL INTERACTION (built environment, not objects)
    # =========================================================================
    # Doors/Windows/Portals
    "open_door",
    "close_door",
    "hold_door",
    "prop_door",
    "unlock_door",
    "lock_door",
    "knock_on_door",
    "ring_doorbell",
    "open_window",
    "close_window",
    "open_gate",
    "close_gate",
    "open_lid",
    "close_lid",
    "lift_cover",
    "replace_cover",
    # Lighting
    "turn_on_light",
    "turn_off_light",
    "switch_light",
    "dim_light",
    "brighten_light",
    "adjust_lighting",
    "illuminate",
    "darken_room",
    # Climate/HVAC
    "adjust_thermostat",
    "set_temperature",
    "turn_on_fan",
    "turn_off_fan",
    "open_vent",
    "close_vent",
    "adjust_airflow",
    "turn_on_heater",
    "turn_off_heater",
    "turn_on_ac",
    "turn_off_ac",
    # Plumbing/Water
    "turn_on_faucet",
    "turn_off_faucet",
    "adjust_water_flow",
    "turn_on_shower",
    "turn_off_shower",
    "flush_toilet",
    "turn_on_hose",
    "turn_off_hose",
    # Electrical/Power
    "plug_into_outlet",
    "unplug_from_outlet",
    "flip_breaker",
    "turn_on_appliance",
    "turn_off_appliance",
    "charge_device",
    "unplug_charger",
    # Furniture Interaction
    "sit_in_chair",
    "stand_from_chair",
    "push_in_chair",
    "pull_out_chair",
    "open_drawer",
    "close_drawer",
    "open_cabinet",
    "close_cabinet",
    "open_closet",
    "close_closet",
    "open_refrigerator",
    "close_refrigerator",
    "adjust_seat",
    "recline_seat",
    "raise_desk",
    "lower_desk",
    # Curtains/Blinds
    "open_curtains",
    "close_curtains",
    "draw_blinds",
    "raise_blinds",
    "lower_blinds",
    "adjust_blinds",
    "tilt_blinds",
    # Elevator/Escalator
    "call_elevator",
    "enter_elevator",
    "exit_elevator",
    "press_floor_button",
    "hold_elevator",
    "step_onto_escalator",
    "step_off_escalator",
    # =========================================================================
    # STATE CHANGES / PHYSICAL TRANSFORMATIONS
    # =========================================================================
    # Temperature Changes
    "heat_up",
    "warm_up",
    "cool_down",
    "chill_down",
    "let_cool",
    "bring_to_temperature",
    "maintain_temperature",
    "thaw_out",
    "freeze_solid",
    "melt",
    "solidify",
    # Moisture Changes
    "wet",
    "dampen",
    "moisten",
    "soak",
    "dry_out",
    "dehydrate",
    "desiccate",
    "air_dry",
    "wring_out",
    "squeeze_dry",
    "blot_dry",
    # Physical State
    "harden",
    "soften",
    "stiffen",
    "loosen_up",
    "thicken",
    "thin_out",
    "dilute",
    "concentrate",
    "dissolve",
    "precipitate",
    "crystallize",
    "coagulate",
    # Shape Changes
    "flatten",
    "round",
    "square_off",
    "taper",
    "expand",
    "contract",
    "inflate",
    "deflate",
    "compress_material",
    "decompress",
    "compact",
    "fluff",
    # Surface Changes
    "smooth",
    "roughen",
    "texture",
    "polish_smooth",
    "corrode",
    "rust",
    "oxidize",
    "patina",
    "coat_surface",
    "strip_surface",
    "refinish",
    # Chemical/Reaction
    "mix_chemicals",
    "react",
    "neutralize",
    "activate",
    "catalyze",
    "inhibit",
    "cure",
    "set_material",
    "ferment",
    "leaven",
    "proof_dough",
    # =========================================================================
    # ATTENTION / COGNITIVE LOAD MANAGEMENT
    # =========================================================================
    # Focus Control
    "focus_attention",
    "focus_on",
    "concentrate_on",
    "attend_to",
    "direct_attention",
    "shift_attention",
    "redirect_focus",
    "narrow_focus",
    "broaden_focus",
    "zoom_in_attention",
    "zoom_out_attention",
    # Divided Attention
    "divide_attention",
    "split_attention",
    "multitask",
    "monitor_multiple",
    "track_multiple",
    "watch_simultaneously",
    "balance_attention",
    "allocate_attention",
    # Selective Attention
    "ignore",
    "filter_out",
    "disregard",
    "tune_out",
    "block_distraction",
    "suppress",
    "deprioritize",
    "select_relevant",
    "discriminate",
    "prioritize_attention",
    # Sustained Attention
    "maintain_focus",
    "sustain_attention",
    "keep_watching",
    "stay_alert",
    "remain_vigilant",
    "keep_monitoring",
    # Attention Switching
    "switch_attention",
    "alternate_attention",
    "toggle_focus",
    "interrupt_focus",
    "resume_focus",
    "return_attention",
    # =========================================================================
    # INFORMATION MANAGEMENT (Observable Actions Only)
    # Note: Pure cognitive/memory verbs are in COGNITIVE_VERBS
    # =========================================================================
    "note",
    "make_note",
    "write_down",
    "record",
    "register",
    "log",
    "document",
    "look_up",
    "search_for",
    "find_information",
    "keep_track_of",
    "track_position",
    "mark_location",
    "bookmark",
    "tag",
    "label",
    "annotate",
    # =========================================================================
    # MULTI-AGENT COORDINATION
    # =========================================================================
    # Synchronization
    "synchronize_with_other",
    "sync_timing",
    "match_pace",
    "coordinate_timing",
    "align_actions",
    "phase_lock",
    "move_in_sync",
    "act_simultaneously",
    "parallel_execute",
    # Turn-Taking/Sequencing
    "wait_for_other",
    "signal_turn",
    "take_turn",
    "go_after",
    "go_before",
    "alternate_with",
    "yield_to",
    "defer_to_other",
    "cede_control",
    # Role Assignment
    "lead",
    "follow_other",
    "support_other",
    "take_primary_role",
    "take_secondary_role",
    "switch_roles",
    "swap_positions",
    # Task Division
    "divide_task",
    "assign_subtask",
    "take_responsibility",
    "share_load",
    "distribute_work",
    "parallelize_work",
    "merge_results",
    "combine_efforts",
    "integrate_work",
    # Formation/Positioning
    "maintain_formation",
    "adjust_formation",
    "reform",
    "flank",
    "surround",
    "encircle",
    "space_from_other",
    "close_on_other",
    "mirror_other",
    # Communication for Coordination
    "signal_ready",
    "signal_start",
    "signal_stop",
    "acknowledge_other",
    "confirm_receipt",
    "request_status",
    "broadcast",
    "notify_all",
    "share_information",
    # Conflict Resolution
    "negotiate",
    "compromise",
    "resolve_conflict",
    "arbitrate",
    "mediate",
    "find_consensus",
    # =========================================================================
    # LEARNING / SKILL ACQUISITION (Meta-Actions)
    # =========================================================================
    # Observation Learning
    "observe_demonstration",
    "watch_expert",
    "study_technique",
    "analyze_motion",
    "note_key_points",
    "identify_pattern",
    # Imitation
    "imitate",
    "mimic",
    "copy_action",
    "replicate_motion",
    "mirror_movement",
    "follow_example",
    "emulate",
    # Practice/Refinement
    "practice",
    "rehearse",
    "drill",
    "repeat_for_learning",
    "refine_skill",
    "improve_technique",
    "polish_execution",
    "correct_error",
    "adjust_technique",
    "fine_tune",
    # Exploration/Discovery
    "explore_options",
    "try_variations",
    "experiment_with",
    "discover",
    "find_new_way",
    "innovate",
    "test_hypothesis",
    "probe_limits",
    "push_boundaries",
    # Feedback Integration
    "receive_feedback",
    "process_feedback",
    "incorporate_correction",
    "learn_from_mistake",
    "update_strategy",
    "adapt_behavior",
    "calibrate",
    "recalibrate",
    "self_correct",
    # Generalization
    "generalize",
    "apply_to_new",
    "transfer_skill",
    "abstract_principle",
    "recognize_similarity",
    "analogize",
    # Skill Consolidation
    "consolidate",
    "automate",
    "make_habitual",
    "chunk_actions",
    "streamline",
    "optimize_execution",
    # =========================================================================
    # DEFORMABLE OBJECT MANIPULATION
    # =========================================================================
    # Stretching/Compression
    "stretch",
    "stretch_out",
    "elongate",
    "extend_material",
    "compress",
    "squish",
    "squeeze_flat",
    "pull_taut",
    "tension_material",
    "slacken_material",
    # Bending/Flexing
    "bend",
    "bend_material",
    "flex",
    "curve",
    "straighten_material",
    "unbend",
    "unflex",
    "arch",
    "bow_material",
    "recurve",
    # Twisting/Torsion
    "twist_material",
    "wring",
    "torsion",
    "untwist",
    "unwring",
    "straighten_twist",
    "spiral",
    "coil_material",
    "helix",
    # Shaping/Molding
    "shape",
    "mold",
    "form",
    "sculpt",
    "reshape",
    "reform",
    "remodel",
    "pinch_shape",
    "press_shape",
    "roll_shape",
    # Folding Deformables
    "fold_fabric",
    "crease_material",
    "pleat_material",
    "gather_material",
    "bunch",
    "ruche",
    "unfold_material",
    "smooth_out",
    "flatten_material",
    # Draping/Hanging
    "drape",
    "hang_fabric",
    "let_hang",
    "suspend_fabric",
    "arrange_drape",
    "adjust_drape",
    "smooth_drape",
    # Cloth-Specific
    "spread_cloth",
    "lay_flat",
    "smooth_wrinkles",
    "tuck_fabric",
    "roll_fabric",
    "bundle_fabric",
    "fold_corner",
    "make_crease",
    "iron_flat",
    # Rope/Cable/Wire
    "coil_rope",
    "uncoil_rope",
    "loop_rope",
    "tie_knot",
    "untie_knot",
    "splice_rope",
    "thread_through",
    "lace_through",
    "weave_through",
    "tighten_rope",
    "loosen_rope",
    "tension_cable",
    # =========================================================================
    # LIQUID HANDLING
    # =========================================================================
    # Pouring/Transferring
    "pour_liquid",
    "pour_slowly",
    "pour_quickly",
    "decant",
    "transfer_liquid",
    "dispense_liquid",
    "drizzle_liquid",
    "stream_liquid",
    "trickle",
    # Containing/Controlling
    "contain_liquid",
    "prevent_spill",
    "catch_drip",
    "dam",
    "block_flow",
    "redirect_flow",
    "channel",
    "funnel",
    "guide_flow",
    # Measuring Liquids
    "measure_liquid",
    "portion_liquid",
    "dose",
    "fill_to_level",
    "fill_to_line",
    "top_off",
    # Mixing Liquids
    "stir_liquid",
    "swirl_liquid",
    "agitate_liquid",
    "blend_liquids",
    "emulsify_liquids",
    "homogenize",
    "separate_liquids",
    "skim",
    "decant_layer",
    # Cleaning Up Liquids
    "mop_up",
    "soak_up",
    "absorb_spill",
    "wipe_spill",
    "blot_liquid",
    "squeegee_liquid",
    # =========================================================================
    # GRANULAR / POWDER HANDLING
    # =========================================================================
    # Scooping/Portioning
    "scoop",
    "scoop_up",
    "ladle",
    "spoon_out",
    "dish_out",
    "portion_granular",
    "measure_powder",
    "level_off",
    "heap",
    # Pouring Granular
    "pour_granular",
    "sprinkle",
    "dust_with",
    "shake_out",
    "tap_out",
    "dispense_powder",
    # Spreading
    "spread_granular",
    "distribute_evenly",
    "scatter",
    "broadcast_seed",
    "strew",
    "disperse",
    # Containing
    "contain_granular",
    "prevent_scatter",
    "funnel_into",
    "bag",
    "sack",
    "bin",
    # Mixing Granular
    "mix_granular",
    "blend_powders",
    "incorporate_dry",
    "sift_together",
    "combine_dry",
    "fold_in_dry",
    # =========================================================================
    # SOFT/COMPLIANT MATERIAL HANDLING
    # =========================================================================
    # Gentle Manipulation
    "handle_soft",
    "support_soft",
    "cradle",
    "cup_hands_around",
    "palm",
    "nestle",
    # Squeezing/Pressing
    "squeeze_gently",
    "press_softly",
    "compress_gently",
    "test_firmness",
    "check_ripeness",
    "feel_softness",
    # Cutting Soft Materials
    "slice_soft",
    "cut_gently",
    "score_surface",
    "puncture_gently",
    "pierce_soft",
    "poke_into",
    # Supporting/Preventing Damage
    "support_underneath",
    "prevent_crushing",
    "cushion_impact",
    "protect_soft",
    "handle_fragile",
    "transport_gently",
    # =========================================================================
    # ASSEMBLY / CONSTRUCTION SEQUENCES
    # =========================================================================
    # Planning Assembly
    "plan_assembly",
    "sequence_steps",
    "order_components",
    "lay_out_parts",
    "organize_materials",
    "prepare_workspace",
    # Joining
    "join",
    "combine",
    "unite",
    "marry_parts",
    "mate_components",
    "couple",
    "interface",
    # Fastening Methods
    "screw_together",
    "bolt_together",
    "nail_together",
    "glue_together",
    "weld_together",
    "solder_together",
    "rivet",
    "staple",
    "pin_together",
    "tape_together",
    "tie_together",
    "band_together",
    # Alignment for Assembly
    "align_for_assembly",
    "position_for_join",
    "orient_for_fit",
    "register",
    "index",
    "locate_precisely",
    # Verification During Assembly
    "check_fit",
    "verify_alignment",
    "test_connection",
    "confirm_secure",
    "validate_assembly",
    "inspect_joint",
    # Disassembly
    "disassemble",
    "take_apart",
    "separate_components",
    "unfasten",
    "disconnect_parts",
    "remove_component",
    "extract_part",
    "pull_apart",
    "break_down",
    # =========================================================================
    # MEASUREMENT / PRECISION ACTIONS
    # =========================================================================
    # Linear Measurement
    "measure_length",
    "measure_width",
    "measure_height",
    "measure_depth",
    "measure_diameter",
    "measure_thickness",
    "use_ruler",
    "use_tape_measure",
    "use_caliper",
    # Angular Measurement
    "measure_angle",
    "check_perpendicular",
    "check_parallel",
    "use_protractor",
    "use_square",
    "use_level",
    # Weight Measurement
    "weigh_object",
    "tare_scale",
    "measure_mass",
    "use_scale",
    "use_balance",
    "check_weight",
    # Volume Measurement
    "measure_volume",
    "measure_capacity",
    "check_level",
    "use_measuring_cup",
    "use_graduated_cylinder",
    # Precision Positioning
    "position_precisely",
    "align_exactly",
    "center_precisely",
    "offset_by",
    "displace_by",
    "adjust_precisely",
    # Marking/Reference
    "mark_measurement",
    "scribe_line",
    "mark_point",
    "set_reference",
    "establish_datum",
    "zero_reference",
    # =========================================================================
    # TIMING / RHYTHM ACTIONS
    # =========================================================================
    # Timing Control
    "time_action",
    "pace_movement",
    "control_tempo",
    "speed_up",
    "slow_down",
    "maintain_rhythm",
    # Synchronization
    "sync_to_beat",
    "follow_rhythm",
    "match_tempo",
    "anticipate_timing",
    "predict_moment",
    "time_precisely",
    # Duration
    "sustain_action",
    "hold_duration",
    "maintain_for_time",
    "pulse",
    "intermittent",
    "burst",
    # Sequencing
    "sequence_actions",
    "chain_movements",
    "flow_between",
    "transition_smoothly",
    "link_actions",
    "concatenate",
    # =========================================================================
    # SOCIAL / EMOTIONAL ACTIONS
    # =========================================================================
    # Emotional Expression
    "express_happiness",
    "show_concern",
    "display_interest",
    "indicate_confusion",
    "show_understanding",
    "express_gratitude",
    # Empathetic Actions
    "comfort",
    "reassure",
    "encourage",
    "calm",
    "soothe",
    "console",
    # Social Protocols
    "greet_formally",
    "greet_informally",
    "say_goodbye",
    "introduce_self",
    "introduce_other",
    "make_small_talk",
    "apologize",
    "excuse_self",
    "thank",
    # Respectful Interaction
    "maintain_personal_space",
    "respect_boundaries",
    "ask_permission",
    "wait_politely",
    "yield_space",
    "make_room",
    # Non-verbal Social
    "maintain_eye_contact",
    "break_eye_contact",
    "look_away_politely",
    "face_speaker",
    "turn_toward",
    "open_posture",
    "nod_understanding",
    "shake_head_disagreement",
    "shrug_uncertainty",
    # =========================================================================
    # WAITING / IDLE ACTIONS
    # =========================================================================
    # Active Waiting
    "wait_actively",
    "standby",
    "remain_ready",
    "idle_safely",
    "park_position",
    "home_position",
    "maintain_pose",
    "hold_position",
    "stay_put",
    # Monitoring While Waiting
    "watch_while_waiting",
    "monitor_while_idle",
    "scan_periodically",
    "check_intermittently",
    # Energy Conservation
    "conserve_energy",
    "reduce_power",
    "enter_low_power",
    "minimize_movement",
    "relax_posture",
    "rest_briefly",
    # Readiness
    "prepare_to_act",
    "anticipate_command",
    "pre_position",
    "stage_for_action",
    "queue_action",
    "buffer_movement",
    # =========================================================================
    # DISAMBIGUATED VERBS (previously ambiguous single words)
    # =========================================================================
    # bow - multiple meanings
    "bow_instrument",  # use bow on string instrument
    "bow_body",  # bend body forward as greeting/respect
    "bow_weapon",  # use bow for archery
    # file - multiple meanings
    "file_document",  # organize/store documents
    "file_tool",  # use file tool to smooth surface
    # lead - multiple meanings
    "lead_guide",  # guide someone/something
    "lead_front",  # be at front of group
    # scale - multiple meanings
    "scale_climb",  # climb up something
    "scale_weigh",  # weigh on a scale
    "scale_resize",  # resize proportionally
    # punch - multiple meanings
    "punch_strike",  # hit with fist
    "punch_hole",  # make hole with punch tool
    "punch_clock",  # punch time clock
    # run - multiple meanings
    "run_locomote",  # move quickly on foot
    "run_operate",  # operate/execute
    "run_flow",  # liquid flowing
    # seal - multiple meanings
    "seal_close",  # close/secure
    "seal_stamp",  # apply seal/stamp
    # park - multiple meanings
    "park_vehicle",  # park a vehicle
    "park_position",  # move to park/home position
    # plant - multiple meanings
    "plant_seed",  # put seed in ground
    "plant_place",  # place firmly
    # iron - multiple meanings
    "iron_clothes",  # press with iron
    "iron_tool",  # use iron tool
    # register - multiple meanings
    "register_align",  # align precisely (assembly)
    "register_record",  # record/log
    # conduct - multiple meanings
    "conduct_lead",  # lead/direct (orchestra)
    "conduct_perform",  # carry out action
    # time - multiple meanings
    "time_measure",  # measure duration
    "time_synchronize",  # sync timing
    # index - multiple meanings
    "index_align",  # align to index point
    "index_catalog",  # catalog/organize
    # pilot - multiple meanings
    "pilot_fly",  # operate aircraft
    "pilot_guide",  # guide through
    # play - multiple meanings
    "play_instrument",  # play musical instrument
    "play_game",  # engage in game/sport
    "play_media",  # play audio/video
    # =========================================================================
    # DIGITAL / COMPUTER INTERACTION
    # =========================================================================
    # Touch/Screen
    "tap_screen",
    "double_tap",
    "long_press_screen",
    "swipe_left",
    "swipe_right",
    "swipe_up",
    "swipe_down",
    "pinch_zoom_in",
    "pinch_zoom_out",
    "spread_fingers",
    "scroll_up",
    "scroll_down",
    "scroll_left",
    "scroll_right",
    "drag_and_drop",
    "drag_drop",
    "drag_to",
    "drop_at",
    # Mouse/Pointer
    "click",
    "double_click",
    "right_click",
    "middle_click",
    "hover_over",
    "mouse_over",
    "move_cursor",
    "drag_mouse",
    "drop_mouse",
    "select_text",
    # Keyboard
    "type_text",
    "type_key",
    "press_key",
    "hold_key",
    "release_key",
    "key_combination",
    "shortcut_keys",
    "enter_text",
    "backspace",
    "delete_text",
    "copy_text",
    "paste_text",
    # Device Interaction
    "plug_usb",
    "unplug_usb",
    "insert_cable",
    "remove_cable",
    "press_power_button",
    "hold_power_button",
    "insert_sd_card",
    "remove_sd_card",
    "connect_bluetooth",
    "disconnect_bluetooth",
    "pair_device",
    "unpair_device",
    # =========================================================================
    # ANIMAL HANDLING / PET CARE
    # =========================================================================
    # Basic Care
    "pet_animal",
    "stroke_animal",
    "pat_animal",
    "scratch_animal",
    "groom_animal",
    "brush_animal",
    "comb_animal",
    "bathe_animal",
    "dry_animal",
    "trim_nails_animal",
    "feed_animal",
    "give_water_animal",
    "fill_bowl",
    "clean_litter",
    "clean_cage",
    "change_bedding",
    # Walking/Leash
    "leash_animal",
    "unleash_animal",
    "attach_leash",
    "remove_leash",
    "walk_dog",
    "heel_command",
    "lead_animal",
    "pick_up_waste",
    "bag_waste",
    "dispose_waste",
    # Handling
    "pick_up_animal",
    "hold_animal",
    "carry_animal",
    "set_down_animal",
    "restrain_animal",
    "calm_animal",
    "comfort_animal",
    "crate_animal",
    "uncrate_animal",
    # Equestrian
    "saddle_horse",
    "unsaddle_horse",
    "bridle_horse",
    "unbridle_horse",
    "mount_horse",
    "dismount_horse",
    "groom_horse",
    "lead_horse",
    "tether_horse",
    "untether_horse",
    # Farm Animals
    "milk_cow",
    "milk_goat",
    "shear_sheep",
    "collect_eggs",
    "herd_animals",
    "corral_animals",
    "separate_animals",
    # =========================================================================
    # CHILD CARE / INFANT CARE
    # =========================================================================
    # Holding/Carrying
    "hold_baby",
    "cradle_baby",
    "support_head",
    "carry_baby",
    "hand_off_baby",
    "receive_baby",
    "rock_baby",
    "bounce_baby",
    "sway_baby",
    # Feeding
    "bottle_feed",
    "burp_baby",
    "prepare_bottle",
    "spoon_feed_baby",
    "wipe_mouth",
    "prepare_formula",
    "warm_bottle",
    "test_temperature",
    # Diapering
    "change_diaper",
    "remove_diaper",
    "clean_baby",
    "apply_diaper_cream",
    "fasten_diaper",
    "dispose_diaper",
    # Dressing
    "dress_baby",
    "undress_baby",
    "swaddle_baby",
    "unswaddle_baby",
    "put_on_onesie",
    "remove_onesie",
    # Bathing
    "bathe_baby",
    "wash_baby",
    "rinse_baby",
    "dry_baby",
    "check_water_temp",
    "support_in_bath",
    # Soothing
    "soothe_baby",
    "rock_to_sleep",
    "pat_back",
    "sing_lullaby",
    "shush",
    "white_noise",
    # Safety
    "strap_into_seat",
    "unstrap_from_seat",
    "place_in_crib",
    "remove_from_crib",
    "buckle_stroller",
    "unbuckle_stroller",
    # =========================================================================
    # OUTDOOR / NATURE / RECREATION
    # =========================================================================
    # Fishing
    "cast_line",
    "reel_in",
    "set_hook",
    "bait_hook",
    "net_fish",
    "unhook_fish",
    "release_fish",
    "tie_fly",
    "change_lure",
    "adjust_drag",
    # Hunting/Trapping
    "set_trap",
    "set_snare",
    "snare_animal",
    "check_trap",
    "bait_trap",
    "release_trap",
    "track_animal",
    "stalk",
    "aim_weapon",
    "shoot",
    "field_dress",
    "carry_game",
    # Foraging/Gathering
    "forage",
    "gather_berries",
    "pick_mushrooms",
    "identify_plant",
    "dig_roots",
    "collect_nuts",
    "harvest_wild",
    # Camping
    "pitch_tent",
    "stake_tent",
    "guy_out",
    "break_camp",
    "start_fire",
    "tend_fire",
    "extinguish_fire",
    "set_up_camp",
    "pack_gear",
    "unpack_gear",
    "hang_food",
    "bear_bag",
    "filter_water",
    # Hiking/Climbing
    "hike",
    "trek",
    "scramble",
    "boulder",
    "belay",
    "rappel",
    "anchor",
    "clip_in",
    "clip_out",
    "tie_knot_climbing",
    "check_harness",
    "rack_gear",
    # Water Sports
    "paddle_canoe",
    "paddle_kayak",
    "row_boat",
    "launch_boat",
    "beach_boat",
    "dock_boat",
    "cast_off",
    "tie_off",
    "anchor_boat",
    # Winter Sports
    "ski",
    "snowboard",
    "skate_ice",
    "put_on_skis",
    "remove_skis",
    "wax_skis",
    "put_on_skates",
    "lace_skates",
    # =========================================================================
    # ART / CRAFT / CREATIVE
    # =========================================================================
    # Drawing/Painting
    "sketch",
    "draw_line",
    "shade",
    "crosshatch",
    "paint_stroke",
    "blend_paint",
    "mix_colors",
    "dip_brush",
    "rinse_brush",
    "load_brush",
    "apply_wash",
    "layer_paint",
    "glaze_painting",
    # Sculpture/3D
    "sculpt",
    "carve_wood",
    "carve_stone",
    "whittle",
    "chisel_stone",
    "sand_sculpture",
    "model_clay",
    "throw_clay",
    "center_clay",
    "shape_clay",
    "smooth_clay",
    "score_clay",
    "fire_pottery",
    "glaze_pottery",
    "kiln_fire",
    # Printmaking
    "engrave",
    "etch_plate",
    "ink_plate",
    "wipe_plate",
    "pull_print",
    "register_print",
    # Woodworking
    "plane_wood",
    "joint_wood",
    "route_wood",
    "turn_lathe",
    "sand_wood",
    "finish_wood",
    "carve_detail",
    "inlay",
    "veneer",
    # Jewelry/Metalwork
    "solder_jewelry",
    "set_stone",
    "polish_metal",
    "bend_wire",
    "twist_wire",
    "coil_wire",
    "clasp",
    "crimp_bead",
    "string_beads",
    # =========================================================================
    # REPAIR / MAINTENANCE / TROUBLESHOOTING
    # =========================================================================
    # Diagnosis
    "diagnose",
    "troubleshoot",
    "debug",
    "test_function",
    "inspect_damage",
    "assess_repair",
    "identify_issue",
    "check_connection",
    "test_continuity",
    "measure_voltage",
    # Repair Actions
    "repair",
    "fix",
    "mend",
    "restore",
    "replace_part",
    "swap_component",
    "upgrade_part",
    "patch_hole",
    "seal_leak",
    "plug_gap",
    "refurbish",
    "recondition",
    "overhaul",
    # Maintenance
    "lubricate",
    "oil",
    "grease",
    "clean_filter",
    "replace_filter",
    "change_oil",
    "top_off_fluid",
    "tighten_loose",
    "adjust_tension",
    "calibrate_device",
    "sharpen_blade",
    "hone",
    "strop",
    # =========================================================================
    # PACKAGING / SHIPPING / LOGISTICS
    # =========================================================================
    # Packaging
    "box_up",
    "unbox",
    "pack_item",
    "unpack_item",
    "wrap_package",
    "unwrap_package",
    "bubble_wrap",
    "pad_package",
    "cushion_item",
    "tape_box",
    "seal_package",
    "close_box",
    "label_package",
    "address_package",
    "affix_label",
    # Palletizing
    "stack_boxes",
    "palletize",
    "shrink_wrap",
    "strap_pallet",
    "band_package",
    # Shipping
    "weigh_package",
    "measure_package",
    "calculate_shipping",
    "print_label",
    "attach_shipping_label",
    "schedule_pickup",
    "drop_off_package",
    # Receiving
    "receive_package",
    "sign_for_delivery",
    "inspect_shipment",
    "verify_contents",
    "check_packing_slip",
    "report_damage",
    # =========================================================================
    # OFFICE / ADMINISTRATIVE
    # =========================================================================
    # Paper Handling
    "collate",
    "staple_papers",
    "remove_staple",
    "paper_clip",
    "binder_clip",
    "hole_punch",
    "three_hole_punch",
    "bind_document",
    "spiral_bind",
    "comb_bind",
    "laminate",
    "insert_laminate",
    "trim_laminate",
    # Filing
    "file_alphabetically",
    "file_numerically",
    "file_chronologically",
    "create_folder",
    "label_folder",
    "tab_folder",
    "archive",
    "retrieve_file",
    "pull_file",
    # Copying/Printing
    "photocopy",
    "scan_document",
    "print_document",
    "load_paper",
    "clear_jam",
    "replace_toner",
    "collate_copies",
    "staple_copies",
    # Shredding/Disposal
    "shred_document",
    "cross_cut_shred",
    "empty_shredder",
    "dispose_confidential",
    # =========================================================================
    # CLEANING DETAILED
    # =========================================================================
    # Sanitization
    "sanitize",
    "disinfect_surface",
    "sterilize_equipment",
    "antibacterial_wipe",
    "alcohol_wipe",
    # Stain Removal
    "treat_stain",
    "pre_treat",
    "blot_stain",
    "apply_stain_remover",
    "scrub_stain",
    "rinse_stain",
    # Odor Control
    "deodorize",
    "neutralize_odor",
    "apply_freshener",
    "ventilate",
    "air_out",
    # Deep Cleaning
    "deep_clean",
    "detail_clean",
    "spot_clean",
    "steam_clean_fabric",
    "extract_clean",
    "descale",
    "delime",
    "remove_buildup",
    # =========================================================================
    # LAUNDRY / FABRIC CARE
    # =========================================================================
    "sort_laundry",
    "separate_colors",
    "check_pockets",
    "turn_inside_out",
    "load_washer",
    "unload_washer",
    "load_dryer",
    "unload_dryer",
    "add_detergent",
    "add_softener",
    "set_wash_cycle",
    "set_dryer_cycle",
    "hang_clothes",
    "hang_to_dry",
    "clip_to_line",
    "remove_from_line",
    "fold_laundry",
    "fold_shirt",
    "fold_pants",
    "fold_towel",
    "iron_shirt",
    "iron_pants",
    "iron_collar",
    "starch_collar",
    "steam_garment",
    "press_crease",
    "hang_garment",
    "store_garment",
    "remove_lint",
    "clean_lint_trap",
    "empty_lint_trap",
    "pre_soak",
    "hand_wash_garment",
    "wring_garment",
    "lay_flat_to_dry",
    # =========================================================================
    # DISHES / KITCHEN CLEANUP
    # =========================================================================
    "scrape_plate",
    "rinse_dish",
    "load_dishwasher",
    "unload_dishwasher",
    "hand_wash_dish",
    "soak_pan",
    "scrub_pot",
    "dry_dish",
    "put_away_dishes",
    "stack_dishes",
    "organize_cabinet",
    "sanitize_cutting_board",
    "polish_silverware",
    "dry_silverware",
    # =========================================================================
    # BED MAKING / BEDROOM
    # =========================================================================
    "strip_bed",
    "make_bed",
    "spread_sheet",
    "tuck_sheet",
    "tuck_corners",
    "fit_sheet",
    "smooth_sheet",
    "place_blanket",
    "smooth_comforter",
    "fluff_pillow",
    "arrange_pillows",
    "change_pillowcase",
    "zip_pillow_cover",
    "fold_blanket",
    "store_bedding",
    "air_mattress",
    # =========================================================================
    # HOME MAINTENANCE
    # =========================================================================
    "change_lightbulb",
    "unscrew_bulb",
    "screw_in_bulb",
    "hang_picture",
    "hammer_nail",
    "level_frame",
    "adjust_hanging",
    "unclog_drain",
    "plunge_drain",
    "snake_drain",
    "reset_breaker",
    "flip_breaker",
    "test_outlet",
    "patch_drywall",
    "sand_patch",
    "paint_patch",
    "caulk_seam",
    "apply_caulk",
    "smooth_caulk",
    "remove_old_caulk",
    # =========================================================================
    # PERSONAL GROOMING EXTENDED
    # =========================================================================
    # Hair
    "braid_hair",
    "tie_ponytail",
    "make_bun",
    "pin_hair",
    "apply_hair_gel",
    "apply_mousse",
    "apply_hairspray",
    "blow_dry_hair",
    "curl_hair",
    "straighten_hair",
    "crimp_hair",
    "part_hair",
    "comb_through",
    "detangle_hair",
    # Makeup
    "apply_foundation",
    "blend_foundation",
    "apply_concealer",
    "apply_mascara",
    "apply_eyeliner",
    "apply_eyeshadow",
    "blend_eyeshadow",
    "apply_lipstick",
    "apply_lip_gloss",
    "line_lips",
    "apply_blush",
    "contour_face",
    "highlight_face",
    "set_makeup",
    "remove_makeup",
    "cleanse_face",
    "tone_face",
    "moisturize_face",
    # Nails
    "file_nail",
    "shape_nail",
    "buff_nail",
    "push_cuticle",
    "trim_cuticle",
    "apply_base_coat",
    "apply_nail_polish",
    "apply_top_coat",
    "remove_nail_polish",
    "clean_under_nails",
    # =========================================================================
    # BATHING / HYGIENE
    # =========================================================================
    "shampoo_hair",
    "lather_shampoo",
    "rinse_shampoo",
    "condition_hair",
    "apply_conditioner",
    "rinse_conditioner",
    "lather_soap",
    "scrub_body",
    "rinse_body",
    "exfoliate_skin",
    "apply_body_wash",
    "use_loofah",
    "shave_face",
    "shave_legs",
    "apply_shaving_cream",
    "rinse_razor",
    "pat_dry",
    "towel_dry",
    "apply_body_lotion",
    "apply_deodorant",
    "apply_antiperspirant",
    # Oral
    "apply_toothpaste",
    "brush_teeth",
    "brush_tongue",
    "floss_teeth",
    "use_floss_pick",
    "rinse_mouth",
    "gargle_mouthwash",
    "scrape_tongue",
    "use_water_flosser",
    # =========================================================================
    # BEVERAGES
    # =========================================================================
    "brew_coffee",
    "grind_coffee",
    "tamp_coffee",
    "pull_espresso",
    "froth_milk",
    "steam_milk",
    "pour_latte_art",
    "steep_tea",
    "brew_tea",
    "strain_tea",
    "add_honey",
    "blend_smoothie",
    "add_ice",
    "pour_drink",
    "muddle_ingredients",
    "shake_cocktail",
    "stir_cocktail",
    "strain_cocktail",
    "rim_glass",
    "garnish_drink",
    "open_bottle",
    "pop_cork",
    "decant_wine",
    "aerate_wine",
    # =========================================================================
    # TABLE SERVICE / DINING
    # =========================================================================
    "set_table",
    "place_placemat",
    "set_plate",
    "set_silverware",
    "fold_napkin",
    "place_napkin",
    "set_glass",
    "light_candle",
    "serve_food",
    "plate_food",
    "pass_dish",
    "offer_seconds",
    "pour_water",
    "pour_wine",
    "refill_glass",
    "clear_table",
    "bus_table",
    "scrape_leftovers",
    "consolidate_dishes",
    # Eating actions
    "bring_to_mouth",
    "chew_food",
    "swallow_food",
    "sip_drink",
    "cut_bite",
    "spear_food",
    "scoop_food",
    "spread_on_bread",
    "dab_mouth",
    "wipe_mouth",
    "unfold_napkin",
    "place_napkin_lap",
    # =========================================================================
    # MEAL PREP ADVANCED
    # =========================================================================
    # Knife cuts
    "chiffonade",
    "brunoise_cut",
    "batonnet_cut",
    "supreme_citrus",
    # Meat prep
    "debone_fish",
    "fillet_fish",
    "skin_fish",
    "butterfly_meat",
    "pound_meat",
    "truss_poultry",
    "tie_roast",
    "stuff_cavity",
    "score_meat",
    "marinate_meat",
    # Breading/coating
    "dredge_flour",
    "egg_wash",
    "coat_breadcrumbs",
    "double_bread",
    # Sauce work
    "reduce_sauce",
    "deglaze_pan",
    "mount_butter",
    "emulsify_sauce",
    "strain_sauce",
    "skim_fat",
    "clarify_butter",
    # Baking
    "proof_yeast",
    "activate_yeast",
    "bloom_gelatin",
    "punch_dough",
    "knock_back_dough",
    "shape_loaf",
    "score_bread",
    "dock_pastry",
    "blind_bake",
    "crimp_edge",
    "lattice_top",
    "temper_chocolate",
    "seed_chocolate",
    # =========================================================================
    # DRIVING / VEHICLE OPERATION
    # =========================================================================
    "start_car",
    "turn_ignition",
    "push_start",
    "adjust_seat",
    "adjust_mirrors",
    "adjust_steering_wheel",
    "fasten_seatbelt",
    "unfasten_seatbelt",
    "release_parking_brake",
    "check_mirrors",
    "check_blind_spot",
    "signal_turn",
    "merge_traffic",
    "change_lanes",
    "yield_right_of_way",
    "parallel_park",
    "back_into_spot",
    "pull_into_spot",
    "three_point_turn",
    "k_turn",
    "u_turn",
    # Vehicle maintenance
    "check_tire_pressure",
    "inflate_tire",
    "deflate_tire",
    "change_tire",
    "loosen_lug_nuts",
    "tighten_lug_nuts",
    "jack_up_car",
    "lower_jack",
    "place_jack_stand",
    "check_oil_level",
    "add_oil",
    "add_coolant",
    "add_washer_fluid",
    "jump_start_car",
    "attach_jumper_cables",
    "remove_jumper_cables",
    "wash_car",
    "wax_car",
    "polish_car",
    "dry_car",
    "vacuum_car_interior",
    "wipe_dashboard",
    "clean_windows",
    # =========================================================================
    # GYM / EXERCISE
    # =========================================================================
    "warm_up",
    "cool_down",
    "stretch_muscle",
    "hold_stretch",
    "do_pushup",
    "do_situp",
    "do_crunch",
    "do_plank",
    "hold_plank",
    "do_squat",
    "do_lunge",
    "do_burpee",
    "do_jumping_jack",
    "jump_rope",
    "skip_rope",
    "use_treadmill",
    "adjust_speed",
    "adjust_incline",
    "use_elliptical",
    "use_rowing_machine",
    "use_stationary_bike",
    "lift_dumbbell",
    "curl_dumbbell",
    "press_dumbbell",
    "do_bench_press",
    "do_deadlift",
    "do_overhead_press",
    "rack_weights",
    "unrack_weights",
    "add_weight_plate",
    "remove_weight_plate",
    "spot_lifter",
    "assist_lift",
    "wipe_equipment",
    "sanitize_equipment",
    "roll_foam_roller",
    "use_resistance_band",
    "stretch_band",
    # =========================================================================
    # BALL SPORTS
    # =========================================================================
    "dribble_basketball",
    "pass_basketball",
    "shoot_basketball",
    "rebound",
    "dribble_soccer",
    "pass_soccer",
    "shoot_soccer",
    "head_ball",
    "trap_ball",
    "chest_trap",
    "thigh_trap",
    "serve_volleyball",
    "set_volleyball",
    "spike_volleyball",
    "dig_volleyball",
    "pitch_baseball",
    "bat_ball",
    "catch_baseball",
    "field_ball",
    "throw_football",
    "catch_football",
    "punt_football",
    "kick_field_goal",
    "swing_golf_club",
    "drive_golf_ball",
    "chip_golf_ball",
    "putt_golf_ball",
    # =========================================================================
    # RACQUET SPORTS
    # =========================================================================
    "serve_tennis",
    "return_serve",
    "hit_forehand",
    "hit_backhand",
    "volley_net",
    "hit_lob",
    "hit_drop_shot",
    "hit_smash",
    "serve_badminton",
    "clear_shuttle",
    "drop_shuttle",
    "smash_shuttle",
    # =========================================================================
    # FIRST AID / MEDICAL
    # =========================================================================
    "apply_direct_pressure",
    "elevate_wound",
    "apply_tourniquet",
    "clean_wound",
    "irrigate_wound",
    "apply_antiseptic",
    "apply_sterile_dressing",
    "secure_bandage",
    "wrap_bandage",
    "splint_limb",
    "immobilize_joint",
    "apply_sling",
    "apply_ice_pack",
    "apply_heat_pack",
    "apply_cold_compress",
    "perform_cpr",
    "give_chest_compressions",
    "give_rescue_breaths",
    "use_aed",
    "attach_aed_pads",
    "deliver_shock",
    "perform_heimlich",
    "abdominal_thrust",
    "back_blows",
    "place_recovery_position",
    "monitor_breathing",
    "check_responsiveness",
    # Medication
    "take_pill",
    "swallow_pill",
    "take_with_water",
    "use_inhaler",
    "prime_inhaler",
    "shake_inhaler",
    "use_nebulizer",
    "attach_mask",
    "turn_on_nebulizer",
    "inject_medication",
    "draw_medication",
    "prime_syringe",
    "check_blood_sugar",
    "prick_finger",
    "apply_blood_to_strip",
    "read_glucose_meter",
    "record_reading",
    "apply_eye_drops",
    "tilt_head_back",
    "pull_lower_lid",
    "apply_ear_drops",
    "tilt_head_sideways",
    # Vital signs
    "take_blood_pressure",
    "apply_bp_cuff",
    "inflate_cuff",
    "release_cuff",
    "read_blood_pressure",
    "record_blood_pressure",
    "count_pulse",
    "find_pulse_point",
    "count_for_minute",
    "count_respirations",
    "observe_breathing",
    "check_oxygen_level",
    "attach_pulse_oximeter",
    # =========================================================================
    # SHOPPING / RETAIL
    # =========================================================================
    "browse_items",
    "examine_item",
    "compare_items",
    "read_price_tag",
    "check_expiration_date",
    "read_nutrition_label",
    "select_item",
    "pick_item",
    "add_to_cart",
    "remove_from_cart",
    "push_shopping_cart",
    "pull_shopping_cart",
    "steer_cart",
    "carry_shopping_basket",
    "carry_bags",
    "wait_in_line",
    "move_up_in_line",
    "load_conveyor",
    "bag_groceries",
    "double_bag",
    "separate_cold_items",
    "load_bags_in_car",
    "unload_groceries",
    "put_away_groceries",
    "check_receipt",
    "verify_purchase",
    # =========================================================================
    # SOCIAL GREETINGS / ETIQUETTE
    # =========================================================================
    "shake_hands",
    "offer_hand",
    "grip_hand",
    "release_handshake",
    "bow_greeting",
    "incline_head",
    "nod_greeting",
    "wave_hello",
    "wave_goodbye",
    "wave_hand",
    "hug_person",
    "embrace",
    "pat_back",
    "kiss_cheek",
    "air_kiss",
    "fist_bump",
    "bump_fists",
    "explode_fist",
    "high_five",
    "slap_hands",
    "introduce_self",
    "state_name",
    "exchange_names",
    "introduce_others",
    "make_introduction",
    "exchange_business_cards",
    "offer_card",
    "receive_card",
    "read_card",
    # =========================================================================
    # COMPUTER / DIGITAL WORK
    # =========================================================================
    "log_in",
    "enter_username",
    "enter_password",
    "log_out",
    "open_application",
    "launch_program",
    "close_application",
    "quit_program",
    "save_file",
    "save_as",
    "open_file",
    "close_file",
    "create_folder",
    "rename_folder",
    "delete_file",
    "move_file",
    "copy_paste_file",
    "cut_paste_file",
    "send_email",
    "compose_email",
    "reply_email",
    "forward_email",
    "attach_file_email",
    "download_attachment",
    "schedule_meeting",
    "send_invite",
    "accept_invite",
    "decline_invite",
    "join_video_call",
    "leave_call",
    "share_screen",
    "stop_sharing",
    "mute_microphone",
    "unmute_microphone",
    "turn_on_camera",
    "turn_off_camera",
    "raise_hand_virtual",
    "lower_hand",
    "send_chat_message",
    "react_to_message",
    # =========================================================================
    # WRITING / DOCUMENTATION
    # =========================================================================
    "draft_document",
    "write_draft",
    "edit_document",
    "revise_text",
    "proofread_document",
    "check_spelling",
    "check_grammar",
    "format_text",
    "bold_text",
    "italicize_text",
    "underline_text",
    "change_font",
    "change_font_size",
    "change_color",
    "insert_image",
    "resize_image",
    "position_image",
    "create_table",
    "add_row",
    "add_column",
    "merge_cells",
    "add_header",
    "add_footer",
    "insert_page_number",
    "number_pages",
    "set_margins",
    "adjust_margins",
    "apply_style",
    "create_style",
    "modify_style",
    "track_changes",
    "accept_change",
    "reject_change",
    "add_comment",
    "reply_to_comment",
    "resolve_comment",
    "delete_comment",
    # =========================================================================
    # MEETINGS / PRESENTATIONS
    # =========================================================================
    "prepare_agenda",
    "distribute_agenda",
    "take_meeting_notes",
    "record_minutes",
    "present_slides",
    "advance_slide",
    "go_back_slide",
    "point_to_screen",
    "use_laser_pointer",
    "highlight_point",
    "distribute_handout",
    "pass_out_materials",
    "facilitate_discussion",
    "moderate_discussion",
    "call_on_speaker",
    "summarize_points",
    "recap_discussion",
    "assign_action_item",
    "delegate_task",
    "set_deadline",
    "agree_on_deadline",
    "confirm_next_steps",
    "adjourn_meeting",
    "end_meeting",
    # =========================================================================
    # PHOTOGRAPHY
    # =========================================================================
    "frame_shot",
    "compose_image",
    "check_framing",
    "focus_lens",
    "manual_focus",
    "auto_focus",
    "half_press_shutter",
    "adjust_aperture",
    "open_aperture",
    "close_aperture",
    "adjust_shutter_speed",
    "set_fast_shutter",
    "set_slow_shutter",
    "set_iso",
    "increase_iso",
    "decrease_iso",
    "meter_light",
    "check_exposure",
    "adjust_exposure_compensation",
    "take_photo",
    "press_shutter",
    "release_shutter",
    "bracket_exposure",
    "take_burst",
    "use_timer",
    "review_photo",
    "zoom_preview",
    "delete_photo",
    "change_lens",
    "attach_lens",
    "remove_lens",
    "mount_flash",
    "adjust_flash",
    "bounce_flash",
    "use_tripod",
    "mount_camera",
    "level_tripod",
    "transfer_photos",
    "import_photos",
    "backup_photos",
    "edit_photo",
    "crop_photo",
    "straighten_photo",
    "adjust_brightness",
    "adjust_contrast",
    "adjust_saturation",
    "sharpen_image",
    "reduce_noise",
    "apply_filter",
    # =========================================================================
    # LAWN / GARDEN CARE
    # =========================================================================
    "mow_lawn",
    "start_mower",
    "push_mower",
    "empty_grass_bag",
    "edge_lawn",
    "trim_edges",
    "use_edger",
    "use_string_trimmer",
    "rake_leaves",
    "bag_leaves",
    "pile_leaves",
    "spread_grass_seed",
    "overseed_lawn",
    "cover_seed",
    "aerate_lawn",
    "use_aerator",
    "core_aerate",
    "dethatch_lawn",
    "remove_thatch",
    "power_rake",
    "apply_fertilizer",
    "spread_fertilizer",
    "water_in_fertilizer",
    "apply_weed_killer",
    "spot_treat_weeds",
    "pull_weeds",
    "spread_mulch",
    "rake_mulch",
    "edge_mulch_bed",
    # =========================================================================
    # KNITTING / CROCHET
    # =========================================================================
    "cast_on_stitches",
    "long_tail_cast_on",
    "cable_cast_on",
    "knit_stitch",
    "insert_needle",
    "wrap_yarn",
    "pull_through",
    "purl_stitch",
    "knit_row",
    "purl_row",
    "yarn_over",
    "make_yarn_over",
    "increase_stitch",
    "knit_front_back",
    "make_one",
    "decrease_stitch",
    "knit_two_together",
    "slip_slip_knit",
    "bind_off",
    "cast_off",
    "secure_last_stitch",
    "pick_up_stitches",
    "pick_up_along_edge",
    "join_new_yarn",
    "weave_in_ends",
    "hide_tails",
    "block_knitting",
    "wet_block",
    "steam_block",
    "pin_to_shape",
    "seam_pieces",
    "mattress_stitch",
    "kitchener_stitch",
}


def is_generic_template(name: str, description: str) -> bool:
    """Check if this looks like a generic template output."""
    name_lower = name.lower().strip()
    desc_lower = description.lower().strip()

    # Reject "Step N:" descriptions
    if re.match(r"^step\s+\d+\s*:", desc_lower):
        return True

    # Reject {generic_verb} {generic_noun} patterns
    words = name_lower.replace("_", " ").split()
    if len(words) == 2:
        verb, noun = words
        if verb in GENERIC_VERBS and noun in GENERIC_NOUNS:
            return True

    # Reject very short descriptions that just repeat the name
    if desc_lower and len(desc_lower) < 20:
        if name_lower in desc_lower or desc_lower in name_lower:
            return True

    return False


def is_valid_atomic(name: str) -> bool:
    """Check if this is a valid atomic action."""
    name_lower = name.lower().replace("_", " ").replace("-", " ")

    # Check if starts with a valid atomic verb
    for verb in ATOMIC_VERBS:
        verb_pattern = verb.replace("_", " ")
        if name_lower.startswith(verb_pattern + " ") or name_lower == verb_pattern:
            return True

    return False


# ============================================================================
# SYSTEM PROMPT - Optimized for VLA/VLN/WBC Training
# ============================================================================

SYSTEM_PROMPT = """You are decomposing human tasks into training data for humanoid robots (VLA/VLN/Whole-Body Control).

## GOAL
Break tasks into ATOMIC ACTIONS that a robot can learn from demonstrations or execute via learned policies.

## WHAT MAKES A GOOD ATOMIC ACTION (for robot training)
1. **Observable**: Can be demonstrated and recorded (video/mocap)
2. **Executable**: Single motor primitive with clear start/end states
3. **Groundable**: References SPECIFIC objects/locations, not abstractions
4. **Repeatable**: Same action structure applies across contexts

## ATOMIC ACTION CATEGORIES

**Manipulation (arm/hand control):**
- grasp <specific_object> - close gripper/hand on object
- release <object> - open gripper, let go
- pick_up <object> from <surface/container>
- place <object> on/in <target_location>
- push/pull <object> <direction/distance>
- rotate/twist <object> <angle/direction>
- insert <object> into <receptacle>
- pour <substance> from <source> into <target>
- open/close <door/drawer/lid/container>
- press/push <button/switch/key>
- turn <knob/dial/handle> <direction>
- slide <object> <direction>
- flip/toss <object>
- catch <object>
- hold <object> while <other_action> (bimanual)
- stabilize <object> with <hand>

**Locomotion/Navigation (VLN - whole body):**
- walk_to <specific_location/object>
- approach <target> until <distance>
- navigate_around <obstacle>
- enter/exit <room/door/area>
- climb/descend <stairs/ladder/step>
- turn_to_face <direction/object>
- step <direction> <distance>
- crouch/stand/kneel
- lean <direction> to <reach/see>
- balance_on <surface>

**Active Perception (head/gaze/sensors):**
- look_at <target_object/location>
- scan <area> for <object_type>
- track <moving_object> visually
- read <text/display/label>
- inspect <object> for <property>
- listen_for <sound_type>
- feel/probe <surface> for <property>
- measure <dimension> of <object>

**Communication/Social (for HRI):**
- say "<utterance>"
- gesture <type> toward <target>
- point_at <object/direction>
- nod/shake_head
- make_eye_contact with <person>
- hand_over <object> to <person>
- receive <object> from <person>

## OUTPUT FORMAT
```json
{
    "is_atomic": boolean,
    "subtasks": [
        {
            "name": "<verb> <specific_object/location>",
            "description": "Physical execution: <how body moves>. Sensing: <what to perceive>. Success: <end state>.",
            "is_atomic": boolean,
            "category": "manipulation|locomotion|perception|communication"
        }
    ]
}
```

## RULES FOR VLA/VLN TRAINING UTILITY
1. **Specific objects**: "grasp the red mug" not "grasp object" - robots need grounded references
2. **Physical descriptions**: Include body parts, forces, directions - "extend right arm forward, close fingers around handle"
3. **Clear success criteria**: "until fingers contact surface" or "until object is 10cm above table"
4. **Sensing modalities**: Specify visual/tactile/proprioceptive feedback needed
5. **No abstractions**: Decompose cognitive tasks (decide, plan, think) into observable actions
6. **Reusable primitives**: "pick_up mug from table" is reusable; "do the mug thing" is not
7. **3-8 subtasks**: Enough granularity without over-fragmentation

## ANTI-PATTERNS (reject these)
- "Step 1: prepare materials" - generic, not trainable
- "check equipment" - what sensing? what equipment?
- "handle the situation" - not executable
- "process the items" - not physical"""


def make_prompt(node: TaskNode) -> str:
    """Create the decomposition prompt for VLA/VLN training."""
    context_parts = []
    if node.description:
        context_parts.append(f"Description: {node.description}")
    if node.parent_id:
        parent_parts = node.parent_id.split("/")
        if len(parent_parts) >= 2:
            context_parts.append(f"Domain: {parent_parts[0].replace('_', ' ')}")
        if len(parent_parts) >= 3:
            context_parts.append(f"Parent task: {parent_parts[-1].replace('_', ' ')}")

    context = "\n".join(context_parts) if context_parts else ""

    return f"""Decompose into atomic actions for humanoid robot training:

**Task:** {node.name}
{context}

For each subtask, specify:
- The PHYSICAL motion (which body parts, what trajectory)
- The SENSING required (visual, tactile, proprioceptive)
- The SUCCESS condition (how robot knows it's done)

Output JSON with specific, trainable actions."""


# ============================================================================
# CORE GENERATOR
# ============================================================================


class AtomicCounter:
    """Thread-safe counter."""

    def __init__(self, initial: int = 0):
        self._value = initial
        self._lock = threading.Lock()

    def increment(self, delta: int = 1) -> int:
        with self._lock:
            self._value += delta
            return self._value

    def set(self, value: int) -> None:
        with self._lock:
            self._value = value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value


@dataclass
class FastGenConfig:
    output_dir: Path
    model: str = "models/gemini-2.5-flash"
    max_tasks: int = 100000
    max_workers: int = 128
    queue_size: int = 1000
    rpm_limit: int = 1000
    mock: bool = False
    save_interval: int = 200
    tui: bool = True
    validate: bool = True  # Enable validation


class GeneratorCore:
    """Core generation logic - thread-safe."""

    def __init__(self, config: FastGenConfig):
        self.config = config
        self.graph = TaskGraph(config.output_dir)

        # Stats
        self.generated = AtomicCounter(0)
        self.decomposed = AtomicCounter(0)
        self.atomic_found = AtomicCounter(0)
        self.errors = AtomicCounter(0)
        self.api_calls = AtomicCounter(0)
        self.in_flight = AtomicCounter(0)
        self.work_queued = AtomicCounter(0)
        self.rejected = AtomicCounter(0)  # Validation rejections

        # Track processed
        self._processed_ids: set[str] = set()
        self._processed_lock = threading.Lock()

        # Pending nodes to save
        self._pending_nodes: list[TaskNode] = []
        self._pending_lock = threading.Lock()

        # Status message
        self.status = "Initializing..."
        self._status_lock = threading.Lock()

        # Control
        self._shutdown = threading.Event()
        self._start_time = time.time()
        self._done = False

        self._load_processed()

        # LLM client
        llm_config = LLMConfig(model=config.model, thinking_budget=0)
        if config.mock:
            self._client = MockLLMClient(config=llm_config, delay=0.05)
        else:
            self._client = LLMClient(config=llm_config)

        self.set_status("Ready")

    def set_status(self, msg: str):
        with self._status_lock:
            self.status = msg

    def get_status(self) -> str:
        with self._status_lock:
            return self.status

    def _load_processed(self):
        count = 0
        for node in self.graph.iter_nodes():
            if node.children_ids:
                self._processed_ids.add(node.id)
                count += 1
        self.set_status(f"Loaded {count:,} processed nodes")

    def get_rpm(self) -> float:
        elapsed = time.time() - self._start_time
        if elapsed < 1:
            return 0
        return (self.api_calls.value / elapsed) * 60

    def get_elapsed(self) -> float:
        return time.time() - self._start_time

    def is_processed(self, node_id: str) -> bool:
        with self._processed_lock:
            return node_id in self._processed_ids

    def mark_processed(self, node_id: str):
        with self._processed_lock:
            self._processed_ids.add(node_id)

    def get_pending_count(self) -> int:
        with self._pending_lock:
            return len(self._pending_nodes)

    def _decompose_node(self, node: TaskNode) -> dict:
        """Decompose a single node. Thread-safe."""
        self.api_calls.increment()
        self.in_flight.increment()

        try:
            prompt = make_prompt(node)
            response = self._client.generate(prompt, SYSTEM_PROMPT, use_thinking=False)

            # Parse JSON
            json_text = response.strip()
            if "```" in json_text:
                parts = json_text.split("```")
                for part in parts:
                    if part.strip().startswith("json"):
                        json_text = part.strip()[4:]
                        break
                    elif part.strip().startswith("{"):
                        json_text = part.strip()
                        break

            result = json.loads(json_text.strip())
            return {"node_id": node.id, "node": node, "success": True, **result}

        except json.JSONDecodeError as e:
            self.errors.increment()
            return {
                "node_id": node.id,
                "node": node,
                "success": False,
                "error": f"JSON: {str(e)[:50]}",
            }
        except Exception as e:
            self.errors.increment()
            return {"node_id": node.id, "node": node, "success": False, "error": str(e)[:100]}
        finally:
            self.in_flight.increment(-1)

    def _process_result(self, result: dict) -> int:
        """Process a decomposition result with validation."""
        if not result.get("success"):
            return 0

        node_id = result["node_id"]
        node = result["node"]
        is_atomic = result.get("is_atomic", False)
        subtasks = result.get("subtasks", [])

        self.mark_processed(node_id)

        if is_atomic or not subtasks:
            # Validate atomic
            if self.config.validate and not is_valid_atomic(node.name):
                # Don't mark as atomic if it doesn't look like one
                # Just skip - it will be reprocessed or stay as subtask
                self.rejected.increment()
                return 0

            node.node_type = NodeType.ATOMIC
            with self._pending_lock:
                self._pending_nodes.append(node)
            self.atomic_found.increment()
            return 0

        count = 0

        with self._pending_lock:
            for subtask in subtasks:
                name = subtask.get("name", str(subtask))
                if not name:
                    continue

                description = subtask.get("description", "")

                # Validate: reject generic templates
                if self.config.validate and is_generic_template(name, description):
                    self.rejected.increment()
                    continue

                child_type = NodeType.ATOMIC if subtask.get("is_atomic") else NodeType.SUBTASK

                # Extra validation for atomic claims
                if child_type == NodeType.ATOMIC and self.config.validate:
                    if not is_valid_atomic(name):
                        child_type = NodeType.SUBTASK  # Downgrade to subtask

                child = TaskNode(
                    id=TaskNode.make_id(name, node.id),
                    name=name,
                    node_type=child_type,
                    parent_id=node.id,
                    description=description,
                    sources=[SeedSource.LLM_GENERATED],
                )

                # Add category as tag if provided
                category = subtask.get("category", "")
                if category:
                    child.tags = [category]

                try:
                    self.graph.add_node(child, save=False)
                    self._pending_nodes.append(child)
                    count += 1
                    if child_type == NodeType.ATOMIC:
                        self.atomic_found.increment()
                except ValueError:
                    pass  # Duplicate

        self.decomposed.increment()
        self.generated.increment(count)
        return count

    def save_pending(self):
        """Save all pending nodes to disk."""
        with self._pending_lock:
            if not self._pending_nodes:
                return
            for node in self._pending_nodes:
                self.graph._save_node(node)
            self._pending_nodes.clear()
        self.graph._save_manifest()

    def iter_decomposable(self, limit: int = 500):
        """Yield nodes that need decomposition."""
        count = 0
        for node in self.graph.get_leaves():
            if count >= limit:
                break
            if self.is_processed(node.id):
                continue
            if node.children_ids:
                self.mark_processed(node.id)
                continue
            if node.node_type == NodeType.DOMAIN:
                continue
            if node.node_type == NodeType.ATOMIC:
                continue
            yield node
            count += 1

    def should_stop(self) -> bool:
        return self._shutdown.is_set() or self.generated.value >= self.config.max_tasks

    def stop(self):
        self._shutdown.set()


# ============================================================================
# RUNNERS
# ============================================================================


def run_without_tui(config: FastGenConfig) -> dict:
    """Run generation without TUI - simple progress output."""
    from tqdm import tqdm

    core = GeneratorCore(config)
    initial_count = len(list(core.graph.iter_nodes()))

    print(f"\n{'='*60}")
    print(f"  Task Mining (improved prompts + validation)")
    print(f"{'='*60}")
    print(f"  Output:     {config.output_dir}")
    print(f"  Workers:    {config.max_workers}")
    print(f"  Validate:   {config.validate}")
    print(f"  Initial:    {initial_count:,} nodes")
    print(f"{'='*60}\n")

    pbar = tqdm(total=config.max_tasks, desc="Mining", unit="tasks")
    save_counter = 0

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        while not core.should_stop():
            nodes = list(core.iter_decomposable(limit=config.queue_size))

            if not nodes:
                core.save_pending()
                nodes = list(core.iter_decomposable(limit=config.queue_size))
                if not nodes:
                    print("\n[INFO] No more nodes to decompose")
                    break

            futures = [executor.submit(core._decompose_node, n) for n in nodes]

            for future in as_completed(futures):
                if core.should_stop():
                    break
                try:
                    result = future.result(timeout=60)
                    count = core._process_result(result)
                    pbar.update(count)
                    save_counter += count

                    pbar.set_postfix(
                        {
                            "rpm": f"{core.get_rpm():.0f}",
                            "atomic": core.atomic_found.value,
                            "rej": core.rejected.value,
                            "err": core.errors.value,
                        }
                    )
                except Exception:
                    core.errors.increment()

            if save_counter >= config.save_interval:
                core.save_pending()
                save_counter = 0

    pbar.close()
    core.save_pending()

    elapsed = core.get_elapsed()
    final_count = len(list(core.graph.iter_nodes()))

    print(f"\n{'='*60}")
    print(f"  COMPLETE")
    print(f"{'='*60}")
    print(f"  Generated: {core.generated.value:,}")
    print(f"  Atomic:    {core.atomic_found.value:,}")
    print(f"  Rejected:  {core.rejected.value:,}")
    print(f"  Errors:    {core.errors.value}")
    print(f"  Time:      {elapsed:.0f}s")
    print(f"  Avg RPM:   {core.get_rpm():.0f}")
    print(f"  Nodes:     {final_count:,} (was {initial_count:,})")
    print(f"{'='*60}\n")

    return {
        "generated": core.generated.value,
        "atomic_found": core.atomic_found.value,
        "rejected": core.rejected.value,
        "errors": core.errors.value,
        "api_calls": core.api_calls.value,
    }


def run_with_tui(config: FastGenConfig) -> dict:
    """Run generation with Textual TUI."""
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, Static, ProgressBar, Label
    from textual.containers import Container

    # Create core outside the app
    core = GeneratorCore(config)
    initial_count = len(list(core.graph.iter_nodes()))
    result_holder = {"result": {}}

    class GeneratorApp(App):
        """Textual app for monitoring generation."""

        CSS = """
        Screen {
            layout: vertical;
        }

        #title {
            text-align: center;
            text-style: bold;
            background: $primary;
            color: $text;
            padding: 1;
        }

        #progress-section {
            height: 4;
            padding: 0 2;
        }

        #flow-section {
            height: 6;
            padding: 1 2;
            border: solid $primary;
            margin: 1;
        }

        #stats-section {
            height: 14;
            padding: 1 2;
            border: solid $secondary;
            margin: 1;
        }

        #status {
            text-align: center;
            background: $surface;
            padding: 1;
        }

        .flow-line {
            height: 1;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("s", "save", "Save Now"),
        ]

        def __init__(self):
            super().__init__()
            self._executor: ThreadPoolExecutor | None = None
            self._worker_thread: threading.Thread | None = None
            self._running = True

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static("TASK MINING (improved prompts + validation)", id="title")

            with Container(id="progress-section"):
                yield Label(f"Progress: 0 / {config.max_tasks:,}", id="progress-label")
                yield ProgressBar(total=config.max_tasks, show_eta=True, id="progress-bar")

            with Container(id="flow-section"):
                yield Static("─── FLOW ───", id="flow-title")
                yield Static(
                    "Work Queue:   [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]    0",
                    id="work-bar",
                    classes="flow-line",
                )
                yield Static(
                    "In Flight:    [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]    0",
                    id="flight-bar",
                    classes="flow-line",
                )
                yield Static(
                    "Pending Save: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]    0",
                    id="pending-bar",
                    classes="flow-line",
                )

            with Container(id="stats-section"):
                yield Static(self._render_stats(), id="stats")

            yield Static("Starting...", id="status")
            yield Footer()

        def _make_bar(self, label: str, value: int, max_val: int) -> str:
            if max_val == 0:
                pct = 0
            else:
                pct = min(100, (value / max_val) * 100)
            width = 30
            filled = int(width * pct / 100)
            bar = "█" * filled + "░" * (width - filled)
            return f"{label:14}[{bar}] {value:>4}"

        def _render_stats(self) -> str:
            elapsed = core.get_elapsed()
            rpm = core.get_rpm()
            rate = core.generated.value / elapsed if elapsed > 0 else 0

            # ETA
            if rate > 0:
                remaining = config.max_tasks - core.generated.value
                eta_sec = remaining / rate
                if eta_sec > 3600:
                    eta = f"{eta_sec/3600:.1f}h"
                elif eta_sec > 60:
                    eta = f"{eta_sec/60:.0f}m"
                else:
                    eta = f"{eta_sec:.0f}s"
            else:
                eta = "..."

            return f"""─── STATISTICS ───
  Generated:  {core.generated.value:>10,}     ETA: {eta}
  Atomic:     {core.atomic_found.value:>10,}
  Decomposed: {core.decomposed.value:>10,}
  Rejected:   {core.rejected.value:>10,}     (validation)
  Errors:     {core.errors.value:>10,}
  API Calls:  {core.api_calls.value:>10,}
  ─────────────────
  RPM:        {rpm:>10.0f}
  Rate:       {rate:>10.1f} tasks/s
  Elapsed:    {elapsed:>10.0f}s"""

        def on_mount(self) -> None:
            # Start worker thread
            self._worker_thread = threading.Thread(target=self._run_generation, daemon=True)
            self._worker_thread.start()

            # Update UI periodically
            self.set_interval(0.2, self._update_ui)

        def _update_ui(self) -> None:
            # Progress
            self.query_one("#progress-bar", ProgressBar).update(progress=core.generated.value)
            self.query_one("#progress-label", Label).update(
                f"Progress: {core.generated.value:,} / {config.max_tasks:,}"
            )

            # Flow bars
            self.query_one("#work-bar", Static).update(
                self._make_bar("Work Queue:", core.work_queued.value, config.queue_size)
            )
            self.query_one("#flight-bar", Static).update(
                self._make_bar("In Flight:", core.in_flight.value, config.max_workers)
            )
            self.query_one("#pending-bar", Static).update(
                self._make_bar("Pending Save:", core.get_pending_count(), config.save_interval)
            )

            # Stats
            self.query_one("#stats", Static).update(self._render_stats())

            # Status
            self.query_one("#status", Static).update(core.get_status())

        def _run_generation(self) -> None:
            """Run generation in background thread."""
            save_counter = 0

            try:
                with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
                    while self._running and not core.should_stop():
                        nodes = list(core.iter_decomposable(limit=200))
                        core.work_queued.set(len(nodes))

                        if not nodes:
                            core.save_pending()
                            save_counter = 0
                            time.sleep(0.1)
                            nodes = list(core.iter_decomposable(limit=200))
                            core.work_queued.set(len(nodes))
                            if not nodes:
                                core.set_status("Hierarchy fully mined! Press Q to exit.")
                                core._done = True
                                break

                        core.set_status(f"Processing {len(nodes)} nodes...")

                        futures = [executor.submit(core._decompose_node, n) for n in nodes]

                        for future in as_completed(futures):
                            if not self._running:
                                break
                            try:
                                result = future.result(timeout=30)
                                core._process_result(result)
                                save_counter += 1
                            except Exception as e:
                                core.errors.increment()

                        if save_counter >= config.save_interval:
                            core.set_status("Saving...")
                            core.save_pending()
                            save_counter = 0

                # Final save
                core.save_pending()

                result_holder["result"] = {
                    "generated": core.generated.value,
                    "atomic_found": core.atomic_found.value,
                    "decomposed": core.decomposed.value,
                    "rejected": core.rejected.value,
                    "errors": core.errors.value,
                    "api_calls": core.api_calls.value,
                }

                if core.generated.value >= config.max_tasks:
                    core.set_status(f"Reached {config.max_tasks:,} tasks! Press Q to exit.")

            except Exception as e:
                core.set_status(f"Error: {e}")

        def action_quit(self) -> None:
            self._running = False
            core.stop()
            core.save_pending()
            self.exit()

        def action_save(self) -> None:
            core.save_pending()
            core.set_status("Saved!")

    # Run the app
    app = GeneratorApp()
    app.run()

    # Print final summary
    elapsed = core.get_elapsed()
    final_count = len(list(core.graph.iter_nodes()))

    print(f"\n{'='*60}")
    print(f"  COMPLETE")
    print(f"{'='*60}")
    print(f"  Generated: {core.generated.value:,}")
    print(f"  Atomic:    {core.atomic_found.value:,}")
    print(f"  Rejected:  {core.rejected.value:,}")
    print(f"  Errors:    {core.errors.value}")
    print(f"  Time:      {elapsed:.0f}s")
    print(f"  Avg RPM:   {core.get_rpm():.0f}")
    print(f"  Nodes:     {final_count:,} (was {initial_count:,})")
    print(f"{'='*60}\n")

    return result_holder["result"]


def run(config: FastGenConfig) -> dict:
    """Run generation with or without TUI."""
    import sys

    if config.tui and sys.stdout.isatty():
        try:
            return run_with_tui(config)
        except ImportError as e:
            print(f"[WARN] Textual not available ({e}), using simple mode")
            return run_without_tui(config)
    else:
        return run_without_tui(config)


# For backwards compatibility
class FastGenerator:
    def __init__(self, config: FastGenConfig):
        self.config = config

    def run(self) -> dict:
        return run(self.config)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fast VLA/VLN task mining")
    parser.add_argument("-o", "--output", default="./task_hierarchy", help="Output directory")
    parser.add_argument("--max-tasks", type=int, default=100000, help="Max tasks to generate")
    parser.add_argument("--workers", type=int, default=128, help="Concurrent workers")
    parser.add_argument("--queue-size", type=int, default=1000, help="Work queue size")
    parser.add_argument("--rpm", type=int, default=1000, help="Rate limit (RPM)")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM")
    parser.add_argument("--no-tui", action="store_true", help="Disable TUI")
    parser.add_argument("--no-validate", action="store_true", help="Disable output validation")
    args = parser.parse_args()

    config = FastGenConfig(
        output_dir=Path(args.output),
        max_tasks=args.max_tasks,
        max_workers=args.workers,
        queue_size=args.queue_size,
        rpm_limit=args.rpm,
        mock=args.mock,
        tui=not args.no_tui,
        validate=not args.no_validate,
    )

    run(config)


if __name__ == "__main__":
    main()
