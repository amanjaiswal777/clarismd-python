# Security Policy — `clarismd` Python SDK

## Reporting a vulnerability

**Please do not file a public GitHub issue for security vulnerabilities.**
Instead, email **`security@clarismd.com`** with:

- A description of the issue and the impact you believe it has
- Steps to reproduce (proof-of-concept code is welcome)
- The version / commit hash you tested against
- Your name or handle for credit (or a request to remain anonymous)

If you'd like to encrypt your report, request our PGP key at the same
address — we'll send it back out of band.

We aim to acknowledge receipt within **2 business days** and provide an
initial assessment within **5 business days**.

## Disclosure timeline

We follow a **90-day coordinated disclosure** window:

| Day | Step |
|----:|---|
| 0   | Report received; we acknowledge and start triage |
| 5   | Initial assessment shared with the reporter |
| 30  | Patch developed and tested |
| 60  | Patch released; advisory drafted |
| 90  | Public advisory published; CVE requested if applicable |

If a fix lands sooner we'll publish sooner. If we need more time
(complex fix, third-party coordination) we'll explain why and propose
a new date.

If we go silent for more than 14 days after the initial
acknowledgement, you are released from coordination and may disclose
at your discretion.

## Scope

This policy covers the **`clarismd` Python SDK** distributed via PyPI
and this GitHub repository. Vulnerabilities in the gateway service it
talks to should also be reported to `security@clarismd.com` — same
address, same SLA.

In scope:

- The published `clarismd` package on PyPI
- Source in this repository
- The CI/CD workflows in `.github/workflows/`

Out of scope:

- Vulnerabilities in third-party dependencies — please report those
  upstream first; we will pick up advisories via Dependabot
- Reports that require an attacker who already has the user's API key
  (`cmd-...`); compromise of caller-side credentials is the caller's
  responsibility

## Supported versions

We patch security issues on the latest minor release line. Older minor
versions are end-of-life unless explicitly listed in this section.

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Hall of fame

We credit reporters in the release notes for the version that ships
the fix, unless you ask to remain anonymous.
