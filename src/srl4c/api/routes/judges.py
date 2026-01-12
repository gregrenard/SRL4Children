"""Judges configuration routes"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from srl4c.judge.config import (
    get_active_judges_file,
    get_judge_file_content,
    list_judge_files,
    set_active_judges,
    test_all_judges,
)

router = APIRouter(prefix="/judges", tags=["judges"])


class JudgeFileInfo(BaseModel):
    name: str
    path: str
    judges_count: int
    n_passes: int
    is_active: bool
    error: str | None = None


class JudgeFileContent(BaseModel):
    name: str
    content: str
    is_active: bool


class SetActiveRequest(BaseModel):
    name: str


@router.get("/", response_model=list[JudgeFileInfo])
async def list_judges():
    """List all available judge configuration files."""
    return list_judge_files()


@router.get("/active")
async def get_active():
    """Get the currently active judge configuration filename."""
    return {"active": get_active_judges_file()}


@router.post("/active")
async def set_active(request: SetActiveRequest):
    """Set the active judge configuration."""
    name = request.name
    if not name.endswith(".judges"):
        name = f"{name}.judges"

    # Check if file exists
    files = list_judge_files()
    names = [f["name"] for f in files]

    if name not in names:
        raise HTTPException(status_code=404, detail=f"Judge config not found: {name}")

    set_active_judges(name)
    return {"active": name}


@router.get("/{name}", response_model=JudgeFileContent)
async def get_judge_content(name: str):
    """Get the content of a specific judge configuration file."""
    if not name.endswith(".judges"):
        name = f"{name}.judges"

    content = get_judge_file_content(name)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Judge config not found: {name}")

    return JudgeFileContent(
        name=name,
        content=content,
        is_active=(name == get_active_judges_file()),
    )


class JudgeTestResult(BaseModel):
    name: str
    model: str
    base_url: str
    success: bool
    error: str | None = None
    response_time_ms: int | None = None


class TestRequest(BaseModel):
    config: str | None = None


@router.post("/test", response_model=list[JudgeTestResult])
async def test_judges(request: TestRequest = None):
    """Test connectivity to judges in a config file."""
    config_name = request.config if request else None
    return test_all_judges(config_name)
