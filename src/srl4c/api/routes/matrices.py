"""Scoring matrices API routes"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from srl4c.core import matrices as core_matrices


router = APIRouter(prefix="/matrices", tags=["matrices"])


# === Schemas ===

class MatrixCreate(BaseModel):
    name: str
    description: Optional[str] = None


class MatrixEntrySchema(BaseModel):
    behavior_id: str
    age_group: str
    presence_level: int
    score: float


class MatrixEntriesUpdate(BaseModel):
    entries: List[MatrixEntrySchema]


class MatrixClone(BaseModel):
    new_name: str
    description: Optional[str] = None


class MatrixResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_builtin: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MatrixDetailResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_builtin: bool = False
    entries: List[MatrixEntrySchema] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# === Endpoints ===

@router.get("/", response_model=List[MatrixResponse])
async def list_matrices():
    """List all scoring matrices."""
    matrices = core_matrices.list_matrices()
    return [
        MatrixResponse(
            id=m.id,
            name=m.name,
            description=m.description,
            is_builtin=m.is_builtin,
            created_at=str(m.created_at) if m.created_at else None,
            updated_at=str(m.updated_at) if m.updated_at else None,
        )
        for m in matrices
    ]


@router.post("/", response_model=MatrixResponse, status_code=201)
async def create_matrix(request: MatrixCreate):
    """Create a new scoring matrix."""
    try:
        matrix = core_matrices.create_matrix(
            name=request.name,
            description=request.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MatrixResponse(
        id=matrix.id,
        name=matrix.name,
        description=matrix.description,
        is_builtin=matrix.is_builtin,
    )


@router.get("/{matrix_id}", response_model=MatrixDetailResponse)
async def get_matrix(matrix_id: str):
    """Get matrix with all entries."""
    matrix = core_matrices.get_matrix(matrix_id)
    if not matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")

    entries = core_matrices.get_matrix_entries(matrix.id)

    return MatrixDetailResponse(
        id=matrix.id,
        name=matrix.name,
        description=matrix.description,
        is_builtin=matrix.is_builtin,
        entries=[
            MatrixEntrySchema(
                behavior_id=e.behavior_id,
                age_group=e.age_group,
                presence_level=e.presence_level,
                score=e.score,
            )
            for e in entries
        ],
        created_at=str(matrix.created_at) if matrix.created_at else None,
        updated_at=str(matrix.updated_at) if matrix.updated_at else None,
    )


@router.put("/{matrix_id}/entries")
async def update_matrix_entries(matrix_id: str, request: MatrixEntriesUpdate):
    """Update all entries for a matrix (replaces existing entries)."""
    try:
        count = core_matrices.update_matrix_entries(
            name_or_id=matrix_id,
            entries=[e.model_dump() for e in request.entries],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"updated": True, "entries_count": count}


@router.post("/{matrix_id}/clone", response_model=MatrixResponse, status_code=201)
async def clone_matrix(matrix_id: str, request: MatrixClone):
    """Clone an existing matrix with a new name."""
    try:
        matrix = core_matrices.clone_matrix(
            source_name_or_id=matrix_id,
            new_name=request.new_name,
            description=request.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MatrixResponse(
        id=matrix.id,
        name=matrix.name,
        description=matrix.description,
        is_builtin=matrix.is_builtin,
    )


@router.delete("/{matrix_id}")
async def delete_matrix(matrix_id: str):
    """Delete a scoring matrix."""
    try:
        deleted = core_matrices.delete_matrix(matrix_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"deleted": deleted}
