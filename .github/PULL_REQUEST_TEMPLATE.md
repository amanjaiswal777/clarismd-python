<!--
Thank you for the contribution! A few quick checks before you submit.
For security fixes, please coordinate via security@clarismd.com first
(see SECURITY.md) rather than opening a public PR.
-->

## What this PR does

<!-- One or two sentences. Why is this change needed? Link the issue
     it resolves with `Closes #nnn` if applicable. -->

## How to verify

<!-- Reviewer-runnable steps: commands, expected output, screenshots. -->

```bash
ruff check src tests examples
pyright src
pytest --cov=clarismd --cov-fail-under=85
```

## Checklist

- [ ] Tests added or updated for the change
- [ ] `pytest` passes locally with coverage ≥ 85%
- [ ] `pyright src` is clean (strict mode)
- [ ] `ruff check src tests examples` is clean
- [ ] CHANGELOG.md updated under `[Unreleased]` for any user-visible change
- [ ] Public API additions have docstrings and type hints
- [ ] Commits are signed off (`git commit -s`)
