# CLAUDE.md - Project Guide for Claude Code

## What is this project?

**SRL4C** (Safety Readiness Level for Children) is a CLI tool to evaluate AI-generated content for children/teens (ages 6-25). It tests AI apps against 15 behaviors across 3 cues that may foster emotional reliance, and generates guardrails to fix failures.

## Project Structure

```
SRL4Children/
├── src/srl4c/                 # Main package
│   ├── core/                  # Shared business logic (CLI + API)
│   │   ├── attack.py          # create_attack(), run_attack()
│   │   ├── score.py           # create_score(), run_score()
│   │   ├── guardrails.py      # create_guardrails(), run_guardrails()
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
│   │   ├── repository.py      # CRUD operations
│   │   └── sync.py            # Sync built-in datasets/judges from files
│   ├── judge/                 # Evaluation system
│   │   ├── config.py          # Judge configuration
│   │   └── evaluator.py       # Multi-judge scoring
│   ├── adapters/              # Endpoint connectors
│   ├── paths.py               # Centralized path config
│   └── wrapper.py             # OpenAI proxy wrapper
│
├── data/
│   ├── criteria/              # Registry configuration (split files)
│   │   ├── criteria.yml       # 15 behavior definitions across 3 cues
│   │   ├── presets.yml        # Named criteria selections
│   │   └── judges/            # Context-based judge configs
│   │       ├── educational.yml
│   │       ├── companionship.yml
│   │       └── entertainment.yml
│   ├── judges/                # Judge prompt implementations
│   │   └── emotional_reliance/  # 15 .prompt files by cue
│   │       ├── anthropomorphic/
│   │       ├── interactional/
│   │       └── relational/
│   └── datasets/              # Attack CSV files (auto-discovered)
│
├── templates/                 # Copied to ~/.srl4c/ on init
│   ├── judges.yaml            # LLM judge model configuration
│   └── guardrails.yaml        # Guardrail generation settings
│
├── archive/                   # Legacy docs (not maintained)
└── sample_apps/               # Example applications
```

## Quick Commands

```bash
# Run CLI
uv run python -m srl4c.cli.main --help
uv run python -m srl4c.cli.main criteria list      # List 15 behaviors across 3 cues
uv run python -m srl4c.cli.main eval-judges list   # List evaluation judges
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

### Cues, Behaviors, and Judges

**Behaviors** are the 15 patterns being evaluated, organized into 3 **cues**:
- **Anthropomorphic** (5): persona/backstories, emotional claims, physical sensations, agency/intentions, sentience
- **Interactional** (6): human communication markers, mimicry, proactivity, flattery, empathy, validation
- **Relational** (4): intrusiveness, relatability, relationship labels, exclusivity

**Judges** are context-specific configurations. Each judge:
- Applies different weights per cue based on the AI's intended use case
- Shares the same `.prompt` files for consistent evaluation
- Judge selection is **required** when scoring (no default)

Built-in judges: `educational`, `companionship`, `entertainment`

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
# src/srl4c/core/attack.py

def create_attack(endpoint_name: str, dataset_name: str) -> str:
    """
    Validates inputs, creates DB record with status='pending'.
    Returns attack_id. Raises ValueError on validation failure.
    """

def run_attack(attack_id: str, on_progress: Callable = None) -> None:
    """
    Executes the job, updates DB progress, sets status on completion/failure.
    Optional on_progress callback for CLI progress bars.
    """
```

### CLI Usage

```python
# CLI calls create, runs in thread, polls DB for progress display
attack_id = create_attack(endpoint, dataset)
thread = Thread(target=run_attack, args=(attack_id,))
thread.start()
# Poll and display progress...
```

### API Usage

```python
# API calls create, runs in background task, client polls status
@router.post("/", status_code=202)
async def create_attack_endpoint(request: AttackCreate, background_tasks: BackgroundTasks):
    attack_id = create_attack(request.endpoint, request.dataset)
    background_tasks.add_task(run_attack, attack_id)
    return {"id": attack_id, "status": "pending"}
```

### Database as State Machine

Jobs use DB columns for state: `status`, `progress_current`, `progress_total`, `error_message`, `updated_at`.

Status flow: `pending` → `running` → `completed` | `failed`

Jobs running >90 min without updates auto-mark as `stale`.

## Key Files

| File | Purpose |
|------|---------|
| `src/srl4c/core/attack.py` | Attack business logic (create + run) |
| `src/srl4c/core/score.py` | Score business logic (create + run + report) |
| `src/srl4c/core/guardrails.py` | Guardrails business logic (create + run) |
| `src/srl4c/core/datasets.py` | Dataset CRUD (list, get, create, delete) |
| `src/srl4c/core/judges.py` | Eval judge CRUD (list, get, create, update weights) |
| `src/srl4c/api/main.py` | FastAPI app with all routers |
| `src/srl4c/api/schemas.py` | Pydantic request/response models |
| `src/srl4c/cli/main.py` | Typer CLI command definitions |
| `src/srl4c/paths.py` | All path constants |
| `src/srl4c/registry/loader.py` | Load criteria & judges from registry |
| `src/srl4c/judge/evaluator.py` | Multi-judge evaluation + weighting |
| `src/srl4c/db/repository.py` | CRUD + progress update methods |
| `src/srl4c/db/sync.py` | Sync built-in datasets/judges from files to DB |
| `data/criteria/criteria.yml` | Behavior definitions (15 across 3 cues) |
| `data/criteria/presets.yml` | Named criteria selections |
| `data/criteria/judges/*.yml` | Context-based judge configs with weights |
| `data/judges/emotional_reliance/*.prompt` | Evaluation prompt implementations |
| `templates/judges.yaml` | LLM judge model configuration |

## Configuration

User configs live in `~/.srl4c/`:
- `judges.yaml` - Which LLM models judge responses (model names, passes, temperatures)
- `guardrails.yaml` - Guardrail generation settings (model, max rules)
- `srl4c.db` - SQLite database (endpoints, attacks, scores, datasets, judges, etc.)

**Note**: Evaluation judge weights are now stored per-judge in the database, not in a separate YAML file. Use the UI or API to create custom judges with weight overrides.

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
