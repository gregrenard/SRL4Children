"""Endpoint routes"""

from fastapi import APIRouter, HTTPException

from srl4c.db.models import Endpoint
from srl4c.db.repository import EndpointRepository, generate_id
from srl4c.adapters.openai import OpenAIAdapter
from srl4c.adapters.simple import SimpleAdapter
from srl4c.api.schemas import (
    EndpointCreate, EndpointResponse, EndpointTestResponse
)
from srl4c.core.logger import Logger

router = APIRouter(prefix="/endpoints", tags=["endpoints"])


def _endpoint_to_response(ep: Endpoint) -> EndpointResponse:
    """Convert Endpoint model to response schema."""
    return EndpointResponse(
        id=ep.id,
        name=ep.name,
        type=ep.type,
        base_url=ep.base_url,
        api_key_env=ep.api_key_env,
        config=ep.config or {},
        created_at=ep.created_at,
        last_used_at=ep.last_used_at,
    )


@router.get("/", response_model=list[EndpointResponse])
async def list_endpoints():
    """List all endpoints."""
    endpoints = EndpointRepository.list_all()
    return [_endpoint_to_response(ep) for ep in endpoints]


@router.post("/", response_model=EndpointResponse, status_code=201)
async def create_endpoint(request: EndpointCreate):
    """Create a new endpoint."""
    # Check name doesn't exist
    existing = EndpointRepository.get_by_name(request.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Endpoint '{request.name}' already exists")

    # Create endpoint
    endpoint = Endpoint(
        id=generate_id(),
        name=request.name,
        type=request.type,
        base_url=request.base_url,
        api_key_env=request.api_key_env,
        config=request.config or {},
    )

    EndpointRepository.create(endpoint)

    Logger.info(
        "endpoint",
        f"Endpoint created: '{endpoint.name}' ({endpoint.type})",
        entity_type="endpoint",
        entity_id=endpoint.id,
        metadata={"name": endpoint.name, "type": endpoint.type, "url": endpoint.base_url}
    )

    return _endpoint_to_response(endpoint)


@router.get("/{endpoint_id}", response_model=EndpointResponse)
async def get_endpoint(endpoint_id: str):
    """Get endpoint by ID or name."""
    try:
        endpoint = EndpointRepository.get_by_id_or_name(endpoint_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    return _endpoint_to_response(endpoint)


@router.post("/{endpoint_id}/test", response_model=EndpointTestResponse)
async def test_endpoint(endpoint_id: str):
    """Test endpoint connectivity."""
    try:
        endpoint = EndpointRepository.get_by_id_or_name(endpoint_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    # Create adapter
    if endpoint.type == "openai":
        adapter = OpenAIAdapter(endpoint.base_url, endpoint.api_key_env, endpoint.config)
    else:
        adapter = SimpleAdapter(endpoint.base_url, endpoint.api_key_env, endpoint.config)

    # Test
    success, response, latency = adapter.test_connection()

    if success:
        EndpointRepository.update_last_used(endpoint.id)
        Logger.info(
            "endpoint",
            f"Endpoint test successful: '{endpoint.name}' ({latency:.0f}ms)",
            entity_type="endpoint",
            entity_id=endpoint.id,
            metadata={"latency_ms": latency}
        )
    else:
        Logger.warning(
            "endpoint",
            f"Endpoint test failed: '{endpoint.name}' - {response}",
            entity_type="endpoint",
            entity_id=endpoint.id,
            metadata={"error": response}
        )

    return EndpointTestResponse(
        success=success,
        response=response if success else None,
        latency_ms=latency if success else None,
        error=response if not success else None,
    )


@router.delete("/{endpoint_id}")
async def delete_endpoint(endpoint_id: str, force: bool = False):
    """Delete an endpoint. Use force=true to cascade delete attacks."""
    try:
        endpoint = EndpointRepository.get_by_id_or_name(endpoint_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    # Check for related attacks
    from srl4c.db.repository import AttackRepository
    attacks = AttackRepository.get_attacks_for_endpoint(endpoint.id)

    if attacks and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Endpoint has {len(attacks)} attack(s). Use force=true to delete with all related data."
        )

    result = EndpointRepository.delete(endpoint.id, cascade=force)

    Logger.info(
        "endpoint",
        f"Endpoint deleted: '{endpoint.name}'" + (f" (cascade: {result.get('attacks', 0)} attacks)" if force else ""),
        entity_type="endpoint",
        entity_id=endpoint.id,
        metadata={"name": endpoint.name, "cascade": force, **result}
    )

    return {
        "deleted": True,
        "attacks": result.get("attacks", 0),
        "records": result.get("records", 0),
        "scores": result.get("scores", 0),
        "evaluations": result.get("evaluations", 0),
    }
