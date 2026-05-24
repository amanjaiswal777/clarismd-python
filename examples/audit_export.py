# Copyright (c) 2026 ClarisMD contributors.
# SPDX-License-Identifier: Apache-2.0

"""Pull a signed audit-log evidence bundle for a date range."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from clarismd import ClarisMD


def main() -> None:
    client = ClarisMD()
    blob = client.audit.export(
        format="pdf",
        start_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 5, 31, tzinfo=timezone.utc),
    )

    out = Path("audit-may-2026.pdf")
    out.write_bytes(blob)
    print(f"Wrote {out} ({len(blob):,} bytes)")


if __name__ == "__main__":
    main()
