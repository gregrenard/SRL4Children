"""Core attack logic.

This module provides the shared attack functionality used by both CLI and API.
"""

import io
import time
from typing import Optional, Callable

import pandas as pd

from srl4c.db.models import Attack, Record
from srl4c.db.repository import (
    EndpointRepository, AttackRepository, RecordRepository, DatasetRepository, generate_id
)
from srl4c.adapters.openai import OpenAIAdapter
from srl4c.adapters.simple import SimpleAdapter
from srl4c.core.logger import Logger


def load_dataset_df(csv_content: str) -> pd.DataFrame:
    """Load dataset from CSV content string and normalize column names."""
    df = pd.read_csv(io.StringIO(csv_content))

    # Find columns
    prompt_col = next((c for c in df.columns if c.lower() in ["prompt", "question"]), None)
    cat_col = next((c for c in df.columns if c.lower() in ["category", "cat"]), None)
    id_col = next((c for c in df.columns if c.lower() in ["promptid", "id", "uid"]), None)

    if not prompt_col:
        raise ValueError("Dataset must have a 'Prompt' or 'Question' column")

    # Normalize
    result = pd.DataFrame()
    result["prompt"] = df[prompt_col]
    result["criteria_id"] = df[cat_col] if cat_col else ""
    result["id"] = df[id_col] if id_col else range(len(df))

    return result


def create_adapter(endpoint):
    """Create the appropriate adapter for an endpoint."""
    if endpoint.type == "openai":
        return OpenAIAdapter(endpoint.base_url, endpoint.api_key_env, endpoint.config)
    else:
        return SimpleAdapter(endpoint.base_url, endpoint.api_key_env, endpoint.config)


def create_attack(endpoint_name: str, dataset_name: str) -> str:
    """Create an attack job record.

    Validates inputs (endpoint exists, dataset exists), creates DB record with
    status='pending', and returns the attack_id.

    Used by both CLI and API.

    Args:
        endpoint_name: Endpoint ID or name
        dataset_name: Dataset ID or name

    Returns:
        attack_id: The ID of the created attack

    Raises:
        ValueError: If endpoint or dataset not found
    """
    # Validate endpoint
    endpoint = EndpointRepository.get_by_id_or_name(endpoint_name)
    if not endpoint:
        raise ValueError(f"Endpoint not found: {endpoint_name}")

    # Validate dataset (from DB)
    dataset = DatasetRepository.get_by_id_or_name(dataset_name)
    if not dataset:
        raise ValueError(f"Dataset not found: {dataset_name}")

    if not dataset.csv_content:
        raise ValueError(f"Dataset '{dataset_name}' has no content")

    # Load dataset to get prompt count
    df = load_dataset_df(dataset.csv_content)

    # Create attack record
    attack_id = generate_id()
    attack = Attack(
        id=attack_id,
        endpoint_id=endpoint.id,
        dataset_id=dataset.id,
        status="pending",
        total_prompts=len(df),
        completed_prompts=0,
        progress_current=0,
        progress_total=len(df),
    )
    AttackRepository.create(attack)

    Logger.info(
        "attack",
        f"Attack created: {len(df)} prompts from '{dataset.name}' to '{endpoint.name}'",
        entity_type="attack",
        entity_id=attack_id,
        metadata={"endpoint_id": endpoint.id, "dataset_id": dataset.id, "total_prompts": len(df)}
    )

    return attack_id


def run_attack(
    attack_id: str,
    on_progress: Optional[Callable[[int, int], None]] = None,
    delay_between_requests: float = 0.1,
) -> None:
    """Execute an attack job.

    Updates status to 'running', sends prompts to endpoint, updates progress
    in DB as it runs, and updates status to 'completed' or 'failed'.

    Called after create_attack(). Can be run synchronously (CLI) or in a
    background task (API).

    Args:
        attack_id: The attack ID to run
        on_progress: Optional callback(current, total) for progress updates
        delay_between_requests: Delay between requests to avoid rate limiting

    Raises:
        ValueError: If attack not found
        Exception: Re-raises any exception after marking attack as failed
    """
    # Get attack record
    attack = AttackRepository.get_by_id(attack_id)
    if not attack:
        raise ValueError(f"Attack not found: {attack_id}")

    # Update status to running
    AttackRepository.update_status(attack_id, "running")
    Logger.info(
        "attack",
        f"Attack started: sending prompts to endpoint",
        entity_type="attack",
        entity_id=attack_id,
    )

    try:
        # Get endpoint
        endpoint = EndpointRepository.get_by_id(attack.endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint not found: {attack.endpoint_id}")

        # Get dataset from DB
        dataset = DatasetRepository.get_by_id(attack.dataset_id)
        if not dataset:
            raise ValueError(f"Dataset not found: {attack.dataset_id}")

        # Load dataset content
        df = load_dataset_df(dataset.csv_content)

        # Create adapter
        adapter = create_adapter(endpoint)

        completed = 0
        errors = 0
        total = len(df)

        for i, (_, row) in enumerate(df.iterrows()):
            prompt = str(row["prompt"])
            criteria_id = str(row["criteria_id"]) if row["criteria_id"] else ""

            # Create record
            record = Record(
                id=generate_id(),
                attack_id=attack_id,
                prompt=prompt,
                criteria_id=criteria_id,
            )
            RecordRepository.create(record)

            # Send to endpoint
            try:
                response = adapter.send_message(prompt)
                RecordRepository.update_response(record.id, response=response)
                completed += 1
            except Exception as e:
                RecordRepository.update_response(record.id, error=str(e))
                errors += 1

            # Update progress in DB
            current = i + 1
            AttackRepository.update_progress(attack_id, current, total)

            # Callback for CLI progress display
            if on_progress:
                on_progress(current, total)

            # Rate limiting delay
            if delay_between_requests > 0:
                time.sleep(delay_between_requests)

        # Mark as completed
        AttackRepository.update_status(attack_id, "completed", completed_prompts=completed)
        EndpointRepository.update_last_used(endpoint.id)

        Logger.info(
            "attack",
            f"Attack completed: {completed}/{total} prompts successful, {errors} errors",
            entity_type="attack",
            entity_id=attack_id,
            metadata={"completed": completed, "errors": errors, "total": total}
        )

    except Exception as e:
        # Mark as failed
        AttackRepository.update_status(attack_id, "failed", error_message=str(e))
        Logger.error(
            "attack",
            f"Attack failed: {str(e)}",
            entity_type="attack",
            entity_id=attack_id,
            metadata={"error": str(e)}
        )
        raise


def get_attack_records(
    attack_id: str,
    page: int = 1,
    page_size: int = 50,
    criteria_filter: str = None,
) -> dict:
    """Get paginated records for an attack.

    Args:
        attack_id: Attack ID
        page: Page number (1-indexed)
        page_size: Records per page
        criteria_filter: Optional criteria ID substring filter

    Returns:
        dict with attack_id, total, page, page_size, records

    Raises:
        ValueError: If attack not found
    """
    attack = AttackRepository.get_by_id(attack_id)
    if not attack:
        raise ValueError(f"Attack not found: {attack_id}")

    # Get all records for this attack
    all_records = RecordRepository.get_by_attack(attack.id)

    # Filter by criteria if specified
    if criteria_filter:
        all_records = [r for r in all_records if r.criteria_id and criteria_filter in r.criteria_id]

    total = len(all_records)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    page_records = all_records[start:end]

    return {
        "attack_id": attack.id,
        "total": total,
        "page": page,
        "page_size": page_size,
        "records": [
            {
                "id": r.id,
                "criteria_id": r.criteria_id or "",
                "prompt": r.prompt,
                "response": r.response,
                "error": r.error,
            }
            for r in page_records
        ],
    }
