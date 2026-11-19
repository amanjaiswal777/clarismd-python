# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Response bodies copied from the backend's pinned /v1 contract
(clarismd-backend ``tests/integration/test_v1_contract_shapes.py``).
Change them only together with the backend."""
from __future__ import annotations

from typing import Any, Dict

KEY: Dict[str, Any] = {
    "id": "5d1c3f7e-1a2b-4c3d-8e9f-001122334455",
    "key_prefix": "cmd_live_ab12",
    "name": "ci",
    "permissions": ["chat"],
    "expires_at": "2026-12-19T18:00:00+00:00",
    "revoked": False,
    "last_used": None,
    "created_by_session_id": None,
    "created_at": "2026-11-19T18:00:00+00:00",
    "key": None,
}

SSN_RESULT: Dict[str, Any] = {
    "scan_id": "scan_1",
    "overall_risk_score": 0.9,
    "should_block": False,
    "entities": [
        {
            "type": "pii",
            "subtype": "ssn",
            "severity": "high",
            "confidence": 0.95,
            "location": {"start": 12, "end": 23},
            "matched_pattern": "ssn",
            "matched_text": "123-45-6789",
        }
    ],
    "scan_duration_ms": 3.2,
}

CLEAN_RESULT: Dict[str, Any] = {
    "scan_id": "scan_2",
    "overall_risk_score": 0.0,
    "should_block": False,
    "entities": [],
    "scan_duration_ms": 1.1,
}


def log(audit_id: str, seq: int = 1) -> Dict[str, Any]:
    return {
        "id": audit_id,
        "action": "PHI_REDACTED_AND_ALLOWED",
        "resource_type": "llm_request",
        "resource_id": None,
        "details": {"phi_detected": True},
        "ip_address": None,
        "user_agent": None,
        "created_at": "2026-11-19T18:00:00.000000+00:00",
        "org_id": "6b1f0c4e-0000-4000-8000-000000000001",
        "user_id": "6b1f0c4e-0000-4000-8000-000000000002",
        "chain_seq": seq,
        "prev_hash": "a" * 64,
        "entry_hash": "b" * 64,
        "created_at_canonical": "2026-11-19T18:00:00.000000Z",
    }


def page(*logs: Dict[str, Any], total: int, limit: int, offset: int) -> Dict[str, Any]:
    return {"logs": list(logs), "total": total, "limit": limit, "offset": offset,
            "has_more": offset + len(logs) < total}


def export(fmt: str = "json") -> Dict[str, Any]:
    return {
        "export_id": "exp_abc",
        "format": fmt,
        "record_count": 1,
        "generated_at": "2026-11-19T18:00:00",
        "download_url": None,
        "payload": {"logs": [log("a1")], "filters": {"format": fmt}} if fmt == "json" else None,
        "signature": "ed25519:84320e154b7cc8c9:c2lnbmF0dXJl",
        "signature_alg": "Ed25519",
        "key_id": "84320e154b7cc8c9",
        "public_keys_url": "/api/v1/evidence/signing-keys",
        "pdf_base64": "JVBERi0xLjc=" if fmt == "pdf" else None,
    }
