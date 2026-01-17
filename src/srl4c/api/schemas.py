"""Pydantic schemas for API request/response models"""

from typing import Any

from pydantic import BaseModel, Field

# === Endpoints ===


class EndpointCreate(BaseModel):
    name: str = Field(..., description="Friendly name for this endpoint")
    type: str = Field(..., description="Endpoint type: 'openai' or 'simple'")
    base_url: str = Field(..., description="Base URL for the endpoint")
    api_key_env: str | None = Field(None, description="Environment variable name for API key")
    config: dict[str, Any] | None = Field(default_factory=dict, description="Additional config")


class EndpointResponse(BaseModel):
    id: str
    name: str
    type: str
    base_url: str
    api_key_env: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    last_used_at: str | None = None


class EndpointTestRequest(BaseModel):
    prompt: str | None = Field(None, description="Custom prompt to send (defaults to 'Hello!')")


class EndpointTestResponse(BaseModel):
    success: bool
    response: str | None = None
    latency_ms: int | None = None
    error: str | None = None


# === Attacks ===


class AttackCreate(BaseModel):
    endpoint: str = Field(..., description="Endpoint ID or name")
    dataset: str = Field(..., description="Dataset ID or name")


class AttackResponse(BaseModel):
    id: str
    endpoint_id: str
    dataset_id: str
    dataset_name: str | None = Field(None, description="Dataset name for display")
    status: str
    total_prompts: int = 0
    completed_prompts: int = 0
    progress: float = Field(0.0, description="Progress 0.0 to 1.0")
    error_message: str | None = None
    started_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None


class AttackCreateResponse(BaseModel):
    id: str
    status: str = "pending"


class AttackRecordItem(BaseModel):
    id: str
    criteria_id: str
    prompt: str
    response: str | None = None
    error: str | None = None


class AttackRecordsResponse(BaseModel):
    attack_id: str
    total: int
    page: int
    page_size: int
    records: list[AttackRecordItem]


# === Scores ===


class ScoreCreate(BaseModel):
    attack_id: str = Field(..., description="Attack ID to score")
    age: str = Field("child", description="Age group: child, teenager, young_adult")
    matrix: str = Field(
        "educational",
        description="Scoring matrix (educational, companionship, entertainment, flat). Matrix determines context scoring rules.",
    )


class ScoreResponse(BaseModel):
    id: str
    attack_id: str
    age_context: str
    matrix_id: str | None = None
    matrix_name: str | None = None
    status: str
    final_score: float | None = None
    category_scores: dict[str, Any] | None = None  # {"categories": {...}, "subcategories": {...}, "presence": {...}}
    progress: float = Field(0.0, description="Progress 0.0 to 1.0")
    error_message: str | None = None
    started_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None


class ScoreCreateResponse(BaseModel):
    id: str
    status: str = "pending"


class FailureItem(BaseModel):
    record_id: str
    criteria_id: str
    final_score: float
    agreement_score: float | None = None
    explanation: str | None = None


class ScoreFailuresResponse(BaseModel):
    score_id: str
    failures: list[FailureItem]
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
    rationale: str | None = None


class GuardrailSetResponse(BaseModel):
    id: str
    score_id: str
    model: str | None = None
    rules_count: int = 0
    status: str
    progress: float = Field(0.0, description="Progress 0.0 to 1.0")
    error_message: str | None = None
    guardrails: list[GuardrailItem] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None


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
    description: str | None = Field(None, description="Dataset description")
    csv_content: str = Field(..., description="CSV content")


class DatasetResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    is_builtin: bool = False
    prompt_count: int = 0
    criteria_breakdown: dict[str, int] | None = Field(default_factory=dict, description="Prompts per criteria")
    created_at: str | None = None
    updated_at: str | None = None


class DatasetDetailResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    is_builtin: bool = False
    prompt_count: int = 0
    criteria_breakdown: dict[str, int] = Field(default_factory=dict, description="Prompts per criteria")
    created_at: str | None = None
    updated_at: str | None = None


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
    prompts: list[dict[str, str]]


# === Criteria ===


class CriteriaResponse(BaseModel):
    id: str
    category: str
    subcategory: str
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)


# === Evaluation Judges ===


class JudgeCreate(BaseModel):
    name: str = Field(..., description="Judge name")
    description: str | None = Field(None, description="Judge description")
    inherits_from: str = Field(..., description="Parent judge ID or name to inherit from")
    weights: dict[str, dict[str, float]] | None = Field(None, description="Weight overrides")


class JudgeUpdateWeights(BaseModel):
    weights: dict[str, dict[str, float]] = Field(..., description="Weight configuration")


class EvalJudgeResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    is_builtin: bool = False
    inherits_from: str | None = Field(None, description="Parent judge ID")
    inherits_from_name: str | None = Field(None, description="Parent judge name for display")
    weights: dict[str, dict[str, float]] | None = None
    implementation_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class EvalJudgeDetailResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    is_builtin: bool = False
    inherits_from: str | None = None
    inherits_from_name: str | None = None
    weights: dict[str, dict[str, float]] = Field(default_factory=dict)
    implementations: list[dict[str, str]] = Field(default_factory=list, description="List of criteria implementations")


# === Presets ===


class PresetResponse(BaseModel):
    name: str
    description: str
    criteria: list[str] = Field(default_factory=list)


# === Common ===


class JobStatus(BaseModel):
    id: str
    status: str
    progress: float
    error_message: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
