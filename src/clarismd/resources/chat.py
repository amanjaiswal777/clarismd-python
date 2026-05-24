# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.chat.completions.create(...)`` — OpenAI-shaped chat surface.

Maps to ``POST /v1/chat/completions`` on the gateway. When ``stream=True``
the gateway emits SSE; we wrap the live response in :class:`Stream` /
:class:`AsyncStream` so callers iterate ``ChatCompletionChunk`` objects
directly.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Union,
    overload,
)

from .._streaming import AsyncStream, Stream
from .._types import ChatCompletion, ChatCompletionChunk, PHIAction
from ._base import _AsyncResource, _options, _SyncResource


def _build_body(
    *,
    model: str,
    messages: List[Dict[str, Any]],
    stream: bool,
    extra: Dict[str, Any],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"model": model, "messages": messages, "stream": stream}
    body.update({k: v for k, v in extra.items() if v is not None})
    return body


class ChatCompletionsResource(_SyncResource):
    @overload
    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        stream: Literal[False] = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        clarismd_policy: Optional[str] = None,
        clarismd_phi_action: Optional[PHIAction] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> ChatCompletion: ...

    @overload
    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        stream: Literal[True],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        clarismd_policy: Optional[str] = None,
        clarismd_phi_action: Optional[PHIAction] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Stream[ChatCompletionChunk]: ...

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        clarismd_policy: Optional[str] = None,
        clarismd_phi_action: Optional[PHIAction] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Union[ChatCompletion, Stream[ChatCompletionChunk]]:
        """Create a chat completion. ``stream=True`` returns a :class:`Stream`."""
        extra: Dict[str, Any] = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "n": n,
            "stop": stop,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "logit_bias": logit_bias,
            "user": user,
            "metadata": metadata,
        }
        body = _build_body(model=model, messages=messages, stream=stream, extra=extra)
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=clarismd_policy,
            phi_action=clarismd_phi_action,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        if stream:
            response = self._client.request(
                "POST",
                "/chat/completions",
                json_body=body,
                options=opts,
                stream=True,
            )
            return Stream(response, ChatCompletionChunk)
        return self._client.request(
            "POST",
            "/chat/completions",
            json_body=body,
            options=opts,
            cast_to=ChatCompletion,
        )


class ChatResource(_SyncResource):
    """``client.chat`` namespace; only ``completions`` for now."""

    completions: ChatCompletionsResource

    def __init__(self, client: Any) -> None:
        super().__init__(client)
        self.completions = ChatCompletionsResource(client)


class AsyncChatCompletionsResource(_AsyncResource):
    @overload
    async def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        stream: Literal[False] = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        clarismd_policy: Optional[str] = None,
        clarismd_phi_action: Optional[PHIAction] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> ChatCompletion: ...

    @overload
    async def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        stream: Literal[True],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        clarismd_policy: Optional[str] = None,
        clarismd_phi_action: Optional[PHIAction] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> AsyncStream[ChatCompletionChunk]: ...

    async def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        clarismd_policy: Optional[str] = None,
        clarismd_phi_action: Optional[PHIAction] = None,
        clarismd_idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Union[ChatCompletion, AsyncStream[ChatCompletionChunk]]:
        extra: Dict[str, Any] = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "n": n,
            "stop": stop,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "logit_bias": logit_bias,
            "user": user,
            "metadata": metadata,
        }
        body = _build_body(model=model, messages=messages, stream=stream, extra=extra)
        opts = _options(
            idempotency=clarismd_idempotency_key,
            policy=clarismd_policy,
            phi_action=clarismd_phi_action,
            extra_headers=extra_headers,
            timeout=timeout,
        )
        if stream:
            response = await self._client.request(
                "POST",
                "/chat/completions",
                json_body=body,
                options=opts,
                stream=True,
            )
            return AsyncStream(response, ChatCompletionChunk)
        return await self._client.request(
            "POST",
            "/chat/completions",
            json_body=body,
            options=opts,
            cast_to=ChatCompletion,
        )


class AsyncChatResource(_AsyncResource):
    completions: AsyncChatCompletionsResource

    def __init__(self, client: Any) -> None:
        super().__init__(client)
        self.completions = AsyncChatCompletionsResource(client)


__all__ = [
    "ChatResource",
    "ChatCompletionsResource",
    "AsyncChatResource",
    "AsyncChatCompletionsResource",
]
