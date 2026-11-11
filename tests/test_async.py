# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Async client coverage — basic chat, streaming, error mapping."""
from __future__ import annotations

import pytest

from clarismd import (
    AsyncClarisMD,
    AsyncStream,
    ChatCompletion,
    ChatCompletionChunk,
    PHIPolicyViolationError,
    RateLimitError,
)

from .conftest import BASE_URL

CHAT_URL = f"{BASE_URL}/chat/completions"


def _ok() -> dict:
    return {
        "id": "chatcmpl-async-1",
        "object": "chat.completion",
        "created": 1719000000,
        "model": "gpt-4o-mini",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
    }


@pytest.mark.asyncio
async def test_async_chat_basic(async_client: AsyncClarisMD, httpx_mock) -> None:
    """Async path round-trips the same as the sync path."""
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_ok())

    result = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )
    assert isinstance(result, ChatCompletion)
    assert result.choices[0].message.content == "hi"


@pytest.mark.asyncio
async def test_async_streaming(async_client: AsyncClarisMD, httpx_mock) -> None:
    """Async streaming yields decoded chunks and stops on [DONE]."""
    body = (
        b'data: {"id":"c1","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{"content":"a"}}]}\n\n'
        b'data: {"id":"c1","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{"content":"b"}}]}\n\n'
        b"data: [DONE]\n\n"
    )
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        content=body,
        headers={"content-type": "text/event-stream"},
    )

    stream = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        stream=True,
    )
    assert isinstance(stream, AsyncStream)

    parts: list[ChatCompletionChunk] = []
    async for chunk in stream:
        parts.append(chunk)
    assert [p.choices[0].delta.content for p in parts] == ["a", "b"]


@pytest.mark.asyncio
async def test_async_error_mapping(async_client: AsyncClarisMD, httpx_mock) -> None:
    """Async error mapping mirrors the sync side."""
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=400,
        json={"error": {"type": "phi_policy_violation", "message": "PHI"}},
    )

    with pytest.raises(PHIPolicyViolationError):
        await async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "patient name"}],
        )


@pytest.mark.asyncio
async def test_async_retries_on_429(
    async_client: AsyncClarisMD, httpx_mock
) -> None:
    """429 → 200 is retried transparently (async)."""
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=429,
        json={"error": {"type": "rate_limit_exceeded", "message": "slow"}},
    )
    httpx_mock.add_response(method="POST", url=CHAT_URL, json=_ok())

    result = await async_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )
    assert result.id == "chatcmpl-async-1"


@pytest.mark.asyncio
async def test_async_rate_limit_after_max_retries(
    async_client: AsyncClarisMD, httpx_mock
) -> None:
    """Persistent 429 surfaces as RateLimitError after the budget is spent."""
    for _ in range(3):
        httpx_mock.add_response(
            method="POST",
            url=CHAT_URL,
            status_code=429,
            json={"error": {"type": "rate_limit_exceeded", "message": "slow"}},
        )

    with pytest.raises(RateLimitError):
        await async_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
        )


@pytest.mark.asyncio
async def test_async_phi_scan(async_client: AsyncClarisMD, httpx_mock) -> None:
    """Async PHI scan returns the same typed result as sync."""
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/phi/scan",
        json={"detected": True, "entities": [{"type": "EMAIL", "text": "a@b.test"}]},
    )

    result = await async_client.phi.scan("contact a@b.test")
    assert result.detected is True
    assert result.entities[0].type == "EMAIL"


@pytest.mark.asyncio
async def test_async_close_is_idempotent() -> None:
    """``aclose()`` may be called multiple times safely."""
    client = AsyncClarisMD(api_key="cmd-x", base_url=BASE_URL)
    await client.aclose()
    # Second close — must not raise.
    await client.aclose()
