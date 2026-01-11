"""Database layer for SRL4C"""

import os
from pathlib import Path

# Use SRL4C_HOME env var if set, otherwise ~/.srl4c
SRL4C_HOME = Path(os.environ.get("SRL4C_HOME", Path.home() / ".srl4c"))
DB_PATH = SRL4C_HOME / "srl4c.db"
