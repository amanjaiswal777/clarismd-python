# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Pull a signed audit-log evidence bundle for a date range.

Verify it offline (no ClarisMD account needed) by exporting with
``format="json"`` and running
``python clarismd-backend/scripts/verify_evidence.py export.json --keys-url
https://api.clarismd.com/api/v1/evidence/signing-keys``.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from clarismd import ClarisMD


def main() -> None:
    client = ClarisMD()
    exported = client.audit.export(
        format="pdf",
        start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 5, 31, tzinfo=timezone.utc),
    )

    pdf = exported.pdf_bytes()
    out = Path("audit-may-2026.pdf")
    out.write_bytes(pdf)
    print(f"Wrote {out} ({len(pdf):,} bytes), signed {exported.signature_alg} key {exported.key_id}")


if __name__ == "__main__":
    main()
