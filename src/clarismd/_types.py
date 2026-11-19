# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Public Pydantic models returned by SDK calls.

These mirror the gateway's v1 API response shapes — each field is set permissively
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


class PHILocation(_LooseModel):
    start: int = 0
    end: int = 0


class PHIEntity(_LooseModel):
    type: str
    """Detector category, e.g. ``"pii"``."""
    subtype: Optional[str] = None
    """Finer identifier class, e.g. ``"ssn"``, ``"mrn"``, ``"dob"``."""
    severity: str = ""
    confidence: float = 0.0
    location: PHILocation = Field(default_factory=PHILocation)
    """Character offsets into the scanned string."""
    matched_pattern: Optional[str] = None
    matched_text: Optional[str] = None


class PHIScanResult(_LooseModel):
    """One result per input string, in input order."""

    scan_id: str = ""
    overall_risk_score: float = 0.0
    should_block: bool = False
    entities: List[PHIEntity] = Field(default_factory=list)
    """Empty when no PHI/PII was found."""
    scan_duration_ms: Optional[float] = None

    @property
    def detected(self) -> bool:
        """True when at least one entity was found."""
        return bool(self.entities)


class PHIScanResponse(_LooseModel):
    """Response of ``POST /v1/phi/scan``: one result per input, in order."""

    results: List[PHIScanResult]
    request_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


class AuditLog(_LooseModel):
    id: str
    action: str = ""
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None
    org_id: Optional[str] = None
    user_id: Optional[str] = None
    chain_seq: Optional[int] = None
    """Position in the organisation's stored hash chain (None for pre-chain entries)."""
    prev_hash: Optional[str] = None
    entry_hash: Optional[str] = None
    """sha256 over the entry's canonical fields and ``prev_hash``."""
    created_at_canonical: Optional[str] = None
    """The exact timestamp string that ``entry_hash`` covers."""


class AuditLogPage(_LooseModel):
    """Offset-paginated page of audit logs."""

    logs: List[AuditLog] = Field(default_factory=list)
    total: int = 0
    """Total matching entries (all pages)."""
    limit: int = 0
    offset: int = 0
    has_more: bool = False
    request_id: Optional[str] = None


class AuditExport(_LooseModel):
    """Signed audit export.

    JSON exports carry ``payload``; PDF exports carry ``pdf_base64`` (see
    :meth:`pdf_bytes`). ``signature`` is ``ed25519:<key_id>:<base64>`` and
    verifies offline with the public key at ``public_keys_url``.
    """

    export_id: str
    format: str
    record_count: int = 0
    generated_at: Optional[str] = None
    download_url: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    signature: Optional[str] = None
    signature_alg: Optional[str] = None
    key_id: Optional[str] = None
    public_keys_url: Optional[str] = None
    pdf_base64: Optional[str] = None
    request_id: Optional[str] = None

    def pdf_bytes(self) -> bytes:
        """Decoded PDF for ``format="pdf"`` exports (empty otherwise)."""
        import base64

        return base64.b64decode(self.pdf_base64) if self.pdf_base64 else b""


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
    key_prefix: str = ""
    key: Optional[str] = Field(
        default=None,
        description="Full secret token. Only present in the response of POST /v1/keys.",
    )
    permissions: Optional[List[str]] = None
    revoked: bool = False
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_by_session_id: Optional[str] = None


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
