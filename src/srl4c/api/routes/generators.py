"""Generator configuration routes"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from srl4c.generator.config import (
    get_active_generators_file,
    get_generator_file_content,
    list_generator_files,
    set_active_generators,
    test_active_generator,
)

router = APIRouter(prefix="/generators", tags=["generators"])


class GeneratorFileInfo(BaseModel):
    name: str
    path: str
    model: str
    base_url: str
    is_active: bool
    error: str | None = None


class GeneratorFileContent(BaseModel):
    name: str
    content: str
    is_active: bool


class SetActiveRequest(BaseModel):
    name: str


class GeneratorTestResult(BaseModel):
    name: str
    model: str
    base_url: str
    success: bool
    error: str | None = None
    response_time_ms: int | None = None


class TestRequest(BaseModel):
    config: str | None = None


@router.get("/", response_model=list[GeneratorFileInfo])
async def list_generators():
    """List all available generator configuration files."""
    return list_generator_files()


@router.get("/active")
async def get_active():
    """Get the currently active generator configuration filename."""
    return {"active": get_active_generators_file()}


@router.post("/active")
async def set_active(request: SetActiveRequest):
    """Set the active generator configuration."""
    name = request.name
    if not name.endswith(".generators"):
        name = f"{name}.generators"

    files = list_generator_files()
    names = [f["name"] for f in files]

    if name not in names:
        raise HTTPException(status_code=404, detail=f"Generator config not found: {name}")

    set_active_generators(name)
    return {"active": name}


@router.get("/{name}", response_model=GeneratorFileContent)
async def get_generator_content(name: str):
    """Get the content of a specific generator configuration file."""
    if not name.endswith(".generators"):
        name = f"{name}.generators"

    content = get_generator_file_content(name)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Generator config not found: {name}")

    return GeneratorFileContent(
        name=name,
        content=content,
        is_active=(name == get_active_generators_file()),
    )


@router.post("/test", response_model=GeneratorTestResult)
async def test_generator(request: TestRequest = None):
    """Test connectivity to the generator."""
    config_name = request.config if request else None
    return test_active_generator(config_name)
