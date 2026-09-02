#!/usr/bin/env python3
"""
Sanctum · tests/vocab_check_test.py

Tests tools/vocab_check.py against synthetic domains. Synthetic on purpose: a
test bound to a live domain file starts failing the day someone edits a word
list, which trains people to ignore it.

Examples here are deliberately neutral. No real domain's vocabulary appears in
this file.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.vocab_check import check_domain, load_vocab, ERROR, WARN, NOTED  # noqa: E402

FAILED = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
    if not ok:
        print(f"        got:  {got!r}")
        print(f"        want: {want!r}")
        FAILED.append(label)


def cfg(groups, boundary=None):
    return {"scoring": {"groups": groups, "word_boundary_terms": boundary or []}}


def kinds(findings, severity=None):
    """The set of check names fired, optionally filtered by severity."""
    return sorted({f.check for f in findings
                   if severity is None or f.severity == severity})


def subjects(findings, check_name):
    return sorted(f.subject for f in findings if f.check == check_name)


TODAY = date(2026, 8, 17)

print("\nA clean domain")
clean = cfg({"alpha": ["widget assembly", "sprocket"],
             "beta": ["quarterly filing"]},
            boundary=["sprocket"])
check("no findings at all", check_domain("t", clean, {}, TODAY), [])

print("\nOrphaned boundary terms — the decay manual review misses")
orphan = cfg({"alpha": ["widget assembly"]}, boundary=["gone", "widget assembly"])
f = check_domain("t", orphan, {}, TODAY)
check("an entry matching no live term is an ERROR",
      [(x.severity, x.check) for x in f], [(ERROR, "orphaned boundary term")])
check("names the dead entry", subjects(f, "orphaned boundary term"), ["'gone'"])

print("  ...the substring trap specifically")
# 'hack' as a boundary entry does NOT cover the live term 'hacked'. Strings are
# compared whole. This is the exact shape of the real-world finding.
trap = cfg({"alpha": ["hacked"]}, boundary=["hack"])
check("a boundary entry is not covered by a longer live term containing it",
      kinds(check_domain("t", trap, {}, TODAY), ERROR),
      ["orphaned boundary term"])

print("\nRedundant boundary terms — harmless, still worth saying")
red = cfg({"alpha": ["abc"]}, boundary=["abc"])
f = check_domain("t", red, {}, TODAY)
check("<=4 chars is a WARN, not an ERROR",
      [(x.severity, x.check) for x in f], [(WARN, "redundant boundary term")])
check("a 5-char entry is load-bearing and silent",
      check_domain("t", cfg({"alpha": ["abcde"]}, boundary=["abcde"]), {}, TODAY),
      [])

print("\nPadded terms — spaces that look like a guard and are not")
# The matcher strips every term, so " x " never behaves as written.
f = check_domain("t", cfg({"alpha": [" longword "]}), {}, TODAY)
check("a padded term above the auto-boundary length is an ERROR",
      [(x.severity, x.check) for x in f], [(ERROR, "padded term")])
check("the finding names the group", subjects(f, "padded term"),
      ["' longword ' in alpha"])
check("a padded SHORT term is only a WARN — length saves it",
      [(x.severity, x.check) for x in
       check_domain("t", cfg({"alpha": [" abc "]}), {}, TODAY)],
      [(WARN, "padded term")])
check("an unpadded term is silent",
      check_domain("t", cfg({"alpha": ["longword"]}), {}, TODAY), [])

print("\nEmpty groups")
f = check_domain("t", cfg({"alpha": [], "beta": ["real term"]}), {}, TODAY)
check("an empty group is an ERROR", kinds(f, ERROR), ["empty group"])
check("only the empty one is named", subjects(f, "empty group"), ["alpha"])

print("\nDropped terms that are still live — the drift the two files exist to stop")
vocab = {"dropped": [{"term": "Ambiguous", "reason": "collides", "date": "2026-08-01"}]}
f = check_domain("t", cfg({"alpha": ["ambiguous", "other"]}), vocab, TODAY)
check("a term marked dropped but still in pnd.md is an ERROR",
      kinds(f, ERROR), ["dropped term still live"])
check("matching is case-insensitive", subjects(f, "dropped term still live"),
      ["'Ambiguous'"])
check("a genuinely removed term is silent",
      check_domain("t", cfg({"alpha": ["other"]}), vocab, TODAY), [])
check("a malformed dropped record is skipped, not fatal",
      check_domain("t", cfg({"alpha": ["other"]}),
                   {"dropped": ["not a mapping", None]}, TODAY), [])

print("\nStaleness")
gm = {"review_interval_days": 90,
      "groups": {"alpha": {"reviewed": "2026-01-01"},
                 "beta": {"reviewed": "2026-08-10"}}}
f = check_domain("t", cfg({"alpha": ["x term"], "beta": ["y term"]}), gm, TODAY)
check("a group past its interval is a WARN", kinds(f, WARN), ["stale group"])
check("only the stale group is named", subjects(f, "stale group"), ["alpha"])
check("staleness never blocks a commit",
      [x for x in f if x.severity == ERROR], [])

print("  ...per-group override for fast-decaying groups")
gm2 = {"review_interval_days": 365,
       "groups": {"fast": {"reviewed": "2026-06-01", "review_interval_days": 30}}}
check("a per-group interval overrides the domain default",
      subjects(check_domain("t", cfg({"fast": ["z term"]}), gm2, TODAY),
               "stale group"),
      ["fast"])

print("  ...and the boundaries of nagging")
check("no vocab.md at all -> no staleness noise, only structural checks",
      check_domain("t", cfg({"alpha": ["x term"]}), {}, TODAY), [])
check("once dates are being recorded, a group without one is flagged",
      subjects(check_domain("t", cfg({"alpha": ["x"], "beta": ["y"]}),
                            {"review_interval_days": 90,
                             "groups": {"alpha": {"reviewed": "2026-08-16"}}},
                            TODAY),
               "no review date"),
      ["beta"])
check("an unparseable review date is treated as no date, not a crash",
      subjects(check_domain("t", cfg({"alpha": ["x"]}),
                            {"review_interval_days": 90,
                             "groups": {"alpha": {"reviewed": "last Tuesday"}}},
                            TODAY),
               "no review date"),
      ["alpha"])

print("\nTracked-only discovery — the commit gate must not block on gitignored domains")
# A second effort held out of the public repo, or a stub that is not
# operational, cannot reach the repo the gate protects. Blocking a commit over
# one teaches people to reach for --no-verify, which switches off every other
# check too. Manual runs still see them.
from tools.vocab_check import git_tracked, discover_domains, REPO_ROOT  # noqa: E402

check("a tracked file is reported tracked",
      git_tracked(REPO_ROOT, "README.md"), True)
check("a path git has never seen is reported untracked",
      git_tracked(REPO_ROOT, "no/such/file/anywhere.md"), False)
check("tracked-only is a subset of the full sweep",
      set(discover_domains(REPO_ROOT, tracked_only=True))
      <= set(discover_domains(REPO_ROOT)), True)
check("the tracked domain is never dropped from the gate",
      "cti" in discover_domains(REPO_ROOT, tracked_only=True), True)
# A leading underscore means "not a domain" (docs/DOMAINS.md). It exists so a
# folder holding domain-shaped files without being a domain is not reported as
# broken forever, and a guard that always fails is a guard people ignore.
check("an underscore-prefixed folder is not treated as a domain",
      [d for d in discover_domains(REPO_ROOT) if d.startswith("_")], [])

print("\nRequirement attribution — which intelligence requirement a keyword feeds")

# A domain with rules, so the orphan check is live.
def ruled(groups, tier_group="alpha"):
    return {"scoring": {"groups": groups, "word_boundary_terms": [],
                        "tiers": [{"id": 1, "weight": 8.0,
                                   "require": {"group": tier_group}},
                                  {"id": 2, "weight": 1.0, "require": "always"}]}}

two = ruled({"alpha": ["real term"], "beta": ["other term"]})

# Bootstrap: a domain that has never used the convention says nothing about it.
check("no group declares an attribution -> no attribution noise",
      "unattributed group" in kinds(check_domain("t", two, {}, TODAY)), False)

vocab_one = {"groups": {"alpha": {"serves": ["PIR-1"]}}}
check("once ONE group declares, the silent ones are named",
      subjects(check_domain("t", two, vocab_one, TODAY), "unattributed group"),
      ["beta"])
check("...and it is a WARN, never an ERROR",
      kinds(check_domain("t", two, vocab_one, TODAY), ERROR), [])

both = {"groups": {"alpha": {"serves": ["PIR-1"]},
                   "beta": {"serves": ["PIR-2"], "role": "elevation"}}}
check("declaring both serves and role is a conflict",
      subjects(check_domain("t", two, both, TODAY), "attribution conflict"),
      ["beta"])

bogus = {"groups": {"alpha": {"serves": ["PIR-1"]}, "beta": {"role": "banana"}}}
check("an unknown role is named rather than accepted",
      kinds(check_domain("t", two, bogus, TODAY), WARN)
      .count("unknown group role"), 1)

print("\nGroups no rule consumes — invisible vocabulary")

# beta is declared, holds terms, and no tier reads it.
check("an unread group is a WARN",
      subjects(check_domain("t", two, {}, TODAY), "group consumed by no rule"),
      ["beta"])

deliberate = {"groups": {"beta": {"role": "unused",
                                  "unused_because": "split from alpha; kept on purpose"}}}
f = check_domain("t", two, deliberate, TODAY)
check("declared unused with a reason downgrades to NOTED",
      [x.severity for x in f if x.check == "group consumed by no rule"], [NOTED])
check("...and it keeps printing rather than being silenced",
      subjects(f, "group consumed by no rule"), ["beta"])

no_reason = {"groups": {"beta": {"role": "unused"}}}
check("declaring it unused without saying why stays a WARN",
      [x.severity for x in check_domain("t", two, no_reason, TODAY)
       if x.check == "group consumed by no rule"], [WARN])

# The production key lives OUTSIDE scoring. A checker that only walks `scoring`
# reports a section-suggester group as dead. That mistake was made on 2026-08-26.
prod = ruled({"alpha": ["real term"], "beta": ["other term"]})
prod["production"] = {"staging_annotations":
                      {"sections": [{"name": "S", "when": {"group": "beta"}}]}}
check("a group used only by the section suggester is NOT reported dead",
      subjects(check_domain("t", prod, {}, TODAY), "group consumed by no rule"), [])

# A stub with vocabulary but no rules yet is not a domain with dead groups.
check("a domain with no rules at all is exempt",
      subjects(check_domain("t", cfg({"alpha": ["real term"]}), {}, TODAY),
               "group consumed by no rule"), [])


print("\nvocab.md parsing")
missing = Path("/nonexistent/does/not/exist/vocab.md")
check("an absent vocab.md yields {} rather than raising", load_vocab(missing), {})

print()
if FAILED:
    print(f"RESULT: FAIL — {len(FAILED)} check(s) failed")
    for x in FAILED:
        print(f"  - {x}")
    sys.exit(1)
print("RESULT: PASS — vocabulary guard catches every decay mode it claims to")
