"""SRL4C REST API - FastAPI Application"""

import os
from pathlib import Path

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from srl4c.api.schemas import HealthResponse
from srl4c.api.routes import attacks, scores, guardrails, endpoints, datasets, criteria, logs, judges, generators, matrices

app = FastAPI(
    title="SRL4C API",
    description="Safety Readiness Level for Children - REST API",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API router with /api prefix
api_router = APIRouter(prefix="/api")
api_router.include_router(endpoints.router)
api_router.include_router(attacks.router)
api_router.include_router(scores.router)
api_router.include_router(guardrails.router)
api_router.include_router(datasets.router)
api_router.include_router(criteria.router)
api_router.include_router(logs.router)
api_router.include_router(judges.router)
api_router.include_router(generators.router)
api_router.include_router(matrices.router)

app.include_router(api_router)


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


# Serve static frontend if available (Docker deployment)
# Check common locations: /app/static (Docker) or relative to cwd
STATIC_DIR = Path("/app/static")
if not STATIC_DIR.exists():
    STATIC_DIR = Path.cwd() / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA - fallback to index.html for client-side routing."""
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
