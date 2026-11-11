# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.health.check()`` — gateway liveness probe.

No authentication required. Useful for self-host setup verification and
for callers that want to confirm the configured ``base_url`` is reachable
before issuing a chat completion.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Optional

from .._types import HealthStatus
from ._base import _AsyncResource, _options, _SyncResource


class HealthResource(_SyncResource):
    def check(
        self,
        *,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> HealthStatus:
        """Return ``{"status": "ok", "version": "..."}`` from the gateway."""
        opts = _options(
            idempotency=False,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return self._client.request(
            "GET",
            "/health",
            options=opts,
            cast_to=HealthStatus,
        )


class AsyncHealthResource(_AsyncResource):
    async def check(
        self,
        *,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> HealthStatus:
        opts = _options(
            idempotency=False,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return await self._client.request(
            "GET",
            "/health",
            options=opts,
            cast_to=HealthStatus,
        )


__all__ = ["HealthResource", "AsyncHealthResource"]
