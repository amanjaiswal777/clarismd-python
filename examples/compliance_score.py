# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Print the auto-verified vs. manual-attestation breakdown for a framework.

ClarisMD never collapses these into a single rolled-up score: auto-verified
checks are what the gateway can demonstrate from telemetry, and manual
attestations are statements your organization has acknowledged. They live in
separate buckets on purpose.
"""
from __future__ import annotations

from clarismd import ClarisMD


def main() -> None:
    client = ClarisMD()
    score = client.compliance.score(framework="hipaa")

    auto = score.auto_verified
    manual = score.manual

    print("HIPAA")
    print(f"  Auto-verified: {auto.satisfied}/{auto.total}")
    print(f"  Manual:        {manual.acknowledged}/{manual.total}")

    pending = client.compliance.requirements(framework="hipaa", status="pending")
    if pending:
        print("\nPending manual attestations:")
        for req in pending:
            print(f"  - {req.code}: {req.title}")


if __name__ == "__main__":
    main()
