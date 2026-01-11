"""
Comprehensive Human Activity Taxonomy.

This module defines the ROOT taxonomy of ALL human activities, synthesized from
authoritative sources covering both LIFE activities and WORK activities.

DATA SOURCES:
=============

1. O*NET Database (Work Activities)
   - 23 major occupation groups
   - 1,016 occupations
   - 18,796 task statements
   - 2,087 Detailed Work Activities (DWAs)
   - 332 Intermediate Work Activities (IWAs)
   Source: U.S. Department of Labor

2. American Time Use Survey (Life Activities)
   - 17 major activity categories
   - 424 detailed activity codes
   - Covers how Americans spend ALL their time
   Source: Bureau of Labor Statistics

3. ICF Activities and Participation (WHO)
   - Universal human capabilities
   - 9 activity domains
   Source: World Health Organization

4. ADL/IADL (Healthcare)
   - Activities of Daily Living
   - Instrumental Activities of Daily Living
   Source: Healthcare standards

TAXONOMY STRUCTURE:
==================

Level 0: Life Domain (WORK + NON-WORK)
    Level 1: Major Category (23 occupation groups + 16 life categories)
        Level 2: Subcategory/Occupation
            Level 3: Task/Activity
                Level 4: Subtask/Step
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# =============================================================================
# TOP-LEVEL LIFE DOMAINS
# =============================================================================


class LifeDomain(str, Enum):
    """
    Top-level life domains covering ALL human activities.

    Split into WORK (professional/occupational) and LIFE (personal/domestic).
    """

    # === WORK DOMAINS (from O*NET SOC Major Groups) ===
    WORK_MANAGEMENT = "work_management"
    WORK_BUSINESS_FINANCIAL = "work_business_financial"
    WORK_COMPUTER_MATHEMATICAL = "work_computer_mathematical"
    WORK_ARCHITECTURE_ENGINEERING = "work_architecture_engineering"
    WORK_SCIENCE = "work_science"
    WORK_COMMUNITY_SOCIAL = "work_community_social"
    WORK_LEGAL = "work_legal"
    WORK_EDUCATION = "work_education"
    WORK_ARTS_MEDIA = "work_arts_media"
    WORK_HEALTHCARE_PRACTITIONERS = "work_healthcare_practitioners"
    WORK_HEALTHCARE_SUPPORT = "work_healthcare_support"
    WORK_PROTECTIVE_SERVICE = "work_protective_service"
    WORK_FOOD_SERVICE = "work_food_service"
    WORK_BUILDING_GROUNDS = "work_building_grounds"
    WORK_PERSONAL_SERVICE = "work_personal_service"
    WORK_SALES = "work_sales"
    WORK_OFFICE_ADMIN = "work_office_admin"
    WORK_FARMING_FISHING = "work_farming_fishing"
    WORK_CONSTRUCTION = "work_construction"
    WORK_INSTALLATION_REPAIR = "work_installation_repair"
    WORK_PRODUCTION = "work_production"
    WORK_TRANSPORTATION = "work_transportation"
    WORK_MILITARY = "work_military"

    # === LIFE DOMAINS (from ATUS) ===
    LIFE_PERSONAL_CARE = "life_personal_care"
    LIFE_HOUSEHOLD = "life_household"
    LIFE_CAREGIVING = "life_caregiving"
    LIFE_CONSUMER = "life_consumer"
    LIFE_EDUCATION_PERSONAL = "life_education_personal"
    LIFE_CIVIC_RELIGIOUS = "life_civic_religious"
    LIFE_VOLUNTEER = "life_volunteer"
    LIFE_SOCIAL_LEISURE = "life_social_leisure"
    LIFE_SPORTS_EXERCISE = "life_sports_exercise"
    LIFE_ARTS_ENTERTAINMENT = "life_arts_entertainment"
    LIFE_TRAVEL = "life_travel"
    LIFE_HEALTHCARE_PERSONAL = "life_healthcare_personal"


# Mapping from O*NET SOC major group codes to LifeDomain
SOC_TO_DOMAIN = {
    "11": LifeDomain.WORK_MANAGEMENT,
    "13": LifeDomain.WORK_BUSINESS_FINANCIAL,
    "15": LifeDomain.WORK_COMPUTER_MATHEMATICAL,
    "17": LifeDomain.WORK_ARCHITECTURE_ENGINEERING,
    "19": LifeDomain.WORK_SCIENCE,
    "21": LifeDomain.WORK_COMMUNITY_SOCIAL,
    "23": LifeDomain.WORK_LEGAL,
    "25": LifeDomain.WORK_EDUCATION,
    "27": LifeDomain.WORK_ARTS_MEDIA,
    "29": LifeDomain.WORK_HEALTHCARE_PRACTITIONERS,
    "31": LifeDomain.WORK_HEALTHCARE_SUPPORT,
    "33": LifeDomain.WORK_PROTECTIVE_SERVICE,
    "35": LifeDomain.WORK_FOOD_SERVICE,
    "37": LifeDomain.WORK_BUILDING_GROUNDS,
    "39": LifeDomain.WORK_PERSONAL_SERVICE,
    "41": LifeDomain.WORK_SALES,
    "43": LifeDomain.WORK_OFFICE_ADMIN,
    "45": LifeDomain.WORK_FARMING_FISHING,
    "47": LifeDomain.WORK_CONSTRUCTION,
    "49": LifeDomain.WORK_INSTALLATION_REPAIR,
    "51": LifeDomain.WORK_PRODUCTION,
    "53": LifeDomain.WORK_TRANSPORTATION,
    "55": LifeDomain.WORK_MILITARY,
}


# Human-readable names for domains
DOMAIN_NAMES = {
    # Work domains
    LifeDomain.WORK_MANAGEMENT: "Management Occupations",
    LifeDomain.WORK_BUSINESS_FINANCIAL: "Business and Financial Operations",
    LifeDomain.WORK_COMPUTER_MATHEMATICAL: "Computer and Mathematical Occupations",
    LifeDomain.WORK_ARCHITECTURE_ENGINEERING: "Architecture and Engineering",
    LifeDomain.WORK_SCIENCE: "Life, Physical, and Social Science",
    LifeDomain.WORK_COMMUNITY_SOCIAL: "Community and Social Service",
    LifeDomain.WORK_LEGAL: "Legal Occupations",
    LifeDomain.WORK_EDUCATION: "Educational Instruction and Library",
    LifeDomain.WORK_ARTS_MEDIA: "Arts, Design, Entertainment, Sports, and Media",
    LifeDomain.WORK_HEALTHCARE_PRACTITIONERS: "Healthcare Practitioners and Technical",
    LifeDomain.WORK_HEALTHCARE_SUPPORT: "Healthcare Support",
    LifeDomain.WORK_PROTECTIVE_SERVICE: "Protective Service",
    LifeDomain.WORK_FOOD_SERVICE: "Food Preparation and Serving",
    LifeDomain.WORK_BUILDING_GROUNDS: "Building and Grounds Cleaning and Maintenance",
    LifeDomain.WORK_PERSONAL_SERVICE: "Personal Care and Service",
    LifeDomain.WORK_SALES: "Sales and Related",
    LifeDomain.WORK_OFFICE_ADMIN: "Office and Administrative Support",
    LifeDomain.WORK_FARMING_FISHING: "Farming, Fishing, and Forestry",
    LifeDomain.WORK_CONSTRUCTION: "Construction and Extraction",
    LifeDomain.WORK_INSTALLATION_REPAIR: "Installation, Maintenance, and Repair",
    LifeDomain.WORK_PRODUCTION: "Production",
    LifeDomain.WORK_TRANSPORTATION: "Transportation and Material Moving",
    LifeDomain.WORK_MILITARY: "Military Specific",
    # Life domains
    LifeDomain.LIFE_PERSONAL_CARE: "Personal Care Activities",
    LifeDomain.LIFE_HOUSEHOLD: "Household Activities",
    LifeDomain.LIFE_CAREGIVING: "Caring for Others",
    LifeDomain.LIFE_CONSUMER: "Consumer Activities",
    LifeDomain.LIFE_EDUCATION_PERSONAL: "Personal Education",
    LifeDomain.LIFE_CIVIC_RELIGIOUS: "Civic and Religious Activities",
    LifeDomain.LIFE_VOLUNTEER: "Volunteer Activities",
    LifeDomain.LIFE_SOCIAL_LEISURE: "Socializing and Leisure",
    LifeDomain.LIFE_SPORTS_EXERCISE: "Sports and Exercise",
    LifeDomain.LIFE_ARTS_ENTERTAINMENT: "Arts and Entertainment",
    LifeDomain.LIFE_TRAVEL: "Travel and Commuting",
    LifeDomain.LIFE_HEALTHCARE_PERSONAL: "Personal Healthcare",
}


def is_work_domain(domain: LifeDomain) -> bool:
    """Check if a domain is work-related."""
    return domain.value.startswith("work_")


def is_life_domain(domain: LifeDomain) -> bool:
    """Check if a domain is life/personal-related."""
    return domain.value.startswith("life_")


def get_domain_name(domain: LifeDomain) -> str:
    """Get human-readable name for a domain."""
    return DOMAIN_NAMES.get(domain, domain.value)


# =============================================================================
# LIFE ACTIVITIES (ATUS-based)
# =============================================================================


@dataclass
class ActivityCategory:
    """A category of activities within a life domain."""

    code: str
    name: str
    domain: LifeDomain
    description: str = ""
    example_tasks: list[str] = field(default_factory=list)


# Life domain activities organized by ATUS categories
LIFE_ACTIVITIES: dict[LifeDomain, list[ActivityCategory]] = {
    LifeDomain.LIFE_PERSONAL_CARE: [
        ActivityCategory(
            code="PC01",
            name="Sleeping",
            domain=LifeDomain.LIFE_PERSONAL_CARE,
            description="Sleep and rest activities",
            example_tasks=["going to sleep", "napping", "resting in bed", "waking up"],
        ),
        ActivityCategory(
            code="PC02",
            name="Grooming and Hygiene",
            domain=LifeDomain.LIFE_PERSONAL_CARE,
            description="Personal hygiene and appearance",
            example_tasks=[
                "showering",
                "bathing",
                "brushing teeth",
                "flossing",
                "washing face",
                "washing hands",
                "shaving",
                "applying deodorant",
                "styling hair",
                "drying hair",
                "applying makeup",
                "removing makeup",
                "trimming nails",
                "filing nails",
                "applying lotion",
                "getting dressed",
                "undressing",
                "choosing outfit",
            ],
        ),
        ActivityCategory(
            code="PC03",
            name="Health Self-Care",
            domain=LifeDomain.LIFE_PERSONAL_CARE,
            description="Self-administered health activities",
            example_tasks=[
                "taking medication",
                "taking vitamins",
                "checking blood pressure",
                "checking blood sugar",
                "applying bandages",
                "wound care",
                "using inhaler",
                "using CPAP machine",
                "physical therapy exercises",
                "stretching",
                "meditation",
                "relaxation exercises",
            ],
        ),
        ActivityCategory(
            code="PC04",
            name="Eating and Drinking",
            domain=LifeDomain.LIFE_PERSONAL_CARE,
            description="Consuming food and beverages",
            example_tasks=[
                "eating breakfast",
                "eating lunch",
                "eating dinner",
                "snacking",
                "drinking water",
                "drinking coffee",
                "drinking tea",
            ],
        ),
    ],
    LifeDomain.LIFE_HOUSEHOLD: [
        ActivityCategory(
            code="HH01",
            name="Housework",
            domain=LifeDomain.LIFE_HOUSEHOLD,
            description="Cleaning and maintaining the home interior",
            example_tasks=[
                "vacuuming floors",
                "mopping floors",
                "sweeping floors",
                "dusting furniture",
                "dusting surfaces",
                "cleaning mirrors",
                "cleaning windows",
                "cleaning bathrooms",
                "scrubbing toilet",
                "cleaning shower",
                "cleaning sink",
                "cleaning kitchen",
                "washing dishes",
                "loading dishwasher",
                "unloading dishwasher",
                "wiping counters",
                "cleaning stovetop",
                "cleaning oven",
                "cleaning refrigerator",
                "taking out trash",
                "recycling",
                "making bed",
                "changing sheets",
                "fluffing pillows",
                "organizing closet",
                "decluttering",
                "tidying room",
            ],
        ),
        ActivityCategory(
            code="HH02",
            name="Food Preparation",
            domain=LifeDomain.LIFE_HOUSEHOLD,
            description="Preparing meals and food",
            example_tasks=[
                "planning meals",
                "writing grocery list",
                "checking pantry",
                "washing vegetables",
                "peeling vegetables",
                "chopping vegetables",
                "slicing fruit",
                "measuring ingredients",
                "mixing ingredients",
                "boiling water",
                "boiling pasta",
                "steaming vegetables",
                "frying eggs",
                "scrambling eggs",
                "making omelet",
                "grilling meat",
                "baking chicken",
                "roasting vegetables",
                "making sandwich",
                "making salad",
                "making soup",
                "brewing coffee",
                "making tea",
                "blending smoothie",
                "setting table",
                "serving food",
                "plating food",
                "storing leftovers",
                "wrapping food",
                "refrigerating food",
            ],
        ),
        ActivityCategory(
            code="HH03",
            name="Laundry",
            domain=LifeDomain.LIFE_HOUSEHOLD,
            description="Washing and managing clothes",
            example_tasks=[
                "sorting laundry",
                "checking pockets",
                "pretreating stains",
                "loading washing machine",
                "adding detergent",
                "starting washer",
                "transferring to dryer",
                "hanging clothes to dry",
                "folding laundry",
                "hanging clothes",
                "ironing clothes",
                "steaming clothes",
                "putting away clothes",
            ],
        ),
        ActivityCategory(
            code="HH04",
            name="Lawn and Garden",
            domain=LifeDomain.LIFE_HOUSEHOLD,
            description="Outdoor property maintenance",
            example_tasks=[
                "mowing lawn",
                "edging lawn",
                "raking leaves",
                "bagging leaves",
                "pulling weeds",
                "applying mulch",
                "watering plants",
                "watering lawn",
                "fertilizing lawn",
                "planting flowers",
                "planting vegetables",
                "pruning bushes",
                "trimming hedges",
                "trimming trees",
                "sweeping patio",
                "cleaning gutters",
                "shoveling snow",
                "salting walkway",
            ],
        ),
        ActivityCategory(
            code="HH05",
            name="Pet Care",
            domain=LifeDomain.LIFE_HOUSEHOLD,
            description="Caring for household pets",
            example_tasks=[
                "feeding pet",
                "filling water bowl",
                "walking dog",
                "letting dog out",
                "cleaning litter box",
                "cleaning cage",
                "grooming pet",
                "brushing pet",
                "bathing pet",
                "giving pet medication",
                "playing with pet",
                "training pet",
            ],
        ),
        ActivityCategory(
            code="HH06",
            name="Home Maintenance",
            domain=LifeDomain.LIFE_HOUSEHOLD,
            description="Fixing and maintaining the home",
            example_tasks=[
                "changing light bulb",
                "replacing batteries",
                "unclogging drain",
                "plunging toilet",
                "fixing leaky faucet",
                "tightening screws",
                "hanging picture",
                "patching wall",
                "painting wall",
                "caulking",
                "weatherstripping",
                "replacing air filter",
                "checking smoke detector",
                "resetting circuit breaker",
                "adjusting thermostat",
            ],
        ),
        ActivityCategory(
            code="HH07",
            name="Vehicle Care",
            domain=LifeDomain.LIFE_HOUSEHOLD,
            description="Maintaining personal vehicles",
            example_tasks=[
                "washing car",
                "vacuuming car interior",
                "wiping dashboard",
                "filling gas tank",
                "checking tire pressure",
                "adding air to tires",
                "checking oil level",
                "adding windshield fluid",
                "scraping ice",
                "defrosting windshield",
            ],
        ),
        ActivityCategory(
            code="HH08",
            name="Household Management",
            domain=LifeDomain.LIFE_HOUSEHOLD,
            description="Planning and organizing household",
            example_tasks=[
                "paying bills",
                "reviewing bank statement",
                "budgeting",
                "scheduling appointments",
                "managing calendar",
                "organizing paperwork",
                "filing documents",
                "shredding documents",
                "inventory pantry",
                "planning weekly meals",
            ],
        ),
    ],
    LifeDomain.LIFE_CAREGIVING: [
        ActivityCategory(
            code="CG01",
            name="Childcare - Physical",
            domain=LifeDomain.LIFE_CAREGIVING,
            description="Physical care of children",
            example_tasks=[
                "feeding baby",
                "bottle feeding",
                "breastfeeding",
                "burping baby",
                "changing diaper",
                "bathing child",
                "dressing child",
                "brushing child's teeth",
                "combing child's hair",
                "putting child to bed",
                "getting child up",
                "carrying child",
                "holding child",
                "rocking child",
                "comforting child",
            ],
        ),
        ActivityCategory(
            code="CG02",
            name="Childcare - Supervision",
            domain=LifeDomain.LIFE_CAREGIVING,
            description="Supervising and guiding children",
            example_tasks=[
                "watching children play",
                "supervising outdoor play",
                "monitoring screen time",
                "enforcing rules",
                "disciplining",
                "resolving conflicts",
                "mediating sibling disputes",
            ],
        ),
        ActivityCategory(
            code="CG03",
            name="Childcare - Educational",
            domain=LifeDomain.LIFE_CAREGIVING,
            description="Educational activities with children",
            example_tasks=[
                "reading to child",
                "helping with homework",
                "teaching letters",
                "teaching numbers",
                "practicing reading",
                "reviewing schoolwork",
                "attending parent-teacher conference",
                "school pickup",
                "school dropoff",
                "packing school lunch",
                "signing permission slips",
            ],
        ),
        ActivityCategory(
            code="CG04",
            name="Childcare - Activities",
            domain=LifeDomain.LIFE_CAREGIVING,
            description="Recreational activities with children",
            example_tasks=[
                "playing games",
                "playing with toys",
                "arts and crafts",
                "going to playground",
                "taking to park",
                "attending sports practice",
                "attending recital",
                "hosting playdate",
                "birthday party",
            ],
        ),
        ActivityCategory(
            code="CG05",
            name="Eldercare",
            domain=LifeDomain.LIFE_CAREGIVING,
            description="Caring for elderly family members",
            example_tasks=[
                "helping with bathing",
                "helping with dressing",
                "preparing meals for elder",
                "feeding assistance",
                "medication management",
                "accompanying to doctor",
                "mobility assistance",
                "transferring from bed",
                "companionship",
                "checking on elder",
            ],
        ),
    ],
    LifeDomain.LIFE_CONSUMER: [
        ActivityCategory(
            code="CS01",
            name="Grocery Shopping",
            domain=LifeDomain.LIFE_CONSUMER,
            description="Purchasing food and household supplies",
            example_tasks=[
                "making shopping list",
                "clipping coupons",
                "checking sales",
                "driving to store",
                "getting shopping cart",
                "selecting produce",
                "comparing prices",
                "checking expiration dates",
                "bagging groceries",
                "loading car",
                "unloading groceries",
                "putting away groceries",
            ],
        ),
        ActivityCategory(
            code="CS02",
            name="General Shopping",
            domain=LifeDomain.LIFE_CONSUMER,
            description="Purchasing goods and services",
            example_tasks=[
                "clothes shopping",
                "trying on clothes",
                "shoe shopping",
                "furniture shopping",
                "electronics shopping",
                "appliance shopping",
                "returning items",
                "exchanging items",
                "online shopping",
                "comparing products",
                "reading reviews",
            ],
        ),
        ActivityCategory(
            code="CS03",
            name="Financial Services",
            domain=LifeDomain.LIFE_CONSUMER,
            description="Banking and financial transactions",
            example_tasks=[
                "visiting bank",
                "depositing check",
                "withdrawing cash",
                "using ATM",
                "transferring money",
                "paying bills online",
                "meeting with financial advisor",
                "reviewing investments",
                "applying for loan",
                "insurance paperwork",
            ],
        ),
        ActivityCategory(
            code="CS04",
            name="Personal Services",
            domain=LifeDomain.LIFE_CONSUMER,
            description="Obtaining personal services",
            example_tasks=[
                "haircut appointment",
                "hair coloring",
                "manicure",
                "pedicure",
                "spa visit",
                "massage appointment",
                "dry cleaning dropoff",
                "dry cleaning pickup",
                "tailoring",
                "shoe repair",
            ],
        ),
    ],
    LifeDomain.LIFE_EDUCATION_PERSONAL: [
        ActivityCategory(
            code="ED01",
            name="Formal Education",
            domain=LifeDomain.LIFE_EDUCATION_PERSONAL,
            description="Attending educational institutions",
            example_tasks=[
                "attending class",
                "attending lecture",
                "taking notes",
                "participating in discussion",
                "laboratory work",
                "studying",
                "reading textbook",
                "writing paper",
                "doing homework",
                "preparing for exam",
                "taking exam",
                "group project work",
                "meeting with professor",
            ],
        ),
        ActivityCategory(
            code="ED02",
            name="Self-Education",
            domain=LifeDomain.LIFE_EDUCATION_PERSONAL,
            description="Self-directed learning",
            example_tasks=[
                "reading non-fiction",
                "watching educational video",
                "online course",
                "tutorial",
                "practicing new skill",
                "language learning",
                "musical instrument practice",
            ],
        ),
    ],
    LifeDomain.LIFE_CIVIC_RELIGIOUS: [
        ActivityCategory(
            code="CR01",
            name="Religious Activities",
            domain=LifeDomain.LIFE_CIVIC_RELIGIOUS,
            description="Religious and spiritual practices",
            example_tasks=[
                "attending religious service",
                "praying",
                "meditating",
                "reading religious text",
                "religious education",
                "religious ceremony",
                "religious holiday observance",
            ],
        ),
        ActivityCategory(
            code="CR02",
            name="Civic Activities",
            domain=LifeDomain.LIFE_CIVIC_RELIGIOUS,
            description="Civic participation",
            example_tasks=[
                "voting",
                "registering to vote",
                "jury duty",
                "attending town hall",
                "community meeting",
                "political volunteering",
                "signing petition",
            ],
        ),
    ],
    LifeDomain.LIFE_VOLUNTEER: [
        ActivityCategory(
            code="VL01",
            name="Community Volunteering",
            domain=LifeDomain.LIFE_VOLUNTEER,
            description="Volunteer work for organizations",
            example_tasks=[
                "food bank volunteering",
                "soup kitchen serving",
                "homeless shelter volunteering",
                "hospital volunteering",
                "animal shelter volunteering",
                "mentoring",
                "tutoring",
                "coaching youth sports",
                "fundraising",
                "charity event organizing",
            ],
        ),
    ],
    LifeDomain.LIFE_SOCIAL_LEISURE: [
        ActivityCategory(
            code="SL01",
            name="Socializing",
            domain=LifeDomain.LIFE_SOCIAL_LEISURE,
            description="Social interactions",
            example_tasks=[
                "visiting friends",
                "having guests over",
                "hosting dinner party",
                "going to party",
                "family gathering",
                "reunion",
                "coffee with friend",
                "lunch date",
                "dinner out",
                "phone call with friend",
                "video call with family",
            ],
        ),
        ActivityCategory(
            code="SL02",
            name="Relaxing",
            domain=LifeDomain.LIFE_SOCIAL_LEISURE,
            description="Relaxation activities",
            example_tasks=[
                "watching TV",
                "streaming shows",
                "watching movie",
                "listening to music",
                "listening to podcast",
                "reading for pleasure",
                "browsing internet",
                "social media",
                "playing video games",
                "napping",
            ],
        ),
        ActivityCategory(
            code="SL03",
            name="Hobbies",
            domain=LifeDomain.LIFE_SOCIAL_LEISURE,
            description="Personal hobby activities",
            example_tasks=[
                "knitting",
                "crocheting",
                "sewing",
                "quilting",
                "woodworking",
                "model building",
                "collecting",
                "gardening for pleasure",
                "birdwatching",
                "photography",
                "scrapbooking",
                "journaling",
                "puzzles",
                "crosswords",
            ],
        ),
    ],
    LifeDomain.LIFE_SPORTS_EXERCISE: [
        ActivityCategory(
            code="SE01",
            name="Exercise",
            domain=LifeDomain.LIFE_SPORTS_EXERCISE,
            description="Physical fitness activities",
            example_tasks=[
                "walking for exercise",
                "jogging",
                "running",
                "cycling",
                "swimming",
                "weight lifting",
                "yoga",
                "pilates",
                "aerobics",
                "dance fitness",
                "stretching",
                "warm up",
                "cool down",
                "gym workout",
                "home workout",
            ],
        ),
        ActivityCategory(
            code="SE02",
            name="Sports",
            domain=LifeDomain.LIFE_SPORTS_EXERCISE,
            description="Participating in sports",
            example_tasks=[
                "playing basketball",
                "playing tennis",
                "playing golf",
                "playing soccer",
                "playing baseball",
                "playing volleyball",
                "playing pickleball",
                "bowling",
                "skiing",
                "snowboarding",
            ],
        ),
        ActivityCategory(
            code="SE03",
            name="Outdoor Recreation",
            domain=LifeDomain.LIFE_SPORTS_EXERCISE,
            description="Outdoor recreational activities",
            example_tasks=[
                "hiking",
                "camping",
                "fishing",
                "hunting",
                "boating",
                "kayaking",
                "canoeing",
                "sailing",
                "rock climbing",
                "mountain biking",
            ],
        ),
    ],
    LifeDomain.LIFE_ARTS_ENTERTAINMENT: [
        ActivityCategory(
            code="AE01",
            name="Creating Art",
            domain=LifeDomain.LIFE_ARTS_ENTERTAINMENT,
            description="Artistic creation",
            example_tasks=[
                "painting",
                "drawing",
                "sketching",
                "sculpting",
                "pottery",
                "ceramics",
                "digital art",
                "playing musical instrument",
                "singing",
                "songwriting",
                "creative writing",
                "poetry",
                "dancing",
            ],
        ),
        ActivityCategory(
            code="AE02",
            name="Attending Events",
            domain=LifeDomain.LIFE_ARTS_ENTERTAINMENT,
            description="Attending entertainment events",
            example_tasks=[
                "going to movies",
                "attending concert",
                "attending theater",
                "visiting museum",
                "visiting art gallery",
                "attending festival",
                "attending sporting event",
                "attending comedy show",
            ],
        ),
    ],
    LifeDomain.LIFE_TRAVEL: [
        ActivityCategory(
            code="TR01",
            name="Commuting",
            domain=LifeDomain.LIFE_TRAVEL,
            description="Travel to and from work",
            example_tasks=[
                "driving to work",
                "taking bus",
                "taking subway",
                "taking train",
                "carpooling",
                "walking to work",
                "cycling to work",
                "waiting for bus",
                "transferring trains",
            ],
        ),
        ActivityCategory(
            code="TR02",
            name="Errands Travel",
            domain=LifeDomain.LIFE_TRAVEL,
            description="Travel for errands and appointments",
            example_tasks=[
                "driving to store",
                "driving to appointment",
                "school pickup",
                "school dropoff",
                "driving kids to activities",
                "parking",
            ],
        ),
        ActivityCategory(
            code="TR03",
            name="Vacation Travel",
            domain=LifeDomain.LIFE_TRAVEL,
            description="Leisure and vacation travel",
            example_tasks=[
                "packing luggage",
                "airport security",
                "boarding plane",
                "flying",
                "renting car",
                "checking into hotel",
                "road trip driving",
                "sightseeing",
                "navigating",
            ],
        ),
    ],
    LifeDomain.LIFE_HEALTHCARE_PERSONAL: [
        ActivityCategory(
            code="HC01",
            name="Medical Appointments",
            domain=LifeDomain.LIFE_HEALTHCARE_PERSONAL,
            description="Receiving medical care",
            example_tasks=[
                "doctor appointment",
                "specialist visit",
                "annual checkup",
                "getting blood drawn",
                "getting X-ray",
                "getting MRI",
                "receiving vaccination",
                "physical therapy session",
                "emergency room visit",
                "urgent care visit",
            ],
        ),
        ActivityCategory(
            code="HC02",
            name="Dental Care",
            domain=LifeDomain.LIFE_HEALTHCARE_PERSONAL,
            description="Dental appointments",
            example_tasks=[
                "dental checkup",
                "teeth cleaning",
                "filling cavity",
                "root canal",
                "tooth extraction",
                "orthodontist visit",
            ],
        ),
        ActivityCategory(
            code="HC03",
            name="Mental Health",
            domain=LifeDomain.LIFE_HEALTHCARE_PERSONAL,
            description="Mental health care",
            example_tasks=[
                "therapy session",
                "psychiatrist appointment",
                "counseling",
                "support group",
            ],
        ),
        ActivityCategory(
            code="HC04",
            name="Pharmacy",
            domain=LifeDomain.LIFE_HEALTHCARE_PERSONAL,
            description="Obtaining medications",
            example_tasks=[
                "picking up prescription",
                "dropping off prescription",
                "consulting pharmacist",
                "buying over-the-counter medicine",
            ],
        ),
    ],
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_all_domains() -> list[LifeDomain]:
    """Get all life domains."""
    return list(LifeDomain)


def get_work_domains() -> list[LifeDomain]:
    """Get only work-related domains."""
    return [d for d in LifeDomain if is_work_domain(d)]


def get_life_domains() -> list[LifeDomain]:
    """Get only life/personal domains."""
    return [d for d in LifeDomain if is_life_domain(d)]


def get_categories_for_domain(domain: LifeDomain) -> list[ActivityCategory]:
    """Get activity categories for a life domain."""
    return LIFE_ACTIVITIES.get(domain, [])


def get_all_life_tasks() -> list[str]:
    """Get all example tasks from life activities."""
    tasks = []
    for domain_categories in LIFE_ACTIVITIES.values():
        for category in domain_categories:
            tasks.extend(category.example_tasks)
    return tasks


def count_life_tasks() -> int:
    """Count total life activity tasks."""
    return len(get_all_life_tasks())


def print_taxonomy_summary() -> None:
    """Print a summary of the taxonomy."""
    print("=" * 70)
    print("PRAXIS TASK TAXONOMY")
    print("=" * 70)

    work_domains = get_work_domains()
    life_domains = get_life_domains()

    print(f"\nWORK DOMAINS: {len(work_domains)}")
    print("-" * 40)
    for d in work_domains:
        print(f"  [{d.value}] {get_domain_name(d)}")

    print(f"\nLIFE DOMAINS: {len(life_domains)}")
    print("-" * 40)
    for d in life_domains:
        cats = get_categories_for_domain(d)
        task_count = sum(len(c.example_tasks) for c in cats)
        print(f"  [{d.value}] {get_domain_name(d)}")
        print(f"      {len(cats)} categories, {task_count} example tasks")

    print()
    print(f"Total domains: {len(LifeDomain)}")
    print(f"Total life example tasks: {count_life_tasks()}")
    print("(Work tasks come from O*NET: 18,796 task statements)")
