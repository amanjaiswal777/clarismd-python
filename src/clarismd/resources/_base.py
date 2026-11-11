# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Tiny shared helpers for resource classes."""
from __future__ import annotations

from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Dict,
    Optional,
    Union,
)

if TYPE_CHECKING:  # pragma: no cover
    from .._client import AsyncClarisMD, ClarisMD, _RequestOptions  # noqa: F401


def _options(
    *,
    idempotency: Union[str, None, bool],
    policy: Optional[str],
    phi_action: Optional[str],
    extra_headers: Optional[Mapping[str, str]],
    timeout: Optional[float],
) -> _RequestOptions:
    from .._client import _RequestOptions

    headers: Dict[str, str] = {}
    if extra_headers:
        headers.update(extra_headers)
    if policy:
        headers["X-ClarisMD-Policy"] = policy
    if phi_action:
        headers["X-ClarisMD-PHI-Action"] = phi_action
    return _RequestOptions(
        idempotency_key=idempotency,
        extra_headers=headers or None,
        timeout=timeout,
    )


class _SyncResource:
    """Base for sync resource classes."""

    def __init__(self, client: ClarisMD) -> None:
        self._client = client


class _AsyncResource:
    """Base for async resource classes."""

    def __init__(self, client: AsyncClarisMD) -> None:
        self._client = client
