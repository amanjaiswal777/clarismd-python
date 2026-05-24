# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Detect PHI entities in free text without making a generation call."""
from __future__ import annotations

from clarismd import ClarisMD


SAMPLE = (
    "Patient John Doe, MRN 4471, called the clinic. "
    "Reach him at j.doe@example.test or 555-867-5309."
)


def main() -> None:
    client = ClarisMD()
    result = client.phi.scan(SAMPLE)

    print(f"PHI detected: {result.detected}")
    for entity in result.entities:
        print(f"  - {entity.type}: {entity.text!r}")


if __name__ == "__main__":
    main()
