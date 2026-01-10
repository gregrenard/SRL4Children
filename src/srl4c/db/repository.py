"""Repository for database CRUD operations"""

import json
import uuid
from datetime import datetime
from typing import Optional

from srl4c.db.models import (
    get_connection, init_db, db_connection,
    Endpoint, Attack, Record, Score, Evaluation, Guardrail
)


def generate_id() -> str:
    """Generate a short UUID"""
    return str(uuid.uuid4())[:8]


def _row_to_endpoint(row) -> Endpoint:
    """Convert a database row to an Endpoint object"""
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


def _row_to_attack(row) -> Attack:
    """Convert a database row to an Attack object"""
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


def _row_to_record(row) -> Record:
    """Convert a database row to a Record object"""
    return Record(
        id=row["id"],
        attack_id=row["attack_id"],
        prompt=row["prompt"],
        response=row["response"],
        principle_id=row["principle_id"],
        error=row["error"],
        created_at=row["created_at"],
    )


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
        return _row_to_endpoint(row) if row else None

    @staticmethod
    def get_by_name(name: str) -> Optional[Endpoint]:
        """Get endpoint by name"""
        init_db()
        conn = get_connection()
        row = conn.execute("SELECT * FROM endpoints WHERE name = ?", (name,)).fetchone()
        conn.close()
        return _row_to_endpoint(row) if row else None

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
        return [_row_to_endpoint(row) for row in rows]

    @staticmethod
    def delete(id: str, cascade: bool = False) -> dict:
        """Delete endpoint by ID.

        If cascade=True, deletes all attacks (and their records/scores/evaluations).
        Returns dict with counts or None if not found.
        """
        endpoint = EndpointRepository.get_by_id(id)
        if not endpoint:
            return None

        deleted = {"attacks": 0, "records": 0, "scores": 0, "evaluations": 0}

        if cascade:
            # Delete all attacks for this endpoint (which cascades further)
            attacks = AttackRepository.get_attacks_for_endpoint(endpoint.id)
            for attack in attacks:
                result = AttackRepository.delete(attack.id, cascade=True)
                if result:
                    deleted["attacks"] += 1
                    deleted["records"] += result["records"]
                    deleted["scores"] += result["scores"]
                    deleted["evaluations"] += result["evaluations"]

        conn = get_connection()
        conn.execute("DELETE FROM endpoints WHERE id = ?", (endpoint.id,))
        conn.commit()
        conn.close()

        return deleted

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
        return _row_to_attack(row) if row else None

    @staticmethod
    def list_all() -> list[Attack]:
        """List all attacks"""
        init_db()
        conn = get_connection()
        rows = conn.execute("SELECT * FROM attacks ORDER BY started_at DESC").fetchall()
        conn.close()
        return [_row_to_attack(row) for row in rows]

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

    @staticmethod
    def delete(id: str, cascade: bool = True) -> dict:
        """Delete attack and optionally cascade to records, scores, evaluations.

        Returns dict with counts of deleted items.
        """
        attack = AttackRepository.get_by_id(id)
        if not attack:
            return None

        deleted = {"records": 0, "scores": 0, "evaluations": 0}

        with db_connection() as conn:
            if cascade:
                # Get scores for this attack
                score_ids = [row[0] for row in conn.execute(
                    "SELECT id FROM scores WHERE attack_id = ?", (attack.id,)
                ).fetchall()]

                # Delete evaluations for each score
                for score_id in score_ids:
                    result = conn.execute("DELETE FROM evaluations WHERE score_id = ?", (score_id,))
                    deleted["evaluations"] += result.rowcount

                # Delete scores
                result = conn.execute("DELETE FROM scores WHERE attack_id = ?", (attack.id,))
                deleted["scores"] = result.rowcount

                # Delete records
                result = conn.execute("DELETE FROM records WHERE attack_id = ?", (attack.id,))
                deleted["records"] = result.rowcount

            # Delete attack
            conn.execute("DELETE FROM attacks WHERE id = ?", (attack.id,))

        return deleted

    @staticmethod
    def get_attacks_for_endpoint(endpoint_id: str) -> list:
        """Get all attacks for an endpoint"""
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM attacks WHERE endpoint_id = ?", (endpoint_id,)
        ).fetchall()
        conn.close()
        return [_row_to_attack(row) for row in rows]


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
        return [_row_to_record(row) for row in rows]

    @staticmethod
    def update_response(id: str, response: str = None, error: str = None):
        """Update record with response or error"""
        with db_connection() as conn:
            conn.execute(
                "UPDATE records SET response = ?, error = ? WHERE id = ?",
                (response, error, id)
            )


class ScoreRepository:
    """CRUD operations for scores"""

    @staticmethod
    def get_by_id(id: str):
        """Get score by ID (supports prefix matching)"""
        init_db()
        with db_connection() as conn:
            row = conn.execute("SELECT * FROM scores WHERE id = ?", (id,)).fetchone()
            if not row:
                rows = conn.execute("SELECT * FROM scores WHERE id LIKE ?", (f"{id}%",)).fetchall()
                if len(rows) == 1:
                    row = rows[0]
                elif len(rows) > 1:
                    raise ValueError(f"Ambiguous ID '{id}' matches: {[r['id'] for r in rows]}")
        return dict(row) if row else None

    @staticmethod
    def delete(id: str) -> dict:
        """Delete score and its evaluations."""
        score = ScoreRepository.get_by_id(id)
        if not score:
            return None

        deleted = {"evaluations": 0}

        with db_connection() as conn:
            # Delete evaluations
            result = conn.execute("DELETE FROM evaluations WHERE score_id = ?", (score["id"],))
            deleted["evaluations"] = result.rowcount

            # Delete score
            conn.execute("DELETE FROM scores WHERE id = ?", (score["id"],))

        return deleted


class GuardrailSetRepository:
    """CRUD operations for guardrail sets"""

    @staticmethod
    def get_by_id(id: str):
        """Get guardrail set by ID (supports prefix matching)"""
        init_db()
        with db_connection() as conn:
            row = conn.execute("SELECT * FROM guardrail_sets WHERE id = ?", (id,)).fetchone()
            if not row:
                rows = conn.execute("SELECT * FROM guardrail_sets WHERE id LIKE ?", (f"{id}%",)).fetchall()
                if len(rows) == 1:
                    row = rows[0]
                elif len(rows) > 1:
                    raise ValueError(f"Ambiguous ID '{id}' matches: {[r['id'] for r in rows]}")
        return dict(row) if row else None

    @staticmethod
    def delete(id: str) -> dict:
        """Delete guardrail set and its guardrails."""
        gset = GuardrailSetRepository.get_by_id(id)
        if not gset:
            return None

        deleted = {"guardrails": 0}

        with db_connection() as conn:
            # Delete guardrails
            result = conn.execute("DELETE FROM guardrails WHERE set_id = ?", (gset["id"],))
            deleted["guardrails"] = result.rowcount

            # Delete set
            conn.execute("DELETE FROM guardrail_sets WHERE id = ?", (gset["id"],))

        return deleted
