#!/usr/bin/env python3
# Sanctum · tools/lag_check.py · diagnostic; history via git
"""
Publication-to-collection lag — what should `max_publish_age_days` be?

WHY. On 2026-08-25 the collection cutoff was set to 7 days, matching the
intelligence cycle window, because that is what the direction said. But the
cutoff and the cycle window answer different questions:

    the recency gate asks   "is this still current?"      and LABELS it
    the collection cutoff   "is this certainly worthless?" and DELETES it

Only one of those is destructive, and the destructive one had no measured
basis. Every item the corpus audit complained about was published before 2026,
which means any cutoff between 8 and 237 days would have caught all of them —
a range so wide it constrains nothing. 30 was proposed and it was a round
number, not a derived one.

WHAT ACTUALLY SETS IT. How late a feed serves something we would have wanted.
The cutoff must sit above that or it deletes items that would have surfaced.
That lag is already in the corpus: every record carries both `published` and
`collected`. This measures it.

    tools/lag_check.py --domain cti

READ IT THIS WAY. Take the smallest cutoff that deletes 0.0% of SURFACING
items, then add margin. The "of all items" column is noise you are happy to
lose; the "of SURFACING items" column is the one that must stay at zero.

CHANGES NOTHING. No writes, no network. Safe to run mid-cycle.
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pnd import load_domain                                   # noqa: E402
from core.rules import score_article                               # noqa: E402

CUTOFFS = (7, 10, 14, 21, 30, 45, 60, 90)


def host(u):
    return re.sub(r"^https?://(www\.)?", "", str(u)).split("/")[0]


def _aware(dt):
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def published_at(art):
    """RSS dates are RFC 2822; some feeds emit ISO. Try both, then give up."""
    raw = str(art.get("published", "") or "")
    if not raw:
        return None
    for parse in (parsedate_to_datetime,
                  lambda x: datetime.fromisoformat(x.replace("Z", "+00:00"))):
        try:
            d = parse(raw)
            if d:
                return _aware(d)
        except Exception:
            continue
    return None


def collected_at(art):
    try:
        return _aware(datetime.fromisoformat(str(art.get("collected", ""))))
    except Exception:
        return None


def pct(values, q):
    if not values:
        return float("nan")
    v = sorted(values)
    return v[min(len(v) - 1, int(round(q / 100.0 * (len(v) - 1))))]


def row(label, values):
    if not values:
        print("%-34s (none)" % label)
        return
    print("%-34s n=%-6d p50=%-7.1f p90=%-7.1f p95=%-7.1f p99=%-7.1f max=%.1f"
          % (label, len(values), pct(values, 50), pct(values, 90),
             pct(values, 95), pct(values, 99), max(values)))


def main():
    ap = argparse.ArgumentParser(description="Sanctum lag check (read-only)")
    ap.add_argument("--domain", default="cti")
    ap.add_argument("--pnd")
    args = ap.parse_args()

    cfg = load_domain(domain=args.domain, pnd_path=args.pnd)
    scoring = cfg["scoring"]
    threshold = float(scoring.get("settings", {}).get("surface_min_score", 2.0))
    configured = cfg["manifest"].get("collection", {}).get("max_publish_age_days")

    lags_all, lags_surf, by_host = [], [], {}
    undated = 0
    for f in glob.glob(os.path.join(str(cfg["corpus_dir"]), "*", "*.json")):
        try:
            art = json.loads(open(f, encoding="utf-8").read())
        except Exception:
            continue
        p, c = published_at(art), collected_at(art)
        if p is None or c is None:
            undated += 1
            continue
        lag = max(0.0, (c - p).total_seconds() / 86400.0)
        lags_all.append(lag)
        score, _tier, _reasons = score_article(art, scoring)
        if score >= threshold:
            lags_surf.append(lag)
            by_host.setdefault(host(art.get("url", "")), []).append(lag)

    print("Publication-to-collection lag, in DAYS.")
    print("Surfacing threshold %.1f · max_publish_age_days currently %s\n"
          % (threshold, configured))
    row("every corpus item", lags_all)
    row("items that WOULD SURFACE", lags_surf)
    print("\nundated — lag unknowable, always kept: %d" % undated)

    print("\n=== what each candidate cutoff would DELETE ===")
    print("%-10s %16s %20s" % ("cutoff", "of all items", "of SURFACING items"))
    safe = None
    for d in CUTOFFS:
        la = sum(1 for x in lags_all if x > d)
        ls = sum(1 for x in lags_surf if x > d)
        print("%-10s %8d (%4.1f%%) %11d (%4.1f%%)"
              % ("%d days" % d, la, 100.0 * la / max(1, len(lags_all)),
                 ls, 100.0 * ls / max(1, len(lags_surf))))
        if ls == 0 and safe is None:
            safe = d

    print()
    if safe is None:
        print("No cutoff in this range is free of loss. Widen the range, or")
        print("accept a measured loss and write down what it is.")
    else:
        print("Smallest cutoff that deletes NOTHING you would have surfaced: "
              "%d days." % safe)
        print("Add margin — the corpus is one sample of feed behaviour, not all")
        print("of it. A slow week is not the slowest week.")

    print("\n=== slowest-serving sensors, among items that would surface ===")
    print("(a large p95 here is either a slow feed or one that dates items by")
    print(" INCIDENT rather than publication — the second kind gets deleted")
    print(" for the wrong reason, so check any outlier by hand)")
    for h, v in sorted(by_host.items(), key=lambda kv: -pct(kv[1], 95))[:12]:
        print("  %-34s n=%-5d p95=%-8.1f max=%.1f"
              % (h[:34], len(v), pct(v, 95), max(v)))


if __name__ == "__main__":
    main()
