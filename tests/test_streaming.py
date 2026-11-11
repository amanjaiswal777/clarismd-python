# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""SSE streaming — chunk parsing, [DONE] terminator, mid-stream errors."""
from __future__ import annotations

import json

import pytest

from clarismd import (
    ChatCompletionChunk,
    ClarisMD,
    InternalServerError,
    PHIPolicyViolationError,
    Stream,
)

from .conftest import BASE_URL

CHAT_URL = f"{BASE_URL}/chat/completions"


def _chunk_event(content: str, *, finish: str | None = None) -> bytes:
    payload = {
        "id": "chatcmpl-stream-1",
        "object": "chat.completion.chunk",
        "created": 1719000000,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "delta": {"content": content},
                "finish_reason": finish,
            }
        ],
    }
    return f"data: {json.dumps(payload)}\n\n".encode()


def _done_event() -> bytes:
    return b"data: [DONE]\n\n"


def _error_event(error_type: str, message: str) -> bytes:
    payload = {"error": {"type": error_type, "message": message}}
    return f"data: {json.dumps(payload)}\n\n".encode()


def test_stream_yields_chunks_and_terminates(client: ClarisMD, httpx_mock) -> None:
    """Three chunks + [DONE] -> three ChatCompletionChunk objects."""
    body = _chunk_event("Hello") + _chunk_event(", ") + _chunk_event("world!", finish="stop") + _done_event()
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        content=body,
        headers={"content-type": "text/event-stream"},
    )

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        stream=True,
    )
    assert isinstance(stream, Stream)

    chunks: list[ChatCompletionChunk] = list(stream)
    assert len(chunks) == 3
    assert chunks[0].choices[0].delta.content == "Hello"
    assert chunks[2].choices[0].finish_reason == "stop"


def test_stream_stops_at_done_even_with_trailing_bytes(
    client: ClarisMD, httpx_mock
) -> None:
    """Anything after ``data: [DONE]`` is ignored."""
    body = _chunk_event("ok") + _done_event() + _chunk_event("ignored")
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        content=body,
        headers={"content-type": "text/event-stream"},
    )

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        stream=True,
    )
    chunks = list(stream)
    assert [c.choices[0].delta.content for c in chunks] == ["ok"]


def test_stream_mid_stream_error_raises_typed_exception(
    client: ClarisMD, httpx_mock
) -> None:
    """A ``data: {"error": {...}}`` event raises the matching APIError class."""
    body = _chunk_event("first") + _error_event("phi_policy_violation", "PHI in stream.")
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        content=body,
        headers={"content-type": "text/event-stream"},
    )

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        stream=True,
    )
    with pytest.raises(PHIPolicyViolationError):
        for _ in stream:
            pass


def test_stream_mid_stream_internal_error_raises_internal(
    client: ClarisMD, httpx_mock
) -> None:
    """``internal_server_error`` mid-stream surfaces as InternalServerError."""
    body = _error_event("internal_server_error", "boom")
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        content=body,
        headers={"content-type": "text/event-stream"},
    )

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        stream=True,
    )
    with pytest.raises(InternalServerError):
        for _ in stream:
            pass


def test_stream_skips_comments_and_blank_lines(
    client: ClarisMD, httpx_mock
) -> None:
    """SSE comments (``: ping``) and stray blank lines must not break parsing."""
    body = (
        b": keepalive\n\n"
        + _chunk_event("a")
        + b": another comment\n\n"
        + _chunk_event("b")
        + _done_event()
    )
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        content=body,
        headers={"content-type": "text/event-stream"},
    )

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        stream=True,
    )
    chunks = list(stream)
    assert [c.choices[0].delta.content for c in chunks] == ["a", "b"]
