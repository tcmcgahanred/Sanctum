"""
Sanctum · tests/s2wo_test.py · the second-domain work order of 2026-10-29

Pins the five behaviours that order changed, each as it was measured:

  1. typographic apostrophes and hyphens are folded before any term matches
  2. the term search tool folds case on both sides, like the scorer
  3. the compliance report counts one event per surfaced group
  4. a domain whose two window settings disagree is refused at load
  5. s2 force-surface reads the conflict word and the aircraft in the title

Every non-ASCII character below is written with chr() so the file prints
cleanly on the authoring machine's cp1252 console.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml                                                     # noqa: E402
from core.lexicanum import make_all_hits                        # noqa: E402
from core.pnd import load_domain                                # noqa: E402
from core.rules import _scopes, make_matcher                    # noqa: E402
from core.arbites import force_surface_match                    # noqa: E402

FAILURES = []
RSQ = chr(0x2019)       # right single quotation mark, the typeset apostrophe
NBH = chr(0x2011)       # non-breaking hyphen


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
    if not ok:
        if detail:
            print(f"        {detail}")
        FAILURES.append(label)


def main():
    print("\n1. Typographic punctuation is folded before matching")
    m = make_matcher([])
    art = {"title": f"People{RSQ}s Liberation Army drills near Taiwan",
           "text": f"A Shahed{NBH}136 was seen."}
    _t, sc, _x = _scopes(art)
    check("a curly apostrophe matches a term typed with a straight one",
          m(sc["title"], ["People's Liberation Army"]) is not None)
    check("a non-breaking hyphen matches a term typed with a plain one",
          m(sc["blob"], ["Shahed-136"]) is not None)
    check("an en dash is NOT folded into a hyphen",
          "-" not in _scopes({"title": "a " + chr(0x2013) + " b",
                              "text": ""})[1]["title"])

    print("\n2. The term search tool folds case on both sides")
    hits = make_all_hits(["China"])
    check("a capitalised term is found in lowercased text",
          hits("china expands", ["China"]) == ["China"])
    check("a boundary-protected term keeps its boundary after folding",
          hits("chinese expands", ["China"]) == [])
    check("a long capitalised term is found as a substring",
          hits("the pantsir-s1 battery", ["Pantsir"]) == ["Pantsir"])

    print("\n3. The compliance report counts one event per surfaced group")
    tmp = Path(tempfile.mkdtemp())
    try:
        day = tmp / "corpus" / datetime.now(timezone.utc).strftime("%Y-%m-%d")
        day.mkdir(parents=True)
        now = datetime.now(timezone.utc)
        # Two reports of one event, one other event, and forty filler
        # headlines that do not surface. The filler is what gives the shared
        # words of the two reports enough weight to group: grouping weighs a
        # word by how rare it is among everything scored.
        ev = ("Suisun City declares emergency after ransomware cyberattack "
              "disrupts 911 dispatch systems")
        body = ("Suisun City in California declared a local emergency after a "
                "ransomware attack disrupted its 911 dispatch systems and the "
                "city reported a data breach.")
        items = [
            (ev + " - Reuters", body),
            (ev + " - Associated Press", body),
            ("Oregon water utility discloses ransomware attack on billing",
             "An Oregon water utility in the United States said a ransomware "
             "attack and data breach hit its billing systems this week."),
        ] + [(f"Gardening column number {k} about tomatoes and soil",
              "Plant tomatoes in spring and water them often.")
             for k in range(40)]
        for i, (t, b) in enumerate(items):
            (day / f"{i}.json").write_text(json.dumps({
                "title": t, "text": b, "url": f"https://example.test/{i}",
                "source": "https://example.test/feed",
                "collected": (now - timedelta(hours=2)).isoformat(),
                "published": format_datetime(now - timedelta(days=1)),
                "fetch_status": "ok", "body_source": "trafilatura"}),
                encoding="utf-8")
        out = tmp / "staging.md"
        r = subprocess.run([sys.executable, "-m", "core.arbites", "--pnd",
                            str(ROOT / "cti" / "pnd.yaml"), "--no-push",
                            "--out", str(out)], cwd=str(ROOT),
                           capture_output=True, text=True,
                           env={**__import__("os").environ,
                                "SANCTUM_BASE": str(tmp)})
        if r.returncode != 0:
            print(r.stdout[-1200:])
            print(r.stderr[-1200:])
            raise SystemExit("arbites failed to run")
        comp = next(tmp.glob("*ompliance*.md")).read_text(encoding="utf-8")
        sur = re.search(r"\| Surfaced candidates \| (\d+) \|", comp)
        ev = re.search(r"\| Distinct events after grouping \| (\d+) \|", comp)
        grouped = "event group" in out.read_text(encoding="utf-8")
        check("the fixture surfaces three items and groups two of them",
              sur is not None and sur.group(1) == "3" and grouped,
              f"surfaced={sur and sur.group(1)} grouped={grouped}")
        check("...which is two events, not one",
              ev is not None and ev.group(1) == "2",
              f"got {ev and ev.group(1)}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n4. Two window settings that disagree are refused")
    tmp = Path(tempfile.mkdtemp())
    try:
        d = tmp / "s2"
        shutil.copytree(ROOT / "s2", d)
        cfg = yaml.safe_load((d / "pnd.yaml").read_text(encoding="utf-8"))
        cfg["scoring"]["settings"]["recency"]["window_days"] = 6
        (d / "pnd.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False),
                                    encoding="utf-8")
        try:
            load_domain(pnd_path=d / "pnd.yaml")
            refused = False
        except ValueError as e:
            refused = "window_days" in str(e)
        check("collection 7 against recency 6 is refused", refused)
        check("the shipped s2 file loads",
              bool(load_domain(domain="s2")["scoring"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n5. s2 force-surface reads the conflict word and aircraft in the "
          "title")
    s2 = load_domain(domain="s2")["scoring"]
    fm = make_matcher(s2.get("word_boundary_terms"))
    body = ("A surface-to-air missile shot down a helicopter during the war, "
            "according to the report.")
    in_title = {"title": "Houthis shot down a Saudi helicopter near Najran",
                "text": body}
    in_body = {"title": "Business jet maker certifies missile protection kit",
               "text": body}
    check("a shoot-down named in the headline is forced",
          force_surface_match(in_title, s2["force_surface"], s2["groups"],
                              fm) is not None)
    check("the same words only in the body are not",
          force_surface_match(in_body, s2["force_surface"], s2["groups"],
                              fm) is None)

    print(f"\n{'PASS' if not FAILURES else 'FAIL'} - the s2 work order of "
          f"2026-10-29 holds")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
