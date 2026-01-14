"""Centralized path configuration for SRL4C"""

import os
from pathlib import Path

# Package root (src/srl4c/)
PACKAGE_ROOT = Path(__file__).parent

# Project root (SRL4Children/)
PROJECT_ROOT = PACKAGE_ROOT.parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
CRITERIA_DIR = DATA_DIR / "criteria"  # Legacy - to be removed
DATASETS_DIR = DATA_DIR / "datasets"
JUDGES_DIR = DATA_DIR / "judges"
REGISTRY_FILE = DATA_DIR / "registry.yml"  # New location
LEGACY_REGISTRY_FILE = CRITERIA_DIR / "registry.yml"  # Old location for migration

# Templates (copied to ~/.srl4c/ on init)
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# User config directory - use SRL4C_HOME env var if set
USER_CONFIG_DIR = Path(os.environ.get("SRL4C_HOME", Path.home() / ".srl4c"))
