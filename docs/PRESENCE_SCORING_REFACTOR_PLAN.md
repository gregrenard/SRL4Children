# Presence Judges + Scoring Matrix Refactor

## Overview

Refactor the SRL4C scoring system from context-specific judges to context-agnostic presence judges with a scoring matrix.

**Current**: `response → judge(context-specific) → score (0-5)`
**Target**: `response → presence_judge(behavior) → presence (1-5) → matrix(age, context) → score (0-5)`

## Key Changes

| Current | New |
|---------|-----|
| 3 context-specific judges | 1 presence judge (15 behaviors) |
| 45 prompt files | 15 prompt files (context-agnostic) |
| Judge outputs score 0-5 | Judge outputs presence 1-5 |
| Score = f(response, context) | Score = matrix(presence, age, context) |
| Select "judge" when scoring | Select "age + context + matrix" |

---

## Phase 1: Database Schema

### New Tables

**File**: `src/srl4c/db/models.py`

```sql
CREATE TABLE IF NOT EXISTS scoring_matrices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    is_builtin INTEGER NOT NULL DEFAULT 0,
    tenant_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, tenant_id)
);

CREATE TABLE IF NOT EXISTS scoring_matrix_entries (
    id TEXT PRIMARY KEY,
    matrix_id TEXT NOT NULL,
    behavior_id TEXT NOT NULL,
    age_group TEXT NOT NULL,          -- child, teenager, young_adult
    context TEXT NOT NULL,            -- companionship, educational, entertainment
    presence_level INTEGER NOT NULL,  -- 1-5
    score REAL NOT NULL,              -- 0-5
    FOREIGN KEY (matrix_id) REFERENCES scoring_matrices(id),
    UNIQUE(matrix_id, behavior_id, age_group, context, presence_level)
);
```

### Modify Existing Tables

```sql
ALTER TABLE scores ADD COLUMN context TEXT;
ALTER TABLE scores ADD COLUMN matrix_id TEXT REFERENCES scoring_matrices(id);
ALTER TABLE evaluations ADD COLUMN presence_level INTEGER;
```

### New Dataclasses

```python
@dataclass
class ScoringMatrix:
    id: str
    name: str
    description: Optional[str] = None
    is_builtin: bool = False
    ...

@dataclass
class ScoringMatrixEntry:
    id: str
    matrix_id: str
    behavior_id: str
    age_group: str
    context: str
    presence_level: int
    score: float
```

---

## Phase 2: Repository Layer

**File**: `src/srl4c/db/repository.py`

Add `ScoringMatrixRepository`:
- `get_by_id(id)` / `get_by_name(name)`
- `list_all(tenant_id)`
- `create(matrix)` / `delete(id)`
- `get_entries(matrix_id)`
- `set_entries(matrix_id, entries)`
- `lookup_score(matrix_id, behavior_id, age_group, context, presence_level)` - returns mapped score, defaults to identity if no entry

---

## Phase 3: Presence Judge Prompts (15 files)

**Location**: `data/judges/presence/emotional_reliance/`

```
anthropomorphic/
    persona_and_backstories.prompt
    emotional_state_expression.prompt
    ai_physical_sensation_claims.prompt
    agency_desires_intentions.prompt
    sentience.prompt
interactional/
    human_markers_of_communication.prompt
    mimicry.prompt
    proactivity.prompt
    flattery.prompt
    empathy.prompt
    validation.prompt
relational/
    intrusiveness.prompt
    relatability.prompt
    relationship_status.prompt
    exclusivity.prompt
```

### Prompt Template

Each prompt file (YAML) contains:
- `role`: Context-agnostic evaluator
- `task`: Detect presence level 1-5 only
- `category` / `category_definition`: From spreadsheet
- `behavior` / `behavior_definition`: From spreadsheet
- `presence_guide`: Levels 1-5 definitions (verbatim from spreadsheet)
- `examples`: ALL 3 context examples (companionship, educational, entertainment) as few-shot
- `output_format`: `{"presence_level": 1-5, "explanation": "...", "evidence_extracts": [...]}`

**Source of truth**: `data/emotional_reliance_spreadsheet.yml`

### Judge Config

**File**: `data/criteria/judges/presence.yml`

```yaml
judge:
  name: presence
  description: "Context-agnostic presence level detection (1-5)"
  implementations:
    emotional_reliance.anthropomorphic.persona_and_backstories:
      file: "judges/presence/emotional_reliance/anthropomorphic/persona_and_backstories.prompt"
    # ... 14 more
```

---

## Phase 4: Default "Flat" Matrix

**File**: `src/srl4c/db/sync.py`

Add `sync_builtin_matrices()`:
- Creates "flat" matrix if not exists
- Identity mapping: presence 1→1, 2→2, 3→3, 4→4, 5→5
- No entries needed (lookup defaults to identity)

---

## Phase 5: Core Scoring Logic

### create_score() changes

**File**: `src/srl4c/core/score.py`

```python
def create_score(
    attack_id: str,
    age: str = "child",           # child, teenager, young_adult
    context: str = "educational", # companionship, educational, entertainment
    matrix: str = "flat",         # Scoring matrix name
) -> str:
```

- Validate age in `["child", "teenager", "young_adult"]`
- Validate context in `["companionship", "educational", "entertainment"]`
- Validate matrix exists
- Store `context` and `matrix_id` in scores table

### run_score() changes

```python
def run_score(score_id: str, ...):
    # Always use "presence" judge
    judge_name = "presence"

    # Get matrix, age, context from score record
    matrix_id = score["matrix_id"]
    age_group = score["age_context"]
    context = score["context"]

    # Evaluate (returns presence levels)
    results = evaluate_records_batch(config, records, judge_name)

    # For each evaluation:
    for crit_result in result.detailed_criteria:
        presence_level = crit_result.presence_level  # 1-5

        # Map to score via matrix
        final_score = ScoringMatrixRepository.lookup_score(
            matrix_id, behavior_id, age_group, context, presence_level
        )

        # Store both presence_level and final_score
        conn.execute("""INSERT INTO evaluations
            (..., presence_level, final_score, ...) VALUES (...)""")
```

---

## Phase 6: Evaluator Changes

**File**: `src/srl4c/judge/evaluator.py`

### parse_presence_response()
- Parse `{"presence_level": 1-5, "explanation": "...", "evidence_extracts": [...]}`
- Validate presence_level is 1-5

### build_presence_evaluation_prompt()
- No age_group parameter (context-agnostic)
- Uses `presence_guide` instead of `scoring_guide`
- Includes all 3 context examples

### CriterionEvaluationResult
- Add `presence_level: int` field

---

## Phase 7: API Changes

### New Router

**File**: `src/srl4c/api/routes/matrices.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/matrices/` | GET | List all matrices |
| `/matrices/` | POST | Create matrix |
| `/matrices/{id}` | GET | Get matrix with entries |
| `/matrices/{id}/entries` | PUT | Update matrix entries |
| `/matrices/{id}` | DELETE | Delete matrix |

### New Schemas

**File**: `src/srl4c/api/schemas.py`

```python
class MatrixCreate(BaseModel):
    name: str
    description: Optional[str] = None

class MatrixEntry(BaseModel):
    behavior_id: str
    age_group: str      # child, teenager, young_adult
    context: str        # companionship, educational, entertainment
    presence_level: int # 1-5
    score: float        # 0-5

class MatrixDetailResponse(BaseModel):
    id: str
    name: str
    entries: List[MatrixEntry] = []
```

### Modify Score Schemas

```python
class ScoreCreate(BaseModel):
    attack_id: str
    age: str = "child"
    context: str = "educational"  # NEW
    matrix: str = "flat"          # NEW (replaces judge)

class ScoreResponse(BaseModel):
    ...
    context: str                  # NEW
    matrix_id: Optional[str]      # NEW
    matrix_name: Optional[str]    # NEW
```

---

## Phase 8: UI Changes

### Dashboard.jsx - Score Form

```javascript
score: {
  fields: [
    { name: 'attack_id', ... },
    { name: 'age', label: 'Age Group', options: [
      { value: 'child', label: 'Child (6-12)' },
      { value: 'teenager', label: 'Teenager (13-17)' },
      { value: 'young_adult', label: 'Young Adult (18-25)' },
    ]},
    { name: 'context', label: 'Context', options: [
      { value: 'companionship', label: 'Companionship' },
      { value: 'educational', label: 'Educational' },
      { value: 'entertainment', label: 'Entertainment' },
    ]},
    { name: 'matrix', label: 'Scoring Matrix', options: matrices },
  ]
}
```

### New MatricesModal.jsx

- List matrices (name, description, is_builtin)
- View entries (grid: 15 behaviors × 5 presence levels, filtered by age/context)
- Create new matrix
- Edit entries (non-builtin only)
- Delete matrix

### Topbar.jsx

Add "Matrices" button in config section (next to Judges).

### API Client

```javascript
getMatrices: () => get('/matrices'),
getMatrix: (id) => get(`/matrices/${id}`),
createMatrix: (data) => post('/matrices', data),
updateMatrixEntries: (id, entries) => put(`/matrices/${id}/entries`, { entries }),
deleteMatrix: (id) => del(`/matrices/${id}`),
```

---

## Phase 9: Cleanup

### Delete old files (after verification)

```
data/judges/companionship/emotional_reliance/**/*.prompt  (15 files)
data/judges/educational/emotional_reliance/**/*.prompt    (15 files)
data/judges/entertainment/emotional_reliance/**/*.prompt  (15 files)
data/criteria/judges/companionship.yml
data/criteria/judges/educational.yml
data/criteria/judges/entertainment.yml
```

### Drop deprecated column

```sql
ALTER TABLE scores DROP COLUMN judge_id;
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/srl4c/db/models.py` | Add scoring_matrices, scoring_matrix_entries tables; add columns to scores/evaluations |
| `src/srl4c/db/repository.py` | Add ScoringMatrixRepository |
| `src/srl4c/db/sync.py` | Add sync_builtin_matrices() |
| `src/srl4c/core/score.py` | Refactor create_score, run_score |
| `src/srl4c/judge/evaluator.py` | Add presence parsing, update prompt building |
| `src/srl4c/api/main.py` | Register matrices router |
| `src/srl4c/api/schemas.py` | Add matrix schemas, update score schemas |
| `src/srl4c/api/routes/matrices.py` | NEW: Matrix CRUD endpoints |
| `src/srl4c/api/routes/scores.py` | Update for new score fields |
| `ui/src/pages/Dashboard.jsx` | Update score form |
| `ui/src/components/modals/MatricesModal.jsx` | NEW: Matrix editor |
| `ui/src/components/layout/Topbar.jsx` | Add Matrices button |
| `ui/src/api/client.js` | Add matrix API methods |

## Files to Create

| File | Description |
|------|-------------|
| `data/judges/presence/emotional_reliance/**/*.prompt` | 15 presence prompts |
| `data/criteria/judges/presence.yml` | Presence judge config |
| `src/srl4c/api/routes/matrices.py` | Matrix API endpoints |
| `ui/src/components/modals/MatricesModal.jsx` | Matrix editor UI |

---

## Verification

1. **Unit tests**: Update existing score tests, add matrix tests
2. **E2E test**: Create score with age=child, context=educational, matrix=flat
3. **Manual verification**:
   - Create score via UI with new form fields
   - Verify presence_level stored in evaluations
   - Verify final_score = presence_level for flat matrix
   - Create custom matrix, verify mapping works
   - View/edit matrices in UI
