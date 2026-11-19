# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.phi.scan(...)`` — PHI entity detection."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List, Optional, Union

from .._types import PHIScanResponse
from ._base import _AsyncResource, _options, _SyncResource


def _scan_body(
    text: Union[str, List[str]],
    *,
    scan_types: Optional[List[str]],
    use_ml: Optional[bool],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"text": text}
    if scan_types is not None:
        body["scan_types"] = scan_types
    if use_ml is not None:
        body["use_ml"] = use_ml
    return body


class PHIResource(_SyncResource):
    def scan(
        self,
        text: Union[str, List[str]],
        *,
        scan_types: Optional[List[str]] = None,
        use_ml: Optional[bool] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> PHIScanResponse:
        """Scan one string or a batch for PHI.

        Returns a :class:`PHIScanResponse` with one :class:`PHIScanResult`
        per input, in order (``response.results[0]`` for a single string).
        Note: the input is sent over the wire — only call this against
        text the caller is permitted to transmit.
        """
        body = _scan_body(text, scan_types=scan_types, use_ml=use_ml)
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
            cast_to=PHIScanResponse,
        )


class AsyncPHIResource(_AsyncResource):
    async def scan(
        self,
        text: Union[str, List[str]],
        *,
        scan_types: Optional[List[str]] = None,
        use_ml: Optional[bool] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> PHIScanResponse:
        body = _scan_body(text, scan_types=scan_types, use_ml=use_ml)
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
            cast_to=PHIScanResponse,
        )


__all__ = ["PHIResource", "AsyncPHIResource"]
