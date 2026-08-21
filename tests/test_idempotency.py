# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Idempotency-Key auto-generation; identical key returns cached response."""
from __future__ import annotations

import httpx
import pytest

from clarismd import AsyncClarisMD, ClarisMD

from .conftest import BASE_URL

CHAT_URL = f"{BASE_URL}/chat/completions"


def _ok() -> dict:
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 1719000000,
        "model": "gpt-4o-mini",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}}],
    }


def test_auto_generated_key_format(client: ClarisMD, httpx_mock) -> None:
    """Auto-key uses the ``cmd-py-{uuid}`` shape and is unique per request."""
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_ok())
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_ok())

    client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )
    client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )

    requests = httpx_mock.get_requests()
    keys = [r.headers["Idempotency-Key"] for r in requests]
    assert all(k.startswith("cmd-py-") for k in keys)
    # Two distinct calls -> two distinct keys.
    assert keys[0] != keys[1]


def test_explicit_key_replays_cached_response(
    client: ClarisMD, httpx_mock
) -> None:
    """When a caller supplies a fixed key, every request goes out with that exact value.

    The backend is responsible for the cache; the SDK's job here is just
    to attach the header verbatim. We assert the on-the-wire header
    rather than mocking a "cached response" — that's a backend test.
    """
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_ok())
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_ok())

    fixed = "cmd-deterministic-replay-1"
    for _ in range(2):
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            clarismd_idempotency_key=fixed,
        )

    requests = httpx_mock.get_requests()
    assert all(r.headers["Idempotency-Key"] == fixed for r in requests)


def test_retry_reuses_the_same_auto_generated_key(
    client: ClarisMD, httpx_mock
) -> None:
    """A retry must carry the key of the attempt it is retrying.

    This is the assertion the defect could not survive. The header build sat
    inside the retry loop, so an auto-generated key was a fresh uuid4 per
    attempt — the server saw two unrelated POSTs where the caller made one, and
    the idempotency cache could never match. In a product that meters cost, a
    5xx retried once billed twice.
    """
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=500,
        json={"error": {"type": "internal_server_error", "message": "boom"}},
    )
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_ok())

    client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )

    keys = [r.headers["Idempotency-Key"] for r in httpx_mock.get_requests()]
    assert len(keys) == 2, "expected one retry"
    assert keys[0] == keys[1]


def test_retry_after_timeout_reuses_the_same_key(
    client: ClarisMD, httpx_mock
) -> None:
    """The timeout path is the one that actually costs money.

    A 500 means the gateway rejected the request. A timeout means it may have
    completed, billed and been metered while the response was in flight — so
    this is the retry where a fresh key turns one charge into two.
    """
    httpx_mock.add_exception(httpx.ReadTimeout("timed out"))
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_ok())

    client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )

    keys = [r.headers["Idempotency-Key"] for r in httpx_mock.get_requests()]
    assert len(keys) == 2, "expected one retry"
    assert keys[0] == keys[1]


@pytest.mark.asyncio
async def test_async_retry_reuses_the_same_auto_generated_key(
    async_client: AsyncClarisMD, httpx_mock
) -> None:
    """The async client had the identical defect and needs the identical guard.

    Asserted separately rather than parametrized: the two request loops are
    duplicated source, so a fix applied to one and not the other is exactly the
    failure mode worth catching.
    """
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=503,
        json={"error": {"type": "service_unavailable", "message": "draining"}},
    )
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_ok())

    await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )

    keys = [r.headers["Idempotency-Key"] for r in httpx_mock.get_requests()]
    assert len(keys) == 2, "expected one retry"
    assert keys[0] == keys[1]


def test_get_requests_have_no_idempotency_header(
    client: ClarisMD, httpx_mock
) -> None:
    """The header is POST-only; GETs are naturally idempotent already."""
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/audit/logs",
        json={"data": [], "next_cursor": None, "has_more": False},
    )

    client.audit.list()

    request = httpx_mock.get_request()
    assert request is not None
    assert "Idempotency-Key" not in request.headers


def test_delete_requests_have_no_idempotency_header(
    client: ClarisMD, httpx_mock
) -> None:
    """DELETE is also exempt — keys carry no body to cache."""
    httpx_mock.add_response(
        method="DELETE", url=f"{BASE_URL}/keys/key_123", status_code=204
    )

    client.keys.delete("key_123")

    request = httpx_mock.get_request()
    assert request is not None
    assert "Idempotency-Key" not in request.headers
