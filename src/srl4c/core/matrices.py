"""Core matrix logic.

This module provides the shared matrix functionality used by both CLI and API.
"""

from typing import Optional

from srl4c.db.models import ScoringMatrix, ScoringMatrixEntry
from srl4c.db.repository import ScoringMatrixRepository, generate_id


def list_matrices(tenant_id: str = None) -> list[ScoringMatrix]:
    """List all scoring matrices."""
    return ScoringMatrixRepository.list_all(tenant_id)


def get_matrix(name_or_id: str, tenant_id: str = None) -> Optional[ScoringMatrix]:
    """Get a matrix by name or ID."""
    return ScoringMatrixRepository.get_by_id_or_name(name_or_id, tenant_id)


def get_matrix_entries(matrix_id: str) -> list[ScoringMatrixEntry]:
    """Get all entries for a matrix."""
    return ScoringMatrixRepository.get_entries(matrix_id)


def create_matrix(
    name: str,
    description: str = None,
    tenant_id: str = None,
) -> ScoringMatrix:
    """Create a new scoring matrix.

    Args:
        name: Matrix name (must be unique)
        description: Optional description
        tenant_id: Optional tenant ID

    Returns:
        The created matrix

    Raises:
        ValueError: If matrix name already exists
    """
    # Check for existing
    existing = ScoringMatrixRepository.get_by_name(name, tenant_id)
    if existing:
        raise ValueError(f"Matrix '{name}' already exists")

    matrix = ScoringMatrix(
        id=generate_id(),
        name=name,
        description=description,
        is_builtin=False,
        tenant_id=tenant_id,
    )

    ScoringMatrixRepository.create(matrix)
    return matrix


def update_matrix_entries(
    name_or_id: str,
    entries: list[dict],
    tenant_id: str = None,
) -> int:
    """Update all entries for a matrix (replaces existing).

    Args:
        name_or_id: Matrix name or ID
        entries: List of entry dicts with keys: behavior_id, age_group, presence_level, score
        tenant_id: Optional tenant ID

    Returns:
        Number of entries updated

    Raises:
        ValueError: If matrix not found or is built-in
    """
    matrix = ScoringMatrixRepository.get_by_id_or_name(name_or_id, tenant_id)
    if not matrix:
        raise ValueError(f"Matrix not found: {name_or_id}")

    if matrix.is_builtin:
        raise ValueError("Cannot modify built-in matrix")

    # Convert to ScoringMatrixEntry objects
    entry_objects = [
        ScoringMatrixEntry(
            id=generate_id(),
            matrix_id=matrix.id,
            behavior_id=e["behavior_id"],
            age_group=e["age_group"],
            presence_level=e["presence_level"],
            score=e["score"],
        )
        for e in entries
    ]

    ScoringMatrixRepository.set_entries(matrix.id, entry_objects)
    return len(entry_objects)


def delete_matrix(name_or_id: str, tenant_id: str = None) -> bool:
    """Delete a scoring matrix.

    Args:
        name_or_id: Matrix name or ID
        tenant_id: Optional tenant ID

    Returns:
        True if deleted

    Raises:
        ValueError: If matrix not found or is built-in
    """
    matrix = ScoringMatrixRepository.get_by_id_or_name(name_or_id, tenant_id)
    if not matrix:
        raise ValueError(f"Matrix not found: {name_or_id}")

    if matrix.is_builtin:
        raise ValueError("Cannot delete built-in matrix")

    return ScoringMatrixRepository.delete(matrix.id, tenant_id)


def clone_matrix(
    source_name_or_id: str,
    new_name: str,
    description: str = None,
    tenant_id: str = None,
) -> ScoringMatrix:
    """Clone an existing matrix with a new name.

    Useful for creating custom matrices based on built-in ones.

    Args:
        source_name_or_id: Source matrix name or ID
        new_name: Name for the new matrix
        description: Optional description (defaults to "Clone of {source}")
        tenant_id: Optional tenant ID

    Returns:
        The created matrix

    Raises:
        ValueError: If source not found or new name already exists
    """
    source = ScoringMatrixRepository.get_by_id_or_name(source_name_or_id, tenant_id)
    if not source:
        raise ValueError(f"Source matrix not found: {source_name_or_id}")

    # Check new name doesn't exist
    existing = ScoringMatrixRepository.get_by_name(new_name, tenant_id)
    if existing:
        raise ValueError(f"Matrix '{new_name}' already exists")

    # Create new matrix
    new_matrix = ScoringMatrix(
        id=generate_id(),
        name=new_name,
        description=description or f"Clone of {source.name}",
        is_builtin=False,
        tenant_id=tenant_id,
    )
    ScoringMatrixRepository.create(new_matrix)

    # Copy entries
    source_entries = ScoringMatrixRepository.get_entries(source.id)
    new_entries = [
        ScoringMatrixEntry(
            id=generate_id(),
            matrix_id=new_matrix.id,
            behavior_id=e.behavior_id,
            age_group=e.age_group,
            presence_level=e.presence_level,
            score=e.score,
        )
        for e in source_entries
    ]

    if new_entries:
        ScoringMatrixRepository.set_entries(new_matrix.id, new_entries)

    return new_matrix
