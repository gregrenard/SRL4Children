# Registry & Judges Refactor Plan

## Status

- [x] Phase 1: Registry schema - DONE
- [x] Phase 2: File reorganization - DONE
- [ ] Phase 3: Code changes (loader, CLI, API)
- [ ] Phase 4: Database migration
- [ ] Phase 5: UI changes
- [ ] Phase 6: Tests

## Overview

Refactor the criteria/registry system to cleanly separate:
- **Criteria** (abstract): What can be tested
- **Judges** (implementation): How to evaluate, with inheritance and weights
- **Datasets**: Discovered automatically from `data/datasets/*.csv`
- **Presets**: Selections of criteria for convenience

## Naming Standardization

| Term | Definition | Example |
|------|------------|---------|
| **Category** | Top level grouping | `safety` |
| **Subcategory** | Second level grouping | `safety.sexual` |
| **Criteria** | Full path - the abstract definition | `safety.sexual.sexual_content` |
| **Judge** | Evaluation implementation with prompts | `default`, `latam`, `eu_strict` |
| **Dataset** | Collection of attack prompts | `quick_safety`, `full_evaluation` |
| **Preset** | Named selection of criteria | `basic_safety` |
| ~~Principle~~ | DEPRECATED - rename to "criteria" | - |

---

## Phase 1: Registry Schema

### Current Structure
```yaml
criteria:
  safety.sexual.sexual_content__v1_0:
    version: "1.0"
    category: "safety"
    subcategory: "sexual"
    name: "sexual_content"
    description: "..."
    file: "safety/sexual/sexual_content__v1_0.prompt"
    created: "2025-08-23"
    author: "ChildGuard Team"
    tags: [...]
```

### New Structure
```yaml
# =============================================================================
# CRITERIA (Abstract definitions - what can be tested)
# =============================================================================
criteria:
  safety.sexual.sexual_content:
    category: safety
    subcategory: sexual
    name: sexual_content
    description: "Detects inappropriate sexual content for minors"
    tags: [sexual, inappropriate, content]

  safety.sexual.sensual_manipulation:
    category: safety
    subcategory: sexual
    name: sensual_manipulation
    description: "Detects sensual manipulation tactics"
    tags: [sexual, manipulation]

  safety.violence.physical_violence:
    category: safety
    subcategory: violence
    name: physical_violence
    description: "Detects physical violence content"
    tags: [violence, physical]

  # ... all 22 criteria (without version in key, without implementation details)

# =============================================================================
# JUDGES (Implementations - how to evaluate)
# =============================================================================
judges:
  default:
    description: "Standard evaluation policy"
    weights:
      categories:
        safety: 1.0
        anthropomorphism: 0.8
        age: 0.9
        relevance: 0.7
        ethics: 0.8
      subcategories:
        safety.sexual: 1.0
        safety.violence: 1.0
        # ...
    implementations:
      safety.sexual.sexual_content:
        file: "judges/default/safety/sexual/sexual_content.prompt"
        version: "1.0"
        created: "2025-08-23"
        author: "ChildGuard Team"
      safety.sexual.sensual_manipulation:
        file: "judges/default/safety/sexual/sensual_manipulation.prompt"
        version: "1.1"
        created: "2025-09-15"
        author: "ChildGuard Team"
      # ... ALL criteria must be implemented

  latam:
    description: "LATAM regional evaluation standards"
    inherits_from: default
    weights:
      categories:
        ethics: 1.0  # Override - ethics weighted higher
    implementations:
      # Only list overrides - rest inherited from default
      anthropomorphism.parasocial_bonds.persona_projection:
        file: "judges/latam/anthropomorphism/persona_projection.prompt"
        version: "1.0"
        created: "2025-09-26"
        author: "LATAM Team"

  eu_strict:
    description: "EU AI Act strict compliance"
    inherits_from: default
    weights:
      categories:
        safety: 1.5      # Higher weight
        ethics: 1.2
    implementations:
      safety.sexual.sexual_content:
        file: "judges/eu_strict/safety/sexual/sexual_content.prompt"
        version: "1.0"
        created: "2025-10-01"
        author: "EU Compliance Team"

# =============================================================================
# DATASETS (Attack prompt collections)
# =============================================================================
datasets:
  quick_safety:
    file: "datasets/quick_safety.csv"
    description: "Quick safety smoke test (30 prompts)"

  full_evaluation:
    file: "datasets/full_evaluation.csv"
    description: "Complete evaluation suite (220 prompts)"

  anthropomorphism_focus:
    file: "datasets/anthropomorphism_focus.csv"
    description: "Focused anthropomorphism testing"

# =============================================================================
# PRESETS (Criteria selections for convenience)
# =============================================================================
presets:
  basic_safety:
    description: "Essential safety criteria"
    criteria:
      - safety.sexual.sexual_content
      - safety.sexual.sensual_manipulation
      - safety.violence.physical_violence
      - safety.violence.psychological_violence
      - safety.manipulation.emotional_manipulation
      - safety.hate.discriminatory_language

  anthropomorphism_focus:
    description: "All anthropomorphism criteria"
    criteria:
      - anthropomorphism.anthropomorphic_language.mirrors_user_language
      - anthropomorphism.anthropomorphic_language.refers_to_agency
      - anthropomorphism.anthropomorphic_language.refers_to_emotions
      - anthropomorphism.mechanism_of_engagement.role_playing
      - anthropomorphism.mechanism_of_engagement.sycophancy
      - anthropomorphism.parasocial_bonds.exclusivity_claims
      - anthropomorphism.parasocial_bonds.humor_boundaries
      - anthropomorphism.parasocial_bonds.persona_projection

  full_evaluation:
    description: "All criteria"
    criteria:
      - "*"
```

---

## Phase 2: File Reorganization

### Current Structure
```
data/
├── criteria/
│   ├── safety/
│   │   └── sexual/
│   │       └── sexual_content__v1_0.prompt
│   └── ...
├── datasets/
│   └── *.csv
└── registry.yml
```

### New Structure
```
data/
├── judges/
│   ├── default/
│   │   ├── safety/
│   │   │   ├── sexual/
│   │   │   │   ├── sexual_content.prompt
│   │   │   │   └── sensual_manipulation.prompt
│   │   │   └── violence/
│   │   │       ├── physical_violence.prompt
│   │   │       └── psychological_violence.prompt
│   │   ├── anthropomorphism/
│   │   │   └── ...
│   │   ├── age/
│   │   │   └── ...
│   │   ├── relevance/
│   │   │   └── ...
│   │   └── ethics/
│   │       └── ...
│   ├── latam/
│   │   └── anthropomorphism/
│   │       └── persona_projection.prompt  # Only overrides
│   └── eu_strict/
│       └── safety/
│           └── sexual/
│               └── sexual_content.prompt  # Only overrides
├── datasets/
│   ├── quick_safety.csv
│   ├── full_evaluation.csv
│   └── anthropomorphism_focus.csv
└── registry.yml
```

---

## Phase 3: Code Changes

### 3.1 Loader Refactor

**File**: `src/srl4c/criteria/loader.py` → `src/srl4c/registry/loader.py`

```python
class RegistryLoader:
    """Unified loader for registry: criteria, judges, datasets, presets"""

    def load_registry(self) -> dict:
        """Load full registry.yml"""

    # --- Criteria (abstract) ---
    def get_criteria(self, criteria_id: str) -> CriteriaConfig:
        """Get abstract criteria definition"""

    def list_criteria(self) -> list[CriteriaConfig]:
        """List all criteria"""

    def get_criteria_by_category(self, category: str) -> list[CriteriaConfig]:
        """Get all criteria in a category"""

    # --- Judges (implementations) ---
    def get_judge(self, judge_name: str) -> JudgeConfig:
        """Get judge with inheritance resolved"""

    def list_judges(self) -> list[str]:
        """List available judge names"""

    def get_judge_prompt(self, judge_name: str, criteria_id: str) -> str:
        """Get prompt content for a criteria from a judge (with inheritance)"""

    def get_judge_weights(self, judge_name: str) -> dict:
        """Get weights for a judge (with inheritance)"""

    # --- Datasets ---
    def get_dataset(self, dataset_name: str) -> DatasetConfig:
        """Get dataset info"""

    def list_datasets(self) -> list[DatasetConfig]:
        """List available datasets"""

    def load_dataset_prompts(self, dataset_name: str) -> list[AttackPrompt]:
        """Load actual prompts from dataset CSV"""

    def get_dataset_criteria_breakdown(self, dataset_name: str) -> dict[str, int]:
        """Get count of prompts per criteria in dataset"""

    # --- Presets ---
    def get_preset(self, preset_name: str) -> list[str]:
        """Get list of criteria IDs in preset"""

    def list_presets(self) -> dict[str, str]:
        """List presets with descriptions"""

    # --- Resolution ---
    def resolve_criteria_selection(self, selection: str) -> list[str]:
        """Resolve preset/category/criteria pattern to criteria IDs"""
```

**Data Classes**:
```python
@dataclass
class CriteriaConfig:
    id: str                    # e.g., "safety.sexual.sexual_content"
    category: str              # e.g., "safety"
    subcategory: str           # e.g., "sexual"
    name: str                  # e.g., "sexual_content"
    description: str
    tags: list[str]

@dataclass
class JudgeImplementation:
    file: str
    version: str
    created: str
    author: str
    prompt_content: dict | None = None  # Loaded lazily

@dataclass
class JudgeConfig:
    name: str
    description: str
    inherits_from: str | None
    weights: dict
    implementations: dict[str, JudgeImplementation]  # criteria_id -> impl

@dataclass
class DatasetConfig:
    name: str
    file: str
    description: str
    criteria_breakdown: dict[str, int] | None = None  # Loaded lazily

@dataclass
class AttackPrompt:
    id: str
    criteria_id: str
    prompt: str
```

### 3.2 CLI Changes

**New/Modified Commands**:

```bash
# --- Datasets ---
srl4c dataset list
# NAME                 CRITERIA    PROMPTS  DESCRIPTION
# quick_safety         6           30       Quick safety smoke test
# full_evaluation      22          220      Complete evaluation suite

srl4c dataset show <name>
# Dataset: quick_safety
# File: datasets/quick_safety.csv
#
# CRITERIA                                   COUNT
# safety.sexual.sexual_content               5
# safety.sexual.sensual_manipulation         5
# ...

# --- Judges ---
srl4c judges list
# NAME        INHERITS    DESCRIPTION
# default     -           Standard evaluation policy
# latam       default     LATAM regional standards
# eu_strict   default     EU AI Act strict compliance

srl4c judges show <name>
# Judge: latam
# Inherits from: default
#
# Weights (overrides):
#   ethics: 1.0
#
# Implementation overrides:
#   anthropomorphism.parasocial_bonds.persona_projection

# --- Criteria ---
srl4c criteria list
# CATEGORY           SUBCATEGORY    NAME                 DESCRIPTION
# safety             sexual         sexual_content       Detects inappropriate...
# safety             sexual         sensual_manipulation Detects sensual...
# ...

# --- Attack (modified) ---
srl4c attack run --endpoint <name> --dataset <name>
# Uses registered dataset instead of file path

# --- Score (modified) ---
srl4c score run <attack_id> --judge <name>
# Default: --judge default
```

### 3.3 API Changes

**New Endpoints**:

```
GET  /datasets                    # List datasets
GET  /datasets/{name}             # Dataset details + criteria breakdown
GET  /judges                      # List judges
GET  /judges/{name}               # Judge details
GET  /criteria                    # List all criteria
GET  /criteria/{id}               # Criteria details
```

**Modified Endpoints**:

```
POST /attacks
  Before: { "endpoint": "x", "dataset": "path/to/file.csv" }
  After:  { "endpoint": "x", "dataset": "quick_safety" }

POST /scores
  Before: { "attack_id": "x", "age_context": "13-17" }
  After:  { "attack_id": "x", "age_context": "13-17", "judge": "default" }
```

**Response Changes**:

```json
// GET /attacks/{id}
{
  "id": "attack_abc",
  "endpoint": "my_device",
  "dataset": "quick_safety",
  "criteria": [                    // NEW: List of criteria tested
    "safety.sexual.sexual_content",
    "safety.violence.physical_violence"
  ],
  "criteria_breakdown": {          // NEW: Count per criteria
    "safety.sexual.sexual_content": 5,
    "safety.violence.physical_violence": 5
  },
  "status": "completed",
  "total_prompts": 10
}

// GET /scores/{id}
{
  "id": "score_xyz",
  "attack_id": "attack_abc",
  "judge": "latam",                // NEW: Which judge was used
  "status": "completed",
  "final_score": 4.2
}
```

### 3.4 UI Changes

**New Settings Pages**:

```
Settings (sidebar menu)
├── Endpoints         (existing)
├── Datasets          (NEW)
│   ├── List view: name, criteria count, prompt count, description
│   └── Detail view: criteria breakdown table
└── Judges            (NEW)
    ├── List view: name, inherits_from, description
    └── Detail view: weights, implementation overrides
```

**Modified Pipeline**:

```
Attack Creation Dialog:
┌─────────────────────────────────────────┐
│ New Attack                              │
│                                         │
│ Endpoint:  [dropdown]                   │
│ Dataset:   [dropdown]                   │
│            └── Shows: "6 criteria, 30 prompts" │
│                                         │
│ [View Dataset Details]  [Create Attack] │
└─────────────────────────────────────────┘

Score Creation Dialog:
┌─────────────────────────────────────────┐
│ New Score                               │
│                                         │
│ Attack:    [dropdown/selected]          │
│ Age Group: [dropdown]                   │
│ Judge:     [dropdown]                   │
│            └── default, latam, eu_strict│
│                                         │
│ [Create Score]                          │
└─────────────────────────────────────────┘

Attack Detail View (enhanced):
┌─────────────────────────────────────────┐
│ Attack: attack_abc123                   │
│ Endpoint: my_device                     │
│ Dataset: quick_safety                   │
│ Status: completed                       │
│                                         │
│ Criteria Breakdown:                     │
│ ┌─────────────────────────────┬───────┐ │
│ │ CRITERIA                    │ COUNT │ │
│ ├─────────────────────────────┼───────┤ │
│ │ safety.sexual.sexual_content│ 5     │ │
│ │ safety.violence.physical... │ 5     │ │
│ └─────────────────────────────┴───────┘ │
└─────────────────────────────────────────┘
```

---

## Phase 4: Database Changes

### Schema Migration

```sql
-- Rename principle_id to criteria_id
ALTER TABLE records RENAME COLUMN principle_id TO criteria_id;
ALTER TABLE evaluations RENAME COLUMN principle_id TO criteria_id;
ALTER TABLE guardrails RENAME COLUMN principle_id TO criteria_id;

-- Add judge column to scores
ALTER TABLE scores ADD COLUMN judge TEXT DEFAULT 'default';

-- Update attacks table
-- dataset_name now references registered dataset name (no change needed, just semantic)
```

### Migration Script

```python
def migrate_v2():
    """Migrate to new registry schema"""
    with db_connection() as conn:
        # 1. Rename columns
        conn.execute("ALTER TABLE records RENAME COLUMN principle_id TO criteria_id")
        conn.execute("ALTER TABLE evaluations RENAME COLUMN principle_id TO criteria_id")
        conn.execute("ALTER TABLE guardrails RENAME COLUMN principle_id TO criteria_id")

        # 2. Add judge column
        conn.execute("ALTER TABLE scores ADD COLUMN judge TEXT DEFAULT 'default'")

        # 3. Strip version from criteria_id values
        # "safety.sexual.sexual_content__v1_0" -> "safety.sexual.sexual_content"
        conn.execute("""
            UPDATE records
            SET criteria_id = SUBSTR(criteria_id, 1, INSTR(criteria_id || '__', '__') - 1)
            WHERE criteria_id LIKE '%__%'
        """)
        # Same for evaluations and guardrails
```

---

## Phase 5: Implementation Order

### Step 1: Branch & Schema (Day 1)
- [ ] Create branch `refactor/registry-judges`
- [ ] Write new `registry.yml` structure
- [ ] Reorganize prompt files into `judges/default/`
- [ ] Keep old structure temporarily for comparison

### Step 2: Loader (Day 1-2)
- [ ] Create `src/srl4c/registry/` module
- [ ] Implement `RegistryLoader` with all methods
- [ ] Add judge inheritance resolution
- [ ] Add dataset criteria breakdown
- [ ] Unit tests for loader

### Step 3: CLI (Day 2)
- [ ] Add `dataset list`, `dataset show` commands
- [ ] Add `judges list`, `judges show` commands
- [ ] Add `criteria list` command
- [ ] Modify `attack run` to use dataset name
- [ ] Modify `score run` to accept `--judge`
- [ ] Update help text

### Step 4: API (Day 2-3)
- [ ] Add `/datasets`, `/judges`, `/criteria` endpoints
- [ ] Modify `/attacks` to use dataset name
- [ ] Modify `/scores` to accept judge
- [ ] Update response schemas
- [ ] Update OpenAPI docs

### Step 5: Database (Day 3)
- [ ] Write migration script
- [ ] Test migration on copy of real data
- [ ] Update repository methods
- [ ] Update model classes

### Step 6: UI (Day 3-4)
- [ ] Add Settings sidebar section
- [ ] Create Datasets page (list + detail)
- [ ] Create Judges page (list + detail)
- [ ] Modify Attack creation dialog
- [ ] Modify Score creation dialog
- [ ] Add criteria breakdown to Attack detail

### Step 7: Testing & Cleanup (Day 4)
- [ ] Update E2E tests
- [ ] Remove old `criteria/` directory
- [ ] Update CLAUDE.md
- [ ] Update README.md

---

## Backward Compatibility

### Breaking Changes
- `principle_id` renamed to `criteria_id` in DB
- Criteria IDs no longer include version (`__v1_0` suffix removed)
- Dataset specified by name, not file path
- Score requires judge selection (defaults to `default`)

### Migration Path
1. Run DB migration script
2. Replace `registry.yml`
3. Move prompt files to `judges/default/`
4. Update any external scripts using old API

---

## Future Enhancements (Out of Scope)

- UI for creating/editing judges
- Custom dataset upload via UI
- Judge comparison reports
- A/B testing between judges
