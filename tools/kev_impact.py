#!/usr/bin/env python3
# Sanctum · tools/kev_impact.py · diagnostic; history via git
"""
What would reading the KEV catalogue actually change?

WHY. The scoring model raises a score by 1.5x for "KEV / actively exploited",
decided by matching phrases in prose. CISA publishes the catalogue as JSON, so
that phrase-matching is an inference standing in for a fact that can simply be
read. Replacing it is a Planning & Direction decision, and P&D should have a
number rather than an argument.

    tools/kev_impact.py --domain cti
    ... --days 30       corpus window (default 30)
    ... --refresh       force a catalogue refetch

WHAT IT MEASURES, against the real corpus:

  AGREE        the word group fired AND a CVE in the article is on the
               catalogue. The current rule got it right.
  MISSED       a CVE in the article IS on the catalogue but the word group
               did not fire. **The multiplier was owed and not paid.** These
               are the items the change would newly elevate.
  OVERCLAIMED  the word group fired but no CVE in the article is on the
               catalogue. Either the article names no CVE at all, or it uses
               exploitation language about something not catalogued. Not
               automatically wrong — but it is the rule being generous.
  NEITHER      no exploitation claim and nothing catalogued. Uninteresting.

Then it re-scores every MISSED item with the multiplier applied, and reports
how many would cross the surfacing threshold. That last number is the decision:
it is what the change buys in items the analyst would actually see.

CHANGES NOTHING in the repo or corpus. It does fetch and cache the catalogue.
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pnd import load_domain                                   # noqa: E402
from core.reflist import fetch, keys_in_article                    # noqa: E402
from core.rules import make_matcher, score_article                 # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="KEV impact report (read-only)")
    ap.add_argument("--domain", default="cti")
    ap.add_argument("--pnd")
    ap.add_argument("--list", default="kev", help="reference list name")
    ap.add_argument("--group", default="kev", help="word group it would replace")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--multiplier", type=float, default=1.5)
    args = ap.parse_args()

    cfg = load_domain(domain=args.domain, pnd_path=args.pnd)
    scoring = cfg["scoring"]
    threshold = float(scoring.get("settings", {}).get("surface_min_score", 2.0))
    spec = (cfg["manifest"].get("reference_lists", {}) or {}).get(args.list)
    if not spec:
        raise SystemExit("no reference list %r declared in the manifest" % args.list)

    keys, note = fetch(args.list, spec, cfg["base_dir"], force=args.refresh)
    print("reference list %r: %d entries (%s)\n" % (args.list, len(keys), note))
    if not keys:
        raise SystemExit("empty list — nothing to measure")

    words = scoring.get("groups", {}).get(args.group, []) or []
    matcher = make_matcher(scoring.get("word_boundary_terms"))
    print("word group %r: %d terms it currently relies on\n" % (args.group, len(words)))

    cut = datetime.now(timezone.utc) - timedelta(days=args.days)
    buckets = {"AGREE": [], "MISSED": [], "OVERCLAIMED": [], "NEITHER": 0}
    total = 0
    for f in glob.glob(os.path.join(str(cfg["corpus_dir"]), "*", "*.json")):
        try:
            art = json.loads(open(f, encoding="utf-8").read())
        except Exception:
            continue
        try:
            c = datetime.fromisoformat(str(art.get("collected", "")))
            c = c if c.tzinfo else c.replace(tzinfo=timezone.utc)
            if c < cut:
                continue
        except Exception:
            pass
        total += 1

        blob = f"{art.get('title','')} {art.get('text','')}".lower()
        said = matcher(blob, words) is not None
        found = keys_in_article(art, spec)
        listed = sorted(found & keys)

        score, _tier, _reasons = score_article(art, scoring)
        row = (score, art.get("title", "(no title)"), art.get("url", ""), listed)
        if said and listed:
            buckets["AGREE"].append(row)
        elif listed:
            buckets["MISSED"].append(row)
        elif said:
            buckets["OVERCLAIMED"].append(row)
        else:
            buckets["NEITHER"] += 1

    print("=== %d items in the last %d days ===\n" % (total, args.days))
    print("  AGREE        %5d   the word group and the catalogue concur"
          % len(buckets["AGREE"]))
    print("  MISSED       %5d   catalogued, but the word group stayed silent"
          % len(buckets["MISSED"]))
    print("  OVERCLAIMED  %5d   word group fired, nothing catalogued in the article"
          % len(buckets["OVERCLAIMED"]))
    print("  NEITHER      %5d" % buckets["NEITHER"])

    newly = [r for r in buckets["MISSED"]
             if r[0] < threshold <= r[0] * args.multiplier]
    print("\n=== the decision ===\n")
    print("Applying x%.1f to the MISSED set would newly surface %d item(s) "
          "(threshold %.1f)." % (args.multiplier, len(newly), threshold))
    if newly:
        print()
        for score, title, url, listed in sorted(newly, key=lambda r: -r[0])[:25]:
            print("  %.2f -> %.2f  %s" % (score, score * args.multiplier, title[:66]))
            print("                %s  [%s]" % (url[:70], ", ".join(listed[:3])))

    if buckets["OVERCLAIMED"]:
        print("\n=== a sample of OVERCLAIMED, to judge whether the word group ===")
        print("=== is being useful or merely loud                          ===\n")
        for score, title, url, _l in sorted(buckets["OVERCLAIMED"],
                                            key=lambda r: -r[0])[:10]:
            print("  %.2f  %s" % (score, title[:72]))

    print("\nRead it this way: MISSED is what the change buys. OVERCLAIMED is")
    print("what you would lose if the catalogue REPLACED the word group rather")
    print("than joining it — an article can describe real exploitation before")
    print("CISA catalogues it, and the wording is the only signal there is.")


if __name__ == "__main__":
    main()
