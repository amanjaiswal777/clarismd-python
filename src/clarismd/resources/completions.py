# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.completions.create(...)`` — legacy single-prompt completion."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Optional, Union

from .._types import PHIAction, TextCompletion
from ._base import _AsyncResource, _options, _SyncResource


def _build_body(
    *,
    model: str,
    prompt: str,
    extra: Dict[str, Any],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"model": model, "prompt": prompt}
    body.update({k: v for k, v in extra.items() if v is not None})
    return body


class CompletionsResource(_SyncResource):
    def create(
        self,
        *,
        model: str,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[Union[str, list[str]]] = None,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        clarismd_policy: Optional[str] = None,
        clarismd_phi_action: Optional[PHIAction] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> TextCompletion:
        body = _build_body(
            model=model,
            prompt=prompt,
            extra={
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "stop": stop,
                "user": user,
                "metadata": metadata,
            },
        )
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=clarismd_policy,
            phi_action=clarismd_phi_action,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return self._client.request(
            "POST",
            "/completions",
            json_body=body,
            options=opts,
            cast_to=TextCompletion,
        )


class AsyncCompletionsResource(_AsyncResource):
    async def create(
        self,
        *,
        model: str,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stop: Optional[Union[str, list[str]]] = None,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        clarismd_policy: Optional[str] = None,
        clarismd_phi_action: Optional[PHIAction] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> TextCompletion:
        body = _build_body(
            model=model,
            prompt=prompt,
            extra={
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "stop": stop,
                "user": user,
                "metadata": metadata,
            },
        )
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=clarismd_policy,
            phi_action=clarismd_phi_action,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return await self._client.request(
            "POST",
            "/completions",
            json_body=body,
            options=opts,
            cast_to=TextCompletion,
        )


__all__ = ["CompletionsResource", "AsyncCompletionsResource"]
