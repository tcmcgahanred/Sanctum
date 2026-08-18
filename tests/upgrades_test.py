#!/usr/bin/env python3
"""
Sanctum · tests/upgrades_test.py

Proves the two 2026-08-16 upgrades:

  1. The exclusion operator (`not`) in the rule grammar.
  2. Lexicanum — archive search and match-frequency counting.

The exclusion tests care most about what must NOT change. A new operator that
alters scores for domains that never use it would be a silent regression across
every existing edition, so the first thing checked is that a config without
`not` in it scores exactly as before.

    tests/upgrades_test.py        # exit 0 = both upgrades work
"""

import json
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.rules import score_article, _eval_atom, make_matcher, _scopes  # noqa: E402
from core.lexicanum import (make_all_hits, bucket, published_date,       # noqa: E402
                            walk_corpus, search, render)
from core.arbites import (staging_target, push_staging,                  # noqa: E402
                          force_surface_match)

FAILURES = []


def check(label, got, want):
    if got == want:
        print(f"  ok    {label}")
    else:
        FAILURES.append(f"{label}: got {got!r}, want {want!r}")
        print(f"  FAIL  {label}: got {got!r}, want {want!r}")


def art(title, text="", published="", url="https://example.com/x"):
    return {"title": title, "text": text, "published": published, "url": url,
            "source": "test"}


# ==================================================================
# 1. EXCLUSION OPERATOR
# ==================================================================
# The collision used throughout: `lazarus` is a long-documented threat actor
# AND a widely used open-source development environment. Both are ordinary
# subjects for a general technology feed, so the term cannot simply be dropped
# and neither can the source.
GROUPS = {
    "actor":    ["lazarus", "sandworm"],
    "dev_tool": ["free pascal", "open-source ide", "release notes"],
    "region":   ["north county"],
}


def ev(atom, a):
    _, scopes, text_l = _scopes(a)
    return _eval_atom(atom, GROUPS, make_matcher(None), scopes, text_l)


def test_exclusion():
    print("\nExclusion operator")

    intrusion = art("Lazarus linked to exchange intrusion",
                    "Investigators attributed the theft to Lazarus operators.")
    software = art("Lazarus 3.0 released",
                   "The open-source IDE ships a new free pascal compiler; "
                   "see the release notes.")

    match_x = {"group": "actor"}
    check("bare group matches the intrusion article", ev(match_x, intrusion), True)
    check("bare group ALSO matches the software release (the problem)",
          ev(match_x, software), True)

    unless = {"all": [{"group": "actor"}, {"not": {"group": "dev_tool"}}]}
    check("with exclusion, intrusion article still matches", ev(unless, intrusion), True)
    check("with exclusion, software release no longer matches", ev(unless, software), False)

    # not/not and nesting
    check("double negation", ev({"not": {"not": {"group": "actor"}}}, intrusion), True)
    check("not over 'any'", ev({"not": {"any": [{"group": "dev_tool"}]}}, intrusion), True)
    check("not over 'all'", ev({"not": {"all": [{"group": "actor"},
                                                {"group": "region"}]}}, intrusion), True)
    check("not over always is False", ev({"not": "always"}, intrusion), False)

    # Reason strings must name the exclusion — tenet 8.
    scoring = {
        "groups": GROUPS,
        "tiers": [{"id": 1, "name": "actor not dev_tool", "weight": 8.0,
                   "require": {"all": [{"group": "actor"},
                                       {"not": {"group": "dev_tool"}}]}},
                  {"id": 4, "name": "floor", "weight": 1.0, "require": "always"}],
        "multipliers": [],
    }
    s, tier, reasons = score_article(intrusion, scoring)
    check("excluded-rule item scores at the tier", (s, tier), (8.0, 1))
    check("reasoning names the exclusion",
          any("not dev_tool" in r for r in reasons), True)

    s_rel, tier_rel, _ = score_article(software, scoring)
    check("software release falls to the floor, not dropped",
          (s_rel, tier_rel), (1.0, 4))


def test_exclusion_changes_nothing_else():
    """A config with no `not` in it must behave exactly as before."""
    print("\nExclusion is inert when unused")

    scoring = {
        "groups": GROUPS,
        "tiers": [{"id": 1, "name": "region+actor", "weight": 8.0,
                   "require": {"all": [{"group": "region"}, {"group": "actor"}]}},
                  {"id": 2, "name": "actor", "weight": 4.0,
                   "require": {"group": "actor"}},
                  {"id": 4, "name": "floor", "weight": 1.0, "require": "always"}],
        "multipliers": [{"factor": 1.5, "name": "region", "when": {"group": "region"}}],
    }
    cases = [
        (art("Lazarus hits North County", "north county lazarus"), 12.0, 1),
        (art("Lazarus campaign widens", "a lazarus operation"),     4.0, 2),
        (art("Unrelated weather report", "rain"),                   1.0, 4),
        (art("North County budget meeting", "north county council"), 1.5, 4),
    ]
    for a, want_s, want_t in cases:
        s, t, _ = score_article(a, scoring)
        check(f"unchanged: {a['title'][:34]!r}", (s, t), (want_s, want_t))


# ==================================================================
# 2. LEXICANUM
# ==================================================================
CORPUS = {
    "2026-01-05": [("Emotet resurfaces in phishing waves", "An Emotet loader was observed.",
                    "2026-01-04")],
    "2026-01-08": [("Emotet infrastructure shifts hosts", "The Emotet operators moved on.",
                    "2026-01-07"),
                   ("Unrelated shipping news", "Containers.", "2026-01-07")],
    "2026-02-02": [("Two Emotet clusters confirmed", "Emotet and Qakbot seen together.",
                    "2026-02-01"),
                   ("Qakbot delivery observed", "A Qakbot payload arrived.", ""),
                   ("LockBit affiliate charged", "A LockBit affiliate was named.",
                    "not a date")],
    "not-a-date": [("Should be ignored", "Emotet", "2026-02-02")],
}

TARGET_GROUPS = {
    "malware_loader": ["emotet", "qakbot"],
    "ransom_brand":   ["lockbit"],
    "never_hits":     ["zzz-nonexistent"],
}


def build_corpus(root):
    for day, items in CORPUS.items():
        d = root / day
        d.mkdir(parents=True)
        for i, (title, text, pub) in enumerate(items):
            (d / f"{i}.json").write_text(json.dumps(
                {"title": title, "text": text, "published": pub,
                 "url": f"https://example.com/{day}/{i}", "source": "test"}))
    # a truncated file must not stop the walk
    (root / "2026-01-05" / "broken.json").write_text("{ not json")


def test_lexicanum():
    print("\nLexicanum — archive search")

    hits = make_all_hits(None)
    check("returns EVERY matching term, not just the first",
          sorted(hits("emotet and qakbot seen", ["emotet", "qakbot"])),
          ["emotet", "qakbot"])
    check("short terms respect word boundaries",
          hits("physics", ["ics"]), [])

    check("week bucket", bucket(date(2026, 1, 5), "week"), "2026-W02")
    check("month bucket", bucket(date(2026, 2, 2), "month"), "2026-02")
    check("day bucket", bucket(date(2026, 2, 2), "day"), "2026-02-02")

    check("iso publication date parses", published_date({"published": "2026-01-04"}),
          date(2026, 1, 4))
    check("rfc-822 publication date parses",
          published_date({"published": "Sat, 04 Jan 2026 10:00:00 +0000"}),
          date(2026, 1, 4))
    check("junk publication date returns None",
          published_date({"published": "not a date"}), None)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "corpus"
        build_corpus(root)

        walked = list(walk_corpus(root))
        check("undated directory is skipped", len(walked), 6)
        check("truncated file does not stop the walk",
              all(isinstance(a, dict) for _, a in walked), True)

        since_only = list(walk_corpus(root, since=date(2026, 2, 1)))
        check("--since filters", len(since_only), 3)

        cfg = {"domain": "test", "corpus_dir": root,
               "scoring": {"groups": TARGET_GROUPS, "word_boundary_terms": None}}

        h, series, per_term, totals, scanned, undated = search(
            cfg, TARGET_GROUPS, None, None, "month", False)

        check("scanned every dated article", scanned, 6)
        check("loader group hit count", sum(series["malware_loader"].values()), 4)
        check("ransom group hit count", sum(series["ransom_brand"].values()), 1)
        check("a group with no hits reports zero, not an error",
              sum(series["never_hits"].values()), 0)

        check("series buckets by month",
              dict(series["malware_loader"]), {"2026-01": 2, "2026-02": 2})

        check("per-term counts split within a group",
              dict(per_term["malware_loader"]), {"emotet": 3, "qakbot": 2})

        one = [x for x in h if x.group == "malware_loader" and x.day == date(2026, 2, 2)
               and "Two Emotet" in x.title][0]
        check("a hit carries both terms it matched", sorted(one.terms),
              ["emotet", "qakbot"])
        check("a hit carries its source", one.source, "example.com")
        check("a hit carries its publication date", one.pub, date(2026, 2, 1))

        # Retroactive question: a group invented now, run over old material.
        new_group = {"invented_today": ["shipping"]}
        _, ser_new, _, _, _, _ = search(cfg, new_group, None, None, "month", False)
        check("a brand-new group finds old articles",
              sum(ser_new["invented_today"].values()), 1)

        # Publication-date axis, including the undated fallback.
        _, ser_pub, _, _, _, und = search(cfg, {"g": ["qakbot", "lockbit"]},
                                       None, None, "month", True)
        check("undated items are counted, not discarded", und, 2)
        check("published axis still totals every hit", sum(ser_pub["g"].values()), 3)


def test_denominator():
    """
    The production trap, reproduced.

    On the first real run, weekly ransomware hits fell 475 -> 122 and read as a
    collapse. Article volume that week had fallen 6,585 -> 1,370, so the RATE
    had actually risen. Counts alone said the opposite of the truth.

    This builds the same shape at small scale: a heavy month and a light month
    with the SAME underlying rate, and asserts the denominators expose it.
    """
    print("\nLexicanum — collection volume must not read as a trend")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "corpus"
        # January: 100 articles, 20 mention the term.
        # February:  10 articles,  2 mention the term.
        # Counts collapse 20 -> 2. The rate is flat at 20%.
        for day, n, hitting in (("2026-01-10", 100, 20), ("2026-02-10", 10, 2)):
            d = root / day
            d.mkdir(parents=True)
            for i in range(n):
                body = "emotet loader seen" if i < hitting else "unrelated filler"
                (d / f"{i}.json").write_text(json.dumps(
                    {"title": f"item {i}", "text": body, "published": day,
                     "url": f"https://example.com/{day}/{i}", "source": "test"}))

        cfg = {"domain": "test", "corpus_dir": root,
               "scoring": {"groups": {}, "word_boundary_terms": None}}
        targets = {"loader": ["emotet"]}

        _, series, _, totals, scanned, _ = search(
            cfg, targets, None, None, "month", False)

        check("every article counted in the denominator, hit or not",
              dict(totals), {"2026-01": 100, "2026-02": 10})
        check("raw counts look like a 90% collapse",
              dict(series["loader"]), {"2026-01": 20, "2026-02": 2})

        rates = {b: round(100.0 * series["loader"][b] / totals[b], 1) for b in totals}
        check("but the rate is flat — the collapse was collection volume",
              rates, {"2026-01": 20.0, "2026-02": 20.0})

        report = render(cfg, targets, [], series, {"loader": {}}, totals,
                        scanned, 0, "month", False, True, None, None)
        check("report states collection volume per period",
              "Articles collected per month" in report, True)
        check("report shows the denominator column", "| of |" in report, True)
        check("report shows the rate, not just the count", "20.0%" in report, True)
        check("report tells the reader to read the rate",
              "Read the rate, not the count" in report, True)


def test_staging_push():
    """
    The staging hand-off. Naming is tested without touching the network,
    because the thing that matters is that consecutive runs do NOT collide.
    """
    print("\nStaging push — dated, and off by default when unconfigured")

    d = date(2026, 8, 17)
    nxt = date(2026, 8, 18)

    check("no staging block configured -> no push",
          staging_target({}, d), (None, None))
    check("backend other than rclone -> no push",
          staging_target({"staging": {"backend": "local"}}, d), (None, None))
    check("backend set but no remote -> no push",
          staging_target({"staging": {"backend": "rclone"}}, d), (None, None))

    m = {"staging": {"backend": "rclone", "rclone_remote": "gdrive:staging",
                     "filename": "WCTI_{date}_STAGING.md"}}
    check("remote passed through", staging_target(m, d)[0], "gdrive:staging")
    check("date substituted into the filename",
          staging_target(m, d)[1], "WCTI_20260817_STAGING.md")

    # The reason the name is dated at all: a fixed name would be overwritten by
    # the next daily run, potentially on top of a draft already being edited.
    check("consecutive days do not collide",
          staging_target(m, d)[1] != staging_target(m, nxt)[1], True)

    check("filename defaults sensibly when omitted",
          staging_target({"staging": {"backend": "rclone",
                                      "rclone_remote": "r:p"}}, d)[1],
          "staging_20260817.md")

    # A failed push must warn and return None, never raise — the local copy
    # already exists and a bad network is not a lost cycle.
    msgs = []
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "staging.md"
        f.write_text("x")
        bad = {"staging": {"backend": "rclone",
                           "rclone_remote": "nonexistent-remote-xyz:p"}}
        got = push_staging(bad, f, d, log=msgs.append)
    check("failed push returns None instead of raising", got, None)
    check("failed push warns and names the local copy",
          bool(msgs) and "WARNING" in msgs[0] and "staging.md" in msgs[0], True)


def test_force_surface():
    """
    Vox Policy §7: surface-vs-drop is a threshold plus guaranteed inclusions,
    never a count. The most important assertion here is the LIMIT — a force
    rule cannot surface something the domain's vocabulary cannot describe.
    """
    print("\nForce-surface — inclusion, not ranking")

    groups = {
        "place":    ["north county", "the valley"],
        "incident": ["ransomware", "breach"],
        "kev":      ["kev catalog"],
        "tech":     ["wordpress"],
    }
    m = make_matcher(None)
    rules = [
        {"name": "M1 place in an incident",
         "when": {"all": [{"group": "place"}, {"group": "incident"}]}},
        {"name": "M2 KEV affecting relevant tech",
         "when": {"all": [{"group": "kev"}, {"group": "tech"}]}},
    ]

    local = art("North County hit by ransomware", "A ransomware attack on the county.")
    kev = art("KEV catalog adds WordPress flaw", "Added to the KEV catalog; WordPress affected.")
    plain = art("Weather report", "Rain expected.")

    check("no rules configured -> nothing is forced",
          force_surface_match(local, [], groups, m), None)
    check("M1 fires on place + incident",
          force_surface_match(local, rules, groups, m), "M1 place in an incident")
    check("M2 fires on KEV + relevant tech",
          force_surface_match(kev, rules, groups, m), "M2 KEV affecting relevant tech")
    check("an unrelated item is not forced",
          force_surface_match(plain, rules, groups, m), None)
    check("first matching rule wins, in declared order",
          force_surface_match(art("North County ransomware and KEV catalog wordpress", ""),
                              rules, groups, m), "M1 place in an incident")

    # A bad rule must not take the cycle down — the run always produces a document.
    bad = [{"name": "typo", "when": {"group": "no_such_group"}}]
    check("a rule naming a missing group is skipped, not fatal",
          force_surface_match(local, bad, groups, m), None)
    check("a malformed atom is skipped, not fatal",
          force_surface_match(local, [{"name": "junk", "when": {"nonsense": 1}}], groups, m), None)

    # THE LIMIT, and it is the point of this test.
    # "Website defaced" is a real incident against an in-AOR entity. The place
    # matches; the incident word does not exist in the vocabulary. So the
    # guarantee does not hold — and it is bounded by the word lists, not the rule.
    defaced = art("North County town website defaced", "The city site was defaced overnight.")
    check("GUARANTEE IS BOUNDED BY VOCABULARY: an incident word that is not in "
          "the group cannot be force-surfaced",
          force_surface_match(defaced, rules, groups, m), None)
    check("...and it starts working the moment the vocabulary covers it",
          force_surface_match(defaced, rules,
                              {**groups, "incident": groups["incident"] + ["defaced"]}, m),
          "M1 place in an incident")


def run():
    test_exclusion()
    test_exclusion_changes_nothing_else()
    test_lexicanum()
    test_denominator()
    test_staging_push()
    test_force_surface()
    print()
    if FAILURES:
        print(f"FAIL — {len(FAILURES)} problem(s)")
        for f in FAILURES:
            print(f"    {f}")
        return 1
    print("PASS — exclusion works and changes nothing unused; archive search "
          "and counting verified")
    return 0


if __name__ == "__main__":
    sys.exit(run())
