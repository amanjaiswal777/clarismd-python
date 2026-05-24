# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Sync + async base clients for the ClarisMD Python SDK.

This module is the brains of the SDK:

* request lifecycle (header injection, JSON encode/decode, retry,
  idempotency-key generation),
* error envelope unpacking → typed exceptions,
* base URL / timeout / max_retries plumbing,
* the public ``ClarisMD`` and ``AsyncClarisMD`` entry points that
  resource modules attach to.

Everything that talks to the network goes through ``_BaseClient._request``
(or its async sibling). Resources never call ``httpx`` directly — they
hand a method, path, and JSON body to the base client and get back a
parsed response.
"""
from __future__ import annotations

import json
import os
import random
import time
import uuid
from collections.abc import Awaitable, Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Optional,
    TypeVar,
    Union,
    cast,
)

import httpx

from ._exceptions import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    _build_api_error,
)
from ._streaming import AsyncStream, Stream  # noqa: F401  (re-exported)
from ._version import __version__

if TYPE_CHECKING:  # pragma: no cover - type-only
    from .resources.audit import AsyncAuditResource, AuditResource
    from .resources.chat import AsyncChatResource, ChatResource
    from .resources.completions import (
        AsyncCompletionsResource,
        CompletionsResource,
    )
    from .resources.compliance import (
        AsyncComplianceResource,
        ComplianceResource,
    )
    from .resources.embeddings import (
        AsyncEmbeddingsResource,
        EmbeddingsResource,
    )
    from .resources.health import AsyncHealthResource, HealthResource
    from .resources.keys import AsyncKeysResource, KeysResource
    from .resources.moderations import (
        AsyncModerationsResource,
        ModerationsResource,
    )
    from .resources.phi import AsyncPHIResource, PHIResource


DEFAULT_BASE_URL = "https://api.clarismd.com/v1"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2
USER_AGENT = f"clarismd-python/{__version__}"

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_RETRY_BACKOFF_SECONDS: tuple[float, ...] = (0.5, 1.0, 2.0)
_RETRY_AFTER_CAP_SECONDS = 60.0

# Sentinel for "do not auto-generate an Idempotency-Key on this POST".
# Callers pass ``clarismd_idempotency_key=False``; the resource layer
# forwards that intent to the base client.
_IDEMPOTENCY_DISABLED = False

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_base_url(base_url: Optional[str]) -> str:
    raw = base_url or os.environ.get("CLARISMD_BASE_URL") or DEFAULT_BASE_URL
    return raw.rstrip("/")


def _resolve_api_key(api_key: Optional[str]) -> Optional[str]:
    return api_key if api_key is not None else os.environ.get("CLARISMD_API_KEY")


def _parse_retry_after(value: str) -> Optional[float]:
    """Parse ``Retry-After`` (seconds-only; HTTP-date is ignored).

    The gateway emits an integer-seconds value in line with
    ``LAUNCH_PLAN/17-v1-api-contract.md``. If the header ever carries an
    HTTP-date we just ignore it and fall back to exponential backoff —
    the SDK's retry behavior must remain bounded.
    """
    try:
        secs = float(value)
    except (TypeError, ValueError):
        return None
    if secs < 0:
        return None
    return min(secs, _RETRY_AFTER_CAP_SECONDS)


def _retry_delay(attempt: int, retry_after: Optional[str]) -> float:
    """Compute the sleep time before the next retry.

    Honors ``Retry-After`` when present; otherwise uses
    ``0.5s, 1s, 2s`` exponential backoff with up to 25% jitter to spread
    a thundering herd that hits a 5xx burst.
    """
    if retry_after is not None:
        parsed = _parse_retry_after(retry_after)
        if parsed is not None:
            return parsed
    base = (
        _RETRY_BACKOFF_SECONDS[attempt]
        if attempt < len(_RETRY_BACKOFF_SECONDS)
        else _RETRY_BACKOFF_SECONDS[-1]
    )
    jitter = base * 0.25 * random.random()
    return base + jitter


def _generate_idempotency_key() -> str:
    return f"cmd-py-{uuid.uuid4()}"


def _coerce_body(raw: bytes, content_type: Optional[str]) -> Any:
    if not raw:
        return None
    if content_type and "application/json" in content_type:
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def _strip_idempotency(headers: Optional[Mapping[str, str]]) -> Dict[str, str]:
    if not headers:
        return {}
    return {k: v for k, v in headers.items() if k.lower() != "idempotency-key"}


# ---------------------------------------------------------------------------
# Request options
# ---------------------------------------------------------------------------


class _RequestOptions:
    """Per-call overrides forwarded from resources into the base client.

    Resource methods accept a small handful of `clarismd_*` kwargs that
    don't go on the wire as JSON — they reshape the HTTP request itself
    (idempotency, headers, timeout). This struct keeps the wire body
    cleanly separated from those overrides.
    """

    __slots__ = ("idempotency_key", "extra_headers", "timeout")

    def __init__(
        self,
        *,
        idempotency_key: Union[str, None, bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.idempotency_key = idempotency_key
        self.extra_headers = dict(extra_headers) if extra_headers else None
        self.timeout = timeout


# ---------------------------------------------------------------------------
# Base client
# ---------------------------------------------------------------------------


class _BaseClient:
    """Shared state + helpers for the sync and async client classes."""

    def __init__(
        self,
        *,
        api_key: Optional[str],
        base_url: Optional[str],
        timeout: float,
        max_retries: int,
        default_headers: Optional[Mapping[str, str]],
    ) -> None:
        self.api_key = _resolve_api_key(api_key)
        self.base_url = _resolve_base_url(base_url)
        self.timeout = timeout
        self.max_retries = max(0, int(max_retries))
        self._default_headers: Dict[str, str] = dict(default_headers or {})

    # -- header construction -------------------------------------------------

    def _build_headers(
        self,
        *,
        method: str,
        extra: Optional[Mapping[str, str]],
        idempotency_key: Union[str, None, bool],
    ) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "X-ClarisMD-Client": f"python/{__version__}",
        }
        headers.update(self._default_headers)
        if extra:
            headers.update(_strip_idempotency(extra) if idempotency_key is False else dict(extra))
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if method.upper() == "POST":
            self._maybe_attach_idempotency(headers, idempotency_key)
        return headers

    def _maybe_attach_idempotency(
        self,
        headers: Dict[str, str],
        idempotency_key: Union[str, None, bool],
    ) -> None:
        if idempotency_key is _IDEMPOTENCY_DISABLED:
            headers.pop("Idempotency-Key", None)
            return
        if isinstance(idempotency_key, str):
            headers["Idempotency-Key"] = idempotency_key
            return
        # idempotency_key is None — caller did not specify; auto-generate
        # only if the caller hasn't already supplied one via extra_headers.
        if "Idempotency-Key" not in headers:
            headers["Idempotency-Key"] = _generate_idempotency_key()

    def _full_url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def _is_retryable_status(self, status: int) -> bool:
        return status in _RETRYABLE_STATUS

    def _request_id(self, response: httpx.Response) -> Optional[str]:
        return response.headers.get("x-request-id") or response.headers.get("X-Request-ID")


# ---------------------------------------------------------------------------
# Sync client
# ---------------------------------------------------------------------------


class ClarisMD(_BaseClient):
    """Synchronous client for the ClarisMD gateway.

    .. code-block:: python

        from clarismd import ClarisMD

        client = ClarisMD(api_key="cmd-...")
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
        )
        print(resp.choices[0].message.content)

    The client owns an ``httpx.Client`` for connection pooling. Use it as
    a context manager (``with ClarisMD(...) as client:``) or call
    :meth:`close` explicitly to release sockets.
    """

    chat: ChatResource
    completions: CompletionsResource
    embeddings: EmbeddingsResource
    moderations: ModerationsResource
    phi: PHIResource
    audit: AuditResource
    compliance: ComplianceResource
    keys: KeysResource
    health: HealthResource

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self._owns_client = http_client is None
        self._http: httpx.Client = http_client or httpx.Client(timeout=timeout)
        self._sleep: Callable[[float], None] = time.sleep

        # Lazy import keeps ``_client.py`` free of resource cycles.
        from .resources.audit import AuditResource
        from .resources.chat import ChatResource
        from .resources.completions import CompletionsResource
        from .resources.compliance import ComplianceResource
        from .resources.embeddings import EmbeddingsResource
        from .resources.health import HealthResource
        from .resources.keys import KeysResource
        from .resources.moderations import ModerationsResource
        from .resources.phi import PHIResource

        self.chat = ChatResource(self)
        self.completions = CompletionsResource(self)
        self.embeddings = EmbeddingsResource(self)
        self.moderations = ModerationsResource(self)
        self.phi = PHIResource(self)
        self.audit = AuditResource(self)
        self.compliance = ComplianceResource(self)
        self.keys = KeysResource(self)
        self.health = HealthResource(self)

    # -- context manager ----------------------------------------------------

    def __enter__(self) -> ClarisMD:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client.

        No-op when the SDK was constructed with a caller-provided
        ``http_client``; that lifecycle belongs to the caller.
        """
        if self._owns_client:
            self._http.close()

    # -- request --------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Any] = None,
        params: Optional[Mapping[str, Any]] = None,
        options: Optional[_RequestOptions] = None,
        stream: bool = False,
        cast_to: Optional[type[T]] = None,
    ) -> Any:
        """Issue a single HTTP request with retry + error mapping.

        ``stream=True`` returns the live :class:`httpx.Response` so the
        caller (the chat resource) can hand it to :class:`Stream`. Every
        other path returns either a parsed ``cast_to`` model, a
        ``dict``, or raw ``bytes`` for binary downloads.
        """
        opts = options or _RequestOptions()
        url = self._full_url(path)
        attempt = 0
        last_exc: Optional[Exception] = None

        while True:
            headers = self._build_headers(
                method=method,
                extra=opts.extra_headers,
                idempotency_key=opts.idempotency_key,
            )
            timeout = opts.timeout if opts.timeout is not None else self.timeout
            try:
                response = self._http.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=json_body,
                    params=dict(params) if params else None,
                    timeout=timeout,
                )
            except httpx.TimeoutException as exc:
                last_exc = APITimeoutError(str(exc) or "Request timed out.")
                if attempt < self.max_retries:
                    self._sleep(_retry_delay(attempt, None))
                    attempt += 1
                    continue
                raise last_exc from exc
            except httpx.HTTPError as exc:
                last_exc = APIConnectionError(str(exc) or "Connection error.")
                if attempt < self.max_retries:
                    self._sleep(_retry_delay(attempt, None))
                    attempt += 1
                    continue
                raise last_exc from exc

            if 200 <= response.status_code < 300:
                if stream:
                    return response
                return self._decode_success(response, cast_to=cast_to)

            if self._is_retryable_status(response.status_code) and attempt < self.max_retries:
                # Drain non-streaming responses so the connection returns
                # to the pool before we sleep.
                response.close()
                self._sleep(_retry_delay(attempt, response.headers.get("Retry-After")))
                attempt += 1
                continue

            # Non-retryable or budget exhausted — convert to a typed error.
            raise self._error_from_response(response)

    def _decode_success(
        self,
        response: httpx.Response,
        *,
        cast_to: Optional[type[T]],
    ) -> Any:
        body = _coerce_body(response.content, response.headers.get("content-type"))
        request_id = self._request_id(response)
        if cast_to is None:
            if body is None:
                return response.content if response.content else None
            if isinstance(body, dict) and request_id and "request_id" not in body:
                body = {**body, "request_id": request_id}
            return body
        if not isinstance(body, dict):
            raise APIError(
                "Expected JSON object response.",
                status_code=response.status_code,
                request_id=request_id,
                body=body,
            )
        if request_id and "request_id" not in body:
            body = {**body, "request_id": request_id}
        # ``cast_to`` is always a Pydantic BaseModel subclass for typed responses.
        return cast(Any, cast_to).model_validate(body)

    def _error_from_response(self, response: httpx.Response) -> APIError:
        body = _coerce_body(response.content, response.headers.get("content-type"))
        request_id = self._request_id(response)
        return _build_api_error(
            status_code=response.status_code,
            request_id=request_id,
            body=body,
        )


# ---------------------------------------------------------------------------
# Async client
# ---------------------------------------------------------------------------


class AsyncClarisMD(_BaseClient):
    """Asynchronous client mirroring :class:`ClarisMD`.

    Use as ``async with AsyncClarisMD(...) as client:`` for proper socket
    cleanup. All resource methods return awaitables; streaming returns an
    :class:`AsyncStream` you can ``async for`` over.
    """

    chat: AsyncChatResource
    completions: AsyncCompletionsResource
    embeddings: AsyncEmbeddingsResource
    moderations: AsyncModerationsResource
    phi: AsyncPHIResource
    audit: AsyncAuditResource
    compliance: AsyncComplianceResource
    keys: AsyncKeysResource
    health: AsyncHealthResource

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self._owns_client = http_client is None
        self._http: httpx.AsyncClient = http_client or httpx.AsyncClient(timeout=timeout)
        # Decoupled so tests can inject a synchronous sleep substitute.
        import asyncio

        self._sleep: Callable[[float], Awaitable[None]] = asyncio.sleep

        from .resources.audit import AsyncAuditResource
        from .resources.chat import AsyncChatResource
        from .resources.completions import AsyncCompletionsResource
        from .resources.compliance import AsyncComplianceResource
        from .resources.embeddings import AsyncEmbeddingsResource
        from .resources.health import AsyncHealthResource
        from .resources.keys import AsyncKeysResource
        from .resources.moderations import AsyncModerationsResource
        from .resources.phi import AsyncPHIResource

        self.chat = AsyncChatResource(self)
        self.completions = AsyncCompletionsResource(self)
        self.embeddings = AsyncEmbeddingsResource(self)
        self.moderations = AsyncModerationsResource(self)
        self.phi = AsyncPHIResource(self)
        self.audit = AsyncAuditResource(self)
        self.compliance = AsyncComplianceResource(self)
        self.keys = AsyncKeysResource(self)
        self.health = AsyncHealthResource(self)

    async def __aenter__(self) -> AsyncClarisMD:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Any] = None,
        params: Optional[Mapping[str, Any]] = None,
        options: Optional[_RequestOptions] = None,
        stream: bool = False,
        cast_to: Optional[type[T]] = None,
    ) -> Any:
        opts = options or _RequestOptions()
        url = self._full_url(path)
        attempt = 0
        last_exc: Optional[Exception] = None

        while True:
            headers = self._build_headers(
                method=method,
                extra=opts.extra_headers,
                idempotency_key=opts.idempotency_key,
            )
            timeout = opts.timeout if opts.timeout is not None else self.timeout
            try:
                response = await self._http.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=json_body,
                    params=dict(params) if params else None,
                    timeout=timeout,
                )
            except httpx.TimeoutException as exc:
                last_exc = APITimeoutError(str(exc) or "Request timed out.")
                if attempt < self.max_retries:
                    await self._sleep(_retry_delay(attempt, None))
                    attempt += 1
                    continue
                raise last_exc from exc
            except httpx.HTTPError as exc:
                last_exc = APIConnectionError(str(exc) or "Connection error.")
                if attempt < self.max_retries:
                    await self._sleep(_retry_delay(attempt, None))
                    attempt += 1
                    continue
                raise last_exc from exc

            if 200 <= response.status_code < 300:
                if stream:
                    return response
                return self._decode_success(response, cast_to=cast_to)

            if self._is_retryable_status(response.status_code) and attempt < self.max_retries:
                await response.aclose()
                await self._sleep(_retry_delay(attempt, response.headers.get("Retry-After")))
                attempt += 1
                continue

            raise self._error_from_response(response)

    def _decode_success(
        self,
        response: httpx.Response,
        *,
        cast_to: Optional[type[T]],
    ) -> Any:
        body = _coerce_body(response.content, response.headers.get("content-type"))
        request_id = self._request_id(response)
        if cast_to is None:
            if body is None:
                return response.content if response.content else None
            if isinstance(body, dict) and request_id and "request_id" not in body:
                body = {**body, "request_id": request_id}
            return body
        if not isinstance(body, dict):
            raise APIError(
                "Expected JSON object response.",
                status_code=response.status_code,
                request_id=request_id,
                body=body,
            )
        if request_id and "request_id" not in body:
            body = {**body, "request_id": request_id}
        return cast(Any, cast_to).model_validate(body)

    def _error_from_response(self, response: httpx.Response) -> APIError:
        body = _coerce_body(response.content, response.headers.get("content-type"))
        request_id = self._request_id(response)
        return _build_api_error(
            status_code=response.status_code,
            request_id=request_id,
            body=body,
        )


__all__ = [
    "ClarisMD",
    "AsyncClarisMD",
    "Stream",
    "AsyncStream",
    "_RequestOptions",
    "_IDEMPOTENCY_DISABLED",
    "DEFAULT_BASE_URL",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
]
