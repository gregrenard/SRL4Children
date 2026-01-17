"""Core datasets logic.

This module provides the shared dataset functionality used by both CLI and API.
Datasets are first-class objects stored in the database.
"""

import csv
import hashlib

from srl4c.db.models import Dataset
from srl4c.db.repository import DatasetRepository, generate_id
from srl4c.db.sync import analyze_csv_content


def list_datasets(tenant_id: str = None) -> list[Dataset]:
    """List all datasets (built-in + user uploads)."""
    return DatasetRepository.list_all(tenant_id)


def get_dataset(dataset_id_or_name: str, tenant_id: str = None) -> Dataset | None:
    """Get a dataset by ID or name."""
    return DatasetRepository.get_by_id_or_name(dataset_id_or_name, tenant_id)


def create_dataset(
    name: str,
    csv_content: str,
    description: str = None,
    tenant_id: str = None,
) -> Dataset:
    """Create a new user dataset.

    Args:
        name: Dataset name (must be unique)
        csv_content: CSV content string
        description: Optional description
        tenant_id: Optional tenant ID for multi-tenant

    Returns:
        Created Dataset object

    Raises:
        ValueError: If name exists or CSV is invalid
    """
    # Check if name already exists
    existing = DatasetRepository.get_by_name(name, tenant_id)
    if existing:
        raise ValueError(f"Dataset '{name}' already exists")

    # Analyze CSV content
    try:
        prompt_count, breakdown = analyze_csv_content(csv_content)
    except Exception as e:
        raise ValueError(f"Invalid CSV content: {e}")

    if prompt_count == 0:
        raise ValueError("CSV has no valid prompts")

    # Create dataset
    content_hash = hashlib.md5(csv_content.encode()).hexdigest()
    dataset = Dataset(
        id=generate_id(),
        name=name,
        description=description,
        is_builtin=False,
        content_hash=content_hash,
        csv_content=csv_content,
        prompt_count=prompt_count,
        criteria_breakdown=breakdown,
        tenant_id=tenant_id,
    )
    DatasetRepository.create(dataset)

    return dataset


def delete_dataset(dataset_id_or_name: str, tenant_id: str = None) -> bool:
    """Delete a user dataset.

    Args:
        dataset_id_or_name: Dataset ID or name
        tenant_id: Optional tenant ID

    Returns:
        True if deleted

    Raises:
        ValueError: If dataset is built-in or not found
    """
    dataset = DatasetRepository.get_by_id_or_name(dataset_id_or_name, tenant_id)
    if not dataset:
        raise ValueError(f"Dataset not found: {dataset_id_or_name}")

    return DatasetRepository.delete(dataset.id, tenant_id)


def get_dataset_prompts(
    dataset_id_or_name: str,
    page: int = 1,
    page_size: int = 50,
    tenant_id: str = None,
) -> dict:
    """Get prompts from a dataset with pagination.

    Args:
        dataset_id_or_name: Dataset ID or name
        page: Page number (1-indexed)
        page_size: Number of prompts per page
        tenant_id: Optional tenant ID

    Returns:
        Dict with dataset_id, dataset_name, total, page, page_size, prompts

    Raises:
        ValueError: If dataset not found or has no content
    """
    dataset = DatasetRepository.get_by_id_or_name(dataset_id_or_name, tenant_id)
    if not dataset:
        raise ValueError(f"Dataset not found: {dataset_id_or_name}")

    if not dataset.csv_content:
        raise ValueError("Dataset has no content")

    # Parse CSV content
    prompts = []
    lines = dataset.csv_content.strip().split("\n")
    if lines:
        first_line = lines[0]
        delimiter = ";" if ";" in first_line and "," not in first_line else ","
        reader = csv.DictReader(lines, delimiter=delimiter)

        for row in reader:
            prompt_id = row.get("PromptID") or row.get("prompt_id") or row.get("id") or ""
            criteria_id = row.get("Category") or row.get("criteria_id") or row.get("category") or ""
            prompt_text = row.get("Prompt") or row.get("prompt") or ""

            if prompt_text:
                # Strip version suffix if present
                if "__" in criteria_id:
                    criteria_id = criteria_id.split("__")[0]

                prompts.append(
                    {
                        "id": prompt_id,
                        "criteria_id": criteria_id,
                        "prompt": prompt_text,
                    }
                )

    total = len(prompts)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    prompts_page = prompts[start:end]

    return {
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "total": total,
        "page": page,
        "page_size": page_size,
        "prompts": prompts_page,
    }
