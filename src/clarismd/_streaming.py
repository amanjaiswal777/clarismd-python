# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Server-Sent-Events (SSE) parser for streaming chat completions.

The gateway emits OpenAI-shaped SSE on ``/v1/chat/completions`` when
``stream=true``: each chunk arrives as ``data: {...json...}\\n\\n`` and
the stream is terminated by ``data: [DONE]``. Mid-stream errors come
through as ``data: {"error": {...}}`` (the same envelope the non-stream
path uses) and we raise the appropriate :class:`APIError` subclass on
the consumer's next iteration.

Two parallel implementations live here so callers don't have to
shuttle between sync and async iterators by hand:

* :class:`Stream` — synchronous; iterate with a normal ``for``.
* :class:`AsyncStream` — asynchronous; iterate with ``async for``.

Both classes own the underlying :class:`httpx.Response` and close it
when iteration completes (or when used as a context manager).
"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import (
    Any,
    Generic,
    Optional,
    TypeVar,
    cast,
)

import httpx
from pydantic import BaseModel

from ._exceptions import _build_api_error

T = TypeVar("T", bound=BaseModel)

_DONE_PAYLOAD = "[DONE]"


def _parse_event_block(buffer: str) -> Optional[str]:
    """Pull the ``data:`` payload out of one complete SSE event block.

    SSE events are separated by a blank line (``\\n\\n``). Within a
    single event block, ``data:`` lines concatenate into the payload —
    OpenAI never multi-lines a chunk, but the spec allows it so we
    handle it. Other field names (``event:``, ``id:``, ``retry:``,
    ``:`` comments) are ignored.
    """
    payload_lines: list[str] = []
    for raw_line in buffer.split("\n"):
        line = raw_line.rstrip("\r")
        if not line or line.startswith(":"):
            continue
        if line.startswith("data:"):
            payload_lines.append(line[len("data:") :].lstrip(" "))
    if not payload_lines:
        return None
    return "\n".join(payload_lines)


def _decode_chunk(payload: str, cast_to: type[T]) -> Optional[T]:
    """Decode one ``data:`` payload, raising on mid-stream errors."""
    if payload == _DONE_PAYLOAD:
        return None
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError:
        # Skip malformed events rather than killing the whole stream;
        # the gateway never emits these intentionally.
        return None
    if isinstance(decoded, dict) and isinstance(decoded.get("error"), dict):
        # Mid-stream error envelope — surface as a typed exception so
        # the consumer's ``for`` loop terminates with the right class.
        raise _build_api_error(
            status_code=200,
            request_id=None,
            body=decoded,
        )
    return cast(Any, cast_to).model_validate(decoded)


class _StreamBase(Generic[T]):
    """Behavior shared between sync + async stream wrappers."""

    def __init__(self, response: httpx.Response, cast_to: type[T]) -> None:
        self._response = response
        self._cast_to = cast_to
        self._closed = False

    @property
    def response(self) -> httpx.Response:
        """The underlying httpx response (headers, status, request_id)."""
        return self._response

    def _flush_event(self, buffer: str) -> tuple[Optional[T], bool]:
        """Decode one buffered SSE event.

        Returns ``(chunk, terminated)``. ``chunk`` is ``None`` when the
        block was a comment / heartbeat / malformed. ``terminated`` is
        ``True`` when the block was the ``[DONE]`` sentinel and the
        iterator should stop.
        """
        payload = _parse_event_block(buffer)
        if payload is None:
            return None, False
        if payload == _DONE_PAYLOAD:
            return None, True
        return _decode_chunk(payload, self._cast_to), False


class Stream(_StreamBase[T]):
    """Synchronous iterator over decoded chat completion chunks."""

    def __iter__(self) -> Iterator[T]:
        return self._iter()

    def __enter__(self) -> Stream[T]:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._response.close()

    def _iter(self) -> Iterator[T]:
        buffer = ""
        try:
            for line in self._response.iter_lines():
                if line == "":
                    if buffer:
                        chunk, terminated = self._flush_event(buffer)
                        buffer = ""
                        if terminated:
                            return
                        if chunk is not None:
                            yield chunk
                    continue
                buffer += line + "\n"
            # Drain trailing partial event (server closed without final blank line).
            if buffer:
                chunk, terminated = self._flush_event(buffer)
                if terminated:
                    return
                if chunk is not None:
                    yield chunk
        finally:
            self.close()


class AsyncStream(_StreamBase[T]):
    """Asynchronous iterator over decoded chat completion chunks."""

    def __aiter__(self) -> AsyncIterator[T]:
        return self._aiter()

    async def __aenter__(self) -> AsyncStream[T]:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if not self._closed:
            self._closed = True
            await self._response.aclose()

    async def _aiter(self) -> AsyncIterator[T]:
        buffer = ""
        try:
            async for line in self._response.aiter_lines():
                if line == "":
                    if buffer:
                        chunk, terminated = self._flush_event(buffer)
                        buffer = ""
                        if terminated:
                            return
                        if chunk is not None:
                            yield chunk
                    continue
                buffer += line + "\n"
            if buffer:
                chunk, terminated = self._flush_event(buffer)
                if terminated:
                    return
                if chunk is not None:
                    yield chunk
        finally:
            await self.aclose()


__all__ = ["Stream", "AsyncStream"]
