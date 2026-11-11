# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.phi.scan(...)`` — PHI entity detection."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List, Optional, Union

from .._types import PHIScanResult
from ._base import _AsyncResource, _options, _SyncResource


class PHIResource(_SyncResource):
    def scan(
        self,
        text: Union[str, List[str]],
        *,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> PHIScanResult:
        """Scan one string or a batch for PHI.

        Returns a :class:`PHIScanResult` with the detected entity list.
        Note: the input is sent over the wire — only call this against
        text the caller is permitted to transmit.
        """
        body: Dict[str, Any] = {"text": text}
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return self._client.request(
            "POST",
            "/phi/scan",
            json_body=body,
            options=opts,
            cast_to=PHIScanResult,
        )


class AsyncPHIResource(_AsyncResource):
    async def scan(
        self,
        text: Union[str, List[str]],
        *,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> PHIScanResult:
        body: Dict[str, Any] = {"text": text}
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return await self._client.request(
            "POST",
            "/phi/scan",
            json_body=body,
            options=opts,
            cast_to=PHIScanResult,
        )


__all__ = ["PHIResource", "AsyncPHIResource"]
