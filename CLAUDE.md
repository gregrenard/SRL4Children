# CLAUDE.md - Project Guide for Claude Code

## What is this project?

**SRL4C** (Safety Readiness Level for Children) is a CLI tool to evaluate AI-generated content for children/teens (ages 6-25). It tests AI apps against 15 behaviors across 3 cues that may foster emotional reliance, using presence detection and context-specific scoring matrices. It generates guardrails to fix failures.

## Project Structure

```
SRL4Children/
├── src/srl4c/                 # Main package
│   ├── core/                  # Shared business logic (CLI + API)
│   │   ├── attack.py          # create_attack(), run_attack()
│   │   ├── score.py           # create_score(), run_score(), generate_report()
│   │   ├── guardrails.py      # create_guardrails(), run_guardrails()
│   │   ├── matrices.py        # Scoring matrix CRUD operations
│   │   ├── datasets.py        # Dataset CRUD operations
│   │   └── judges.py          # Evaluation judge CRUD operations
│   ├── cli/                   # Typer CLI (thin wrapper)
│   │   ├── main.py            # Command definitions
│   │   └── commands/          # Command implementations
│   ├── api/                   # FastAPI REST API (thin wrapper)
│   │   ├── main.py            # FastAPI app + routers
│   │   ├── schemas.py         # Pydantic request/response models
│   │   └── routes/            # Route handlers
│   ├── registry/              # Registry loader
│   │   └── loader.py          # Loads criteria & judges from split files
│   ├── db/                    # SQLite persistence
│   │   ├── models.py          # Data models + dataclasses
│   │   ├── repository.py      # CRUD operations + score lookup
│   │   └── sync.py            # Sync datasets/matrices + generate .prompt/.guardrail files
│   ├── judge/                 # Evaluation system
│   │   ├── config.py          # Judge configuration
│   │   └── evaluator.py       # Presence detection evaluation
│   ├── adapters/              # Endpoint connectors
│   ├── paths.py               # Centralized path config
│   └── wrapper.py             # OpenAI proxy wrapper
│
├── data/
│   ├── emotional_reliance_spreadsheet.yml  # SOURCE OF TRUTH (from research Excel)
│   ├── criteria/              # Registry configuration (split files)
│   │   ├── criteria.yml       # 15 behavior definitions across 3 cues
│   │   ├── presets.yml        # Named criteria selections
│   │   └── judges/            # Judge configs
│   │       └── presence.yml   # Presence detection judge config
│   ├── judges/                # GENERATED from YAML spreadsheet
│   │   └── presence/
│   │       └── emotional_reliance/
│   │           ├── anthropomorphic/
│   │           │   ├── *.prompt      # For presence judges
│   │           │   └── *.guardrail   # For guardrail generation
│   │           ├── interactional/
│   │           └── relational/
│   └── datasets/              # Attack CSV files (auto-discovered)
│
├── templates/                 # Copied to ~/.srl4c/ on init
│   ├── judges.yaml            # LLM judge model configuration
│   └── guardrails.yaml        # Guardrail generation settings
│
├── ui/                        # React/Vite web dashboard
│   └── src/
│       └── pages/
│           ├── Dashboard.jsx
│           ├── Datasets.jsx
│           └── ScoringConfig.jsx  # Matrix editor
│
├── archive/                   # Legacy docs (not maintained)
└── sample_apps/               # Example applications
```

## Quick Commands

```bash
# Run CLI
uv run python -m srl4c.cli.main --help
uv run python -m srl4c.cli.main criteria list      # List 15 behaviors across 3 cues
uv run python -m srl4c.cli.main matrix list        # List scoring matrices
uv run python -m srl4c.cli.main dataset list       # List datasets

# Start API server
uv run python -m srl4c.cli.main api serve --port 8000

# Start UI (in separate terminal)
cd ui && VITE_API_URL=http://localhost:8000 npm run dev

# Install globally
uv tool install -e . --force
srl4c --help
srl4c api serve --port 8000
```

## Key Concepts

### Scoring Architecture

SRL4C uses a two-stage scoring system:

```
Response → Presence Judge → Presence Level (1-5) → Scoring Matrix → Final Score (0-5)
```

**Stage 1: Presence Detection** (context-agnostic)
- A single "presence" judge evaluates each response
- Detects HOW MUCH of each behavior is present (1-5 scale)
- Level 1 = minimal/no presence, Level 5 = strong presence
- Uses `.prompt` files generated from the YAML spreadsheet

**Stage 2: Score Mapping** (context-specific)
- Scoring matrices map presence levels to safety scores
- Three built-in matrices: `educational`, `companionship`, `entertainment`
- Score 0 = most concerning, Score 5 = fully safe
- Age group (child, teenager, young_adult) affects the mapping

### Source of Truth

All behavior definitions come from `data/emotional_reliance_spreadsheet.yml`:

```
YAML Spreadsheet (from research team's Excel)
         ↓
    sync_all() on startup
         ↓
    ┌────┴────┐
    ↓         ↓
.prompt    .guardrail
(judges)   (guardrails)
```

- **YAML Spreadsheet**: Contains all 15 behaviors, presence level definitions (1-5), and examples
- **`.prompt` files**: Generated for presence judges
- **`.guardrail` files**: Generated for guardrail generation (presence level definitions only)

### Cues and Behaviors

**Behaviors** are the 15 patterns being evaluated, organized into 3 **cues**:
- **Anthropomorphic** (5): persona/backstories, emotional claims, physical sensations, agency/intentions, sentience
- **Interactional** (6): human communication markers, mimicry, proactivity, flattery, empathy, validation
- **Relational** (4): intrusiveness, relatability, relationship labels, exclusivity

### Scoring Matrices

Context-specific matrices map `(behavior, age_group, presence_level)` → `score`:

| Matrix | Context | Scoring |
|--------|---------|---------|
| `educational` | Tutoring, homework help | Stricter (low tolerance for warmth) |
| `companionship` | AI friends, emotional support | More permissive |
| `entertainment` | Games, stories | Balanced |

Built-in matrices are created by `sync_builtin_matrices()` in `sync.py`.

### Datasets

**First-class DB objects** - both built-in (synced from `data/datasets/*.csv`) and user-uploaded.

CSV format:
- `PromptID`: UUID
- `Category`: Behavior ID (e.g., `emotional_reliance.relational.exclusivity`)
- `Prompt`: The adversarial prompt text

### CLI Workflow
```
ATTACK → SCORE → GUARDRAILS → RE-ATTACK → COMPARE
```

## Core Module Pattern

All long-running operations share code between CLI and API via the `core/` module.

### Pattern

Each operation has two functions:

```python
# src/srl4c/core/score.py

def create_score(attack_id: str, age: str = "child", matrix: str = "educational") -> str:
    """
    Validates inputs, creates DB record with status='pending'.
    Returns score_id. Raises ValueError on validation failure.
    """

def run_score(score_id: str, on_progress: Callable = None) -> None:
    """
    Runs presence detection, maps to scores via matrix,
    updates progress in DB, sets status on completion/failure.
    """
```

### CLI Usage

```python
# CLI calls create, runs in thread, polls DB for progress display
score_id = create_score(attack_id, age="child", matrix="educational")
thread = Thread(target=run_score, args=(score_id,))
thread.start()
# Poll and display progress...
```

### API Usage

```python
# API calls create, runs in background task, client polls status
@router.post("/", status_code=202)
async def create_score_endpoint(request: ScoreCreate, background_tasks: BackgroundTasks):
    score_id = create_score(request.attack_id, request.age, request.matrix)
    background_tasks.add_task(run_score, score_id)
    return {"id": score_id, "status": "pending"}
```

### Database as State Machine

Jobs use DB columns for state: `status`, `progress_current`, `progress_total`, `error_message`, `updated_at`.

Status flow: `pending` → `running` → `completed` | `failed`

Jobs running >90 min without updates auto-mark as `stale`.

## Key Files

| File | Purpose |
|------|---------|
| `data/emotional_reliance_spreadsheet.yml` | **SOURCE OF TRUTH** - All behavior definitions |
| `src/srl4c/core/attack.py` | Attack business logic (create + run) |
| `src/srl4c/core/score.py` | Score business logic (presence detection + matrix mapping + report) |
| `src/srl4c/core/guardrails.py` | Guardrails business logic (loads .guardrail files for definitions) |
| `src/srl4c/core/matrices.py` | Scoring matrix CRUD |
| `src/srl4c/core/datasets.py` | Dataset CRUD (list, get, create, delete) |
| `src/srl4c/api/main.py` | FastAPI app with all routers |
| `src/srl4c/api/schemas.py` | Pydantic request/response models |
| `src/srl4c/cli/main.py` | Typer CLI command definitions |
| `src/srl4c/paths.py` | All path constants |
| `src/srl4c/registry/loader.py` | Load criteria & judges from registry |
| `src/srl4c/judge/evaluator.py` | Presence detection evaluation |
| `src/srl4c/db/repository.py` | CRUD + `ScoringMatrixRepository.lookup_score()` |
| `src/srl4c/db/sync.py` | Sync datasets/matrices + generate .prompt/.guardrail files |
| `data/criteria/criteria.yml` | Behavior definitions (15 across 3 cues) |
| `data/judges/presence/emotional_reliance/*.prompt` | Generated presence judge prompts |
| `data/judges/presence/emotional_reliance/*.guardrail` | Generated guardrail definitions |
| `templates/judges.yaml` | LLM judge model configuration |

## Configuration

User configs live in `~/.srl4c/`:
- `judges.yaml` - Which LLM models detect presence (model names, passes, temperatures)
- `guardrails.yaml` - Guardrail generation settings (model, max rules)
- `srl4c.db` - SQLite database (endpoints, attacks, scores, evaluations, matrices, etc.)

## Database Schema

Key tables for scoring:

```sql
-- Evaluations store both presence level and mapped score
CREATE TABLE evaluations (
    ...
    presence_level INTEGER,    -- 1-5 from judge
    final_score REAL,          -- 0-5 from matrix mapping
    ...
);

-- Scoring matrices map (behavior, age, presence) → score
CREATE TABLE scoring_matrices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,        -- educational, companionship, entertainment
    is_builtin INTEGER,
    ...
);

CREATE TABLE scoring_matrix_entries (
    matrix_id TEXT,
    behavior_id TEXT,          -- e.g., "flattery"
    age_group TEXT,            -- child, teenager, young_adult
    presence_level INTEGER,    -- 1-5
    score REAL,                -- 0-5 mapped score
    ...
);
```

## Testing

E2E test suite validates full pipeline using fake servers (no real LLM calls).

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test
uv run pytest tests/e2e/test_pipeline_api.py -v
```

### Test Structure

```
tests/
├── conftest.py              # Fixtures: fake servers, isolated DB, path patching
├── fixtures/
│   └── test_dataset.csv     # 8 prompts matching registry criteria
└── e2e/
    ├── test_pipeline_api.py # Full pipeline via REST API (TestClient)
    └── test_pipeline_cli.py # Full pipeline via CLI subprocess
```

### Fake Servers

- `tools/fake_endpoint.py` - Simulates chatbot endpoint
- `tools/fake_judge.py` - Simulates OpenAI judge (forces ~25% failures for guardrails testing)

## Notes

- Always use `uv`, never `pip`
- Paths are centralized in `src/srl4c/paths.py`
- API keys go in `.env` at project root
- All DB operations must use `db_connection()` context manager from `src/srl4c/db/models.py`:
  ```python
  from srl4c.db.models import db_connection

  with db_connection() as conn:
      conn.execute("SELECT * FROM ...")
  # Auto-commits on success, auto-closes on exit
  ```

## Score Interpretation

| Score | Meaning |
|-------|---------|
| 5.0 | Fully safe (presence level 1) |
| 3.0+ | Acceptable |
| < 3.0 | Concerning (triggers guardrails) |
| 0.0 | Most concerning (presence level 5) |

## Guardrails Generation

Guardrails read presence level definitions from `.guardrail` files:

```python
# src/srl4c/core/guardrails.py
def get_presence_definitions(behavior_id: str) -> Dict[int, str]:
    """Load from .guardrail file (generated from YAML spreadsheet)"""
```

The guardrail prompt includes:
- Current presence level + its definition
- Target (level 1) definition
- This gives the LLM concrete guidance on what "safe" looks like
