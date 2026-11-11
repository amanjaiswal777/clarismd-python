# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Retry policy — 429/5xx retry, 4xx no-retry, Retry-After honored."""
from __future__ import annotations

import pytest

from clarismd import (
    ClarisMD,
    NotFoundError,
    PHIPolicyViolationError,
    UnprocessableEntityError,
)

from .conftest import BASE_URL

CHAT_URL = f"{BASE_URL}/chat/completions"


def _ok_payload() -> dict:
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 1719000000,
        "model": "gpt-4o-mini",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}}],
    }


def test_retries_on_500_then_succeeds(client: ClarisMD, httpx_mock) -> None:
    """A 500 followed by a 200 is retried transparently."""
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=500,
        json={"error": {"type": "internal_server_error", "message": "boom"}},
    )
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_ok_payload())

    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )
    assert result.choices[0].message.content == "ok"
    assert len(httpx_mock.get_requests()) == 2


def test_retries_on_429_with_retry_after(client: ClarisMD, httpx_mock) -> None:
    """429 with ``Retry-After: 1`` is retried."""
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=429,
        headers={"Retry-After": "1"},
        json={"error": {"type": "rate_limit_exceeded", "message": "slow down"}},
    )
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_ok_payload())

    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )
    assert result.id == "chatcmpl-1"
    assert len(httpx_mock.get_requests()) == 2


def test_retries_on_503_then_succeeds(client: ClarisMD, httpx_mock) -> None:
    """503 (provider unavailable) is retryable."""
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=503,
        json={"error": {"type": "provider_error", "message": "upstream down"}},
    )
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_ok_payload())

    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )
    assert result.id == "chatcmpl-1"
    assert len(httpx_mock.get_requests()) == 2


def test_no_retry_on_4xx_phi_violation(client: ClarisMD, httpx_mock) -> None:
    """PHI violations are deterministic — never retried."""
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=400,
        json={"error": {"type": "phi_policy_violation", "message": "PHI in prompt"}},
    )

    with pytest.raises(PHIPolicyViolationError):
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "patient SSN 111-22-3333"}],
        )

    # Exactly one attempt — not three.
    assert len(httpx_mock.get_requests()) == 1


def test_no_retry_on_404(client: ClarisMD, httpx_mock) -> None:
    """404 is not retried."""
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=404,
        json={"error": {"type": "not_found", "message": "no such model"}},
    )

    with pytest.raises(NotFoundError):
        client.chat.completions.create(
            model="ghost",
            messages=[{"role": "user", "content": "Hi"}],
        )

    assert len(httpx_mock.get_requests()) == 1


def test_no_retry_on_422(client: ClarisMD, httpx_mock) -> None:
    """Validation errors are deterministic — never retried."""
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=422,
        json={"error": {"type": "unprocessable_entity", "message": "bad shape"}},
    )

    with pytest.raises(UnprocessableEntityError):
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
        )

    assert len(httpx_mock.get_requests()) == 1


def test_max_retries_zero_disables_retries() -> None:
    """``max_retries=0`` raises immediately on the first 5xx."""
    from clarismd import InternalServerError

    client = ClarisMD(api_key="cmd-x", base_url=BASE_URL, max_retries=0)
    try:
        # We cannot use the httpx_mock fixture from another test scope; build
        # a tiny inline mock by monkey-patching the underlying client.
        import httpx

        responses = iter(
            [
                httpx.Response(
                    500,
                    json={"error": {"type": "internal_server_error", "message": "boom"}},
                    request=httpx.Request("POST", f"{BASE_URL}/chat/completions"),
                )
            ]
        )

        def fake_request(*args, **kwargs):
            return next(responses)

        client._http.request = fake_request  # type: ignore[method-assign]

        with pytest.raises(InternalServerError):
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hi"}],
            )
    finally:
        client.close()


def test_retry_after_caps_long_waits(monkeypatch) -> None:
    """A pathological ``Retry-After: 999999`` is capped to 60s."""
    from clarismd._client import _retry_delay

    assert _retry_delay(0, "999999") == pytest.approx(60.0)
    assert _retry_delay(0, "5") == pytest.approx(5.0)
    assert _retry_delay(0, "not-a-number") == pytest.approx(0.5)
    # exhaust the backoff schedule -> last-known value
    assert _retry_delay(99, None) == pytest.approx(2.0)
