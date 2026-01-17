# 🎯 NEW APPROACH: Value-First Task Curation

**Date**: 2026-01-17
**Pivot**: From quantity to quality - Focus on MARKETABLE tasks

## The Problem

The current dataset has **95.8% tasks in MEDIUM tier** - they need human judgment. Most tasks are not interesting or valuable from a robotics company's perspective.

**User feedback**: "It's a pain in the ass to go through this dataset because there's a lot of pointless shit."

## The Solution

**Stop generating more data. Start curating for VALUE.**

### New Focus: Robotics Company POV

When a robotics company (humanoids, bi-manual arms, mobile manipulators, grippers) reads this dataset, they should find tasks that:

1. **Make robots MARKETABLE** - Customers would pay for this capability
2. **Are technically IMPRESSIVE** - Spectators would be wowed
3. **Solve REAL problems** - Clear practical utility
4. **Demonstrate SOPHISTICATION** - Shows advanced capability
5. **Transfer to other tasks** - Generalizable skills

### Task Reading Hierarchy

Robotics companies will read the dataset like this:

```
Domain (e.g., Hospitality, Healthcare, Manufacturing)
  ↓
Task (e.g., "Make coffee", "Transfer patient", "Assemble component")
  ↓
Subtasks (detailed breakdown)
  ↓
Atomic actions (for training)
```

**Key insight**: They read at the **TASK level**, not atomic level. Tasks need to be impressive and valuable.

## Value Tiers

### ⭐ PREMIUM (Top 5%) - "Shut up and take my money"
**Examples**:
- Pick up broken glass (delicate + dangerous + common problem)
- Make coffee end-to-end (high demand + marketable)
- Fold laundry (huge market + technically challenging)
- Transfer patient safely (healthcare + high liability)
- Assemble electronic components (manufacturing ROI)

**Criteria**: Would make a KILLER demo video

### 🔥 HIGH (Top 20%) - Very valuable
**Examples**:
- Wash dishes
- Mop floor
- Stock shelves
- Sort packages
- Harvest crops

**Criteria**: Clear customer demand + practical utility

### 👍 MEDIUM - Useful but not exciting
**Examples**:
- Most tasks need manual review
- May be prerequisites for premium tasks
- Could be bundled into valuable workflows

### 👎 LOW - Marginal value
**Examples**:
- Tasks with limited market
- Very specialized/niche
- Low technical impressiveness

### 🗑️ TRASH - Delete these (2.8% currently)
**Examples**:
- Planning/scheduling tasks (not physical)
- Monitoring/logging (passive)
- Calibration/setup (robot internals)
- Documentation/reporting (administrative)

## Current Dataset Stats

```
Total: 24,189 tasks

PREMIUM:    201 tasks (0.9%)   - WOW factor
HIGH:       130 tasks (0.6%)   - Very valuable
MEDIUM:  22,322 tasks (95.8%)  - Needs review ⚠️
LOW:          0 tasks (0.0%)   - None yet
TRASH:      653 tasks (2.8%)   - DELETE
```

**Problem**: 95.8% need manual review to assess true value.

## New Tools

### 1. Value Review App (http://localhost:5003)

**Purpose**: Review tasks domain-by-domain from robotics company POV

**Features**:
- Shows tasks grouped by domain (Healthcare, Manufacturing, etc.)
- Each domain shows task count
- Click domain → see all tasks in that domain
- Rate each task: PREMIUM, HIGH, MEDIUM, LOW, or TRASH
- Progress tracking per domain
- Session stats

**Workflow**:
1. Open domain (e.g., "work_healthcare")
2. Read through tasks (e.g., "Transfer patient to wheelchair")
3. Ask: "Would a robotics company want to demo this?"
4. Rate it
5. Move to next task

### 2. Value Assessment (Python script)

**File**: `value_assessment.py`

**Purpose**: Automatically assess task value using patterns

**Output**:
- `value_assessment_report.txt` - Full report
- `tiered_datasets/` - JSON files split by tier
  - `premium_tasks.json`
  - `high_tasks.json`
  - `medium_tasks.json`
  - `trash_tasks.json`

## Examples of Premium Tasks

### From User: "Pick up broken glass"
- **Why valuable**: Dangerous, delicate, common household problem
- **Market**: Every home, every restaurant
- **Impressiveness**: High - shows precision + safety
- **Difficulty**: Medium-high - fragility + sharp edges

### Coffee Making
- **Why valuable**: Universal demand, high frequency
- **Market**: Offices, hotels, homes, cafes
- **Impressiveness**: Medium - but very relatable
- **Difficulty**: Medium - manipulation + sequencing

### Patient Transfer
- **Why valuable**: Healthcare staff shortage, high liability
- **Market**: Hospitals, nursing homes, home care
- **Impressiveness**: High - shows strength + gentleness
- **Difficulty**: High - safety critical

### Laundry Folding
- **Why valuable**: Time-consuming, everyone hates it
- **Market**: Massive consumer market
- **Impressiveness**: Very high - complex cloth manipulation
- **Difficulty**: High - deformable objects

## Next Steps

### Immediate (Now)

1. ✅ Run value assessment (`value_assessment.py`)
2. ✅ Review TRASH tier - confirm deletion
3. 🔄 **Use Value Review App** to rate tasks domain-by-domain
4. 🔄 Focus on finding 100-200 PREMIUM tasks first

### Short-term (This week)

1. Delete TRASH tasks from dataset
2. Curate top 100 PREMIUM tasks
3. Create "showcase" dataset of premium tasks only
4. Export premium tasks to HuggingFace as "Taskpedia-Premium"

### Mid-term (This month)

1. Review all HIGH tier tasks
2. Clean up MEDIUM tier - most will go to LOW or TRASH
3. Organize by customer personas:
   - **Home robots**: Cooking, cleaning, laundry
   - **Healthcare robots**: Patient care, medication, hygiene
   - **Warehouse robots**: Picking, sorting, inventory
   - **Manufacturing robots**: Assembly, inspection, packaging

### Long-term (Ongoing)

1. Add "difficulty score" for each task
2. Add "training data requirements" estimate
3. Create task bundles (e.g., "Barista skills", "Housekeeper skills")
4. Market analysis for each premium task

## Success Metrics

### Old Metrics (Quantity-focused)
- ❌ Total tasks generated
- ❌ API calls per minute
- ❌ Tasks per second

### New Metrics (Value-focused)
- ✅ Number of PREMIUM tasks identified
- ✅ Tasks rated by value tier
- ✅ Customer-facing task bundles created
- ✅ Tasks matched to robotics company needs

## Key Insight

> "A robotics company doesn't need 30,000 tasks. They need 100 KILLER tasks that make their robot marketable and impressive."

## Files

- `value_assessment.py` - Automatic value assessment
- `value_review_app.py` - Manual review interface (port 5003)
- `value_ratings.jsonl` - Your ratings
- `tiered_datasets/` - Dataset split by value tier
- `value_assessment_report.txt` - Full assessment report

## Usage

```bash
# Assess current dataset
python value_assessment.py

# Start review interface
python value_review_app.py
# Open http://localhost:5003

# Export final dataset
# (After rating tasks)
```

---

**Bottom line**: Focus on curation over generation. Quality over quantity. Find the tasks that make robots VALUABLE and IMPRESSIVE.
