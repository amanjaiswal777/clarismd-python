# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Five-line quickstart against the ClarisMD gateway.

Set ``CLARISMD_API_KEY`` (and optionally ``CLARISMD_BASE_URL`` for self-host)
before running:

    export CLARISMD_API_KEY=cmd-...
    python examples/quickstart.py
"""
from __future__ import annotations

from clarismd import ClarisMD


def main() -> None:
    client = ClarisMD()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is hypertension?"}],
    )
    print(resp.choices[0].message.content)


if __name__ == "__main__":
    main()
