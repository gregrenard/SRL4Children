"""Repository for database CRUD operations"""

import json
import uuid
from datetime import datetime
from typing import Optional

from srl4c.db.models import (
    get_connection, init_db,
    Endpoint, Attack, Record, Score, Evaluation, Guardrail
)


def generate_id() -> str:
    """Generate a short UUID"""
    return str(uuid.uuid4())[:8]


class EndpointRepository:
    """CRUD operations for endpoints"""

    @staticmethod
    def create(endpoint: Endpoint) -> Endpoint:
        """Create a new endpoint"""
        init_db()
        conn = get_connection()
        conn.execute(
            """INSERT INTO endpoints (id, name, type, base_url, api_key_env, config_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                endpoint.id,
                endpoint.name,
                endpoint.type,
                endpoint.base_url,
                endpoint.api_key_env,
                json.dumps(endpoint.config) if endpoint.config else None,
                datetime.now().isoformat(),
            )
        )
        conn.commit()
        conn.close()
        return endpoint

    @staticmethod
    def get_by_id(id: str) -> Optional[Endpoint]:
        """Get endpoint by ID (supports prefix matching)"""
        init_db()
        conn = get_connection()
        # Try exact match first
        row = conn.execute("SELECT * FROM endpoints WHERE id = ?", (id,)).fetchone()
        if not row:
            # Try prefix match
            rows = conn.execute("SELECT * FROM endpoints WHERE id LIKE ?", (f"{id}%",)).fetchall()
            if len(rows) == 1:
                row = rows[0]
            elif len(rows) > 1:
                conn.close()
                raise ValueError(f"Ambiguous ID '{id}' matches: {[r['id'] for r in rows]}")
        conn.close()
        if row:
            return Endpoint(
                id=row["id"],
                name=row["name"],
                type=row["type"],
                base_url=row["base_url"],
                api_key_env=row["api_key_env"],
                config=json.loads(row["config_json"]) if row["config_json"] else {},
                created_at=row["created_at"],
                last_used_at=row["last_used_at"],
            )
        return None

    @staticmethod
    def get_by_name(name: str) -> Optional[Endpoint]:
        """Get endpoint by name"""
        init_db()
        conn = get_connection()
        row = conn.execute("SELECT * FROM endpoints WHERE name = ?", (name,)).fetchone()
        conn.close()
        if row:
            return Endpoint(
                id=row["id"],
                name=row["name"],
                type=row["type"],
                base_url=row["base_url"],
                api_key_env=row["api_key_env"],
                config=json.loads(row["config_json"]) if row["config_json"] else {},
                created_at=row["created_at"],
                last_used_at=row["last_used_at"],
            )
        return None

    @staticmethod
    def get_by_id_or_name(id_or_name: str) -> Optional[Endpoint]:
        """Get endpoint by ID (prefix) or name"""
        # Try by name first
        endpoint = EndpointRepository.get_by_name(id_or_name)
        if endpoint:
            return endpoint
        # Try by ID
        return EndpointRepository.get_by_id(id_or_name)

    @staticmethod
    def list_all() -> list[Endpoint]:
        """List all endpoints"""
        init_db()
        conn = get_connection()
        rows = conn.execute("SELECT * FROM endpoints ORDER BY created_at DESC").fetchall()
        conn.close()
        return [
            Endpoint(
                id=row["id"],
                name=row["name"],
                type=row["type"],
                base_url=row["base_url"],
                api_key_env=row["api_key_env"],
                config=json.loads(row["config_json"]) if row["config_json"] else {},
                created_at=row["created_at"],
                last_used_at=row["last_used_at"],
            )
            for row in rows
        ]

    @staticmethod
    def delete(id: str) -> bool:
        """Delete endpoint by ID"""
        endpoint = EndpointRepository.get_by_id(id)
        if not endpoint:
            return False
        conn = get_connection()
        conn.execute("DELETE FROM endpoints WHERE id = ?", (endpoint.id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def update_last_used(id: str):
        """Update last_used_at timestamp"""
        conn = get_connection()
        conn.execute(
            "UPDATE endpoints SET last_used_at = ? WHERE id = ?",
            (datetime.now().isoformat(), id)
        )
        conn.commit()
        conn.close()


class AttackRepository:
    """CRUD operations for attacks"""

    @staticmethod
    def create(attack: Attack) -> Attack:
        """Create a new attack"""
        init_db()
        conn = get_connection()
        conn.execute(
            """INSERT INTO attacks (id, endpoint_id, dataset_name, status, total_prompts, completed_prompts, started_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                attack.id,
                attack.endpoint_id,
                attack.dataset_name,
                attack.status,
                attack.total_prompts,
                attack.completed_prompts,
                datetime.now().isoformat(),
            )
        )
        conn.commit()
        conn.close()
        return attack

    @staticmethod
    def get_by_id(id: str) -> Optional[Attack]:
        """Get attack by ID (supports prefix matching)"""
        init_db()
        conn = get_connection()
        row = conn.execute("SELECT * FROM attacks WHERE id = ?", (id,)).fetchone()
        if not row:
            rows = conn.execute("SELECT * FROM attacks WHERE id LIKE ?", (f"{id}%",)).fetchall()
            if len(rows) == 1:
                row = rows[0]
            elif len(rows) > 1:
                conn.close()
                raise ValueError(f"Ambiguous ID '{id}' matches: {[r['id'] for r in rows]}")
        conn.close()
        if row:
            return Attack(
                id=row["id"],
                endpoint_id=row["endpoint_id"],
                dataset_name=row["dataset_name"],
                status=row["status"],
                total_prompts=row["total_prompts"],
                completed_prompts=row["completed_prompts"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
            )
        return None

    @staticmethod
    def list_all() -> list[Attack]:
        """List all attacks"""
        init_db()
        conn = get_connection()
        rows = conn.execute("SELECT * FROM attacks ORDER BY started_at DESC").fetchall()
        conn.close()
        return [
            Attack(
                id=row["id"],
                endpoint_id=row["endpoint_id"],
                dataset_name=row["dataset_name"],
                status=row["status"],
                total_prompts=row["total_prompts"],
                completed_prompts=row["completed_prompts"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
            )
            for row in rows
        ]

    @staticmethod
    def update_status(id: str, status: str, completed_prompts: int = None):
        """Update attack status"""
        conn = get_connection()
        if completed_prompts is not None:
            conn.execute(
                "UPDATE attacks SET status = ?, completed_prompts = ?, completed_at = ? WHERE id = ?",
                (status, completed_prompts, datetime.now().isoformat() if status == "completed" else None, id)
            )
        else:
            conn.execute(
                "UPDATE attacks SET status = ?, completed_at = ? WHERE id = ?",
                (status, datetime.now().isoformat() if status == "completed" else None, id)
            )
        conn.commit()
        conn.close()


class RecordRepository:
    """CRUD operations for records"""

    @staticmethod
    def create(record: Record) -> Record:
        """Create a new record"""
        conn = get_connection()
        conn.execute(
            """INSERT INTO records (id, attack_id, prompt, response, principle_id, error, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                record.id,
                record.attack_id,
                record.prompt,
                record.response,
                record.principle_id,
                record.error,
                datetime.now().isoformat(),
            )
        )
        conn.commit()
        conn.close()
        return record

    @staticmethod
    def get_by_attack(attack_id: str) -> list[Record]:
        """Get all records for an attack"""
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM records WHERE attack_id = ? ORDER BY created_at",
            (attack_id,)
        ).fetchall()
        conn.close()
        return [
            Record(
                id=row["id"],
                attack_id=row["attack_id"],
                prompt=row["prompt"],
                response=row["response"],
                principle_id=row["principle_id"],
                error=row["error"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    @staticmethod
    def update_response(id: str, response: str = None, error: str = None):
        """Update record with response or error"""
        conn = get_connection()
        conn.execute(
            "UPDATE records SET response = ?, error = ? WHERE id = ?",
            (response, error, id)
        )
        conn.commit()
        conn.close()
