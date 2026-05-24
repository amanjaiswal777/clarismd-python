# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""End-to-end happy-path coverage for ``chat.completions.create``."""
from __future__ import annotations

import json

import httpx
import pytest

from clarismd import ChatCompletion, ClarisMD

from .conftest import API_KEY, BASE_URL

CHAT_URL = f"{BASE_URL}/chat/completions"


def _completion_payload() -> dict:
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 1719000000,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hi!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
    }


def test_chat_completions_basic(client: ClarisMD, httpx_mock) -> None:
    """A 200 response decodes into a ChatCompletion."""
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        json=_completion_payload(),
        headers={"X-Request-ID": "req_abc123"},
    )

    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )

    assert isinstance(result, ChatCompletion)
    assert result.id == "chatcmpl-1"
    assert result.choices[0].message.content == "Hi!"
    assert result.request_id == "req_abc123"


def test_chat_completions_sends_authorization_and_idempotency(
    client: ClarisMD, httpx_mock
) -> None:
    """Bearer header + auto-generated Idempotency-Key go on every POST."""
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_completion_payload())

    client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["Authorization"] == f"Bearer {API_KEY}"
    assert request.headers["User-Agent"].startswith("clarismd-python/")
    assert request.headers["Idempotency-Key"].startswith("cmd-py-")


def test_chat_completions_clarismd_overrides_become_headers(
    client: ClarisMD, httpx_mock
) -> None:
    """``clarismd_policy`` and ``clarismd_phi_action`` map to X-ClarisMD-* headers."""
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_completion_payload())

    client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        clarismd_policy="hipaa-strict",
        clarismd_phi_action="redact",
    )

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["X-ClarisMD-Policy"] == "hipaa-strict"
    assert request.headers["X-ClarisMD-PHI-Action"] == "redact"


def test_chat_completions_body_excludes_none_values(
    client: ClarisMD, httpx_mock
) -> None:
    """Keys whose value is ``None`` must NOT appear on the wire."""
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_completion_payload())

    client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        temperature=0.2,
    )

    request = httpx_mock.get_request()
    assert request is not None
    body = json.loads(request.content)
    assert body["temperature"] == 0.2
    # presence_penalty / frequency_penalty / etc. were never set -> not in body
    for k in ("presence_penalty", "frequency_penalty", "logit_bias", "stop"):
        assert k not in body


def test_explicit_idempotency_key_passed_through(
    client: ClarisMD, httpx_mock
) -> None:
    """Caller-supplied idempotency key wins over auto-generation."""
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_completion_payload())

    client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        clarismd_idempotency_key="my-deterministic-key-123",
    )

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["Idempotency-Key"] == "my-deterministic-key-123"


def test_idempotency_disabled_strips_header(client: ClarisMD, httpx_mock) -> None:
    """``clarismd_idempotency_key=False`` opts out of the header entirely."""
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_completion_payload())

    client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        clarismd_idempotency_key=False,
    )

    request = httpx_mock.get_request()
    assert request is not None
    assert "Idempotency-Key" not in request.headers


def test_custom_base_url_used_for_self_host() -> None:
    """``base_url=...`` overrides the default for self-hosted gateways."""
    client = ClarisMD(api_key="cmd-x", base_url="https://internal.example/v1/")
    try:
        # Trailing slash is stripped so URLs join cleanly.
        assert client.base_url == "https://internal.example/v1"
    finally:
        client.close()


def test_env_base_url_used_when_no_argument(monkeypatch) -> None:
    """``CLARISMD_BASE_URL`` is honored when no ``base_url=`` is supplied."""
    monkeypatch.setenv("CLARISMD_BASE_URL", "https://env.example/v1")
    client = ClarisMD(api_key="cmd-x")
    try:
        assert client.base_url == "https://env.example/v1"
    finally:
        client.close()


def test_request_id_header_promoted_to_response_field(
    client: ClarisMD, httpx_mock
) -> None:
    """When the body lacks ``request_id`` we backfill from ``X-Request-ID``."""
    payload = _completion_payload()  # no request_id in payload
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        json=payload,
        headers={"X-Request-ID": "req_from_header"},
    )

    result = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )
    assert result.request_id == "req_from_header"


def test_timeout_handling_raises(client: ClarisMD, httpx_mock) -> None:
    """A timeout surfaces as APITimeoutError after retries."""
    from clarismd import APITimeoutError

    httpx_mock.add_exception(httpx.ReadTimeout("timed out"))
    httpx_mock.add_exception(httpx.ReadTimeout("timed out"))
    httpx_mock.add_exception(httpx.ReadTimeout("timed out"))

    with pytest.raises(APITimeoutError):
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
        )


def test_connection_error_raises(client: ClarisMD, httpx_mock) -> None:
    """Transport errors map to APIConnectionError after retries."""
    from clarismd import APIConnectionError

    httpx_mock.add_exception(httpx.ConnectError("conn refused"))
    httpx_mock.add_exception(httpx.ConnectError("conn refused"))
    httpx_mock.add_exception(httpx.ConnectError("conn refused"))

    with pytest.raises(APIConnectionError):
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
        )
