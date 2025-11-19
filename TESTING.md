# 🧪 SRL4Children - Testing Strategy

This document describes the testing strategy to ensure quality and reliability of the SRL4Children system.

---

## 🎯 Testing Objectives

1. **Functional validation**: Verify each module works correctly
2. **Regression**: Ensure modifications don't introduce bugs
3. **Performance**: Measure and optimize processing times
4. **Security**: Prevent sensitive data leaks

---

## 📊 Test Structure

### Test Levels

```
tests/
├── unit/                  # Unit tests (individual functions)
│   ├── test_judge.py
│   ├── test_criteria_loader.py
│   ├── test_weighting_system.py
│   └── test_clients.py
├── integration/           # Integration tests (combined modules)
│   ├── test_benchmark_flow.py
│   ├── test_guardrail_generation.py
│   └── test_ollama_connection.py
├── e2e/                   # End-to-end tests (complete scenarios)
│   └── test_full_pipeline.py
├── fixtures/              # Test data
│   ├── sample_records.json
│   ├── mock_responses.json
│   └── test_datasets.csv
└── conftest.py            # Pytest configuration
```

---

## 🔬 Unit Tests

### 1. Module `judge.py`

**File**: `tests/unit/test_judge.py`

**Objectives**:
- Validate JSON parsing of judge responses
- Test error handling for malformed formats
- Verify consistency calculation (variance, agreement)
- Test multi-level weighting

**Test example**:
```python
def test_parse_and_validate_valid_json():
    raw = '{"score": 2.5, "explanation": "Test", "evidence_extracts": ["quote1"]}'
    result = parse_and_validate(raw, repair_model="qwen3:8b", host="localhost", port=11434)
    assert result["score"] == 2.5
    assert result["explanation"] == "Test"
    assert len(result["evidence_extracts"]) == 1

def test_parse_and_validate_invalid_json_repair():
    raw = "This is not JSON at all"
    result = parse_and_validate(raw, repair_model="qwen3:8b", host="localhost", port=11434)
    assert "score" in result
    assert 0.0 <= result["score"] <= 5.0
```

### 2. Module `criteria_loader.py`

**File**: `tests/unit/test_criteria_loader.py`

**Objectives**:
- Verify registry loading
- Test criteria selection by category/subcategory
- Validate prompt construction with interpolation

**Test example**:
```python
def test_load_registry():
    loader = CriteriaLoader()
    registry = loader.load_registry()
    assert "criteria" in registry
    assert len(registry["criteria"]) > 0

def test_select_criteria_by_category():
    loader = CriteriaLoader()
    criteria = loader.select_criteria(selection="safety")
    assert all(c.category == "safety" for c in criteria)
```

### 3. Module `weighting_system.py`

**File**: `tests/unit/test_weighting_system.py`

**Objectives**:
- Verify weights sum to 1.0 at each level
- Test aggregated score calculation
- Validate cascading weights (category → subcategory → criterion)

**Test example**:
```python
def test_category_weights_sum_to_one():
    ws = WeightingSystem(config)
    weights = ws.get_category_weights()
    assert abs(sum(weights.values()) - 1.0) < 0.0001

def test_compute_weighted_score():
    ws = WeightingSystem(config)
    scores = {"safety": 2.0, "age": 3.0, "relevance": 4.0}
    weighted = ws.compute_weighted_score(scores)
    assert 0.0 <= weighted <= 5.0
```

### 4. Module `clients.py`

**File**: `tests/unit/test_clients.py`

**Objectives**:
- Test API calls with mocks (no real API)
- Verify timeout handling
- Validate response formats

**Test example**:
```python
@patch('src.connectors.clients.ollama_generate')
def test_ollama_generate_success(mock_ollama):
    mock_ollama.return_value = '{"score": 3.0}'
    result = ollama_generate("test prompt", "qwen3:8b")
    assert result == '{"score": 3.0}'

@patch('src.connectors.clients.ollama_generate')
def test_ollama_generate_timeout(mock_ollama):
    mock_ollama.side_effect = TimeoutError("Connection timeout")
    with pytest.raises(TimeoutError):
        ollama_generate("test prompt", "qwen3:8b")
```

---

## 🔗 Integration Tests

### 1. Complete benchmark pipeline

**File**: `tests/integration/test_benchmark_flow.py`

**Scenario**:
1. Load minimal dataset (3 prompts)
2. Run benchmark with 1 judge, 1 pass
3. Verify JSON files are created
4. Validate output JSON structure

**Example**:
```python
def test_full_benchmark_minimal():
    config = load_test_config()
    dataset = "tests/fixtures/mini_dataset.csv"

    # Run benchmark
    run_benchmark(config, dataset)

    # Verify outputs exist
    output_dir = Path("outputs")
    assert output_dir.exists()

    records = list(output_dir.glob("**/record_*.json"))
    assert len(records) == 3
```

### 2. Guardrail generation

**File**: `tests/integration/test_guardrail_generation.py`

**Scenario**:
1. Create a record with scores > 0 (failures)
2. Launch guardrail generation
3. Verify guardrails are consistent with criteria
4. Validate output format

**Example**:
```python
def test_generate_guardrails_for_failing_record():
    record_path = "tests/fixtures/failing_record.json"

    # Generate guardrails
    output = generate_guardrails(
        record_path,
        provider="openai",
        model="gpt-5-mini"
    )

    assert "guardrails" in output
    assert len(output["guardrails"]) > 0

    # Verify guardrail structure
    guardrail = output["guardrails"][0]
    assert "rule" in guardrail
    assert "criterion_id" in guardrail
```

---

## 🌐 End-to-End Tests

### 1. Complete scenario

**File**: `tests/e2e/test_full_pipeline.py`

**Scenario**:
1. Start with clean dataset
2. Run full benchmark (3 judges, 3 passes)
3. Generate guardrails for all records
4. Replay prompts with guardrails
5. Verify score improvements

**Estimated duration**: 30-45 minutes (can be marked `@pytest.mark.slow`)

---

## ⚙️ Pytest Configuration

**File**: `tests/conftest.py`

```python
import pytest
from pathlib import Path
import shutil

@pytest.fixture(scope="session")
def test_output_dir():
    """Create temporary output directory for tests"""
    output_dir = Path("tests/outputs")
    output_dir.mkdir(exist_ok=True)
    yield output_dir
    # Cleanup after tests
    shutil.rmtree(output_dir)

@pytest.fixture
def mock_config():
    """Simplified test configuration"""
    return {
        "judge_system": {
            "judges": {
                "judge_test": {
                    "model": "qwen3:8b",
                    "options": {"temperature": 0.1}
                }
            },
            "evaluation": {"n_passes": 1}
        }
    }

@pytest.fixture
def sample_record():
    """Test record with consistent data"""
    return {
        "record_data": {
            "prompt": "What is friendship?",
            "reply": "Friendship is a bond...",
            "maturity": "9-12",
            "model": "qwen3:8b"
        }
    }
```

---

## 🚀 Running Tests

### Install test dependencies

```bash
pip install pytest pytest-asyncio pytest-cov
```

### Run all tests

```bash
pytest tests/ -v
```

### Run unit tests only

```bash
pytest tests/unit/ -v
```

### Run with code coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

### Run only fast tests (skip e2e)

```bash
pytest tests/ -m "not slow"
```

---

## 📊 Quality Metrics

### Coverage Goals

- **Code coverage**: ≥ 80%
- **Critical modules** (judge, criteria_loader): ≥ 90%
- **Passing tests**: 100%

### CI/CD (upcoming)

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ --cov=src
```

---

## 🔒 Security Tests

### 1. Secrets verification

**Objective**: Ensure no API keys are committed

```bash
# Add pre-commit hook
pip install pre-commit
```

**File**: `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### 2. Sanitization testing

**Objective**: Verify logs don't contain sensitive data

```python
def test_logs_dont_contain_api_keys():
    # Simulate a call
    with open("logs/test.log", "r") as f:
        content = f.read()

    # Verify no API keys are present
    assert "sk-" not in content
    assert "OPENAI_API_KEY" not in content
```

---

## 📅 Testing Roadmap

### Phase 1 (immediate)
- [x] Define test structure
- [ ] Implement basic unit tests (judge, criteria_loader)
- [ ] Configure pytest

### Phase 2 (short term)
- [ ] Integration tests for complete pipeline
- [ ] Guardrail generation tests
- [ ] Coverage ≥ 60%

### Phase 3 (medium term)
- [ ] Complete e2e tests
- [ ] CI/CD on GitHub Actions
- [ ] Coverage ≥ 80%

### Phase 4 (long term)
- [ ] Performance tests (benchmarking)
- [ ] Load tests (stress testing)
- [ ] Automated security tests

---

## 🆘 Test Troubleshooting

### Issue: "Ollama not responding"

**Solution**: Use mocks for unit tests
```python
@patch('src.connectors.clients.ollama_generate')
def test_with_mock(mock_ollama):
    mock_ollama.return_value = '{"score": 3.0}'
    # Your test here
```

### Issue: "Tests too slow"

**Solution**: Mark slow tests
```python
@pytest.mark.slow
def test_full_benchmark():
    # Long test...
```

Then run: `pytest -m "not slow"`

---

**SRL4Children v1.1.0** - Testing Strategy
*Designed by Freedom.AI | Greg Renard*
