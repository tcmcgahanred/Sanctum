#!/usr/bin/env python3
"""Unit test for near-duplicate GROUPING (display only — never merge, never drop).

The fixture is NOT synthetic. These are real titles from the 2026-08-13
production corpus — the run in which the first implementation collapsed 520
unrelated articles into a single group. Ground truth is hand-labelled:
fifteen reports of one California city incident, two reports of one ransomware
campaign, and twelve unrelated singletons that share heavy vocabulary overlap
with them ("California", "cyberattack", "state of emergency", "data breach").

The hard negative is deliberate: a *different* California city cyberattack
that also prompted a state of emergency. Any approach loose enough to gather
all fifteen true reports will also swallow it — so the target is PRECISION.
A missed grouping costs nothing beyond the status quo; a false grouping hides
an item under an unrelated head, which is worse than not grouping at all.

Asserts:
  1. zero false groupings on real data (precision 1.00)
  2. useful recall (>= 0.5 of true same-event pairs)
  3. the hard negative stays out of the incident group
  4. no mega-cluster can form — the v1 regression
  5. a below-cut member is identifiable for rescue
  6. config disable works; grouping is non-destructive
"""
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.arbites import group_near_duplicates, _tokens

FAILS = []


def check(label, got, want, cmp=lambda a, b: a == b):
    ok = cmp(got, want)
    print(f"{'OK  ' if ok else 'FAIL'} {label}: got {got!r}, want {want!r}")
    if not ok:
        FAILS.append(label)


# (score, title, event-label or None)  — real corpus titles, score-ordered
FIXTURE = [
    (15.21, "Patch Tuesday - August 2026", None),
    (11.70, "Gunra Ransomware Exploits Fortinet and Schneider Electric Flaws to Breach Networks", "gunra"),
    (10.40, "Local governments in four states dealing with cyberattacks that have shut down services", None),
    (10.40, "Suisan City, California, Responds to Cyber Incident Amid Wave of US Local Government Attacks", "city"),
    (10.40, "Ransomware attack takes Visalia Unified's computer systems offline, school district says - ABC30 Fresno", None),
    (10.14, "OpenAI Slows Down New Astra Model Development to Measure Cybersecurity Capabilities", None),
    (8.00, "Sacramento-Area School District Waited Months to Disclose Data Breach - GovTech", None),
    (8.00, "California city declares a 'state of emergency' after cyberattack on computer systems - Los Angeles Times", "city"),
    (8.00, "California city declares state of emergency after major cyberattack disrupts key systems - Daily Express US", "city"),
    (8.00, "California city declares State emergency as cyber attacks hit crucial services, including 911 - The Times of India", "city"),
    (8.00, "California city declares emergency after 911 system hacked - NewsNation", "city"),
    (8.00, "Calif. City Declares Local Emergency After Cyberattack Disrupts 911 Calls - PCMag", "city"),
    (8.00, "WEEKLY WATER NEWS DIGEST for June 7-12: El Nino is here and likely to be historic - Maven's Notebook", None),
    (8.00, "California medical group data breach impacts 3.3 million patients - BleepingComputer", None),
    (8.00, "Suisun City, Calif., Shutters Network Following Cyber Attack - GovTech", "city"),
    (8.00, "California city declares emergency after cyberattack disrupts computer systems - NewsNation", "city"),
    (8.00, "California City Declares State of Emergency After Cyberattack Disrupts Computer Systems - NewsBreak", "city"),
    (8.00, "Another cyberattack causes California 911 systems to shut down - wiproud.com", "city"),
    (8.00, "A Californian City Declares State Of Emergency Following Cyberattack On Emergency Systems - NDTV", "city"),
    (8.00, "Cyberattack impacts critical public safety operations in California city - Smart Cities Dive", "city"),
    (8.00, "California city declares state of emergency after cyberattack on computer systems - AOL.com", "city"),
    (8.00, "California City Declares Emergency After Cyberattack Disrupts 911 Services - The420.in", "city"),
    (8.00, "California Federal Court Holds that Damages Properly Alleged in RockYou Data Breach Case - InfoLawGroup LLP", None),
    (8.00, "Cyberattack Forces California City to Shut Down Network - varindia.com", "city"),
    # HARD NEGATIVE — a different incident, near-identical vocabulary
    (8.00, "Two Contra Costa Cities Hit By Cyber Attacks, Prompting State of Emergency - California City News", None),
    (7.80, "CrowdStrike Threat Hunts for Shell Command Obfuscation on VMware ESX", None),
    (7.80, "Rapid7 Analysis: Unauthenticated Remote Code Execution in JetBrains TeamCity (CVE-2026-63077)", None),
    (7.80, "ClamAV Vulnerabilities Affecting Cisco Products: August 2026", None),
    (7.80, "Gunra Ransomware Exploits Fortinet VPN Flaws to Bypass MFA and Steal Enterprise Data", "gunra"),
]
CONTRA_COSTA = 24

# Background corpus. Word weighting is inverse-document-frequency based, so it
# only behaves realistically against a corpus of realistic size — a 29-item
# fixture makes common words look rare. These 320 deterministic filler titles
# reproduce the shape of a real collection window (vendor advisories, national
# incident reporting) so the weighting under test matches production. They are
# scored below the fixture and excluded from the precision/recall arithmetic.
_PRODUCTS = ["Fortinet FortiGate", "Cisco IOS XE", "Apache Tomcat", "Microsoft SharePoint",
             "SonicWall SMA", "MikroTik RouterOS", "WordPress", "Palo Alto PAN-OS",
             "VMware ESXi", "Ivanti Connect Secure", "Citrix NetScaler", "Zimbra",
             "GitLab", "Jenkins", "Atlassian Confluence", "Progress MOVEit"]
_FLAWS = ["critical vulnerability", "authentication bypass", "remote code execution",
          "privilege escalation", "path traversal", "information disclosure"]
_STATES = ["actively exploited in the wild", "added to CISA KEV catalog",
          "patched in latest release", "disclosed by researchers"]
_ACTS = ["Ransomware group claims attack on", "Hackers breach", "Data breach exposes records at",
         "Threat actors target", "New malware campaign hits"]
_ORGS = ["a hospital network", "a school district", "a county government",
         "a utility provider", "a manufacturing firm", "a logistics provider"]
_GEOS = ["Texas", "Ohio", "Florida", "New York", "Illinois", "Georgia", "Michigan", "Oregon"]

BACKGROUND = []
for _n in range(320):
    if _n % 3 != 2:
        BACKGROUND.append(f"{_PRODUCTS[_n % len(_PRODUCTS)]} {_FLAWS[(_n * 7) % len(_FLAWS)]} "
                          f"{_STATES[(_n * 11) % len(_STATES)]} advisory {_n}")
    else:
        BACKGROUND.append(f"{_ACTS[(_n * 5) % len(_ACTS)]} {_ORGS[(_n * 13) % len(_ORGS)]} "
                          f"in {_GEOS[(_n * 3) % len(_GEOS)]} incident {_n}")

scored = ([(s, 1, ["T1"], {"title": t}, False) for s, t, _ in FIXTURE]
          + [(1.0, 4, ["T4"], {"title": t}, False) for t in BACKGROUND])
labels = [lab for _, _, lab in FIXTURE]
N_REAL = len(FIXTURE)

groups, grouped, dissolved = group_near_duplicates(scored, {})

print("=== groups formed ===")
for head, members in sorted(groups.items()):
    if head >= N_REAL:
        continue                     # background filler; not part of the assertion set
    for m in members:
        print(f"  {'HEAD' if m == head else '  ↳ '} [{scored[m][0]:>5}] {scored[m][3]['title'][:66]}")
    print()

member_of = {}
for head, members in groups.items():
    for m in members:
        member_of[m] = head

tp = fp = fn = 0
false_pairs = []
for i, j in itertools.combinations(range(N_REAL), 2):
    pred = member_of.get(i, i) == member_of.get(j, j)
    true = bool(labels[i]) and labels[i] == labels[j]
    if pred and true:
        tp += 1
    elif pred and not true:
        fp += 1
        false_pairs.append((i, j))
    elif true:
        fn += 1

precision = tp / (tp + fp) if (tp + fp) else 1.0
recall = tp / (tp + fn) if (tp + fn) else 0.0
print(f"pairs: tp={tp} fp={fp} fn={fn} | precision {precision:.2f} recall {recall:.2f}")
if false_pairs:
    for i, j in false_pairs:
        print(f"  FALSE PAIR: {FIXTURE[i][1][:48]} || {FIXTURE[j][1][:48]}")
print()

# 1 — no false groupings at all
check("precision on real corpus", round(precision, 2), 1.0)

# 2 — recall is actually useful
check("recall >= 0.50", recall >= 0.50, True)

# 3 — the hard negative is not swept into the incident group
city_head = member_of.get(7)
check("Contra Costa kept separate", member_of.get(CONTRA_COSTA) == city_head and city_head is not None, False)

# 4 — v1 regression: no mega-cluster, and no chaining across unrelated items.
#     v1 produced a single 520-item group by transitive linking; the guard is
#     that no group may mix the labelled fixture with unrelated background.
real_groups = {h: m for h, m in groups.items() if h < N_REAL}
largest_real = max((len(m) for m in real_groups.values()), default=0)
check("largest real group <= 16 (no chaining)", largest_real <= 16, True)
mixed = [h for h, m in groups.items()
         if any(i < N_REAL for i in m) and any(i >= N_REAL for i in m)]
check("no group mixes fixture with background", mixed, [])
check("more than one real group found", len([h for h in groups if h < N_REAL]) >= 2, True)

# 5 — a member below a tight cut is identifiable for rescue
SURFACE_N = 10
rescuable = [m for h, ms in groups.items() if h < SURFACE_N for m in ms if SURFACE_N <= m < N_REAL]
check("below-cut members identified", len(rescuable) > 0, True)

# 6 — config + non-destructiveness
off = group_near_duplicates(scored, {"grouping": {"enabled": False}})
check("disabled by config", off, ({}, set(), 0))
check("no items added or removed", len(scored), N_REAL + len(BACKGROUND))
check("scores untouched", [r[0] for r in scored[:N_REAL]], [f[0] for f in FIXTURE])
check("publisher suffix stripped", "pcmag" in _tokens("Foo bar baz - PCMag"), False)

# 7 — oversized clusters are dissolved rather than shown as one event.
#     Formulaic vendor titles embedded in a varied corpus: the shared words
#     carry enough weight to cluster, but 40 advisories are not one incident.
_VARIED = [(1.0, 4, ["T4"], {"title": f"Unrelated report about topic {k} and matters {k*3}"}, False)
           for k in range(200)]
_TEMPLATE = [(2.0, 4, ["T4"],
              {"title": f"Zylonix Edge Gateway critical authentication bypass exploited CVE-2026-{k:05d}"},
              False) for k in range(40)]
_tg, _tgr, _td = group_near_duplicates(_TEMPLATE + _VARIED, {"grouping": {"max_group_size": 25}})
check("oversized cluster dissolved", _td >= 1, True)
check("dissolved items left ungrouped", all(i >= len(_TEMPLATE) for i in _tgr), True)
_tg2, _, _td2 = group_near_duplicates(_TEMPLATE + _VARIED, {"grouping": {"max_group_size": 100}})
check("same cluster kept when cap raised", max((len(m) for m in _tg2.values()), default=0) > 25, True)

print()
if FAILS:
    print(f"RESULT: FAIL — {len(FAILS)} check(s): {', '.join(FAILS)}")
    sys.exit(1)
print("RESULT: PASS")
