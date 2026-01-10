# CLAUDE.md - Project Guide for Claude Code

## What is this project?

**SRL4C** (Safety Readiness Level for Children) is a CLI tool to evaluate AI-generated content for children/teens (ages 6-25). It tests AI apps against 22 Design Principles and generates guardrails to fix failures.

## Project Structure

```
SRL4Children/
├── src/srl4c/                 # Main package
│   ├── core/                  # Shared business logic (CLI + API)
│   │   ├── attack.py          # create_attack(), run_attack()
│   │   ├── score.py           # create_score(), run_score()
│   │   └── guardrails.py      # create_guardrails(), run_guardrails()
│   ├── cli/                   # Typer CLI (thin wrapper)
│   │   ├── main.py            # Command definitions
│   │   └── commands/          # Command implementations
│   ├── api/                   # FastAPI REST API (thin wrapper)
│   │   ├── main.py            # FastAPI app + routers
│   │   ├── schemas.py         # Pydantic request/response models
│   │   └── routes/            # Route handlers
│   ├── criteria/              # Criteria loader
│   │   └── loader.py          # Loads principles from registry
│   ├── db/                    # SQLite persistence
│   │   ├── models.py          # Data models
│   │   └── repository.py      # CRUD operations
│   ├── judge/                 # Evaluation system
│   │   ├── config.py          # Judge configuration
│   │   └── evaluator.py       # Multi-judge scoring
│   ├── adapters/              # Endpoint connectors
│   ├── paths.py               # Centralized path config
│   └── wrapper.py             # OpenAI proxy wrapper
│
├── data/
│   ├── criteria/              # 22 .prompt files + registry.yml
│   │   ├── safety/
│   │   ├── anthropomorphism/
│   │   ├── age/
│   │   ├── relevance/
│   │   └── ethics/
│   └── datasets/              # Attack CSV files
│
├── templates/                 # Copied to ~/.srl4c/ on init
│   ├── judges.yaml
│   ├── weights.yaml
│   └── guardrails.yaml
│
├── archive/                   # Legacy docs (not maintained)
└── sample_apps/               # Example applications
```

## Quick Commands

```bash
# Run CLI
uv run python -m srl4c.cli.main --help
uv run python -m srl4c.cli.main principles list
uv run python -m srl4c.cli.main dataset list

# Start API server
uv run python -m srl4c.cli.main api serve --port 8000

# Install globally
uv tool install -e . --force
srl4c --help
srl4c api serve --port 8000
```

## Key Concepts

### Design Principles
22 safety criteria in 5 categories:
- **Safety** (6): sexual_content, violence, manipulation, hate
- **Anthropomorphism** (8): emotions, agency, sycophancy, parasocial bonds
- **Age** (3): vocabulary, complexity, abstract concepts
- **Relevance** (2): topic match, factual accuracy
- **Ethics** (3): harmful advice, positive guidance, social norms

Each principle has a `.prompt` file in `data/criteria/` with scoring guide and examples.

### Datasets
CSV files in `data/datasets/` with attack prompts:
- `PromptID`: UUID
- `Category`: Which principle this tests
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
| `src/srl4c/api/main.py` | FastAPI app with all routers |
| `src/srl4c/api/schemas.py` | Pydantic request/response models |
| `src/srl4c/cli/main.py` | Typer CLI command definitions |
| `src/srl4c/paths.py` | All path constants |
| `src/srl4c/criteria/loader.py` | Load principles from registry |
| `src/srl4c/judge/evaluator.py` | Multi-judge evaluation + weighting |
| `src/srl4c/db/repository.py` | CRUD + progress update methods |
| `data/criteria/registry.yml` | Principle registry with presets |
| `templates/judges.yaml` | Judge model configuration |
| `templates/weights.yaml` | Score weighting presets |

## Configuration

User configs live in `~/.srl4c/`:
- `judges.yaml` - Which models judge responses
- `weights.yaml` - How to weight categories (presets: balanced, safety_focused, etc.)
- `guardrails.yaml` - Guardrail generation settings
- `srl4c.db` - SQLite database

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
