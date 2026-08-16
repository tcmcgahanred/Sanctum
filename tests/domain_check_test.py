#!/usr/bin/env python3
"""
Sanctum · tests/domain_check_test.py

Proves the domain-file guardrail before it is trusted to block a commit.

A guard that passes everything is worse than no guard, because it reads as
assurance. So this exercises both directions: a realistic clean domain file
must pass untouched, and every form of behavior we care about must be caught.

    tests/domain_check_test.py        # exit 0 = the guard works
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from domain_check import check_source  # noqa: E402


# A realistic domain file in the shape a real one would take: comments carrying
# the explanation that used to live in prose, and nothing else.
CLEAN = '''
"""Example domain — Planning & Direction."""

# Shared once, used in two groups below. Retyping a term list is how the two
# copies drift apart.
ASSETS = ["water treatment", "wastewater", "pumping station", "scada"]

manifest = {
    "domain": "example",
    "base_dir": None,          # resolved from SANCTUM_BASE at runtime
    "corpus": {"backend": "rclone", "rclone_remote": "drive:sanctum/example"},
}

scoring = {
    "groups": {
        "asset": ASSETS,
        "asset_wide": ASSETS,
        "region": ["north county", "coastal district", "the valley"],
    },
    # 8/4/2/1. A fully elevated Tier 2 item can outrank a bare Tier 1 item;
    # that is intended — convergence is the signal.
    "tiers": [
        {"weight": 8.0, "require": {"proximity": {"a": "region", "b": "asset",
                                                  "window": 120}}},
        {"weight": 4.0, "require": {"group": "asset_wide"}},
        {"weight": 1.0, "require": "always"},
    ],
    "multipliers": [
        {"factor": 1.3, "when": {"group": "region"}},
    ],
    "settings": {"window_days": 30, "min_score": -1},
}
'''

DIRTY = [
    ("import os",                                   "Import"),
    ("from pathlib import Path",                    "ImportFrom"),
    ("def weight(x):\n    return x",                "FunctionDef"),
    ("class Cfg:\n    pass",                        "ClassDef"),
    ("if True:\n    a = 1",                         "If"),
    ("for x in [1]:\n    a = x",                    "For"),
    ("while False:\n    pass",                      "While"),
    ("try:\n    a = 1\nexcept Exception:\n    pass", "Try"),
    ("a = open('x')",                               "Call"),
    ("a = lambda: 1",                               "Lambda"),
    ("a = 1 if True else 2",                        "IfExp"),
    ("a = [x for x in [1]]",                        "ListComp"),
    ("a = {k: 1 for k in []}",                      "DictComp"),
    ("a = os.environ",                              "Attribute"),
    ("a = [1]\nb = a[0]",                           "Subscript"),
    ("a = 2 + 2",                                   "BinOp"),
    ("a = True and False",                          "BoolOp"),
    ("a = 1 == 2",                                  "Compare"),
    ("n = 'x'\na = f'{n}!'",                        "JoinedStr"),
    ("assert True",                                 "Assert"),
    ("raise ValueError('x')",                       "Raise"),
    ("a = 1\na += 1",                               "+= assignment"),
    ("a = {'k': 1}\nb = {**a}",                     "dict merge"),
    ("a = [1]\nb = [*a]",                           "unpacking"),
    ("a = UNDEFINED_NAME",                          "reference to 'UNDEFINED_NAME'"),
    ("a = [1, 2 + 2]",                              "BinOp"),          # nested in a list
    ("a = {'k': [1, os.sep]}",                      "Attribute"),      # nested two deep
    ("a = (1, open('x'))",                          "Call"),           # nested in a tuple
]


def run():
    failures = []

    # --- must pass ---------------------------------------------------------
    v = check_source(CLEAN, "clean.py")
    if v:
        failures.append("clean domain file was rejected:\n" + "\n".join(
            f"      line {x.line}: {x.construct} — {x.why}" for x in v))
    else:
        print("  ok    clean domain file passes")

    # negative numbers and a bare docstring must survive
    for src, label in (("a = -3", "negative number"),
                       ('"""doc"""\na = 1', "docstring"),
                       ("a = None", "None"),
                       ("x = ['a']\ny = {'g': x}", "reference to earlier name")):
        if check_source(src, "ok.py"):
            failures.append(f"{label} was wrongly rejected")
        else:
            print(f"  ok    {label} passes")

    # --- must be caught ----------------------------------------------------
    for src, expected in DIRTY:
        v = check_source(src, "dirty.py")
        if not v:
            failures.append(f"NOT CAUGHT: {expected!r} in {src!r}")
            continue
        found = [x.construct for x in v]
        if expected not in found:
            failures.append(
                f"wrong reason for {src!r}: expected {expected!r}, got {found!r}")
        else:
            print(f"  ok    caught {expected}")

    # --- every violation must explain itself -------------------------------
    for src, _ in DIRTY:
        for x in check_source(src, "dirty.py"):
            if not x.why or len(x.why) < 10:
                failures.append(f"unhelpful message for {x.construct!r}: {x.why!r}")

    print()
    if failures:
        print(f"FAIL — {len(failures)} problem(s):")
        for f in failures:
            print(f"    {f}")
        return 1
    print(f"PASS — clean file accepted, {len(DIRTY)} behaviors refused, "
          f"all with plain-language reasons")
    return 0


if __name__ == "__main__":
    sys.exit(run())
