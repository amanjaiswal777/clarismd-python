# Contributing to `clarismd` (Python SDK)

Thanks for considering a contribution. This document covers the dev
environment, code style, commit and PR conventions, and how the project
handles licensing.

## Inbound = outbound, no CLA

This repo is licensed **Apache-2.0** (see [`LICENSE`](./LICENSE)). By
submitting a pull request you confirm that you wrote the contribution
(or have the right to submit it) and that you license it under the
Apache-2.0 license.

We do **not** use a Contributor License Agreement. We do ask that every
commit carries a [Developer Certificate of Origin](https://developercertificate.org/)
sign-off — a one-line statement that you have the right to submit the
work, attached automatically by `git commit -s`:

```
Signed-off-by: Your Name <you@example.com>
```

CI rejects PRs whose commits are not signed off.

## Dev environment

Python 3.9+ is required (CI exercises 3.9 through 3.13).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

The editable install (`-e`) means changes to `src/clarismd/` show up
immediately without reinstalling.

## Running checks locally

The same gate the CI runs:

```bash
ruff check src tests examples       # lint
pyright src                         # type check (strict mode)
pytest --cov=clarismd --cov-fail-under=85
```

Auto-fix lint:

```bash
ruff check --fix src tests examples
```

## Code style

- **Line length**: 100 cols (configured in `pyproject.toml`).
- **Imports**: `from __future__ import annotations` at the top of every
  module; `ruff` sorts imports.
- **Type hints**: required on every public function and method. The
  `pyright --strict` gate is non-negotiable.
- **Docstrings**: every public class and method gets one. Format is
  free-form prose; the first line is a one-sentence summary that fits
  on a tooltip.
- **Comments**: only when the *why* is non-obvious. Don't restate the
  code.
- **Internal modules** are prefixed with `_` (e.g. `_client.py`,
  `_streaming.py`). Public API is whatever `clarismd/__init__.py`
  re-exports — nothing else.

## Tests

- New public methods need tests in `tests/test_<resource>.py`.
- Mock the gateway with `pytest-httpx`; never make real network
  requests in unit tests.
- Async tests use the auto-mode `pytest-asyncio` configured in
  `pyproject.toml` — just `async def test_...`.
- The shared `client` / `async_client` fixtures (see `tests/conftest.py`)
  patch sleep + jitter so the suite stays fast and deterministic.

## Commit & PR conventions

- **Commit messages**: imperative subject under 72 chars, body wrapped
  at 72 explaining *why*. Reference issues with `#nnn`.
- **One concern per PR.** A bug fix is one PR; a refactor is another.
- **CHANGELOG**: add a bullet under `[Unreleased]` for any
  user-visible change.

## Releasing

The release flow lives in [`RELEASING.md`](./RELEASING.md). Maintainers
only.

## Reporting bugs / requesting features

Use the issue templates at
<https://github.com/clarismd/clarismd-python/issues/new/choose>.
For security issues, **do not** open a public issue — see
[`SECURITY.md`](./SECURITY.md).
