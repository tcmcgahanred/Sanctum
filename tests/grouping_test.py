#!/usr/bin/env python3
"""Unit test for near-duplicate GROUPING (display only — never merge, never drop).

Covers the failure this was built for: four outlets report one incident with
four different headlines, collection dedup can't see it (different URLs,
different titles), and scoring scatters them — the headline that names the
victim can land below the cut while vaguer copies rank top.

Asserts:
  1. the four copies land in ONE group, anchored on the highest scorer
  2. a copy below the surface cut is identified as rescued
  3. unrelated articles are NOT swept in
  4. grouping can be disabled by config
  5. nothing is added, removed, or re-scored
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.arbites import group_near_duplicates, _tokens

FAILS = []


def check(label, got, want):
    ok = got == want
    print(f"{'OK  ' if ok else 'FAIL'} {label}: got {got!r}, want {want!r}")
    if not ok:
        FAILS.append(label)


def rec(score, title):
    """Minimal (score, tier, reasons, article, is_stale) tuple."""
    return (score, 1, ["T1"], {"title": title}, False)


# One incident, four outlets. Plus filler that must not be swept in.
scored = [
    rec(23.4, "Suisun City declares state of emergency after cyberattack - Los Angeles Times"),
    rec(12.0, "Suisun City emergency declaration follows cyberattack on city systems"),
    rec(8.0,  "Fortinet FortiGate flaw added to CISA KEV catalog"),
    rec(4.0,  "Ransomware disrupts hospital network in Ohio"),
    rec(2.0,  "Suisun City 911 dispatch restored days after cyberattack"),
    rec(1.0,  "Suisun City confirms cyberattack disrupted emergency dispatch | KTVU"),
]
SURFACE_N = 3   # deliberately tight so two copies fall below the cut

groups, grouped = group_near_duplicates(scored, {})

print("=== groups found ===")
for head, members in sorted(groups.items()):
    for m in members:
        flag = "HEAD" if m == head else "  ↳ "
        print(f"  {flag} [{scored[m][0]:>5}] {scored[m][3]['title'][:62]}")
print()

# 1 — all four Suisun copies in one group, anchored on the top scorer
check("one group found", len(groups), 1)
head = next(iter(groups)) if groups else None
check("group anchored on highest scorer", head, 0)
check("group has all four copies", sorted(groups.get(0, [])), [0, 1, 4, 5])

# 2 — the two below the cut are rescuable
rescued = [m for m in groups.get(0, []) if m >= SURFACE_N]
check("copies below cut identified", rescued, [4, 5])

# 3 — unrelated items untouched
check("KEV item not grouped", 2 in grouped, False)
check("Ohio item not grouped", 3 in grouped, False)

# 4 — config can disable it
off_groups, off_grouped = group_near_duplicates(scored, {"grouping": {"enabled": False}})
check("disabled by config", (off_groups, off_grouped), ({}, set()))

# 5 — grouping is non-destructive: no scores or items changed
check("no items added or removed", len(scored), 6)
check("scores untouched", [r[0] for r in scored], [23.4, 12.0, 8.0, 4.0, 2.0, 1.0])

# 6 — publisher suffix stripped so it can't create false kinship
check("suffix stripped from tokens", "times" in _tokens("Foo bar - Los Angeles Times"), False)
check("suffix stripped (pipe form)", "ktvu" in _tokens("Foo bar | KTVU"), False)

# 7 — a single shared rare token is not enough (guards over-grouping)
pair = [rec(5.0, "Metabase zero-day exploited in the wild"),
        rec(4.0, "Metabase releases quarterly product roadmap")]
g2, _ = group_near_duplicates(pair, {})
check("one shared rare token does not group", g2, {})

print()
if FAILS:
    print(f"RESULT: FAIL — {len(FAILS)} check(s): {', '.join(FAILS)}")
    sys.exit(1)
print("RESULT: PASS")
