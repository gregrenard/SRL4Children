"""Core judges logic.

This module provides the shared judge functionality used by both CLI and API.
Judges are first-class objects stored in the database.
"""

from typing import Optional

from srl4c.db.models import Judge, JudgeCriteria
from srl4c.db.repository import JudgeRepository, generate_id


def list_judges(tenant_id: str = None) -> list[Judge]:
    """List all judges (built-in + user created)."""
    return JudgeRepository.list_all(tenant_id)


def get_judge(judge_id_or_name: str, tenant_id: str = None) -> Optional[Judge]:
    """Get a judge by ID or name."""
    return JudgeRepository.get_by_id_or_name(judge_id_or_name, tenant_id)


def get_judge_criteria(judge_id: str) -> list[JudgeCriteria]:
    """Get all criteria implementations for a judge."""
    return JudgeRepository.get_criteria(judge_id)


def create_judge(
    name: str,
    inherits_from: str,
    weights: dict = None,
    description: str = None,
    tenant_id: str = None,
) -> Judge:
    """Create a new user judge with weight overrides.

    User judges inherit implementations from a parent judge and
    can only override weights.

    Args:
        name: Judge name (must be unique)
        inherits_from: Parent judge ID or name to inherit from
        weights: Weight overrides (optional)
        description: Optional description
        tenant_id: Optional tenant ID for multi-tenant

    Returns:
        Created Judge object

    Raises:
        ValueError: If name exists or parent not found
    """
    # Check if name already exists
    existing = JudgeRepository.get_by_name(name, tenant_id)
    if existing:
        raise ValueError(f"Judge '{name}' already exists")

    # Validate parent judge exists
    parent = JudgeRepository.get_by_id_or_name(inherits_from, tenant_id)
    if not parent:
        raise ValueError(f"Parent judge not found: {inherits_from}")

    # Create judge
    judge = Judge(
        id=generate_id(),
        name=name,
        description=description,
        is_builtin=False,
        inherits_from=parent.id,
        weights=weights or {},
        tenant_id=tenant_id,
    )
    JudgeRepository.create(judge)

    return judge


def update_judge_weights(
    judge_id_or_name: str,
    weights: dict,
    tenant_id: str = None,
) -> Judge:
    """Update weights for a user judge.

    Args:
        judge_id_or_name: Judge ID or name
        weights: New weight configuration
        tenant_id: Optional tenant ID

    Returns:
        Updated Judge object

    Raises:
        ValueError: If judge not found or is built-in
    """
    judge = JudgeRepository.get_by_id_or_name(judge_id_or_name, tenant_id)
    if not judge:
        raise ValueError(f"Judge not found: {judge_id_or_name}")

    JudgeRepository.update_weights(judge.id, weights, tenant_id)

    # Return updated judge
    return JudgeRepository.get_by_id(judge.id, tenant_id)


def delete_judge(judge_id_or_name: str, tenant_id: str = None) -> bool:
    """Delete a user judge.

    Args:
        judge_id_or_name: Judge ID or name
        tenant_id: Optional tenant ID

    Returns:
        True if deleted

    Raises:
        ValueError: If judge is built-in or not found
    """
    judge = JudgeRepository.get_by_id_or_name(judge_id_or_name, tenant_id)
    if not judge:
        raise ValueError(f"Judge not found: {judge_id_or_name}")

    return JudgeRepository.delete(judge.id, tenant_id)


def get_resolved_weights(judge_id_or_name: str, tenant_id: str = None) -> dict:
    """Get resolved weights for a judge (with inheritance applied).

    Walks up the inheritance chain and merges weights.

    Args:
        judge_id_or_name: Judge ID or name
        tenant_id: Optional tenant ID

    Returns:
        Merged weight configuration

    Raises:
        ValueError: If judge not found
    """
    judge = JudgeRepository.get_by_id_or_name(judge_id_or_name, tenant_id)
    if not judge:
        raise ValueError(f"Judge not found: {judge_id_or_name}")

    # Start with empty weights
    resolved = {"categories": {}, "subcategories": {}, "criteria": {}}

    # Build inheritance chain
    chain = []
    current = judge
    while current:
        chain.append(current)
        if current.inherits_from:
            current = JudgeRepository.get_by_id(current.inherits_from, tenant_id)
        else:
            current = None

    # Apply weights from root to leaf (so child overrides parent)
    for j in reversed(chain):
        if j.weights:
            for level in ["categories", "subcategories", "criteria"]:
                if level in j.weights:
                    resolved[level].update(j.weights[level])

    return resolved
