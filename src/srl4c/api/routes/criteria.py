"""Criteria and evaluation judges routes.

Criteria definitions stay in registry.yml (abstract definitions).
Judges are first-class objects in DB (synced from registry for built-in).
"""

from fastapi import APIRouter, HTTPException

from srl4c.api.schemas import (
    CriteriaResponse,
    EvalJudgeDetailResponse,
    EvalJudgeResponse,
    JudgeCreate,
    JudgeUpdateWeights,
    PresetResponse,
)
from srl4c.core.judges import (
    create_judge,
    delete_judge,
    get_judge,
    get_judge_criteria,
    get_resolved_weights,
    list_judges,
    update_judge_weights,
)
from srl4c.db.repository import JudgeRepository
from srl4c.registry import get_registry_loader

router = APIRouter(tags=["registry"])


# === Criteria (from registry.yml) ===


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


# === Evaluation Judges (from DB) ===


def _judge_to_response(judge) -> EvalJudgeResponse:
    """Convert Judge model to response schema."""
    # Get parent name for display
    parent_name = None
    if judge.inherits_from:
        parent = JudgeRepository.get_by_id(judge.inherits_from)
        if parent:
            parent_name = parent.name

    # Get implementation count (all judges now have implementations in DB)
    criteria = get_judge_criteria(judge.id)
    impl_count = len(criteria)

    return EvalJudgeResponse(
        id=judge.id,
        name=judge.name,
        description=judge.description,
        is_builtin=judge.is_builtin,
        inherits_from=judge.inherits_from,
        inherits_from_name=parent_name,
        weights=judge.weights if judge.weights else None,
        implementation_count=impl_count,
        created_at=str(judge.created_at) if judge.created_at else None,
        updated_at=str(judge.updated_at) if judge.updated_at else None,
    )


@router.get("/eval-judges", response_model=list[EvalJudgeResponse])
async def list_eval_judges():
    """List evaluation judges (built-in + user created)."""
    judges = list_judges()
    return [_judge_to_response(j) for j in judges]


@router.post("/eval-judges", response_model=EvalJudgeResponse, status_code=201)
async def create_eval_judge(request: JudgeCreate):
    """Create a new user judge with weight overrides."""
    try:
        judge = create_judge(
            name=request.name,
            inherits_from=request.inherits_from,
            weights=request.weights,
            description=request.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _judge_to_response(judge)


@router.get("/eval-judges/{judge_id}", response_model=EvalJudgeDetailResponse)
async def get_eval_judge(judge_id: str):
    """Get evaluation judge details by ID or name."""
    judge = get_judge(judge_id)
    if not judge:
        raise HTTPException(status_code=404, detail=f"Evaluation judge not found: {judge_id}")

    # Get parent name for display
    parent_name = None
    if judge.inherits_from:
        parent = JudgeRepository.get_by_id(judge.inherits_from)
        if parent:
            parent_name = parent.name

    # Get resolved weights (with inheritance)
    resolved_weights = get_resolved_weights(judge.id)

    # Get criteria implementations (all judges now have implementations in DB)
    criteria = get_judge_criteria(judge.id)
    implementations = [
        {
            "criteria_id": c.criteria_id,
            "version": c.version,
            "author": c.author,
            "created_at": str(c.created_at) if c.created_at else None,
        }
        for c in criteria
    ]

    return EvalJudgeDetailResponse(
        id=judge.id,
        name=judge.name,
        description=judge.description,
        is_builtin=judge.is_builtin,
        inherits_from=judge.inherits_from,
        inherits_from_name=parent_name,
        weights=resolved_weights,
        implementations=implementations,
    )


@router.put("/eval-judges/{judge_id}/weights", response_model=EvalJudgeResponse)
async def update_eval_judge_weights(judge_id: str, request: JudgeUpdateWeights):
    """Update weights for a user judge."""
    try:
        judge = update_judge_weights(judge_id, request.weights)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _judge_to_response(judge)


@router.delete("/eval-judges/{judge_id}")
async def delete_eval_judge(judge_id: str):
    """Delete a user judge (cannot delete built-in)."""
    try:
        delete_judge(judge_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"deleted": True, "id": judge_id}


# === Presets (from registry.yml) ===


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
