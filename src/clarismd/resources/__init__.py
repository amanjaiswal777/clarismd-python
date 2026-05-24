# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Resource namespaces — one module per `/v1` collection."""

from .audit import AsyncAuditResource, AuditResource
from .chat import (
    AsyncChatCompletionsResource,
    AsyncChatResource,
    ChatCompletionsResource,
    ChatResource,
)
from .completions import AsyncCompletionsResource, CompletionsResource
from .compliance import AsyncComplianceResource, ComplianceResource
from .embeddings import AsyncEmbeddingsResource, EmbeddingsResource
from .health import AsyncHealthResource, HealthResource
from .keys import AsyncKeysResource, KeysResource
from .moderations import AsyncModerationsResource, ModerationsResource
from .phi import AsyncPHIResource, PHIResource

__all__ = [
    "AsyncAuditResource",
    "AsyncChatCompletionsResource",
    "AsyncChatResource",
    "AsyncCompletionsResource",
    "AsyncComplianceResource",
    "AsyncEmbeddingsResource",
    "AsyncHealthResource",
    "AsyncKeysResource",
    "AsyncModerationsResource",
    "AsyncPHIResource",
    "AuditResource",
    "ChatCompletionsResource",
    "ChatResource",
    "CompletionsResource",
    "ComplianceResource",
    "EmbeddingsResource",
    "HealthResource",
    "KeysResource",
    "ModerationsResource",
    "PHIResource",
]
