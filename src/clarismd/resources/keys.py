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
    scopes: Optional[List[str]],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if scopes is not None:
        body["scopes"] = scopes
    return body


def _keys_from_envelope(raw: Any) -> List[APIKey]:
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        candidate = raw.get("data")
        items = candidate if isinstance(candidate, list) else []
    else:
        items = []
    return [APIKey.model_validate(item) for item in items]


def _key_from_envelope(raw: Any) -> APIKey:
    if isinstance(raw, dict) and "data" in raw and isinstance(raw["data"], dict):
        return APIKey.model_validate(raw["data"])
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
        return _keys_from_envelope(raw)

    def create(
        self,
        *,
        name: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> APIKey:
        """Create an API key. The full ``secret`` is returned **once** — store it now.

        The gateway returns the secret on this response only; subsequent
        ``get`` calls return the metadata without the secret.
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
            json_body=_create_body(name=name, scopes=scopes),
            options=opts,
        )
        return _key_from_envelope(raw)

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
        return _key_from_envelope(raw)

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
        return _keys_from_envelope(raw)

    async def create(
        self,
        *,
        name: Optional[str] = None,
        scopes: Optional[List[str]] = None,
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
            json_body=_create_body(name=name, scopes=scopes),
            options=opts,
        )
        return _key_from_envelope(raw)

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
        return _key_from_envelope(raw)

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
