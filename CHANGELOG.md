# Changelog

All notable changes to the `clarismd` Python SDK are tracked here. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- `clarismd_policy` / `clarismd_phi_action` are now honored by the gateway
  (they were sent but ignored). Both are tighten-only; invalid values raise
  `UnprocessableEntityError`. See "ClarisMD-specific request options".
- **Breaking:** `embeddings.create` no longer accepts `clarismd_policy` /
  `clarismd_phi_action`. The gateway does not PHI-scan embedding input, so the
  options never applied there.
- **Breaking:** `keys`, `phi.scan` and `audit` now match what the gateway
  actually returns. The previous models described shapes it never sent, so
  `phi.scan(...).detected` was **always False**, `keys.create(...).secret`
  was always `None`, and `audit.list(cursor=...)` always returned page one.
  - `keys.create(name=, permissions=, expires_in_days=)`; the one-time secret
    is in `key`. `APIKey` fields are `key_prefix`, `permissions`, `revoked`,
    `last_used`, `expires_at` (were `prefix`, `scopes`, `revoked_at`,
    `last_used_at`, `secret`).
  - `phi.scan()` returns `PHIScanResponse` (`results`: one `PHIScanResult`
    per input). Entities are `type`, `subtype`, `severity`, `confidence`,
    `location.start/end`, `matched_text`; `PHIScanResult.detected` is kept as
    a property. New `scan_types` / `use_ml` arguments.
  - `audit.list()` uses `offset` (was `cursor`, which the gateway ignored)
    and returns `logs`, `total`, `limit`, `offset`, `has_more`; new `action`
    and `resource_type` filters. `AuditLog` matches the gateway's entry shape,
    including the hash-chain fields `chain_seq`, `prev_hash`, `entry_hash`.
  - `audit.export()` returns a typed, Ed25519-signed `AuditExport` (was JSON
    re-serialised to bytes, with `request_id` injected into them);
    `AuditExport.pdf_bytes()` decodes PDF exports. `format` is
    `"json" | "pdf"`; new `request_id` / `phi_detected` filters.
- A plain string `user` on chat/completions is now accepted by the gateway
  (it was rejected with a 422).
- `scripts/codegen.sh` defaults to `../clarismd-backend/packages/openapi/v1.yaml`
  (the old default path did not exist).

### Documented

- Agent gate: `metadata={"agent_id": ...}` on chat/completions runs the
  agent's gate check before the provider call.
- Verifying signed evidence offline.
- Python 3.10 is now the minimum. The fix for anyio's TLS host-name
  advisory (GHSA-82r6-8w77-94w6), which the async client's TLS
  connections go through, ships only in anyio 4.14.2, and anyio
  4.13+ requires Python 3.10.
- Dependency floors now exclude versions with known advisories:
  `pydantic>=2.4`, `anyio>=4.14.2`, `certifi>=2026.10.19`,
  `h11>=0.16`, `idna>=3.15`.

## [0.1.1] — 2026-08-21

### Fixed

- A retried request now carries the same `Idempotency-Key` as the
  attempt it retries. The header was rebuilt inside the retry loop on
  both `ClarisMD.request` and `AsyncClarisMD.request`, so an
  auto-generated key was a fresh `uuid4` per attempt and the gateway
  saw several unrelated POSTs where the caller made one — its
  idempotency cache could never match. A POST that timed out after the
  gateway had already accepted and metered it was therefore billed
  again on retry. Callers who pass an explicit
  `clarismd_idempotency_key` were never affected.

## [0.1.0] — 2026-06-21

Initial public release.

### Added

- `ClarisMD` and `AsyncClarisMD` clients targeting `/v1/...` on
  `https://api.clarismd.com` (override with `CLARISMD_BASE_URL`).
- Resources: `chat.completions`, `completions`, `embeddings`,
  `moderations`, `phi.scan`, `audit.{list,get,export}`,
  `compliance.{score,requirements,evidence,acknowledge}`,
  `keys.{list,create,get,delete}`, `health.check`.
- SSE streaming on `chat.completions.create(stream=True)`; chunks
  iterate as `ChatCompletionChunk` and stop at `data: [DONE]`.
- Closed-set error hierarchy mapped from the backend's error envelope:
  `AuthenticationError`, `PermissionDeniedError`, `NotFoundError`,
  `ConflictError`, `UnprocessableEntityError`, `RateLimitError`,
  `PHIPolicyViolationError`, `BudgetExceededError`, `ProviderError`,
  `InternalServerError`, plus `APIConnectionError` /
  `APITimeoutError`.
- Retry policy: 429, 5xx, connection errors, and timeouts are retried
  up to `max_retries` times with `0.5s, 1s, 2s` backoff plus jitter;
  `Retry-After` is honored. 4xx (other than 429) is never retried.
- Auto-generated `Idempotency-Key: cmd-py-{uuid4()}` on every POST;
  opt-out with `clarismd_idempotency_key=False`.
- ClarisMD-specific overrides on chat / completions / embeddings:
  `clarismd_policy`, `clarismd_phi_action`,
  `clarismd_idempotency_key`.
- Pyright-strict typing across the public surface.

[Unreleased]: https://github.com/amanjaiswal777/clarismd-python/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/amanjaiswal777/clarismd-python/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/amanjaiswal777/clarismd-python/releases/tag/v0.1.0
