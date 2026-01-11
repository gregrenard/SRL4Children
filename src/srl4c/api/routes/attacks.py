"""Attack routes"""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from srl4c.core.attack import create_attack, run_attack
from srl4c.db.repository import AttackRepository
from srl4c.api.schemas import (
    AttackCreate, AttackResponse, AttackCreateResponse
)

router = APIRouter(prefix="/attacks", tags=["attacks"])


def _attack_to_response(attack) -> AttackResponse:
    """Convert Attack model to response schema."""
    progress = 0.0
    if attack.progress_total and attack.progress_total > 0:
        progress = attack.progress_current / attack.progress_total
    return AttackResponse(
        id=attack.id,
        endpoint_id=attack.endpoint_id,
        dataset_name=attack.dataset_name,
        status=attack.status,
        total_prompts=attack.total_prompts,
        completed_prompts=attack.completed_prompts,
        progress=progress,
        error_message=attack.error_message,
        started_at=attack.started_at,
        updated_at=attack.updated_at,
        completed_at=attack.completed_at,
    )


@router.get("/", response_model=list[AttackResponse])
async def list_attacks():
    """List all attacks."""
    attacks = AttackRepository.list_all()
    return [_attack_to_response(a) for a in attacks]


@router.post("/", response_model=AttackCreateResponse, status_code=202)
async def create_attack_endpoint(
    request: AttackCreate,
    background_tasks: BackgroundTasks,
):
    """Start a new attack. Returns immediately with job ID."""
    try:
        attack_id = create_attack(request.endpoint, request.dataset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Run in background
    background_tasks.add_task(run_attack, attack_id)

    return AttackCreateResponse(id=attack_id, status="pending")


@router.get("/{attack_id}", response_model=AttackResponse)
async def get_attack(attack_id: str):
    """Get attack status and progress."""
    try:
        attack = AttackRepository.get_by_id(attack_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not attack:
        raise HTTPException(status_code=404, detail="Attack not found")

    return _attack_to_response(attack)


@router.get("/{attack_id}/delete-preview")
async def preview_delete_attack(attack_id: str):
    """Preview what will be deleted if this attack is deleted."""
    preview = AttackRepository.delete_preview(attack_id)
    if preview is None:
        raise HTTPException(status_code=404, detail="Attack not found")
    return preview


@router.delete("/{attack_id}")
async def delete_attack(attack_id: str):
    """Delete an attack and all related data."""
    result = AttackRepository.delete(attack_id, cascade=True)
    if result is None:
        raise HTTPException(status_code=404, detail="Attack not found")

    return {
        "deleted": True,
        **result,
    }
