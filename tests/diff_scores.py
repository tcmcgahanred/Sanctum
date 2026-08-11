#!/usr/bin/env python3
"""
Behavior-preservation test: the new domain-agnostic engine must score
IDENTICALLY to the original hardcoded CTI arbites.py.

Compares (score, tier) from old_arbites.score_article vs
core.rules.score_article(cfg) over hand-built cases (every branch) plus a
seeded fuzz of 500 random articles. Exits non-zero on any mismatch.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import old_arbites  # the original, preserved verbatim
from core.pnd import load_domain
from core.rules import score_article as new_score

cfg = load_domain(domain="cti")["scoring"]


def old(art):
    s, t, _ = old_arbites.score_article(art)
    return s, t


def new(art):
    s, t, _ = new_score(art, cfg)
    return s, t


CASES = [
    {"title": "Fresno County hit by ransomware", "text": "The county reported an outage."},
    {"title": "Local utility disruption",
     "text": "The California water agency confirmed a ransomware attack locked operator systems."},
    {"title": "Texas school district ransomware", "text": "A school district was hit."},
    {"title": "Critical Fortinet flaw actively exploited",
     "text": "CISA added the known exploited flaw to its catalog."},
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
]


def run_cases():
    fails = 0
    print(f"{'score(old/new)':<20} {'tier':<10} title")
    for c in CASES:
        o, n = old(c), new(c)
        ok = (o == n)
        fails += (not ok)
        mark = "OK " if ok else "XX "
        print(f"{mark}{str(o[0])+'/'+str(n[0]):<17} {str(o[1])+'/'+str(n[1]):<10} {c['title'][:50]!r}")
    return fails


def run_fuzz(n=500, seed=1337):
    rng = random.Random(seed)
    tokens = []
    for g in cfg["groups"].values():
        tokens += [t.strip() for t in g]
    tokens += ["the", "a", "report", "system", "update", "vendor", "issue",
               "san francisco", "physics", "network", "and", "of", "new"]
    fails = 0
    for _ in range(n):
        ntitle = rng.randint(0, 6)
        nbody = rng.randint(0, 14)
        title = " ".join(rng.choice(tokens) for _ in range(ntitle))
        text = " ".join(rng.choice(tokens) for _ in range(nbody))
        art = {"title": title, "text": text}
        o, nw = old(art), new(art)
        if o != nw:
            fails += 1
            print(f"FUZZ MISMATCH old={o} new={nw}\n  title={title!r}\n  text={text!r}")
    return fails


if __name__ == "__main__":
    print("=== hand-built cases ===")
    f1 = run_cases()
    print("\n=== fuzz (500 random articles) ===")
    f2 = run_fuzz()
    total = f1 + f2
    print(f"\nRESULT: {'PASS — new engine matches old exactly' if total == 0 else f'FAIL — {total} mismatches'}")
    sys.exit(1 if total else 0)
