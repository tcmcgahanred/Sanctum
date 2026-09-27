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
                       an undeclared domain is younger, not broken, and s2 is
                       the standing example: it scores daily and declares no
                       `serves:` field on any tier. The old reason given here
                       was that s2 was git-ignored, which stopped being true
                       at some point before 2026-09-27
  multiplier evidence  a fired multiplier names the term that fired it
  floor evidence       the same, for a floor
  evidence is display  none of it moves a score
  term is matchable    no declared term in either domain is unmatchable, which
                       is what 518 of s2's 951 terms were until case folding
  logsource reachable  no requirement declares a vantage no sensor supplies,
                       unless it is `unsupported` and the zero is the finding
  signature unchanged  score_article still returns exactly three values, because
                       eleven call sites across seven files unpack it

    tests/handover_test.py        # exit 0 = the handover holds
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pnd import load_domain                                # noqa: E402
from core.rules import (score_article, matched_evidence,      # noqa: E402
                        tier_requirement, satisfied_elements,
                        make_matcher, logsource_match)

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

    # The important one. A domain WILL run without this field - s2 scores daily
    # and has no requirements tree yet. Printing "Requirement met: None" on
    # every candidate would be worse than printing nothing at all.
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

    print("\nElements satisfied — only what a rule actually claims")
    ee = scoring()
    ee["tiers"][0]["serves_eei"] = ["EEI-1.2.a"]
    ee["multipliers"] = [{"name": "bump", "factor": 1.5,
                          "serves_eei": ["EEI-3.2.a"],
                          "when": {"group": "beta"}}]
    both = art("red widget", "a blue gadget")
    check("a fired tier and a fired multiplier both contribute",
          satisfied_elements(both, ee), ["EEI-1.2.a", "EEI-3.2.a"])
    # A rule that did not fire claims nothing. Naming an element that was not
    # satisfied sends the analyst to check the wrong thing.
    check("an unfired multiplier contributes nothing",
          satisfied_elements(art("red widget"), ee), ["EEI-1.2.a"])
    check("only the WINNING tier contributes, not every qualifying one",
          satisfied_elements(art("nothing here"), ee), [])
    # s2 declares none of this and must stay silent rather than print noise.
    check("a domain declaring no elements returns nothing",
          satisfied_elements(both, scoring()), [])
    check("...and declaring elements still moves no score",
          score_article(both, ee)[0], score_article(both, scoring())[0] * 1.5)

    # EVERY TRACKED DOMAIN MUST SCORE WITHOUT RAISING, and this is a regression
    # guard on a real outage. `s2`'s single force-surface rule was written with
    # `require:`, which is a TIER's field name; the engine reads `when:`. Every
    # run collected successfully, then `satisfied_elements` raised
    # KeyError('when') 28 seconds later and the service exited 1. The corpus kept
    # growing and the staging document silently stopped being rewritten. The
    # loader refuses it now; this checks the whole path end to end.
    print("\nEvery tracked domain scores without raising")
    probe = art("a probe headline with nothing special in it")
    for dom in ("cti", "s2"):
        try:
            live = load_domain(domain=dom)["scoring"]
            score_article(probe, live)
            satisfied_elements(probe, live)
            ok = True
        except Exception as e:
            ok = f"{type(e).__name__}: {e}"
        check(f"{dom} scores and reports its elements", ok, True)
        rules = [(k, r) for k in ("multipliers", "floors", "force_surface")
                 for r in (load_domain(domain=dom)["scoring"].get(k) or [])]
        check(f"...and every {dom} multiplier, floor and force rule states "
              f"`when:`",
              [f"{k}:{r.get('name')}" for k, r in rules if "when" not in r], [])

    # EVERY DECLARED TERM CAN MATCH SOMETHING. The engine lowercases every scope
    # it searches and used to compare the declared term to it verbatim, so a
    # term carrying a capital letter was inert. Measured 2026-09-27: 518 of s2's
    # 951 terms, 54.5 percent, including all 213 weapon designations. A term
    # nobody can ever hit is worse than a missing term, because the group reads
    # as populated and the rule above it reads as active.
    print("\nEvery declared term can match its own text")
    for dom in ("cti", "s2"):
        sc = load_domain(domain=dom)["scoring"]
        m = make_matcher(sc.get("word_boundary_terms"))
        # TWO PROBES, and either one counts. A term is word-boundaried when it
        # is four characters or fewer, and `\b` needs a word character on the
        # far side, so a term ENDING IN PUNCTUATION cannot match itself standing
        # alone: cti declares `cve-`, `zdi-` and `vu#`, which are meant to be
        # followed by digits and match "CVE-2026-1234" correctly. The padded
        # probe serves an ordinary term, the digit probe serves those.
        def matchable(t):
            low = t.lower()
            return (m(f" {low} ", [t]) is not None
                    or m(f" {low}1 ", [t]) is not None)

        dead = [f"{g}:{t}" for g, terms in sc["groups"].items()
                for t in terms if t.strip() and not matchable(t)]
        check(f"no {dom} group term is unmatchable", dead[:6], [])

    # A LOGSOURCE NO SENSOR SUPPLIES IS A SILENT KILL, found on cti 2026-09-24
    # when four requirements were narrowed until they matched almost no sensor
    # and their detectors quietly returned nothing. `unsupported` is the one
    # legitimate case: cti's SIR-1.1.1 and SIR-1.1.2 declare vantages the
    # manifest genuinely cannot supply, and their zero is the finding.
    print("\nEvery requirement can be reached by at least one sensor")
    for dom in ("cti", "s2"):
        cfg = load_domain(domain=dom)
        classes = (cfg.get("sensor_classes") or {}).values()
        starved = [r["id"]
                   for p in (cfg.get("requirements") or {}).get("pirs", [])
                   for i in p.get("indicators", [])
                   for r in i.get("sirs", [])
                   if r.get("status") != "unsupported"
                   and not any(logsource_match(r.get("logsource") or {}, v)
                               for v in classes)]
        check(f"no {dom} requirement declares a logsource no sensor matches",
              starved, [])

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
