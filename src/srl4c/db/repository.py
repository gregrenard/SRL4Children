"""Repository for database CRUD operations"""

import json
import uuid
from datetime import datetime
from typing import Optional

from srl4c.db.models import (
    get_connection, init_db, db_connection,
    Endpoint, Attack, Record, Score, Evaluation, Guardrail, Log,
    Dataset, Judge, JudgeCriteria
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
        dataset_id=row["dataset_id"],
        status=row["status"],
        total_prompts=row["total_prompts"],
        completed_prompts=row["completed_prompts"],
        progress_current=row["progress_current"] or 0,
        progress_total=row["progress_total"] or 0,
        error_message=row["error_message"],
        started_at=row["started_at"],
        updated_at=row["updated_at"],
        completed_at=row["completed_at"],
    )


def _row_to_record(row) -> Record:
    """Convert a database row to a Record object"""
    return Record(
        id=row["id"],
        attack_id=row["attack_id"],
        prompt=row["prompt"],
        response=row["response"],
        criteria_id=row["criteria_id"],
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
        created_at = datetime.now().isoformat()
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
                created_at,
            )
        )
        conn.commit()
        conn.close()
        endpoint.created_at = created_at
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
    def delete_preview(id: str) -> dict:
        """Preview what will be deleted if this endpoint is cascade deleted."""
        endpoint = EndpointRepository.get_by_id(id)
        if not endpoint:
            return None

        counts = {"attacks": 0, "records": 0, "scores": 0, "evaluations": 0, "guardrail_sets": 0, "guardrails": 0}

        with db_connection() as conn:
            attacks = conn.execute("SELECT id FROM attacks WHERE endpoint_id = ?", (endpoint.id,)).fetchall()
            counts["attacks"] = len(attacks)

            for attack in attacks:
                counts["records"] += conn.execute("SELECT COUNT(*) FROM records WHERE attack_id = ?", (attack["id"],)).fetchone()[0]

                scores = conn.execute("SELECT id FROM scores WHERE attack_id = ?", (attack["id"],)).fetchall()
                counts["scores"] += len(scores)

                for score in scores:
                    counts["evaluations"] += conn.execute("SELECT COUNT(*) FROM evaluations WHERE score_id = ?", (score["id"],)).fetchone()[0]
                    gsets = conn.execute("SELECT id FROM guardrail_sets WHERE score_id = ?", (score["id"],)).fetchall()
                    counts["guardrail_sets"] += len(gsets)
                    for gset in gsets:
                        counts["guardrails"] += conn.execute("SELECT COUNT(*) FROM guardrails WHERE set_id = ?", (gset["id"],)).fetchone()[0]

        return {"endpoint": {"id": endpoint.id, "name": endpoint.name}, "will_delete": counts, "has_children": counts["attacks"] > 0}

    @staticmethod
    def delete(id: str, cascade: bool = False) -> dict:
        """Delete endpoint by ID.

        If cascade=True, deletes all attacks (and their records/scores/evaluations/guardrails).
        Returns dict with counts or None if not found.
        """
        endpoint = EndpointRepository.get_by_id(id)
        if not endpoint:
            return None

        deleted = {"attacks": 0, "records": 0, "scores": 0, "evaluations": 0, "guardrail_sets": 0, "guardrails": 0}

        if cascade:
            # Delete all attacks for this endpoint (which cascades further)
            attacks = AttackRepository.get_attacks_for_endpoint(endpoint.id)
            for attack in attacks:
                result = AttackRepository.delete(attack.id, cascade=True)
                if result:
                    deleted["attacks"] += 1
                    deleted["records"] += result.get("records", 0)
                    deleted["scores"] += result.get("scores", 0)
                    deleted["evaluations"] += result.get("evaluations", 0)
                    deleted["guardrail_sets"] += result.get("guardrail_sets", 0)
                    deleted["guardrails"] += result.get("guardrails", 0)

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
        started_at = datetime.now().isoformat()
        conn.execute(
            """INSERT INTO attacks (id, endpoint_id, dataset_id, status, total_prompts, completed_prompts, started_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                attack.id,
                attack.endpoint_id,
                attack.dataset_id,
                attack.status,
                attack.total_prompts,
                attack.completed_prompts,
                started_at,
            )
        )
        conn.commit()
        conn.close()
        attack.started_at = started_at
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
    def update_status(id: str, status: str, completed_prompts: int = None, error_message: str = None):
        """Update attack status and optionally error message."""
        now = datetime.now().isoformat()
        with db_connection() as conn:
            if status == "completed":
                conn.execute(
                    """UPDATE attacks SET status = ?, completed_prompts = ?,
                       completed_at = ?, updated_at = ? WHERE id = ?""",
                    (status, completed_prompts, now, now, id)
                )
            elif status == "failed":
                conn.execute(
                    """UPDATE attacks SET status = ?, error_message = ?,
                       updated_at = ? WHERE id = ?""",
                    (status, error_message, now, id)
                )
            else:
                conn.execute(
                    "UPDATE attacks SET status = ?, updated_at = ? WHERE id = ?",
                    (status, now, id)
                )

    @staticmethod
    def update_progress(id: str, current: int, total: int = None):
        """Update attack progress. Also updates updated_at for stale detection."""
        now = datetime.now().isoformat()
        with db_connection() as conn:
            if total is not None:
                conn.execute(
                    """UPDATE attacks SET progress_current = ?, progress_total = ?,
                       updated_at = ? WHERE id = ?""",
                    (current, total, now, id)
                )
            else:
                conn.execute(
                    "UPDATE attacks SET progress_current = ?, updated_at = ? WHERE id = ?",
                    (current, now, id)
                )

    @staticmethod
    def delete_preview(id: str) -> dict:
        """Preview what will be deleted if this attack is cascade deleted."""
        attack = AttackRepository.get_by_id(id)
        if not attack:
            return None

        counts = {"records": 0, "scores": 0, "evaluations": 0, "guardrail_sets": 0, "guardrails": 0}

        with db_connection() as conn:
            counts["records"] = conn.execute("SELECT COUNT(*) FROM records WHERE attack_id = ?", (attack.id,)).fetchone()[0]

            scores = conn.execute("SELECT id FROM scores WHERE attack_id = ?", (attack.id,)).fetchall()
            counts["scores"] = len(scores)

            for score in scores:
                counts["evaluations"] += conn.execute("SELECT COUNT(*) FROM evaluations WHERE score_id = ?", (score["id"],)).fetchone()[0]
                gsets = conn.execute("SELECT id FROM guardrail_sets WHERE score_id = ?", (score["id"],)).fetchall()
                counts["guardrail_sets"] += len(gsets)
                for gset in gsets:
                    counts["guardrails"] += conn.execute("SELECT COUNT(*) FROM guardrails WHERE set_id = ?", (gset["id"],)).fetchone()[0]

        has_children = counts["records"] > 0 or counts["scores"] > 0
        return {"attack": {"id": attack.id, "dataset_id": attack.dataset_id}, "will_delete": counts, "has_children": has_children}

    @staticmethod
    def delete(id: str, cascade: bool = True) -> dict:
        """Delete attack and optionally cascade to records, scores, evaluations, guardrails.

        Returns dict with counts of deleted items.
        """
        attack = AttackRepository.get_by_id(id)
        if not attack:
            return None

        deleted = {"records": 0, "scores": 0, "evaluations": 0, "guardrail_sets": 0, "guardrails": 0}

        with db_connection() as conn:
            if cascade:
                # Get scores for this attack
                score_ids = [row[0] for row in conn.execute(
                    "SELECT id FROM scores WHERE attack_id = ?", (attack.id,)
                ).fetchall()]

                for score_id in score_ids:
                    # Delete guardrails for guardrail_sets of this score
                    gset_ids = [row[0] for row in conn.execute(
                        "SELECT id FROM guardrail_sets WHERE score_id = ?", (score_id,)
                    ).fetchall()]
                    for gset_id in gset_ids:
                        result = conn.execute("DELETE FROM guardrails WHERE set_id = ?", (gset_id,))
                        deleted["guardrails"] += result.rowcount

                    # Delete guardrail_sets
                    result = conn.execute("DELETE FROM guardrail_sets WHERE score_id = ?", (score_id,))
                    deleted["guardrail_sets"] += result.rowcount

                    # Delete evaluations
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
            """INSERT INTO records (id, attack_id, prompt, response, criteria_id, error, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                record.id,
                record.attack_id,
                record.prompt,
                record.response,
                record.criteria_id,
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
    def update_status(id: str, status: str, error_message: str = None):
        """Update score status and optionally error message."""
        now = datetime.now().isoformat()
        with db_connection() as conn:
            if status == "completed":
                conn.execute(
                    "UPDATE scores SET status = ?, completed_at = ?, updated_at = ? WHERE id = ?",
                    (status, now, now, id)
                )
            elif status == "failed":
                conn.execute(
                    "UPDATE scores SET status = ?, error_message = ?, updated_at = ? WHERE id = ?",
                    (status, error_message, now, id)
                )
            else:
                conn.execute(
                    "UPDATE scores SET status = ?, updated_at = ? WHERE id = ?",
                    (status, now, id)
                )

    @staticmethod
    def update_progress(id: str, current: int, total: int = None):
        """Update score progress. Also updates updated_at for stale detection."""
        now = datetime.now().isoformat()
        with db_connection() as conn:
            if total is not None:
                conn.execute(
                    """UPDATE scores SET progress_current = ?, progress_total = ?,
                       updated_at = ? WHERE id = ?""",
                    (current, total, now, id)
                )
            else:
                conn.execute(
                    "UPDATE scores SET progress_current = ?, updated_at = ? WHERE id = ?",
                    (current, now, id)
                )

    @staticmethod
    def delete_preview(id: str) -> dict:
        """Preview what will be deleted if this score is deleted."""
        score = ScoreRepository.get_by_id(id)
        if not score:
            return None

        counts = {"evaluations": 0, "guardrail_sets": 0, "guardrails": 0}

        with db_connection() as conn:
            counts["evaluations"] = conn.execute("SELECT COUNT(*) FROM evaluations WHERE score_id = ?", (score["id"],)).fetchone()[0]
            gsets = conn.execute("SELECT id FROM guardrail_sets WHERE score_id = ?", (score["id"],)).fetchall()
            counts["guardrail_sets"] = len(gsets)
            for gset in gsets:
                counts["guardrails"] += conn.execute("SELECT COUNT(*) FROM guardrails WHERE set_id = ?", (gset["id"],)).fetchone()[0]

        has_children = counts["evaluations"] > 0 or counts["guardrail_sets"] > 0
        return {"score": {"id": score["id"], "final_score": score.get("final_score")}, "will_delete": counts, "has_children": has_children}

    @staticmethod
    def delete(id: str) -> dict:
        """Delete score and its evaluations and guardrail_sets."""
        score = ScoreRepository.get_by_id(id)
        if not score:
            return None

        deleted = {"evaluations": 0, "guardrail_sets": 0, "guardrails": 0}

        with db_connection() as conn:
            # Delete guardrails for guardrail_sets of this score
            gset_ids = [row[0] for row in conn.execute(
                "SELECT id FROM guardrail_sets WHERE score_id = ?", (score["id"],)
            ).fetchall()]
            for gset_id in gset_ids:
                result = conn.execute("DELETE FROM guardrails WHERE set_id = ?", (gset_id,))
                deleted["guardrails"] += result.rowcount

            # Delete guardrail_sets
            result = conn.execute("DELETE FROM guardrail_sets WHERE score_id = ?", (score["id"],))
            deleted["guardrail_sets"] = result.rowcount

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
    def update_status(id: str, status: str, error_message: str = None):
        """Update guardrail set status and optionally error message."""
        now = datetime.now().isoformat()
        with db_connection() as conn:
            if status == "completed":
                conn.execute(
                    "UPDATE guardrail_sets SET status = ?, completed_at = ?, updated_at = ? WHERE id = ?",
                    (status, now, now, id)
                )
            elif status == "failed":
                conn.execute(
                    "UPDATE guardrail_sets SET status = ?, error_message = ?, updated_at = ? WHERE id = ?",
                    (status, error_message, now, id)
                )
            else:
                conn.execute(
                    "UPDATE guardrail_sets SET status = ?, updated_at = ? WHERE id = ?",
                    (status, now, id)
                )

    @staticmethod
    def update_progress(id: str, current: int, total: int = None):
        """Update guardrail set progress. Also updates updated_at for stale detection."""
        now = datetime.now().isoformat()
        with db_connection() as conn:
            if total is not None:
                conn.execute(
                    """UPDATE guardrail_sets SET progress_current = ?, progress_total = ?,
                       updated_at = ? WHERE id = ?""",
                    (current, total, now, id)
                )
            else:
                conn.execute(
                    "UPDATE guardrail_sets SET progress_current = ?, updated_at = ? WHERE id = ?",
                    (current, now, id)
                )

    @staticmethod
    def delete_preview(id: str) -> dict:
        """Preview what will be deleted if this guardrail set is deleted."""
        gset = GuardrailSetRepository.get_by_id(id)
        if not gset:
            return None

        counts = {"guardrails": 0}

        with db_connection() as conn:
            counts["guardrails"] = conn.execute("SELECT COUNT(*) FROM guardrails WHERE set_id = ?", (gset["id"],)).fetchone()[0]

        has_children = counts["guardrails"] > 0
        return {"guardrail_set": {"id": gset["id"], "rules_count": gset.get("rules_count")}, "will_delete": counts, "has_children": has_children}

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


def _row_to_log(row) -> Log:
    """Convert a database row to a Log object"""
    return Log(
        id=row["id"],
        timestamp=row["timestamp"],
        level=row["level"],
        source=row["source"],
        message=row["message"],
        entity_type=row["entity_type"],
        entity_id=row["entity_id"],
        metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else None,
        created_at=row["created_at"],
    )


class LogRepository:
    """CRUD operations for logs"""

    @staticmethod
    def create(log: Log) -> Log:
        """Create a new log entry"""
        init_db()
        with db_connection() as conn:
            conn.execute(
                """INSERT INTO logs (id, timestamp, level, source, message, entity_type, entity_id, metadata_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    log.id,
                    log.timestamp,
                    log.level,
                    log.source,
                    log.message,
                    log.entity_type,
                    log.entity_id,
                    json.dumps(log.metadata) if log.metadata else None,
                )
            )
        return log

    @staticmethod
    def list_all(limit: int = 100, offset: int = 0, level: str = None,
                 entity_type: str = None, entity_id: str = None) -> list[Log]:
        """List logs with optional filters, newest first"""
        init_db()
        query = "SELECT * FROM logs WHERE 1=1"
        params = []

        if level:
            query += " AND level = ?"
            params.append(level)
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with db_connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_row_to_log(row) for row in rows]

    @staticmethod
    def count(level: str = None, entity_type: str = None) -> int:
        """Count logs with optional filters"""
        init_db()
        query = "SELECT COUNT(*) FROM logs WHERE 1=1"
        params = []

        if level:
            query += " AND level = ?"
            params.append(level)
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        with db_connection() as conn:
            return conn.execute(query, params).fetchone()[0]

    @staticmethod
    def cleanup(days: int = 30) -> int:
        """Delete logs older than X days. Returns count of deleted logs."""
        with db_connection() as conn:
            result = conn.execute(
                "DELETE FROM logs WHERE timestamp < datetime('now', ?)",
                (f"-{days} days",)
            )
            return result.rowcount


def _row_to_dataset(row) -> Dataset:
    """Convert a database row to a Dataset object"""
    return Dataset(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        is_builtin=bool(row["is_builtin"]),
        content_hash=row["content_hash"],
        csv_content=row["csv_content"],
        prompt_count=row["prompt_count"] or 0,
        criteria_breakdown=json.loads(row["criteria_breakdown_json"]) if row["criteria_breakdown_json"] else None,
        tenant_id=row["tenant_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_judge(row) -> Judge:
    """Convert a database row to a Judge object"""
    return Judge(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        is_builtin=bool(row["is_builtin"]),
        inherits_from=row["inherits_from"],
        weights=json.loads(row["weights_json"]) if row["weights_json"] else None,
        content_hash=row["content_hash"],
        tenant_id=row["tenant_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class DatasetRepository:
    """CRUD operations for datasets"""

    @staticmethod
    def get_by_id(id: str, tenant_id: str = None) -> Optional[Dataset]:
        """Get dataset by ID"""
        init_db()
        with db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM datasets WHERE id = ? AND (tenant_id IS NULL OR tenant_id = ?)",
                (id, tenant_id)
            ).fetchone()
            if not row:
                # Try prefix match
                rows = conn.execute(
                    "SELECT * FROM datasets WHERE id LIKE ? AND (tenant_id IS NULL OR tenant_id = ?)",
                    (f"{id}%", tenant_id)
                ).fetchall()
                if len(rows) == 1:
                    row = rows[0]
                elif len(rows) > 1:
                    raise ValueError(f"Ambiguous ID '{id}' matches: {[r['id'] for r in rows]}")
        return _row_to_dataset(row) if row else None

    @staticmethod
    def get_by_name(name: str, tenant_id: str = None) -> Optional[Dataset]:
        """Get dataset by name"""
        init_db()
        with db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM datasets WHERE name = ? AND (tenant_id IS NULL OR tenant_id = ?)",
                (name, tenant_id)
            ).fetchone()
        return _row_to_dataset(row) if row else None

    @staticmethod
    def get_by_id_or_name(id_or_name: str, tenant_id: str = None) -> Optional[Dataset]:
        """Get dataset by ID (prefix) or name"""
        dataset = DatasetRepository.get_by_name(id_or_name, tenant_id)
        if dataset:
            return dataset
        return DatasetRepository.get_by_id(id_or_name, tenant_id)

    @staticmethod
    def list_all(tenant_id: str = None) -> list[Dataset]:
        """List all datasets (built-in + user's)"""
        init_db()
        with db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM datasets WHERE tenant_id IS NULL OR tenant_id = ? ORDER BY is_builtin DESC, name",
                (tenant_id,)
            ).fetchall()
        return [_row_to_dataset(row) for row in rows]

    @staticmethod
    def create(dataset: Dataset) -> Dataset:
        """Create a new user dataset"""
        init_db()
        with db_connection() as conn:
            conn.execute(
                """INSERT INTO datasets
                    (id, name, description, is_builtin, content_hash, csv_content, prompt_count, criteria_breakdown_json, tenant_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    dataset.id,
                    dataset.name,
                    dataset.description,
                    1 if dataset.is_builtin else 0,
                    dataset.content_hash,
                    dataset.csv_content,
                    dataset.prompt_count,
                    json.dumps(dataset.criteria_breakdown) if dataset.criteria_breakdown else None,
                    dataset.tenant_id,
                )
            )
        return dataset

    @staticmethod
    def delete(id: str, tenant_id: str = None) -> bool:
        """Delete a user dataset (cannot delete built-in)"""
        dataset = DatasetRepository.get_by_id(id, tenant_id)
        if not dataset:
            return False
        if dataset.is_builtin:
            raise ValueError("Cannot delete built-in dataset")

        with db_connection() as conn:
            conn.execute("DELETE FROM datasets WHERE id = ?", (dataset.id,))
        return True


class JudgeRepository:
    """CRUD operations for judges"""

    @staticmethod
    def get_by_id(id: str, tenant_id: str = None) -> Optional[Judge]:
        """Get judge by ID"""
        init_db()
        with db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM judges WHERE id = ? AND (tenant_id IS NULL OR tenant_id = ?)",
                (id, tenant_id)
            ).fetchone()
            if not row:
                # Try prefix match
                rows = conn.execute(
                    "SELECT * FROM judges WHERE id LIKE ? AND (tenant_id IS NULL OR tenant_id = ?)",
                    (f"{id}%", tenant_id)
                ).fetchall()
                if len(rows) == 1:
                    row = rows[0]
                elif len(rows) > 1:
                    raise ValueError(f"Ambiguous ID '{id}' matches: {[r['id'] for r in rows]}")
        return _row_to_judge(row) if row else None

    @staticmethod
    def get_by_name(name: str, tenant_id: str = None) -> Optional[Judge]:
        """Get judge by name"""
        init_db()
        with db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM judges WHERE name = ? AND (tenant_id IS NULL OR tenant_id = ?)",
                (name, tenant_id)
            ).fetchone()
        return _row_to_judge(row) if row else None

    @staticmethod
    def get_by_id_or_name(id_or_name: str, tenant_id: str = None) -> Optional[Judge]:
        """Get judge by ID (prefix) or name"""
        judge = JudgeRepository.get_by_name(id_or_name, tenant_id)
        if judge:
            return judge
        return JudgeRepository.get_by_id(id_or_name, tenant_id)

    @staticmethod
    def list_all(tenant_id: str = None) -> list[Judge]:
        """List all judges (built-in + user's)"""
        init_db()
        with db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM judges WHERE tenant_id IS NULL OR tenant_id = ? ORDER BY is_builtin DESC, name",
                (tenant_id,)
            ).fetchall()
        return [_row_to_judge(row) for row in rows]

    @staticmethod
    def create(judge: Judge) -> Judge:
        """Create a new user judge"""
        init_db()
        with db_connection() as conn:
            conn.execute(
                """INSERT INTO judges
                    (id, name, description, is_builtin, inherits_from, weights_json, content_hash, tenant_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    judge.id,
                    judge.name,
                    judge.description,
                    1 if judge.is_builtin else 0,
                    judge.inherits_from,
                    json.dumps(judge.weights) if judge.weights else None,
                    judge.content_hash,
                    judge.tenant_id,
                )
            )
        return judge

    @staticmethod
    def update_weights(id: str, weights: dict, tenant_id: str = None) -> bool:
        """Update judge weights (only for user judges)"""
        judge = JudgeRepository.get_by_id(id, tenant_id)
        if not judge:
            return False
        if judge.is_builtin:
            raise ValueError("Cannot modify built-in judge weights")

        with db_connection() as conn:
            conn.execute(
                "UPDATE judges SET weights_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(weights), judge.id)
            )
        return True

    @staticmethod
    def delete(id: str, tenant_id: str = None) -> bool:
        """Delete a user judge (cannot delete built-in)"""
        judge = JudgeRepository.get_by_id(id, tenant_id)
        if not judge:
            return False
        if judge.is_builtin:
            raise ValueError("Cannot delete built-in judge")

        with db_connection() as conn:
            # Delete judge criteria first
            conn.execute("DELETE FROM judge_criteria WHERE judge_id = ?", (judge.id,))
            conn.execute("DELETE FROM judges WHERE id = ?", (judge.id,))
        return True

    @staticmethod
    def get_criteria(judge_id: str) -> list[JudgeCriteria]:
        """Get all criteria implementations for a judge"""
        with db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM judge_criteria WHERE judge_id = ? ORDER BY criteria_id",
                (judge_id,)
            ).fetchall()
        return [
            JudgeCriteria(
                id=row["id"],
                judge_id=row["judge_id"],
                criteria_id=row["criteria_id"],
                version=row["version"],
                author=row["author"],
                prompt_content=row["prompt_content"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    @staticmethod
    def get_criterion_prompt(judge_id: str, criteria_id: str) -> Optional[str]:
        """Get prompt content for a specific criterion from a judge"""
        with db_connection() as conn:
            row = conn.execute(
                "SELECT prompt_content FROM judge_criteria WHERE judge_id = ? AND criteria_id = ?",
                (judge_id, criteria_id)
            ).fetchone()
        return row["prompt_content"] if row else None
