#!/usr/bin/env python3
"""
Sanctum · tests/detect_test.py

A requirement can carry its own detector, and a coverage report can tell
"nothing matched" apart from "nothing could".

WHY THIS EXISTS
---------------
Until now the only way a requirement could be detected was for a SCORING rule
to name it in `serves_sir:`. That forced two different jobs through one
expression. A scoring rule answers "is this article worth surfacing". A
detector answers "which requirement did this article satisfy". They are not
the same question, and tying them together made cheap requirements
undetectable: a MITRE ATT&CK technique code is a one-line pattern that should
never move a score, so no scoring rule would ever want to own it, so the
requirement stayed unanswerable.

So a requirement may now carry `detect:`, written in the same atom language
the scoring rules use, plus one new atom, `pattern:`, for facts that are
identifiers rather than vocabulary.

WHAT IS CHECKED
---------------
  pattern atom       matches an identifier, honours scope, is case-insensitive
  bad pattern        refused loudly at evaluation, never a silent non-match
  detect block       satisfies its requirement without touching any score
  rule claim         still works, and the two paths are a union
  satisfied_by       `all` needs every component, `any` needs one
  no detector        an indicator nothing can test is NOT reported as a miss
  needs_detector     an `all` indicator with one detector written and one not
                     is neither satisfied nor a miss
  live domain        cti still loads and its detectors compile

    tests/detect_test.py           # exit 0 = a requirement can detect itself
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.pnd import load_domain                                    # noqa: E402
from core.rules import (_eval_atom, _scopes, detectable_requirements,  # noqa: E402
                        eval_detection, make_matcher,
                        requirement_coverage, score_article)

FAILURES = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
    if not ok:
        print(f"        got:  {got!r}")
        print(f"        want: {want!r}")
        FAILURES.append(label)


def art(title, text=""):
    return {"title": title, "text": text, "url": "https://example.test/a"}


def ev(atom, a, groups=None):
    groups = groups or {}
    matcher = make_matcher([])
    _t, scopes, text_l = _scopes(a)
    return _eval_atom(atom, groups, matcher, scopes, text_l)


TCODE = {"pattern": {"match": r"\bT\d{4}(\.\d{3})?\b", "scope": "blob"}}


def main():
    print("\nThe pattern atom finds an identifier")
    check("a technique code in the body", ev(TCODE, art("x", "uses T1059 here")), True)
    check("a sub-technique code", ev(TCODE, art("x", "uses T1059.003 here")), True)
    check("a code in the headline reaches the blob scope",
          ev(TCODE, art("T1486 deployed")), True)
    check("case does not matter", ev(TCODE, art("x", "uses t1059 here")), True)
    check("no code, no match", ev(TCODE, art("x", "no identifiers at all")), False)
    check("word boundaries hold at the front",
          ev(TCODE, art("x", "part ST1059 is a component")), False)
    check("...and at the back", ev(TCODE, art("x", "code T10594 unknown")), False)

    print("\nScope is honoured, and written bare it is the widest")
    title_only = {"pattern": {"match": r"\bT\d{4}\b", "scope": "title"}}
    check("title scope ignores the body", ev(title_only, art("plain", "T1059")), False)
    check("...and finds the title", ev(title_only, art("T1059 seen", "plain")), True)
    check("a bare pattern string defaults to blob",
          ev({"pattern": r"\bT\d{4}\b"}, art("plain", "T1059")), True)

    print("\nA pattern that cannot compile fails loudly")
    try:
        ev({"pattern": "T(\\d{4}"}, art("x", "T1059"))
        check("a broken pattern is refused", "evaluated", "refused")
    except ValueError as e:
        check("a broken pattern is refused, naming it",
              "not a valid regular expression" in str(e), True)
    try:
        ev({"pattern": {"match": r"\bT\d{4}\b", "scope": "nowhere"}}, art("x"))
        check("an unknown scope is refused", "evaluated", "refused")
    except KeyError as e:
        check("an unknown scope is refused, naming it", "nowhere" in str(e), True)

    print("\nA detector satisfies its requirement, and changes no score")
    req = {"pirs": [{"id": "PIR-9", "name": "t", "question": "q", "indicators": [
        {"id": "IND-9.1", "statement": "s", "satisfied_by": "any", "sirs": [
            {"id": "SIR-9.1.1", "fact": "a technique code", "detect": TCODE}]},
        {"id": "IND-9.2", "statement": "s", "satisfied_by": "all", "sirs": [
            {"id": "SIR-9.2.1", "fact": "a", "detect": TCODE},
            {"id": "SIR-9.2.2", "fact": "b",
             "detect": {"pattern": r"\bG\d{4}\b"}}]},
        {"id": "IND-9.3", "statement": "s", "satisfied_by": "any", "sirs": [
            {"id": "SIR-9.3.1", "fact": "c"}]},
        {"id": "IND-9.4", "statement": "s", "satisfied_by": "any", "sirs": [
            {"id": "SIR-9.4.1", "fact": "d"}]},
    ]}]}
    scoring = {"groups": {}, "tiers": [{"id": 1, "weight": 1.0, "require": "always"}],
               "multipliers": [], "floors": [], "force_surface": []}
    det = detectable_requirements(req, scoring)
    check("only requirements with a detector are detectable",
          det, {"SIR-9.1.1", "SIR-9.2.1", "SIR-9.2.2"})

    a1 = art("Actor uses T1059.003", "and is tracked as G0016")
    cov = requirement_coverage(a1, req, scoring, detectable=det)
    check("both components matched", cov["sirs_met"],
          ["SIR-9.1.1", "SIR-9.2.1", "SIR-9.2.2"])
    check("an `any` indicator is satisfied", cov["indicators"]["IND-9.1"], "satisfied")
    check("an `all` indicator with both components is satisfied",
          cov["indicators"]["IND-9.2"], "satisfied")
    check("an indicator nothing can test is NOT a miss",
          cov["indicators"]["IND-9.3"], "no_detector")
    check("...nor is one whose detector nobody has written",
          cov["indicators"]["IND-9.4"], "no_detector")
    check("the score is untouched by any of it",
          score_article(a1, scoring)[0], score_article(art("plain", "plain"), scoring)[0])

    a2 = art("Actor uses T1059.003", "no group id here")
    cov2 = requirement_coverage(a2, req, scoring, detectable=det)
    check("one of two components is NOT an `all` indicator",
          cov2["indicators"]["IND-9.2"], "unsatisfied")
    check("...but it still satisfies the `any` indicator",
          cov2["indicators"]["IND-9.1"], "satisfied")

    print("\nThe rule path still works, and the two paths are a union")
    scoring2 = dict(scoring)
    scoring2["tiers"] = [{"id": 1, "weight": 1.0, "require": "always",
                          "serves_sir": ["SIR-9.3.1"]}]
    det2 = detectable_requirements(req, scoring2)
    check("a requirement named by a rule becomes detectable",
          "SIR-9.3.1" in det2, True)
    cov3 = requirement_coverage(art("plain", "plain"), req, scoring2, detectable=det2)
    check("the rule fired, so its requirement is met",
          "SIR-9.3.1" in cov3["sirs_met"], True)
    check("...and its indicator is satisfied",
          cov3["indicators"]["IND-9.3"], "satisfied")
    check("the detector path is unaffected and found nothing",
          cov3["indicators"]["IND-9.1"], "unsatisfied")

    print("\nAn `all` indicator half built says so, and is not a miss")
    req2 = {"pirs": [{"id": "PIR-8", "name": "t", "question": "q", "indicators": [
        {"id": "IND-8.1", "statement": "s", "satisfied_by": "all", "sirs": [
            {"id": "SIR-8.1.1", "fact": "a", "detect": TCODE},
            {"id": "SIR-8.1.2", "fact": "b"}]}]}]}
    det3 = detectable_requirements(req2, scoring)
    cov4 = requirement_coverage(art("T1059 seen"), req2, scoring, detectable=det3)
    check("the written half passed, the unwritten half is named as unwritten",
          cov4["indicators"]["IND-8.1"], "needs_detector")
    cov4b = requirement_coverage(art("nothing here"), req2, scoring, detectable=det3)
    check("...and when the written half fails it is an ordinary miss",
          cov4b["indicators"]["IND-8.1"], "unsatisfied")

    print("\nThe live domain still loads and its detectors compile")
    cfg = load_domain(domain="cti")
    live = cfg["requirements"]
    sirs = [s for p in live["pirs"] for i in p["indicators"] for s in i["sirs"]]
    check("cti declares 27 requirements", len(sirs), 27)
    with_det = [s for s in sirs if s.get("detection") is not None]
    blocked = [s for s in sirs if s.get("status") == "blocked"]
    check("...18 of which carry a detection block", len(with_det), 18)
    check("...none is parked as undecidable any more",
          [s["id"] for s in sirs if "decidable" in s], [])
    # Four were reworded on 2026-09-25 from "does the audience own this" to
    # "what kind of thing is this", which is answerable, so they stopped being
    # blocked. An audience inventory across 16 critical infrastructure sectors
    # is not maintainable, and a requirement that depends on one is a
    # permanent zero wearing a `blocked_by:` line.
    check("...5 are blocked on an input that does not exist yet",
          len(blocked), 5)
    check("...every one of those names the input it is waiting for",
          all(str(s.get("blocked_by") or "").strip() for s in blocked), True)
    check("...and none of them pretends to have a detector",
          [s["id"] for s in blocked if s.get("detection") is not None], [])
    check("every rule with a detector also states a logsource",
          all(s.get("logsource") for s in with_det), True)
    check("...each loaded from its own file in cti/requirements/",
          sorted(s["id"] for s in sirs)[:3],
          ["SIR-1.1.1", "SIR-1.1.2", "SIR-1.1.3"])
    check("...and every rule carries a readiness value from the four",
          sorted({s.get("status") for s in sirs}),
          ["blocked", "draft", "stable", "unsupported"])
    # Every detection must PARSE and EVALUATE. Whether it matches this one
    # probe is not the test; that is what the corpus is for.
    probe = art("California county election office hit by ransomware",
                "The registrar of voters confirmed a cyberattack. CVE-2026-1234 "
                "is actively exploited in FortiGate. T1190 was used. Attributed "
                "to Russia, a state-sponsored group.")
    matcher = make_matcher(cfg["scoring"].get("word_boundary_terms"))
    _t, pscopes, ptext = _scopes(probe)
    bad = []
    for s in with_det:
        try:
            eval_detection(s["detection"], cfg["scoring"]["groups"],
                           matcher, pscopes, ptext)
        except Exception as e:
            bad.append(f"{s['id']}: {e}")
    check("every detection parses and evaluates", bad, [])
    check("the technique-identifier rule matches a probe that carries one",
          eval_detection(
              [s for s in with_det if s["id"] == "SIR-5.1.1"][0]["detection"],
              cfg["scoring"]["groups"], matcher, pscopes, ptext), True)
    live_det = detectable_requirements(live, cfg["scoring"])
    cov5 = requirement_coverage(probe, live, cfg["scoring"], detectable=live_det)
    check("the probe answers the technique-identifier requirement",
          "SIR-5.1.1" in cov5["sirs_met"], True)
    check("...and the country-of-origin one, which it also carries",
          "SIR-5.2.2" in cov5["sirs_met"], True)
    check("...but not the group-identifier one, which needs a G number",
          "SIR-5.2.1" in cov5["sirs_met"], False)
    # A listicle with no identifiers and no incident language answers nothing
    # under PIR-5, which is the exclusion every rule there carries.
    quiet = requirement_coverage(
        art("Top 10 predictions", "nothing here"), live, cfg["scoring"],
        detectable=live_det)
    check("a listicle with nothing in it answers nothing under PIR-5",
          [x for x in quiet["sirs_met"] if x.startswith("SIR-5")], [])

    print("\nThe logsource is the FIRST filter, before any term is matched")
    classes = cfg["sensor_classes"]
    check("every sensor in the manifest is classified", len(classes), 55)
    check("...on two axes",
          sorted({k for v in classes.values() for k in v}), ["kind", "scope"])

    # A corpus record stores the sensor's own URL in `source`, so the lookup
    # back to the sensor is exact rather than inferred.
    press = next(u for u, c in classes.items()
                 if c == {"scope": "national", "kind": "press"})
    registry = next(u for u, c in classes.items()
                    if c["kind"] == "breach_registry")

    def sourced(url, title, text=""):
        a = art(title, text)
        a["source"] = url
        return a

    # THE FAILURE THIS FIXES. SIR-1.1.1 is "a breach notification naming a
    # California organization", its logsource is a regional breach registry,
    # no such sensor exists, and before this it matched 153 articles of press
    # coverage in 30 days.
    breachy = ("Sacramento county says personal information was exposed. The "
               "breach notification letter names 4,000 records affected by the "
               "cyberattack, and the attorney general was notified.")
    live_det2 = detectable_requirements(live, cfg["scoring"])

    def met(a):
        return requirement_coverage(a, live, cfg["scoring"],
                                    detectable=live_det2,
                                    sensor_classes=classes)["sirs_met"]

    check("press coverage of a breach does NOT answer the registry requirement",
          "SIR-1.1.1" in met(sourced(press, "County breach", breachy)), False)
    check("...and the national breach registry does not either, being the "
          "wrong scope",
          "SIR-1.1.1" in met(sourced(registry, "County breach", breachy)), False)
    check("...nor does an article whose sensor is no longer in the manifest",
          "SIR-1.1.1" in met(sourced("https://gone.test/feed", "County breach",
                                     breachy)), False)

    # A rule declaring `any` on both axes reads everything, which is how a
    # technique identifier turning up anywhere says so out loud.
    tcode = sourced(press, "Actor uses T1059.003", "living off the land")
    check("a rule scoped any/any still matches press",
          "SIR-5.1.1" in met(tcode), True)
    gone = sourced("https://gone.test/feed", "Actor uses T1059.003", "x")
    check("...and still matches an article from a retired sensor",
          "SIR-5.1.1" in met(gone), True)

    print()
    if FAILURES:
        print(f"FAIL — {len(FAILURES)} problem(s)")
        for f in FAILURES:
            print(f"    {f}")
        return 1
    print("PASS — a requirement can carry its own detector, an identifier can "
          "be matched by pattern, and an untestable indicator is not a miss")
    return 0


if __name__ == "__main__":
    sys.exit(main())
