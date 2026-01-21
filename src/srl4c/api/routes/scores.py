"""Score routes"""

import json

from fastapi import APIRouter, BackgroundTasks, HTTPException

from srl4c.api.schemas import FailureItem, ScoreCreate, ScoreCreateResponse, ScoreFailuresResponse, ScoreResponse
from srl4c.core.score import create_score, run_score
from srl4c.db.models import db_connection
from srl4c.db.repository import ScoreRepository, ScoringMatrixRepository

router = APIRouter(prefix="/scores", tags=["scores"])


def _score_to_response(score: dict) -> ScoreResponse:
    """Convert score dict to response schema."""
    progress = 0.0
    if score.get("progress_total") and score["progress_total"] > 0:
        progress = score["progress_current"] / score["progress_total"]

    category_scores = None
    if score.get("category_scores_json"):
        category_scores = json.loads(score["category_scores_json"])

    # Get matrix name for display
    matrix_name = None
    matrix_id = score.get("matrix_id")
    if matrix_id:
        matrix = ScoringMatrixRepository.get_by_id(matrix_id)
        if matrix:
            matrix_name = matrix.name

    return ScoreResponse(
        id=score["id"],
        attack_id=score["attack_id"],
        age_context=score["age_context"],
        context=score.get("context"),
        matrix_id=matrix_id,
        matrix_name=matrix_name,
        status=score["status"],
        final_score=score.get("final_score"),
        category_scores=category_scores,
        progress=progress,
        progress_current=score.get("progress_current") or 0,
        progress_total=score.get("progress_total") or 0,
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
        score_id = create_score(
            attack_id=request.attack_id,
            age=request.age,
            matrix=request.matrix,
        )
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
            (score["id"],),
        ).fetchall()

    failures = [
        FailureItem(
            record_id=e["record_id"],
            criteria_id=e["criteria_id"],
            final_score=e["final_score"],
            agreement_score=e["agreement_score"],
            explanation=e["explanation"],
        )
        for e in evals
    ]

    return ScoreFailuresResponse(
        score_id=score["id"],
        failures=failures,
        count=len(failures),
    )


@router.get("/{score_id}/report")
async def get_score_report(score_id: str, format: str = "md"):
    """Generate a report for a score.

    Args:
        format: Report format - "md" for Markdown (default), "pdf" for PDF
    """
    if format == "pdf":
        from fastapi.responses import Response

        from srl4c.core.report_pdf import generate_pdf_report

        try:
            pdf_bytes = generate_pdf_report(score_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=srl4c-report-{score_id[:8]}.pdf"},
        )

    # Default: Markdown
    from srl4c.core.score import generate_report

    try:
        markdown = generate_report(score_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"score_id": score_id, "report": markdown}


@router.get("/{score_id}/delete-preview")
async def preview_delete_score(score_id: str):
    """Preview what will be deleted if this score is deleted."""
    preview = ScoreRepository.delete_preview(score_id)
    if preview is None:
        raise HTTPException(status_code=404, detail="Score not found")
    return preview


@router.delete("/{score_id}")
async def delete_score(score_id: str):
    """Delete a score and its evaluations and guardrail sets."""
    result = ScoreRepository.delete(score_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Score not found")

    return {
        "deleted": True,
        **result,
    }
