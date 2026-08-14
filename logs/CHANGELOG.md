# Changelog — Sanctum

Notable changes to the Sanctum intelligence apparatus. **Git is the source of truth**; this file is the curated-highlights layer and `git log` is the full record. Brief editions (Vox) are keyed by distribution date (`vYYYYMMDD`), separate from code versioning.

## [2026-08-11] Same-event grouping in the staging report

- **Problem.** Collection dedup catches identical URLs and identical normalized titles. It cannot catch several outlets writing different headlines about one incident — those arrive as separate articles, and because scoring keys on terms rather than events they *scatter*. Measured on three realistic headlines for one incident: 8.0, 8.0 and 1.0, where the 1.0 was the only one naming the affected town. The best-sourced copy was the one below the cut.
- **Built.** `core/arbites.py` now groups suspected same-event items under their highest-scoring sibling, marked `⧉`, with a group count in the report header. Any grouped copy that fell below the cut is pulled up and labelled *rescued from drop list*; it also stays listed in the drop list, cross-referenced.
- **Display only.** No score is changed, no item merged, no item dropped — consistent with flag-don't-drop. The corroboration count stays visible because several independent outlets on one incident is itself a signal.
- **Signal used:** shared rare tokens in titles, publisher suffix stripped. Two items sharing at least `min_shared_rare` distinctive tokens are treated as one event. Common words are excluded automatically by document frequency, so no per-domain stopword list is needed. Config: `scoring.settings.grouping` — `enabled`, `min_shared_rare`, `max_df_abs`, `max_df_frac`, `max_bucket`.
- **Bug caught by the new test before release:** a fixed rarity threshold (`max_df: 3`) meant an incident covered by four outlets had the victim's name classified as too common to be distinctive, and nothing grouped at all. The threshold now scales with corpus size.
- **Verification:** new `tests/grouping_test.py` (12 checks) covers clustering, anchoring on the top scorer, below-cut rescue, non-grouping of unrelated items, config disable, non-destructiveness, and publisher-suffix stripping. Scorer parity **514/514 PASS**, recency **PASS**. End-to-end on a 204-article synthetic corpus: one group found, two copies rescued, 200 templated fillers correctly untouched.
- **Caveat:** thresholds are defaults tuned on synthetic data. Verify against a real corpus before trusting them.

## [2026-08-11] Staging doc enlarged; restraint doctrine scoped to the distributed product

- **The staging doc is now a review surface with its own, larger target.** Previously the docs carried a single "5–8 items per edition" rule that applied to everything, which produced only 2–3 items per section on the Monday draft — 5–8 spread across three content sections is 2–3 each by arithmetic. **Staging target is now ~5–6 per content section, ~15–18 total.**
- **"Restraint is the product" now explicitly governs the DISTRIBUTED product only.** The Thursday finished report stays at **5–8 items total**. The count narrows through the week, and that funnel is the stated intent rather than slippage. This ambiguity is corrected in `cti/pnd.md`, `cti/mandate.md`, `cti/codex.md` and the README tenet.
- **Standards are unchanged.** The additional staging entries are the next-lower-ranked items from the *same* sorted queue — lower tier and/or fewer elevation signals, not weaker sourcing. Extending the cut line down a ranked list is not relaxing the bar. Every staging entry still carries its scoring reasoning (tier + which multipliers fired) so the analyst can audit where the cut falls.
- **Config keys renamed for the distinction:** `production.item_target` → `production.staging_item_target` `[15, 18]`, `production.staging_per_section` `[5, 6]`, `production.distributed_item_target` `[5, 8]`. Safe because no engine reads them — `arbites.py` takes only `report_title` from this block.
- **No engine or scoring change.** `scoring.settings.surface_n` stays at 55, already ~3× the new staging target. Verified: scorer parity **514/514 PASS**, recency gate **PASS**, config loads, 50 sensors intact. The only edit under `core/` is a docstring in `pnd.py` naming the renamed keys.

## [2026-08-11] Sensor audit — AOR sources loaded, dead sensors pruned

- **Four curated AOR/official sensors added and verified live** against host egress: a state emergency-management newsroom, a state technology-department newsroom, an SLTT government-technology trade feed, and the CIS/MS-ISAC alert feed (companion to the advisories feed already loaded). All four confirmed producing on the first production cycle. Closes the standing "curated AOR trusted sources" direction.
- **Two dead sensors dropped** on nine cycles of evidence: a national cyber-news feed whose RSS path appears retired by the publisher, and an over-narrow regional government query that matches nothing. Both returned zero lifetime articles and logged `no text` on every cycle — they yielded neither feed entries nor extractable page text, and because `process_page` returns before recording the URL, both were re-fetched in full every run. Recorded in `cti/pnd.md` prose so they are not reintroduced. One further sensor is on notice at 1 new item in 9 runs.
- **Two candidate feeds rejected** rather than loaded: a department-wide feed still live but last updated 16 months prior (its newsroom sub-feed is the live path), and a trade publication whose advertised feed paths return zero entries and 404.
- **Sensor count 48 → 50.**
- **Sensor health is observable from the existing collector log.** `acolyte.py` already writes per-URL yield and per-URL failure lines every cycle, so a `grep` plus an `awk` over `collector.log` answers feed liveness, lifetime yield, and dead-vs-quiet. A standalone validator script and a proposed `--check` flag on Acolyte were both drafted and **discarded** as redundant. No new files, no new engine code.
- **`production` block confirmed advisory, not enforced.** `arbites.py` reads only `report_title` from it; `item_target` and `sections` are referenced nowhere in `core/`. The sole code-enforced production knob is `scoring.settings.surface_n`. This settles how edition-size changes must be made — by doctrine and analyst behaviour, or by `surface_n`, not by editing `item_target`.
- **Two defects recorded, not yet fixed.** `process_page` dedupes on URL hash, so page-type sources are collected once and never revisited (blocks portal sources). `acolyte.py` sets no collection timeout, so a stalled feed can block a sequential run indefinitely.
- **`run.sh` is committed non-executable** (mode 644) in every commit, so `./run.sh <domain>` fails on a fresh clone. The systemd unit invokes `bash` explicitly, which is why this stayed hidden. Use `bash run.sh <domain>` until the mode bit is fixed.

## Initial release

A domain-agnostic OSINT collection-and-triage apparatus.

- **Domain-agnostic engine.** All logic lives in `core/` (`acolyte` collector, `arbites` scorer, `rules` matcher/scorer, `pnd` config loader). The engines hold no domain knowledge; each domain supplies a single `pnd.md` (manifest + sensors + scoring + production).
- **Collector (Acolyte).** RSS/Atom + page collection, full-text extraction (trafilatura), URL-hash **and** normalized-title deduplication, dated JSON corpus, push to a corpus store via rclone. Runs unattended on a systemd timer.
- **Pre-filter / scorer (Arbites).** Config-driven multiplicative scoring (tier weights × elevation multipliers) with a wide cut (~55 surfaced), a mandatory drop list, and visible per-item reasoning. No API — local scoring only.
- **Recency gate.** Flags items whose *publication* date falls outside the cycle window as "STALE — confirm current hook"; never drops them (preserves legitimately-current re-emergences).
- **Single-file P&D.** A domain's entire configuration — feeds, scoring model, output shape — lives in one `pnd.md`. Adding a domain is: drop in `<domain>/pnd.md` and run `run.sh <domain>`.
- **CTI effort (operational).** An SLTT cyber-threat-intelligence cycle: 48 trusted national/sector feeds at initial release, a convergence-based scoring model, and a staged weekly brief. Tuned as an example for a California SLTT AOR.
- **Second-domain support.** The engine is domain-agnostic by construction; a second effort needs only its own `pnd.md`.
- **Verification.** A parity test proves the config-driven scorer reproduces the original hardcoded logic exactly; a recency test covers the publish-date gate.
