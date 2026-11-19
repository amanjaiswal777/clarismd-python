# clarismd-python

`clarismd` (PyPI, v0.1.1, Apache-2.0) is the official Python client for the ClarisMD gateway (clarismd-backend `/v1/*`). It provides sync `ClarisMD` and async `AsyncClarisMD`, designed as a drop-in for the `openai>=1.0` SDK. It is a library, not a service, and has no ML dependencies.

## Stack
- Python >=3.10 (CI matrix 3.10-3.13; local `.venv` is 3.12). Build backend: hatchling.
- Runtime: httpx, pydantic v2, typing-extensions, plus CVE-floor pins (anyio, certifi, h11, idna).
- Plain pip, no lockfile.

## Commands
- Install: `source .venv/bin/activate && pip install -e ".[dev]"`
- Lint: `ruff check src tests examples`
- Type-check: `pyright` (strict, `src/` only, excludes `src/clarismd/_generated`)
- Test: `pytest --cov=clarismd --cov-fail-under=85`
  - Single test: `pytest tests/test_chat.py::test_name`
- Build: `python -m build && twine check dist/*`
- Example: `python examples/quickstart.py` (needs `CLARISMD_API_KEY`)
- Codegen: `scripts/codegen.sh ../clarismd-backend/packages/openapi/v1.yaml`
  - Always pass the path: the default points at the old monorepo.
  - Needs `pipx install 'openapi-python-client>=0.21,<0.22'`.
  - Codegen wipes `src/clarismd/_generated/`.
- Full check before done: `ruff check src tests examples && pyright && pytest --cov=clarismd --cov-fail-under=85`

## Layout
- `src/clarismd/_client.py`: sync and async clients, retries, headers.
- `src/clarismd/_streaming.py` (SSE), `_exceptions.py`, `_types.py`, `_version.py`.
- `src/clarismd/resources/`: one module per API group (chat, completions, embeddings, moderations, phi, audit, compliance, keys, health), plus `_base.py`.
- `src/clarismd/_generated/`: codegen output. Currently a stub.
- `tests/` uses pytest-httpx mocks. `conftest.py` turns sleeps into no-ops and puts `src/` on the path.
- `examples/`, `scripts/codegen.sh`, `codegen-config.yml`.

## Conventions
- Ruff rules E, W, F, I, B, UP with line-length 100. CI does not run `ruff format`, so avoid reformatting untouched code.
- Pytest:
  - `asyncio_mode=auto`.
  - `filterwarnings="error"`, so any warning fails a test.
  - Coverage must stay at or above 85%.
- Env: `CLARISMD_API_KEY` (Bearer) and `CLARISMD_BASE_URL` (default `https://api.clarismd.com/v1`).
- Headers: `X-ClarisMD-Client`, `X-ClarisMD-Policy`, `X-ClarisMD-PHI-Action`, and an auto `Idempotency-Key` on POST (stable across retries).
- Keep the API surface parallel with clarismd-node (`clarismd_policy` / `clarismdPolicy`). API changes start in the backend spec.
- Note user-visible changes in `CHANGELOG.md` under `[Unreleased]`.
- Conventional Commits with DCO sign-off (`git commit -s`). Never commit or push yourself.

## Gotchas
- pyright `pythonVersion = "3.9"` and ruff `target-version = "py39"` are stale (requires-python is >=3.10). The UP006/UP007/UP035/UP045 ignores exist only because of that. Ask before changing them.
- The version lives in BOTH `pyproject.toml` and `src/clarismd/_version.py`. Bump both, or the publish fails.

## Release (don't trigger)
- `.github/workflows/ci.yml` runs on push or PR to `main`: ruff, pyright, and pytest across the matrix, then a build.
- `publish.yml` runs on a `v*` tag. The tag must equal `__version__`, then it publishes to PyPI via OIDC (environment `pypi`).
