#!/usr/bin/env python3
"""
Scoring regression test.

WHAT THIS USED TO BE. Until 2026-08-24 it compared the engine against
`tests/old_arbites.py`, the original hardcoded CTI scorer, to prove the port
changed nothing. That job finished long ago, and the scoring work of 2026-08-24
deliberately changed the model, so the comparison could only report the change
we asked for. Re-baselined rather than deleted: the fuzz corpus is worth keeping.

WHAT IT IS NOW. Three checks, in order of how much they matter:

  1. REQUIREMENTS - the named items from the P&D work orders. False positives
     must fall below the surface threshold AND out of every force-surface rule;
     true positives must stay surfaced; floored items must reach their floor
     WITHOUT being force-surfaced. Assertions about intent.
  2. HAND CASES - one article per rule branch, against a stored baseline.
  3. FUZZ - 500 seeded random articles against the same baseline.

A SNAPSHOT CANNOT VALIDATE ITSELF. The baseline is generated from whatever the
code does at the time, so a defect present when it is written is recorded as
correct and reported PASS forever after. That happened on 2026-08-24: a padding
bug fired force-surface M1 on 190 articles and this file said PASS. The named
requirements above, and a run against the real corpus
(tools/rescore_check.py), are what catch that class of error.

Re-baseline deliberately, and say in the changelog why the numbers moved:

    python3 tests/diff_scores.py --update
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.pnd import load_domain                                          # noqa: E402
from core.rules import score_article, make_matcher, _eval_atom, _scopes   # noqa: E402
from tests.scoring_fixtures import FALSE_POSITIVES, TRUE_POSITIVES, FLOORED  # noqa: E402

BASELINE = Path(__file__).resolve().parent / "score_baseline.json"

cfg = load_domain(domain="cti")["scoring"]
THRESHOLD = float(cfg["settings"].get("surface_min_score") or 0)


def score(art):
    s, t, _ = score_article(art, cfg)
    return [s, t]


def force_rule(art):
    """Name of the first force-surface rule that fires, or None."""
    groups = cfg["groups"]
    matcher = make_matcher(cfg.get("word_boundary_terms"))
    _title, scopes, text_l = _scopes(art)
    for rule in cfg.get("force_surface", []) or []:
        if _eval_atom(rule["when"], groups, matcher, scopes, text_l):
            return rule.get("name", "force")
    return None


CASES = [
    {"title": "Fresno County hit by ransomware", "text": "The county reported an outage."},
    {"title": "Local utility disruption",
     "text": "The California water agency confirmed a ransomware attack locked operator systems."},
    {"title": "Texas school district ransomware", "text": "A school district was hit."},
    {"title": "Critical Fortinet flaw actively exploited",
     "text": "CISA added the known exploited flaw to its catalog. Tracked as CVE-2026-9001."},
    {"title": "New malware framework analysis", "text": "Researchers describe a new framework."},
    {"title": "", "text": "orphan feed artifact with no title"},
    {"title": "npm package compromised in supply chain attack", "text": "A dependency was backdoored."},
    {"title": "San Francisco startup breach", "text": "A startup disclosed a breach."},
    {"title": "Physics research breakthrough", "text": "Nothing to do with security."},
    {"title": "California hospital ransomware via Fortinet exploited in the wild",
     "text": "Attackers used known exploited flaws against the hospital."},
    {"title": "Sacramento County data breach", "text": "Records stolen from county systems."},
    {"title": "Water sector targeted nationwide", "text": "PLC and SCADA systems at risk."},
    {"title": "MSP compromise cascades to clients", "text": "A managed service provider breach hit customers."},
    {"title": "Cisco patches router firewall bug", "text": "Cisco released updates for its firewall."},
    {"title": "Top 10 Best Firewall Solutions",
     "text": "Fortinet and Cisco are actively exploited targets sometimes."},
    {"title": "Sonoma water district taken offline by ransomware",
     "text": "The utility district confirmed an outage."},
    {"title": "Hotel chain breach",
     "text": "The resort has a water park. Separately, analysts note actively exploited flaws."},
    # Padding guard: 'uc ' must not match inside "product"/"reduce".
    {"title": "Pokemon Center data breach", "text": "A product breach exposed records; reduce risk now."},
    # Availability language must NOT reach tier 1: a California non-cyber outage
    # is not an AOR cyber incident. Work order 2026-08-24, decision 4.
    {"title": "California utility announces planned outage",
     "text": "A public safety power shutoff will affect Fresno County during high winds."},
    # ...but it SHOULD work where the sector is the subject.
    {"title": "School district taken offline by denial of service",
     "text": "The district said classes continued."},
]


def fuzz_articles(n=500, seed=1337):
    rng = random.Random(seed)
    tokens = []
    for g in cfg["groups"].values():
        tokens += [t.strip() for t in g]
    tokens += ["the", "a", "report", "system", "update", "vendor", "issue",
               "san francisco", "physics", "network", "and", "of", "new"]
    tokens.sort()  # deterministic regardless of group ordering in the config
    for _ in range(n):
        ntitle = rng.randint(0, 6)
        nbody = rng.randint(0, 14)
        yield {"title": " ".join(rng.choice(tokens) for _ in range(ntitle)),
               "text": " ".join(rng.choice(tokens) for _ in range(nbody))}


def build():
    return {"cases": [score(c) for c in CASES],
            "fuzz": [score(a) for a in fuzz_articles()]}


def check_requirements():
    print("=== requirements (P&D work orders) ===")
    fails = 0
    for art in FALSE_POSITIVES:
        s, _t, _r = score_article(art, cfg)
        f = force_rule(art)
        ok = (s < THRESHOLD) and (f is None)
        fails += (not ok)
        why = "" if ok else (" - still forced by %s" % f if f else " - %s >= %s" % (s, THRESHOLD))
        print("%smust drop     %6s  %s%s" % ("OK " if ok else "XX ", s, art["key"], why))
    for art in TRUE_POSITIVES:
        s, _t, _r = score_article(art, cfg)
        ok = (s >= THRESHOLD) or (force_rule(art) is not None)
        fails += (not ok)
        print("%smust surface  %6s  %s%s" % ("OK " if ok else "XX ", s, art["key"],
              "" if ok else " - below threshold and no force rule"))
    for art in FLOORED:
        s, _t, _r = score_article(art, cfg)
        f = force_rule(art)
        ok = (s >= float(art["min_score"])) and (f is None)
        fails += (not ok)
        why = "" if ok else (" - force-surfaced by %s" % f if f else " - %s < %s" % (s, art["min_score"]))
        print("%smust floor    %6s  %s%s" % ("OK " if ok else "XX ", s, art["key"], why))
    return fails


def check_baseline():
    if not BASELINE.exists():
        print("\nNO BASELINE at %s - run with --update to create it." % BASELINE)
        return 1
    want = json.loads(BASELINE.read_text())
    have = build()
    fails = 0
    print("\n=== hand-built cases vs baseline ===")
    for c, w, h in zip(CASES, want["cases"], have["cases"]):
        ok = (w == h)
        fails += (not ok)
        shown = str(h) if ok else "%s -> %s" % (w, h)
        print("%s%-22s %r" % ("OK " if ok else "XX ", shown, c["title"][:48]))
    print("\n=== fuzz (500 seeded articles) vs baseline ===")
    mism = [(i, w, h) for i, (w, h) in enumerate(zip(want["fuzz"], have["fuzz"])) if w != h]
    for i, w, h in mism[:10]:
        print("XX fuzz[%d] baseline=%s now=%s" % (i, w, h))
    if len(mism) > 10:
        print("   ... and %d more" % (len(mism) - 10))
    if not mism:
        print("OK  all 500 match")
    return fails + len(mism)


if __name__ == "__main__":
    if "--update" in sys.argv:
        BASELINE.write_text(json.dumps(build(), indent=1) + "\n")
        print("baseline written: %s" % BASELINE)
        sys.exit(0)
    total = check_requirements() + check_baseline()
    print("\nRESULT: %s" % ("PASS" if total == 0 else "FAIL - %d mismatch(es)" % total))
    sys.exit(1 if total else 0)
