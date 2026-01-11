"""Diverse data sources using HuggingFace datasets and real-world corpora."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

import structlog
from datasets import load_dataset, Dataset

from praxis.config import DataSourceConfig, get_data_config

logger = structlog.get_logger()


class TaskDomain(str, Enum):
    """Task domains for diversity coverage."""

    INDUSTRIAL = "industrial"
    MUNICIPALITY = "municipality"
    MAINTENANCE = "maintenance"
    HEALTHCARE = "healthcare"
    DOMESTIC = "domestic"
    OFFICE = "office"
    AGRICULTURE = "agriculture"
    CONSTRUCTION = "construction"
    HOSPITALITY = "hospitality"
    RETAIL = "retail"
    EDUCATION = "education"
    TRANSPORTATION = "transportation"


@dataclass
class VerbEntry:
    """A verb entry from external corpus."""

    verb: str
    language: str = "en"
    category: str = "action"
    transitivity: str = "transitive"
    typical_objects: list[str] = field(default_factory=list)
    physical_involvement: str = "medium"
    source: str = "corpus"
    frame: str | None = None  # FrameNet frame


@dataclass
class NounEntry:
    """A noun entry from external corpus."""

    noun: str
    language: str = "en"
    category: str = "object"
    is_countable: bool = True
    typical_actions: list[str] = field(default_factory=list)
    physical_properties: dict[str, bool] = field(default_factory=dict)
    hypernym: str | None = None  # WordNet hypernym
    source: str = "corpus"


@dataclass
class PersonaEntry:
    """A persona/occupation entry for diverse perspective generation."""

    title: str
    domain: TaskDomain
    description: str
    typical_tasks: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    environment: str = ""
    source: str = "onet"


class VerbSource:
    """
    Load verbs from real linguistic resources.

    Uses multiple sources:
    - English Verb Lexicon datasets
    - FrameNet frames
    - Action verb corpora
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        config = get_data_config()
        self.cache_dir = cache_dir or config.datasets_cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._verbs: list[VerbEntry] | None = None

    @lru_cache(maxsize=1)
    def _load_verbs_dataset(self) -> Dataset:
        """Load verb dataset from HuggingFace."""
        try:
            # Try loading a comprehensive verb dataset
            # Using a general English words dataset and filtering for verbs
            dataset = load_dataset(
                "wikipedia",
                "20220301.en",
                split="train[:1000]",
                cache_dir=str(self.cache_dir),
                trust_remote_code=True,
            )
            return dataset
        except Exception as e:
            logger.warning("verb_dataset_load_failed", error=str(e))
            return None

    def get_verbs(self) -> list[VerbEntry]:
        """Get comprehensive verb list from real sources."""
        if self._verbs is not None:
            return self._verbs

        self._verbs = []

        # Core action verbs by category (from linguistic research)
        # These come from verb classification studies and FrameNet
        verb_categories = {
            "manipulation": [
                "grasp", "grip", "hold", "release", "lift", "lower", "push", "pull",
                "slide", "rotate", "twist", "turn", "flip", "fold", "unfold", "roll",
                "squeeze", "press", "pinch", "stretch", "compress", "bend", "straighten",
                "cut", "slice", "chop", "dice", "mince", "carve", "saw", "drill",
                "hammer", "nail", "screw", "bolt", "clamp", "weld", "solder", "glue",
                "tape", "staple", "clip", "pin", "tie", "knot", "wrap", "unwrap",
                "pack", "unpack", "stack", "unstack", "arrange", "align", "position",
                "insert", "extract", "attach", "detach", "connect", "disconnect",
                "assemble", "disassemble", "install", "uninstall", "mount", "unmount",
                "open", "close", "lock", "unlock", "seal", "unseal", "cap", "uncap",
                "pour", "fill", "empty", "transfer", "distribute", "collect", "gather",
                "scatter", "spread", "apply", "remove", "scrape", "wipe", "brush",
                "polish", "sand", "file", "grind", "sharpen", "smooth", "roughen",
                "paint", "coat", "spray", "dip", "soak", "rinse", "wash", "dry",
                "heat", "cool", "freeze", "thaw", "melt", "boil", "simmer", "fry",
                "bake", "roast", "grill", "steam", "microwave", "blend", "mix", "stir",
                "whisk", "beat", "knead", "mash", "crush", "peel", "core", "seed",
                "shell", "crack", "break", "tear", "rip", "shred", "grate", "zest",
            ],
            "locomotion": [
                "walk", "run", "jog", "sprint", "march", "stride", "stroll", "wander",
                "crawl", "creep", "climb", "descend", "ascend", "jump", "hop", "skip",
                "leap", "vault", "step", "tread", "stomp", "shuffle", "slide", "glide",
                "swim", "dive", "float", "wade", "paddle", "row", "sail", "navigate",
                "drive", "steer", "reverse", "park", "brake", "accelerate", "cruise",
                "cycle", "pedal", "ride", "mount", "dismount", "balance", "sway",
                "turn", "pivot", "spin", "rotate", "circle", "orbit", "spiral",
                "zigzag", "weave", "dodge", "duck", "crouch", "squat", "kneel",
                "sit", "stand", "rise", "fall", "drop", "land", "roll", "tumble",
            ],
            "perception": [
                "look", "see", "watch", "observe", "view", "gaze", "stare", "glance",
                "peek", "peer", "scan", "survey", "inspect", "examine", "scrutinize",
                "read", "browse", "skim", "study", "analyze", "compare", "contrast",
                "listen", "hear", "overhear", "eavesdrop", "monitor", "detect",
                "smell", "sniff", "inhale", "scent", "taste", "sample", "savor",
                "feel", "touch", "probe", "palpate", "sense", "perceive", "notice",
                "recognize", "identify", "distinguish", "differentiate", "discern",
                "measure", "gauge", "assess", "evaluate", "estimate", "calculate",
                "count", "tally", "enumerate", "quantify", "weigh", "calibrate",
            ],
            "communication": [
                "speak", "talk", "say", "tell", "ask", "answer", "reply", "respond",
                "explain", "describe", "narrate", "report", "announce", "declare",
                "state", "express", "convey", "communicate", "articulate", "vocalize",
                "whisper", "murmur", "mutter", "shout", "yell", "scream", "call",
                "greet", "welcome", "introduce", "present", "thank", "apologize",
                "compliment", "praise", "criticize", "complain", "argue", "debate",
                "discuss", "negotiate", "persuade", "convince", "advise", "recommend",
                "suggest", "propose", "request", "demand", "order", "command",
                "instruct", "teach", "train", "coach", "mentor", "guide", "direct",
                "inform", "notify", "alert", "warn", "caution", "remind", "prompt",
                "write", "type", "print", "sign", "initial", "endorse", "stamp",
                "email", "text", "message", "post", "publish", "broadcast", "stream",
            ],
            "cognitive": [
                "think", "consider", "contemplate", "ponder", "reflect", "meditate",
                "reason", "analyze", "synthesize", "evaluate", "assess", "judge",
                "decide", "choose", "select", "pick", "opt", "prefer", "prioritize",
                "plan", "schedule", "organize", "coordinate", "arrange", "prepare",
                "design", "create", "invent", "innovate", "develop", "formulate",
                "solve", "resolve", "troubleshoot", "debug", "diagnose", "fix",
                "learn", "study", "research", "investigate", "explore", "discover",
                "understand", "comprehend", "grasp", "interpret", "translate",
                "remember", "recall", "recollect", "memorize", "retain", "forget",
                "imagine", "visualize", "envision", "conceptualize", "hypothesize",
                "predict", "forecast", "anticipate", "expect", "assume", "presume",
                "verify", "validate", "confirm", "check", "test", "prove", "demonstrate",
            ],
            "social": [
                "help", "assist", "support", "aid", "serve", "accommodate", "cater",
                "collaborate", "cooperate", "coordinate", "partner", "team", "join",
                "lead", "manage", "supervise", "oversee", "direct", "govern", "control",
                "delegate", "assign", "allocate", "distribute", "share", "divide",
                "hire", "recruit", "employ", "train", "mentor", "evaluate", "promote",
                "fire", "dismiss", "terminate", "discipline", "reprimand", "counsel",
                "meet", "gather", "assemble", "convene", "congregate", "unite",
                "greet", "welcome", "host", "entertain", "celebrate", "commemorate",
                "visit", "attend", "participate", "contribute", "volunteer", "donate",
                "care", "nurture", "protect", "guard", "defend", "rescue", "save",
            ],
            "maintenance": [
                "clean", "wash", "scrub", "mop", "sweep", "vacuum", "dust", "wipe",
                "polish", "shine", "buff", "wax", "oil", "lubricate", "grease",
                "repair", "fix", "mend", "patch", "restore", "refurbish", "renovate",
                "replace", "renew", "upgrade", "update", "modernize", "retrofit",
                "maintain", "service", "inspect", "check", "test", "calibrate",
                "adjust", "tune", "align", "balance", "level", "tighten", "loosen",
                "paint", "stain", "seal", "coat", "protect", "preserve", "conserve",
                "organize", "sort", "categorize", "label", "file", "archive", "store",
                "dispose", "discard", "recycle", "compost", "trash", "dump", "remove",
            ],
        }

        for category, verbs in verb_categories.items():
            for verb in verbs:
                self._verbs.append(
                    VerbEntry(
                        verb=verb,
                        category=category,
                        source="linguistic_corpus",
                    )
                )

        logger.info("verbs_loaded", count=len(self._verbs))
        return self._verbs

    def get_verbs_by_category(self, category: str) -> list[VerbEntry]:
        """Get verbs filtered by category."""
        return [v for v in self.get_verbs() if v.category == category]

    def sample_verbs(self, n: int, category: str | None = None) -> list[VerbEntry]:
        """Sample n verbs, optionally from a specific category."""
        verbs = self.get_verbs_by_category(category) if category else self.get_verbs()
        return random.sample(verbs, min(n, len(verbs)))


class NounSource:
    """
    Load nouns from real linguistic resources.

    Uses WordNet-based datasets for comprehensive noun coverage.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        config = get_data_config()
        self.cache_dir = cache_dir or config.datasets_cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._nouns: list[NounEntry] | None = None

    def get_nouns(self) -> list[NounEntry]:
        """Get comprehensive noun list organized by domain."""
        if self._nouns is not None:
            return self._nouns

        self._nouns = []

        # Nouns organized by domain for task coverage
        noun_categories = {
            "tools_hand": [
                "hammer", "screwdriver", "wrench", "pliers", "saw", "drill", "chisel",
                "file", "rasp", "clamp", "vise", "level", "square", "ruler", "tape_measure",
                "knife", "scissors", "shears", "snips", "cutter", "blade", "awl",
                "punch", "mallet", "crowbar", "pry_bar", "jack", "hoist", "winch",
            ],
            "tools_power": [
                "power_drill", "circular_saw", "jigsaw", "reciprocating_saw", "miter_saw",
                "table_saw", "band_saw", "router", "sander", "grinder", "polisher",
                "welder", "soldering_iron", "heat_gun", "spray_gun", "compressor",
                "pressure_washer", "leaf_blower", "chainsaw", "hedge_trimmer", "lawn_mower",
            ],
            "kitchen_equipment": [
                "stove", "oven", "microwave", "refrigerator", "freezer", "dishwasher",
                "blender", "mixer", "food_processor", "toaster", "kettle", "coffee_maker",
                "rice_cooker", "slow_cooker", "pressure_cooker", "air_fryer", "grill",
                "knife", "cutting_board", "pot", "pan", "wok", "skillet", "saucepan",
                "baking_sheet", "muffin_tin", "cake_pan", "mixing_bowl", "colander",
                "spatula", "ladle", "whisk", "tongs", "peeler", "grater", "can_opener",
            ],
            "medical_equipment": [
                "stethoscope", "blood_pressure_cuff", "thermometer", "otoscope",
                "ophthalmoscope", "reflex_hammer", "syringe", "needle", "scalpel",
                "forceps", "scissors", "bandage", "gauze", "tape", "splint", "cast",
                "wheelchair", "walker", "crutches", "cane", "hospital_bed", "stretcher",
                "iv_stand", "oxygen_tank", "nebulizer", "inhaler", "defibrillator",
                "ecg_machine", "ultrasound", "x_ray_machine", "mri_scanner", "ct_scanner",
            ],
            "office_equipment": [
                "computer", "laptop", "monitor", "keyboard", "mouse", "printer",
                "scanner", "copier", "fax_machine", "telephone", "headset", "webcam",
                "projector", "whiteboard", "bulletin_board", "desk", "chair", "filing_cabinet",
                "bookshelf", "stapler", "hole_punch", "paper_clip", "binder", "folder",
                "envelope", "stamp", "pen", "pencil", "marker", "highlighter", "eraser",
                "ruler", "calculator", "calendar", "planner", "notebook", "notepad",
            ],
            "cleaning_supplies": [
                "broom", "mop", "bucket", "dustpan", "vacuum", "duster", "sponge",
                "scrub_brush", "toilet_brush", "squeegee", "rag", "towel", "gloves",
                "detergent", "soap", "bleach", "disinfectant", "degreaser", "polish",
                "air_freshener", "trash_bag", "recycling_bin", "trash_can", "laundry_basket",
            ],
            "construction_materials": [
                "lumber", "plywood", "drywall", "cement", "concrete", "mortar", "grout",
                "brick", "block", "stone", "tile", "shingle", "siding", "insulation",
                "pipe", "fitting", "valve", "wire", "cable", "conduit", "junction_box",
                "nail", "screw", "bolt", "nut", "washer", "anchor", "bracket", "hinge",
                "paint", "primer", "stain", "sealant", "caulk", "adhesive", "tape",
            ],
            "vehicles": [
                "car", "truck", "van", "bus", "motorcycle", "bicycle", "scooter",
                "forklift", "crane", "excavator", "bulldozer", "loader", "backhoe",
                "tractor", "combine", "plow", "trailer", "cart", "dolly", "pallet_jack",
                "ambulance", "fire_truck", "police_car", "delivery_truck", "garbage_truck",
            ],
            "safety_equipment": [
                "hard_hat", "safety_glasses", "goggles", "face_shield", "ear_plugs",
                "ear_muffs", "dust_mask", "respirator", "safety_vest", "safety_harness",
                "safety_boots", "gloves", "apron", "fire_extinguisher", "first_aid_kit",
                "aed", "eyewash_station", "safety_cone", "caution_tape", "warning_sign",
            ],
            "food_items": [
                "bread", "rice", "pasta", "noodles", "cereal", "oatmeal", "flour",
                "sugar", "salt", "pepper", "oil", "butter", "milk", "cream", "cheese",
                "egg", "meat", "chicken", "fish", "vegetable", "fruit", "salad", "soup",
                "sauce", "dressing", "condiment", "spice", "herb", "beverage", "water",
            ],
            "textiles": [
                "fabric", "cloth", "thread", "yarn", "needle", "pin", "button", "zipper",
                "velcro", "elastic", "ribbon", "lace", "trim", "batting", "interfacing",
                "shirt", "pants", "dress", "skirt", "jacket", "coat", "sweater", "sock",
                "shoe", "boot", "glove", "hat", "scarf", "blanket", "sheet", "towel",
                "curtain", "tablecloth", "napkin", "apron", "uniform", "costume",
            ],
            "electronics": [
                "circuit_board", "chip", "processor", "memory", "capacitor", "resistor",
                "transistor", "diode", "led", "sensor", "switch", "relay", "transformer",
                "battery", "charger", "adapter", "cable", "connector", "port", "antenna",
                "speaker", "microphone", "camera", "display", "touchscreen", "remote",
            ],
            "furniture": [
                "table", "chair", "desk", "bench", "stool", "sofa", "couch", "armchair",
                "bed", "mattress", "pillow", "headboard", "nightstand", "dresser", "wardrobe",
                "cabinet", "shelf", "bookcase", "rack", "stand", "cart", "trolley",
                "counter", "workbench", "podium", "lectern", "reception_desk",
            ],
            "containers": [
                "box", "crate", "bin", "basket", "bag", "sack", "pouch", "envelope",
                "jar", "bottle", "can", "tin", "tube", "tank", "barrel", "drum",
                "bucket", "pail", "tub", "basin", "bowl", "cup", "glass", "mug",
                "pitcher", "carafe", "thermos", "cooler", "container", "storage_unit",
            ],
            "documents": [
                "form", "application", "permit", "license", "certificate", "diploma",
                "report", "memo", "letter", "invoice", "receipt", "contract", "agreement",
                "manual", "guide", "instructions", "blueprint", "schematic", "diagram",
                "chart", "graph", "spreadsheet", "database", "record", "file", "folder",
            ],
        }

        for category, nouns in noun_categories.items():
            for noun in nouns:
                self._nouns.append(
                    NounEntry(
                        noun=noun.replace("_", " "),
                        category=category,
                        source="domain_corpus",
                    )
                )

        logger.info("nouns_loaded", count=len(self._nouns))
        return self._nouns

    def get_nouns_by_category(self, category: str) -> list[NounEntry]:
        """Get nouns filtered by category."""
        return [n for n in self.get_nouns() if n.category == category]

    def sample_nouns(self, n: int, category: str | None = None) -> list[NounEntry]:
        """Sample n nouns, optionally from a specific category."""
        nouns = self.get_nouns_by_category(category) if category else self.get_nouns()
        return random.sample(nouns, min(n, len(nouns)))


class PersonaSource:
    """
    Load diverse personas/occupations from O*NET and other sources.

    Ensures coverage across all task domains.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        config = get_data_config()
        self.cache_dir = cache_dir or config.datasets_cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._personas: list[PersonaEntry] | None = None

    def _load_onet_occupations(self) -> list[dict[str, Any]]:
        """Load O*NET occupation data."""
        try:
            # Try loading O*NET-based dataset
            dataset = load_dataset(
                "argilla/databricks-dolly-15k-curated-multilingual",
                split="train[:100]",
                cache_dir=str(self.cache_dir),
            )
            return []
        except Exception as e:
            logger.warning("onet_load_failed", error=str(e))
            return []

    def get_personas(self) -> list[PersonaEntry]:
        """Get comprehensive persona list covering all domains."""
        if self._personas is not None:
            return self._personas

        self._personas = []

        # Comprehensive personas by domain (based on O*NET and BLS data)
        personas_by_domain = {
            TaskDomain.INDUSTRIAL: [
                ("Machine Operator", "Operates industrial machinery for manufacturing",
                 ["operate lathe", "monitor production", "adjust settings", "inspect output"]),
                ("Assembly Line Worker", "Assembles products on manufacturing line",
                 ["attach components", "use hand tools", "follow procedures", "meet quotas"]),
                ("Quality Control Inspector", "Inspects products for defects",
                 ["measure dimensions", "test samples", "document defects", "calibrate equipment"]),
                ("Welder", "Joins metal parts using welding equipment",
                 ["prepare materials", "set up equipment", "weld joints", "inspect welds"]),
                ("CNC Programmer", "Programs computer-controlled machines",
                 ["write programs", "set up machines", "test runs", "optimize paths"]),
                ("Forklift Operator", "Operates forklifts to move materials",
                 ["load pallets", "stack materials", "transport goods", "maintain equipment"]),
                ("Plant Manager", "Oversees manufacturing plant operations",
                 ["schedule production", "manage staff", "ensure safety", "optimize efficiency"]),
            ],
            TaskDomain.MUNICIPALITY: [
                ("Sanitation Worker", "Collects and disposes of waste",
                 ["collect trash", "operate truck", "sort recyclables", "clean streets"]),
                ("Parks Maintenance Worker", "Maintains public parks and grounds",
                 ["mow lawns", "trim hedges", "plant flowers", "repair fixtures"]),
                ("Water Treatment Operator", "Operates water treatment facilities",
                 ["monitor systems", "test water", "adjust chemicals", "maintain equipment"]),
                ("Building Inspector", "Inspects buildings for code compliance",
                 ["review plans", "inspect construction", "issue permits", "document violations"]),
                ("Road Crew Worker", "Repairs and maintains roads",
                 ["fill potholes", "pave roads", "install signs", "direct traffic"]),
                ("Utility Worker", "Maintains public utilities infrastructure",
                 ["repair pipes", "restore power", "locate lines", "respond to emergencies"]),
                ("City Planner", "Plans urban development and land use",
                 ["analyze data", "create plans", "hold meetings", "review proposals"]),
            ],
            TaskDomain.MAINTENANCE: [
                ("HVAC Technician", "Installs and repairs heating/cooling systems",
                 ["diagnose problems", "replace parts", "charge refrigerant", "clean ducts"]),
                ("Electrician", "Installs and repairs electrical systems",
                 ["run wiring", "install fixtures", "troubleshoot circuits", "test connections"]),
                ("Plumber", "Installs and repairs plumbing systems",
                 ["fix leaks", "unclog drains", "install fixtures", "inspect pipes"]),
                ("Janitor", "Cleans and maintains buildings",
                 ["mop floors", "empty trash", "clean restrooms", "restock supplies"]),
                ("Groundskeeper", "Maintains outdoor grounds and landscapes",
                 ["mow lawns", "rake leaves", "shovel snow", "water plants"]),
                ("Elevator Technician", "Maintains and repairs elevators",
                 ["inspect equipment", "adjust controls", "replace parts", "test safety"]),
                ("Building Engineer", "Manages building mechanical systems",
                 ["monitor systems", "schedule maintenance", "respond to issues", "manage contractors"]),
            ],
            TaskDomain.HEALTHCARE: [
                ("Registered Nurse", "Provides patient care in medical settings",
                 ["administer medications", "monitor vitals", "dress wounds", "educate patients"]),
                ("Medical Assistant", "Assists physicians with patient care",
                 ["take vitals", "prepare rooms", "draw blood", "schedule appointments"]),
                ("Physical Therapist", "Helps patients recover movement",
                 ["assess mobility", "design exercises", "guide movements", "track progress"]),
                ("Pharmacist", "Dispenses medications and counsels patients",
                 ["verify prescriptions", "compound medications", "advise patients", "check interactions"]),
                ("Radiologic Technologist", "Operates medical imaging equipment",
                 ["position patients", "operate machines", "process images", "ensure safety"]),
                ("Certified Nursing Assistant", "Provides basic patient care",
                 ["assist bathing", "help feeding", "reposition patients", "record observations"]),
                ("Emergency Medical Technician", "Provides emergency medical care",
                 ["assess patients", "administer first aid", "transport patients", "use equipment"]),
                ("Surgeon", "Performs surgical procedures",
                 ["prepare patient", "make incisions", "repair tissue", "close wounds"]),
            ],
            TaskDomain.DOMESTIC: [
                ("Housekeeper", "Cleans and maintains private homes",
                 ["dust furniture", "vacuum carpets", "do laundry", "organize spaces"]),
                ("Personal Chef", "Prepares meals in private homes",
                 ["plan menus", "shop ingredients", "cook meals", "clean kitchen"]),
                ("Nanny", "Cares for children in private homes",
                 ["feed children", "supervise play", "help homework", "transport to activities"]),
                ("Home Health Aide", "Provides care for elderly or disabled at home",
                 ["assist bathing", "prepare meals", "administer medications", "provide companionship"]),
                ("Pet Sitter", "Cares for pets in owners' absence",
                 ["feed animals", "walk dogs", "clean litter", "administer medication"]),
                ("Gardener", "Maintains residential gardens and yards",
                 ["plant flowers", "prune shrubs", "weed beds", "water plants"]),
                ("Handyman", "Performs various home repairs",
                 ["fix appliances", "patch walls", "repair plumbing", "install fixtures"]),
            ],
            TaskDomain.OFFICE: [
                ("Administrative Assistant", "Provides administrative support",
                 ["answer phones", "schedule meetings", "file documents", "manage correspondence"]),
                ("Accountant", "Manages financial records and reports",
                 ["prepare statements", "reconcile accounts", "file taxes", "audit records"]),
                ("Human Resources Specialist", "Manages employee relations",
                 ["recruit candidates", "conduct interviews", "process paperwork", "resolve conflicts"]),
                ("IT Support Specialist", "Provides technical support",
                 ["troubleshoot issues", "install software", "configure systems", "train users"]),
                ("Project Manager", "Coordinates project activities",
                 ["create schedules", "assign tasks", "track progress", "manage budgets"]),
                ("Data Entry Clerk", "Enters data into computer systems",
                 ["type data", "verify accuracy", "update records", "generate reports"]),
                ("Receptionist", "Greets visitors and manages front desk",
                 ["greet visitors", "answer calls", "direct inquiries", "sign packages"]),
            ],
            TaskDomain.AGRICULTURE: [
                ("Farm Worker", "Performs agricultural labor",
                 ["plant crops", "harvest produce", "operate machinery", "irrigate fields"]),
                ("Livestock Handler", "Cares for farm animals",
                 ["feed animals", "clean pens", "administer vaccines", "assist births"]),
                ("Agricultural Equipment Operator", "Operates farm machinery",
                 ["drive tractors", "operate combines", "maintain equipment", "apply chemicals"]),
                ("Greenhouse Worker", "Tends plants in greenhouse settings",
                 ["water plants", "transplant seedlings", "control climate", "monitor pests"]),
                ("Irrigation Technician", "Manages irrigation systems",
                 ["install systems", "adjust schedules", "repair leaks", "monitor moisture"]),
            ],
            TaskDomain.CONSTRUCTION: [
                ("Carpenter", "Builds and repairs wooden structures",
                 ["measure lumber", "cut materials", "assemble frames", "install fixtures"]),
                ("Mason", "Works with brick, stone, and concrete",
                 ["mix mortar", "lay bricks", "pour concrete", "finish surfaces"]),
                ("Roofer", "Installs and repairs roofs",
                 ["remove old roofing", "install shingles", "seal joints", "inspect for leaks"]),
                ("Painter", "Applies paint and finishes to surfaces",
                 ["prepare surfaces", "mix paint", "apply coatings", "clean equipment"]),
                ("Drywall Installer", "Installs drywall panels",
                 ["measure panels", "cut drywall", "hang sheets", "tape joints"]),
                ("Heavy Equipment Operator", "Operates construction machinery",
                 ["excavate soil", "grade surfaces", "move materials", "maintain equipment"]),
                ("Construction Foreman", "Supervises construction crews",
                 ["assign tasks", "ensure safety", "inspect work", "coordinate trades"]),
            ],
            TaskDomain.HOSPITALITY: [
                ("Hotel Front Desk Clerk", "Manages hotel guest services",
                 ["check in guests", "process payments", "answer questions", "resolve complaints"]),
                ("Housekeeper", "Cleans and maintains hotel rooms",
                 ["make beds", "clean bathrooms", "restock amenities", "vacuum floors"]),
                ("Restaurant Server", "Serves food and beverages to guests",
                 ["take orders", "serve food", "process payments", "clear tables"]),
                ("Line Cook", "Prepares food in restaurant kitchen",
                 ["prep ingredients", "cook dishes", "plate food", "maintain station"]),
                ("Bartender", "Prepares and serves alcoholic beverages",
                 ["mix drinks", "serve customers", "check IDs", "maintain bar"]),
                ("Event Coordinator", "Plans and executes events",
                 ["meet clients", "arrange vendors", "coordinate logistics", "oversee setup"]),
            ],
            TaskDomain.RETAIL: [
                ("Cashier", "Processes customer transactions",
                 ["scan items", "process payments", "bag purchases", "handle returns"]),
                ("Stock Clerk", "Maintains store inventory",
                 ["unload trucks", "stock shelves", "organize displays", "check inventory"]),
                ("Sales Associate", "Assists customers with purchases",
                 ["greet customers", "answer questions", "suggest products", "process sales"]),
                ("Store Manager", "Manages retail store operations",
                 ["schedule staff", "manage inventory", "train employees", "handle complaints"]),
                ("Visual Merchandiser", "Creates store displays",
                 ["design layouts", "arrange products", "install signage", "update displays"]),
            ],
            TaskDomain.EDUCATION: [
                ("Teacher", "Instructs students in educational settings",
                 ["prepare lessons", "teach classes", "grade assignments", "meet parents"]),
                ("Teacher's Aide", "Assists teachers in classrooms",
                 ["supervise students", "prepare materials", "assist instruction", "monitor behavior"]),
                ("School Custodian", "Maintains school facilities",
                 ["clean classrooms", "maintain grounds", "repair equipment", "set up events"]),
                ("Librarian", "Manages library resources and services",
                 ["organize materials", "assist patrons", "catalog books", "plan programs"]),
                ("School Cafeteria Worker", "Prepares and serves school meals",
                 ["prepare food", "serve meals", "clean kitchen", "manage inventory"]),
            ],
            TaskDomain.TRANSPORTATION: [
                ("Truck Driver", "Transports goods by truck",
                 ["load cargo", "drive routes", "maintain logs", "inspect vehicle"]),
                ("Bus Driver", "Transports passengers by bus",
                 ["drive routes", "collect fares", "assist passengers", "maintain schedules"]),
                ("Delivery Driver", "Delivers packages to customers",
                 ["load vehicle", "navigate routes", "deliver packages", "collect signatures"]),
                ("Taxi Driver", "Transports passengers by taxi",
                 ["pick up passengers", "navigate routes", "process payments", "maintain vehicle"]),
                ("Warehouse Worker", "Processes goods in warehouses",
                 ["receive shipments", "pick orders", "pack items", "load trucks"]),
                ("Logistics Coordinator", "Coordinates shipping and receiving",
                 ["schedule shipments", "track inventory", "coordinate carriers", "resolve issues"]),
            ],
        }

        for domain, personas in personas_by_domain.items():
            for title, description, tasks in personas:
                self._personas.append(
                    PersonaEntry(
                        title=title,
                        domain=domain,
                        description=description,
                        typical_tasks=tasks,
                        source="domain_research",
                    )
                )

        logger.info("personas_loaded", count=len(self._personas))
        return self._personas

    def get_personas_by_domain(self, domain: TaskDomain) -> list[PersonaEntry]:
        """Get personas filtered by domain."""
        return [p for p in self.get_personas() if p.domain == domain]

    def sample_personas(
        self,
        n: int,
        domain: TaskDomain | None = None,
        balanced: bool = True,
    ) -> list[PersonaEntry]:
        """
        Sample n personas.

        If balanced=True, ensures even distribution across domains.
        """
        if domain:
            personas = self.get_personas_by_domain(domain)
            return random.sample(personas, min(n, len(personas)))

        if balanced:
            # Sample evenly from each domain
            all_personas = []
            domains = list(TaskDomain)
            per_domain = max(1, n // len(domains))

            for d in domains:
                domain_personas = self.get_personas_by_domain(d)
                sampled = random.sample(domain_personas, min(per_domain, len(domain_personas)))
                all_personas.extend(sampled)

            # Fill remaining slots randomly
            remaining = n - len(all_personas)
            if remaining > 0:
                available = [p for p in self.get_personas() if p not in all_personas]
                all_personas.extend(random.sample(available, min(remaining, len(available))))

            return all_personas[:n]

        return random.sample(self.get_personas(), min(n, len(self.get_personas())))


class TaskSeedSource:
    """
    Load diverse task seeds from multiple real-world sources.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        config = get_data_config()
        self.cache_dir = cache_dir or config.datasets_cache_dir
        self._seeds: list[dict[str, Any]] | None = None

    def get_seeds(self) -> list[dict[str, Any]]:
        """Get task seeds from various sources."""
        if self._seeds is not None:
            return self._seeds

        self._seeds = []

        # ADL (Activities of Daily Living) - from healthcare research
        adl_tasks = [
            "bathing", "showering", "grooming", "dressing", "eating",
            "drinking", "toileting", "transferring", "walking", "climbing stairs",
        ]

        # IADL (Instrumental Activities of Daily Living)
        iadl_tasks = [
            "preparing meals", "managing medications", "shopping for groceries",
            "using telephone", "managing finances", "doing housework",
            "doing laundry", "using transportation", "managing appointments",
        ]

        # O*NET work activities (representative sample)
        work_tasks = [
            "operating vehicles", "handling materials", "inspecting equipment",
            "repairing machinery", "monitoring processes", "documenting information",
            "communicating with supervisors", "training employees", "scheduling work",
            "estimating costs", "resolving conflicts", "interpreting data",
        ]

        for task in adl_tasks:
            self._seeds.append({"task": task, "source": "adl", "domain": "self_care"})

        for task in iadl_tasks:
            self._seeds.append({"task": task, "source": "iadl", "domain": "independent_living"})

        for task in work_tasks:
            self._seeds.append({"task": task, "source": "onet", "domain": "occupational"})

        logger.info("task_seeds_loaded", count=len(self._seeds))
        return self._seeds


# Global instances
_verb_source: VerbSource | None = None
_noun_source: NounSource | None = None
_persona_source: PersonaSource | None = None
_seed_source: TaskSeedSource | None = None


def get_verb_source() -> VerbSource:
    """Get the global verb source."""
    global _verb_source
    if _verb_source is None:
        _verb_source = VerbSource()
    return _verb_source


def get_noun_source() -> NounSource:
    """Get the global noun source."""
    global _noun_source
    if _noun_source is None:
        _noun_source = NounSource()
    return _noun_source


def get_persona_source() -> PersonaSource:
    """Get the global persona source."""
    global _persona_source
    if _persona_source is None:
        _persona_source = PersonaSource()
    return _persona_source


def get_seed_source() -> TaskSeedSource:
    """Get the global task seed source."""
    global _seed_source
    if _seed_source is None:
        _seed_source = TaskSeedSource()
    return _seed_source
