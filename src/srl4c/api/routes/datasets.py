"""Dataset routes - thin wrapper around core.datasets."""

from fastapi import APIRouter, HTTPException

from srl4c.api.schemas import DatasetCreate, DatasetDetailResponse, DatasetPromptsResponse, DatasetResponse
from srl4c.core.datasets import create_dataset, delete_dataset, get_dataset, get_dataset_prompts, list_datasets

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _dataset_to_response(ds) -> DatasetResponse:
    """Convert Dataset model to response schema."""
    return DatasetResponse(
        id=ds.id,
        name=ds.name,
        description=ds.description,
        is_builtin=ds.is_builtin,
        prompt_count=ds.prompt_count,
        criteria_breakdown=ds.criteria_breakdown,
        created_at=str(ds.created_at) if ds.created_at else None,
        updated_at=str(ds.updated_at) if ds.updated_at else None,
    )


@router.get("/", response_model=list[DatasetResponse])
async def list_datasets_endpoint():
    """List all datasets (built-in + user uploads)."""
    datasets = list_datasets()
    return [_dataset_to_response(ds) for ds in datasets]


@router.post("/", response_model=DatasetResponse, status_code=201)
async def create_dataset_endpoint(request: DatasetCreate):
    """Upload a new dataset."""
    try:
        dataset = create_dataset(
            name=request.name,
            csv_content=request.csv_content,
            description=request.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _dataset_to_response(dataset)


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset_endpoint(dataset_id: str):
    """Get dataset details by ID or name."""
    ds = get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")

    return DatasetDetailResponse(
        id=ds.id,
        name=ds.name,
        description=ds.description,
        is_builtin=ds.is_builtin,
        prompt_count=ds.prompt_count,
        criteria_breakdown=ds.criteria_breakdown or {},
        created_at=str(ds.created_at) if ds.created_at else None,
        updated_at=str(ds.updated_at) if ds.updated_at else None,
    )


@router.get("/{dataset_id}/prompts", response_model=DatasetPromptsResponse)
async def get_prompts_endpoint(dataset_id: str, page: int = 1, page_size: int = 50):
    """Get prompts from a dataset with pagination."""
    try:
        result = get_dataset_prompts(dataset_id, page, page_size)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return DatasetPromptsResponse(**result)


@router.delete("/{dataset_id}")
async def delete_dataset_endpoint(dataset_id: str):
    """Delete a user dataset (cannot delete built-in)."""
    try:
        delete_dataset(dataset_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"deleted": True, "id": dataset_id}
