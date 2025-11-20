# 🤝 Contributing to SRL4Children

Thank you for your interest in contributing to SRL4Children! This project aims to create a safety standard for child-facing AI systems, and we welcome contributions from developers, researchers, educators, and child safety experts.

---

## 🎯 How You Can Contribute

### 1. **Code Contributions**
- Implement new Design Principles
- Improve performance (parallelization, caching)
- Add test coverage
- Fix bugs
- Refactor code

### 2. **Research Contributions**
- Validate existing Design Principles scientifically
- Create new Design Principles based on research
- Contribute golden datasets with ground truth labels
- Benchmark against other safety approaches

### 3. **Documentation**
- Improve README, guides, tutorials
- Translate documentation to other languages
- Create video tutorials or demos
- Write blog posts about SRL4Children

### 4. **Testing & Quality**
- Write unit tests
- Create integration tests
- Report bugs with detailed reproduction steps
- Test on different platforms (Windows, Linux, macOS)

---

## 🚀 Getting Started

### 1. Fork & Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/SRL4Children.git
cd SRL4Children
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov black ruff pre-commit
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

---

## 💻 Development Workflow

### Code Style

We use **Black** for formatting and **Ruff** for linting:

```bash
# Format code
black src/ tools/

# Check linting
ruff check src/ tools/

# Fix auto-fixable issues
ruff check --fix src/ tools/
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run only fast tests (skip slow e2e)
pytest tests/ -m "not slow"
```

**Note:** Currently, the test suite is being developed. See [TESTING.md](TESTING.md) for the testing roadmap.

### Type Hints

Please use type hints for all function signatures:

```python
from typing import Dict, List, Optional

def my_function(param: str, optional_param: Optional[int] = None) -> Dict[str, Any]:
    """
    Clear docstring explaining what this function does.

    Args:
        param: Description of param
        optional_param: Description of optional_param

    Returns:
        Description of return value
    """
    pass
```

---

## 📝 Commit Guidelines

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(criteria): add new parasocial bond detection criterion

This criterion detects when the AI creates exclusive emotional bonds
with children by claiming special relationships.

Closes #42
```

```bash
fix(judge): handle NaN values in consistency calculation

Previously, NaN values would crash the weighting system. Now they
are filtered out before variance calculation.

Fixes #15
```

---

## 🧪 Adding Tests

### Test Structure

```
tests/
├── unit/           # Test individual functions/classes
├── integration/    # Test module interactions
└── e2e/            # Test complete workflows
```

### Writing a Test

```python
# tests/unit/test_judge.py

import pytest
from src.core.judge import parse_and_validate

def test_parse_valid_json():
    """Test parsing valid JSON response from judge"""
    raw = '{"score": 3.0, "explanation": "Test", "evidence_extracts": ["quote"]}'
    result = parse_and_validate(raw, repair_model="qwen3:8b", host="localhost", port=11434)

    assert result["score"] == 3.0
    assert result["explanation"] == "Test"
    assert len(result["evidence_extracts"]) == 1

def test_parse_invalid_json_repair():
    """Test JSON repair for malformed responses"""
    raw = "This is not JSON"
    result = parse_and_validate(raw, repair_model="qwen3:8b", host="localhost", port=11434)

    assert "score" in result
    assert 0.0 <= result["score"] <= 5.0
```

---

## 🔬 Adding New Design Principles

### 1. Create Scientific Validation

Before adding a new Design Principle, ensure it is:
- **Scientifically validated** through research or expert consensus
- **Measurable** with clear scoring criteria (0-5 scale)
- **Age-appropriate** with guidance for different age groups
- **Culturally sensitive** or adaptable to different contexts

### 2. Create the `.prompt` File

```yaml
# assets/criteria/category/subcategory/principle_name__v1_0.prompt

role: "You are an expert evaluator for [specific aspect]"

task: "Evaluate whether the model response [specific behavior to detect]"

age_context: "Child is {age_group} years old"

scoring_guide: |
  Score 0 – [Most harmful behavior]
  Score 1 – [Problematic behavior]
  Score 2 – [Neutral with concerns]
  Score 3 – [Acceptable with minor issues]
  Score 4 – [Good practice]
  Score 5 – [Exemplary practice]

examples: |
  Example 1:
  PROMPT: "[Example child question]"
  RESPONSE: "[Example problematic response]"
  SCORE: 0
  EXPLANATION: "[Why this is harmful]"
  EVIDENCE_EXTRACTS: ["quote 1", "quote 2"]

  Example 2:
  PROMPT: "[Example child question]"
  RESPONSE: "[Example good response]"
  SCORE: 5
  EXPLANATION: "[Why this is exemplary]"
  EVIDENCE_EXTRACTS: ["quote"]

output_format: |
  {{
    "score": 0-5,
    "explanation": "Your detailed reasoning for this score",
    "evidence_extracts": ["exact quote 1", "exact quote 2"]
  }}

CONTENT TO ANALYZE:

PROMPT: {prompt}
RESPONSE: {response}
```

### 3. Update `criteria_registry.yml`

```yaml
criteria:
  - id: "category.subcategory.principle_name__v1_0"
    category: "category"
    subcategory: "subcategory"
    name: "Principle Name"
    description: "Brief description of what this principle detects"
    version: "1.0"
    validated: true  # Set to true only if scientifically validated
    validation_source: "Research paper DOI or expert team name"
```

### 4. Update `Design_Principles.md`

```markdown
## Category

- **principle_name** (`category.subcategory.principle_name__v1_0`) – Description
```

### 5. Create Test Cases

Create attack prompts in `data/` that specifically test this principle.

---

## 🐛 Reporting Bugs

Please use the [GitHub issue tracker](https://github.com/everyoneai/SRL4Children/issues) and include:

1. **Environment**: OS, Python version, SRL4Children version
2. **Steps to reproduce**: Minimal code/config to reproduce the issue
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Error messages**: Full stack trace if applicable

---

## 🌍 Translation & Localization

We welcome translations of:
- Documentation (README, guides)
- Design Principles (for cultural adaptation)
- Error messages
- Dashboard UI

Please create a new directory `doc/translations/[LANGUAGE_CODE]/` and submit a PR.

---

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of background, identity, or experience level.

### Expected Behavior

- Be respectful and constructive
- Focus on what's best for child safety
- Welcome newcomers and help them get started
- Give and receive feedback gracefully

### Unacceptable Behavior

- Harassment, discrimination, or exclusionary behavior
- Trolling, insulting comments, or personal attacks
- Publishing others' private information
- Any conduct that would be inappropriate around children

### Enforcement

Violations can be reported to [maintainer email]. All reports will be reviewed and investigated.

---

## 🏆 Recognition

Contributors will be:
- Listed in `CONTRIBUTORS.md`
- Mentioned in release notes for significant contributions
- Credited in any academic papers using their work (if desired)

---

## 📞 Questions?

- **GitHub Discussions**: For general questions and discussions
- **GitHub Issues**: For bug reports and feature requests
- **Email**: [contact email if available]

---

## 📄 License

By contributing to SRL4Children, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

**Thank you for helping make AI safer for children! 🌟**

Every contribution, no matter how small, makes a difference in protecting the well-being and safety of our children.
