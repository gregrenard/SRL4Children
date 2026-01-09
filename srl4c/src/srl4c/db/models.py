"""SQLite database models and schema"""

import sqlite3
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from pathlib import Path

from srl4c.db import DB_PATH


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
    status TEXT NOT NULL DEFAULT 'running',
    total_prompts INTEGER,
    completed_prompts INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (endpoint_id) REFERENCES endpoints(id)
);

CREATE TABLE IF NOT EXISTS records (
    id TEXT PRIMARY KEY,
    attack_id TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT,
    principle_id TEXT NOT NULL,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attack_id) REFERENCES attacks(id)
);

CREATE TABLE IF NOT EXISTS scores (
    id TEXT PRIMARY KEY,
    attack_id TEXT NOT NULL,
    age_context TEXT NOT NULL,
    weights_preset TEXT,
    weights_json TEXT,
    final_score REAL,
    category_scores_json TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (attack_id) REFERENCES attacks(id)
);

CREATE TABLE IF NOT EXISTS evaluations (
    id TEXT PRIMARY KEY,
    score_id TEXT NOT NULL,
    record_id TEXT NOT NULL,
    principle_id TEXT NOT NULL,
    final_score REAL,
    explanation TEXT,
    evidence_json TEXT,
    judge_details_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (score_id) REFERENCES scores(id),
    FOREIGN KEY (record_id) REFERENCES records(id)
);

CREATE TABLE IF NOT EXISTS guardrails (
    id TEXT PRIMARY KEY,
    score_id TEXT NOT NULL,
    principle_id TEXT NOT NULL,
    rule_text TEXT NOT NULL,
    coverage_score REAL,
    validated INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (score_id) REFERENCES scores(id)
);
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
    status: str = "running"
    total_prompts: int = 0
    completed_prompts: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Record:
    id: str
    attack_id: str
    prompt: str
    principle_id: str
    response: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Score:
    id: str
    attack_id: str
    age_context: str
    status: str = "running"
    weights_preset: Optional[str] = None
    weights: Optional[dict] = None
    final_score: Optional[float] = None
    category_scores: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Evaluation:
    id: str
    score_id: str
    record_id: str
    principle_id: str
    final_score: Optional[float] = None
    explanation: Optional[str] = None
    evidence: Optional[list] = None
    judge_details: Optional[dict] = None
    created_at: Optional[datetime] = None


@dataclass
class Guardrail:
    id: str
    score_id: str
    principle_id: str
    rule_text: str
    coverage_score: Optional[float] = None
    validated: bool = False
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
