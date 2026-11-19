<p align="center">
  <img src="./assets/logo.svg" alt="ClarisMD" width="120" height="120"/>
</p>

<h1 align="center">clarismd</h1>

<p align="center">
  <a href="https://pypi.org/project/clarismd/"><img alt="PyPI" src="https://img.shields.io/pypi/v/clarismd.svg"/></a>
  <a href="https://pypi.org/project/clarismd/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/clarismd.svg"/></a>
  <a href="https://github.com/amanjaiswal777/clarismd-python/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/amanjaiswal777/clarismd-python/actions/workflows/ci.yml/badge.svg"/></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/pypi/l/clarismd.svg"/></a>
  <a href="https://pypi.org/project/clarismd/"><img alt="PyPI Downloads" src="https://img.shields.io/pypi/dm/clarismd.svg"/></a>
</p>

Official Python SDK for the [ClarisMD](https://clarismd.com) governed-AI gateway
for healthcare. One-line drop-in replacement for the OpenAI SDK with PHI
detection, audit logging, and configurable policy enforcement built in.

> **Note.** ClarisMD is a governance gateway. It does not, by itself, make any
> call HIPAA compliant — compliance is a property of your full deployment,
> contracts (BAAs), and operational controls. See `NOTICE` for the full
> disclaimer.

---

## Install

From PyPI:

```bash
pip install clarismd
```

From the public GitHub repo (latest `main`, or pin to a tag/commit):

```bash
pip install git+https://github.com/amanjaiswal777/clarismd-python.git
pip install git+https://github.com/amanjaiswal777/clarismd-python.git@v0.1.0
pip install git+https://github.com/amanjaiswal777/clarismd-python.git@<commit-sha>
```

In a `requirements.txt`:

```
clarismd @ git+https://github.com/amanjaiswal777/clarismd-python.git@v0.1.0
```

For local development (editable install with dev extras):

```bash
git clone https://github.com/amanjaiswal777/clarismd-python.git
cd clarismd-python
pip install -e ".[dev]"
```

Python 3.10+ supported.

---

## Quickstart

```python
from clarismd import ClarisMD

client = ClarisMD()  # reads CLARISMD_API_KEY

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Summarize hypertension treatment options."}],
)
print(resp.choices[0].message.content)
```

Set your API key once:

```bash
export CLARISMD_API_KEY=clr_live_...
```

---

## Migrating from OpenAI

The surface mirrors `openai>=1.0`. In most cases, the diff is one line:

```diff
-from openai import OpenAI
-client = OpenAI()
+from clarismd import ClarisMD
+client = ClarisMD()
```

Everything else — `client.chat.completions.create`, `client.embeddings.create`,
streaming, async — works the same way.

---

## Self-host

Point the SDK at your own gateway with one environment variable:

```bash
export CLARISMD_BASE_URL=https://gateway.your-org.internal/v1
export CLARISMD_API_KEY=clr_live_...
```

Or pass it explicitly:

```python
client = ClarisMD(base_url="https://gateway.your-org.internal/v1")
```

Verify the gateway is reachable (no API key required):

```python
status = client.health.check()
print(status.status, status.version)  # "ok" 0.4.2
```

---

## Streaming

```python
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Explain ACE inhibitors briefly."}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.content:
        print(delta.content, end="", flush=True)
```

Streams expose `.close()` and the underlying `httpx.Response` via
`stream.response`, and can be used as context managers.

---

## Async

```python
import asyncio
from clarismd import AsyncClarisMD

async def main() -> None:
    async with AsyncClarisMD() as client:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
        )
        print(resp.choices[0].message.content)

asyncio.run(main())
```

---

## PHI scan

Run text through the PHI detector without making a generation call:

```python
response = client.phi.scan("Patient John Doe, MRN 4471, called the clinic.")
result = response.results[0]  # one result per input; pass a list to scan a batch
if result.detected:
    for entity in result.entities:
        print(entity.subtype or entity.type, "->", entity.matched_text, entity.location)
```

---

## Audit export

Pull a signed evidence bundle for a date range:

```python
from datetime import datetime, timezone

bundle = client.audit.export(
    format="pdf",  # or "json" (default): the logs are in bundle.payload
    start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
    end_date=datetime(2026, 5, 31, tzinfo=timezone.utc),
)
with open("audit-may.pdf", "wb") as f:
    f.write(bundle.pdf_bytes())
```

List entries with offset paging; each carries its position in your
organisation's stored hash chain (`chain_seq`, `prev_hash`, `entry_hash`):

```python
page = client.audit.list(phi_detected=True, limit=100, offset=0)
print(page.total, page.has_more, page.logs[0].entry_hash if page.logs else None)
```

### Verifying evidence

Exports and evidence packages are signed with **Ed25519**
(`signature="ed25519:<key_id>:<base64>"`). Anyone can verify them with the
public key, without a ClarisMD account and without trusting the server:

```bash
python clarismd-backend/scripts/verify_evidence.py export.json \
  --keys-url https://api.clarismd.com/api/v1/evidence/signing-keys
```

The verifier checks the signature and re-hashes every chained log entry. Pin
the key's `kid` out of band; a key fetched from the server being audited only
proves consistency.

---

## Agent gate

Pass the id of an agent you registered (`POST /api/v1/agents`) in `metadata`
and the gateway runs that agent's gate check **before** the model is called:

```python
client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    metadata={"agent_id": "0b6f6a3e-5a1d-4c55-9a7e-6f0f3f1c2d4b", "workflow_name": "prior-auth"},
)
```

A suspended agent, a data classification outside its allowlist, or a trust
score below the threshold (70 when the input contains PHI, 50 otherwise)
raises `PermissionDeniedError` (`code="agent_gate_denied"`) and nothing is sent
to the provider. An `agent_id` that is not one of your agents raises
`UnprocessableEntityError` (`code="invalid_agent"`). This gates the model call
made on the agent's behalf; it is not tool-call authorization.

---

## API keys

```python
key = client.keys.create(name="ci", permissions=["chat"], expires_in_days=90)
print(key.key)  # the full secret, returned once: store it now
```

---

## Compliance score

```python
score = client.compliance.score(framework="hipaa")
print(f"Auto-verified: {score.auto_verified.satisfied}/{score.auto_verified.total}")
print(f"Manual:        {score.manual.acknowledged}/{score.manual.total}")
```

---

## Error handling

All errors derive from `ClarisMDError`. The closed-set typed errors let you
branch precisely:

```python
from clarismd import (
    ClarisMD,
    AuthenticationError,
    PHIPolicyViolationError,
    RateLimitError,
)

client = ClarisMD()

try:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "..."}],
    )
except PHIPolicyViolationError as exc:
    # Request was blocked by a configured PHI policy.
    print("PHI violation:", exc, "request_id:", exc.request_id)
except RateLimitError as exc:
    # Retry-After honored automatically; this fires only after the budget is spent.
    print("Backed off too long:", exc)
except AuthenticationError:
    # 401 — bad / missing / revoked key.
    raise
```

Every `APIError` carries `.status_code`, `.request_id`, `.code`, `.param`,
`.type`, and `.body` for structured handling and bug reports.

### ClarisMD-specific request options

Two extra kwargs on `chat.completions.create` and `completions.create`
translate into headers the gateway applies to that request:

| Kwarg                | Header                       | Effect |
|----------------------|------------------------------|--------|
| `clarismd_policy`    | `X-ClarisMD-Policy`          | Id of one of your own active security policies; its rules are applied on top of your settings for this call |
| `clarismd_phi_action`| `X-ClarisMD-PHI-Action`      | `block`, `redact` (alias `tokenize`) or `alert` |

Both are **tighten-only**: they can make this call stricter than your
organisation's settings, never looser (`alert` on a tenant that redacts still
redacts). `block` refuses a request containing PHI before the provider is
called (`PHIPolicyViolationError`). An unknown value, or a policy id that is not
your own active policy, raises `UnprocessableEntityError`. The response header
`X-ClarisMD-PHI-Action-Applied` reports what the gateway actually did with PHI:
`redact`, `alert`, or `none`.

```python
client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "..."}],
    clarismd_phi_action="redact",
)
```

---

## Examples

Runnable scripts live in [`examples/`](./examples):

- [`quickstart.py`](./examples/quickstart.py) — five-line basic call
- [`streaming.py`](./examples/streaming.py) — server-sent-events streaming
- [`async_chat.py`](./examples/async_chat.py) — `AsyncClarisMD` round-trip
- [`phi_scan.py`](./examples/phi_scan.py) — PHI entity detection
- [`audit_export.py`](./examples/audit_export.py) — pull a PDF evidence bundle
- [`compliance_score.py`](./examples/compliance_score.py) — auto vs. manual breakdown

---

## License

Apache-2.0. See [`LICENSE`](./LICENSE) and [`NOTICE`](./NOTICE).

The ClarisMD backend is licensed AGPL-3.0; this SDK is intentionally permissive
so you can ship it inside any application without copyleft obligations.

## Contributing

Issues and PRs welcome. Before opening a PR, run the checks CI enforces:

```bash
pip install -e ".[dev]"
ruff check src tests examples
pyright
pytest --cov=clarismd --cov-fail-under=85
```

Add a bullet under `[Unreleased]` in `CHANGELOG.md` for any user-visible change.
Contributions are accepted under Apache-2.0 (LICENSE §5).

## Releasing (maintainers)

1. Bump `version` in `pyproject.toml` **and** `__version__` in `src/clarismd/_version.py`.
2. In `CHANGELOG.md`, move `[Unreleased]` items to `## [X.Y.Z] — YYYY-MM-DD` and update the compare links.
3. `git commit -am "Release vX.Y.Z" && git tag -a vX.Y.Z -m vX.Y.Z && git push origin main vX.Y.Z`

`.github/workflows/publish.yml` fails if the tag ≠ `_version.py`, then builds and uploads to
PyPI via trusted publishing (GitHub environment `pypi`). PyPI never accepts a re-upload of
the same version — yank a broken release and ship the next patch.

## Security

Report vulnerabilities privately to **security@clarismd.com** — do not open a
public issue. Include the SDK version or commit, reproduction steps, and impact.
We acknowledge within 2 business days, follow 90-day coordinated disclosure,
and patch the latest minor line (currently `0.1.x`).
