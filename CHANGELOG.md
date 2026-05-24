# Changelog

All notable changes to the `clarismd` Python SDK are tracked here. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/clarismd/clarismd-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/clarismd/clarismd-python/releases/tag/v0.1.0
