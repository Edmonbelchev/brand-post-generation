from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Decision(str, Enum):
    PUBLISH = "publish"
    HOLD = "hold"
    REJECT = "reject"


class RuleViolation(BaseModel):
    rule: str
    message: str


class HardRulesResult(BaseModel):
    passed: bool
    violations: list[RuleViolation] = Field(default_factory=list)


class BrandVoiceResult(BaseModel):
    score: int | None = None
    passed: bool = False
    feedback: list[str] = Field(default_factory=list)
    error: str | None = None


class GenerationResult(BaseModel):
    success: bool
    post: str | None = None
    error: str | None = None
    model: str | None = None


class GenerateRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)


class ValidateRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    post: str = Field(min_length=1, max_length=5000)


class ChecksResponse(BaseModel):
    hard_rules: HardRulesResult
    brand_voice: BrandVoiceResult


class GenerateResponse(BaseModel):
    decision: Decision
    post: str | None = None
    generated_post: str | None = None
    checks: ChecksResponse
    reasons: list[RuleViolation | dict[str, str]] = Field(default_factory=list)
    audit_id: str


class AuditRecord(BaseModel):
    id: str
    topic: str
    post: str | None
    hard_rules: HardRulesResult
    brand_voice: BrandVoiceResult
    decision: Decision
    reasons: list[Any] = Field(default_factory=list)
    generation: GenerationResult | None = None
    created_at: datetime
    model: str | None = None
