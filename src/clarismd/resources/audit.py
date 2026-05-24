# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.audit.{list,get,export}`` — audit log access."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Dict, Optional, Union

from .._types import AuditLog, AuditLogPage
from ._base import _AsyncResource, _options, _SyncResource


def _isoformat(value: Union[None, str, datetime]) -> Optional[str]:
    if value is None or isinstance(value, str):
        return value
    return value.isoformat()


def _list_params(
    *,
    start_date: Union[None, str, datetime],
    end_date: Union[None, str, datetime],
    limit: Optional[int],
    cursor: Optional[str],
    request_id: Optional[str],
    phi_detected: Optional[bool],
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if start_date is not None:
        params["start_date"] = _isoformat(start_date)
    if end_date is not None:
        params["end_date"] = _isoformat(end_date)
    if limit is not None:
        params["limit"] = limit
    if cursor is not None:
        params["cursor"] = cursor
    if request_id is not None:
        params["request_id"] = request_id
    if phi_detected is not None:
        params["phi_detected"] = "true" if phi_detected else "false"
    return params


def _export_body(
    *,
    format: str,
    start_date: Union[None, str, datetime],
    end_date: Union[None, str, datetime],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"format": format}
    if start_date is not None:
        body["start_date"] = _isoformat(start_date)
    if end_date is not None:
        body["end_date"] = _isoformat(end_date)
    return body


class AuditResource(_SyncResource):
    def list(
        self,
        *,
        start_date: Union[None, str, datetime] = None,
        end_date: Union[None, str, datetime] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        request_id: Optional[str] = None,
        phi_detected: Optional[bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> AuditLogPage:
        params = _list_params(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            cursor=cursor,
            request_id=request_id,
            phi_detected=phi_detected,
        )
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return self._client.request(
            "GET",
            "/audit/logs",
            params=params,
            options=opts,
            cast_to=AuditLogPage,
        )

    def get(
        self,
        audit_id: str,
        *,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> AuditLog:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return self._client.request(
            "GET",
            f"/audit/logs/{audit_id}",
            options=opts,
            cast_to=AuditLog,
        )

    def export(
        self,
        *,
        format: str = "json",
        start_date: Union[None, str, datetime] = None,
        end_date: Union[None, str, datetime] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> bytes:
        """Export an audit evidence package.

        Returns the raw bytes — the gateway responds with a signed
        archive (PDF or JSON depending on ``format``). Callers write
        the bytes to disk or feed them to whatever evidence locker
        they're integrating with.
        """
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        result = self._client.request(
            "POST",
            "/audit/export",
            json_body=_export_body(format=format, start_date=start_date, end_date=end_date),
            options=opts,
        )
        if isinstance(result, bytes):
            return result
        if isinstance(result, dict):
            # Some operators emit JSON envelopes around the export blob;
            # serialize to UTF-8 so callers always receive bytes.
            import json

            return json.dumps(result).encode("utf-8")
        return b""


class AsyncAuditResource(_AsyncResource):
    async def list(
        self,
        *,
        start_date: Union[None, str, datetime] = None,
        end_date: Union[None, str, datetime] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        request_id: Optional[str] = None,
        phi_detected: Optional[bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> AuditLogPage:
        params = _list_params(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            cursor=cursor,
            request_id=request_id,
            phi_detected=phi_detected,
        )
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return await self._client.request(
            "GET",
            "/audit/logs",
            params=params,
            options=opts,
            cast_to=AuditLogPage,
        )

    async def get(
        self,
        audit_id: str,
        *,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> AuditLog:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return await self._client.request(
            "GET",
            f"/audit/logs/{audit_id}",
            options=opts,
            cast_to=AuditLog,
        )

    async def export(
        self,
        *,
        format: str = "json",
        start_date: Union[None, str, datetime] = None,
        end_date: Union[None, str, datetime] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> bytes:
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        result = await self._client.request(
            "POST",
            "/audit/export",
            json_body=_export_body(format=format, start_date=start_date, end_date=end_date),
            options=opts,
        )
        if isinstance(result, bytes):
            return result
        if isinstance(result, dict):
            import json

            return json.dumps(result).encode("utf-8")
        return b""


__all__ = ["AuditResource", "AsyncAuditResource"]
