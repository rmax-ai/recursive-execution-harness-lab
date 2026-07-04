from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def now_utc() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class TaskSpec(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    title: str
    question: str
    expected_output_type: Literal["article", "report", "answer", "plan"] = "report"
    success_criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    evaluation_questions: list[str] = Field(default_factory=list)


class DocumentRef(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    source_path: str
    title: str | None = None
    content_hash: str
    char_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceCard(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    source_ref: str
    quote_or_excerpt: str
    summary: str
    claim_supported: str
    confidence: Literal["low", "medium", "high"] = "medium"
    worker_id: str
    created_at: datetime = Field(default_factory=now_utc)


class PlanItem(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    subquestion: str
    assigned_refs: list[str]
    expected_evidence: list[str] = Field(default_factory=list)


class Plan(BaseModel):
    model_config = {"extra": "forbid"}

    id: str = Field(default_factory=lambda: new_id("plan"))
    strategy: str
    items: list[PlanItem]
    verification_strategy: str


class WorkerResult(BaseModel):
    model_config = {"extra": "forbid"}

    worker_id: str
    plan_item_id: str
    subquestion: str
    assigned_refs: list[str]
    findings: list[EvidenceCard]
    open_questions: list[str] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)


class ClaimCheck(BaseModel):
    model_config = {"extra": "forbid"}

    claim: str
    supported: bool
    evidence_ids: list[str] = Field(default_factory=list)
    issue: str | None = None


class VerificationResult(BaseModel):
    model_config = {"extra": "forbid"}

    id: str = Field(default_factory=lambda: new_id("verify"))
    verdict: Literal["pass", "partial", "fail"]
    checks: list[ClaimCheck]
    unsupported_claims: list[str] = Field(default_factory=list)
    source_attribution_errors: list[str] = Field(default_factory=list)


class TraceEvent(BaseModel):
    model_config = {"extra": "forbid"}

    run_id: str
    event_id: str = Field(default_factory=lambda: new_id("evt"))
    timestamp: datetime = Field(default_factory=now_utc)
    stage: str
    event_type: str
    actor: str
    input_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    token_usage: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunMetrics(BaseModel):
    model_config = {"extra": "forbid"}

    run_id: str
    mode: Literal["long-context", "recursive"]
    token_input_estimate: int = 0
    token_output_estimate: int = 0
    wall_clock_seconds: float = 0
    document_count: int = 0
    evidence_card_count: int = 0
    unsupported_claim_count: int = 0
    source_attribution_error_count: int = 0
    verification_verdict: str | None = None
