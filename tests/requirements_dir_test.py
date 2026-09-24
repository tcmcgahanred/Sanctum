#!/usr/bin/env python3
"""
Sanctum · tests/requirements_dir_test.py

One requirement, one file. A rule reads on its own, and a tree that disagrees
with its files refuses to load.

WHY THIS EXISTS
---------------
The requirements lived inside `cti/pnd.yaml`, nested six levels deep. Written
out in full, with each rule carrying its own search terms instead of pointing
at a list defined 1,200 lines away, they would have taken that file past 3,000
lines. Nobody opened it to work on requirements, and 25 of 27 requirements had
nothing that could find them.

So the tree is a directory: `_tree.yaml` holds the priority intelligence
requirements, their indicators and `satisfied_by`, and names which rules sit
under each; every other file is one rule.

The failure this guards against is a tree and a set of files that disagree. A
listed rule with no file, and a file nobody lists, both look exactly like a
working tree from outside, and the second one is worse because the rule exists,
looks finished, and is never evaluated.

WHAT IS CHECKED
---------------
  assembly        a directory produces the same structure the block held
  fallback        a domain with no directory keeps its inline block
  two copies      a directory AND an inline block is refused
  dangling        a listed rule with no file is refused, naming it
  orphan          a file nobody lists is refused, naming it
  filename        a rule whose id does not match its filename is refused
  no tree         a directory with no _tree.yaml is refused
  bad status      a readiness value outside the four is refused
  blocked         `status: blocked` with no `blocked_by:` is refused
  dead block      a detection block nothing references is refused
  proximity       an operand of a proximity block counts as a reference
  condition       named blocks plus a condition line, with and / or / not
  bad condition   a condition naming a block that does not exist raises
  keywords        a rule carrying its own terms matches without a group
  live domain     cti loads from its directory, 27 rules, every one listed

    tests/requirements_dir_test.py      # exit 0 = a rule is a file
"""

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.pnd import load_domain, load_requirements                 # noqa: E402
from core.rules import (_scopes, eval_detection, make_matcher)      # noqa: E402

FAILURES = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
    if not ok:
        print(f"        got:  {got!r}")
        print(f"        want: {want!r}")
        FAILURES.append(label)


def refuses(label, fn, needle):
    try:
        fn()
        check(label, "loaded", "refused")
    except Exception as e:
        check(label, needle in str(e), True)
        if needle not in str(e):
            print(f"        message was: {e}")


TREE = """\
pirs:
- id: PIR-9
  name: test
  question: does this assemble?
  indicators:
  - id: IND-9.1
    statement: it assembles
    satisfied_by: any
    requirements: [SIR-9.1.1, SIR-9.1.2]
"""

RULE_A = """\
id: SIR-9.1.1
title: first
status: stable
fact: the first fact
decidable: machine
detection:
  alpha:
    keywords: [ransomware]
    scope: blob
  condition: alpha
"""

RULE_B = """\
id: SIR-9.1.2
title: second
status: draft
fact: the second fact
standard: nobody has written this detector yet
"""


def build(tmp, tree=TREE, rules=(("SIR-9.1.1", RULE_A), ("SIR-9.1.2", RULE_B))):
    d = Path(tmp)
    (d / "requirements").mkdir(parents=True, exist_ok=True)
    if tree is not None:
        (d / "requirements" / "_tree.yaml").write_text(tree, encoding="utf-8")
    for name, body in rules:
        (d / "requirements" / f"{name}.yaml").write_text(body, encoding="utf-8")
    return d


def ev(detection, art, groups=None):
    matcher = make_matcher([])
    _t, scopes, text_l = _scopes(art)
    return eval_detection(detection, groups or {}, matcher, scopes, text_l)


def art(title, text=""):
    return {"title": title, "text": text, "url": "https://example.test/a"}


def main():
    tmp = Path(tempfile.mkdtemp())
    try:
        print("\nA directory assembles into the structure the block used to hold")
        d = build(tmp / "ok")
        tree = load_requirements(d, None)
        check("one priority intelligence requirement", len(tree["pirs"]), 1)
        ind = tree["pirs"][0]["indicators"][0]
        check("its indicator keeps satisfied_by", ind["satisfied_by"], "any")
        check("the rules are assembled under `sirs`, the old name",
              [s["id"] for s in ind["sirs"]], ["SIR-9.1.1", "SIR-9.1.2"])
        check("...with their whole contents, not just identifiers",
              ind["sirs"][1]["standard"], "nobody has written this detector yet")
        check("...and `requirements:` is consumed, not left beside `sirs`",
              "requirements" in ind, False)

        print("\nA domain with no directory keeps its inline block")
        inline = {"pirs": [{"id": "PIR-8"}]}
        check("the inline block is returned untouched",
              load_requirements(tmp / "nothing-here", inline), inline)
        check("...and an empty one is not an error",
              load_requirements(tmp / "nothing-here", None), {})

        print("\nTwo sources of truth are refused")
        d2 = build(tmp / "both")
        refuses("a directory AND an inline block is refused",
                lambda: load_requirements(d2, inline), "BOTH")

        print("\nA tree and its files must agree")
        d3 = build(tmp / "dangling", rules=(("SIR-9.1.1", RULE_A),))
        refuses("a listed rule with no file is refused, naming it",
                lambda: load_requirements(d3, None), "SIR-9.1.2")

        d4 = build(tmp / "orphan", rules=(
            ("SIR-9.1.1", RULE_A), ("SIR-9.1.2", RULE_B),
            ("SIR-9.9.9", RULE_B.replace("SIR-9.1.2", "SIR-9.9.9"))))
        refuses("a file nobody lists is refused, naming it",
                lambda: load_requirements(d4, None), "SIR-9.9.9")

        d5 = build(tmp / "misnamed", rules=(
            ("SIR-9.1.1", RULE_A),
            ("SIR-9.1.2", RULE_B.replace("id: SIR-9.1.2", "id: SIR-0.0.0"))))
        refuses("a rule whose id does not match its filename is refused",
                lambda: load_requirements(d5, None), "named")

        d6 = build(tmp / "notree", tree=None)
        refuses("a directory with no _tree.yaml is refused",
                lambda: load_requirements(d6, None), "_tree.yaml")

        print("\nA readiness value must be one of the four, and `blocked` says by what")
        d7 = build(tmp / "badstatus", rules=(
            ("SIR-9.1.1", RULE_A.replace("status: stable", "status: analyst")),
            ("SIR-9.1.2", RULE_B)))
        refuses("a status outside the four is refused, naming it",
                lambda: load_requirements(d7, None), "analyst")

        d8 = build(tmp / "blocked", rules=(
            ("SIR-9.1.1", RULE_A.replace("status: stable", "status: blocked")),
            ("SIR-9.1.2", RULE_B)))
        refuses("`blocked` with no `blocked_by:` is refused",
                lambda: load_requirements(d8, None), "blocked_by")

        d9 = build(tmp / "blockedok", rules=(
            ("SIR-9.1.1", RULE_A.replace(
                "status: stable",
                "status: blocked\nblocked_by: the ATT&CK software list")),
            ("SIR-9.1.2", RULE_B)))
        check("...and accepted when it does",
              load_requirements(d9, None)["pirs"][0]["indicators"][0]
              ["sirs"][0]["blocked_by"], "the ATT&CK software list")

        # THE MIRROR OF A FILE NOBODY LISTS, and the worse of the two, because
        # the rule looks finished. SIR-3.1.1 shipped with a proximity block its
        # condition never named, so it fired on a vulnerability identifier
        # anywhere plus exploitation language anywhere: 235 matches in 30 days
        # and nothing said so.
        dead = RULE_A.replace(
            "  condition: alpha",
            "  beta:\n    keywords: [unused]\n    scope: blob\n  condition: alpha")
        d7 = build(tmp / "deadblock",
                   rules=(("SIR-9.1.1", dead), ("SIR-9.1.2", RULE_B)))
        refuses("a detection block nothing references is refused, naming it",
                lambda: load_requirements(d7, None), "beta")

        # ...but an operand of a proximity block IS referenced, even though the
        # condition never names it, and must not be refused.
        prox = RULE_A.replace(
            "  condition: alpha",
            "  beta:\n    keywords: [utility]\n    scope: blob\n"
            "  near:\n    proximity: {a: alpha, b: beta, window: 50, scope: blob}\n"
            "  condition: near")
        d8 = build(tmp / "proxok",
                   rules=(("SIR-9.1.1", prox), ("SIR-9.1.2", RULE_B)))
        tree8 = load_requirements(d8, None)
        check("a proximity operand counts as a reference",
              tree8["pirs"][0]["indicators"][0]["sirs"][0]["id"], "SIR-9.1.1")

        print("\nNamed blocks plus a condition line")
        det = {"code": {"pattern": r"\bT\d{4}\b", "scope": "blob"},
               "listicle": {"keywords": ["top 10", "biggest"], "scope": "title"},
               "geo": {"keywords": ["california"], "scope": "blob"},
               "condition": "code and not listicle"}
        check("the condition is satisfied", ev(det, art("Actor uses T1059")), True)
        check("`not` excludes", ev(det, art("Top 10 threats", "T1059")), False)
        check("a missing block makes it false", ev(det, art("nothing here")), False)

        det["condition"] = "code or geo"
        check("`or` takes either branch", ev(det, art("California city breached")), True)
        det["condition"] = "(code or geo) and not listicle"
        check("parentheses group as written",
              ev(det, art("Top 10 California stories", "T1059")), False)
        det["condition"] = "code and geo"
        check("`and` needs both",
              ev(det, art("Actor uses T1059 against a California city")), True)
        check("...and fails on one",
              ev(det, art("Actor uses T1059 against a Texas city")), False)

        print("\nA condition that names nothing real fails loudly")
        refuses("an unknown block name raises, listing the real ones",
                lambda: ev({"a": {"keywords": ["x"]}, "condition": "b"}, art("x")),
                "not a block in this detection")
        refuses("a detection with no condition line is refused",
                lambda: ev({"a": {"keywords": ["x"]}}, art("x")), "condition")

        print("\nA rule carries its own terms, so it reads on its own")
        own = {"incident": {"keywords": ["breach", "ransomware", "cyberattack"],
                            "scope": "blob"},
               "condition": "incident"}
        check("an inline term list matches with no group defined anywhere",
              ev(own, art("City hit by ransomware")), True)
        check("...and misses when absent", ev(own, art("City council meets")), False)

        print("\nThe live domain loads from its directory")
        cfg = load_domain(domain="cti")
        live = cfg["requirements"]
        sirs = [s for p in live["pirs"] for i in p["indicators"] for s in i["sirs"]]
        check("cti assembles 27 rules from files", len(sirs), 27)
        check("...5 priority intelligence requirements", len(live["pirs"]), 5)
        check("...14 indicators",
              sum(len(p["indicators"]) for p in live["pirs"]), 14)
        check("...every rule has a file named for its identifier",
              sorted(p.stem for p in (ROOT / "cti" / "requirements").glob("*.yaml")
                     if p.stem != "_tree"),
              sorted(s["id"] for s in sirs))
        check("...and every one carries a readiness value from the four",
              sorted({s.get("status") for s in sirs}),
              ["blocked", "draft", "stable", "unsupported"])
        check("...none of which is the retired `decidable:`",
              [s["id"] for s in sirs if "decidable" in s], [])
        check("...and every blocked rule names its missing input",
              [s["id"] for s in sirs if s.get("status") == "blocked"
               and not str(s.get("blocked_by") or "").strip()], [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if FAILURES:
        print(f"FAIL — {len(FAILURES)} problem(s)")
        for f in FAILURES:
            print(f"    {f}")
        return 1
    print("PASS — one requirement is one file, the tree and its files must "
          "agree, and a condition line reads as a sentence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
