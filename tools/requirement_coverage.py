#!/usr/bin/env python3
# Sanctum · tools/requirement_coverage.py · diagnostic; history via git
"""
Which intelligence requirements does the corpus actually answer?

WHY. The requirements tree names 27 specific information requirements. Until
now nothing could say how many of them the collection actually satisfies, so
"we have a collection gap" was an assertion. This makes it a count.

    tools/requirement_coverage.py --domain cti
    ... --days 7           corpus window in days (default 7, one cycle)
    ... --surfaced-only    count only items that clear surface_min_score
    ... --sir SIR-5.1.1    show matching titles for one requirement
    ... --corpus DIR       read a corpus copy instead of the live one

A rule's `logsource:` is the FIRST filter, before any term is matched, the
way it is in Sigma. A rule that needs a breach registry does not read press.
An article whose sensor is no longer in the manifest cannot be matched by any
rule that declares a logsource, and the count of those is printed.

WHAT IT REPORTS

  Per requirement, over the window:
      MET n       n articles satisfied it
      NONE        it can be tested and nothing matched. A real gap in the
                  reporting, or a detector that is too narrow.
      no source   it has a detector, but its `logsource:` matches NO sensor in
                  the manifest, so nothing it could read is ever collected.
                  This reads identically to NONE and means the opposite: not a
                  quiet month, an impossible one. Four rules were in this
                  state the morning the logsource filter shipped.
      no detector nothing can test it. No `detection:` block on the
                  requirement and no scoring rule names it in `serves_sir:`.
                  This is a BUILD gap, not a quiet week, and the two must not
                  be added together. A rule with `status: blocked` lands here
                  and says in `blocked_by:` what it is waiting for.

  Per indicator, the state across the window: satisfied, needs_detector,
  unsatisfied, or no_detector. `satisfied_by: all` means every requirement
  under it must be met; `any` means one is enough.

CHANGES NOTHING. No writes, no network. Safe to run mid-cycle.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.pnd import load_domain                                    # noqa: E402
from core.rules import (detectable_requirements, logsource_match,  # noqa: E402
                        requirement_coverage, satisfied_elements,
                        score_article)


def load(corpus_dir, days):
    cut = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    root = Path(corpus_dir)
    if not root.exists():
        raise SystemExit(f"no corpus at {root}")
    for day in sorted(root.iterdir()):
        if not day.is_dir():
            continue
        for jf in day.glob("*.json"):
            try:
                art = json.loads(jf.read_text(encoding="utf-8"))
            except Exception:
                continue
            # On any doubt about the date, KEEP. Rounding up is the same
            # choice core/arbites.py makes, and for the same reason: an
            # unreadable timestamp is not evidence the article is old.
            try:
                c = datetime.fromisoformat(str(art.get("collected", "")))
                c = c if c.tzinfo else c.replace(tzinfo=timezone.utc)
                if c < cut:
                    continue
            except Exception:
                pass
            out.append(art)
    return out


def main():
    ap = argparse.ArgumentParser(description="requirement coverage (read-only)")
    ap.add_argument("--domain", default="cti")
    ap.add_argument("--pnd")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--surfaced-only", action="store_true")
    ap.add_argument("--sir", help="show matching titles for one requirement")
    ap.add_argument("--corpus", help="read a corpus directory other than the "
                    "domain's own (for testing against a copy)")
    args = ap.parse_args()

    cfg = load_domain(domain=args.domain, pnd_path=args.pnd)
    scoring = cfg["scoring"]
    req = cfg.get("requirements") or {}
    if not req.get("pirs"):
        raise SystemExit(f"[{args.domain}] declares no requirements tree")

    threshold = float(scoring.get("settings", {}).get("surface_min_score", 2.0))
    detectable = detectable_requirements(req, scoring)
    classes = cfg.get("sensor_classes") or {}

    corpus = args.corpus or cfg["corpus_dir"]
    arts = load(corpus, args.days)
    print(f"corpus window: {args.days} day(s), {len(arts)} article(s) "
          f"from {corpus}")
    if args.surfaced_only:
        arts = [a for a in arts if score_article(a, scoring)[0] >= threshold]
        print(f"surfaced only: {len(arts)} at or above {threshold}")
    print()

    # How many articles came from a sensor the manifest no longer lists. A
    # rule with a logsource cannot read those, so the number has to be visible
    # rather than absorbed into the misses.
    unknown = sum(1 for a in arts if str(a.get("source", "")) not in classes)
    print(f"sensor classes: {len(classes)} sensors classified; "
          f"{unknown} article(s) in this window came from a source the "
          f"manifest no longer lists\n")

    met = {}
    examples = {}
    ind_states = {}
    for art in arts:
        cov = requirement_coverage(art, req, scoring, detectable=detectable,
                                   sensor_classes=classes)
        for sid in cov["sirs_met"]:
            met[sid] = met.get(sid, 0) + 1
            if args.sir and sid == args.sir:
                examples.setdefault(sid, []).append(art.get("title", "(untitled)"))
        for iid, state in cov["indicators"].items():
            rank = {"satisfied": 3, "needs_detector": 2,
                    "unsatisfied": 1, "no_detector": 0}
            if rank[state] > rank.get(ind_states.get(iid, "no_detector"), 0):
                ind_states[iid] = state

    counts = {"MET": 0, "NONE": 0, "no source": 0, "no detector": 0}
    for pir in req["pirs"]:
        head = f"{pir['id']}  {pir.get('name', '')}"
        if pir.get("status") == "DRAFT":
            head += "   [DRAFT]"
        print(head)
        for ind in pir.get("indicators", []) or []:
            state = ind_states.get(ind["id"], "no_detector")
            print(f"    {ind['id']}  [{ind.get('satisfied_by')}]  {state.upper()}")
            print(f"        {ind.get('statement', '')}")
            for sir in ind.get("sirs", []) or []:
                sid = sir["id"]
                # A REQUIREMENT NOTHING COLLECTS FOR IS NOT A QUIET MONTH.
                # Counting the sensors a logsource matches is what separates
                # the two, and it is one line because both sides declare the
                # same two axes.
                nsens = (sum(1 for v in (classes or {}).values()
                             if logsource_match(sir.get("logsource"), v))
                         if sir.get("logsource") else len(classes or {}))
                if sid not in detectable:
                    verdict, key = "no detector", "no detector"
                elif not nsens:
                    verdict, key = "no source", "no source"
                elif met.get(sid):
                    verdict, key = f"MET {met[sid]}", "MET"
                else:
                    verdict, key = "NONE", "NONE"
                counts[key] += 1
                how = "detect" if sir.get("detection") is not None else (
                    "rule" if sid in detectable else "-")
                ls = sir.get("logsource") or {}
                src = (f"{ls.get('scope', '-')}/{ls.get('kind', '-')}"
                       if ls else "-")
                print(f"          {sid:<12} {verdict:<12} via {how:<7} "
                      f"{src:<28} {sir.get('fact', '')[:44]}")
        print()

    total = sum(counts.values())
    print(f"{total} requirement(s): {counts['MET']} met, {counts['NONE']} "
          f"testable but unmatched, {counts['no source']} with no source, "
          f"{counts['no detector']} with no detector")

    if args.sir:
        titles = examples.get(args.sir, [])
        print(f"\n{args.sir}: {len(titles)} matching article(s)")
        for tl in titles[:40]:
            print("   ", str(tl)[:110])

    # THE NUMBER THAT MATTERS is on the last line, because that is the one
    # that gets pasted back.
    print(f"\ncoverage: {counts['MET']}/{counts['MET'] + counts['NONE']} "
          f"testable requirement(s) answered this window")
    return 0


if __name__ == "__main__":
    sys.exit(main())
