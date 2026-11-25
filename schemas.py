"""Pydantic request and response schemas for the Ollive AI FastAPI service."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

SupportedModel = Literal[
    "gemini-flash-lite-latest",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "qwen2.5-0.5B",
]


class ErrorResponse(BaseModel):
    """Consistent error response payload returned by all error handlers."""

    error: str = Field(..., description="Short machine-readable error code.")
    detail: str = Field(..., description="Human-readable error description.")
    status_code: int = Field(..., description="HTTP status code.")
    path: Optional[str] = Field(default=None, description="Request path where the error occurred.")


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    version: str = Field(default="1.0.0")


class RootResponse(BaseModel):
    status: str
    message: str


class StatusResponse(BaseModel):
    status: str
    message: str = Field(default="Operation completed successfully.")


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    model: SupportedModel
    message: str = Field(..., min_length=1, max_length=20000)
    system_prompt: Optional[str] = Field(default=None, max_length=4000)


class ChatResponse(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str
    latency: float = Field(..., ge=0.0)
    tokens: int = Field(..., ge=0)
    tool_used: Optional[str] = None
    guardrail_triggered: bool = False


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    rating: int = 0


class HistoryResponse(BaseModel):
    session_id: str
    model: str
    history: list[ChatMessageOut]
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    offset: int = Field(..., ge=0)
    has_more: bool


class ModelStatsOut(BaseModel):
    model: str
    requests: int = Field(..., ge=0)
    avg_latency_ms: Optional[float] = 0.0
    total_prompt_tokens: Optional[int] = 0
    total_completion_tokens: Optional[int] = 0
    guardrail_hits: Optional[int] = 0


class StatsResponse(BaseModel):
    stats: list[ModelStatsOut]
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    offset: int = Field(..., ge=0)
    has_more: bool


class RateRequest(BaseModel):
    rating: int = Field(..., ge=-1, le=1, description="Rating must be -1, 0, or 1.")


class RateResponse(BaseModel):
    status: str
    message_id: int
    rating: int


class CompareRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1, max_length=20000)


class CompareModelResult(BaseModel):
    content: str
    latency: float = Field(..., ge=0.0)
    tokens: int = Field(..., ge=0)


class CompareResponse(BaseModel):
    tool_used: Optional[str] = None
    gemini: CompareModelResult
    qwen: CompareModelResult


class EvalRunTriggerResponse(BaseModel):
    status: Literal["started", "already_running"]
    message: str


class EvalLogsResponse(BaseModel):
    logs: str
    is_running: bool


class EvalRunOut(BaseModel):
    id: int
    run_at: str
    model_name: str
    passed: int = Field(..., ge=0)
    total: int = Field(..., ge=0)
    score_pct: float = Field(..., ge=0.0, le=100.0)
    hallucination_passed: int = Field(..., ge=0)
    hallucination_total: int = Field(..., ge=0)
    bias_passed: int = Field(..., ge=0)
    bias_total: int = Field(..., ge=0)
    safety_passed: int = Field(..., ge=0)
    safety_total: int = Field(..., ge=0)


class EvalHistoryResponse(BaseModel):
    items: list[EvalRunOut]
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    offset: int = Field(..., ge=0)
    has_more: bool
