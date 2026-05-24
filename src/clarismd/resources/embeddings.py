# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.embeddings.create(...)`` — vector embeddings."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List, Optional, Union

from .._types import EmbeddingResponse, PHIAction
from ._base import _AsyncResource, _options, _SyncResource


def _build_body(
    *,
    model: str,
    input_: Union[str, List[str]],
    user: Optional[str],
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"model": model, "input": input_}
    if user is not None:
        body["user"] = user
    if metadata is not None:
        body["metadata"] = metadata
    return body


class EmbeddingsResource(_SyncResource):
    def create(
        self,
        *,
        model: str,
        input: Union[str, List[str]],
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        clarismd_policy: Optional[str] = None,
        clarismd_phi_action: Optional[PHIAction] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> EmbeddingResponse:
        body = _build_body(model=model, input_=input, user=user, metadata=metadata)
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=clarismd_policy,
            phi_action=clarismd_phi_action,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return self._client.request(
            "POST",
            "/embeddings",
            json_body=body,
            options=opts,
            cast_to=EmbeddingResponse,
        )


class AsyncEmbeddingsResource(_AsyncResource):
    async def create(
        self,
        *,
        model: str,
        input: Union[str, List[str]],
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        clarismd_policy: Optional[str] = None,
        clarismd_phi_action: Optional[PHIAction] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> EmbeddingResponse:
        body = _build_body(model=model, input_=input, user=user, metadata=metadata)
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=clarismd_policy,
            phi_action=clarismd_phi_action,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return await self._client.request(
            "POST",
            "/embeddings",
            json_body=body,
            options=opts,
            cast_to=EmbeddingResponse,
        )


__all__ = ["EmbeddingsResource", "AsyncEmbeddingsResource"]
