# SRL4C Pipeline Feature Implementation

## Summary

Successfully implemented a complete `run-pipeline` command for the SRL4C CLI and a corresponding `POST /api/pipeline` REST API endpoint. These features allow users to run the full SRL4C workflow (endpoint setup → attack → scoring → guardrails generation) in a single command with sensible defaults.

## Changes Made

### 1. CLI Command: `srl4c run-pipeline`

**File**: [src/srl4c/cli/commands/pipeline.py](src/srl4c/cli/commands/pipeline.py)
**Main Entry Point**: [src/srl4c/cli/main.py](src/srl4c/cli/main.py)

#### Command Signature
```bash
srl4c run-pipeline NAME --type {simple|openai} --url ENDPOINT_URL [OPTIONS]
```

#### Required Arguments
- `name`: Friendly name for the endpoint
- `--url` / `-u`: Endpoint URL (base URL for openai, full URL for simple)
- `--type` / `-t`: Endpoint type (default: `simple`)

#### Optional Arguments
- `--api-key-env`: Environment variable containing API key
- `--base-url`: Base URL (for openai type)
- `--dataset`: Dataset name (default: `anthropomorphism_question_mini`)
- `--age`: Age context (default: `child`)
- `--weights`: Weight preset (default: `balanced`)
- `--request-field`: JSON request field (default: `message`, simple type only)
- `--response-field`: JSON response field (default: `response`, simple type only)
- `--max-rules`: Max guardrails per criterion (default: `3`)
- `--max-total`: Max total guardrails (default: `20`)
- `--deploy-worker`: Deploy Cloudflare Worker (default: `false`)

#### Workflow
1. **Create/Connect Endpoint**: Reuses existing endpoint or creates new one
2. **Run Attack**: Executes adversarial prompts from dataset
3. **Score Results**: Evaluates responses using judges
4. **Generate Guardrails**: Creates safety rules from failures
5. **Optional**: Deploy guardrails as Cloudflare Worker (currently reserved for future implementation)

### 2. REST API Endpoint: `POST /api/pipeline/`

**File**: [src/srl4c/api/routes/pipeline.py](src/srl4c/api/routes/pipeline.py)
**Schema**: [src/srl4c/api/schemas.py](src/srl4c/api/schemas.py) - `PipelineRequest` and `PipelineResponse`
**Registration**: [src/srl4c/api/main.py](src/srl4c/api/main.py)

#### Request Body
```json
{
  "name": "my-app",
  "endpoint_type": "simple",
  "endpoint_url": "https://example.com/chat",
  "api_key_env": "MY_API_KEY",
  "dataset": "anthropomorphism_question_mini",
  "age": "child",
  "weights": "balanced",
  "request_field": "message",
  "response_field": "response",
  "max_rules": 3,
  "max_total": 20,
  "deploy_worker": false
}
```

#### Response (201 Created)
```json
{
  "endpoint_id": "abc12345",
  "attack_id": "def67890",
  "score_id": "ghi11121",
  "guardrail_set_id": "jkl31415",
  "status": "completed",
  "final_score": 2.5,
  "message": "Pipeline completed successfully"
}
```

### 3. Tests

**File**: [tests/test_pipeline.py](tests/test_pipeline.py)

#### CLI Tests
- `test_pipeline_help`: Verify help text works
- `test_pipeline_run_simple_endpoint`: Full pipeline with simple endpoint
- `test_pipeline_creates_endpoint`: Verify endpoint creation
- `test_pipeline_with_custom_age_context`: Test with different age context
- `test_pipeline_with_guardrail_options`: Test custom guardrail parameters

#### API Tests
- `test_pipeline_api_endpoint`: Basic pipeline execution
- `test_pipeline_api_required_fields`: Validation of required fields
- `test_pipeline_api_with_worker_deployment_flag`: Test worker deployment flag
- `test_pipeline_api_response_structure`: Verify response structure

**All 9 tests pass successfully.**

## Code Quality

- **Formatting**: Applied with `ruff format`
- **Linting**: Verified with `ruff check` (all checks pass)
- **Type Annotations**: Uses modern Python `X | None` syntax (Python 3.10+)
- **Error Handling**: Proper exception handling with informative error messages
- **Logging**: Integrated with existing Logger system for audit trails

## Design Decisions

1. **Sane Defaults**: All options except `name` and `--url` have sensible defaults based on common use cases
2. **Endpoint Reuse**: Command checks for existing endpoint to avoid duplication
3. **Progress Display**: Visual progress bars for long-running operations (attack, scoring)
4. **Worker Deployment**: Flag is available but implementation is reserved for future (would require Cloudflare integration)
5. **Separation of Concerns**: CLI and API logic is separated, with shared core functions in `srl4c.core.guardrails`, `srl4c.core.attack`, and `srl4c.core.score`
6. **Logging Integration**: All pipeline operations are logged through the Logger system for traceability

## Files Modified

1. **New Files**:
   - `src/srl4c/cli/commands/pipeline.py` - CLI command implementation
   - `src/srl4c/api/routes/pipeline.py` - API route implementation
   - `tests/test_pipeline.py` - Comprehensive test suite

2. **Modified Files**:
   - `src/srl4c/cli/main.py` - Added `run-pipeline` command registration
   - `src/srl4c/api/main.py` - Registered pipeline router
   - `src/srl4c/api/schemas.py` - Added `PipelineRequest` and `PipelineResponse` schemas

## Usage Examples

### CLI Example
```bash
# Run full pipeline with defaults
srl4c run-pipeline my-chatbot --url http://localhost:8000/chat

# Run with custom dataset and age context
srl4c run-pipeline my-chatbot \
  --url http://localhost:8000/chat \
  --dataset test_mini \
  --age teen

# Run with custom guardrail options
srl4c run-pipeline my-chatbot \
  --url http://localhost:8000/chat \
  --max-rules 5 \
  --max-total 30
```

### API Example
```bash
curl -X POST http://localhost:8000/api/pipeline/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-chatbot",
    "endpoint_type": "simple",
    "endpoint_url": "http://localhost:8000/chat",
    "dataset": "test_mini",
    "age": "child"
  }'
```

## Testing

All tests use the existing test infrastructure with fake endpoint and judge servers:
- No real LLM calls are made during testing
- Tests are isolated with temporary configuration directories
- Tests complete in ~45 seconds for the full suite
