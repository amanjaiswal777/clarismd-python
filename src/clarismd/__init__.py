# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""ClarisMD Python SDK — open-source AI gateway with PHI-aware governance.

Quickstart::

    from clarismd import ClarisMD

    client = ClarisMD(api_key="cmd-...")
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(resp.choices[0].message.content)

For self-hosted deployments, set ``CLARISMD_BASE_URL`` (or pass
``base_url=...``) to point the client at your gateway:

    client = ClarisMD(api_key="cmd-...", base_url="https://gateway.your-org.example/v1")
"""
from __future__ import annotations

from ._client import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    AsyncClarisMD,
    ClarisMD,
)
from ._exceptions import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    BudgetExceededError,
    ClarisMDError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    PHIPolicyViolationError,
    ProviderError,
    RateLimitError,
    UnprocessableEntityError,
)
from ._streaming import AsyncStream, Stream
from ._types import (
    APIKey,
    AuditLog,
    AuditLogPage,
    ChatCompletion,
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    ChatMessage,
    CompletionUsage,
    ComplianceCounts,
    ComplianceScore,
    Embedding,
    EmbeddingResponse,
    EvidenceArtifact,
    HealthStatus,
    ModerationResponse,
    ModerationResult,
    PHIAction,
    PHIEntity,
    PHIScanResult,
    Requirement,
    TextCompletion,
    TextCompletionChoice,
)
from ._version import __version__

__all__ = [
    # Clients
    "ClarisMD",
    "AsyncClarisMD",
    # Streaming
    "Stream",
    "AsyncStream",
    # Errors
    "ClarisMDError",
    "APIError",
    "APIConnectionError",
    "APITimeoutError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "PHIPolicyViolationError",
    "BudgetExceededError",
    "ProviderError",
    "InternalServerError",
    # Types
    "APIKey",
    "AuditLog",
    "AuditLogPage",
    "ChatCompletion",
    "ChatCompletionChoice",
    "ChatCompletionChunk",
    "ChatCompletionChunkChoice",
    "ChatCompletionChunkDelta",
    "ChatMessage",
    "ComplianceCounts",
    "ComplianceScore",
    "CompletionUsage",
    "Embedding",
    "EmbeddingResponse",
    "EvidenceArtifact",
    "HealthStatus",
    "ModerationResponse",
    "ModerationResult",
    "PHIAction",
    "PHIEntity",
    "PHIScanResult",
    "Requirement",
    "TextCompletion",
    "TextCompletionChoice",
    # Defaults
    "DEFAULT_BASE_URL",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_TIMEOUT",
    # Version
    "__version__",
]
