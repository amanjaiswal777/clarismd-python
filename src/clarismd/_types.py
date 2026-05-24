# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Public Pydantic models returned by SDK calls.

These mirror the response shapes documented in
``LAUNCH_PLAN/17-v1-api-contract.md`` — each field is set permissively
(``Optional`` / extra-allow) so additive backend changes do not break
client code that pins an older SDK version. Once OpenAPI codegen is in
place, narrower generated models will live under ``_generated/``; until
then these hand-written models are the source of truth for callers.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Chat & completions
# ---------------------------------------------------------------------------


class _LooseModel(BaseModel):
    """Base for response models — tolerate unknown fields."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ChatMessage(_LooseModel):
    role: str
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ChatCompletionChoice(_LooseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: Optional[str] = None
    logprobs: Optional[Dict[str, Any]] = None


class CompletionUsage(_LooseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletion(_LooseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int = 0
    model: str = ""
    choices: List[ChatCompletionChoice] = Field(default_factory=list)
    usage: Optional[CompletionUsage] = None
    system_fingerprint: Optional[str] = None
    request_id: Optional[str] = None


class ChatCompletionChunkDelta(_LooseModel):
    role: Optional[str] = None
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ChatCompletionChunkChoice(_LooseModel):
    index: int = 0
    delta: ChatCompletionChunkDelta = Field(default_factory=ChatCompletionChunkDelta)
    finish_reason: Optional[str] = None


class ChatCompletionChunk(_LooseModel):
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int = 0
    model: str = ""
    choices: List[ChatCompletionChunkChoice] = Field(default_factory=list)
    request_id: Optional[str] = None


class TextCompletionChoice(_LooseModel):
    index: int = 0
    text: str = ""
    finish_reason: Optional[str] = None
    logprobs: Optional[Dict[str, Any]] = None


class TextCompletion(_LooseModel):
    id: str
    object: Literal["text_completion"] = "text_completion"
    created: int = 0
    model: str = ""
    choices: List[TextCompletionChoice] = Field(default_factory=list)
    usage: Optional[CompletionUsage] = None
    request_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------


class Embedding(_LooseModel):
    object: Literal["embedding"] = "embedding"
    index: int = 0
    embedding: List[float] = Field(default_factory=list)


class EmbeddingResponse(_LooseModel):
    object: Literal["list"] = "list"
    data: List[Embedding] = Field(default_factory=list)
    model: str = ""
    usage: Optional[CompletionUsage] = None
    request_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Moderations
# ---------------------------------------------------------------------------


class ModerationResult(_LooseModel):
    flagged: bool = False
    categories: Dict[str, bool] = Field(default_factory=dict)
    category_scores: Dict[str, float] = Field(default_factory=dict)


class ModerationResponse(_LooseModel):
    id: str
    model: str = ""
    results: List[ModerationResult] = Field(default_factory=list)
    request_id: Optional[str] = None


# ---------------------------------------------------------------------------
# PHI scan
# ---------------------------------------------------------------------------


class PHIEntity(_LooseModel):
    type: str
    text: str
    start: int = 0
    end: int = 0
    score: Optional[float] = None


class PHIScanResult(_LooseModel):
    detected: bool = False
    entities: List[PHIEntity] = Field(default_factory=list)
    request_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


class AuditLog(_LooseModel):
    id: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    endpoint: Optional[str] = None
    model: Optional[str] = None
    phi_detected: bool = False
    phi_action: Optional[str] = None
    cost_usd: Optional[float] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditLogPage(_LooseModel):
    data: List[AuditLog] = Field(default_factory=list)
    next_cursor: Optional[str] = None
    has_more: bool = False
    request_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Compliance
# ---------------------------------------------------------------------------


class ComplianceCounts(_LooseModel):
    satisfied: int = 0
    total: int = 0
    acknowledged: Optional[int] = None


class ComplianceScore(_LooseModel):
    auto_verified: ComplianceCounts = Field(default_factory=ComplianceCounts)
    manual: ComplianceCounts = Field(default_factory=ComplianceCounts)
    framework: str = "hipaa"
    as_of: Optional[datetime] = None
    request_id: Optional[str] = None


class Requirement(_LooseModel):
    id: str
    code: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    framework: str = "hipaa"
    acknowledgment_status: Literal[
        "pending", "acknowledged", "not_applicable", "auto_satisfied"
    ] = "pending"
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    notes: Optional[str] = None
    policy_url: Optional[str] = None
    evidence_count: int = 0


class EvidenceArtifact(_LooseModel):
    id: str
    requirement_id: Optional[str] = None
    audit_log_id: Optional[str] = None
    artifact_type: Optional[str] = None
    evidence_payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------


class APIKey(_LooseModel):
    id: str
    name: Optional[str] = None
    prefix: Optional[str] = None
    secret: Optional[str] = Field(
        default=None,
        description="Full secret token. Only present in the response of POST /v1/keys.",
    )
    scopes: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class HealthStatus(_LooseModel):
    status: str = "ok"
    version: Optional[str] = None


# Re-exported PHI action literal so callers don't import from
# ``typing.Literal`` themselves.
PHIAction = Literal["block", "redact", "tokenize", "alert"]


# httpx ships ``Stream``-like primitives; we expose ours from
# ``_streaming``. Re-exported here only for type-hint convenience.
JSONValue = Union[None, bool, int, float, str, List[Any], Dict[str, Any]]


__all__ = [
    "ChatMessage",
    "ChatCompletion",
    "ChatCompletionChoice",
    "ChatCompletionChunk",
    "ChatCompletionChunkChoice",
    "ChatCompletionChunkDelta",
    "TextCompletion",
    "TextCompletionChoice",
    "CompletionUsage",
    "Embedding",
    "EmbeddingResponse",
    "ModerationResult",
    "ModerationResponse",
    "PHIEntity",
    "PHIScanResult",
    "PHIAction",
    "AuditLog",
    "AuditLogPage",
    "ComplianceCounts",
    "ComplianceScore",
    "Requirement",
    "EvidenceArtifact",
    "APIKey",
    "HealthStatus",
    "JSONValue",
]
