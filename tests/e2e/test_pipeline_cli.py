"""
E2E test for full SRL4C pipeline via CLI.

Tests: endpoint → attack → score → guardrails
Uses fake endpoint and fake judge servers (no real LLMs).
"""

import os
import re
import sys
import time
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_cli(args: list[str], env: dict = None, timeout: float = 120) -> subprocess.CompletedProcess:
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


def extract_id_from_output(output: str, pattern: str = r"([0-9a-f]{8})") -> str:
    """Extract an ID from CLI output"""
    match = re.search(pattern, output)
    if match:
        return match.group(1)
    return None


class TestPipelineCLI:
    """Full pipeline test via CLI"""

    @pytest.fixture
    def cli_env(self, tmp_path, fake_endpoint_server, fake_judge_server):
        """Create isolated environment for CLI tests"""
        # Create isolated home directory
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        # Create .srl4c directory
        config_dir = fake_home / ".srl4c"
        config_dir.mkdir()

        # Create fake.judges config pointing to test server
        fake_judges_content = f"""# Test Judge Configuration
n_passes: 1

judges:
  fake_judge:
    provider_openai_base_url: {fake_judge_server['base_url']}
    model: fake-model
"""
        (config_dir / "fake.judges").write_text(fake_judges_content)

        # Create settings to use fake.judges
        settings_content = "active_judges: fake.judges\n"
        (config_dir / "settings.yaml").write_text(settings_content)

        # Patch paths before importing db modules
        import srl4c.paths
        import srl4c.db
        srl4c.paths.USER_CONFIG_DIR = config_dir
        srl4c.db.SRL4C_HOME = config_dir
        srl4c.db.DB_PATH = config_dir / "srl4c.db"

        # Also patch in models module
        import srl4c.db.models
        srl4c.db.models.DB_PATH = config_dir / "srl4c.db"

        # Initialize database with sync (populates built-in datasets/judges)
        from srl4c.db.models import init_db
        from srl4c.core.datasets import create_dataset

        init_db()

        # Create test dataset in DB
        test_dataset_src = PROJECT_ROOT / "tests" / "fixtures" / "test_dataset.csv"
        csv_content = test_dataset_src.read_text()
        try:
            create_dataset(
                name="test_mini",
                csv_content=csv_content,
                description="Test dataset for E2E tests",
            )
        except ValueError:
            pass  # Already exists

        # Create environment with modified HOME and SRL4C_HOME
        env = os.environ.copy()
        env["HOME"] = str(fake_home)
        env["SRL4C_HOME"] = str(config_dir)  # Explicit path to config dir
        env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

        return {
            "env": env,
            "config_dir": config_dir,
            "endpoint_url": fake_endpoint_server["url"],
        }

    def test_cli_help(self):
        """Verify CLI is accessible"""
        result = run_cli(["--help"])
        assert result.returncode == 0
        assert "srl4c" in result.stdout.lower() or "safety" in result.stdout.lower()

    def test_full_pipeline(self, cli_env, fake_endpoint_server):
        """Run complete pipeline: endpoint → attack → score → guardrails"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        # Step 1: Add endpoint
        result = run_cli([
            "endpoint", "add", "simple",
            "--name", "test-bot",
            "--url", endpoint_url,
        ], env=env)
        assert result.returncode == 0, f"Failed to add endpoint: {result.stderr}\n{result.stdout}"
        assert "test-bot" in result.stdout.lower() or "created" in result.stdout.lower()

        # Verify endpoint exists
        result = run_cli(["endpoint", "list"], env=env)
        assert result.returncode == 0
        assert "test-bot" in result.stdout

        # Step 2: Run attack
        result = run_cli([
            "attack", "run",
            "--endpoint", "test-bot",
            "--dataset", "test_mini",
        ], env=env, timeout=180)
        assert result.returncode == 0, f"Attack failed: {result.stderr}\n{result.stdout}"

        # Extract attack ID from output
        # Look for ID pattern in output (8 hex chars after "Attack" or in completion message)
        attack_id = None
        for line in result.stdout.split("\n"):
            if "attack" in line.lower():
                match = re.search(r"([0-9a-f]{8})", line)
                if match:
                    attack_id = match.group(1)
                    break

        # Also check attack list to get full ID
        result = run_cli(["attack", "list"], env=env)
        assert result.returncode == 0
        # Find the first attack ID (should be our test attack)
        for line in result.stdout.split("\n"):
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                attack_id = match.group(1)
                break

        assert attack_id is not None, f"Could not find attack ID in output:\n{result.stdout}"

        # Step 3: Run score
        result = run_cli([
            "score", "run", attack_id,
            "--age", "child",
            "--matrix", "flat",
        ], env=env, timeout=180)
        assert result.returncode == 0, f"Score failed: {result.stderr}\n{result.stdout}"

        # Get score ID from list
        result = run_cli(["score", "list"], env=env)
        assert result.returncode == 0
        score_id = None
        for line in result.stdout.split("\n"):
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                score_id = match.group(1)
                break

        assert score_id is not None, f"Could not find score ID in output:\n{result.stdout}"

        # Step 4: Generate guardrails
        result = run_cli([
            "guardrails", "generate", score_id,
            "--max-rules", "3",
            "--max-total", "10",
        ], env=env, timeout=180)
        assert result.returncode == 0, f"Guardrails failed: {result.stderr}\n{result.stdout}"

        # Verify guardrails were created
        result = run_cli(["guardrails", "list"], env=env)
        assert result.returncode == 0

        # Step 5: Verify data consistency
        # Check attack details
        result = run_cli(["attack", "show", attack_id], env=env)
        assert result.returncode == 0
        assert "completed" in result.stdout.lower()

        # Check score details
        result = run_cli(["score", "show", score_id], env=env)
        assert result.returncode == 0
        assert "completed" in result.stdout.lower()

    def test_endpoint_add_and_list(self, cli_env):
        """Test endpoint CRUD operations"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        # Add
        result = run_cli([
            "endpoint", "add", "simple",
            "--name", "my-bot",
            "--url", endpoint_url,
        ], env=env)
        assert result.returncode == 0

        # List
        result = run_cli(["endpoint", "list"], env=env)
        assert result.returncode == 0
        assert "my-bot" in result.stdout

    def test_dataset_list(self, cli_env):
        """Test dataset listing shows built-in datasets"""
        env = cli_env["env"]

        result = run_cli(["dataset", "list"], env=env)
        assert result.returncode == 0
        # Should show built-in datasets
        assert "emotional_reliance" in result.stdout.lower()

    def test_judges_list(self, cli_env):
        """Test judge configuration listing"""
        env = cli_env["env"]

        result = run_cli(["judges", "list"], env=env)
        assert result.returncode == 0
        assert "fake.judges" in result.stdout

    def test_criteria_list(self, cli_env):
        """Test criteria listing"""
        env = cli_env["env"]

        result = run_cli(["criteria", "list"], env=env)
        assert result.returncode == 0
        # Should list some criteria (emotional reliance behaviors)
        assert "emotional_reliance" in result.stdout.lower() or "anthropomorphic" in result.stdout.lower()

    def test_score_report(self, cli_env):
        """Test score report generation via CLI"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        # Create endpoint
        run_cli(["endpoint", "add", "simple", "--name", "report-bot", "--url", endpoint_url], env=env)

        # Run attack
        result = run_cli(["attack", "run", "--endpoint", "report-bot", "--dataset", "test_mini"], env=env, timeout=180)
        assert result.returncode == 0

        # Get attack ID
        result = run_cli(["attack", "list"], env=env)
        attack_id = None
        for line in result.stdout.split("\n"):
            if "report-bot" in line or "test_mini" in line:
                import re
                match = re.search(r"([0-9a-f]{8})", line)
                if match:
                    attack_id = match.group(1)
                    break
        assert attack_id is not None

        # Run score
        result = run_cli(["score", "run", attack_id, "--age", "child", "--matrix", "flat"], env=env, timeout=180)
        assert result.returncode == 0

        # Get score ID
        result = run_cli(["score", "list"], env=env)
        score_id = None
        for line in result.stdout.split("\n"):
            import re
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                score_id = match.group(1)
                break
        assert score_id is not None

        # Generate report
        result = run_cli(["score", "report", score_id], env=env)
        assert result.returncode == 0
        assert "SRL4C Score Report" in result.stdout or "Score" in result.stdout

    def test_guardrails_export(self, cli_env):
        """Test guardrails export via CLI"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        # Create endpoint
        run_cli(["endpoint", "add", "simple", "--name", "export-bot", "--url", endpoint_url], env=env)

        # Run attack
        run_cli(["attack", "run", "--endpoint", "export-bot", "--dataset", "test_mini"], env=env, timeout=180)

        # Get attack ID
        result = run_cli(["attack", "list"], env=env)
        attack_id = None
        for line in result.stdout.split("\n"):
            import re
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
            import re
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                score_id = match.group(1)
                break

        # Generate guardrails
        run_cli(["guardrails", "generate", score_id], env=env, timeout=180)

        # Get guardrail set ID
        result = run_cli(["guardrails", "list"], env=env)
        set_id = None
        for line in result.stdout.split("\n"):
            import re
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                set_id = match.group(1)
                break

        if set_id:
            # Export guardrails
            result = run_cli(["guardrails", "export", set_id], env=env)
            assert result.returncode == 0

    def test_delete_endpoint(self, cli_env):
        """Test endpoint deletion via CLI"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        # Create endpoint
        run_cli(["endpoint", "add", "simple", "--name", "del-endpoint", "--url", endpoint_url], env=env)

        # Verify exists
        result = run_cli(["endpoint", "list"], env=env)
        assert "del-endpoint" in result.stdout

        # Delete (with --yes to skip confirmation)
        result = run_cli(["endpoint", "remove", "del-endpoint", "--yes"], env=env)
        assert result.returncode == 0

        # Verify deleted
        result = run_cli(["endpoint", "list"], env=env)
        assert "del-endpoint" not in result.stdout

    def test_delete_attack(self, cli_env):
        """Test attack deletion via CLI"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        # Create endpoint and attack
        run_cli(["endpoint", "add", "simple", "--name", "del-attack-bot", "--url", endpoint_url], env=env)
        run_cli(["attack", "run", "--endpoint", "del-attack-bot", "--dataset", "test_mini"], env=env, timeout=180)

        # Get attack ID
        result = run_cli(["attack", "list"], env=env)
        attack_id = None
        for line in result.stdout.split("\n"):
            import re
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                attack_id = match.group(1)
                break
        assert attack_id is not None

        # Delete (with --yes)
        result = run_cli(["attack", "delete", attack_id, "--yes"], env=env)
        assert result.returncode == 0

        # Verify deleted
        result = run_cli(["attack", "list"], env=env)
        assert attack_id not in result.stdout

    def test_delete_score(self, cli_env):
        """Test score deletion via CLI"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        # Create endpoint, attack, score
        run_cli(["endpoint", "add", "simple", "--name", "del-score-bot", "--url", endpoint_url], env=env)
        run_cli(["attack", "run", "--endpoint", "del-score-bot", "--dataset", "test_mini"], env=env, timeout=180)

        # Get attack ID
        result = run_cli(["attack", "list"], env=env)
        attack_id = None
        for line in result.stdout.split("\n"):
            import re
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
            import re
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                score_id = match.group(1)
                break
        assert score_id is not None

        # Delete (with --yes)
        result = run_cli(["score", "delete", score_id, "--yes"], env=env)
        assert result.returncode == 0

        # Verify deleted
        result = run_cli(["score", "list"], env=env)
        assert score_id not in result.stdout

    def test_delete_guardrails(self, cli_env):
        """Test guardrails deletion via CLI"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        # Full pipeline
        run_cli(["endpoint", "add", "simple", "--name", "del-guard-bot", "--url", endpoint_url], env=env)
        run_cli(["attack", "run", "--endpoint", "del-guard-bot", "--dataset", "test_mini"], env=env, timeout=180)

        result = run_cli(["attack", "list"], env=env)
        attack_id = None
        for line in result.stdout.split("\n"):
            import re
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                attack_id = match.group(1)
                break

        run_cli(["score", "run", attack_id, "--age", "child", "--matrix", "flat"], env=env, timeout=180)

        result = run_cli(["score", "list"], env=env)
        score_id = None
        for line in result.stdout.split("\n"):
            import re
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                score_id = match.group(1)
                break

        run_cli(["guardrails", "generate", score_id], env=env, timeout=180)

        result = run_cli(["guardrails", "list"], env=env)
        set_id = None
        for line in result.stdout.split("\n"):
            import re
            match = re.search(r"([0-9a-f]{8})", line)
            if match:
                set_id = match.group(1)
                break

        if set_id:
            # Delete (with --yes)
            result = run_cli(["guardrails", "delete", set_id, "--yes"], env=env)
            assert result.returncode == 0

            # Verify deleted
            result = run_cli(["guardrails", "list"], env=env)
            assert set_id not in result.stdout
