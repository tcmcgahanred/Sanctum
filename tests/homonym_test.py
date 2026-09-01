#!/usr/bin/env python3
"""
Sanctum · tests/homonym_test.py

The cyber-domain gate: an ordinary English word cannot carry a requirement.

WHY THIS EXISTS
---------------
On 2026-08-31 *"A Baby Great White Leapt from the Ocean Near a Boogie Boarder"*
scored 8.0, took tier 1, and FORCE-SURFACED on M1. `geo:'california'` matched
the beach; `incident:'breach'` matched a shark breaching the ocean surface. The
score could not correct it, because force-surface exists precisely to override
the score. An earlier great-white item escaped only because it was stale.

"breach" is also a levee, a dam, a contract, a courtroom verdict, a code of
conduct and a hull. This is the third instance of the class — `water` in
`sector`, `" calif "` in `geo`, now `breach` in `incident`.

WHAT SHIPPED, AND WHAT DID NOT
------------------------------
NOT shipped: narrowing `incident` to compound forms only. Measured against 776
real items, it removed 15 false positives and took at least 10 genuine ones with
them. Tier 1's proximity atom names `incident` as a STRING, so it always reads
the raw group — narrow the group and an article whose only incident word near
the California mention was `breach` falls out, even with "data breach" in its
own headline. **Proximity cannot be guarded from outside the group it names.**

NOT shipped: requiring the literal word "cyber". Measured: it would have deleted
the California DMV data breach, the LA Superior Court ransomware shutdown, the
Northern Inyo Hospital breach and all three tier-3 vulnerability advisories.
**Incident reporting does not say "cyber."** Journalists and policy writers do.

SHIPPED: `cyber_context`, a required conjunct on tiers 1-3 and all three
force-surface rules. Measured on the same 776 items: 16 of 137 surfaced items
removed, all 16 non-cyber, zero genuine losses. `breach` was never touched.

WHAT THIS FILE GUARDS
---------------------
Every case below is a real item from the 2026-08-31 corpus, reconstructed. The
MUST DROP set is the false positives. The MUST STAY set is the items that any
future tightening must not take with them — each one was lost by an earlier
attempt, which is why it is here.

    tests/homonym_test.py        # exit 0 = the gate holds
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pnd import load_domain          # noqa: E402
from core.rules import score_article      # noqa: E402

FAILURES = []

# (label, must_surface, title, body)
CASES = [
    # --- MUST DROP: ordinary English, no computer anywhere in it -----------
    ("shark breaching the surface", False,
     "A Baby Great White Leapt from the Ocean Near a Boogie Boarder",
     "A juvenile great white shark breached the surface off a Southern California "
     "beach near a boogie boarder in the surf."),
    ("whale watching listicle", False,
     "12 Best Whale-Watching Destinations in the U.S.",
     "California's coast offers a chance to see a whale breach the surface. "
     "Monterey and Sacramento day trips are popular."),
    ("lottery lawsuit", False,
     "California man loses lawsuit over $750,000 lottery prize",
     "A California man lost his lawsuit after the ticket was allegedly in breach "
     "of the retailer's rules."),
    ("levee breach, physical infrastructure", False,
     "Levee breach floods farmland in California's Central Valley",
     "A levee breach near Stockton sent water across California farmland; crews "
     "closed the breach overnight."),

    # --- MUST STAY: every one of these was killed by an earlier attempt ----
    ("California DMV data breach", True,
     "California DMV data breach shared Social Security information of thousands",
     "The California DMV said a data breach exposed Social Security numbers of "
     "thousands of residents."),
    ("Northern Inyo Hospital", True,
     "Northern Inyo Hospital Data Breach Confirmed",
     "Northern Inyo Healthcare District in California confirmed a data breach "
     "exposing patient records."),
    ("LA Superior Court ransomware", True,
     "LA Superior Court system closed Monday following ransomware attack",
     "The Los Angeles Superior Court in California shut its systems after a "
     "ransomware attack."),
    # Lost by the FIRST version of the gate, which used a bare "hack". The
    # matcher word-boundaries anything <=4 chars, so "hack" never matched
    # "Hacks" and one plural noun deleted a tier-2 water-sector item.
    ("water systems, plural 'Hacks'", True,
     "Attackers Targeted Over 100 US Water Systems in July Hacks",
     "Attackers targeted more than 100 water systems across the United States "
     "in July hacks."),
    ("vulnerability advisory", True,
     "SonicWall NetExtender Vulnerabilities Allow Arbitrary File Write",
     "Researchers disclosed vulnerabilities in SonicWall NetExtender that are "
     "actively exploited in the wild."),
]


def run():
    cfg = load_domain(domain="cti")
    sc = cfg["scoring"]
    thr = float(sc.get("settings", {}).get("surface_min_score", 2.0))
    print("\nCyber-domain gate — threshold %.2f\n" % thr)

    for label, want_surface, title, body in CASES:
        art = {"title": title, "text": body,
               "url": "https://example.test/x", "source": "https://example.test/f"}
        score, tier, _ = score_article(art, sc)
        got = score >= thr
        ok = got == want_surface
        if not ok:
            FAILURES.append(label)
        print("  %s  %-32s %5.2f  tier %-2s  %s (want %s)" % (
            "ok  " if ok else "FAIL", label, score, tier,
            "surfaces" if got else "drops",
            "surfaces" if want_surface else "drops"))

    # The gate must be a PRECONDITION, not a scorer. If it ever starts adding
    # weight, an item could surface on the gate alone, which is the opposite of
    # the intent.
    print("\nThe gate adds no weight")
    plain = {"title": "An article about nothing in particular",
             "text": "There is no computer in this story at all.",
             "url": "u", "source": "s"}
    cyber = {"title": "An article about nothing in particular",
             "text": "There is no computer in this story at all. Ransomware.",
             "url": "u", "source": "s"}
    a, b = score_article(plain, sc)[0], score_article(cyber, sc)[0]
    ok = a == b
    if not ok:
        FAILURES.append("gate adds weight")
    print("  %s  adding a cyber word alone changes nothing: %.2f -> %.2f"
          % ("ok  " if ok else "FAIL", a, b))

    print()
    if FAILURES:
        print("FAIL — %d case(s):" % len(FAILURES))
        for f in FAILURES:
            print("    " + f)
        return 1
    print("PASS — homonyms drop, every previously-lost item still surfaces, "
          "and the gate adds no weight")
    return 0


if __name__ == "__main__":
    sys.exit(run())
