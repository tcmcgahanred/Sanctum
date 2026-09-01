#!/usr/bin/env python3
"""
Sanctum · tests/handover_test.py

Proves the 2026-08-26 requirement handover — the evidence stage 3a computes and
must pass to stage 3b, because 3b cannot re-derive it.

WHY THIS EXISTS
---------------
The four scoring tiers and the four priority requirements in `requirements.md`
were the same four things and always had been. Nothing said so. `core/rules.py`
computed the tier on every scoring pass, `core/arbites.py` carried it through
the entire staging build, and neither ever printed it — the one number tying an
item to an intelligence requirement was calculated and discarded. Multiplier
reasons named their factor and never the words that fired, so half the evidence
behind a score was invisible.

None of that is recoverable downstream. An analyst reading the staging document
cannot work out which requirement an item answered, because the answer was never
written down. **3a's job is not only to decide what surfaces. It is to hand 3b
everything 3b cannot re-derive.**

WHAT IS CHECKED
---------------
  serves declared      a tier that declares one reports it, with its own name
  serves absent        a tier that declares none reports nothing, silently —
                       an undeclared domain is not a broken domain, and s2 is
                       git-ignored so it cannot be edited from the repo at all
  multiplier evidence  a fired multiplier names the term that fired it
  floor evidence       the same, for a floor
  evidence is display  none of it moves a score
  signature unchanged  score_article still returns exactly three values, because
                       eleven call sites across seven files unpack it

    tests/handover_test.py        # exit 0 = the handover holds
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.rules import (score_article, matched_evidence,      # noqa: E402
                        tier_requirement)

FAILURES = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
    if not ok:
        print(f"        got:  {got!r}")
        print(f"        want: {want!r}")
        FAILURES.append(label)


def scoring(tiers=None, multipliers=None, floors=None):
    """A minimal domain: one real group, one always-tier, nothing clever."""
    return {
        "groups": {"alpha": ["red widget"], "beta": ["blue gadget"]},
        "word_boundary_terms": [],
        "tiers": tiers if tiers is not None else [
            {"id": 1, "name": "the high one", "serves": "PIR-1",
             "weight": 8.0, "require": {"group": "alpha"}},
            {"id": 4, "name": "the floor", "serves": "PIR-4",
             "weight": 1.0, "require": "always"},
        ],
        "multipliers": multipliers or [],
        "floors": floors or [],
    }


def art(title="", text=""):
    return {"title": title, "text": text,
            "url": "https://example.test/x", "source": "https://example.test/f"}


def run():
    print("\nA tier reports the requirement it answers")
    sc = scoring()
    check("a declared tier reports its identifier and its own name",
          tier_requirement(1, sc), ("PIR-1", "the high one"))
    check("a tier id that does not exist reports nothing",
          tier_requirement(99, sc), None)

    # The important one. s2 is git-ignored and cannot be edited from the repo,
    # so a domain WILL run without this field. Printing "Requirement met: None"
    # on every candidate would be worse than printing nothing at all.
    print("\nAn undeclared domain stays silent — it is not a broken domain")
    bare = scoring(tiers=[{"id": 1, "name": "unnamed", "weight": 8.0,
                           "require": "always"}])
    check("a tier with no serves reports nothing", tier_requirement(1, bare), None)
    check("...and still scores exactly as before",
          score_article(art("anything"), bare)[0], 8.0)

    print("\nA multiplier names the word that fired it")
    mult = scoring(multipliers=[{"name": "gadget bump", "factor": 1.5,
                                 "when": {"group": "beta"}}])
    s, tier, reasons = score_article(art("red widget", "a blue gadget appeared"), mult)
    fired = [r for r in reasons if r.startswith("x1.5")]
    check("the multiplier fired", len(fired), 1)
    check("...and its reason names the term, not just the factor",
          "blue gadget" in fired[0], True)
    check("...and the score is the tier times the factor", s, 12.0)

    # An unfired multiplier must not appear at all. A reason naming a match that
    # did not happen sends the analyst to check the wrong thing.
    s2_, _t, reasons2 = score_article(art("red widget", "nothing else here"), mult)
    check("an unfired multiplier contributes no reason",
          [r for r in reasons2 if r.startswith("x1.5")], [])
    check("...and no score", s2_, 8.0)

    print("\nA floor names its evidence too")
    fl = scoring(floors=[{"name": "gadget floor", "score": 5.0,
                          "when": {"group": "beta"}}])
    s3, _t, reasons3 = score_article(art("nothing", "a blue gadget"), fl)
    floors_fired = [r for r in reasons3 if r.startswith("floor")]
    check("the floor fired and named its term",
          bool(floors_fired) and "blue gadget" in floors_fired[0], True)
    check("...and raised the score to the floor", s3, 5.0)

    print("\nVocabulary present — the handle for refinement, not the score")
    ev = matched_evidence(art("red widget", "and a blue gadget"), sc)
    check("every group present is reported",
          sorted(ev), ["alpha", "beta"])
    check("...with the term that matched",
          [ev["alpha"], ev["beta"]], ["red widget", "blue gadget"])
    check("a group that is absent is not reported",
          sorted(matched_evidence(art("red widget"), sc)), ["alpha"])
    check("an article matching nothing yields nothing",
          matched_evidence(art("unrelated"), sc), {})

    # beta decides no tier in `sc`, yet it is reported. That is deliberate: the
    # line is labelled "vocabulary present", not "terms fired", and it exists so
    # a term can be traced even when it contributed nothing this time.
    check("a group that decided nothing is still reported as present",
          "beta" in matched_evidence(art("red widget", "a blue gadget"), sc), True)

    print("\nNone of this moves a score, and no caller breaks")
    before = score_article(art("red widget", "a blue gadget"), sc)
    check("scoring an article twice is stable", before,
          score_article(art("red widget", "a blue gadget"), sc))
    check("score_article still returns exactly three values", len(before), 3)
    check("...score, tier, reasons — in that order",
          [type(before[0]).__name__, type(before[1]).__name__,
           type(before[2]).__name__],
          ["float", "int", "list"])

    print()
    if FAILURES:
        print(f"FAIL — {len(FAILURES)} problem(s)")
        for f in FAILURES:
            print(f"    {f}")
        return 1
    print("PASS — the requirement reaches the staging document, an undeclared "
          "domain stays silent, and no score moved")
    return 0


if __name__ == "__main__":
    sys.exit(run())
