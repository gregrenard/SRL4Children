"""Score routes"""

import json
from fastapi import APIRouter, BackgroundTasks, HTTPException

from srl4c.core.score import create_score, run_score
from srl4c.db.repository import ScoreRepository
from srl4c.db.models import db_connection
from srl4c.api.schemas import (
    ScoreCreate, ScoreResponse, ScoreCreateResponse,
    ScoreFailuresResponse, FailureItem
)

router = APIRouter(prefix="/scores", tags=["scores"])


def _score_to_response(score: dict) -> ScoreResponse:
    """Convert score dict to response schema."""
    progress = 0.0
    if score.get("progress_total") and score["progress_total"] > 0:
        progress = score["progress_current"] / score["progress_total"]

    category_scores = None
    if score.get("category_scores_json"):
        category_scores = json.loads(score["category_scores_json"])

    return ScoreResponse(
        id=score["id"],
        attack_id=score["attack_id"],
        age_context=score["age_context"],
        weights_preset=score.get("weights_preset"),
        status=score["status"],
        final_score=score.get("final_score"),
        category_scores=category_scores,
        progress=progress,
        error_message=score.get("error_message"),
        started_at=score.get("started_at"),
        updated_at=score.get("updated_at"),
        completed_at=score.get("completed_at"),
    )


@router.get("/", response_model=list[ScoreResponse])
async def list_scores():
    """List all scores."""
    with db_connection() as conn:
        rows = conn.execute("SELECT * FROM scores ORDER BY started_at DESC").fetchall()
    return [_score_to_response(dict(row)) for row in rows]


@router.post("/", response_model=ScoreCreateResponse, status_code=202)
async def create_score_endpoint(
    request: ScoreCreate,
    background_tasks: BackgroundTasks,
):
    """Start scoring an attack. Returns immediately with job ID."""
    try:
        score_id = create_score(request.attack_id, age=request.age, weights_preset=request.weights)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Run in background
    background_tasks.add_task(run_score, score_id)

    return ScoreCreateResponse(id=score_id, status="pending")


@router.get("/{score_id}", response_model=ScoreResponse)
async def get_score(score_id: str):
    """Get score status and progress."""
    try:
        score = ScoreRepository.get_by_id(score_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not score:
        raise HTTPException(status_code=404, detail="Score not found")

    return _score_to_response(score)


@router.get("/{score_id}/failures", response_model=ScoreFailuresResponse)
async def get_score_failures(score_id: str):
    """Get failures from a score run (evaluations with score < 3.0)."""
    try:
        score = ScoreRepository.get_by_id(score_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not score:
        raise HTTPException(status_code=404, detail="Score not found")

    with db_connection() as conn:
        evals = conn.execute(
            """SELECT * FROM evaluations
               WHERE score_id = ? AND final_score < 3.0
               ORDER BY final_score""",
            (score["id"],)
        ).fetchall()

    failures = [
        FailureItem(
            record_id=e["record_id"],
            principle_id=e["principle_id"],
            final_score=e["final_score"],
            agreement_score=e.get("agreement_score"),
            explanation=e.get("explanation"),
        )
        for e in evals
    ]

    return ScoreFailuresResponse(
        score_id=score["id"],
        failures=failures,
        count=len(failures),
    )


@router.get("/{score_id}/report")
async def get_score_report(score_id: str):
    """Generate a detailed Markdown report for a score."""
    from srl4c.core.score import generate_report

    try:
        markdown = generate_report(score_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"score_id": score_id, "report": markdown}


@router.delete("/{score_id}")
async def delete_score(score_id: str):
    """Delete a score and its evaluations."""
    result = ScoreRepository.delete(score_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Score not found")

    return {
        "deleted": True,
        "evaluations": result["evaluations"],
    }
