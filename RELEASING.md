# Releasing `clarismd` to PyPI

Internal runbook for cutting a release. The CI workflow at
`.github/workflows/python-sdk-publish.yml` does the actual upload via
PyPI **trusted publishing** (OIDC, no API token). This file lists the
human steps that bracket that workflow.

## Prerequisites — one-time

These run once per project, not per release. Track in
`LAUNCH_PLAN/STATUS.md` once each is done.

1. **Claim `clarismd` on PyPI and TestPyPI.**
   - Sign in to <https://pypi.org/> and <https://test.pypi.org/>.
   - Reserve the project name by uploading the local
     `dist/clarismd-0.1.0.tar.gz` once via `twine` (manual upload is
     fine; the trusted-publisher flow works for subsequent releases).
   - If the name is taken, the contingency in `LAUNCH_PLAN/16` triggers.

2. **Configure trusted publishers.**
   - In <https://pypi.org/manage/project/clarismd/settings/publishing/>,
     add a publisher: workflow `python-sdk-publish.yml`, repo
     `amanjaiswal777/clarismd-python`, environment `pypi`.
   - Repeat on TestPyPI with environment `testpypi`.
   - In the GitHub repo, create matching environments under
     **Settings → Environments**: `pypi` and `testpypi`. Restrict
     `pypi` to protected tags `v*`.

3. **Smoke-test the workflow with a TestPyPI dry run.**
   - Bump `_version.py` to `0.1.0rc0` on a branch.
   - Tag `v0.1.0rc0` and push. The workflow's `testpypi` job picks
     it up and uploads.
   - In a fresh venv: `pip install -i https://test.pypi.org/simple/ clarismd==0.1.0rc0`,
     then `python -c "from clarismd import ClarisMD; print(ClarisMD.__module__)"`.

## Per-release checklist

For each new version (`X.Y.Z`):

1. **Update `_version.py`** — `__version__ = "X.Y.Z"`.

2. **Update `CHANGELOG.md`** — move items from `[Unreleased]` into a
   new `[X.Y.Z] — YYYY-MM-DD` section. Bump the `[Unreleased]` and
   `[X.Y.Z]` link footers.

3. **Local validation** — must all pass:
   ```bash
   ruff check src tests examples
   pyright src
   pytest --cov=clarismd --cov-fail-under=85
   rm -rf dist build && python -m build
   twine check dist/*
   ```

4. **Fresh-venv smoke** — the wheel must install and expose all
   resources without the source tree on `PYTHONPATH`:
   ```bash
   python -m venv /tmp/cmd-smoke && /tmp/cmd-smoke/bin/pip install dist/clarismd-X.Y.Z-py3-none-any.whl
   /tmp/cmd-smoke/bin/python -c "
   from clarismd import ClarisMD
   c = ClarisMD(api_key='cmd-smoke', base_url='http://localhost:8000/v1')
   for name in ('chat', 'completions', 'embeddings', 'moderations', 'phi',
                'audit', 'compliance', 'keys', 'health'):
       assert hasattr(c, name), name
   print('ok')
   "
   ```

5. **Integration smoke against staging gateway.** Uses the real
   hosted-demo endpoint (`https://demo.clarismd.com/v1`):
   ```bash
   CLARISMD_BASE_URL=https://demo.clarismd.com/v1 \
   CLARISMD_API_KEY=cmd-... \
   python examples/quickstart.py
   ```
   Expectation: a 200 response with a non-empty `choices[0].message.content`,
   plus an audit log entry visible in the dashboard. If staging is
   unavailable, run against a local `infrastructure/install.sh` deploy.

6. **Tag and push.**
   ```bash
   git commit -am "Release vX.Y.Z"
   git tag -s vX.Y.Z -m "vX.Y.Z"
   git push origin main vX.Y.Z
   ```
   The `python-sdk-publish.yml` workflow runs on the tag and uploads
   to PyPI via the trusted publisher.

7. **Verify the release.**
   - PyPI page shows the new version: <https://pypi.org/project/clarismd/>.
   - `pip install clarismd==X.Y.Z` works in a fresh venv.
   - GitHub Releases auto-generates from the tag; edit the body to
     paste the matching CHANGELOG section.

## Rollback

PyPI does not allow re-uploading a deleted version. If a release is
broken:

1. Yank the version on PyPI (Project → Manage → Yank). This keeps
   `pip install clarismd==X.Y.Z` working for pinned users but hides
   it from `pip install clarismd`.
2. Cut `X.Y.Z+1` with the fix.

## v0.1.0 launch checklist (one-time)

Cross-references `LAUNCH_PLAN/07-python-sdk.md` "Done when":

- [ ] Trusted publishers configured on PyPI + TestPyPI.
- [ ] TestPyPI dry run via `v0.1.0rc0` tag — install + import + one
      live call against staging works.
- [ ] Local validation green (ruff + pyright + pytest ≥ 85% + build +
      twine check).
- [ ] Integration smoke against `demo.clarismd.com` returns 200 and
      writes an audit log.
- [ ] `v0.1.0` tag pushed; `python-sdk-publish.yml` green; PyPI shows
      `clarismd 0.1.0`.
- [ ] `pip install clarismd` in a fresh venv on a different machine
      works end-to-end.
