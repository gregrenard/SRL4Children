# CLAUDE.md - Project Guide for Claude Code

## What is this project?

**SRL4Children** (Safety Readiness Level for Children) is a framework to evaluate AI-generated content for children/teens (ages 6-25). Think NASA's TRL but for child-facing AI safety.

The project has two parts:
1. **Evaluation Engine** (`src/`) - Existing code that judges AI responses against 22 Design Principles
2. **CLI Framework** (`srl4c/`) - New Typer-based CLI being built to make the engine easy to use

## Quick Commands

```bash
# Always use uv, never pip
cd srl4c/

# Run CLI during development
uv run python -m srl4c.cli.main --help
uv run python -m srl4c.cli.main principles list
uv run python -m srl4c.cli.main dataset list

# Install globally (after changes)
uv tool install -e . --force

# Then run directly
srl4c --help
```

## Architecture

```
SRL4Children/
├── src/                        # EXISTING evaluation engine
│   ├── core/
│   │   ├── judge.py            # Multi-judge system (3 judges × 3 passes)
│   │   ├── criteria_loader.py  # Loads Design Principles from YAML/prompts
│   │   └── weighting_system.py # Aggregates scores hierarchically
│   ├── connectors/
│   │   └── clients.py          # Ollama LLM connector
│   └── data/
│       └── loader.py           # Dataset CSV loader
│
├── assets/                     # Design Principles definitions
│   ├── criteria/               # 22 .prompt files (evaluation specs)
│   │   ├── safety/
│   │   ├── anthropomorphism/
│   │   ├── age/
│   │   ├── relevance/
│   │   └── ethics/
│   └── criteria_registry.yml   # Registry of all principles
│
├── data/                       # Attack datasets (CSV)
│   ├── anthropomorphism_question.csv
│   ├── basic_safety.csv
│   └── ...
│
├── tools/                      # Guardrail generation
│   └── generate_guardrails.py
│
├── srl4c/                      # NEW CLI framework
│   ├── pyproject.toml
│   ├── PLAN.md                 # Implementation plan with examples
│   └── src/srl4c/
│       ├── cli/
│       │   ├── main.py         # Typer app with all commands
│       │   └── commands/       # Command implementations
│       ├── db/                 # TODO: SQLite layer
│       └── adapters/           # TODO: Endpoint connectors
│
└── config.yml                  # Main config (judges, weights, etc.)
```

## Key Concepts

### Design Principles
The 22 safety criteria organized in 5 categories:
- **Safety** (6): sexual_content, violence, manipulation, hate
- **Anthropomorphism** (8): emotions, agency, sycophancy, parasocial bonds
- **Age** (3): vocabulary, complexity, abstract concepts
- **Relevance** (2): topic match, factual accuracy
- **Ethics** (3): harmful advice, positive guidance, social norms

Each principle has a `.prompt` file in `assets/criteria/` defining:
- Scoring guide (0-5 scale)
- Examples
- Evidence extraction format

### Datasets
CSV files with attack prompts. Each row has:
- `PromptID`: UUID
- `Category`: Which principle this prompt tests (e.g., `anthropomorphism.parasocial_bonds.exclusivity_claims`)
- `Prompt`: The adversarial prompt text

**Important**: Prompts are coupled to principles. "Are we friends?" tests `exclusivity_claims`, not `vocabulary_level`.

### CLI Workflow
```
1. ATTACK:    Send prompts to endpoint → Get responses
2. SCORE:     Judge responses + Aggregate with weights → Report
3. GUARDRAILS: Generate fixes for failures → Export for system prompt
4. RE-ATTACK: Validate improvement with guardrails applied
```

Attack and Score are separate operations (can re-score same attack with different age/weights).

## CLI Commands

### Working Now
```bash
srl4c init                          # Setup ~/.srl4c/
srl4c principles list               # Show 22 principles
srl4c principles show <name>        # Show principle details
srl4c dataset list                  # Show datasets
srl4c dataset show <name>           # Show dataset contents
```

### TODO (Stubs Exist)
```bash
srl4c endpoint add openai --name X --base-url URL --api-key-env VAR
srl4c endpoint add simple --name X --url URL --api-key-env VAR
srl4c endpoint list/test/remove

srl4c attack run --endpoint X --dataset Y
srl4c attack list/show

srl4c score run <attack-id> --age child --weights balanced
srl4c score list/show/failures/compare

srl4c guardrails generate <score-id>
srl4c guardrails list/show/export/transform

srl4c config show/set/edit
```

## Key Design Decisions

1. **SQLite for state** - Store endpoints, attacks, scores, guardrails in `~/.srl4c/srl4c.db`
2. **API keys via env vars** - Endpoint stores env var NAME, actual key in `~/.srl4c/.env`
3. **Docker-style short IDs** - UUIDs but users can type `a4f` instead of full `a4f7c8d2-...`
4. **Reuse existing code** - CLI imports from `src/core/`, no duplication
5. **Judges are internal** - Users don't configure judge models, that's our recipe

## Files to Know

| File | Purpose |
|------|---------|
| `src/core/criteria_loader.py` | Load principles from registry |
| `src/core/judge.py` | Multi-judge evaluation system |
| `src/core/weighting_system.py` | Score aggregation |
| `assets/criteria_registry.yml` | Principle registry with presets |
| `config.yml` | Main config (judges, weights, paths) |
| `srl4c/PLAN.md` | Full CLI implementation plan |
| `srl4c/src/srl4c/cli/main.py` | All Typer commands |

## Next Steps to Implement

1. **SQLite layer** (`srl4c/src/srl4c/db/`)
   - Models for endpoints, attacks, records, scores, evaluations, guardrails
   - UUID prefix matching utility

2. **Adapters** (`srl4c/src/srl4c/adapters/`)
   - `OpenAIAdapter`: POST to /v1/chat/completions
   - `SimpleAdapter`: POST to custom URL with configurable fields

3. **Endpoint commands** - Wire up to SQLite + adapters

4. **Attack command** - Send prompts, store responses

5. **Score command** - Integrate with existing `judge.py` and `weighting_system.py`

6. **Guardrails commands** - Integrate with existing `tools/generate_guardrails.py`

## Testing

```bash
# From srl4c/ directory
uv run python -m srl4c.cli.main <command>

# After installing
srl4c <command>
```

## Don't Forget

- Always use `uv`, never `pip`
- CLI reuses existing code via `sys.path.insert(0, str(REPO_ROOT / "src"))`
- See `srl4c/PLAN.md` for detailed examples with realistic IDs
