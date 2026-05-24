# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Closed-set error mapping — one test per ``error.type`` value."""
from __future__ import annotations

import pytest

from clarismd import (
    APIError,
    AuthenticationError,
    BudgetExceededError,
    ClarisMD,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    PHIPolicyViolationError,
    ProviderError,
    RateLimitError,
    UnprocessableEntityError,
)

from .conftest import BASE_URL

CHAT_URL = f"{BASE_URL}/chat/completions"


def _error_envelope(type_: str, message: str = "boom") -> dict:
    return {
        "error": {
            "type": type_,
            "code": f"{type_}_code",
            "message": message,
            "param": "messages[0]",
            "request_id": f"req_{type_}",
        }
    }


# (error.type, status_code, expected_class) — one row per closed-set value.
ERROR_MATRIX: list[tuple[str, int, type[APIError]]] = [
    ("authentication_error", 401, AuthenticationError),
    ("permission_denied", 403, PermissionDeniedError),
    ("not_found", 404, NotFoundError),
    ("conflict", 409, ConflictError),
    ("unprocessable_entity", 422, UnprocessableEntityError),
    ("rate_limit_exceeded", 429, RateLimitError),
    ("phi_policy_violation", 400, PHIPolicyViolationError),
    ("budget_exceeded", 402, BudgetExceededError),
    ("provider_error", 502, ProviderError),
    ("internal_server_error", 500, InternalServerError),
]


@pytest.mark.parametrize("error_type,status,expected_class", ERROR_MATRIX)
def test_error_type_maps_to_class(
    client: ClarisMD,
    httpx_mock,
    error_type: str,
    status: int,
    expected_class: type[APIError],
) -> None:
    """Every closed-set error.type maps to its matching subclass."""
    # For retryable statuses we have to schedule enough responses to cover
    # the retry budget — otherwise pytest-httpx blocks the second attempt.
    if status in {429, 500, 502, 503, 504}:
        for _ in range(3):  # 1 initial + 2 retries
            httpx_mock.add_response(
                method="POST",
                url=CHAT_URL,
                status_code=status,
                json=_error_envelope(error_type),
            )
    else:
        httpx_mock.add_response(
            method="POST",
            url=CHAT_URL,
            status_code=status,
            json=_error_envelope(error_type),
        )

    with pytest.raises(expected_class) as exc_info:
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
        )

    err = exc_info.value
    assert err.status_code == status
    assert err.code == f"{error_type}_code"
    assert err.message == "boom"
    assert err.param == "messages[0]"
    assert err.request_id == f"req_{error_type}"
    assert err.type == error_type


def test_error_str_includes_status_code_and_request_id(
    client: ClarisMD, httpx_mock
) -> None:
    """``str(exc)`` must surface the metadata humans need for support tickets."""
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=404,
        json=_error_envelope("not_found", "no such model"),
    )

    with pytest.raises(NotFoundError) as exc_info:
        client.chat.completions.create(
            model="ghost",
            messages=[{"role": "user", "content": "Hi"}],
        )

    text = str(exc_info.value)
    assert "[404]" in text
    assert "request_id=req_not_found" in text
    assert "no such model" in text


def test_unknown_error_type_falls_back_to_status_code(
    client: ClarisMD, httpx_mock
) -> None:
    """Unknown ``error.type`` is recovered via HTTP status mapping."""
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=403,
        json={"error": {"type": "novel_unknown_type", "message": "denied"}},
    )

    with pytest.raises(PermissionDeniedError):
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
        )


def test_malformed_error_body_still_raises_apierror(
    client: ClarisMD, httpx_mock
) -> None:
    """Non-JSON / unparseable error responses still raise an APIError subclass."""
    httpx_mock.add_response(
        method="POST",
        url=CHAT_URL,
        status_code=418,
        content=b"<html>internal proxy error</html>",
        headers={"content-type": "text/html"},
    )

    with pytest.raises(APIError) as exc_info:
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
        )

    assert exc_info.value.status_code == 418
