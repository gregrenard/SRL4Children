"""Core attack logic.

This module provides the shared attack functionality used by both CLI and API.
"""

import time
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from srl4c.adapters.openai import OpenAIAdapter
from srl4c.adapters.simple import SimpleAdapter
from srl4c.core.logger import Logger
from srl4c.db.models import Attack, Record
from srl4c.db.repository import (
    AttackRepository,
    EndpointRepository,
    RecordRepository,
    generate_id,
)


def get_dataset_path(name: str) -> Path | None:
    """Get path to dataset by name."""
    from srl4c.cli.commands.dataset import get_builtin_datasets

    datasets = get_builtin_datasets()
    if name in datasets:
        return datasets[name]["path"]

    # Check custom datasets
    custom_dir = Path.home() / ".srl4c" / "datasets"
    custom_path = custom_dir / f"{name}.csv"
    if custom_path.exists():
        return custom_path
    return None


def load_dataset(path: Path) -> pd.DataFrame:
    """Load dataset and normalize column names."""
    df = pd.read_csv(path)

    # Find columns
    prompt_col = next((c for c in df.columns if c.lower() in ["prompt", "question"]), None)
    cat_col = next((c for c in df.columns if c.lower() in ["category", "cat"]), None)
    id_col = next((c for c in df.columns if c.lower() in ["promptid", "id", "uid"]), None)

    if not prompt_col:
        raise ValueError("Dataset must have a 'Prompt' or 'Question' column")

    # Normalize
    result = pd.DataFrame()
    result["prompt"] = df[prompt_col]
    result["principle_id"] = df[cat_col] if cat_col else ""
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
        dataset_name: Dataset name

    Returns:
        attack_id: The ID of the created attack

    Raises:
        ValueError: If endpoint or dataset not found
    """
    # Validate endpoint
    endpoint = EndpointRepository.get_by_id_or_name(endpoint_name)
    if not endpoint:
        raise ValueError(f"Endpoint not found: {endpoint_name}")

    # Validate dataset
    dataset_path = get_dataset_path(dataset_name)
    if not dataset_path:
        raise ValueError(f"Dataset not found: {dataset_name}")

    # Load dataset to get prompt count
    df = load_dataset(dataset_path)

    # Create attack record
    attack_id = generate_id()
    attack = Attack(
        id=attack_id,
        endpoint_id=endpoint.id,
        dataset_name=dataset_name,
        status="pending",
        total_prompts=len(df),
        completed_prompts=0,
        progress_current=0,
        progress_total=len(df),
    )
    AttackRepository.create(attack)

    Logger.info(
        "attack",
        f"Attack created: {len(df)} prompts from '{dataset_name}' to '{endpoint.name}'",
        entity_type="attack",
        entity_id=attack_id,
        metadata={
            "endpoint_id": endpoint.id,
            "dataset": dataset_name,
            "total_prompts": len(df),
        },
    )

    return attack_id


def run_attack(
    attack_id: str,
    on_progress: Callable[[int, int], None] | None = None,
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
        "Attack started: sending prompts to endpoint",
        entity_type="attack",
        entity_id=attack_id,
    )

    try:
        # Get endpoint
        endpoint = EndpointRepository.get_by_id(attack.endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint not found: {attack.endpoint_id}")

        # Load dataset
        dataset_path = get_dataset_path(attack.dataset_name)
        df = load_dataset(dataset_path)

        # Create adapter
        adapter = create_adapter(endpoint)

        completed = 0
        errors = 0
        total = len(df)

        for i, (_, row) in enumerate(df.iterrows()):
            prompt = str(row["prompt"])
            principle_id = str(row["principle_id"]) if row["principle_id"] else ""

            # Create record
            record = Record(
                id=generate_id(),
                attack_id=attack_id,
                prompt=prompt,
                principle_id=principle_id,
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
            metadata={"completed": completed, "errors": errors, "total": total},
        )

    except Exception as e:
        # Mark as failed
        AttackRepository.update_status(attack_id, "failed", error_message=str(e))
        Logger.error(
            "attack",
            f"Attack failed: {str(e)}",
            entity_type="attack",
            entity_id=attack_id,
            metadata={"error": str(e)},
        )
        raise
