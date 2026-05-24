# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.audit.{list,get,export}``."""
from __future__ import annotations

from datetime import datetime, timezone

from clarismd import AuditLog, AuditLogPage, ClarisMD

from .conftest import BASE_URL


def _row(audit_id: str) -> dict:
    return {
        "id": audit_id,
        "request_id": "req_x",
        "user_id": "user_1",
        "endpoint": "/v1/chat/completions",
        "model": "gpt-4o-mini",
        "phi_detected": True,
        "phi_action": "redact",
        "cost_usd": 0.0034,
        "timestamp": "2026-05-24T01:23:45+00:00",
        "metadata": {},
    }


def test_audit_list_pages(client: ClarisMD, httpx_mock) -> None:
    """First call returns a cursor; second call uses it to fetch the next page."""
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/audit/logs?limit=2",
        json={"data": [_row("a1"), _row("a2")], "next_cursor": "cursor-2", "has_more": True},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/audit/logs?limit=2&cursor=cursor-2",
        json={"data": [_row("a3")], "next_cursor": None, "has_more": False},
    )

    page1 = client.audit.list(limit=2)
    assert isinstance(page1, AuditLogPage)
    assert page1.has_more is True
    assert page1.next_cursor == "cursor-2"
    assert [log.id for log in page1.data] == ["a1", "a2"]

    page2 = client.audit.list(limit=2, cursor="cursor-2")
    assert page2.has_more is False
    assert [log.id for log in page2.data] == ["a3"]


def test_audit_list_serializes_datetime_filters(
    client: ClarisMD, httpx_mock
) -> None:
    """``datetime`` values are passed as ISO-8601 query params."""
    httpx_mock.add_response(
        method="GET",
        json={"data": [], "next_cursor": None, "has_more": False},
    )

    start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    end = datetime(2026, 5, 31, tzinfo=timezone.utc)
    client.audit.list(start_date=start, end_date=end, phi_detected=True)

    request = httpx_mock.get_request()
    assert request is not None
    qs = request.url.params
    assert qs["start_date"] == start.isoformat()
    assert qs["end_date"] == end.isoformat()
    assert qs["phi_detected"] == "true"


def test_audit_get_returns_single_record(client: ClarisMD, httpx_mock) -> None:
    """``audit.get`` deserializes one ``AuditLog`` row."""
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/audit/logs/audit_123",
        json=_row("audit_123"),
    )

    log = client.audit.get("audit_123")
    assert isinstance(log, AuditLog)
    assert log.id == "audit_123"
    assert log.phi_detected is True


def test_audit_export_returns_bytes(client: ClarisMD, httpx_mock) -> None:
    """``audit.export`` returns the raw evidence bytes."""
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/audit/export",
        content=b"%PDF-1.7\n...",
        headers={"content-type": "application/pdf"},
    )

    result = client.audit.export(format="pdf")
    assert isinstance(result, bytes)
    assert result.startswith(b"%PDF")
