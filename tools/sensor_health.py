#!/usr/bin/env python3
# Sanctum · tools/sensor_health.py · diagnostic; history via git
"""
Sensor health — which feeds are working, and which are buying reassurance.

WHY. On 2026-08-25 four sensors were found to have been producing nothing
usable for weeks: news.google.com, msrc.microsoft.com, darkreading.com and
industrialcyber.co, 169 items between them, all unusable, none noticed. They
went unnoticed because at 56 sensors nobody can watch 56 sensors by eye.

Tenet 6 says coverage emerges from good sensors well-operated, not from piling
on feeds. This is the instrument that makes "well-operated" checkable. It
reads what the apparatus already records — the collector log and the corpus —
and adds no new store, because the 2026-08-11 lesson still stands: read what
production already records before building a tool.

    tools/sensor_health.py --domain cti
    ... --days 30            corpus window for the contribution section
    ... --log-only           skip the corpus pass (fast)

TWO SECTIONS, TWO QUESTIONS.

  YIELD          from the collector log. Is this feed alive, and is what it
                 returns usable? A feed with items but no bodies is broken in
                 a way a liveness check cannot see.

  CONTRIBUTION   from the corpus. Has this feed ever been the ONLY source of
                 something that surfaced? A feed that has never been the sole
                 source of a surfaced item is not buying coverage — it is
                 buying reassurance. That is a real thing to buy, and worth
                 knowing which feeds you are paying for it with.

Contribution reuses the scorer and the near-duplicate grouping, so "the same
story from four outlets" counts once and the sole source of it is identified.

CHANGES NOTHING. No writes, no network.
"""

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.arbites import group_near_duplicates                     # noqa: E402
from core.pnd import load_domain                                   # noqa: E402
from core.rules import score_article                               # noqa: E402

# Both log formats: the pre-2026-08-25 one and the tallied one that replaced it.
RE_NEW = re.compile(r"(https?://\S+) -> (\d+) new")
RE_TALLY = re.compile(r"(https?://\S+) -> (\d+) new, (\d+) too old, "
                      r"(\d+) no body, (\d+) undated")
RE_RUN = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def host(u):
    return re.sub(r"^https?://(www\.)?", "", str(u)).split("/")[0]


def short(u, n=44):
    u = re.sub(r"^https?://(www\.)?", "", str(u))
    return u if len(u) <= n else "…" + u[-(n - 1):]


def read_log(path):
    """Per-sensor totals and the set of run days each was seen in."""
    stats = defaultdict(lambda: {"runs": set(), "new": 0, "too_old": 0,
                                 "no_body": 0, "last_new": None})
    if not Path(path).exists():
        return stats, 0
    day = "?"
    runs = set()
    for line in open(path, encoding="utf-8", errors="replace"):
        m = RE_RUN.match(line)
        if m:
            day = m.group(1)
        t = RE_TALLY.search(line)
        if t:
            url, new, too_old, no_body = t.group(1), int(t.group(2)), int(t.group(3)), int(t.group(4))
        else:
            n = RE_NEW.search(line)
            if not n:
                continue
            url, new, too_old, no_body = n.group(1), int(n.group(2)), 0, 0
        s = stats[url]
        s["runs"].add(day)
        s["new"] += new
        s["too_old"] += too_old
        s["no_body"] += no_body
        if new:
            s["last_new"] = day
        runs.add(day)
    return stats, len(runs)


def main():
    ap = argparse.ArgumentParser(description="Sanctum sensor health (read-only)")
    ap.add_argument("--domain", default="cti")
    ap.add_argument("--pnd")
    ap.add_argument("--days", type=int, default=30,
                    help="corpus window for the contribution section")
    ap.add_argument("--log-only", action="store_true")
    args = ap.parse_args()

    cfg = load_domain(domain=args.domain, pnd_path=args.pnd)
    scoring = cfg["scoring"]
    threshold = float(scoring.get("settings", {}).get("surface_min_score", 2.0))
    sensors = list(cfg["sensors"])

    # ---------------------------------------------------------------- yield
    stats, run_count = read_log(cfg["log_path"])
    print("=== YIELD — from %s, %d run(s) recorded ===\n" % (cfg["log_path"], run_count))
    if not run_count:
        print("No collector log yet. Run a cycle first.\n")
    else:
        print("%-46s %6s %7s %8s %8s  %s"
              % ("sensor", "runs", "new", "too old", "no body", "last new"))
        print("-" * 96)
        rows = []
        for u in sensors:
            s = stats.get(u)
            rows.append((u, s["new"] if s else 0, s))
        for u, _n, s in sorted(rows, key=lambda r: (r[1], r[0])):
            if s is None:
                print("%-46s %6s %7s %8s %8s  %s"
                      % (short(u), "-", "-", "-", "-", "NEVER IN THE LOG"))
                continue
            flag = ""
            if s["new"] == 0:
                flag = "  <- no item, ever"
            elif s["no_body"] and s["no_body"] >= s["new"]:
                flag = "  <- every item unusable"
            print("%-46s %6d %7d %8d %8d  %s%s"
                  % (short(u), len(s["runs"]), s["new"], s["too_old"],
                     s["no_body"], s["last_new"] or "never", flag))
        orphans = [u for u in stats if u not in set(sensors)]
        if orphans:
            print("\nIn the log but no longer configured (%d): %s"
                  % (len(orphans), ", ".join(short(u, 30) for u in orphans[:6])))

    if args.log_only:
        return

    # --------------------------------------------------------- contribution
    cut = datetime.now(timezone.utc) - timedelta(days=args.days)
    arts = []
    for f in glob.glob(os.path.join(str(cfg["corpus_dir"]), "*", "*.json")):
        try:
            a = json.loads(open(f, encoding="utf-8").read())
        except Exception:
            continue
        try:
            c = datetime.fromisoformat(str(a.get("collected", "")))
            c = c if c.tzinfo else c.replace(tzinfo=timezone.utc)
        except Exception:
            c = None
        if c is None or c >= cut:
            arts.append(a)

    # EVERY article is scored and passed to the grouper, not just the surfaced
    # ones. Similarity is IDF-weighted, so the corpus IS the denominator: hand
    # it five articles and a word shared by four of them carries zero
    # information and nothing groups. Feeding it only the surface produced
    # four separate "events" from four outlets covering one incident. Match
    # what arbites does exactly — score all, surfaced block first, then group.
    scored = []
    for a in arts:
        s, tier, reasons = score_article(a, scoring)
        scored.append((s, tier, reasons, a, False, s >= threshold))
    scored.sort(key=lambda x: (not x[5], -x[0], str(x[3].get("title", "")),
                               str(x[3].get("url", ""))))
    surfaced_n = sum(1 for x in scored if x[5])

    seps = tuple(cfg["manifest"].get("collection", {}).get(
        "suffix_separators", (" - ", " | ", " — ")))
    groups, grouped, _dissolved = group_near_duplicates(
        scored, scoring.get("settings", {}), seps)

    # One entry per distinct SURFACED event: a head plus anything nested under
    # it. Group members below the cut still count as coverage — another sensor
    # carried the story, it just scored lower there.
    events = []
    for i in range(surfaced_n):
        if i in grouped and i not in groups:
            continue
        members = [i] + list(groups.get(i, []))
        events.append({host(scored[m][3].get("source", "") or scored[m][3].get("url", ""))
                       for m in members})

    sole, shared = defaultdict(int), defaultdict(int)
    for hosts in events:
        if len(hosts) == 1:
            sole[next(iter(hosts))] += 1
        else:
            for h in hosts:
                shared[h] += 1

    print("\n\n=== CONTRIBUTION — last %d days, %d items scored, %d surfaced, "
          "%d distinct events ===\n" % (args.days, len(arts), surfaced_n, len(events)))
    print("SOLE SOURCE means no other sensor carried that event. A feed with a")
    print("zero here is not buying coverage — it is buying reassurance.\n")
    print("%-40s %12s %10s" % ("sensor host", "SOLE SOURCE", "also-ran"))
    print("-" * 66)
    seen_hosts = set(sole) | set(shared)
    for h in sorted(seen_hosts, key=lambda x: (-sole[x], -shared[x], x)):
        mark = "   <- never the only source" if sole[h] == 0 else ""
        print("%-40s %12d %10d%s" % (h[:40], sole[h], shared[h], mark))

    configured_hosts = {host(u) for u in sensors}
    silent = sorted(configured_hosts - seen_hosts)
    if silent:
        print("\nConfigured but contributed NOTHING that surfaced in %d days (%d):"
              % (args.days, len(silent)))
        for h in silent:
            print("  %s" % h)
    print("\nA sensor is not judged on one window. Read this across several")
    print("cycles before pruning anything, and prefer removing a feed that is")
    print("both silent AND unusable over one that is merely quiet.")


if __name__ == "__main__":
    main()
