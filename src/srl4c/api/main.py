"""SRL4C REST API - FastAPI Application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from srl4c.api.schemas import HealthResponse
from srl4c.api.routes import attacks, scores, guardrails, endpoints, datasets, principles, logs, judges

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

# Include routers
app.include_router(endpoints.router)
app.include_router(attacks.router)
app.include_router(scores.router)
app.include_router(guardrails.router)
app.include_router(datasets.router)
app.include_router(principles.router)
app.include_router(logs.router)
app.include_router(judges.router)


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/", tags=["health"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "SRL4C API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
