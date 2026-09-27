#!/usr/bin/env python3
"""
Sanctum · tools/sensor_candidates.py · finding the next sensor from evidence

Two jobs, and the first one is the point.

    --list   (default)  read the corpus and rank the publishers Sanctum is
                        ALREADY collecting from indirectly but does not declare
                        as a sensor. Offline. No network. Safe mid-cycle.
    --probe  <domain>   try the common feed paths on one host and report what
                        each returns. Needs network, so it runs on the
                        collection host and nowhere else.

WHY THIS EXISTS
---------------
Adding a sensor has been guesswork with one exception, and that exception is the
method this tool automates. On 2026-08-23 a session read a CyberWire daily
roundup, listed which outlets its ten stories came from, found that five came
from two publishers Sanctum did not collect, and added both. That worked. It
also took an afternoon and it only looked at ten stories.

The corpus already holds the same evidence for thousands of stories. Eleven of
the fourteen regional sensors are Google News queries, and a Google News item
carries the publisher's own URL once the wrapper is resolved. So every article
that arrived through a query is a vote for a publisher Sanctum may want to read
directly.

A DIRECT FEED IS NOT THE SAME AS A QUERY, which is why an already-reached
publisher is still a candidate:

  - `gnews_interval` is one second per wrapper, and every wrapper is resolved
    one at a time. Collection went from 88 seconds to 20 minutes when wrapper
    resolution landed. A direct feed costs one request.
  - a query returns what Google chose to match, not what the publisher
    published. The publisher's own feed is the complete list.
  - a resolution failure loses the article entirely. A direct feed has no
    wrapper to fail.

WHAT IT MEASURES, and the ranking is deliberate
-----------------------------------------------
Article count is the wrong ranking and has been since 2026-08-26, when
Malwarebytes was declined after measurement showed zero of its items would
surface. **A good feed is not the same as an additive one.** So each publisher
is ranked by how many of its articles WOULD SURFACE at the domain's own
threshold, with the requirement count beside it:

    surfaced   scored at or above scoring.settings.surface_min_score
    answered   satisfied at least one intelligence requirement
    articles   how many are in the window at all
    viaquery   how many arrived through a Google News query sensor rather
               than a direct feed

A publisher with many articles and no surfacing items is not a candidate. A
publisher with few articles that all surface is.

THE RESOLVED-URL CAVEAT, and it broke a measurement on 2026-09-26
-----------------------------------------------------------------
A corpus record keeps `url` as collected and `final_url` only when resolution
CHANGED it. A probe that read `url` alone found 52 of 57 hits on
`news.google.com` and learned nothing about publishers. This tool prefers
`final_url` and falls back to `url`, and it PRINTS how many records were still
unresolved, because that number is the ceiling on what it can see.

CHANGES NOTHING. No writes, no corpus, no seen.txt.

    tools/sensor_candidates.py --domain cti --days 30
    ... --top 25                 how many candidates to print (default 20)
    ... --min-articles 2         ignore publishers below this (default 2)
    ... --declared               also print the publishers already declared
    ... --probe example.com      try the common feed paths on one host
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pnd import load_domain                                   # noqa: E402
from core.rules import (detectable_requirements,                   # noqa: E402
                        requirement_coverage, score_article)

# The paths worth trying, ordered by how often they are ALREADY the path of a
# declared sensor. Counted 2026-09-26 across the 41 non-query sensors:
#   /feed/ 11 · /rss.xml 5 · /feed 3 · /rss/ 1 · /blog/feed/ 1 · /feed/atom/ 1
# The rest are conventions this apparatus has not needed yet - the WordPress
# query form, the Ghost and Hugo defaults - and they cost one request each.
#
# THIS LIST IS A STARTING POINT, NOT A SUBSTITUTE FOR LOOKING. Nine declared
# sensors sit at a path no convention would guess: /vulfeed, /jvn.rdf,
# /current-activity.xml, /CiscoSecurityAdvisory.xml, /ir.xml. When every path
# here comes back empty, the feed may still exist - read the publisher's page.
FEED_PATHS = ["/feed/", "/rss.xml", "/feed", "/rss/", "/blog/feed/",
              "/feed/atom/", "/rss", "/feed.xml", "/atom.xml", "/index.xml",
              "/?feed=rss2"]


def host_of(url):
    """The bare host of a URL, with no scheme and no leading www."""
    return re.sub(r"^https?://(www\.)?", "", str(url or "")).split("/")[0].lower()


def publisher_of(art):
    """
    The publisher's host for one corpus record, or None when unresolvable.

    `final_url` is written only when resolution CHANGED the URL, so it is the
    resolved wrapper when there was one and absent otherwise.
    """
    h = host_of(art.get("final_url") or art.get("url"))
    return h or None


def load(corpus_dir, days):
    cut = datetime.now(timezone.utc) - timedelta(days=days)
    root = Path(corpus_dir)
    if not root.exists():
        raise SystemExit(f"no corpus at {root}")
    out = []
    for day in sorted(root.iterdir()):
        if not day.is_dir():
            continue
        for jf in day.glob("*.json"):
            try:
                art = json.loads(jf.read_text(encoding="utf-8"))
            except Exception:
                continue
            # On any doubt about the date, KEEP - the same choice
            # core/arbites.py and tools/requirement_coverage.py make.
            try:
                c = datetime.fromisoformat(str(art.get("collected", "")))
                c = c if c.tzinfo else c.replace(tzinfo=timezone.utc)
                if c < cut:
                    continue
            except Exception:
                pass
            out.append(art)
    return out


def run_list(args, cfg):
    scoring = cfg["scoring"]
    req = cfg.get("requirements") or {}
    classes = cfg.get("sensor_classes") or {}
    threshold = float(scoring.get("settings", {})
                      .get("surface_min_score", 2.0))
    detectable = detectable_requirements(req, scoring) if req else set()
    declared = {host_of(u) for u in (cfg.get("sensors") or [])}

    arts = load(args.corpus or cfg["corpus_dir"], args.days)
    stats = defaultdict(lambda: dict(articles=0, surfaced=0, answered=0,
                                     viaquery=0))
    unresolved = 0
    for art in arts:
        pub = publisher_of(art)
        if not pub:
            continue
        if pub == "news.google.com":
            # An unresolved wrapper. It names no publisher, so it can only be
            # counted as a ceiling on what this tool can see.
            unresolved += 1
            continue
        s = stats[pub]
        s["articles"] += 1
        if (classes.get(str(art.get("source", ""))) or {}).get("kind") == "query":
            s["viaquery"] += 1
        try:
            score = score_article(art, scoring)[0]
        except Exception:
            score = 0.0
        if score >= threshold:
            s["surfaced"] += 1
        if req:
            cov = requirement_coverage(art, req, scoring,
                                       detectable=detectable,
                                       sensor_classes=classes)
            if cov["sirs_met"]:
                s["answered"] += 1

    def rank(items):
        return sorted(items, key=lambda kv: (-kv[1]["surfaced"],
                                             -kv[1]["answered"],
                                             -kv[1]["articles"], kv[0]))

    cands = [(h, s) for h, s in stats.items()
             if h not in declared and s["articles"] >= args.min_articles]
    already = [(h, s) for h, s in stats.items() if h in declared]

    print(f"CANDIDATES - publishers in the corpus that are NOT declared "
          f"sensors, ranked by how many of their articles would surface at "
          f"{threshold}:")
    print(f"  {'surfaced':>8}  {'answered':>8}  {'articles':>8}  "
          f"{'viaquery':>8}  publisher")
    shown = rank(cands)[:args.top]
    for h, s in shown:
        print(f"  {s['surfaced']:>8}  {s['answered']:>8}  "
              f"{s['articles']:>8}  {s['viaquery']:>8}  {h}")
    if not shown:
        print("  (none)")

    if args.declared:
        print()
        print("ALREADY DECLARED, for comparison:")
        print(f"  {'surfaced':>8}  {'answered':>8}  {'articles':>8}  "
              f"{'viaquery':>8}  publisher")
        for h, s in rank(already)[:args.top]:
            print(f"  {s['surfaced']:>8}  {s['answered']:>8}  "
                  f"{s['articles']:>8}  {s['viaquery']:>8}  {h}")

    print()
    would = sum(s["surfaced"] for _h, s in cands)
    print("CANDIDATES arts=" + str(len(arts))
          + " publishers=" + str(len(stats))
          + " undeclared=" + str(len(cands))
          + " their_surfacing_articles=" + str(would)
          + " unresolved_wrappers=" + str(unresolved)
          + " threshold=" + str(threshold))


def run_probe(args):
    """Try the common feed paths on one host. Network. Collection host only."""
    try:
        import feedparser
    except ImportError:
        raise SystemExit("--probe needs feedparser, which lives in the "
                         "collection host's venv. Run it there.")

    host = host_of(args.probe) or args.probe
    print(f"PROBING {host} - status and ITEM COUNT, because a 200 that serves "
          f"a webpage is not a feed. Packet Storm did exactly that:")
    best = None
    for p in FEED_PATHS:
        url = f"https://{host}{p}"
        status, items, title = "-", 0, ""
        try:
            d = feedparser.parse(url)
            status = str(getattr(d, "status", "-"))
            items = len(getattr(d, "entries", []) or [])
            title = str((getattr(d, "feed", {}) or {}).get("title", ""))[:44]
            if getattr(d, "bozo", 0) and not items:
                exc = getattr(d, "bozo_exception", None)
                status = type(exc).__name__ if exc else "malformed"
        except Exception as e:
            status = type(e).__name__
        print(f"  {status:>12}  items={items:<4}  {url}   {title}")
        if items and best is None:
            best = (url, items)
    print()
    if best:
        print(f"PROBE {host} BEST={best[0]} items={best[1]}")
    else:
        print(f"PROBE {host} BEST=none - no path returned feed items")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Find the next sensor from evidence already collected")
    ap.add_argument("--domain", default="cti")
    ap.add_argument("--pnd")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--min-articles", type=int, default=2)
    ap.add_argument("--declared", action="store_true")
    ap.add_argument("--corpus", help="read a corpus directory other than the "
                    "domain's own")
    ap.add_argument("--probe", help="one host to try the common feed paths on")
    args = ap.parse_args(argv)

    if args.probe:
        run_probe(args)
        return 0
    cfg = load_domain(domain=args.domain, pnd_path=args.pnd)
    run_list(args, cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
