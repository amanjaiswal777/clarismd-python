# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.keys.{list,create,get,delete}``."""
from __future__ import annotations

from clarismd import APIKey, ClarisMD

from .conftest import BASE_URL


def test_keys_list(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/keys",
        json={
            "data": [
                {
                    "id": "key_1",
                    "name": "prod",
                    "prefix": "cmd-abc",
                    "scopes": ["chat:write"],
                },
                {
                    "id": "key_2",
                    "name": "staging",
                    "prefix": "cmd-def",
                    "scopes": ["chat:read"],
                },
            ]
        },
    )

    keys = client.keys.list()
    assert len(keys) == 2
    assert all(isinstance(k, APIKey) for k in keys)
    assert keys[0].name == "prod"


def test_keys_create_returns_secret_once(client: ClarisMD, httpx_mock) -> None:
    """The ``secret`` field is populated only on the create response."""
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/keys",
        json={
            "data": {
                "id": "key_99",
                "name": "ci-bot",
                "prefix": "cmd-xyz",
                "secret": "cmd-xyz-fullsecret-do-not-leak",
                "scopes": ["chat:write"],
            }
        },
    )

    key = client.keys.create(name="ci-bot", scopes=["chat:write"])
    assert key.id == "key_99"
    assert key.secret == "cmd-xyz-fullsecret-do-not-leak"


def test_keys_get_no_secret(client: ClarisMD, httpx_mock) -> None:
    """``keys.get`` returns metadata only — secret is never replayed."""
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/keys/key_99",
        json={
            "data": {
                "id": "key_99",
                "name": "ci-bot",
                "prefix": "cmd-xyz",
                "scopes": ["chat:write"],
            }
        },
    )

    key = client.keys.get("key_99")
    assert key.secret is None


def test_keys_delete_returns_none(client: ClarisMD, httpx_mock) -> None:
    """A 204 response is treated as success and produces ``None``."""
    httpx_mock.add_response(
        method="DELETE", url=f"{BASE_URL}/keys/key_99", status_code=204
    )

    result = client.keys.delete("key_99")
    assert result is None
