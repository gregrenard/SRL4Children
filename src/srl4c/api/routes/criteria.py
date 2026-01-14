"""Criteria and evaluation judges routes."""

from fastapi import APIRouter, HTTPException

from srl4c.registry import get_registry_loader
from srl4c.api.schemas import (
    CriteriaResponse,
    EvalJudgeResponse,
    EvalJudgeDetailResponse,
    PresetResponse,
)

router = APIRouter(tags=["registry"])


# === Criteria ===

@router.get("/criteria", response_model=list[CriteriaResponse])
async def list_criteria():
    """List all criteria definitions."""
    loader = get_registry_loader()
    criteria = loader.list_criteria()

    return [
        CriteriaResponse(
            id=c.id,
            category=c.category,
            subcategory=c.subcategory,
            name=c.name,
            description=c.description,
            tags=c.tags,
        )
        for c in criteria
    ]


@router.get("/criteria/{criteria_id:path}", response_model=CriteriaResponse)
async def get_criteria(criteria_id: str):
    """Get a specific criteria by ID."""
    loader = get_registry_loader()

    try:
        c = loader.get_criteria(criteria_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Criteria not found: {criteria_id}")

    return CriteriaResponse(
        id=c.id,
        category=c.category,
        subcategory=c.subcategory,
        name=c.name,
        description=c.description,
        tags=c.tags,
    )


# === Evaluation Judges ===

@router.get("/eval-judges", response_model=list[EvalJudgeResponse])
async def list_eval_judges():
    """List evaluation judges (scoring policies)."""
    loader = get_registry_loader()
    judge_names = loader.list_judges()

    result = []
    for name in judge_names:
        judge = loader.get_judge(name)
        result.append(
            EvalJudgeResponse(
                name=judge.name,
                description=judge.description,
                inherits_from=judge.inherits_from,
                weights=judge.weights if judge.weights.get("categories") else None,
                implementation_count=len(judge.implementations),
            )
        )

    return result


@router.get("/eval-judges/{name}", response_model=EvalJudgeDetailResponse)
async def get_eval_judge(name: str):
    """Get evaluation judge details."""
    loader = get_registry_loader()

    try:
        judge = loader.get_judge(name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Evaluation judge not found: {name}")

    # Convert implementations to serializable format
    implementations = {}
    for criteria_id, impl in judge.implementations.items():
        implementations[criteria_id] = {
            "file": impl.file,
            "version": impl.version,
            "author": impl.author,
        }

    return EvalJudgeDetailResponse(
        name=judge.name,
        description=judge.description,
        inherits_from=judge.inherits_from,
        weights=judge.weights,
        implementations=implementations,
    )


# === Presets ===

@router.get("/presets", response_model=list[PresetResponse])
async def list_presets():
    """List criteria presets."""
    loader = get_registry_loader()
    presets = loader.list_presets()

    result = []
    for name, description in presets.items():
        criteria = loader.get_preset(name)
        result.append(
            PresetResponse(
                name=name,
                description=description,
                criteria=criteria,
            )
        )

    return result


@router.get("/presets/{name}", response_model=PresetResponse)
async def get_preset(name: str):
    """Get preset details."""
    loader = get_registry_loader()

    try:
        criteria = loader.get_preset(name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Preset not found: {name}")

    presets = loader.list_presets()
    description = presets.get(name, "")

    return PresetResponse(
        name=name,
        description=description,
        criteria=criteria,
    )
