#!/usr/bin/env python3
"""
Before/after re-score against the REAL corpus, for a scoring-config change.

tests/diff_scores.py proves the rules do what a work order asked, on fixtures.
This proves it on the articles that caused the complaint. Two runs have now
caught defects the suite reported PASS on - a padding bug that fired
force-surface M1 on 190 unrelated articles, and two must-surface items whose
real headlines used words the fixtures did not. RUN IT BEFORE EVERY SCORING
COMMIT, on the collector host, where the corpus is.

    python3 tools/rescore_check.py --domain cti --old <old-pnd.md> [--limit 40]
    git show HEAD:cti/pnd.yaml > /tmp/pnd_old.yaml   # or pnd.md on a split domain

Reports: surfaced counts before and after; what STOPPED surfacing; what STARTED
(a long list means something was loosened by accident); and per-feed removal
rates, where a feed far above the others is a sensor question, not a scoring one.

Nothing is written. This reads the corpus and prints.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.pnd import load_domain                                         # noqa: E402
from core.rules import score_article, make_matcher, _eval_atom, _scopes  # noqa: E402
from core.arbites import load_window, source_name                        # noqa: E402


def evaluate(art, scoring):
    s, tier, reasons = score_article(art, scoring)
    groups = scoring["groups"]
    matcher = make_matcher(scoring.get("word_boundary_terms"))
    _t, scopes, text_l = _scopes(art)
    forced = None
    for rule in scoring.get("force_surface", []) or []:
        if _eval_atom(rule["when"], groups, matcher, scopes, text_l):
            forced = rule.get("name", "force")
            break
    thresh = scoring["settings"].get("surface_min_score")
    thresh = float(thresh) if thresh is not None else 0.0
    return s, tier, reasons, forced, bool(s >= thresh or forced)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="cti")
    ap.add_argument("--old", required=True, help="path to the PREVIOUS domain file (pnd.yaml or pnd.md)")
    ap.add_argument("--new", help="path to the new domain file (default: the domain's)")
    ap.add_argument("--limit", type=int, default=40, help="rows to print per list")
    ap.add_argument("--grep", help="only show rows whose feed or title contains this")
    a = ap.parse_args()

    new_cfg = load_domain(pnd_path=a.new) if a.new else load_domain(domain=a.domain)
    old_cfg = load_domain(pnd_path=a.old)
    window_days = int(new_cfg["manifest"].get("collection", {}).get("window_days", 7))
    arts = load_window(new_cfg["corpus_dir"], window_days)
    print("corpus window: %dd - %d articles\n" % (window_days, len(arts)))

    stopped, started, rows = [], [], []
    for art in arts:
        os_, ot, _or, _of, osurf = evaluate(art, old_cfg["scoring"])
        ns_, nt, nr, nf, nsurf = evaluate(art, new_cfg["scoring"])
        rows.append((osurf, nsurf))
        if osurf and not nsurf:
            stopped.append((os_ - ns_, os_, ns_, ot, nt, art))
        elif nsurf and not osurf:
            started.append((ns_ - os_, os_, ns_, ot, nt, art, nr, nf))

    before = sum(1 for o, _n in rows if o)
    after = sum(1 for _o, n in rows if n)
    print("surfaced BEFORE : %d" % before)
    print("surfaced AFTER  : %d" % after)
    print("net change      : %+d   (%d stopped, %d started)\n"
          % (after - before, len(stopped), len(started)))

    def keep(art):
        if not a.grep:
            return True
        g = a.grep.lower()
        return g in source_name(art.get("url", "")).lower() or g in art.get("title", "").lower()

    stopped.sort(reverse=True, key=lambda r: r[0])
    print("--- stopped surfacing (top %d by score drop) ---" % a.limit)
    for _d, os_, ns_, ot, nt, art in [r for r in stopped if keep(r[5])][:a.limit]:
        print("  %6s -> %-6s T%s->T%s  %-22s %s"
              % (os_, ns_, ot, nt, source_name(art.get("url", ""))[:22], art.get("title", "")[:70]))

    started.sort(reverse=True, key=lambda r: r[0])
    print("\n--- started surfacing (top %d by score rise) ---" % a.limit)
    shown = [r for r in started if keep(r[5])][:a.limit]
    if not shown:
        print("  none")
    for _r, os_, ns_, ot, nt, art, nr, nf in shown:
        tag = " [%s]" % nf if nf else ""
        print("  %6s -> %-6s T%s->T%s  %-22s %s%s"
              % (os_, ns_, ot, nt, source_name(art.get("url", ""))[:22],
                 art.get("title", "")[:60], tag))
        for r in nr:
            print("          - %s" % r)

    print("\n--- which feeds the removals came from ---")
    tot = Counter(source_name(art.get("url", "")) for art in arts)
    rem = Counter(source_name(r[5].get("url", "")) for r in stopped)
    print("  %-32s %7s %9s %13s" % ("feed", "removed", "in corpus", "removal rate"))
    for feed, n in rem.most_common():
        t = tot.get(feed, 0) or 1
        print("  %-32s %7d %9d %11d%%" % (feed[:32], n, tot.get(feed, 0), round(100.0 * n / t)))
    print("\n  A feed whose removal rate sits far above the others is producing a"
          "\n  disproportionate share of the false positives. That is a sensor"
          "\n  question, not a scoring one - take it to Planning & Direction.")


if __name__ == "__main__":
    main()
