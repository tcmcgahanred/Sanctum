"""
Sanctum · tests/oldevent_test.py · old events in new coverage are labelled

Two labels on staging candidates, from the 2026-10-28 work order. Labels only:
this test also proves an item carrying one keeps its score and its place.

Every headline below is a real one from the CTI cycles 7 to 28 October 2026
that the measurement read, so the test pins the behaviour that was measured.
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
from core.oldevent import PriorEditions, secondary_hit          # noqa: E402

FAILURES = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
    if not ok:
        if detail:
            print(f"        {detail}")
        FAILURES.append(label)


def main():
    cfg = yaml.safe_load((ROOT / "cti" / "pnd.yaml").read_text(encoding="utf-8"))
    spec = cfg["production"]["staging_annotations"]["old_event"]
    sec = spec["secondary_coverage"]

    print("\nSecondary coverage reads whole words in the headline")
    cases = [
        ("Privacy commissioner opens investigation into Crime Stoppers data "
         "breach - CityNews Toronto", "opens investigation"),
        ("California reaches $6 mn 23andMe settlement over genetic data breach",
         "settlement"),
        ("Class action accuses Live Nation of negligence in data breach",
         "class action"),
        ("ETS Sued Over Data Breach Affecting Current, Former Calif. Students",
         "sued"),
        ("Enroll Confidently Settles Data Breach Lawsuit for $990,000",
         "settles"),
    ]
    for title, want in cases:
        got = secondary_hit({"title": title}, sec)
        check(f"labels: {title[:60]}", got == want, f"got {got!r}, want {want!r}")
    # "confirms" was measured and removed: the one item it labelled, the
    # Burnaby schools attack, was a current incident. Whole words only:
    # "Lawsuits" alone is not "lawsuit".
    for title in ["Burnaby school district confirms student and staff data "
                  "stolen in ransomware attack",
                  "Frontline Education breach puts student data at risk",
                  "Lawsuits mount for the vendor"]:
        check(f"does not label: {title[:60]}",
              secondary_hit({"title": title}, sec) is None)
    check("the body is never read",
          secondary_hit({"title": "Ransomware hits county",
                         "text": "A class action lawsuit followed."}, sec) is None)

    print("\nAlready reported matches a name and an incident in a recent edition")
    tmp = Path(tempfile.mkdtemp())
    try:
        corpus = tmp / "corpus" / "2026-10-20"
        corpus.mkdir(parents=True)
        now = datetime(2026, 10, 28, 11, 0, tzinfo=timezone.utc)
        body = ("Reporting said the breach at Paradigm Healthcare exposed "
                "records, and individuals were notified. A breach at Paradigm "
                "affected individuals, and the individuals were offered help. "
                "The data breach impacted patients, and data was impacted, "
                "and it compromises information, and the data breach "
                "compromises information.")
        for i, t in enumerate([
                "Paradigm Healthcare breach reported",
                "Blueberry Pediatrics Data Breach Impacted 340k Individuals",
                "Ivanti Connect Secure zero-day exploited (CVE-2026-104935)"]
                + [f"Unrelated headline number {k} about patches" for k in range(40)]):
            (corpus / f"{i}.json").write_text(json.dumps({
                "title": t, "text": body,
                "collected": (now - timedelta(days=8)).isoformat()}),
                encoding="utf-8")
        eds = tmp / "editions"
        eds.mkdir()
        (eds / "WCTI_v20260924.md").write_text(
            "**20260924-C — A breach at Paradigm Healthcare Services is "
            "reported to affect Medi-Cal members.** text\n"
            "**20260924-D — A data breach compromises information for 2,206 "
            "Individuals.** text\n"
            "**20260924-E — A Cisco Secure Email Gateway zero-day "
            "(CVE-2026-76461) is exploited.** text\n", encoding="utf-8")
        grouping = cfg["scoring"]["settings"]["grouping"]
        seps = (" - ", " | ", " — ")
        pe = PriorEditions(tmp / "corpus", eds, spec["prior_editions"],
                           grouping, seps, now=now)
        h = pe.hit("Over 970,000 individuals affected by Paradigm Healthcare "
                   "data breach - teiss", now)
        check("a named organisation in a recent edition is found",
              bool(h) and h[0] == "20260924-C", f"got {h!r}")
        check("Title Case does not make an ordinary word a name",
              pe.hit("Blueberry Pediatrics Data Breach Impacted 340k Individuals",
                     now) is None)
        check("different CVE identifiers are different events",
              pe.hit("Ivanti Connect Secure zero-day exploited in the wild "
                     "(CVE-2026-104935)", now) is None)
        check("an edition older than the lookback is not consulted",
              pe.hit("Over 970,000 individuals affected by Paradigm Healthcare "
                     "data breach", now + timedelta(weeks=7)) is None)
        check("an edition dated after the cycle is not consulted",
              pe.hit("Over 970,000 individuals affected by Paradigm Healthcare "
                     "data breach", datetime(2026, 9, 20, tzinfo=timezone.utc))
              is None)

        print("\nThe staging document prints the label and moves nothing")
        base = tmp / "run"
        day = base / "corpus" / datetime.now(timezone.utc).strftime("%Y-%m-%d")
        day.mkdir(parents=True)
        items = [
            ("California county reports ransomware attack on court systems",
             "A California county said a ransomware attack disrupted its court "
             "systems this week. The county is working on the breach."),
            ("California class action filed over county ransomware data breach",
             "A California county faces a class action after a ransomware attack "
             "and data breach disrupted court systems this week."),
        ]
        for i, (t, b) in enumerate(items):
            (day / f"{i}.json").write_text(json.dumps({
                "title": t, "text": b, "url": f"https://example.test/{i}",
                "source": "https://example.test/feed",
                "collected": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "published": format_datetime(datetime.now(timezone.utc) - timedelta(days=1)),
                "fetch_status": "ok", "body_source": "trafilatura"}),
                encoding="utf-8")
        outs = {}
        for name, pnd in (("with", ROOT / "cti" / "pnd.yaml"), ("without", None)):
            if pnd is None:
                c2 = yaml.safe_load((ROOT / "cti" / "pnd.yaml").read_text(encoding="utf-8"))
                c2["production"]["staging_annotations"].pop("old_event")
                d2 = tmp / "noold" / "cti"
                shutil.copytree(ROOT / "cti", d2, ignore=shutil.ignore_patterns("editions"))
                (d2 / "pnd.yaml").write_text(yaml.safe_dump(c2, sort_keys=False),
                                             encoding="utf-8")
                pnd = d2 / "pnd.yaml"
            out = base / f"{name}.md"
            r = subprocess.run([sys.executable, "-m", "core.arbites", "--pnd", str(pnd),
                                "--no-push", "--out", str(out)], cwd=str(ROOT),
                               capture_output=True, text=True,
                               env={**__import__("os").environ, "SANCTUM_BASE": str(base)})
            if r.returncode != 0:
                print(r.stdout[-1200:]); print(r.stderr[-1200:])
                raise SystemExit("arbites failed to run")
            outs[name] = out.read_text(encoding="utf-8")
        w = outs["with"]
        check("the labelled item carries the marker in its heading",
              "[SECONDARY COVERAGE]" in w and
              re.search(r"### .*\[SECONDARY COVERAGE\].*class action filed", w) is not None)
        check("...and says which word fired",
              'headline says "class action", so verify the event date' in w)
        check("the unlabelled item has no marker",
              re.search(r"### (?!.*SECONDARY).*reports ransomware attack on court", w) is not None)
        check("the header counts the labels", "1 SECONDARY COVERAGE" in w)

        def scores(t):
            return re.findall(r"^### .*?\[(\d+(?:\.\d+)?)\] (.+?)(?: \u29c9|$)", t, re.M)
        sw = [(s, re.sub(r"\[SECONDARY COVERAGE\] |\[ALREADY REPORTED\?\] ", "", x))
              for s, x in scores(w)]
        so = scores(outs["without"])
        check("scores and order are identical with and without the labels",
              sw == so, f"with={sw} without={so}")
        check("a domain that declares no old_event block prints no label",
              "SECONDARY COVERAGE" not in outs["without"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'PASS' if not FAILURES else 'FAIL'} — old events in new coverage "
          f"are labelled, and labelling moves nothing")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
