"""Dataset routes - auto-discovered from filesystem."""

from fastapi import APIRouter, HTTPException

from srl4c.registry import get_registry_loader
from srl4c.api.schemas import DatasetResponse, DatasetDetailResponse, DatasetPromptsResponse

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/", response_model=list[DatasetResponse])
async def list_datasets():
    """List available datasets (auto-discovered from data/datasets/)."""
    loader = get_registry_loader()
    datasets = loader.list_datasets()

    return [
        DatasetResponse(
            name=ds.name,
            path=str(ds.file),
            prompt_count=ds.prompt_count,
            criteria_count=len(ds.criteria_breakdown),
            categories=sorted(set(
                cid.split(".")[0] for cid in ds.criteria_breakdown.keys() if "." in cid
            )),
        )
        for ds in datasets
    ]


@router.get("/{name}", response_model=DatasetDetailResponse)
async def get_dataset(name: str):
    """Get dataset details including criteria breakdown."""
    loader = get_registry_loader()

    try:
        ds = loader.get_dataset(name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {name}")

    return DatasetDetailResponse(
        name=ds.name,
        path=str(ds.file),
        prompt_count=ds.prompt_count,
        criteria_count=len(ds.criteria_breakdown),
        categories=sorted(set(
            cid.split(".")[0] for cid in ds.criteria_breakdown.keys() if "." in cid
        )),
        criteria_breakdown=ds.criteria_breakdown,
    )


@router.get("/{name}/prompts", response_model=DatasetPromptsResponse)
async def get_prompts(name: str, page: int = 1, page_size: int = 50):
    """Get prompts from a dataset with pagination."""
    loader = get_registry_loader()

    try:
        loader.get_dataset(name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {name}")

    all_prompts = loader.load_dataset_prompts(name)
    total = len(all_prompts)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    prompts_page = all_prompts[start:end]

    return DatasetPromptsResponse(
        dataset=name,
        total=total,
        page=page,
        page_size=page_size,
        prompts=[
            {"id": p.id, "criteria_id": p.criteria_id, "prompt": p.prompt}
            for p in prompts_page
        ],
    )
