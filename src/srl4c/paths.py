"""Centralized path configuration for SRL4C"""

import os
from pathlib import Path

# Package root (src/srl4c/)
PACKAGE_ROOT = Path(__file__).parent

# Project root (SRL4Children/)
PROJECT_ROOT = PACKAGE_ROOT.parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
CRITERIA_DIR = DATA_DIR / "criteria"  # Contains criteria.yml, presets.yml, judges/
DATASETS_DIR = DATA_DIR / "datasets"

# Registry files (split into multiple files in CRITERIA_DIR)
CRITERIA_FILE = CRITERIA_DIR / "criteria.yml"  # Abstract criteria definitions
PRESETS_FILE = CRITERIA_DIR / "presets.yml"  # Named criteria selections
JUDGES_REGISTRY_DIR = CRITERIA_DIR / "judges"  # Judge implementation configs (*.yml)

# Legacy paths (kept for backward compatibility)
REGISTRY_FILE = DATA_DIR / "registry.yml"  # Old monolithic file - to be removed

# Templates (copied to ~/.srl4c/ on init)
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# User config directory - use SRL4C_HOME env var if set
USER_CONFIG_DIR = Path(os.environ.get("SRL4C_HOME", Path.home() / ".srl4c"))
