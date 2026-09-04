#!/usr/bin/env python3
"""
Sanctum · tests/page_recollect_test.py

A portal keeps one URL and changes its contents. Identity must follow the
contents.

WHY THIS EXISTS
---------------
`process_page` opened with `if uid(url) in seen: return`, and on success wrote
that same URL hash to seen.txt. So a source that is a web page rather than a
feed was fetched exactly once, ever, and every later run returned without
making a request. Two planned sensors were blocked on it — the California
Attorney General breach registry and Cal-CSIC advisories are both portals whose
URL never changes — and one of them is the only authoritative in-area breach
source for the highest-weighted requirement in the domain.

Two things had to change together, because fixing one without the other fixes
nothing:

  IDENTITY   a page snapshot is keyed on a hash of its normalised text, so new
             material posted under an unchanging URL is new, and a reflowed
             page is not.
  TITLE      a page has no headline, and the scorer floors and flags an
             untitled record — so a re-read portal could never have surfaced
             however fresh it was. `title:` on the sensor record is how the
             domain says what the page is.

And one thing had to stay exactly as it was. `process_feed` returns None
whenever a feed yields no entries — including a healthy feed having a bad day —
so this function also receives real feeds. Re-reading those every run would
write a fresh record every time an error page reflowed. **Re-collection is
therefore opt-in: `kind: page`, declared by the domain.**

WHAT IS CHECKED
---------------
  declared page      re-read every run; unchanged content saves nothing
  changed content    saves a second record, and both survive in the corpus
  identity           the record id is the content hash, not the URL hash
  declared title     reaches the record, so the scorer can judge it
  no title           unchanged behaviour — the record carries none
  undeclared source  a non-feed with no `kind` is still collected ONCE
  kind typo          refused at load, naming the value

    tests/page_recollect_test.py       # exit 0 = a portal can be watched
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.acolyte import content_uid, process_page, uid          # noqa: E402
from core.pnd import load_domain                                  # noqa: E402
import core.acolyte as acolyte                                    # noqa: E402

FAILURES = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
    if not ok:
        print(f"        got:  {got!r}")
        print(f"        want: {want!r}")
        FAILURES.append(label)


class Log:
    """Collects what the collector said, so a warning can be asserted."""

    def __init__(self):
        self.lines = []

    def _add(self, msg, *a):
        try:
            self.lines.append(str(msg) % a if a else str(msg))
        except Exception:
            self.lines.append(str(msg))

    info = warning = error = _add

    def said(self, needle):
        return any(needle in x for x in self.lines)


URL = "https://example.test/registry/list"


def harness(tmp, body_sequence):
    """Return (run, state). `run` collects once and returns the tally."""
    state = {"i": 0, "seen": set(), "run_dir": tmp / "corpus",
             "seen_path": tmp / "seen.txt", "log": Log()}
    state["run_dir"].mkdir(parents=True, exist_ok=True)
    state["seen_path"].touch()

    # Stand in for the network. The real fetch_body is not exercised here; what
    # is under test is the identity and title logic around it.
    def fake_fetch(url, opts=None, log=None):
        i = min(state["i"], len(body_sequence) - 1)
        state["i"] += 1
        return body_sequence[i], "ok", url

    acolyte.fetch_body = fake_fetch

    def run(record):
        return process_page(URL, state["seen"], state["run_dir"],
                            {"fetch": {}, "seen_path": state["seen_path"]},
                            state["log"], record=record)

    return run, state


def corpus_records(tmp):
    out = []
    for p in sorted((tmp / "corpus").rglob("*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def main():
    real_fetch = acolyte.fetch_body
    tmp = Path(tempfile.mkdtemp())
    try:
        # ---- a declared page, contents unchanged --------------------------
        print("\nA declared page is re-read every run, and says nothing new")
        same = "The registry lists three reported breaches this month."
        run, st = harness(tmp / "a", [same, same, same])
        rec = {"url": URL, "kind": "page",
               "title": "Example registry — reported breach list"}

        t1 = run(rec)
        check("the first run collects it", t1["saved"], 1)
        t2 = run(rec)
        check("the second run FETCHES, and saves nothing", t2["unchanged"], 1)
        check("...and does not count as saved", t2["saved"], 0)
        t3 = run(rec)
        check("the third run is the same", (t3["saved"], t3["unchanged"]), (0, 1))
        check("a request was made on every run, not just the first",
              st["i"], 3)
        check("...and the log says so plainly",
              st["log"].said("unchanged since last run"), True)
        check("one record in the corpus", len(corpus_records(tmp / "a")), 1)

        # ---- identity and title ------------------------------------------
        print("\nIdentity follows the CONTENTS, and the declared title lands")
        one = corpus_records(tmp / "a")[0]
        check("the id is the content hash", one["id"], content_uid(same))
        check("...and NOT the url hash", one["id"] == uid(URL), False)
        check("the url is still recorded", one["url"], URL)
        check("the declared title reached the record",
              one["title"], "Example registry — reported breach list")
        check("...and the record says it came from a page",
              one["body_source"], "page")
        # THE CORPUS IS UTF-8, ON EVERY PLATFORM. `save()` wrote with the
        # platform default while the scorer has always read UTF-8, so the two
        # halves agreed only by accident of operating system — on Windows this
        # title's em dash was written as cp1252 and could not be read back.
        # The title above is deliberately non-ASCII so this stays guarded.
        check("the record is readable as UTF-8 whatever the platform default is",
              b"\x97" in (tmp / "a" / "corpus").rglob("*.json").__next__().read_bytes(),
              False)

        # ---- the contents change -----------------------------------------
        print("\nWhen the page changes, that is new collection")
        changed = "The registry lists four reported breaches this month."
        run, st = harness(tmp / "b", [same, changed, changed])
        check("first run saves", run(rec)["saved"], 1)
        check("changed contents save again", run(rec)["saved"], 1)
        check("then it settles", run(rec)["unchanged"], 1)
        recs = corpus_records(tmp / "b")
        check("both snapshots are in the corpus, neither overwrote the other",
              len(recs), 2)
        check("...and they have different identities",
              len({r["id"] for r in recs}), 2)

        # ---- whitespace is not news --------------------------------------
        print("\nReflowed markup is not new reporting")
        run, st = harness(tmp / "c", [same, "  The   registry lists three "
                                            "reported\nbreaches this month.  "])
        check("first run saves", run(rec)["saved"], 1)
        check("the same words, re-wrapped, save nothing", run(rec)["unchanged"], 1)

        # ---- no declared title -------------------------------------------
        print("\nWithout a declared title, behaviour is unchanged")
        run, st = harness(tmp / "d", [same])
        run({"url": URL, "kind": "page"})
        check("the record carries no title", corpus_records(tmp / "d")[0]["title"], "")

        # ---- an UNDECLARED non-feed is still collected once --------------
        print("\nA source that merely failed to parse as a feed is NOT re-read")
        # This is the guard that matters most. process_feed returns None for a
        # healthy feed that is temporarily empty, so re-reading everything that
        # reaches process_page would write a record whenever an error page
        # reflowed.
        run, st = harness(tmp / "e", [same, "totally different text now"])
        plain = {"url": URL}
        check("the first run collects it", run(plain)["saved"], 1)
        t = run(plain)
        check("the second run does not even fetch", st["i"], 1)
        check("...and saves nothing", t["saved"], 0)
        check("...and it is not reported as an unchanged page", t["unchanged"], 0)
        check("the operator is warned to declare it if it is a portal",
              st["log"].said("NOT-A-FEED"), True)

        # ---- a kind nobody implements is refused --------------------------
        print("\nA kind the engine does not implement is refused at load")
        dom = tmp / "typo"
        dom.mkdir(parents=True, exist_ok=True)
        (dom / "pnd.yaml").write_text(
            "manifest:\n"
            "  domain: typo\n"
            "  base_dir: /tmp/typo\n"
            "  sensors:\n"
            "  - url: https://example.test/a\n"
            "    kind: pages\n"
            "scoring:\n"
            "  groups: {}\n"
            "  multipliers: []\n"
            "  tiers:\n"
            "  - id: 1\n"
            "    weight: 1.0\n"
            "    require: always\n", encoding="utf-8")
        try:
            load_domain(pnd_path=str(dom / "pnd.yaml"))
            check("a misspelled kind is refused", "loaded", "refused")
        except ValueError as e:
            check("a misspelled kind is refused, naming the value",
                  "pages" in str(e), True)

        # ---- the real domain still loads ----------------------------------
        print("\nThe live domain is unaffected")
        cfg = load_domain(domain="cti")
        check("cti still resolves 55 sensors", len(cfg["sensors"]), 55)
        check("...and now carries a record for each",
              len(cfg["sensor_records"]), 55)
        check("...with every url preserved, in order",
              [r["url"] for r in cfg["sensor_records"]], cfg["sensors"])
        check("...and none of them is declared a page yet",
              sum(1 for r in cfg["sensor_records"] if r.get("kind") == "page"), 0)
    finally:
        acolyte.fetch_body = real_fetch
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if FAILURES:
        print(f"FAIL — {len(FAILURES)} problem(s)")
        for f in FAILURES:
            print(f"    {f}")
        return 1
    print("PASS — a declared portal is re-read and keyed on its contents, and a "
          "feed having a bad day is still collected once")
    return 0


if __name__ == "__main__":
    sys.exit(main())
