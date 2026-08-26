#!/usr/bin/env python3
# Sanctum · tools/sensor_bench.py · diagnostic; history via git
"""
Sensor bench — measure what each sensor actually yields, per fetch strategy.

WHY. On 2026-08-25 a corpus audit found 169 of 1303 items with no usable body.
Four hosts were failing four different ways and nothing in the pipeline could
tell them apart. The fixes that followed were chosen from evidence gathered by
this tool, not from assumption: the collector host is the only machine that can
reach these publishers, so it is the only machine whose answer counts.

Run it whenever a sensor's yield looks wrong, and before adding one.

    /opt/ravenor/venv/bin/python3 tools/sensor_bench.py --domain cti
    ... --host darkreading.com          only sensors matching this substring
    ... --limit 2                       articles sampled per feed (default 2)
    ... --strategies plain,ua,imp       which strategies to try

WHAT IT REPORTS, per sensor:
    entries      how many items the feed returned
    fresh        how many are inside the domain's max_publish_age_days
    plain        trafilatura, library defaults (what Sanctum used before)
    ua           trafilatura with a browser user agent
    imp          curl_cffi with a browser TLS fingerprint
    gnews        the same, after resolving a Google News wrapper

A column of zeroes next to a non-zero column is the answer: that sensor needs
that strategy. All columns zero means the sensor is unreachable from this host,
which is a different problem and not one a fetch strategy will fix.

CHANGES NOTHING. No writes, no corpus, no seen.txt. Safe to run mid-cycle.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import feedparser                                                  # noqa: E402
import trafilatura                                                 # noqa: E402

from core import fetch as F                                        # noqa: E402
from core.acolyte import published_dt, too_old                     # noqa: E402
from core.pnd import load_domain                                   # noqa: E402


def words(t):
    return len((t or "").split())


def strat_plain(url, opts):
    """Exactly what the collector did before 2026-08-25: library defaults."""
    try:
        raw = trafilatura.fetch_url(url)
        return words(trafilatura.extract(raw, include_comments=False) if raw else "")
    except Exception:
        return 0


def strat_ua(url, opts):
    text, status = F.try_strategy("trafilatura", url, opts)
    return words(text) if status == F.STATUS_OK else 0


def strat_imp(url, opts):
    if not F.available_strategies()["impersonate"]:
        return -1
    text, status = F.try_strategy("impersonate", url, opts)
    return words(text) if status == F.STATUS_OK else 0


STRATEGIES = {"plain": strat_plain, "ua": strat_ua, "imp": strat_imp}


def bench_url(url, opts, names):
    """Return {strategy: word_count}. -1 means the strategy is unavailable."""
    out = {}
    resolved = url
    if F.is_google_news_url(url):
        if not F.available_strategies()["google_news_decode"]:
            out["gnews"] = -1
        else:
            r = F.resolve_google_news(url, opts)
            out["gnews"] = 1 if r else 0
            resolved = r or url
    for n in names:
        out[n] = STRATEGIES[n](resolved, opts)
    return out, resolved


def main():
    ap = argparse.ArgumentParser(description="Sanctum sensor bench (read-only)")
    ap.add_argument("--domain", default="cti")
    ap.add_argument("--pnd")
    ap.add_argument("--host", help="only sensors whose URL contains this")
    ap.add_argument("--limit", type=int, default=2, help="articles per feed")
    ap.add_argument("--strategies", default="plain,ua,imp")
    ap.add_argument("--feeds", type=int, default=0, help="stop after N sensors (0 = all)")
    args = ap.parse_args()

    names = [n.strip() for n in args.strategies.split(",") if n.strip() in STRATEGIES]
    cfg = load_domain(domain=args.domain, pnd_path=args.pnd)
    collection = cfg["manifest"].get("collection", {})
    opts = collection.get("fetch", {}) or {}
    max_age = collection.get("max_publish_age_days")

    avail = F.available_strategies()
    print("strategies available: " +
          "  ".join("%s=%s" % (k, v) for k, v in avail.items()))
    print("max_publish_age_days = %s\n" % max_age)

    sensors = [u for u in cfg["sensors"] if not args.host or args.host in u]
    if args.feeds:
        sensors = sensors[:args.feeds]
    if not sensors:
        print("no sensors matched"); return

    hdr = "%-46s %7s %6s" % ("sensor", "entries", "fresh")
    for n in names:
        hdr += " %7s" % n
    print(hdr)
    print("-" * len(hdr))

    totals = {n: [0, 0] for n in names}      # [with a body, attempted]
    for s in sensors:
        t0 = time.time()
        try:
            parsed = feedparser.parse(s)
        except Exception as e:
            print("%-46s  parse failed: %s" % (s[:46], e)); continue
        entries = list(parsed.entries)
        fresh = [e for e in entries if not too_old(e, max_age)]
        picks = fresh[:args.limit] if fresh else entries[:args.limit]

        best = {n: 0 for n in names}
        gnews_note = ""
        for e in picks:
            link = e.get("link")
            if not link:
                continue
            res, _resolved = bench_url(link, opts, names)
            if "gnews" in res:
                gnews_note = " gnews=%s" % ("resolved" if res["gnews"] == 1
                                            else ("n/a" if res["gnews"] < 0 else "FAILED"))
            for n in names:
                best[n] = max(best[n], res.get(n, 0))
                totals[n][1] += 1
                if res.get(n, 0) > 0:
                    totals[n][0] += 1

        row = "%-46s %7d %6d" % (s[-46:], len(entries), len(fresh))
        for n in names:
            row += " %7s" % ("n/a" if best[n] < 0 else best[n])
        undated = sum(1 for e in entries if published_dt(e) is None)
        extras = []
        if undated:
            extras.append("%d undated" % undated)
        if gnews_note:
            extras.append(gnews_note.strip())
        extras.append("%.1fs" % (time.time() - t0))
        print(row + "   " + ", ".join(extras))

    print()
    print("=== strategy success rate across every article sampled ===")
    for n in names:
        got, tried = totals[n]
        if tried:
            print("  %-6s %d/%d produced a body (%d%%)" % (n, got, tried,
                                                           round(100 * got / tried)))
    print()
    print("Read it this way: a strategy column that is zero where another is not")
    print("names the fix for that sensor. Every column zero means the host is")
    print("unreachable from here, which no fetch strategy repairs.")


if __name__ == "__main__":
    main()
