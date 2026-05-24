# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Idempotency-Key auto-generation; identical key returns cached response."""
from __future__ import annotations

from clarismd import ClarisMD

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
