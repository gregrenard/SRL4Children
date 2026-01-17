"""
E2E tests for CLI resource commands (non-pipeline).

Tests: init, dataset, matrices, criteria, judges, generators, config, etc.
"""

import os
import sys
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_cli(args: list[str], env: dict = None, timeout: float = 60) -> subprocess.CompletedProcess:
    """Run CLI command and return result"""
    cmd = [sys.executable, "-m", "srl4c.cli.main"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        cwd=str(PROJECT_ROOT),
    )
    return result


class TestInitCLI:
    """Tests for init command"""

    def test_init_creates_config_dir(self, tmp_path):
        """init command creates ~/.srl4c directory"""
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        env = os.environ.copy()
        env["HOME"] = str(fake_home)
        env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

        result = run_cli(["init"], env=env)
        assert result.returncode == 0

        config_dir = fake_home / ".srl4c"
        assert config_dir.exists()


class TestDatasetCLI:
    """Tests for dataset commands"""

    def test_dataset_show(self, cli_env):
        """dataset show displays dataset details"""
        env = cli_env["env"]
        result = run_cli(["dataset", "show", "emotional_reliance"], env=env)
        assert result.returncode == 0
        assert "emotional_reliance" in result.stdout.lower()

    def test_dataset_validate(self, cli_env, tmp_path):
        """dataset validate checks CSV format"""
        env = cli_env["env"]

        # Create valid CSV
        csv_file = tmp_path / "valid.csv"
        csv_file.write_text("""PromptID,Category,Prompt
test-001,emotional_reliance.interactional.flattery,"Test prompt"
""")

        result = run_cli(["dataset", "validate", str(csv_file)], env=env)
        assert result.returncode == 0

    def test_dataset_add(self, cli_env, tmp_path):
        """dataset add creates custom dataset"""
        env = cli_env["env"]

        # Create CSV
        csv_file = tmp_path / "custom.csv"
        csv_file.write_text("""PromptID,Category,Prompt
custom-001,emotional_reliance.interactional.flattery,"Custom prompt"
custom-002,emotional_reliance.relational.exclusivity,"Another prompt"
""")

        result = run_cli(["dataset", "add", str(csv_file), "--name", "cli-test-dataset"], env=env)
        assert result.returncode == 0

        # Verify it exists
        result = run_cli(["dataset", "list"], env=env)
        assert "cli-test-dataset" in result.stdout


class TestEndpointTestCLI:
    """Tests for endpoint test command"""

    def test_endpoint_test(self, cli_env):
        """endpoint test checks connectivity"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        # Add endpoint first
        run_cli(["endpoint", "add", "simple", "--name", "test-conn-bot", "--url", endpoint_url], env=env)

        # Test it
        result = run_cli(["endpoint", "test", "test-conn-bot"], env=env)
        assert result.returncode == 0

    def test_endpoint_test_with_prompt(self, cli_env):
        """endpoint test with custom prompt"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        run_cli(["endpoint", "add", "simple", "--name", "test-prompt-bot", "--url", endpoint_url], env=env)

        result = run_cli(["endpoint", "test", "test-prompt-bot", "--prompt", "Hello there!"], env=env)
        assert result.returncode == 0


class TestScoreCLI:
    """Tests for score commands"""

    def test_score_failures(self, cli_env):
        """score failures shows failing evaluations"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        # Create endpoint, attack, score
        run_cli(["endpoint", "add", "simple", "--name", "failures-bot", "--url", endpoint_url], env=env)
        run_cli(["attack", "run", "--endpoint", "failures-bot", "--dataset", "test_mini"], env=env, timeout=180)

        # Get attack ID
        result = run_cli(["attack", "list"], env=env)
        import re
        attack_id = None
        for line in result.stdout.split("\n"):
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                attack_id = match.group(1)
                break

        # Run score
        run_cli(["score", "run", attack_id, "--age", "child", "--matrix", "flat"], env=env, timeout=180)

        # Get score ID
        result = run_cli(["score", "list"], env=env)
        score_id = None
        for line in result.stdout.split("\n"):
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                score_id = match.group(1)
                break

        # Check failures
        result = run_cli(["score", "failures", score_id], env=env)
        assert result.returncode == 0


class TestGuardrailsCLI:
    """Tests for guardrails commands"""

    def test_guardrails_show(self, cli_env):
        """guardrails show displays rules"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        # Full pipeline
        run_cli(["endpoint", "add", "simple", "--name", "show-guard-bot", "--url", endpoint_url], env=env)
        run_cli(["attack", "run", "--endpoint", "show-guard-bot", "--dataset", "test_mini"], env=env, timeout=180)

        import re
        result = run_cli(["attack", "list"], env=env)
        attack_id = None
        for line in result.stdout.split("\n"):
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                attack_id = match.group(1)
                break

        run_cli(["score", "run", attack_id, "--age", "child", "--matrix", "flat"], env=env, timeout=180)

        result = run_cli(["score", "list"], env=env)
        score_id = None
        for line in result.stdout.split("\n"):
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                score_id = match.group(1)
                break

        run_cli(["guardrails", "generate", score_id], env=env, timeout=180)

        result = run_cli(["guardrails", "list"], env=env)
        set_id = None
        for line in result.stdout.split("\n"):
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                set_id = match.group(1)
                break

        if set_id:
            result = run_cli(["guardrails", "show", set_id], env=env)
            assert result.returncode == 0


class TestCriteriaCLI:
    """Tests for criteria commands"""

    def test_criteria_show(self, cli_env):
        """criteria show displays criterion details"""
        env = cli_env["env"]
        result = run_cli(["criteria", "show", "emotional_reliance.interactional.flattery"], env=env)
        assert result.returncode == 0
        assert "flattery" in result.stdout.lower()


class TestJudgesCLI:
    """Tests for judges commands"""

    def test_judges_show(self, cli_env):
        """judges show displays config content"""
        env = cli_env["env"]

        # List first
        result = run_cli(["judges", "list"], env=env)
        assert result.returncode == 0

        # Show fake.judges (created in fixture)
        result = run_cli(["judges", "show", "fake.judges"], env=env)
        assert result.returncode == 0

    def test_judges_use(self, cli_env):
        """judges use switches active config"""
        env = cli_env["env"]
        result = run_cli(["judges", "use", "fake.judges"], env=env)
        assert result.returncode == 0


class TestEvalJudgesCLI:
    """Tests for eval-judges commands"""

    def test_eval_judges_list(self, cli_env):
        """eval-judges list shows evaluation judges"""
        env = cli_env["env"]
        result = run_cli(["eval-judges", "list"], env=env)
        assert result.returncode == 0


class TestGeneratorsCLI:
    """Tests for generators commands"""

    def test_generators_list(self, cli_env):
        """generators list shows available configs"""
        env = cli_env["env"]
        result = run_cli(["generators", "list"], env=env)
        assert result.returncode == 0


class TestMatricesCLI:
    """Tests for matrices commands"""

    def test_matrices_list(self, cli_env):
        """matrices list shows scoring matrices"""
        env = cli_env["env"]
        result = run_cli(["matrices", "list"], env=env)
        assert result.returncode == 0
        # Should show built-in matrices
        assert "educational" in result.stdout.lower() or "flat" in result.stdout.lower()

    def test_matrices_show(self, cli_env):
        """matrices show displays matrix details"""
        env = cli_env["env"]
        result = run_cli(["matrices", "show", "educational"], env=env)
        assert result.returncode == 0

    def test_matrices_create(self, cli_env):
        """matrices create makes new matrix"""
        env = cli_env["env"]
        result = run_cli(["matrices", "create", "cli-test-matrix", "--description", "Test"], env=env)
        assert result.returncode == 0

        # Verify exists
        result = run_cli(["matrices", "list"], env=env)
        assert "cli-test-matrix" in result.stdout

    def test_matrices_clone(self, cli_env):
        """matrices clone duplicates existing matrix"""
        env = cli_env["env"]
        result = run_cli(["matrices", "clone", "educational", "--name", "cli-cloned-matrix"], env=env)
        assert result.returncode == 0

        # Verify exists
        result = run_cli(["matrices", "list"], env=env)
        assert "cli-cloned-matrix" in result.stdout

    def test_matrices_delete(self, cli_env):
        """matrices delete removes custom matrix"""
        env = cli_env["env"]

        # Create first
        run_cli(["matrices", "create", "to-delete-matrix"], env=env)

        # Delete
        result = run_cli(["matrices", "delete", "to-delete-matrix", "--yes"], env=env)
        assert result.returncode == 0

        # Verify gone
        result = run_cli(["matrices", "list"], env=env)
        assert "to-delete-matrix" not in result.stdout


class TestConfigCLI:
    """Tests for config commands"""

    def test_config_show(self, cli_env):
        """config show displays current config"""
        env = cli_env["env"]
        result = run_cli(["config", "show"], env=env)
        assert result.returncode == 0
