#!/usr/bin/env python3
"""Unit test for the recency gate (flag-by-publish-date, never drop)."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.rules import compute_cycle_window, recency_tag

settings = {"recency": {"enabled": True, "window_days": 7,
                        "cutoff_weekday": "monday", "cutoff_time": "09:00",
                        "timezone": "America/Los_Angeles"}}

# Fixed 'now' = Wed 2026-08-12 12:00 UTC → cutoff = Mon 2026-08-10 09:00 LA.
now = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
window_start, cutoff = compute_cycle_window(now, settings)
print("window_start:", window_start.isoformat(), "  cutoff:", cutoff.isoformat())

checks = [
    ("2026-06-18", "STALE"),                              # the FortiBleed case
    ("Mon, 11 Aug 2026 10:00:00 -0700", None),           # in window (RFC-822)
    ("2026-08-04T08:00:00Z", None),                      # in window (ISO)
    ("2026-07-01", "STALE"),                             # clearly old
    ("", "unknown"),                                     # missing date
    ("not a date", "unknown"),                           # unparseable
]

fails = 0
for pub, expect in checks:
    tag = recency_tag(pub, window_start)
    if expect is None:
        ok = tag is None
    elif expect == "STALE":
        ok = tag is not None and tag.startswith("STALE —")
    else:  # unknown
        ok = tag is not None and "unknown" in tag
    fails += (not ok)
    print(f"{'OK ' if ok else 'XX '}pub={pub!r:40} -> {tag!r}")

print(f"\nRESULT: {'PASS' if fails == 0 else f'FAIL ({fails})'}")
sys.exit(1 if fails else 0)
