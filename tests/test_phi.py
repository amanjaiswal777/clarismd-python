# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.phi.scan`` against the gateway's real ``{results: [...]}`` shape.

The SDK previously parsed a flat ``{detected, entities}`` body the gateway never
sends, so every scan reported "no PHI". These tests pin the real shape."""
from __future__ import annotations

import json

from clarismd import ClarisMD, PHIScanResponse, PHIScanResult

from ._shapes import CLEAN_RESULT, SSN_RESULT
from .conftest import BASE_URL

PHI_URL = f"{BASE_URL}/phi/scan"


def test_phi_scan_surfaces_detected_entities(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(method="POST", url=PHI_URL, json={"results": [SSN_RESULT]})

    response = client.phi.scan("Patient SSN 123-45-6789")
    assert isinstance(response, PHIScanResponse)
    (result,) = response.results
    assert isinstance(result, PHIScanResult)
    assert result.detected is True
    entity = result.entities[0]
    assert (entity.subtype, entity.location.start, entity.location.end) == ("ssn", 12, 23)
    assert entity.matched_text == "123-45-6789"


def test_phi_scan_batch_returns_one_result_per_input(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(method="POST", url=PHI_URL, json={"results": [CLEAN_RESULT, SSN_RESULT]})

    response = client.phi.scan(["clean", "SSN 123-45-6789"])
    assert [r.detected for r in response.results] == [False, True]
    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {"text": ["clean", "SSN 123-45-6789"]}


def test_phi_scan_forwards_scan_types_and_use_ml(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(method="POST", url=PHI_URL, json={"results": [CLEAN_RESULT]})

    client.phi.scan("hi", scan_types=["pii"], use_ml=True)
    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {"text": "hi", "scan_types": ["pii"], "use_ml": True}
