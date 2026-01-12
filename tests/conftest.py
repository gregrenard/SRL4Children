"""
Pytest fixtures for SRL4C E2E testing

Provides isolated database, fake servers, and config fixtures.
"""

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def get_free_port() -> int:
    """Find an available port"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def wait_for_server(port: int, timeout: float = 10.0) -> bool:
    """Wait for a server to be available on the given port"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except (TimeoutError, ConnectionRefusedError):
            time.sleep(0.1)
    return False


@pytest.fixture(scope="session")
def fake_endpoint_server():
    """Start fake endpoint server for the test session"""
    port = get_free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "fake_endpoint.py"),
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if not wait_for_server(port):
        proc.kill()
        raise RuntimeError(f"Fake endpoint server failed to start on port {port}")

    yield {"port": port, "url": f"http://localhost:{port}/chat"}

    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def fake_judge_server():
    """Start fake judge server for the test session"""
    port = get_free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "fake_judge.py"),
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if not wait_for_server(port):
        proc.kill()
        raise RuntimeError(f"Fake judge server failed to start on port {port}")

    yield {"port": port, "base_url": f"http://localhost:{port}/v1"}

    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def fake_generator_server():
    """Start fake generator server for the test session"""
    port = get_free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "fake_generator.py"),
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if not wait_for_server(port):
        proc.kill()
        raise RuntimeError(f"Fake generator server failed to start on port {port}")

    yield {"port": port, "base_url": f"http://localhost:{port}/v1"}

    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture
def temp_config_dir(tmp_path, fake_judge_server, fake_generator_server, monkeypatch):
    """Create isolated config directory with fake.judges and fake.generators pointing to fake servers"""
    # Create fake home directory
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    config_dir = fake_home / ".srl4c"
    config_dir.mkdir()

    # Copy test dataset to custom datasets directory
    datasets_dir = config_dir / "datasets"
    datasets_dir.mkdir()
    test_dataset_src = PROJECT_ROOT / "tests" / "fixtures" / "test_dataset.csv"
    test_dataset_dst = datasets_dir / "test_mini.csv"
    test_dataset_dst.write_text(test_dataset_src.read_text())

    # Create fake.judges config pointing to test server
    fake_judges_content = f"""# Test Judge Configuration
n_passes: 1

judges:
  fake_judge:
    provider_openai_base_url: {fake_judge_server["base_url"]}
    model: fake-model
"""
    (config_dir / "fake.judges").write_text(fake_judges_content)

    # Create fake.generators config pointing to test server
    fake_generators_content = f"""# Test Generator Configuration
name: fake
provider_openai_base_url: {fake_generator_server["base_url"]}
model: fake-generator
temperature: 0.15
max_tokens: 1000
"""
    (config_dir / "fake.generators").write_text(fake_generators_content)

    # Create settings.yaml to use fake.judges and fake.generators
    settings_content = """active_judges: fake.judges
active_generators: fake.generators
"""
    (config_dir / "settings.yaml").write_text(settings_content)

    # Monkeypatch Path.home() to return our fake home
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    # Monkeypatch paths module
    import srl4c.db
    import srl4c.generator.config
    import srl4c.judge.config
    import srl4c.paths

    monkeypatch.setattr(srl4c.paths, "USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(srl4c.db, "SRL4C_HOME", config_dir)
    monkeypatch.setattr(srl4c.db, "DB_PATH", config_dir / "srl4c.db")
    monkeypatch.setattr(srl4c.judge.config, "USER_CONFIG_DIR", config_dir)
    monkeypatch.setattr(srl4c.generator.config, "USER_CONFIG_DIR", config_dir)

    # Also need to patch the already-imported reference in models
    import srl4c.db.models

    monkeypatch.setattr(srl4c.db.models, "DB_PATH", config_dir / "srl4c.db")

    yield config_dir


@pytest.fixture
def temp_db(temp_config_dir):
    """Initialize fresh database for each test"""
    from srl4c.db.models import init_db

    init_db()
    yield temp_config_dir / "srl4c.db"


@pytest.fixture
def api_client(temp_db):
    """FastAPI TestClient with isolated database"""
    from fastapi.testclient import TestClient

    from srl4c.api.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_endpoint(api_client, fake_endpoint_server):
    """Create a test endpoint and return its info"""
    response = api_client.post(
        "/api/endpoints",
        json={
            "name": "test-bot",
            "type": "simple",
            "base_url": fake_endpoint_server["url"],
        },
    )
    assert response.status_code == 201, f"Failed to create endpoint: {response.text}"
    return response.json()


@pytest.fixture
def test_dataset_path():
    """Path to test dataset fixture"""
    return PROJECT_ROOT / "tests" / "fixtures" / "test_dataset.csv"


def poll_status(api_client, endpoint: str, target_status: str, timeout: float = 60.0) -> dict:
    """Poll an endpoint until status matches or timeout"""
    start = time.time()
    while time.time() - start < timeout:
        response = api_client.get(endpoint)
        data = response.json()
        status = data.get("status")
        if status == target_status:
            return data
        if status == "failed":
            raise RuntimeError(f"Job failed: {data.get('error_message', 'Unknown error')}")
        time.sleep(0.5)
    raise TimeoutError(f"Timed out waiting for {endpoint} to reach status '{target_status}'")
