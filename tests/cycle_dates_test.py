#!/usr/bin/env python3
"""
Sanctum · tests/cycle_dates_test.py

The staging document must state its own cycle dates.

WHY THIS EXISTS
---------------
On 2026-09-02 a vox came out with no date range at the top. Nothing was broken:
Vox Policy §2 and §4 require an ICOD in the product header, `compute_cycle_window`
had calculated it, `core/arbites.py` used it to set the STALE flags — and then
discarded it. The staging document's header said "window 7d" and never which
seven days. The model building the vox could not re-derive the cutoff from the
document, and correctly declined to invent one.

That is the same defect class as the requirement identifier fixed on 2026-08-26,
and the same doctrine applies: **3a's job includes handing 3b everything 3b
cannot re-derive.** A fact 3a computes and throws away is a fact 3b has to guess.

It also went unnoticed because nothing tested the staging BUILD — only the
scoring underneath it. This file is the first test that runs arbites end to end
against a real corpus and reads what it wrote.

WHAT IS CHECKED
---------------
  icod printed      the cutoff appears, in the domain's declared timezone
  window printed    the opening of the cycle window appears
  coverage printed  the observed publish span of the IN-WINDOW candidates
  stale excluded    a stale item does not drag the coverage span backwards
  copy line         a line the analyst can paste into the vox header verbatim
  silent when off   a domain with no recency block prints none of it, rather
                    than printing "ICOD: None" — s2 declares no recency at all

    tests/cycle_dates_test.py        # exit 0 = 3b can date its own product
"""

import json
import re
import subprocess
import sys
import tempfile
import shutil
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml                                                     # noqa: E402

FAILURES = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
    if not ok:
        if detail:
            print(f"        {detail}")
        FAILURES.append(label)


def build_corpus(base, items):
    """items: (title, body, days_published_ago)"""
    now = datetime.now(timezone.utc)
    for i, (title, body, ago) in enumerate(items):
        collected = now - timedelta(hours=2)
        published = now - timedelta(days=ago)
        day = (base / "corpus" / collected.strftime("%Y-%m-%d"))
        day.mkdir(parents=True, exist_ok=True)
        (day / f"{i:03d}.json").write_text(json.dumps({
            "title": title, "text": body,
            "url": f"https://example.test/{i}",
            "source": "https://example.test/feed",
            "collected": collected.isoformat(),
            "published": format_datetime(published),
            "fetch_status": "ok", "body_source": "trafilatura",
        }), encoding="utf-8")


def run_arbites(base, pnd, *extra, expect_fail=False):
    out = base / "STAGING.md"
    r = subprocess.run(
        [sys.executable, "-m", "core.arbites", "--pnd", str(pnd),
         "--no-push", "--out", str(out)] + list(extra),
        cwd=str(ROOT), capture_output=True, text=True,
        env={**__import__("os").environ, "SANCTUM_BASE": str(base)})
    if expect_fail:
        return r.returncode, (r.stdout + r.stderr)
    if r.returncode != 0:
        print(r.stdout[-1500:]); print(r.stderr[-1500:])
        raise SystemExit("arbites failed to run — see output above")
    return out.read_text(encoding="utf-8")


def build_corpus_aged(base, items):
    """items: (title, body, days_published_ago, hours_collected_ago)

    build_corpus above collects everything two hours ago, which is the normal
    case. The window override needs items COLLECTED at different ages, because
    `load_window` gathers by collection date and not by publication date.
    """
    now = datetime.now(timezone.utc)
    for i, (title, body, pub_ago, coll_ago) in enumerate(items):
        collected = now - timedelta(hours=coll_ago)
        published = now - timedelta(days=pub_ago)
        day = (base / "corpus" / collected.strftime("%Y-%m-%d"))
        day.mkdir(parents=True, exist_ok=True)
        (day / f"{i:03d}.json").write_text(json.dumps({
            "title": title, "text": body,
            "url": f"https://example.test/aged/{i}",
            "source": "https://example.test/feed",
            "collected": collected.isoformat(),
            "published": format_datetime(published),
            "fetch_status": "ok", "body_source": "trafilatura",
        }), encoding="utf-8")


# Two items that WILL score: California plus an incident word plus cyber
# context, which is what tier 1 requires. One fresh, one deliberately stale.
ITEMS = [
    ("California county reports ransomware attack on court systems",
     "A California county said a ransomware attack disrupted its court systems "
     "this week. The county is working with incident response on the breach.", 1),
    ("California city discloses data breach from earlier in the year",
     "A California city disclosed a data breach involving a ransomware incident "
     "that occurred earlier in the year, affecting resident records.", 40),
]


def main():
    tmp = Path(tempfile.mkdtemp())
    try:
        # ---- recency ON: the real cti domain --------------------------------
        print("\nA domain that declares a cycle window states it")
        base = tmp / "on"
        build_corpus(base, ITEMS)
        text = run_arbites(base, ROOT / "cti" / "pnd.yaml")

        check("the ICOD is printed", "ICOD (information current as of)" in text)
        check("...in the domain's own timezone, abbreviated for a reader",
              bool(re.search(r"ICOD.*\d{4} (PDT|PST)\b", text)),
              "expected a PDT/PST abbreviation, not an IANA name")
        check("the window opening is printed", "cycle window opens" in text)
        check("a copy-paste line for the vox header exists",
              "Copy into the vox header" in text)
        check("...and it carries a real date, not a placeholder",
              bool(re.search(r"Information current as of \d{2} \w+ \d{4}, \d{4}", text)))

        m = re.search(r"\*\*Reporting covered: (.+?) – (.+?) (PDT|PST)\*\*", text)
        check("the observed reporting span is printed", bool(m))
        if m:
            # The 40-day-old item is stale. It must be counted, never folded
            # into the span — a stale item does not define the period the
            # product covers, and letting it would date the vox to July.
            check("a STALE item is counted separately, not folded into the span",
                  "STALE outside it" in text)
            # Measure it rather than pattern-match the month: the stale item is
            # 40 days old and the window is 7, so a span opening more than ten
            # days back means the stale item was folded in.
            lo_raw = m.group(1)                       # e.g. "28 Aug 0133"
            now = datetime.now(timezone.utc)
            lo_dt = datetime.strptime(f"{lo_raw} {now.year}", "%d %b %H%M %Y")
            age_days = (now.replace(tzinfo=None) - lo_dt).days
            check("...so the span opens inside the window, not at the stale item",
                  age_days <= 10,
                  f"span opened {age_days} days back at {lo_raw!r}; "
                  f"the window is 7 days and the stale item is 40")

        # ---- recency OFF: silence, not "None" -------------------------------
        print("\nA domain that declares no cycle window says nothing")
        cfg = yaml.safe_load((ROOT / "cti" / "pnd.yaml").read_text())
        cfg["scoring"]["settings"].pop("recency", None)
        off = tmp / "off"
        off.mkdir(parents=True, exist_ok=True)
        (off / "pnd.yaml").write_text(yaml.dump(cfg, sort_keys=False),
                                      encoding="utf-8")
        build_corpus(off, ITEMS)
        text2 = run_arbites(off, off / "pnd.yaml")

        check("no ICOD line", "ICOD" not in text2)
        check("no window line", "cycle window opens" not in text2)
        check("no copy-paste line", "Copy into the vox header" not in text2)
        check("no coverage line", "Reporting covered" not in text2)
        check("...and it still produced a document",
              text2.lstrip().startswith("#"))
        check("...saying plainly that the gate is off", "recency gate OFF" in text2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

        # ---- the window override, for the daily differential -------------
        #
        # Added 2026-09-30. `--window-days` exists so ONE config can serve a
        # seven-day product and a one-day personal read over the SAME corpus.
        # The alternative, a second config file, would have been checked by
        # neither the vocabulary gate nor the domain gate, because both match
        # exact filenames.
        print("\nThe window can be overridden for one run, and says so")
        aged = tmp / "aged"
        build_corpus_aged(aged, [
            ("California county reports ransomware attack on court systems",
             "A California county said a ransomware attack disrupted its court "
             "systems this week. Incident response is engaged on the breach.",
             1, 2),
            ("California city discloses data breach affecting residents",
             "A California city disclosed a data breach involving a ransomware "
             "incident this week, affecting resident records.", 1, 3),
            ("California school district reports a ransomware incident",
             "A California school district reported a ransomware attack and "
             "data breach affecting its systems, per the district.", 2, 72),
            ("California utility discloses a cyberattack on billing",
             "A California utility disclosed a cyberattack and data breach "
             "affecting its billing systems, the utility said.", 2, 96),
        ])
        wide = run_arbites(aged, ROOT / "cti" / "pnd.yaml")
        check("the declared seven-day window sees all four",
              "window 7d · 4 articles scored" in wide)
        narrow = run_arbites(aged, ROOT / "cti" / "pnd.yaml",
                             "--window-days", "1")
        check("a one-day override sees only the two collected today",
              "window 1d · 2 articles scored" in narrow)
        check("...and the document states the overridden window, not 7d",
              "window 7d" not in narrow)
        rc, msg = run_arbites(aged, ROOT / "cti" / "pnd.yaml",
                              "--window-days", "0", expect_fail=True)
        check("a window of zero is refused rather than scoring nothing",
              rc != 0 and "at least 1" in msg)

        # The remote name must be overridable too, or a second pass would
        # copy over the first on the remote under the same dated filename.
        from core.arbites import staging_target
        man = {"staging": {"backend": "rclone", "rclone_remote": "gdrive:s",
                           "filename": "WCTI_{date}_DAILY.md"}}
        check("a second pass can land under its own dated name",
              staging_target(man, date(2026, 9, 30))[1]
              == "WCTI_20260930_DAILY.md")

    print()
    if FAILURES:
        print(f"FAIL — {len(FAILURES)} problem(s)")
        for f in FAILURES:
            print(f"    {f}")
        return 1
    print("PASS — the staging document dates itself, and a domain without a "
          "cycle window stays silent rather than printing nothing useful")
    return 0


if __name__ == "__main__":
    sys.exit(main())
