"""Dataset routes (read-only)"""

from fastapi import APIRouter, HTTPException

from srl4c.core.datasets import get_all_datasets, get_dataset_prompts
from srl4c.api.schemas import DatasetResponse, DatasetPromptsResponse

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/", response_model=list[DatasetResponse])
async def list_datasets():
    """List available datasets with principles they cover."""
    datasets = get_all_datasets()
    return [
        DatasetResponse(
            name=name,
            path=str(info["path"]),
            rows=info["rows"],
            principles=info["principles"],
        )
        for name, info in datasets.items()
    ]


@router.get("/{name}", response_model=DatasetResponse)
async def get_dataset(name: str):
    """Get dataset info by name."""
    datasets = get_all_datasets()
    if name not in datasets:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {name}")

    info = datasets[name]
    return DatasetResponse(
        name=name,
        path=str(info["path"]),
        rows=info["rows"],
        principles=info["principles"],
    )


@router.get("/{name}/prompts", response_model=DatasetPromptsResponse)
async def get_prompts(name: str, page: int = 1, page_size: int = 50):
    """Get prompts from a dataset with pagination."""
    datasets = get_all_datasets()
    if name not in datasets:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {name}")

    all_prompts = get_dataset_prompts(name)
    total = len(all_prompts)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    prompts = all_prompts[start:end]

    return DatasetPromptsResponse(
        dataset=name,
        total=total,
        page=page,
        page_size=page_size,
        prompts=prompts,
    )
