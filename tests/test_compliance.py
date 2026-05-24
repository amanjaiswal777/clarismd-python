# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.compliance.{score,requirements,evidence,acknowledge}``."""
from __future__ import annotations

import json

from clarismd import ClarisMD, ComplianceScore, EvidenceArtifact, Requirement

from .conftest import BASE_URL


def test_compliance_score_shape(client: ClarisMD, httpx_mock) -> None:
    """``compliance.score`` returns the auto/manual breakdown."""
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/compliance/score?framework=hipaa",
        json={
            "auto_verified": {"satisfied": 45, "total": 60},
            "manual": {"acknowledged": 8, "total": 12, "satisfied": 8},
            "framework": "hipaa",
            "as_of": "2026-05-24T00:00:00+00:00",
            "request_id": "req_score",
        },
    )

    score = client.compliance.score()
    assert isinstance(score, ComplianceScore)
    assert score.auto_verified.satisfied == 45
    assert score.auto_verified.total == 60
    assert score.manual.acknowledged == 8


def test_compliance_requirements_envelope_unwrapped(
    client: ClarisMD, httpx_mock
) -> None:
    """The list endpoint may return either ``{ "data": [...] }`` or a bare array."""
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/compliance/requirements?framework=hipaa",
        json={
            "data": [
                {
                    "id": "req-1",
                    "code": "164.308(a)(1)",
                    "title": "Risk analysis",
                    "framework": "hipaa",
                    "acknowledgment_status": "acknowledged",
                    "evidence_count": 2,
                },
                {
                    "id": "req-2",
                    "code": "164.308(a)(3)",
                    "title": "Workforce security",
                    "framework": "hipaa",
                    "acknowledgment_status": "pending",
                    "evidence_count": 0,
                },
            ]
        },
    )

    items = client.compliance.requirements()
    assert len(items) == 2
    assert all(isinstance(r, Requirement) for r in items)
    assert items[0].acknowledgment_status == "acknowledged"


def test_compliance_evidence_returns_list(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/compliance/requirements/req-1/evidence",
        json={
            "data": [
                {
                    "id": "ev-1",
                    "requirement_id": "req-1",
                    "audit_log_id": "audit-99",
                    "artifact_type": "auto_check",
                    "evidence_payload": {"check": "tls_capture", "result": "pass"},
                    "created_at": "2026-05-24T00:00:00+00:00",
                }
            ]
        },
    )

    evidence = client.compliance.evidence("req-1")
    assert len(evidence) == 1
    assert isinstance(evidence[0], EvidenceArtifact)
    assert evidence[0].artifact_type == "auto_check"


def test_compliance_acknowledge_posts_status(client: ClarisMD, httpx_mock) -> None:
    """``acknowledge`` POSTs the status + notes and returns the updated row."""
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/compliance/requirements/req-1/acknowledge",
        json={
            "data": {
                "id": "req-1",
                "code": "164.308(a)(1)",
                "framework": "hipaa",
                "acknowledgment_status": "acknowledged",
                "notes": "annual review complete",
                "policy_url": "https://wiki.example/risk-analysis",
                "evidence_count": 2,
            }
        },
    )

    updated = client.compliance.acknowledge(
        "req-1",
        status="acknowledged",
        notes="annual review complete",
        policy_url="https://wiki.example/risk-analysis",
    )

    assert isinstance(updated, Requirement)
    assert updated.acknowledgment_status == "acknowledged"
    assert updated.notes == "annual review complete"

    request = httpx_mock.get_request()
    assert request is not None
    body = json.loads(request.content)
    assert body == {
        "status": "acknowledged",
        "notes": "annual review complete",
        "policy_url": "https://wiki.example/risk-analysis",
    }
