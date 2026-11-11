# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Stream tokens from the gateway as they arrive."""
from __future__ import annotations

from clarismd import ClarisMD


def main() -> None:
    client = ClarisMD()
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Explain ACE inhibitors in two sentences."}
        ],
        stream=True,
    )

    with stream as s:
        for chunk in s:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                print(delta.content, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
