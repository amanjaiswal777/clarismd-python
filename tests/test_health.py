# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.health.check()`` round-trip."""
from __future__ import annotations

import pytest

from clarismd import AsyncClarisMD, ClarisMD, HealthStatus

from .conftest import BASE_URL

HEALTH_URL = f"{BASE_URL}/health"


def test_health_check_returns_typed_status(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=HEALTH_URL,
        json={"status": "ok", "version": "0.4.2"},
    )

    result = client.health.check()
    assert isinstance(result, HealthStatus)
    assert result.status == "ok"
    assert result.version == "0.4.2"


def test_health_check_no_idempotency_key_sent(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=HEALTH_URL,
        json={"status": "ok"},
    )

    client.health.check()

    request = httpx_mock.get_request()
    assert request is not None
    assert "Idempotency-Key" not in request.headers


def test_health_works_without_api_key(httpx_mock) -> None:
    """Liveness probe should not require auth — useful pre-credential."""
    httpx_mock.add_response(
        method="GET",
        url=HEALTH_URL,
        json={"status": "ok"},
    )

    c = ClarisMD(api_key=None, base_url=BASE_URL)
    try:
        c.health.check()
    finally:
        c.close()

    request = httpx_mock.get_request()
    assert request is not None
    assert "Authorization" not in request.headers


@pytest.mark.asyncio
async def test_health_check_async(async_client: AsyncClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=HEALTH_URL,
        json={"status": "ok", "version": "0.4.2"},
    )

    result = await async_client.health.check()
    assert result.status == "ok"
    assert result.version == "0.4.2"
