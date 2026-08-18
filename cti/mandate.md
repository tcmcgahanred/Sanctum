# MANDATE — Sanctum CTI Cycle

*Sanctum · Mandate · v1.0 (starting anchor; history via git)*

*Standing planning & direction record. Lives with the collector. This document is the continuity mechanism for the weekly intelligence cycle: any chat session handed this Mandate can run the cycle at full quality without re-deriving decisions. It captures (1) standing directives that govern how the cycle runs, and (2) a dated log of lessons/decisions that shaped them and directions pending. Update it at the Feedback stage of every cycle; it feeds the Planning & Direction stage of the next.*

*Relationship to other artifacts: the **Codex** holds the current analytical framework (KIQ/PIRs/scoring). This Mandate holds the directives and lesson-history that shape collection, analysis, production, and dissemination over time. When a lesson changes the framework, log it here AND update the Codex.*

---

## HOW TO USE THIS DOCUMENT (for a fresh chat session)

1. Read the Standing Directives — they are the current operative rules. Apply them.
2. Read Pending Direction — that's what this cycle or the next should act on.
3. When the cycle ends, add lessons to the Log and update directives/pending as needed.
4. If a directive here conflicts with an ad-hoc request, the directive is the retained decision — confirm before overriding.

---

## WEEKLY CADENCE (the operative schedule)

| When | Step |
|------|------|
| **Monday 0500 PT** | **Collector runs. Collection cutoff = ICOD** ("information current as of"). Corpus windowed on the 7 days ending here. |
| **Monday 0500** (same run) | **Staging document written** by `arbites.py` — 3a, machine, deterministic. Pushed to the staging store. |
| **Monday ~0600** | **Vox created** from the staging document — 3b, operator plus a model, per `../EXPLOITATION.md`. |
| **Monday–Tuesday** | **Individual review / amend** — analyst verification and edits. |
| **Wednesday** | **Team review.** |
| **Thursday afternoon** | **Distribution** — finished report sent. This is the product's **title date**. |

**Three dates — keep them distinct:**
- **Title date = distribution (Thursday).** What the product is dated.
- **ICOD line = collection cutoff (that week's Monday 0500 PT).** Carried in the product body: "information current as of …".
- **LTIOV** (latest time information is of value) — **planning doctrine only. Never printed on the product.**

**Two documents, two names — never interchangeable** (Vox Policy §3):

| | 3a staging document | 3b vox |
|---|---|---|
| Made by | `arbites.py`, deterministic | operator + model |
| Title | `WCTI — Staging Document (candidate queue)` | `WCTI — Weekly Cyber Threat Intelligence` |
| Filename | dated by collection day, pushed to the staging store | `WCTI_v[YYYYMMDD]` — date is **distribution (Thursday)** |
| Committed? | **No** — machine-made and reproducible | **Yes**, to `editions/` |

**"Vox" is internal shorthand and never appears in the reader-facing document.** No `CCIC` prefix until AOR-direct sensors exist. No `_STAGING` suffix on a vox — that suffix belongs to the other document entirely.

---

## STANDING DIRECTIVES (current operative rules)

### Collection
- **Quality over quantity on sensors.** A feed earns its place only if reliable AND additive (offers a vantage the others don't). Drop noisy sensors rather than filter them.
- **Trusted sources ingested wholesale; AOR relevance decided at scoring**, not by keyword pre-filtering at collection.
- **Verify every feed URL against the current host's actual egress** before loading (some sources 403 datacenter/server IPs even when they work from a browser).
- **Collection window: the 7 days ending Monday 0500 PT (ICOD).** The window closes at the 0500 cutoff and the staging document is built from that closed corpus in the same run. The 0500 time exists so a 0600 pull sees a finished run, leaving the analyst until 0900 to review.
- **Dropped and why:** 34 county Google News keyword feeds — keyword search on a general news index returns the county's whole news firehose, not its cyber incidents. Wrong instrument for precision local detection. Do not reintroduce keyword-query feeds.

### Analysis / Scoring
- **Multiplicative scoring** (tier weight × product of elevation multipliers). Convergence wins by design — a heavily-elevated lower-tier item can outrank a bare higher-tier item. This is intentional.
- **The score is an ordering aid, not a measurement.** The analyst always overrides it.
- **Prefer false positives to false negatives on items.** Missing a real AOR threat is far costlier than surfacing an extra item to skim.
- **Strict on sensors, generous on items.** Quality gate applies to feeds, not to individual articles from good feeds.
- **One event, one entry.** Place an incident in the section matching its dominant value; fold secondary angles in. Do not repeat it across sections.
- **Recency by publication date, not collection date.** Flag items published outside the collection window as "STALE — confirm current hook"; never hard-drop (keep old-CVE/new-exploitation re-emergences). Rule lives in Codex Layer 4.
- **Arbites (pre-filter) known limits the analyst must catch:** keyword scoring can mis-tag on proximity (e.g., a national article discussing California near an incident word looks tier-1 — check the title), and national threat-landscape roundups score mid-pack. These are expected; the human gate catches them.

### Production
- **NO CAP ON THE REVIEW SURFACE — trust the weights.** *(Vox Policy §7. Supersedes the item targets this document carried until 2026-08-17.)* There is no fixed limit on items per section or overall. Every item that qualifies — by score, or by the mandatory-surface rule below — appears, however many that is. If 20 high-weight items qualify, 20 surface. **The count is an OUTPUT of the scoring and the rules, never a target imposed on top of them.**
  - The former targets (~5–6 per section, ~15–18 total) were exactly such a cap and have been removed here and from `pnd.md` (and from `codex.md`, before that file was retired).
  - Surface-vs-drop is now a **score threshold** — `scoring.settings.surface_min_score` — plus guaranteed inclusions. Never a rank cut.
- **If the surface is too large or too noisy, tune Sanctum — do not cap.** Adjust the weights, the mandatory-surface vocabulary, or the exclusion operators. Capping hides what the scoring did and destroys the feedback that tunes it. **The uncapped surface IS the diagnostic.**
- **Mandatory-surface rule — inclusion, not ranking.** An item is force-surfaced regardless of score if it meets any of: **(M1)** an in-AOR entity is the subject of a cyberattack, breach or disruption; **(M2)** in-the-wild exploitation, weaponised public PoC, or KEV addition **and** the affected product is in the SLTT-relevant technology vocabulary; **(M3)** a specific incident confirms an SLTT sector was targeted or impacted. Score still orders everything, so a forced low-scoring item sits at the bottom of the surface with its ranking/relevance disagreement visible — which is the tuning signal. **Known limit: these rules can only fire on vocabulary the domain has already declared** — see `vocab.md`, Open finding 1.
- **"Restraint is the product" governs the DISTRIBUTED product only.** Restraint is the finished report's virtue, applied by the cyber team as editorial judgment after review. It is never an automated cap on what surfaces. The distributed target (5–8 items, Thursday) sits **outside Sanctum's scope** and is recorded here for reference only.
- **A wider surface does not lower the standard.** The added entries are lower-ranked items from the *same* sorted queue — lower tier and/or fewer elevation signals, not lower-quality sourcing. Every entry still shows its scoring reasoning so the analyst can audit where the cut falls.
#### Content standards — owned by [`vox_policy.md`](vox_policy.md) §7

**Read them there, not here.** Body-not-headline, serious-impact verification,
attribution discipline, the audience-portfolio filter, provider relevance, plain
language and sourcing are all locked in the policy, and the policy is the
authority. *A summary of them lived in this section from 2026-08-17 until it was
removed the same day: reproducing rules is how the two copies drift, and this
Mandate is not their home.*

- **Every item needs a "why an SLTT org cares" clause** tied to the low-maturity California SLTT audience, framed as vendor accountability and procurement or foundational controls (CIS IG1), not developer-level fixes. Items without SLTT relevance get cut.
- **Plain language, minimal-tooling recommendations** (IG1 CIS controls preferred). Audience consumes vendor software; they don't write code. Emphasis on vendor accountability and procurement governance.
- **The vox is content, not a finished product.** No handling markings, no distribution furniture. The distributed product is a separate template with TLP:CLEAR, deeper analysis and presentation polish, built downstream by the team. Never conflate the two.
- **No internal machinery in the reader-facing document** (Vox Policy §4). The header carries the heading, the filename and dates, a paragraph on what the document is, and a note on the scores. It does **not** carry staging-document filenames, stage labels, sensor names, feed URLs or pipeline paths. *"Local reporting was thin this week"* is the collection note; *"the Cal OES feed returned nothing"* is not.
- **Three dates on the distribution product:** title = distribution (Thursday); ICOD line in body = collection cutoff (Monday 0500 PT); LTIOV never printed.
- **Citations nested per entry** (not consolidated endnotes).
- **Source-access check before publishing:** confirm every cited URL is publicly reachable. On 403/paywall/login wall, find an alternative citation for the same reporting. A citation the audience can't open is not usable.
- **Synthesis stays manual** (no API/tokens) — deliberate choice, not a limitation to fix by default.

### Dissemination
- **Distribution target: Thursday afternoon** (after Monday staging, Mon–Tue individual review, Wednesday team review).
- **Product is TLP:CLEAR** — freely shareable, no distribution restriction.

---

## PENDING DIRECTION (act on these; move to Log when done)

- ~~**Verify + load curated AOR trusted sources**~~ — **DONE 2026-08-11.** Loaded and verified live against host egress: `news.caloes.ca.gov/feed/`, `cdt.ca.gov/newsroom/feed/`, `statescoop.com/feed/`, `cisecurity.org/feed/alert`. All four produced on the first cycle. Rejected: `cdt.ca.gov/feed/` (site-wide feed, last updated Apr 2025 — the newsroom sub-feed is the live one) and both GovTech feed paths (0 entries / 404). CA regional press deliberately **not** expanded — the statewide thematic queries already cover it, and individual outlets are largely paywalled. Re-check yield after several cycles; drop any that prove noisy.
- **Fix `process_page` re-collection** (`core/acolyte.py:114`) — page-type sources are deduped on URL hash, so a page is collected once and never revisited. Blocks every portal source below. Small engine change; needs a test.
- **Cal-CSIC cyber advisories** — `caloes.ca.gov/…/cyber-advisories/`. **Confirmed alive and publishing through August 2026.** PDF/DOCX links under month accordions that render out of chronological order; no RSS, no pagination, email-only subscription. Acolyte's existing page-collection path can take it once the dedupe fix above lands — extracting the index page may yield enough, since titles and dates are what the scorer consumes. Prove that before building PDF parsing.
- Build CA AG breach-registry scraper — authoritative AOR breach sensor (web portal, not RSS). **Keep separate from Cal-CSIC**; do not build a shared "portal scraper" abstraction until a second use case forces it.
- Add ransomware leak-site aggregator (e.g. Ransomware.live) filtered for California — early-warning AOR sensor (catches victims before local press).
- **Set a collection timeout** — `core/acolyte.py` sets no timeout on `feedparser.parse` and no `socket.setdefaulttimeout`, so a stalled feed can block a sequential run indefinitely. A full cycle legitimately takes 15–30 min, so a real hang is hard to distinguish from normal slowness.
- **Fix the `run.sh` mode bit** — committed as 644 in every commit, so `./run.sh <domain>` fails on a fresh clone or after `git reset --hard`. Hidden until now because the systemd unit invokes `bash` explicitly. Fix with `git update-index --chmod=+x run.sh`.
- **Decide MSRC volume** — `api.msrc.microsoft.com/update-guide/rss` produced 3,561 of 6,757 lifetime articles (52.7%, ~396/cycle) against a next-largest sensor at 270 lifetime. Per-CVE Patch Tuesday enumeration, not intelligence. Directly contradicts "quality over quantity on sensors." Options: drop, filtered variant, or per-source intake cap.
- **Decide county coverage approach** — direction is high-confidence county-specific sensors rather than keyword queries, but **which counties are in the AOR** must be settled before researching 58 county newsrooms. The dropped keyword set covered 34 of 58 and omitted the population centres.
- ~~**Implement the Arbites recency flag**~~ — **DONE 2026-08-10.** Implemented in `core/arbites.py` (flag stale-by-publish-date vs the cycle window, never drop; configurable in `cti/pnd.md` → `scoring.settings.recency`). Verified by `tests/recency_test.py`; score parity preserved.
- Build distribution template + TLP:CLEAR presentation layer.
- Consider extending Arbites to scaffold a rough Vox draft (reduce chat tether without adding an API).
- Corpus still holds stale county-feed articles; they age out of the 7-day window — expect cleaner Arbites output over the following days.
- Analyst pass on edition v20260810 — merge cross-section duplicates (A/E + G/K), elevate primary sources, verify the Minnesota water-utilities claim.
- Consider widening the recency window — the current 7-day window flags many still-relevant 1–2-week-old items as STALE; a longer window may fit CTI better (tune empirically).
- Host monitoring — deferred.

### Repo hygiene — reviewed and closed 2026-08-11

- **Edition publishing stays manual.** `cti/editions/WCTI_v20260813.md` (renamed from `..._STAGING.md` on 2026-08-17) and `The_Seal.png` (commit `23b61f3`) were placed in the repo deliberately, by hand. **Do not automate edition publishing** and do not propose it. Editions reach the repo when the analyst puts them there.
- **`CCIC` reference in `WCTI_v20260813.md` — reviewed, left as-is.** Line 17 names the CCIC 34-county AOR. Raised as a possible scrub violation (the CCIC title was stripped from the Cogitator during scrubbing, per CHANGELOG 2026-08-11); reviewed by the analyst and accepted. **Do not re-raise.** Note for context: the AOR is 34 counties — this is why the dropped county keyword feeds numbered 34, not a partial rollout.

*(Per-domain status/backlog lives here in the Mandate; the Cogitator is the shared, domain-neutral cycle map at `diagrams/cogitator.drawio`.)*

---

## LESSONS / DECISIONS LOG (dated; newest first)

### 2026-08-13 — Same-event grouping: shipped after the first build failed in production

- **Problem.** Four outlets reporting one incident arrive as four articles. Collection dedup cannot see it — different URLs, different headlines — and scoring **scatters** them, because it keys on terms, not events. Demonstrated live: three realistic Suisun City headlines scored 8.0, 8.0 and **1.0**, and the 1.0 was the only one naming the town. The most useful copy was the one below the cut.
- **The 2026-08 deferral of fuzzy dedup was conditioned on "a real false-*merge*."** The failure actually occurring is a false-*split* — one story wrongly kept apart. The trigger was written for the opposite failure mode and would never have fired. **Lesson: when deferring a fix, state the trigger in terms of the failure you expect, and check it is a failure the mechanism can actually produce.**
- **v1 failed on the live corpus.** Passed a synthetic 204-article test, then on 1,432 real articles produced **one group of 520** — Suisun City reporting chained to OpenAI, CrowdStrike and JetBrains items. Two root causes, both design rather than tuning:
  - **Transitivity.** Union-find meant A~B and B~C merged A, B and C. Across a real corpus that chains without limit.
  - **Rarity was the wrong signal.** v1 called a token distinctive if it appeared in few titles — but a heavily-covered incident puts its distinctive token in *many* titles. The strongest available evidence was being discarded as too common. Tightening the threshold only recreated the earlier bug where the victim's own name was classified as common.
- **v2, shipped.** Head-anchored greedy clustering (an item joins a head it resembles directly, or starts its own — chains cannot form) with IDF-weighted Jaccard similarity, an absolute floor on shared information, oversize dissolution, a display cap, and deterministic tie-breaking.
- **Tuned for precision, not recall, deliberately.** A missed grouping costs nothing beyond the status quo; a false grouping hides an item under an unrelated head. Measured against 29 hand-labelled titles from the failing corpus: **precision 1.00, recall 0.75.**
- **Four independent guards against a repeat of the 520-item cluster:** no transitivity; `min_evidence` (boilerplate overlaps heavily while sharing little information); `max_group_size` (a cluster past 25 is template-matching, not an event — it is dissolved and reported in the header); `max_group_display` (bounds how much of the report one group can occupy).
- **Deterministic ordering added.** Score ties are common, and grouping anchors on whichever member is seen first, so the same corpus could previously produce different heads run to run. Sorting now breaks ties on title then URL. A false positive present in one end-to-end run disappeared once ordering was stable — **non-determinism was masquerading as a tuning problem.**
- **Known limitation:** two genuinely different incidents sharing heavy vocabulary can still group — a second California city cyberattack with its own emergency declaration is the observed near-miss. Grouping is labelled as a suggestion for exactly this reason; the analyst confirms it.
- **Process note.** v1 was tested only against synthetic data of my own construction, which shared the assumptions of the code under test. v2's fixture is 29 real titles from the run that broke it. **Test against the data that failed, not against data you invented.**

### 2026-08-11 — One sensor is over half the corpus
- `api.msrc.microsoft.com/update-guide/rss` produced **3,561 of 6,757** lifetime articles across 9 runs — 52.7%, ~396 per cycle. The next largest sensor has produced 270 *lifetime*.
- This is per-CVE Patch Tuesday enumeration arriving as individual articles. It is volume, not intelligence, and it directly contradicts the standing "quality over quantity on sensors" directive — coverage is not emerging from good sensors well-operated, it is being buried by one.
- **Lesson:** a sensor's yield needs auditing as well as its liveness. A feed can be reliable, additive on paper, and still be wrong for the apparatus because of the *shape* of what it emits. Add intake volume to the criteria for admitting a feed.
- Decision pending in Pending Direction.

### 2026-08-11 — Read what production already records before building a tool
- A candidate-feed validator script and a proposed `--check` flag on Acolyte were both drafted, then discarded unbuilt. `acolyte.py` already logs per-URL yield and per-URL failures every cycle, so a `grep` and an `awk` over `collector.log` answered feed liveness, lifetime yield, and dead-vs-quiet completely.
- The log also caught a wrong explanation. Two sensors showing 0 new across 9 runs were first written up as "collected once, then URL-deduped into silence." The log said otherwise: both logged `WARNING no text` on **every** cycle, meaning they yielded neither feed entries nor extractable page text and were re-fetched in full each run. The corrected reason was pushed to `cti/pnd.md`, the changelog and this file.
- **Lesson within the lesson:** a plausible mechanism is not evidence. The dedupe story fit the symptom and was wrong; one `grep` for the `no text` warning settled it. Check the log before writing a cause into three documents.
- **Lesson:** the collector's own log is the sensor-health instrument. Query it before writing anything.

### 2026-08-11 — `production` config is advisory, not enforced
- `core/arbites.py` loads the `production` block but reads only `report_title`. `item_target` and `sections` are referenced nowhere in `core/`.
- **Consequence for the edition-size question:** editing `item_target` changes nothing mechanically. A bigger *product* means changing doctrine plus analyst behaviour. The two are separate levers and only one is code.
- **Superseded 2026-08-17.** This entry named `scoring.settings.surface_n` as the sole code-enforced production knob. That knob was a rank cut — a cap — and Vox Policy §7 forbids caps, so it was removed from the engine. The code-enforced knobs are now `scoring.settings.surface_min_score` (a threshold) and `scoring.force_surface` (guaranteed inclusions). The reasoning above still holds; only the lever changed.
- Consistent with "synthesis stays manual" — the production block is documentation for the human stage.

### 2026-08-11 — When clones disagree, check commit dates before assuming
- The collector host was found running 82 sensors against the repo's 48. This read as unpushed host drift; it was the opposite. The host had never pulled since publication (history was rewritten at first release, so a plain pull will not fast-forward) and was still running the pre-drop county-feed config. The repo was ahead the whole time.
- A second check compounded it: a `grep -c` line count matched by coincidence and masked the mismatch.
- **Lesson:** compare commit timestamps before deciding which clone is ahead, and verify *content* — a count can collide.

### Recency gate: enforce by publish-date, not collect-date
- A June FortiBleed advisory (pub. 2026-06-18) surfaced in edition v20260810. Root cause: "current week" was effectively windowed on the *collection* date, and the score carries no recency term — so a feed re-serving an old item (advisory update, re-list, roundup, KEV resurfacing) lands it in the current corpus, where it ranks on relevance.
- Fix logged as a **Codex Layer-4 rule** (recency gate — flag items published outside the cycle window as "STALE — confirm current hook," never hard-drop; keep old-CVE/new-exploitation re-emergences). **The rule lives in the Codex; this is the breadcrumb.**
- Interim (until Arbites codes it): synthesis-layer check — cut items published outside the cycle week unless they carry a fresh this-week hook.
- Cogitator Stage 3 updated with the recency gate; Arbites backlog carries the build.

### 2026-08 — Pre-filter (Arbites) built and tuned on live corpus
- Keyword scoring has substring-collision failure modes: "cisco" matched inside "San Francisco," "hack" inside culinary usage, "ics" inside other words. Fixed with word-boundary matching for short/ambiguous terms.
- Tier-1 (California-direct) must require California as the SUBJECT of an incident (in the title, or in close proximity to an incident word), not a passing mention. A national article that merely lists "...including California..." must not inherit tier-1. This protects genuine AOR items from being outranked by national name-drops.
- Empty-title feed artifacts get floored and flagged, not ranked.
- Result: genuine California SLTT incidents (school-district and hospital ransomware) now surface correctly at the top.

### 2026-08 — External review (Gemini) incorporated
- **Accepted:** upstream pre-filter/staging script (built as Arbites); ransomware leak-site aggregator as a new AOR sensor; cross-section dedup discipline; primary-source elevation.
- **Rejected:** additive 0–100 scoring model with tier floors — it would reverse the deliberate convergence-wins design. The valid sub-point (multiplicative scores look falsely precise) is handled by treating the score as an ordering aid, which is already doctrine.
- **Deferred:** fuzzy dedup (Jaccard/Levenshtein) — over-engineered; revisit only if a real false-merge is observed. **Revisited 2026-08-11 — see below.**

### 2026-08 — County keyword feeds dropped
- 34 county Google News query feeds returned local human-interest news, not cyber incidents. Root cause: keyword search on a general index treats cyber terms as soft hints, not hard filters. Architecturally wrong, not tunable. Rebuild AOR coverage via curated reliable sources + authoritative breach registry.

### 2026-08 — Collection doctrine settled
- Quality over quantity: strict on sensors, generous on items. Reliable + additive is the bar for adding a feed. Coverage emerges from good sensors well-operated, not from adding feeds.

### 2026-08 — Dedup hardened
- Added normalized-title dedup alongside URL-hash dedup (Google News links are redirect tokens, so URL-hash alone let the same story survive across feeds). Confirmed: a large backfill run dropped ~98% on the immediate second pass.

---

*End of Mandate. This document + the Codex + the `pnd.md` sensors are sufficient for any session to run the cycle. Keep it current — it is the memory of the intelligence cycle.*
