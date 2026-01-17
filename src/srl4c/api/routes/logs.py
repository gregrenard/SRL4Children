"""Logs routes"""

from fastapi import APIRouter, Query

from srl4c.db.repository import LogRepository

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/")
async def list_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    level: str | None = Query(None, description="Filter by level: info, warning, error"),
    entity_type: str | None = Query(None, description="Filter by entity type: endpoint, attack, score, guardrail_set"),
    entity_id: str | None = Query(None, description="Filter by entity ID"),
):
    """List logs with optional filters, newest first."""
    logs = LogRepository.list_all(
        limit=limit,
        offset=offset,
        level=level,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    return [
        {
            "id": log.id,
            "timestamp": log.timestamp,
            "level": log.level,
            "source": log.source,
            "message": log.message,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "metadata": log.metadata,
        }
        for log in logs
    ]


@router.get("/count")
async def count_logs(
    level: str | None = Query(None, description="Filter by level"),
    entity_type: str | None = Query(None, description="Filter by entity type"),
):
    """Get count of logs matching filters."""
    return {"count": LogRepository.count(level=level, entity_type=entity_type)}


@router.delete("/cleanup")
async def cleanup_logs(days: int = Query(30, ge=1, le=365)):
    """Delete logs older than X days."""
    deleted = LogRepository.cleanup(days=days)
    return {"deleted": deleted}
