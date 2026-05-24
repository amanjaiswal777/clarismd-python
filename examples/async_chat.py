# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Round-trip a chat completion via ``AsyncClarisMD``."""
from __future__ import annotations

import asyncio

from clarismd import AsyncClarisMD


async def main() -> None:
    async with AsyncClarisMD() as client:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Briefly: what is metformin?"}],
        )
        print(resp.choices[0].message.content)


if __name__ == "__main__":
    asyncio.run(main())
