"""Pydantic schemas for API request/response models"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


# === Endpoints ===

class EndpointCreate(BaseModel):
    name: str = Field(..., description="Friendly name for this endpoint")
    type: str = Field(..., description="Endpoint type: 'openai' or 'simple'")
    base_url: str = Field(..., description="Base URL for the endpoint")
    api_key_env: Optional[str] = Field(None, description="Environment variable name for API key")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional config")


class EndpointResponse(BaseModel):
    id: str
    name: str
    type: str
    base_url: str
    api_key_env: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    last_used_at: Optional[str] = None


class EndpointTestResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None


# === Attacks ===

class AttackCreate(BaseModel):
    endpoint: str = Field(..., description="Endpoint ID or name")
    dataset: str = Field(..., description="Dataset ID or name")


class AttackResponse(BaseModel):
    id: str
    endpoint_id: str
    dataset_id: str
    dataset_name: Optional[str] = Field(None, description="Dataset name for display")
    status: str
    total_prompts: int = 0
    completed_prompts: int = 0
    progress: float = Field(0.0, description="Progress 0.0 to 1.0")
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


class AttackCreateResponse(BaseModel):
    id: str
    status: str = "pending"


# === Scores ===

class ScoreCreate(BaseModel):
    attack_id: str = Field(..., description="Attack ID to score")
    age: str = Field("child", description="Age context: child, teen, young_adult, emerging")
    judge: str = Field(..., description="Evaluation judge name")


class ScoreResponse(BaseModel):
    id: str
    attack_id: str
    age_context: str
    judge_id: Optional[str] = Field(None, description="Evaluation judge ID")
    judge_name: Optional[str] = Field(None, description="Evaluation judge name for display")
    status: str
    final_score: Optional[float] = None
    category_scores: Optional[Dict[str, Dict[str, float]]] = None  # {"categories": {...}, "subcategories": {...}}
    progress: float = Field(0.0, description="Progress 0.0 to 1.0")
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


class ScoreCreateResponse(BaseModel):
    id: str
    status: str = "pending"


class FailureItem(BaseModel):
    record_id: str
    criteria_id: str
    final_score: float
    agreement_score: Optional[float] = None
    explanation: Optional[str] = None


class ScoreFailuresResponse(BaseModel):
    score_id: str
    failures: List[FailureItem]
    count: int


# === Guardrails ===

class GuardrailsCreate(BaseModel):
    score_id: str = Field(..., description="Score ID to generate guardrails from")
    max_rules: int = Field(3, description="Max guardrails per failing criterion")
    max_total: int = Field(20, description="Max total guardrails")


class GuardrailItem(BaseModel):
    id: str
    criteria_id: str
    rule_text: str
    rationale: Optional[str] = None


class GuardrailSetResponse(BaseModel):
    id: str
    score_id: str
    model: Optional[str] = None
    rules_count: int = 0
    status: str
    progress: float = Field(0.0, description="Progress 0.0 to 1.0")
    error_message: Optional[str] = None
    guardrails: Optional[List[GuardrailItem]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None


class GuardrailsCreateResponse(BaseModel):
    id: str
    status: str = "pending"


class GuardrailsExportResponse(BaseModel):
    id: str
    rules_count: int
    text: str


# === Datasets ===

class DatasetCreate(BaseModel):
    name: str = Field(..., description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")
    csv_content: str = Field(..., description="CSV content")


class DatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_builtin: bool = False
    prompt_count: int = 0
    criteria_breakdown: Optional[Dict[str, int]] = Field(default_factory=dict, description="Prompts per criteria")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DatasetDetailResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_builtin: bool = False
    prompt_count: int = 0
    criteria_breakdown: Dict[str, int] = Field(default_factory=dict, description="Prompts per criteria")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DatasetPrompt(BaseModel):
    id: str
    criteria_id: str
    prompt: str


class DatasetPromptsResponse(BaseModel):
    dataset_id: str
    dataset_name: str
    total: int
    page: int
    page_size: int
    prompts: List[Dict[str, str]]


# === Criteria ===

class CriteriaResponse(BaseModel):
    id: str
    category: str
    subcategory: str
    name: str
    description: str
    tags: List[str] = Field(default_factory=list)


# === Evaluation Judges ===

class JudgeCreate(BaseModel):
    name: str = Field(..., description="Judge name")
    description: Optional[str] = Field(None, description="Judge description")
    inherits_from: str = Field(..., description="Parent judge ID or name to inherit from")
    weights: Optional[Dict[str, Dict[str, float]]] = Field(None, description="Weight overrides")


class JudgeUpdateWeights(BaseModel):
    weights: Dict[str, Dict[str, float]] = Field(..., description="Weight configuration")


class EvalJudgeResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_builtin: bool = False
    inherits_from: Optional[str] = Field(None, description="Parent judge ID")
    inherits_from_name: Optional[str] = Field(None, description="Parent judge name for display")
    weights: Optional[Dict[str, Dict[str, float]]] = None
    implementation_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class EvalJudgeDetailResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_builtin: bool = False
    inherits_from: Optional[str] = None
    inherits_from_name: Optional[str] = None
    weights: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    implementations: List[Dict[str, str]] = Field(default_factory=list, description="List of criteria implementations")


# === Presets ===

class PresetResponse(BaseModel):
    name: str
    description: str
    criteria: List[str] = Field(default_factory=list)


# === Common ===

class JobStatus(BaseModel):
    id: str
    status: str
    progress: float
    error_message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
