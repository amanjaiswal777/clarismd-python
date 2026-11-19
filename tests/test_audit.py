# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.audit.{list,get,export}`` against the gateway's real shapes."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from clarismd import AuditExport, AuditLog, AuditLogPage, ClarisMD

from ._shapes import export, log, page
from .conftest import BASE_URL


def test_audit_list_uses_offset_paging(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{BASE_URL}/audit/logs?limit=2",
        json=page(log("a1", 1), log("a2", 2), total=3, limit=2, offset=0),
    )
    httpx_mock.add_response(
        method="GET", url=f"{BASE_URL}/audit/logs?limit=2&offset=2",
        json=page(log("a3", 3), total=3, limit=2, offset=2),
    )

    first = client.audit.list(limit=2)
    assert isinstance(first, AuditLogPage)
    assert [entry.id for entry in first.logs] == ["a1", "a2"]
    assert (first.total, first.has_more) == (3, True)
    assert isinstance(first.logs[0], AuditLog)
    assert first.logs[0].chain_seq == 1 and first.logs[0].entry_hash == "b" * 64

    second = client.audit.list(limit=2, offset=first.offset + len(first.logs))
    assert [entry.id for entry in second.logs] == ["a3"]
    assert second.has_more is False


def test_audit_list_forwards_filters(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(method="GET", json=page(total=0, limit=50, offset=0))

    client.audit.list(
        start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
        end_date="2026-05-31T00:00:00Z",
        action="PHI",
        resource_type="llm_request",
        request_id="req_x",
        phi_detected=True,
    )
    request = httpx_mock.get_request()
    assert request is not None
    q = dict(request.url.params)
    assert q == {
        "start_date": "2026-05-01T00:00:00+00:00",
        "end_date": "2026-05-31T00:00:00Z",
        "action": "PHI",
        "resource_type": "llm_request",
        "request_id": "req_x",
        "phi_detected": "true",
    }


def test_audit_list_rejects_old_cursor_kwarg(client: ClarisMD) -> None:
    with pytest.raises(TypeError):
        client.audit.list(cursor="c1")  # type: ignore[call-arg]


def test_audit_get(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(method="GET", url=f"{BASE_URL}/audit/logs/a9", json=log("a9", 9))
    entry = client.audit.get("a9")
    assert entry.action == "PHI_REDACTED_AND_ALLOWED"
    assert entry.details == {"phi_detected": True}


def test_audit_export_json_is_typed_and_signed(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(method="POST", url=f"{BASE_URL}/audit/export", json=export("json"))

    exp = client.audit.export(start_date="2026-05-01", phi_detected=True)
    assert isinstance(exp, AuditExport)
    assert exp.signature_alg == "Ed25519"
    assert exp.payload is not None and exp.payload["logs"][0]["entry_hash"] == "b" * 64
    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {"format": "json", "start_date": "2026-05-01", "phi_detected": True}


def test_audit_export_pdf_decodes(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(method="POST", url=f"{BASE_URL}/audit/export", json=export("pdf"))

    exp = client.audit.export(format="pdf")
    assert exp.pdf_bytes().startswith(b"%PDF")
