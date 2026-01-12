"""Principles routes (read-only)"""

from fastapi import APIRouter, HTTPException

from srl4c.api.schemas import PrincipleResponse
from srl4c.core.datasets import get_prompt_stats_by_principle
from srl4c.criteria.loader import get_criteria_loader

router = APIRouter(prefix="/principles", tags=["principles"])


def _match_principle_to_stats(principle_id: str, stats: dict) -> dict:
    """Match a principle ID to its stats, handling version suffixes."""
    if principle_id in stats:
        return stats[principle_id]

    # Try without version suffix (e.g., safety.sexual.sexual_content__v1_0 -> safety.sexual.sexual_content)
    base_id = principle_id.rsplit("__", 1)[0] if "__" in principle_id else principle_id
    if base_id in stats:
        return stats[base_id]

    return {"count": 0, "samples": []}


@router.get("/", response_model=list[PrincipleResponse])
async def list_principles():
    """List all design principles with prompt counts and samples."""
    loader = get_criteria_loader()
    registry = loader.load_registry()
    criteria = registry.get("criteria", {})
    stats = get_prompt_stats_by_principle()

    result = []
    for crit_id, crit_data in criteria.items():
        parts = crit_id.split(".")
        category = parts[0] if parts else ""
        subcategory = ".".join(parts[1:-1]) if len(parts) > 2 else (parts[1] if len(parts) > 1 else "")

        principle_stats = _match_principle_to_stats(crit_id, stats)

        result.append(
            PrincipleResponse(
                id=crit_id,
                name=crit_data.get("name", crit_id),
                category=category,
                subcategory=subcategory,
                description=crit_data.get("description"),
                prompt_count=principle_stats["count"],
                sample_prompts=principle_stats["samples"],
            )
        )
    return result


@router.get("/{principle_id}", response_model=PrincipleResponse)
async def get_principle(principle_id: str):
    """Get principle by ID with prompt count and samples."""
    loader = get_criteria_loader()
    registry = loader.load_registry()
    criteria = registry.get("criteria", {})
    stats = get_prompt_stats_by_principle()

    if principle_id in criteria:
        crit_data = criteria[principle_id]
        parts = principle_id.split(".")
        category = parts[0] if parts else ""
        subcategory = ".".join(parts[1:-1]) if len(parts) > 2 else (parts[1] if len(parts) > 1 else "")

        principle_stats = _match_principle_to_stats(principle_id, stats)

        return PrincipleResponse(
            id=principle_id,
            name=crit_data.get("name", principle_id),
            category=category,
            subcategory=subcategory,
            description=crit_data.get("description"),
            prompt_count=principle_stats["count"],
            sample_prompts=principle_stats["samples"],
        )

    raise HTTPException(status_code=404, detail=f"Principle not found: {principle_id}")
