"""Tests for the run-pipeline command (CLI and API)"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


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


class TestPipelineCLI:
    """Test the run-pipeline CLI command"""

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
    provider_openai_base_url: {fake_judge_server["base_url"]}
    model: fake-model
"""
        (config_dir / "fake.judges").write_text(fake_judges_content)

        # Create settings to use fake.judges
        settings_content = "active_judges: fake.judges\n"
        (config_dir / "settings.yaml").write_text(settings_content)

        # Copy test dataset
        datasets_dir = config_dir / "datasets"
        datasets_dir.mkdir()
        test_dataset_src = PROJECT_ROOT / "tests" / "fixtures" / "test_dataset.csv"
        test_dataset_dst = datasets_dir / "test_mini.csv"
        test_dataset_dst.write_text(test_dataset_src.read_text())

        # Initialize database
        import sqlite3

        from srl4c.db.models import SCHEMA

        db_path = config_dir / "srl4c.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()

        # Create environment with modified HOME
        env = os.environ.copy()
        env["HOME"] = str(fake_home)
        env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

        return {
            "env": env,
            "config_dir": config_dir,
            "endpoint_url": fake_endpoint_server["url"],
        }

    def test_pipeline_help(self):
        """Verify run-pipeline command help works"""
        result = run_cli(["run-pipeline", "--help"])
        assert result.returncode == 0
        assert "pipeline" in result.stdout.lower()

    def test_pipeline_run_simple_endpoint(self, cli_env, fake_endpoint_server):
        """Test full pipeline with simple endpoint"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        result = run_cli(
            [
                "run-pipeline",
                "test-app",
                "--type",
                "simple",
                "--url",
                endpoint_url,
                "--dataset",
                "test_mini",
                "--age",
                "child",
            ],
            env=env,
            timeout=300,
        )

        assert result.returncode == 0, f"Pipeline failed: {result.stderr}\n{result.stdout}"
        assert "pipeline" in result.stdout.lower() or "complete" in result.stdout.lower()
        assert "endpoint" in result.stdout.lower() or "test-app" in result.stdout

    def test_pipeline_creates_endpoint(self, cli_env, fake_endpoint_server):
        """Test that pipeline creates a new endpoint"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        # Run pipeline (creates endpoint)
        result = run_cli(
            [
                "run-pipeline",
                "my-new-app",
                "--type",
                "simple",
                "--url",
                endpoint_url,
                "--dataset",
                "test_mini",
            ],
            env=env,
            timeout=300,
        )
        assert result.returncode == 0

        # Verify endpoint exists in endpoint list
        result = run_cli(["endpoint", "list"], env=env)
        assert result.returncode == 0
        assert "my-new-app" in result.stdout

    def test_pipeline_with_custom_age_context(self, cli_env, fake_endpoint_server):
        """Test pipeline with a non-default age context"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        result = run_cli(
            [
                "run-pipeline",
                "test-app",
                "--type",
                "simple",
                "--url",
                endpoint_url,
                "--dataset",
                "test_mini",
                "--age",
                "teen",
            ],
            env=env,
            timeout=300,
        )

        assert result.returncode == 0
        assert "teen" in result.stdout or "score" in result.stdout.lower()

    def test_pipeline_with_guardrail_options(self, cli_env, fake_endpoint_server):
        """Test pipeline with custom guardrail generation options"""
        env = cli_env["env"]
        endpoint_url = cli_env["endpoint_url"]

        result = run_cli(
            [
                "run-pipeline",
                "test-app",
                "--type",
                "simple",
                "--url",
                endpoint_url,
                "--dataset",
                "test_mini",
                "--max-rules",
                "2",
                "--max-total",
                "10",
            ],
            env=env,
            timeout=300,
        )

        assert result.returncode == 0


class TestPipelineAPI:
    """Test the POST /api/pipeline endpoint"""

    def test_pipeline_api_endpoint(self, api_client, fake_endpoint_server):
        """Test POST /api/pipeline with simple endpoint"""
        payload = {
            "name": "api-test-app",
            "endpoint_type": "simple",
            "endpoint_url": fake_endpoint_server["url"],
            "dataset": "test_mini",
            "age": "child",
            "weights": "balanced",
        }

        response = api_client.post("/api/pipeline/", json=payload)

        assert response.status_code == 201, f"Failed: {response.text}"
        data = response.json()

        assert "endpoint_id" in data
        assert "attack_id" in data
        assert "score_id" in data
        assert data["status"] == "completed"

    def test_pipeline_api_required_fields(self, api_client):
        """Test that required fields are enforced"""
        payload = {
            "endpoint_type": "simple",
            # Missing required 'name' and 'endpoint_url'
        }

        response = api_client.post("/api/pipeline/", json=payload)
        assert response.status_code == 422  # Validation error

    def test_pipeline_api_with_worker_deployment_flag(self, api_client, fake_endpoint_server):
        """Test pipeline API with worker deployment flag"""
        payload = {
            "name": "api-test-deploy",
            "endpoint_type": "simple",
            "endpoint_url": fake_endpoint_server["url"],
            "dataset": "test_mini",
            "deploy_worker": False,  # Explicitly set to False
        }

        response = api_client.post("/api/pipeline/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "completed"

    def test_pipeline_api_response_structure(self, api_client, fake_endpoint_server):
        """Test that API response has all required fields"""
        payload = {
            "name": "api-response-test",
            "endpoint_type": "simple",
            "endpoint_url": fake_endpoint_server["url"],
            "dataset": "test_mini",
        }

        response = api_client.post("/api/pipeline/", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert isinstance(data, dict)
        assert "endpoint_id" in data
        assert "attack_id" in data
        assert "score_id" in data
        assert "status" in data
        # Note: final_score might be None if scoring fails
