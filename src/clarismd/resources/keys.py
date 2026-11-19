# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.keys.{list,create,get,delete}`` — API key management."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List, Optional, Union

from .._types import APIKey
from ._base import _AsyncResource, _options, _SyncResource


def _create_body(
    *,
    name: Optional[str],
    permissions: Optional[List[str]],
    expires_in_days: Optional[int],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if permissions is not None:
        body["permissions"] = permissions
    if expires_in_days is not None:
        body["expires_in_days"] = expires_in_days
    return body


# The gateway returns a bare array / bare object (no ``{"data": ...}`` envelope).
def _keys_from_response(raw: Any) -> List[APIKey]:
    if not isinstance(raw, list):
        raise ValueError("Unexpected key list response shape from gateway.")
    return [APIKey.model_validate(item) for item in raw]


def _key_from_response(raw: Any) -> APIKey:
    if isinstance(raw, dict):
        return APIKey.model_validate(raw)
    raise ValueError("Unexpected key response shape from gateway.")


class KeysResource(_SyncResource):
    def list(
        self,
        *,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> List[APIKey]:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        raw = self._client.request("GET", "/keys", options=opts)
        return _keys_from_response(raw)

    def create(
        self,
        *,
        name: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> APIKey:
        """Create an API key. The full secret is returned **once**, in ``key`` — store it now.

        Subsequent ``get`` / ``list`` calls return metadata only (``key_prefix``).
        ``expires_in_days`` is 1-365; omit it for a non-expiring key.
        """
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        raw = self._client.request(
            "POST",
            "/keys",
            json_body=_create_body(
                name=name, permissions=permissions, expires_in_days=expires_in_days
            ),
            options=opts,
        )
        return _key_from_response(raw)

    def get(
        self,
        key_id: str,
        *,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> APIKey:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        raw = self._client.request("GET", f"/keys/{key_id}", options=opts)
        return _key_from_response(raw)

    def delete(
        self,
        key_id: str,
        *,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> None:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        self._client.request("DELETE", f"/keys/{key_id}", options=opts)


class AsyncKeysResource(_AsyncResource):
    async def list(
        self,
        *,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> List[APIKey]:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        raw = await self._client.request("GET", "/keys", options=opts)
        return _keys_from_response(raw)

    async def create(
        self,
        *,
        name: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> APIKey:
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        raw = await self._client.request(
            "POST",
            "/keys",
            json_body=_create_body(
                name=name, permissions=permissions, expires_in_days=expires_in_days
            ),
            options=opts,
        )
        return _key_from_response(raw)

    async def get(
        self,
        key_id: str,
        *,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> APIKey:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        raw = await self._client.request("GET", f"/keys/{key_id}", options=opts)
        return _key_from_response(raw)

    async def delete(
        self,
        key_id: str,
        *,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> None:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        await self._client.request("DELETE", f"/keys/{key_id}", options=opts)


__all__ = ["KeysResource", "AsyncKeysResource"]
