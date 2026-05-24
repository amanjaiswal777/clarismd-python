# clarismd

Official Python SDK for the [ClarisMD](https://clarismd.com) governed-AI gateway
for healthcare. One-line drop-in replacement for the OpenAI SDK with PHI
detection, audit logging, and configurable policy enforcement built in.

> **Note.** ClarisMD is a governance gateway. It does not, by itself, make any
> call HIPAA compliant — compliance is a property of your full deployment,
> contracts (BAAs), and operational controls. See `NOTICE` for the full
> disclaimer.

---

## Install

```bash
pip install clarismd
```

Python 3.9+ supported.

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
export CLARISMD_API_KEY=cmd-...
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
export CLARISMD_API_KEY=cmd-...
```

Or pass it explicitly:

```python
client = ClarisMD(base_url="https://gateway.your-org.internal/v1")
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
result = client.phi.scan("Patient John Doe, MRN 4471, called the clinic.")
if result.detected:
    for entity in result.entities:
        print(entity.type, "->", entity.text)
```

---

## Audit export

Pull a signed evidence bundle for a date range:

```python
from datetime import datetime, timezone

bundle = client.audit.export(
    format="pdf",
    start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
    end_date=datetime(2026, 5, 31, tzinfo=timezone.utc),
)
with open("audit-may.pdf", "wb") as f:
    f.write(bundle)
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

Two extra kwargs are accepted on every method and translate into HTTP headers
the gateway understands:

| Kwarg                | Header                       | Effect |
|----------------------|------------------------------|--------|
| `clarismd_policy`    | `X-ClarisMD-Policy`          | Override the policy for this request |
| `clarismd_phi_action`| `X-ClarisMD-PHI-Action`      | One of `block`, `redact`, `tokenize`, `alert` |

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

Issues and PRs welcome at <https://github.com/clarismd/clarismd>.
