#!/usr/bin/env python3
"""
Sanctum · tools/geo_classify.py · derive a geography confidence table

WHY THIS EXISTS
---------------
A hand-written place-name list does not scale and cannot know what it collides
with. `geo` carried 34 California counties and five cities; four collisions were
known and written down, and a measurement on 2026-09-02 found six:

    lake county    12 states   CA,CO,FL,IL,IN,MI,MN,MT,OH,OR,SD,TN
    butte county    3 states   CA,ID,SD          <- not previously recorded
    nevada county   2 states   AR,CA             <- not previously recorded
    kings county    2 states   CA,NY
    sierra county   2 states   CA,NM
    trinity county  2 states   CA,TX

Adding more names makes that worse, not better. What fixes it is a property no
hand-maintained list can carry: **how confusable is this name?** The Census
Gazetteer answers it for every place in the country, so the answer is derived
rather than decided, and re-derived when the census updates.

WHAT IT PRODUCES
----------------
One table, committed to the repo, one row per name:

    A  unique to the state          match on the name alone
    B  shared with 2-3 states       require corroboration nearby
    C  shared with 4+ states,       never on the name alone
       or a common English word

C is not a discard pile. Commerce, Industry, Orange and Paradise are real
California cities that have had real incidents; they simply cannot carry a
requirement by themselves — the same rule an ordinary English word has always
been held to in this apparatus.

TWO MEASURED SIGNALS, NO JUDGEMENT
----------------------------------
  state count   straight from the national gazetteer
  word frequency  Zipf scale, threshold 4.0, single-word names only. This
                  replaced a dictionary test that flagged `Alhambra` and
                  `Alameda` as ordinary English, which is wrong:
                      industry 5.19  commerce 4.37  weed 4.27  orange 4.62
                      alhambra 2.74  cupertino 2.59  tehachapi 2.08

`wordfreq` is needed only for the second signal and only when regenerating.
Nothing at runtime reads it — the committed table carries the answer, so the
commit gate stays stdlib-plus-PyYAML and a clone needs no network to score.

    Source files (public domain, Census Bureau):
      .../gazetteer/2025_Gazetteer/2025_Gaz_counties_national.txt
      .../gazetteer/2025_Gazetteer/2025_Gaz_place_national.txt

    tools/geo_classify.py --counties C.txt --places P.txt --state CA \\
                          --out cti/data/geo_classified.txt

WHERE THE TABLE LIVES, AND WHY NOT IN references/
--------------------------------------------------
`cti/data/`, not `cti/references/`. The references folder is gitignored on
purpose — it holds working notes and source surveys that carry internal detail
and are never published. This table is the opposite: derived from a public
domain federal dataset, machine-generated, carrying no judgement of anyone's,
and READ BY A TEST — so a clone without it fails its own commit gate. Derived
data the apparatus needs at rest belongs where git can see it.

KNOWN LIMIT — READ THIS BEFORE USING THE TABLE FOR A SUB-STATE AREA
-------------------------------------------------------------------
The places file carries no county column, so this cannot tell you which places
fall inside a sub-state area of responsibility. Every place in the state is
classified. Narrowing to a specific set of counties needs the Census
place-to-county relationship file, which is a separate download and a separate
decision.
"""

import argparse
import csv
import datetime
import re
import sys
from collections import defaultdict
from pathlib import Path

# Gazetteer NAME fields carry their legal/statistical descriptor. Strip it to
# get the name a journalist would actually write.
COUNTY_SUFFIX = re.compile(
    r"\s+(County|Parish|Borough|Census Area|Municipality|City and Borough|Municipio)$",
    re.I)
PLACE_SUFFIX = re.compile(
    r"\s+(city|town|village|borough|CDP|municipality|city and borough|urban county"
    r"|comunidad|zona urbana|consolidated government|metro government"
    r"|unified government|corporation|plantation|township|charter township"
    r"|reservation)$", re.I)

COMMON_WORD_ZIPF = 4.0          # ~ a word met a few times per million
SHARED_MANY = 4                 # 4+ states -> bucket C


def read_gazetteer(path):
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="|"):
            yield {(k or "").strip(): (v or "").strip() for k, v in row.items()}


def load_frequency():
    """Return a zipf(word) callable, or None when wordfreq is absent.

    Absence is REPORTED, never silently absorbed: a table built without the
    frequency signal classifies `Commerce` and `Bishop` on state count alone
    and is a different table. The header records which signal set built it.
    """
    try:
        from wordfreq import zipf_frequency
        return lambda w: zipf_frequency(w, "en")
    except ImportError:
        return None


def classify(name, kind, states, zipf):
    """(bucket, reason) for one name.

    THE COMPARISON DEPENDS ON THE FORM THE TERM TAKES IN A RULE, and getting
    this wrong was the first bug in this tool. A domain writes `lake county`,
    a two-word phrase that can only match "Lake County" in text. Scoring it
    against every settlement named Lake, and against the frequency of the bare
    word "lake", put six correct county terms in the wrong bucket.

      county rows  compared against COUNTIES ONLY, and never frequency-tested:
                   "X County" is a phrase, not an English word.
      place rows   compared against every name in the gazetteer, because a bare
                   city name in prose competes with counties too, and
                   frequency-tested when it is a single word.
    """
    n = len(states)
    if kind == "place":
        low = name.lower()
        if zipf is not None and " " not in low:
            f = zipf(low)
            if f >= COMMON_WORD_ZIPF:
                return "C", f"common English word, zipf {f:.2f}"
    noun = "counties" if kind == "county" else "states"
    if n >= SHARED_MANY:
        return "C", f"shares its name with {n} {noun}"
    if n >= 2:
        return "B", f"shares its name with {n} {noun}"
    return "A", ""


def build(counties_path, places_path, state):
    zipf = load_frequency()
    counties_idx = defaultdict(set)     # bare name -> states, COUNTIES only
    any_idx = defaultdict(set)          # bare name -> states, every kind
    entries = []                        # (name, kind) for the target state

    for path, kind, suffix in ((counties_path, "county", COUNTY_SUFFIX),
                               (places_path, "place", PLACE_SUFFIX)):
        if not path:
            continue
        for r in read_gazetteer(path):
            bare = suffix.sub("", r["NAME"]).strip()
            any_idx[bare.lower()].add(r["USPS"])
            if kind == "county":
                counties_idx[bare.lower()].add(r["USPS"])
            if r["USPS"] == state:
                entries.append((bare, kind))

    seen, rows = set(), []
    for name, kind in sorted(set(entries)):
        key = (name.lower(), kind)
        if key in seen:
            continue
        seen.add(key)
        idx = counties_idx if kind == "county" else any_idx
        states = idx[name.lower()]
        bucket, reason = classify(name, kind, states, zipf)
        rows.append({
            "name": name.lower(),
            "kind": kind,
            "bucket": bucket,
            "states": len(states),
            "reason": reason,
            "where": ",".join(sorted(states)) if 1 < len(states) <= 12 else "",
        })
    return rows, zipf is not None


def write_table(rows, out, state, with_freq, sources):
    counts = defaultdict(int)
    for r in rows:
        counts[r["bucket"]] += 1
    head = [
        "# Sanctum · derived geography confidence table — DO NOT EDIT BY HAND",
        f"# regenerate with: tools/geo_classify.py --state {state}",
        f"# generated {datetime.date.today().isoformat()} · state {state} · {len(rows)} names",
        "# source: US Census Bureau Gazetteer (public domain)",
    ]
    head += [f"#   {s}" for s in sources]
    head += [
        "# frequency signal: " + ("wordfreq" if with_freq else
            "UNAVAILABLE — names classified on state count alone"),
        "#",
        "#   A  unique to this state      match on the name alone",
        "#   B  shared with 2-3 states    require corroboration nearby",
        "#   C  shared with 4+ states, or a common English word — never alone",
        "#",
        f"#   A {counts['A']}   B {counts['B']}   C {counts['C']}",
        "#",
        "# LIMIT: the places file has no county column, so this covers the whole",
        "# state. Narrowing to a sub-state AOR needs the Census place-to-county",
        "# relationship file.",
        "#",
        "# name|kind|bucket|states|reason",
    ]
    body = [f"{r['name']}|{r['kind']}|{r['bucket']}|{r['states']}|{r['reason']}"
            for r in rows]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(head + body) + "\n", encoding="utf-8")
    return counts


def read_existing(path):
    """Previous buckets, so a regeneration can report what MOVED."""
    p = Path(path)
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            out[(parts[0], parts[1])] = parts[2]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Derive a geography confidence table")
    ap.add_argument("--counties", help="national counties gazetteer file")
    ap.add_argument("--places", help="national places gazetteer file")
    ap.add_argument("--state", default="CA", help="two-letter USPS code (default CA)")
    ap.add_argument("--out", required=True, help="table to write")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if not args.counties and not args.places:
        print("geo_classify: give at least one of --counties or --places",
              file=sys.stderr)
        return 2

    before = read_existing(args.out)
    rows, with_freq = build(args.counties, args.places, args.state)
    sources = [Path(p).name for p in (args.counties, args.places) if p]
    counts = write_table(rows, args.out, args.state, with_freq, sources)

    if args.quiet:
        return 0

    print(f"\n{args.state}: {len(rows)} names classified -> {args.out}")
    total = len(rows) or 1
    for b, label in (("A", "unique, match alone"),
                     ("B", "2-3 states, corroborate"),
                     ("C", "4+ states or common word, never alone")):
        print(f"  {b}  {counts[b]:5}  {counts[b]*100//total:2}%  {label}")
    if not with_freq:
        print("\n  WARNING: wordfreq is not installed. Names were classified on")
        print("  state count alone, so common words like 'Commerce' and 'Bishop'")
        print("  are NOT in bucket C. Install wordfreq and regenerate.")

    if before:
        now = {(r["name"], r["kind"]): r["bucket"] for r in rows}
        moved = [(k, before[k], now[k]) for k in now
                 if k in before and before[k] != now[k]]
        added = [k for k in now if k not in before]
        gone = [k for k in before if k not in now]
        print(f"\n  since the last table: {len(moved)} moved bucket, "
              f"{len(added)} added, {len(gone)} removed")
        for (name, kind), was, isnow in sorted(moved)[:20]:
            print(f"    {was} -> {isnow}  {name} ({kind})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
