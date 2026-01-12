"""Guardrails routes"""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from srl4c.api.schemas import (
    GuardrailItem,
    GuardrailsCreate,
    GuardrailsCreateResponse,
    GuardrailSetResponse,
    GuardrailsExportResponse,
)
from srl4c.core.guardrails import create_guardrails, run_guardrails
from srl4c.db.models import db_connection
from srl4c.db.repository import GuardrailSetRepository

router = APIRouter(prefix="/guardrails", tags=["guardrails"])


def _gset_to_response(gset: dict, include_guardrails: bool = False) -> GuardrailSetResponse:
    """Convert guardrail set dict to response schema."""
    progress = 0.0
    if gset.get("progress_total") and gset["progress_total"] > 0:
        progress = gset["progress_current"] / gset["progress_total"]

    guardrails = None
    if include_guardrails:
        with db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM guardrails WHERE set_id = ? ORDER BY created_at",
                (gset["id"],),
            ).fetchall()
        guardrails = [
            GuardrailItem(
                id=g["id"],
                principle_id=g["principle_id"],
                rule_text=g["rule_text"],
                rationale=g["rationale"],
            )
            for g in rows
        ]

    return GuardrailSetResponse(
        id=gset["id"],
        score_id=gset["score_id"],
        model=gset.get("model"),
        rules_count=gset.get("rules_count", 0),
        status=gset.get("status") or "completed",
        progress=progress,
        error_message=gset.get("error_message"),
        guardrails=guardrails,
        created_at=gset.get("created_at"),
        updated_at=gset.get("updated_at"),
        completed_at=gset.get("completed_at"),
    )


@router.get("/", response_model=list[GuardrailSetResponse])
async def list_guardrail_sets():
    """List all guardrail sets."""
    with db_connection() as conn:
        rows = conn.execute("SELECT * FROM guardrail_sets ORDER BY created_at DESC").fetchall()
    return [_gset_to_response(dict(row)) for row in rows]


@router.post("/", response_model=GuardrailsCreateResponse, status_code=202)
async def create_guardrails_endpoint(
    request: GuardrailsCreate,
    background_tasks: BackgroundTasks,
):
    """Generate guardrails from a score. Returns immediately with job ID."""
    try:
        set_id = create_guardrails(
            request.score_id,
            max_rules=request.max_rules,
            max_total=request.max_total,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Run in background
    background_tasks.add_task(
        run_guardrails,
        set_id,
        max_rules=request.max_rules,
        max_total=request.max_total,
    )

    return GuardrailsCreateResponse(id=set_id, status="pending")


@router.get("/{set_id}", response_model=GuardrailSetResponse)
async def get_guardrail_set(set_id: str):
    """Get guardrail set details including all rules."""
    try:
        gset = GuardrailSetRepository.get_by_id(set_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not gset:
        raise HTTPException(status_code=404, detail="Guardrail set not found")

    return _gset_to_response(gset, include_guardrails=True)


@router.get("/{set_id}/export", response_model=GuardrailsExportResponse)
async def export_guardrails(set_id: str):
    """Export guardrails as text for system prompt."""
    try:
        gset = GuardrailSetRepository.get_by_id(set_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not gset:
        raise HTTPException(status_code=404, detail="Guardrail set not found")

    with db_connection() as conn:
        guardrails = conn.execute(
            "SELECT * FROM guardrails WHERE set_id = ? ORDER BY created_at",
            (gset["id"],),
        ).fetchall()

        # Get score info
        score = conn.execute("SELECT * FROM scores WHERE id = ?", (gset["score_id"],)).fetchone()

        # Get attack info
        attack = conn.execute("SELECT * FROM attacks WHERE id = ?", (score["attack_id"],)).fetchone() if score else None

        # Get endpoint info
        endpoint = (
            conn.execute("SELECT * FROM endpoints WHERE id = ?", (attack["endpoint_id"],)).fetchone()
            if attack
            else None
        )

    rules = "\n".join(f"- {g['rule_text']}" for g in guardrails)

    # Build context section
    context_lines = []
    if endpoint:
        context_lines.append(f"Endpoint: {endpoint['name']} ({endpoint['base_url']})")
    if attack:
        context_lines.append(f"Dataset: {attack['dataset_name']}")
        context_lines.append(f"Prompts tested: {attack['total_prompts']}")
    if score:
        context_lines.append(f"Age context: {score['age_context']}")
        if score["weights_preset"]:
            context_lines.append(f"Weights preset: {score['weights_preset']}")
        if score["final_score"] is not None:
            context_lines.append(f"Final score: {score['final_score']:.2f}/5")
    context_lines.append(f"Model used: {gset['model']}")

    context = "\n".join(context_lines)

    text = f"""# Safety Guardrails

Add these guardrails to your system prompt to improve child safety.

## Instructions

1. Copy the rules below into your AI assistant's system prompt
2. Place them in a section clearly labeled as safety guidelines
3. Test your assistant again to verify improvement

## Context

{context}

## Rules ({len(guardrails)} total)

{rules}

---
Generated by SRL4C (Safety Readiness Level for Children)
"""

    return GuardrailsExportResponse(
        id=gset["id"],
        rules_count=len(guardrails),
        text=text,
    )


@router.get("/{set_id}/delete-preview")
async def preview_delete_guardrail_set(set_id: str):
    """Preview what will be deleted if this guardrail set is deleted."""
    preview = GuardrailSetRepository.delete_preview(set_id)
    if preview is None:
        raise HTTPException(status_code=404, detail="Guardrail set not found")
    return preview


@router.delete("/{set_id}")
async def delete_guardrail_set(set_id: str):
    """Delete a guardrail set and its rules."""
    result = GuardrailSetRepository.delete(set_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Guardrail set not found")

    return {
        "deleted": True,
        **result,
    }
