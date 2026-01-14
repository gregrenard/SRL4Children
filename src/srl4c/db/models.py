"""SQLite database models and schema"""

import sqlite3
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from pathlib import Path

from srl4c.db import DB_PATH

# Jobs running longer than this without progress updates are considered stale
STALE_TIMEOUT_MINUTES = 90


SCHEMA = """
CREATE TABLE IF NOT EXISTS endpoints (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    base_url TEXT NOT NULL,
    api_key_env TEXT,
    config_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attacks (
    id TEXT PRIMARY KEY,
    endpoint_id TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_prompts INTEGER,
    completed_prompts INTEGER DEFAULT 0,
    progress_current INTEGER DEFAULT 0,
    progress_total INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (endpoint_id) REFERENCES endpoints(id)
);

CREATE TABLE IF NOT EXISTS records (
    id TEXT PRIMARY KEY,
    attack_id TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT,
    criteria_id TEXT NOT NULL,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attack_id) REFERENCES attacks(id)
);

CREATE TABLE IF NOT EXISTS scores (
    id TEXT PRIMARY KEY,
    attack_id TEXT NOT NULL,
    age_context TEXT NOT NULL,
    judge TEXT DEFAULT 'default',
    final_score REAL,
    category_scores_json TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    progress_current INTEGER DEFAULT 0,
    progress_total INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (attack_id) REFERENCES attacks(id)
);

CREATE TABLE IF NOT EXISTS evaluations (
    id TEXT PRIMARY KEY,
    score_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    criteria_id TEXT NOT NULL,
    final_score REAL,
    agreement_score REAL,
    explanation TEXT,
    evidence_json TEXT,
    judge_details_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (score_id) REFERENCES scores(id),
    FOREIGN KEY (record_id) REFERENCES records(id)
);

CREATE TABLE IF NOT EXISTS guardrail_sets (
    id TEXT PRIMARY KEY,
    score_id TEXT NOT NULL,
    model TEXT,
    rules_count INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    progress_current INTEGER DEFAULT 0,
    progress_total INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (score_id) REFERENCES scores(id)
);

CREATE TABLE IF NOT EXISTS guardrails (
    id TEXT PRIMARY KEY,
    set_id TEXT NOT NULL,
    criteria_id TEXT NOT NULL,
    rule_text TEXT NOT NULL,
    rationale TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (set_id) REFERENCES guardrail_sets(id)
);

CREATE TABLE IF NOT EXISTS logs (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    level TEXT NOT NULL,
    source TEXT NOT NULL,
    message TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_entity ON logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
"""


@dataclass
class Endpoint:
    id: str
    name: str
    type: str  # 'openai' or 'simple'
    base_url: str
    api_key_env: Optional[str] = None
    config: dict = field(default_factory=dict)
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None


@dataclass
class Attack:
    id: str
    endpoint_id: str
    dataset_name: str
    status: str = "pending"
    total_prompts: int = 0
    completed_prompts: int = 0
    progress_current: int = 0
    progress_total: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Record:
    id: str
    attack_id: str
    prompt: str
    criteria_id: str
    response: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Score:
    id: str
    attack_id: str
    age_context: str
    status: str = "pending"
    judge: str = "default"
    final_score: Optional[float] = None
    category_scores: Optional[dict] = None
    progress_current: int = 0
    progress_total: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Evaluation:
    id: str
    score_id: str
    record_id: str
    criteria_id: str
    final_score: Optional[float] = None
    explanation: Optional[str] = None
    evidence: Optional[list] = None
    judge_details: Optional[dict] = None
    created_at: Optional[datetime] = None


@dataclass
class GuardrailSet:
    id: str
    score_id: str
    model: Optional[str] = None
    rules_count: int = 0
    status: str = "pending"
    progress_current: int = 0
    progress_total: int = 0
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Guardrail:
    id: str
    set_id: str
    criteria_id: str
    rule_text: str
    rationale: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Log:
    id: str
    timestamp: str
    level: str  # 'info', 'warning', 'error'
    source: str  # 'endpoint', 'attack', 'score', 'guardrails', 'api'
    message: str
    entity_type: Optional[str] = None  # 'endpoint', 'attack', 'score', 'guardrail_set'
    entity_id: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None


def get_connection() -> sqlite3.Connection:
    """Get database connection, creating DB if needed"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema"""
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


from contextlib import contextmanager

@contextmanager
def db_connection():
    """Database connection context manager.

    Usage:
        with db_connection() as conn:
            conn.execute(...)

    Automatically commits on success, closes on exit.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
