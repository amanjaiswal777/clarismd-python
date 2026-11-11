# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.moderations.create(...)`` — content moderation."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List, Optional, Union

from .._types import ModerationResponse
from ._base import _AsyncResource, _options, _SyncResource


def _build_body(
    *,
    input_: Union[str, List[str]],
    model: Optional[str],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"input": input_}
    if model is not None:
        body["model"] = model
    return body


class ModerationsResource(_SyncResource):
    def create(
        self,
        *,
        input: Union[str, List[str]],
        model: Optional[str] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> ModerationResponse:
        body = _build_body(input_=input, model=model)
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return self._client.request(
            "POST",
            "/moderations",
            json_body=body,
            options=opts,
            cast_to=ModerationResponse,
        )


class AsyncModerationsResource(_AsyncResource):
    async def create(
        self,
        *,
        input: Union[str, List[str]],
        model: Optional[str] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> ModerationResponse:
        body = _build_body(input_=input, model=model)
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return await self._client.request(
            "POST",
            "/moderations",
            json_body=body,
            options=opts,
            cast_to=ModerationResponse,
        )


__all__ = ["ModerationsResource", "AsyncModerationsResource"]
