#!/usr/bin/env python3
"""
Sanctum · tests/geo_classify_test.py

A place name is classified by what it is confusable WITH, and the comparison
depends on the form the term takes in a rule.

WHY THIS EXISTS
---------------
`tools/geo_classify.py` derives a confidence bucket for every place name in a
state, so that a domain does not hand-maintain a judgement about which names
are safe. Two measured signals decide it: how many states share the name, and
how common the name is as an ordinary English word.

The first version pooled counties and places into one index. `lake county` —
a two-word phrase that can only match "Lake County" in text — was scored
against every settlement named Lake and against the frequency of the bare word
"lake", and **26 county rows landed in the wrong bucket**, including six that
were correct before. The tool's own change-report caught it, which is the only
reason it was found before the table shipped.

So the rule this file guards is:

    county rows  -> compared against COUNTIES ONLY, never frequency-tested,
                    because "X County" is a phrase and not an English word
    place rows   -> compared against every name, and frequency-tested when
                    the name is a single word

WHAT IS CHECKED
---------------
  classification   the two signals, and the county/place asymmetry above
  no dependency    the frequency signal is injected, so this runs anywhere
  absent signal    without wordfreq nothing crashes; names fall to state count
  the real table   the committed table parses, and the collisions measured on
                   2026-09-02 are still in the buckets they were put in

    tests/geo_classify_test.py        # exit 0 = the geography table is sound
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from geo_classify import classify, COMMON_WORD_ZIPF   # noqa: E402

FAILURES = []
TABLE = ROOT / "cti" / "data" / "geo_classified.txt"


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
    if not ok:
        print(f"        got:  {got!r}")
        print(f"        want: {want!r}")
        FAILURES.append(label)


# An injected frequency function: no wordfreq needed, and the thresholds under
# test are visible rather than buried in a package.
FREQ = {"lake": 4.83, "orange": 4.62, "commerce": 4.37, "weed": 4.27,
        "industry": 5.19, "bishop": 4.30,
        "alhambra": 2.74, "cupertino": 2.59, "tehachapi": 2.08, "modesto": 3.10}
zipf = lambda w: FREQ.get(w, 1.0)


def st(n):
    """n distinct states, as the classifier only ever counts them."""
    return set(f"S{i}" for i in range(n))


def run():
    print("\nState count decides the bucket")
    check("one state is A", classify("Cupertino", "place", st(1), zipf)[0], "A")
    check("two states is B", classify("Alhambra", "place", st(2), zipf)[0], "B")
    check("three states is B", classify("Alhambra", "place", st(3), zipf)[0], "B")
    check("four states is C", classify("Alhambra", "place", st(4), zipf)[0], "C")
    check("...and the reason says how many",
          "4" in classify("Alhambra", "place", st(4), zipf)[1], True)

    print("\nA common English word is C however few states have it")
    b, why = classify("Commerce", "place", st(1), zipf)
    check("a common word overrides a unique name", b, "C")
    check("...and the reason names the frequency", "zipf" in why, True)
    check("a rare name at the same state count stays A",
          classify("Tehachapi", "place", st(1), zipf)[0], "A")
    check("the threshold is the documented one", COMMON_WORD_ZIPF, 4.0)

    print("\nA multi-word name is never frequency-tested")
    # "Lake Forest" is not the word "lake". Only single-token names are tested,
    # because a two-word name is already distinctive.
    check("a two-word place is judged on state count alone",
          classify("Lake Forest", "place", st(1), zipf)[0], "A")

    print("\nCounty rows are compared against counties, and never by frequency")
    # THE BUG. `lake county` is a phrase; scoring it on the word "lake" and on
    # every settlement named Lake moved 26 county rows to the wrong bucket.
    check("a county whose name is a common word is NOT C for that reason",
          classify("Lake", "county", st(2), zipf)[0], "B")
    check("...its reason talks about counties, not states",
          "counties" in classify("Lake", "county", st(2), zipf)[1], True)
    check("a county unique among counties is A even if the word is common",
          classify("Orange", "county", st(1), zipf)[0], "A")
    check("a place with the same name is still C",
          classify("Orange", "place", st(1), zipf)[0], "C")

    print("\nWithout the frequency signal nothing crashes")
    check("a common word falls back to its state count",
          classify("Commerce", "place", st(1), None)[0], "A")
    check("...and a genuine collision is still caught",
          classify("Commerce", "place", st(9), None)[0], "C")

    print("\nThe committed table")
    if not TABLE.exists():
        check("the table exists", False, True)
        return 1
    rows, header = {}, []
    for line in TABLE.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            header.append(line)
            continue
        if not line.strip():
            continue
        parts = line.split("|")
        check_len = len(parts) >= 5
        if not check_len:
            FAILURES.append(f"malformed row: {line!r}")
            continue
        rows[(parts[0], parts[1])] = parts[2]
    check("every row parses into name|kind|bucket|states|reason",
          [f for f in FAILURES if f.startswith("malformed")], [])
    check("the header records which frequency signal built it",
          any("frequency signal" in h for h in header), True)
    check("the header warns that it covers the whole state, not an AOR",
          any("AOR" in h for h in header), True)
    check("it carries both counties and places",
          sorted({k[1] for k in rows}), ["county", "place"])

    # Measured 2026-09-02 against the 2025 gazetteer. If a regeneration moves
    # any of these, that is a real change in the source data and wants reading,
    # not a silent re-bucket.
    print("\n  known collisions, measured 2026-09-02")
    for name, kind, want in [("lake", "county", "C"), ("orange", "county", "C"),
                             ("kings", "county", "B"), ("nevada", "county", "B"),
                             ("sierra", "county", "B"), ("trinity", "county", "B"),
                             ("butte", "county", "B")]:
        check(f"{name} {kind} is {want}", rows.get((name, kind)), want)
    print("\n  known-safe names")
    for name, kind, want in [("cupertino", "place", "A"), ("tehachapi", "place", "A"),
                             ("inyo", "county", "A"), ("yolo", "county", "A"),
                             ("stockton", "place", "C"), ("commerce", "place", "C")]:
        check(f"{name} {kind} is {want}", rows.get((name, kind)), want)

    print()
    if FAILURES:
        print(f"FAIL — {len(FAILURES)} problem(s)")
        for f in FAILURES:
            print(f"    {f}")
        return 1
    print("PASS — names are classified by what they are confusable with, and a "
          "county phrase is not judged as an English word")
    return 0


if __name__ == "__main__":
    sys.exit(run())
