# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""``client.keys.{list,create,get,delete}`` against the gateway's real shapes."""
from __future__ import annotations

import json

import pytest

from clarismd import APIKey, ClarisMD

from ._shapes import KEY
from .conftest import BASE_URL


def test_keys_list_is_a_bare_array(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(method="GET", url=f"{BASE_URL}/keys", json=[KEY, {**KEY, "id": "k2"}])

    keys = client.keys.list()
    assert len(keys) == 2
    assert all(isinstance(k, APIKey) for k in keys)
    assert keys[0].key_prefix == "cmd_live_ab12"
    assert keys[0].key is None


def test_keys_create_returns_secret_once_in_key(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST", url=f"{BASE_URL}/keys", status_code=201,
        json={**KEY, "key": "cmd_live_ab12-fullsecret-do-not-leak"},
    )

    key = client.keys.create(name="ci", permissions=["chat"], expires_in_days=30)
    assert key.key == "cmd_live_ab12-fullsecret-do-not-leak"
    assert key.permissions == ["chat"]
    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {"name": "ci", "permissions": ["chat"], "expires_in_days": 30}


def test_keys_create_with_no_params_sends_empty_body(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(method="POST", url=f"{BASE_URL}/keys", status_code=201, json={**KEY, "key": "s"})
    client.keys.create()
    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {}


def test_keys_get_returns_metadata_without_secret(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(method="GET", url=f"{BASE_URL}/keys/{KEY['id']}", json={**KEY, "revoked": True})

    key = client.keys.get(KEY["id"])
    assert key.revoked is True
    assert key.key is None


def test_keys_unexpected_envelope_is_an_error_not_an_empty_list(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(method="GET", url=f"{BASE_URL}/keys", json={"data": [KEY]})
    with pytest.raises(ValueError, match="Unexpected key list"):
        client.keys.list()


def test_keys_create_rejects_old_scopes_kwarg(client: ClarisMD) -> None:
    with pytest.raises(TypeError):
        client.keys.create(name="x", scopes=["read"])  # type: ignore[call-arg]


def test_keys_delete(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(method="DELETE", url=f"{BASE_URL}/keys/{KEY['id']}", status_code=204)
    assert client.keys.delete(KEY["id"]) is None
