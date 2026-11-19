# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Coverage for the smaller resource modules — completions, embeddings,
moderations — and async paths of audit / keys / compliance."""
from __future__ import annotations

import json

import pytest

from clarismd import (
    AsyncClarisMD,
    ClarisMD,
    EmbeddingResponse,
    ModerationResponse,
    TextCompletion,
)

from . import _shapes as shapes
from .conftest import BASE_URL

# ---------------------------------------------------------------------------
# completions
# ---------------------------------------------------------------------------


def test_legacy_completions(client: ClarisMD, httpx_mock) -> None:
    """``client.completions.create`` returns a TextCompletion."""
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/completions",
        json={
            "id": "cmpl-1",
            "object": "text_completion",
            "created": 1719000000,
            "model": "gpt-3.5-turbo-instruct",
            "choices": [{"index": 0, "text": "hello"}],
        },
    )

    result = client.completions.create(model="gpt-3.5-turbo-instruct", prompt="hi")
    assert isinstance(result, TextCompletion)
    assert result.choices[0].text == "hello"


@pytest.mark.asyncio
async def test_legacy_completions_async(
    async_client: AsyncClarisMD, httpx_mock
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/completions",
        json={
            "id": "cmpl-1",
            "object": "text_completion",
            "created": 1,
            "model": "m",
            "choices": [{"index": 0, "text": "ok"}],
        },
    )

    result = await async_client.completions.create(model="m", prompt="hi")
    assert result.choices[0].text == "ok"


def test_legacy_completions_send_governance_headers(client: ClarisMD, httpx_mock) -> None:
    """``clarismd_policy`` / ``clarismd_phi_action`` reach the gateway on completions."""
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/completions",
        json={"id": "c", "object": "text_completion", "created": 1, "model": "m",
              "choices": [{"index": 0, "text": "ok"}]},
    )
    client.completions.create(
        model="m", prompt="hi", clarismd_phi_action="block",
        clarismd_policy="0b6f6a3e-5a1d-4c55-9a7e-6f0f3f1c2d4b",
    )
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["X-ClarisMD-PHI-Action"] == "block"
    assert request.headers["X-ClarisMD-Policy"] == "0b6f6a3e-5a1d-4c55-9a7e-6f0f3f1c2d4b"


@pytest.mark.parametrize("kwarg", ["clarismd_policy", "clarismd_phi_action"])
def test_embeddings_reject_governance_kwargs(client: ClarisMD, kwarg: str) -> None:
    """The gateway does not PHI-scan embeddings, so the options are not offered there."""
    with pytest.raises(TypeError):
        client.embeddings.create(model="m", input="x", **{kwarg: "block"})


@pytest.mark.parametrize("kwarg", ["clarismd_policy", "clarismd_phi_action"])
async def test_embeddings_reject_governance_kwargs_async(
    async_client: AsyncClarisMD, kwarg: str
) -> None:
    with pytest.raises(TypeError):
        await async_client.embeddings.create(model="m", input="x", **{kwarg: "block"})


# ---------------------------------------------------------------------------
# embeddings
# ---------------------------------------------------------------------------


def test_embeddings(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/embeddings",
        json={
            "object": "list",
            "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
            "model": "text-embedding-3-small",
        },
    )

    result = client.embeddings.create(
        model="text-embedding-3-small", input="hello world"
    )
    assert isinstance(result, EmbeddingResponse)
    assert result.data[0].embedding == [0.1, 0.2]


def test_embeddings_batch_input(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/embeddings",
        json={
            "object": "list",
            "data": [
                {"object": "embedding", "index": 0, "embedding": [0.1]},
                {"object": "embedding", "index": 1, "embedding": [0.2]},
            ],
            "model": "m",
        },
    )

    result = client.embeddings.create(model="m", input=["a", "b"], user="user-1")
    assert len(result.data) == 2

    request = httpx_mock.get_request()
    assert request is not None
    body = json.loads(request.content)
    assert body == {"model": "m", "input": ["a", "b"], "user": "user-1"}


@pytest.mark.asyncio
async def test_embeddings_async(
    async_client: AsyncClarisMD, httpx_mock
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/embeddings",
        json={
            "object": "list",
            "data": [{"object": "embedding", "index": 0, "embedding": [1.0]}],
            "model": "m",
        },
    )

    result = await async_client.embeddings.create(model="m", input="x")
    assert result.data[0].embedding == [1.0]


# ---------------------------------------------------------------------------
# moderations
# ---------------------------------------------------------------------------


def test_moderations(client: ClarisMD, httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/moderations",
        json={
            "id": "mod-1",
            "model": "omni-moderation-latest",
            "results": [
                {
                    "flagged": False,
                    "categories": {"violence": False},
                    "category_scores": {"violence": 0.001},
                }
            ],
        },
    )

    result = client.moderations.create(input="hello world")
    assert isinstance(result, ModerationResponse)
    assert result.results[0].flagged is False


@pytest.mark.asyncio
async def test_moderations_async(
    async_client: AsyncClarisMD, httpx_mock
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/moderations",
        json={"id": "mod-2", "model": "m", "results": []},
    )

    result = await async_client.moderations.create(input="x")
    assert result.id == "mod-2"


# ---------------------------------------------------------------------------
# Async coverage for audit / keys / compliance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_list_async(
    async_client: AsyncClarisMD, httpx_mock
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/audit/logs?limit=1&offset=1",
        json=shapes.page(shapes.log("a2", 2), total=2, limit=1, offset=1),
    )

    page = await async_client.audit.list(limit=1, offset=1)
    assert [entry.id for entry in page.logs] == ["a2"]
    assert page.has_more is False


@pytest.mark.asyncio
async def test_audit_get_async(
    async_client: AsyncClarisMD, httpx_mock
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/audit/logs/audit_xyz",
        json=shapes.log("audit_xyz"),
    )

    log = await async_client.audit.get("audit_xyz")
    assert log.id == "audit_xyz"


@pytest.mark.asyncio
async def test_audit_export_async(
    async_client: AsyncClarisMD, httpx_mock
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/audit/export",
        json=shapes.export("pdf"),
    )

    exp = await async_client.audit.export(format="pdf", request_id="req_1")
    assert exp.pdf_bytes().startswith(b"%PDF")
    request = httpx_mock.get_request()
    assert request is not None
    assert json.loads(request.content) == {"format": "pdf", "request_id": "req_1"}


@pytest.mark.asyncio
async def test_keys_full_lifecycle_async(
    async_client: AsyncClarisMD, httpx_mock
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/keys",
        json=[{**shapes.KEY, "id": "k1"}],
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/keys",
        status_code=201,
        json={**shapes.KEY, "id": "k2", "key": "s"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/keys/k2",
        json={**shapes.KEY, "id": "k2"},
    )
    httpx_mock.add_response(
        method="DELETE", url=f"{BASE_URL}/keys/k2", status_code=204
    )

    listed = await async_client.keys.list()
    created = await async_client.keys.create(name="new", permissions=["chat"], expires_in_days=7)
    fetched = await async_client.keys.get("k2")
    await async_client.keys.delete("k2")

    assert listed[0].id == "k1"
    assert created.key == "s"
    assert fetched.key is None


@pytest.mark.asyncio
async def test_compliance_async(
    async_client: AsyncClarisMD, httpx_mock
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/compliance/score?framework=hipaa",
        json={
            "auto_verified": {"satisfied": 1, "total": 2},
            "manual": {"acknowledged": 0, "total": 1, "satisfied": 0},
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/compliance/requirements?framework=hipaa",
        json=[{"id": "r1", "framework": "hipaa", "acknowledgment_status": "pending"}],
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/compliance/requirements/r1/evidence",
        json=[],
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/compliance/requirements/r1/acknowledge",
        json={"id": "r1", "framework": "hipaa", "acknowledgment_status": "acknowledged"},
    )

    score = await async_client.compliance.score()
    reqs = await async_client.compliance.requirements()
    evidence = await async_client.compliance.evidence("r1")
    ack = await async_client.compliance.acknowledge("r1", status="acknowledged")

    assert score.auto_verified.satisfied == 1
    assert reqs[0].id == "r1"
    assert evidence == []
    assert ack.acknowledgment_status == "acknowledged"


# ---------------------------------------------------------------------------
# Streaming edge cases
# ---------------------------------------------------------------------------


def test_stream_close_releases_response(client: ClarisMD, httpx_mock) -> None:
    """Calling ``close()`` early stops iteration and closes the response."""
    body = b"data: {\"id\":\"c\",\"object\":\"chat.completion.chunk\",\"created\":1,\"model\":\"m\",\"choices\":[]}\n\ndata: [DONE]\n\n"
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/chat/completions",
        content=body,
        headers={"content-type": "text/event-stream"},
    )

    stream = client.chat.completions.create(
        model="m",
        messages=[{"role": "user", "content": "hi"}],
        stream=True,
    )
    stream.close()
    # Idempotent — second close must not raise.
    stream.close()


def test_stream_context_manager(client: ClarisMD, httpx_mock) -> None:
    """``with stream as s:`` releases the connection on exit."""
    body = b"data: [DONE]\n\n"
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/chat/completions",
        content=body,
        headers={"content-type": "text/event-stream"},
    )

    stream = client.chat.completions.create(
        model="m",
        messages=[{"role": "user", "content": "hi"}],
        stream=True,
    )
    with stream as s:
        chunks = list(s)
    assert chunks == []


def test_stream_response_property(client: ClarisMD, httpx_mock) -> None:
    """``stream.response`` exposes the underlying httpx.Response."""
    body = b"data: [DONE]\n\n"
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/chat/completions",
        content=body,
        status_code=200,
        headers={"content-type": "text/event-stream", "X-Request-ID": "req-abc"},
    )

    stream = client.chat.completions.create(
        model="m",
        messages=[{"role": "user", "content": "hi"}],
        stream=True,
    )
    assert stream.response.status_code == 200
    assert stream.response.headers["X-Request-ID"] == "req-abc"
    list(stream)


# ---------------------------------------------------------------------------
# Sync sync-context-manager + close coverage
# ---------------------------------------------------------------------------


def test_sync_client_context_manager() -> None:
    with ClarisMD(api_key="cmd-x", base_url=BASE_URL) as c:
        assert c.api_key == "cmd-x"


def test_sync_client_owns_close_idempotent() -> None:
    c = ClarisMD(api_key="cmd-x", base_url=BASE_URL)
    c.close()
    c.close()


@pytest.mark.asyncio
async def test_async_client_context_manager() -> None:
    async with AsyncClarisMD(api_key="cmd-x", base_url=BASE_URL) as c:
        assert c.api_key == "cmd-x"
