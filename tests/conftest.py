# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Shared pytest fixtures for the SDK tests.

The SDK ships a baked-in retry loop with sleep delays between attempts
— in tests we patch ``time.sleep`` / ``asyncio.sleep`` to no-ops so the
suite runs in milliseconds rather than seconds. Same goes for the
random jitter on backoff.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Tests run with ``pip install -e .`` in CI, but for local ``pytest``
# without an editable install we make sure the in-tree source wins.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


BASE_URL = "https://gateway.test.example/v1"
API_KEY = "cmd-test-key"


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace blocking sleep with a no-op for retry tests."""
    import asyncio

    async def _async_noop(_seconds: float) -> None:
        return None

    monkeypatch.setattr("time.sleep", lambda _s: None)
    monkeypatch.setattr(asyncio, "sleep", _async_noop)


@pytest.fixture(autouse=True)
def _deterministic_jitter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin jitter to zero so retry timings are reproducible."""
    monkeypatch.setattr("clarismd._client.random.random", lambda: 0.0)


@pytest.fixture
def client():
    """Sync client with a deterministic base_url + api_key."""
    from clarismd import ClarisMD

    c = ClarisMD(api_key=API_KEY, base_url=BASE_URL, max_retries=2, timeout=5.0)
    try:
        yield c
    finally:
        c.close()


@pytest.fixture
async def async_client():
    """Async client with a deterministic base_url + api_key."""
    from clarismd import AsyncClarisMD

    c = AsyncClarisMD(api_key=API_KEY, base_url=BASE_URL, max_retries=2, timeout=5.0)
    try:
        yield c
    finally:
        await c.aclose()
