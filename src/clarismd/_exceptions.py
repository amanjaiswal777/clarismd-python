# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Exception hierarchy for the ClarisMD Python SDK.

Mirrors the closed-set ``error.type`` values defined in the v1 API
contract (see ``LAUNCH_PLAN/17-v1-api-contract.md``). The mapping is
intentionally one-to-one so callers can do ``except RateLimitError`` (for
example) without inspecting status codes.

Every API-derived exception carries the metadata the backend's error
envelope returns: ``status_code``, ``code``, ``message``, ``param``, and
``request_id``. The ``request_id`` is the most useful field for support
tickets and is always surfaced in ``str(exc)`` so it ends up in logs.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Optional


class ClarisMDError(Exception):
    """Base class for all errors raised by this SDK.

    Catching :class:`ClarisMDError` will catch every exception the SDK
    emits, both protocol-level (API responses) and transport-level
    (network failures, timeouts).
    """


class APIConnectionError(ClarisMDError):
    """The SDK could not reach the gateway.

    Wraps the underlying ``httpx`` transport error. Inspect ``__cause__``
    for the original exception.
    """

    def __init__(self, message: str = "Connection error.") -> None:
        super().__init__(message)
        self.message = message


class APITimeoutError(APIConnectionError):
    """A request exceeded the configured timeout.

    Subclass of :class:`APIConnectionError` so retry logic that catches
    connection failures also catches timeouts.
    """

    def __init__(self, message: str = "Request timed out.") -> None:
        super().__init__(message)


class APIError(ClarisMDError):
    """Base class for API-level errors (any non-2xx response).

    The full backend error envelope is preserved on the exception:

    .. code-block:: python

        try:
            client.chat.completions.create(...)
        except clarismd.RateLimitError as exc:
            print(exc.request_id, exc.message)
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        request_id: Optional[str] = None,
        code: Optional[str] = None,
        param: Optional[str] = None,
        type: Optional[str] = None,
        body: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.status_code: int = status_code
        self.request_id: Optional[str] = request_id
        self.code: Optional[str] = code
        self.param: Optional[str] = param
        self.type: Optional[str] = type
        self.body: Optional[Any] = body

    def __str__(self) -> str:
        parts: list[str] = []
        if self.status_code:
            parts.append(f"[{self.status_code}]")
        if self.code:
            parts.append(f"({self.code})")
        parts.append(self.message)
        if self.request_id:
            parts.append(f"[request_id={self.request_id}]")
        return " ".join(parts)


class AuthenticationError(APIError):
    """``error.type=authentication_error`` — HTTP 401."""


class PermissionDeniedError(APIError):
    """``error.type=permission_denied`` — HTTP 403."""


class NotFoundError(APIError):
    """``error.type=not_found`` — HTTP 404."""


class ConflictError(APIError):
    """``error.type=conflict`` — HTTP 409."""


class UnprocessableEntityError(APIError):
    """``error.type=unprocessable_entity`` — HTTP 422."""


class RateLimitError(APIError):
    """``error.type=rate_limit_exceeded`` — HTTP 429.

    Retried automatically by the SDK (with ``Retry-After`` honored) up to
    ``max_retries`` times before being raised.
    """


class PHIPolicyViolationError(APIError):
    """``error.type=phi_policy_violation`` — HTTP 400.

    Raised when the gateway's PHI policy blocks a request. Deterministic;
    never retried.
    """


class BudgetExceededError(APIError):
    """``error.type=budget_exceeded`` — HTTP 402.

    Reserved for the paid tier. Deterministic; never retried.
    """


class ProviderError(APIError):
    """``error.type=provider_error`` — HTTP 502 / 503.

    The upstream LLM provider failed. Retried automatically.
    """


class InternalServerError(APIError):
    """``error.type=internal_server_error`` — HTTP 500.

    Retried automatically.
    """


_TYPE_TO_CLASS: Dict[str, type[APIError]] = {
    "authentication_error": AuthenticationError,
    "permission_denied": PermissionDeniedError,
    "not_found": NotFoundError,
    "conflict": ConflictError,
    "unprocessable_entity": UnprocessableEntityError,
    "rate_limit_exceeded": RateLimitError,
    "phi_policy_violation": PHIPolicyViolationError,
    "budget_exceeded": BudgetExceededError,
    "provider_error": ProviderError,
    "internal_server_error": InternalServerError,
}


_STATUS_FALLBACK: Dict[int, type[APIError]] = {
    400: PHIPolicyViolationError,
    401: AuthenticationError,
    402: BudgetExceededError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
    500: InternalServerError,
    502: ProviderError,
    503: ProviderError,
}


def _build_api_error(
    *,
    status_code: int,
    request_id: Optional[str],
    body: Any,
) -> APIError:
    """Construct the right APIError subclass from a parsed response body.

    Selection order:
    1. ``body.error.type`` if present and in the closed set.
    2. ``status_code`` fallback for known HTTP codes.
    3. Generic :class:`APIError` for anything else (e.g. malformed body).
    """
    err_obj: Mapping[str, Any] = {}
    if isinstance(body, Mapping):
        candidate = body.get("error")
        if isinstance(candidate, Mapping):
            err_obj = candidate

    raw_type = err_obj.get("type")
    raw_code = err_obj.get("code")
    raw_param = err_obj.get("param")
    raw_message = err_obj.get("message")
    err_type: Optional[str] = raw_type if isinstance(raw_type, str) else None
    err_code: Optional[str] = raw_code if isinstance(raw_code, str) else None
    err_param: Optional[str] = raw_param if isinstance(raw_param, str) else None
    err_message: str = (
        raw_message
        if isinstance(raw_message, str)
        else f"HTTP {status_code} from ClarisMD gateway"
    )
    # Prefer request_id from envelope; fall back to the header copy.
    envelope_rid = err_obj.get("request_id")
    if isinstance(envelope_rid, str):
        request_id = envelope_rid

    cls: type[APIError]
    if err_type and err_type in _TYPE_TO_CLASS:
        cls = _TYPE_TO_CLASS[err_type]
    elif status_code in _STATUS_FALLBACK:
        cls = _STATUS_FALLBACK[status_code]
    else:
        cls = APIError

    return cls(
        err_message,
        status_code=status_code,
        request_id=request_id,
        code=err_code,
        param=err_param,
        type=err_type,
        body=body,
    )


__all__ = [
    "ClarisMDError",
    "APIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "PHIPolicyViolationError",
    "BudgetExceededError",
    "ProviderError",
    "InternalServerError",
    "APIConnectionError",
    "APITimeoutError",
]
