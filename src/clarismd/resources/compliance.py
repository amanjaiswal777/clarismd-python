# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.compliance.{score,requirements,evidence,acknowledge}``."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List, Literal, Optional, Union

from .._types import ComplianceScore, EvidenceArtifact, Requirement
from ._base import _AsyncResource, _options, _SyncResource


def _list_requirement_params(
    *,
    framework: str,
    status: Optional[str],
    limit: Optional[int],
    cursor: Optional[str],
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"framework": framework}
    if status is not None:
        params["status"] = status
    if limit is not None:
        params["limit"] = limit
    if cursor is not None:
        params["cursor"] = cursor
    return params


def _ack_body(
    *,
    status: str,
    notes: Optional[str],
    policy_url: Optional[str],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"status": status}
    if notes is not None:
        body["notes"] = notes
    if policy_url is not None:
        body["policy_url"] = policy_url
    return body


def _requirements_from_envelope(raw: Any) -> List[Requirement]:
    """Coerce ``GET /v1/compliance/requirements`` payload into a list.

    The endpoint returns either ``{ "data": [...] }`` (paginated wrapper)
    or a bare array depending on whether ``cursor`` is in play. Normalize
    both shapes so callers always get a ``list[Requirement]``.
    """
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        candidate = raw.get("data")
        items = candidate if isinstance(candidate, list) else []
    else:
        items = []
    return [Requirement.model_validate(item) for item in items]


def _evidence_from_envelope(raw: Any) -> List[EvidenceArtifact]:
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        candidate = raw.get("data")
        items = candidate if isinstance(candidate, list) else []
    else:
        items = []
    return [EvidenceArtifact.model_validate(item) for item in items]


class ComplianceResource(_SyncResource):
    def score(
        self,
        *,
        framework: str = "hipaa",
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> ComplianceScore:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return self._client.request(
            "GET",
            "/compliance/score",
            params={"framework": framework},
            options=opts,
            cast_to=ComplianceScore,
        )

    def requirements(
        self,
        *,
        framework: str = "hipaa",
        status: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> List[Requirement]:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        raw = self._client.request(
            "GET",
            "/compliance/requirements",
            params=_list_requirement_params(
                framework=framework, status=status, limit=limit, cursor=cursor
            ),
            options=opts,
        )
        return _requirements_from_envelope(raw)

    def evidence(
        self,
        requirement_id: str,
        *,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> List[EvidenceArtifact]:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        raw = self._client.request(
            "GET",
            f"/compliance/requirements/{requirement_id}/evidence",
            options=opts,
        )
        return _evidence_from_envelope(raw)

    def acknowledge(
        self,
        requirement_id: str,
        *,
        status: Literal[
            "pending", "acknowledged", "not_applicable", "auto_satisfied"
        ] = "acknowledged",
        notes: Optional[str] = None,
        policy_url: Optional[str] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Requirement:
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        raw = self._client.request(
            "POST",
            f"/compliance/requirements/{requirement_id}/acknowledge",
            json_body=_ack_body(status=status, notes=notes, policy_url=policy_url),
            options=opts,
        )
        # Backend wraps the result in ``{"data": {...}}``; unwrap defensively.
        if isinstance(raw, dict) and "data" in raw and isinstance(raw["data"], dict):
            return Requirement.model_validate(raw["data"])
        if isinstance(raw, dict):
            return Requirement.model_validate(raw)
        raise ValueError("Unexpected acknowledge response shape from gateway.")


class AsyncComplianceResource(_AsyncResource):
    async def score(
        self,
        *,
        framework: str = "hipaa",
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> ComplianceScore:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        return await self._client.request(
            "GET",
            "/compliance/score",
            params={"framework": framework},
            options=opts,
            cast_to=ComplianceScore,
        )

    async def requirements(
        self,
        *,
        framework: str = "hipaa",
        status: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> List[Requirement]:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        raw = await self._client.request(
            "GET",
            "/compliance/requirements",
            params=_list_requirement_params(
                framework=framework, status=status, limit=limit, cursor=cursor
            ),
            options=opts,
        )
        return _requirements_from_envelope(raw)

    async def evidence(
        self,
        requirement_id: str,
        *,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> List[EvidenceArtifact]:
        opts = _options(
            idempotency=None,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        raw = await self._client.request(
            "GET",
            f"/compliance/requirements/{requirement_id}/evidence",
            options=opts,
        )
        return _evidence_from_envelope(raw)

    async def acknowledge(
        self,
        requirement_id: str,
        *,
        status: Literal[
            "pending", "acknowledged", "not_applicable", "auto_satisfied"
        ] = "acknowledged",
        notes: Optional[str] = None,
        policy_url: Optional[str] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Requirement:
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=None,
            phi_action=None,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        raw = await self._client.request(
            "POST",
            f"/compliance/requirements/{requirement_id}/acknowledge",
            json_body=_ack_body(status=status, notes=notes, policy_url=policy_url),
            options=opts,
        )
        if isinstance(raw, dict) and "data" in raw and isinstance(raw["data"], dict):
            return Requirement.model_validate(raw["data"])
        if isinstance(raw, dict):
            return Requirement.model_validate(raw)
        raise ValueError("Unexpected acknowledge response shape from gateway.")


__all__ = ["ComplianceResource", "AsyncComplianceResource"]
