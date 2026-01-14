"""
Sync service for populating DB from files.

Handles:
- Built-in datasets: Sync from data/datasets/*.csv
- Built-in judges: Sync from registry.yml + prompt files
"""

import csv
import hashlib
import json
import logging
from pathlib import Path

import yaml

from srl4c.db.models import db_connection
from srl4c.db.repository import generate_id
from srl4c.paths import DATA_DIR, DATASETS_DIR, REGISTRY_FILE

logger = logging.getLogger(__name__)


def compute_file_hash(file_path: Path) -> str:
    """Compute MD5 hash of a file."""
    return hashlib.md5(file_path.read_bytes()).hexdigest()


def compute_combined_hash(contents: list[str]) -> str:
    """Compute MD5 hash of combined content."""
    combined = "".join(contents)
    return hashlib.md5(combined.encode()).hexdigest()


def analyze_csv_content(csv_content: str) -> tuple[int, dict[str, int]]:
    """Analyze CSV content and return prompt count and criteria breakdown."""
    lines = csv_content.strip().split("\n")
    if not lines:
        return 0, {}

    # Detect delimiter
    first_line = lines[0]
    delimiter = ";" if ";" in first_line and "," not in first_line else ","

    reader = csv.DictReader(lines, delimiter=delimiter)
    breakdown: dict[str, int] = {}
    count = 0

    for row in reader:
        count += 1
        criteria_id = row.get("Category") or row.get("criteria_id") or row.get("category")
        if criteria_id:
            # Strip version suffix if present
            if "__" in criteria_id:
                criteria_id = criteria_id.split("__")[0]
            breakdown[criteria_id] = breakdown.get(criteria_id, 0) + 1

    return count, breakdown


# =============================================================================
# Dataset Sync
# =============================================================================


def sync_builtin_datasets(tenant_id: str = None) -> int:
    """
    Sync built-in datasets from filesystem to DB.

    Returns number of datasets synced/updated.
    """
    if not DATASETS_DIR.exists():
        logger.warning(f"Datasets directory not found: {DATASETS_DIR}")
        return 0

    synced = 0

    for csv_file in sorted(DATASETS_DIR.glob("*.csv")):
        # Skip hidden files
        if csv_file.name.startswith(".") or csv_file.name.startswith("_"):
            continue

        dataset_name = csv_file.stem
        content_hash = compute_file_hash(csv_file)

        with db_connection() as conn:
            # Check if exists
            existing = conn.execute(
                "SELECT id, content_hash FROM datasets WHERE name = ? AND (tenant_id IS NULL OR tenant_id = ?)",
                (dataset_name, tenant_id)
            ).fetchone()

            if existing:
                # Check if hash changed
                if existing["content_hash"] == content_hash:
                    continue  # No change

                # Update existing
                csv_content = csv_file.read_text(encoding="utf-8")
                prompt_count, breakdown = analyze_csv_content(csv_content)

                conn.execute(
                    """UPDATE datasets SET
                        content_hash = ?, csv_content = ?, prompt_count = ?,
                        criteria_breakdown_json = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                    (content_hash, csv_content, prompt_count, json.dumps(breakdown), existing["id"])
                )
                logger.info(f"Updated dataset: {dataset_name}")
                synced += 1
            else:
                # Insert new
                csv_content = csv_file.read_text(encoding="utf-8")
                prompt_count, breakdown = analyze_csv_content(csv_content)

                conn.execute(
                    """INSERT INTO datasets
                        (id, name, is_builtin, content_hash, csv_content, prompt_count, criteria_breakdown_json, tenant_id)
                    VALUES (?, ?, 1, ?, ?, ?, ?, ?)""",
                    (generate_id(), dataset_name, content_hash, csv_content, prompt_count, json.dumps(breakdown), tenant_id)
                )
                logger.info(f"Added dataset: {dataset_name}")
                synced += 1

    return synced


# =============================================================================
# Judge Sync
# =============================================================================


def compute_judge_content_hash(judge_def: dict) -> str:
    """Compute combined hash of all prompt files for a judge."""
    implementations = judge_def.get("implementations", {})
    if not implementations:
        return hashlib.md5(b"").hexdigest()

    contents = []
    for criteria_id in sorted(implementations.keys()):
        impl = implementations[criteria_id]
        file_path = DATA_DIR / impl["file"]
        if file_path.exists():
            contents.append(file_path.read_text(encoding="utf-8"))

    return compute_combined_hash(contents)


def sync_builtin_judges(tenant_id: str = None) -> int:
    """
    Sync built-in judges from registry.yml to DB.

    Returns number of judges synced/updated.
    """
    if not REGISTRY_FILE.exists():
        logger.warning(f"Registry file not found: {REGISTRY_FILE}")
        return 0

    with open(REGISTRY_FILE, encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    judges_data = registry.get("judges", {})
    synced = 0
    judge_id_map = {}  # name -> id

    # First pass: create/update judges
    for judge_name, judge_def in judges_data.items():
        content_hash = compute_judge_content_hash(judge_def)
        weights_json = json.dumps(judge_def.get("weights", {}))

        with db_connection() as conn:
            existing = conn.execute(
                "SELECT id, content_hash FROM judges WHERE name = ? AND (tenant_id IS NULL OR tenant_id = ?)",
                (judge_name, tenant_id)
            ).fetchone()

            if existing:
                judge_id_map[judge_name] = existing["id"]

                if existing["content_hash"] == content_hash:
                    continue

                # Update existing judge
                conn.execute(
                    """UPDATE judges SET
                        description = ?, weights_json = ?, content_hash = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                    (judge_def.get("description", ""), weights_json, content_hash, existing["id"])
                )

                # Reload all criteria for this judge
                _sync_judge_criteria(conn, existing["id"], judge_def)
                logger.info(f"Updated judge: {judge_name}")
                synced += 1
            else:
                # Insert new judge
                judge_id = generate_id()
                judge_id_map[judge_name] = judge_id

                conn.execute(
                    """INSERT INTO judges
                        (id, name, description, is_builtin, weights_json, content_hash, tenant_id)
                    VALUES (?, ?, ?, 1, ?, ?, ?)""",
                    (judge_id, judge_name, judge_def.get("description", ""),
                     weights_json, content_hash, tenant_id)
                )

                # Add criteria for this judge
                _sync_judge_criteria(conn, judge_id, judge_def)
                logger.info(f"Added judge: {judge_name}")
                synced += 1

    # Second pass: resolve inherits_from references
    for judge_name, judge_def in judges_data.items():
        inherits_from = judge_def.get("inherits_from")
        if inherits_from and inherits_from in judge_id_map:
            with db_connection() as conn:
                conn.execute(
                    "UPDATE judges SET inherits_from = ? WHERE name = ? AND (tenant_id IS NULL OR tenant_id = ?)",
                    (judge_id_map[inherits_from], judge_name, tenant_id)
                )

    # Third pass: inherit implementations from parent for judges without their own
    for judge_name, judge_def in judges_data.items():
        if not judge_def.get("implementations") and judge_def.get("inherits_from"):
            _inherit_implementations(judge_id_map[judge_name], judge_id_map, judges_data)

    return synced


def _inherit_implementations(judge_id: str, judge_id_map: dict, judges_data: dict):
    """Copy implementations from parent to child judge (recursive up the chain)."""
    with db_connection() as conn:
        # Check if this judge already has implementations
        existing = conn.execute(
            "SELECT COUNT(*) as cnt FROM judge_criteria WHERE judge_id = ?",
            (judge_id,)
        ).fetchone()

        if existing["cnt"] > 0:
            return  # Already has implementations

        # Find parent
        judge = conn.execute(
            "SELECT name, inherits_from FROM judges WHERE id = ?", (judge_id,)
        ).fetchone()

        if not judge or not judge["inherits_from"]:
            return

        parent_id = judge["inherits_from"]

        # Recursively ensure parent has implementations first
        parent_judge = conn.execute(
            "SELECT name FROM judges WHERE id = ?", (parent_id,)
        ).fetchone()

        if parent_judge:
            parent_name = parent_judge["name"]
            if parent_name in judges_data and not judges_data[parent_name].get("implementations"):
                _inherit_implementations(parent_id, judge_id_map, judges_data)

        # Copy parent's implementations to this judge (row by row to get unique IDs)
        parent_criteria = conn.execute(
            "SELECT criteria_id, version, author, prompt_content, created_at FROM judge_criteria WHERE judge_id = ?",
            (parent_id,)
        ).fetchall()

        for row in parent_criteria:
            conn.execute(
                """INSERT INTO judge_criteria (id, judge_id, criteria_id, version, author, prompt_content, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (generate_id(), judge_id, row["criteria_id"], row["version"], row["author"],
                 row["prompt_content"], row["created_at"])
            )

        logger.info(f"Inherited {len(parent_criteria)} implementations for judge {judge['name']}")


def _sync_judge_criteria(conn, judge_id: str, judge_def: dict):
    """Sync criteria implementations for a judge (within existing connection)."""
    # Delete existing criteria for this judge
    conn.execute("DELETE FROM judge_criteria WHERE judge_id = ?", (judge_id,))

    implementations = judge_def.get("implementations", {})
    for criteria_id, impl in implementations.items():
        file_path = DATA_DIR / impl["file"]
        if not file_path.exists():
            logger.warning(f"Prompt file not found: {file_path}")
            continue

        prompt_content = file_path.read_text(encoding="utf-8")

        conn.execute(
            """INSERT INTO judge_criteria
                (id, judge_id, criteria_id, version, author, prompt_content, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (generate_id(), judge_id, criteria_id,
             impl.get("version", ""), impl.get("author", ""), prompt_content,
             impl.get("created", None))
        )


# =============================================================================
# Main Sync Function
# =============================================================================


def sync_all(tenant_id: str = None) -> dict[str, int]:
    """
    Sync all built-in data from files to DB.

    Returns dict with counts of synced entities.
    """
    logger.info("Starting sync of built-in data...")

    datasets_synced = sync_builtin_datasets(tenant_id)
    judges_synced = sync_builtin_judges(tenant_id)

    logger.info(f"Sync complete: {datasets_synced} datasets, {judges_synced} judges")

    return {
        "datasets": datasets_synced,
        "judges": judges_synced,
    }
