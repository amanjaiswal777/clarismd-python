# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.phi.scan`` round-trip."""
from __future__ import annotations

import json

from clarismd import ClarisMD, PHIScanResult

from .conftest import BASE_URL

PHI_URL = f"{BASE_URL}/phi/scan"


def test_phi_scan_returns_typed_result(client: ClarisMD, httpx_mock) -> None:
    """Detected entities are surfaced as ``PHIEntity`` objects."""
    httpx_mock.add_response(
        method="POST",
        url=PHI_URL,
        json={
            "detected": True,
            "entities": [
                {"type": "PHONE_NUMBER", "text": "(415) 555-0192", "start": 24, "end": 38, "score": 0.99},
                {"type": "PERSON", "text": "Jane Doe", "start": 0, "end": 8, "score": 0.97},
            ],
            "request_id": "req_phi_1",
        },
    )

    result = client.phi.scan("Jane Doe — call me at (415) 555-0192")
    assert isinstance(result, PHIScanResult)
    assert result.detected is True
    assert len(result.entities) == 2
    assert result.entities[0].type == "PHONE_NUMBER"
    assert result.request_id == "req_phi_1"


def test_phi_scan_accepts_list_input(client: ClarisMD, httpx_mock) -> None:
    """Batch scans send the input array verbatim."""
    httpx_mock.add_response(
        method="POST",
        url=PHI_URL,
        json={"detected": False, "entities": []},
    )

    client.phi.scan(["clean text", "also clean"])

    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {"text": ["clean text", "also clean"]}


def test_phi_scan_clean_text(client: ClarisMD, httpx_mock) -> None:
    """No detections returns ``detected=False`` and an empty list."""
    httpx_mock.add_response(
        method="POST",
        url=PHI_URL,
        json={"detected": False, "entities": []},
    )

    result = client.phi.scan("the weather is fine")
    assert result.detected is False
    assert result.entities == []
