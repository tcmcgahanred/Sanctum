# core — the engines

*The only code in Sanctum. None of it knows anything about any subject.*

Everything here is driven by one file per subject: `<subject>/pnd.md`. The engines
read it, do the work, and hold no memory of what the subject was. That is the
whole design, and `tests/domain_check.py` enforces it rather than trusting anyone
to remember.

## What each engine does

| Engine | Job |
|---|---|
| `acolyte.py` | Collects. Reads the source list, pulls full text, removes duplicates, writes a dated corpus. |
| `arbites.py` | Scores. Ranks the corpus against the subject's priorities and writes the staging document, with the reasoning attached to every item. |
| `lexicanum.py` | Searches everything ever collected, and counts how often terms appear over time. Asked on demand; changes nothing. |
| `rules.py` | The matcher and the scoring model both of the above use. |
| `pnd.py` | Loads and validates a subject's configuration file. |

The names come from the Imperium's Inquisition — an Acolyte that gathers, an
Arbites that judges provisionally, a Lexicanum that remembers. The theme is
flavour; underneath it is a plain, auditable pipeline.

## Running it

```
./run.sh <subject>          # collect, then score
```

Searching everything ever collected, rather than just the current window:

```
core/lexicanum.py cti --group ransom --by week
core/lexicanum.py cti --all-groups --counts --by month
core/lexicanum.py cti --term "emotet"                       # ad-hoc, not in the config
core/lexicanum.py --pnd /path/to/pnd.md --group platform --since 2026-01-01
```

**Matches are recomputed on demand, never stored.** A stored index can only
answer questions you thought to ask on collection day. Re-running the live
matcher lets a word list invented this morning run against everything collected
last year, and guarantees the results agree with the scorer, because it is the
same matcher and there is no second copy to drift.

**Read the rate, not the count.** Every table shows hits, how many articles were
collected in that period, and the resulting rate — because a period where you
collected less looks exactly like a period where less happened. On the first real
run, hits fell 475 to 122 and read as a collapse; the denominators were 6,585
articles against 1,370, and the rate had *risen*.

## Feeds and portals are collected differently, and you declare which

A sensor record's `kind` decides how a source is read. This is domain-agnostic —
every subject gets the same two behaviours.

| | `kind: feed` (default) | `kind: page` |
|---|---|---|
| what is read | the feed's items | the page itself |
| identity | each item's URL | a hash of the page's normalised text |
| how often | every run, new items only | every run, **re-read in full** |
| unchanged | nothing to collect | nothing saved, counted as `unchanged` |
| title | from the feed entry | from the record's `title:`, or none |

**A portal has to say it is one.** `process_feed` returns nothing whenever a feed
yields no entries, which includes a healthy feed having a bad day — so the page
path also receives real feeds. Re-reading everything that lands there would write
a fresh record every time an error page reflowed. An undeclared non-feed is
therefore still collected once, keyed on its URL, exactly as before, and the log
says `NOT-A-FEED` so a dead feed is not mistaken for a quiet one.

**A `kind: page` record wants a `title:`.** A page has no headline, and the scorer
floors and flags an untitled record — so a portal without one can never surface,
however fresh it is. Choose the words carefully: any rule using `scope: title`
matches against them on every snapshot.

## Checking a subject before you run it

```
python3 tools/vocab_check.py <subject>     # word-list defects
python3 tools/sensor_check.py <subject>    # which sources are actually returning anything
```

Run the source check **from the machine that does the collecting**, not your own.
Several publishers serve a browser normally and refuse a datacentre address.

## The commit gate — install once per clone

```
git config core.hooksPath .githooks
mkdir -p .githooks && ln -sf ../tests/pre_commit.sh .githooks/pre-commit
```

On Windows, copy `pre_commit.sh` into `.githooks/` rather than linking it.

Three checks run on every commit: no subject file contains logic, no word list
has quietly decayed, and — a warning only — you changed something without
writing it down. The first two can be overridden with `git commit --no-verify`,
which should be rare enough to feel wrong.

**Nothing here scans for private detail.** A scrub check used to, and was removed
because it demanded a local denylist file before any clone could commit — a
per-user secret standing between a stranger and a working engine. Tenet 8 still
holds; it is now yours to keep, not the gate's.

## Stack and portability

Python — `feedparser`, `trafilatura`, `pyyaml` — plus `rclone` as a system binary
and a timer to run it. Any rclone-supported storage works for the corpus.

**The only host-coupled setting is `base_dir`** in each subject's configuration.
Override it per machine with the `SANCTUM_BASE` environment variable. Note that
the variable *wins* over the file, so if it is set globally it will override every
subject at once — which silently defeats giving each subject its own directory.

To move Sanctum elsewhere: clone, `pip install -r requirements.txt`, point the
configuration at your storage, run. No code changes.

**Give every subject its own `base_dir` and its own storage location.** Two
subjects sharing either will share the record of what has already been collected,
and one will silently starve the other. There is no guard for this yet.

## Version control

**Git is the source of truth.** The remote is authoritative. The authoring
machine pushes; **the collecting machine only ever pulls** — nothing it produces
is tracked, and read-only means a compromise there cannot rewrite the record.

No hand-maintained version numbers and no per-file changelogs. Each file carries
a one-time starting anchor in its header, and history flows through git from
there — the anchor is never incremented by hand.

```
Sanctum · Arbites · v0.4 (starting anchor; history via git)
```

`logs/CHANGELOG.md` is the curated-highlights layer; `git log` is the full record.

**What is committed and what is not.** Each subject's `editions/` folder holds
its published voxes, because judgement was applied and nothing can regenerate
them. The staging document is **not** committed — it is machine-made and
reproducible from the corpus plus the configuration, both of which are kept.

Secrets never enter the repo. `.gitignore` blocks credential carriers and runtime
data. Public source URLs are safe to commit.
