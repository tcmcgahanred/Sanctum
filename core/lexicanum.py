#!/usr/bin/env python3
"""
Sanctum · core/lexicanum.py · the archive search engine

Searches everything Sanctum has ever collected, by keyword group or by an
ad-hoc term, and counts how often each term appears over time.

WHY THIS EXISTS
---------------
Sanctum scores each cycle independently and then forgets. It keeps every
article permanently but offers no way to ask the archive a question, so the
corpus has been a write-only store: the reason the operator retains everything
— trend — is the one thing the tooling could not do.

The workflow this replaces was manual: bulk keyword search across a pile of
documents, hits pasted into a spreadsheet with a column naming the term that
matched. The term was not a filter. It was an INDEX — a handle to pull later:
"show me everywhere this has appeared." That is question one. Question two
follows immediately: if the same subject keeps appearing, is it actually
SPREADING, or is one event simply being re-reported? Those call for different
responses, and both are the same feature. Search finds the items; counting them
per period turns them into a trend.

MATCHES ARE COMPUTED, NOT STORED
--------------------------------
Nothing about matching is written down at collection time. This engine re-runs
the live matcher over the stored articles on demand.

That is the design, not a shortcut. A stored index can only answer questions you
thought to ask on collection day. Because the full text is retained and the
matcher is deterministic, a group invented this morning can be run against
everything collected last year — including terms for a system nobody was
tracking when the articles arrived. An index cannot do that.

It also means results always agree with the scorer. Same matcher, same word
boundary rules, same scopes. There is no second implementation to drift.

WHICH DATE
----------
Series are bucketed by COLLECTION date, which is the corpus directory an article
sits in. Publication dates are missing or malformed often enough that the scorer
carries a whole recency gate to cope with it; bucketing on a field that is
frequently absent would produce a clean-looking chart built on guesses. Each hit
still shows its publication date, and `--by-published` will bucket on that
instead where you accept the gaps. Where collection is daily and continuous, the
two axes track closely.

WHAT IT DOES NOT DO
-------------------
It does not interpret. It reports counts and the items behind them; whether a
rise means proliferation, repositioning, or a single news cycle being loud is an
analyst's call (tenet 9). Every count is backed by a listable item, so no number
appears that you cannot drill into (tenet 8).

USAGE
    core/lexicanum.py <domain> --group ransom
    core/lexicanum.py <domain> --group ransom --group supplychain --by month
    core/lexicanum.py <domain> --term "emotet" --term "qakbot"
    core/lexicanum.py <domain> --all-groups --counts --by week
    core/lexicanum.py --pnd /path/to/pnd.md --group sector --since 2026-01-01
    core/lexicanum.py <domain> --all-groups --counts -o trend.md

EXIT CODES
    0  ran (including "no hits" — an empty answer is an answer)
    1  bad arguments, unknown group, or the corpus is unreadable
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pnd import load_domain          # noqa: E402
from core.rules import _scopes            # noqa: E402


# ------------------------------------------------------------------
# Matching
#
# The scorer's matcher answers "did anything in this group hit?" and stops at
# the first term. Search needs every term that hit, so that a per-term count is
# possible at all. Same rules, exhaustive instead of short-circuiting.
# ------------------------------------------------------------------
def make_all_hits(word_boundary_terms):
    wb = set(word_boundary_terms or [])

    def _all(text, terms):
        found = []
        for t in terms:
            t = t.strip()
            if not t:
                continue
            if len(t) <= 4 or t in wb:
                if re.search(r"\b" + re.escape(t) + r"\b", text):
                    found.append(t)
            elif t in text:
                found.append(t)
        return found

    return _all


# ------------------------------------------------------------------
# Corpus walk
# ------------------------------------------------------------------
def parse_day(name):
    try:
        return date.fromisoformat(name)
    except ValueError:
        return None


def walk_corpus(corpus_root, since=None, until=None):
    """Yield (collection_date, article) for the whole archive, oldest first."""
    if not corpus_root.exists():
        return
    for day_dir in sorted(corpus_root.iterdir()):
        if not day_dir.is_dir():
            continue
        day = parse_day(day_dir.name)
        if day is None:
            continue                       # not a dated run directory
        if since and day < since:
            continue
        if until and day > until:
            continue
        for jf in sorted(day_dir.glob("*.json")):
            try:
                yield day, json.loads(jf.read_text(encoding="utf-8"))
            except Exception:
                continue                   # a truncated file is not a reason to stop


def published_date(art):
    raw = str(art.get("published", "") or "")
    for fmt in (None, "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            if fmt is None:
                return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
            return datetime.strptime(raw, fmt).date()
        except Exception:
            continue
    return None


def bucket(d, by):
    if by == "day":
        return d.isoformat()
    if by == "week":
        iso = d.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"
    return f"{d.year}-{d.month:02d}"       # month


# ------------------------------------------------------------------
# Search
# ------------------------------------------------------------------
class Hit:
    def __init__(self, day, pub, group, terms, art):
        self.day = day
        self.pub = pub
        self.group = group
        self.terms = terms
        self.title = str(art.get("title", "") or "(no title)")
        self.url = str(art.get("url", "") or "")
        self.source = re.sub(r"^https?://(www\.)?", "", self.url).split("/")[0]


def search(cfg, targets, since, until, by, by_published):
    """
    `targets` is {label: [terms]}. Returns
    (hits, series, per_term, totals, scanned, undated).
      series    {label: {bucket: hit count}}
      per_term  {label: {term: count}}
      totals    {bucket: articles COLLECTED in that bucket}

    `totals` is the denominator, and it is the whole reason this function counts
    articles it found nothing in. Without it a period where less was collected
    looks exactly like a period where less happened. Measured on the first real
    run: ransomware hits fell 475 -> 122 week over week, which read as a
    collapse until the denominators showed 6,585 articles collected versus
    1,370 — the RATE had risen, 7.2% to 8.9%. Counts alone said the opposite of
    the truth.
    """
    scoring = cfg["scoring"]
    all_hits = make_all_hits(scoring.get("word_boundary_terms"))

    hits = []
    series = {label: defaultdict(int) for label in targets}
    per_term = {label: defaultdict(int) for label in targets}
    totals = defaultdict(int)
    scanned = 0
    undated = 0

    for day, art in walk_corpus(cfg["corpus_dir"], since, until):
        scanned += 1
        _, scopes, _ = _scopes(art)
        blob = scopes["blob"]
        pub = published_date(art)

        axis = pub if by_published else day
        if axis is None:
            undated += 1
            axis = day                     # fall back rather than discard

        b = bucket(axis, by)
        totals[b] += 1                     # counted whether or not anything hits

        for label, terms in targets.items():
            found = all_hits(blob, terms)
            if not found:
                continue
            hits.append(Hit(day, pub, label, found, art))
            series[label][b] += 1
            for t in found:
                per_term[label][t] += 1

    return hits, series, per_term, totals, scanned, undated


# ------------------------------------------------------------------
# Report
# ------------------------------------------------------------------
def render(cfg, targets, hits, series, per_term, totals, scanned, undated,
           by, by_published, counts_only, since, until):
    L = []
    dom = cfg["domain"]
    axis = "publication date" if by_published else "collection date"
    L.append(f"# Archive search — {dom}")
    L.append("")
    span = []
    if since:
        span.append(f"from {since.isoformat()}")
    if until:
        span.append(f"to {until.isoformat()}")
    L.append(f"*{scanned} article(s) searched{' ' + ' '.join(span) if span else ' — whole archive'} · "
             f"{len(hits)} hit(s) · bucketed by {by} on {axis}.*")
    if by_published and undated:
        L.append("")
        L.append(f"> **{undated} article(s) had no usable publication date** and were "
                 f"bucketed by collection date instead. Counts below are that far approximate.")
    L.append("")
    L.append("> **Read the rate, not the count.** Hits rise and fall with how much "
             "was collected, so the `of` column is the denominator and `rate` is "
             "the comparable number. The bar tracks rate for that reason. Even "
             "then, reporting volume is not activity — a quiet week for a "
             "publisher looks identical to a quiet week in the field.")
    L.append("")

    # Collection volume per period, stated once. Every rate below divides by it,
    # and an uneven row here explains most surprising-looking trends.
    if totals:
        L.append(f"**Articles collected per {by}:** " + " · ".join(
            f"{b} **{totals[b]}**" for b in sorted(totals)))
        L.append("")

    for label in targets:
        s = series[label]
        total = sum(s.values())
        L.append(f"## {label} — {total} hit(s)")
        L.append("")
        if not total:
            L.append("*No hits in the searched range.* A group that never matches is "
                     "either mistargeted or genuinely quiet; both are worth knowing.")
            L.append("")
            continue

        def rate(b):
            t = totals.get(b, 0)
            return (100.0 * s[b] / t) if t else 0.0

        L.append(f"| {by} | hits | of | rate | |")
        L.append("|---|---:|---:|---:|---|")
        peak_rate = max((rate(b) for b in s), default=0.0)
        for b in sorted(s):
            r = rate(b)
            bar = "█" * max(1, round(20 * r / peak_rate)) if peak_rate else ""
            L.append(f"| {b} | {s[b]} | {totals.get(b, 0)} | {r:.1f}% | {bar} |")
        L.append("")

        pt = per_term[label]
        if pt:
            L.append("**Terms that fired:** " + ", ".join(
                f"`{t}` ({n})" for t, n in
                sorted(pt.items(), key=lambda kv: (-kv[1], kv[0]))))
            L.append("")

        if counts_only:
            continue

        L.append("<details><summary>Items</summary>")
        L.append("")
        for h in sorted([x for x in hits if x.group == label],
                        key=lambda x: (x.day, x.title), reverse=True):
            pub = h.pub.isoformat() if h.pub else "pub date unknown"
            L.append(f"- **{h.day.isoformat()}** ({pub}) — {h.title} — {h.source}")
            L.append(f"  - matched: {', '.join(f'`{t}`' for t in h.terms)}")
            if h.url:
                L.append(f"  - {h.url}")
        L.append("")
        L.append("</details>")
        L.append("")

    return "\n".join(L)


# ------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Search the Sanctum archive by keyword group and count matches over time.")
    ap.add_argument("domain", nargs="?", help="domain name (omit if using --pnd)")
    ap.add_argument("--pnd", help="path to an out-of-tree domain file")
    ap.add_argument("--group", action="append", default=[],
                    help="a keyword group from the domain file (repeatable)")
    ap.add_argument("--all-groups", action="store_true", help="search every group")
    ap.add_argument("--term", action="append", default=[],
                    help="an ad-hoc term not in the domain file (repeatable)")
    ap.add_argument("--since", help="YYYY-MM-DD")
    ap.add_argument("--until", help="YYYY-MM-DD")
    ap.add_argument("--by", choices=("day", "week", "month"), default="week")
    ap.add_argument("--by-published", action="store_true",
                    help="bucket on publication date instead of collection date")
    ap.add_argument("--counts", action="store_true", help="series only, omit the item lists")
    ap.add_argument("-o", "--out", help="write to a file instead of stdout")
    args = ap.parse_args(argv)

    if not args.domain and not args.pnd:
        ap.error("give a domain name or --pnd")
    if not (args.group or args.all_groups or args.term):
        ap.error("nothing to search for — give --group, --all-groups or --term")

    def as_date(s, what):
        if not s:
            return None
        try:
            return date.fromisoformat(s)
        except ValueError:
            ap.error(f"--{what} must be YYYY-MM-DD, got {s!r}")

    since, until = as_date(args.since, "since"), as_date(args.until, "until")
    if since and until and since > until:
        ap.error("--since is after --until")

    try:
        cfg = load_domain(domain=args.domain, pnd_path=args.pnd)
    except Exception as e:
        print(f"lexicanum: cannot load domain: {e}", file=sys.stderr)
        return 1

    groups = cfg["scoring"]["groups"]
    targets = {}
    if args.all_groups:
        targets.update({g: list(t) for g, t in groups.items()})
    for g in args.group:
        if g not in groups:
            print(f"lexicanum: no group named '{g}'. Available: "
                  f"{', '.join(sorted(groups))}", file=sys.stderr)
            return 1
        targets[g] = list(groups[g])
    if args.term:
        targets["ad-hoc"] = list(args.term)

    if not cfg["corpus_dir"].exists():
        print(f"lexicanum: no corpus at {cfg['corpus_dir']} — nothing collected yet, "
              f"or SANCTUM_BASE points somewhere else", file=sys.stderr)
        return 1

    hits, series, per_term, totals, scanned, undated = search(
        cfg, targets, since, until, args.by, args.by_published)

    report = render(cfg, targets, hits, series, per_term, totals, scanned, undated,
                    args.by, args.by_published, args.counts, since, until)

    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(report, encoding="utf-8")
        print(f"[{cfg['domain']}] {scanned} searched, {len(hits)} hit(s) -> {p}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
