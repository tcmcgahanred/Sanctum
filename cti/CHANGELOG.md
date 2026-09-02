# CTI — Changelog

*Dated history for the CTI domain. Nothing here is operative. The operative rules
live in [`pnd.md`](pnd.md); what survived this history lives in the tenets at the
top of that file. This exists so a decision can be traced, not so it has to be
re-read before acting.*

---

## Vocabulary decisions

*Sanctum · CTI domain · the reasoning behind the word lists in `pnd.md`.*

**Version:** v1 — first pass. Established 2026-08-17 when the vocabulary method
(`../docs/VOCABULARY.md`) was written down and `tools/vocab_check.py` was run against
this domain for the first time.

> **This file never repeats the term lists.** `pnd.md` is the single source of
> truth for terms. This file records *decisions about* terms — what was dropped
> and why, what collides, what is missing, when each group was last reviewed.
> Two copies of the same words drift within a month.

---

### v1 changelog

1. **Boundary list reduced from 11 entries to 4.** Seven were dead. `hack`,
   `leak` and `war` matched no live term in any group — the terms they guarded
   had been removed at some earlier point and the entries survived. `ics`,
   `grid`, `uc` and `csu` are four characters or fewer, where the matcher
   already applies word boundaries automatically, so the entries added nothing.
   All seven removals are provable no-ops; parity confirms scoring is unchanged.
   Remaining: `scada`, `ransom`, `court`, `cisco`.

2. **No terms added or removed from any group.** Everything below marked as a
   gap or a collision is *recorded, not fixed* — vocabulary content is a
   Planning & Direction decision and belongs in the CTI briefing chat.

---

### v2 changelog - 2026-08-24, scoring precision

Two P&D work orders in one day. The first tightened matching after the staging
queue's top filled with false positives; the second approved the vocabulary that
stops the tightening from creating misses. **Every change is a precision change.
No requirement was dropped.**

1. **`sector` rewritten from bare nouns to compound terms.** The worst entry was
   `water`, which gave tier 2 (weight 4.0) to an Australian hotel with a water
   park and to a Comcast release about a water-cooled data centre. Dropped:
   `water`, `utility`, `utilities`, `college`, `tribal`, `election`, `transit`,
   `court`, `sheriff`. Added: `water utility`, `water district`,
   `water authority`, `water treatment`, `water system`, `water sector`,
   `drinking water`, `utility district`, `public utility`, `electric utility`,
   `utility sector`, `community college`, `school system`, `public schools`,
   `public works`, `tribal government`, `tribal nation`, `election office`,
   `election systems`, `transit agency`, `transit authority`, `superior court`,
   `county court`, `sheriff's office`, `sheriff's department`. **An ordinary
   English word cannot carry a sector requirement.**
2. **`ci` rewritten the same way**, for the same reason: it feeds the
   ransomware-versus-critical-infrastructure multiplier, where bare `water`,
   `utility`, `power`, `grid`, `school` and `government` fired on nearly
   anything.
3. **`kev` was doing two jobs**, mixing exploitation evidence with generic
   vulnerability vocabulary, so a buyer's guide saying "a zero-day is always a
   possibility" scored as an exploited flaw. **New group `exploit_strong`**
   carries only exploitation evidence. `kev` is retained, used by no rule.
   **When a group turns out to be two groups, split it; do not delete half.**
4. **`incident` gained theft and intrusion language** - `hackers`, `stolen data`,
   `data theft`, `blackmail`, `defaced`, `defacement`. The trigger was a real
   miss: *"Hackers Release Stolen Data From State's Largest School District"*
   matched `school district` in the title and then failed for want of an
   incident word, because the group held `hacked` (not "hackers") and
   `data stolen` (not "stolen data"). **Word order and plurality are not
   details here.**
5. **Availability language deliberately kept OUT of `incident`.** `outage`,
   `denial of service` and `ddos` live in `targeting` only. `incident` feeds
   tier 1 and force-surface M1, which need a place name plus one incident word,
   so `outage` there would turn every California wildfire or public safety power
   shutoff into an AOR cyber incident. In `targeting` the same words fire only
   where the sector is already the subject. Genuine cyber-caused outages still
   reach M1 through `ransomware`, `breach`, `hacked` and the new theft terms.
   P&D work order 2026-08-24, decision 4.
6. **`hacker` singular is confined to `incident_broad`, and is ON WATCH.** It is
   noise-prone - *ethical hacker*, *hacker conference*, the feed name *The Hacker
   News*. Held there it can only fire where the sector is already the subject and
   can never reach tier 1. **If it over-fires next cycle, drop the singular and
   keep only `hackers`.**
7. **New groups `targeting` and `incident_broad`.** The second is the union of
   the first two plus `hacker`, needed because the `proximity` atom takes one
   group per side. Keep it as that union.
8. **New group `listicle`** - headline shapes that are never incident reporting.
   Title-matched, used through `not`, so it withholds a tier rather than
   dropping anything.
9. **New groups `cve` and `cisa_source`.** `cve` tests whether exploitation
   language sits near a real identifier. `cisa_source` is matched against the
   article's SOURCE, never its text, so an official directive can be told apart
   from a trade write-up about one.
10. **Boundary list is now `scada`, `ransom`, `cisco`, `how to`, `what is`,
    `hacker`.** `court` was orphaned when bare `court` left `sector`; `cve-` is
    four characters and gets boundaries automatically. **The guard caught all of
    these** - none was found by reading.

#### Still open after this pass

- **`incident` remains incomplete** - see Open finding 1. This pass closed the
  theft and defacement gap; wipers, destruction and recovery-inhibition are
  still absent, and availability language is confined to `targeting` by design.
  **Expect a few more gaps per cycle. The fix is always a term add, never a rule
  loosening.**
- **No education-sector term.** *"ShinyHunters Targets Education Sector with
  Oracle PeopleSoft Exploit"* falls from 15.21 to 1.0: `sector` has
  `school district`, `university` and `community college`, but not
  `education sector` or `higher education`. Raised before the work order and not
  among the approved terms, so not added. **P&D decision.**
- **`geo` does not cover the whole state, by design, and that now shows.**
  *"El Cerrito Blackmailed by Notorious Cyber Gang"* cannot surface: El Cerrito
  is in Contra Costa County, which is not among the 34 counties in `geo`. Adding
  `blackmail` did not help, because **the failure is geographic, not lexical**.
  Whether the AOR is 34 counties or wider is a P&D decision.

### v3 changelog - 2026-08-31, the homonym gate

A third homonym reached tier 1, and this time it force-surfaced.

1. **"breach" is not a cyber word.** *"A Baby Great White Leapt from the Ocean Near a
   Boogie Boarder"* scored **8.0, tier 1, force-surfaced on M1** — `geo:'california'`
   matched the beach and `incident:'breach'` matched a shark breaching the surface.
   The same word is a levee, a contract, a courtroom verdict and a code of conduct.
   An earlier great-white item escaped only because it was stale.

2. **The obvious fix was measured and rejected.** Removing bare `breach` and keeping
   only compounds — `data breach`, `security breach` — was tested against 776 real
   items. It removed 15 false positives and **took at least 10 genuine items with
   them**, including two LACMA data breach stories, the Madera Community Hospital
   class action and the FBI item on a Chinese hacking group. **Root cause:** tier 1's
   proximity atom names `incident` as a string, so it always reads the raw group.
   Narrow the group and any article whose only incident word near the California
   mention was `breach` falls out — *even when "data breach" is in its own headline*.
   **Proximity cannot be guarded from outside the group it names.**

3. **The owner's instinct was right and his word was wrong.** He proposed requiring
   the word "cyber". Measured: that would have deleted the California DMV data
   breach, the LA Superior Court ransomware shutdown, the Northern Inyo Hospital
   breach and all three tier-3 vulnerability advisories — 44 of 137 surfaced items,
   roughly half of them the most in-scope in the set. **Incident reporting does not
   say "cyber."** Journalists and policy writers do.

4. **What shipped: a cyber-domain gate.** A new group `cyber_context` — 39 terms, the
   language a computer story actually uses — is now a required conjunct on tiers 1, 2
   and 3 and on all three force-surface rules. Measured on the same 776 items: **16 of
   137 surfaced items removed, and all 16 are non-cyber** — sharks, whale watching,
   two lottery suits, Oakley v Nike, a reinsurance dispute, Justice Thomas at Stanford.
   Zero genuine losses. **`breach` was not touched.**

5. **A four-character stem is not a stem.** The first version used `hack`. The matcher
   gives any term of 4 characters or fewer automatic word-boundary matching, so `hack`
   matched the standalone noun and nothing else — and *"Attackers Targeted Over 100 US
   Water Systems in July Hacks"*, a tier-2 water-sector item, was deleted by one plural
   noun. Every form is now spelled out. **Same 4-character rule as Open finding 2.**

**The class, stated once:** an ordinary English word cannot carry a requirement. This is
the third instance — `water` in `sector`, `" calif "` in `geo`, now `breach` in
`incident`. The cure is never to delete the term. It is to require context.

---

## Verification status

**Not yet validated against live output.** Per `../docs/VOCABULARY.md` §7:

- [x] `tools/vocab_check.py` passes with the accepted finding recorded
- [x] Parity test confirms the boundary-list reduction changed no score
- [ ] Read the drop list before the candidate list for the next three cycles
- [ ] Confirm `surface_min_score: 2.0` produces a sane surface size — the value
      is provisional and has never been measured against the live corpus
- [ ] Count how often M1 fires on a passing mention rather than a subject — the
      rule is a co-occurrence approximation, not subject-of detection

---

## Cycle lessons and decisions

#### 2026-08-13 — Same-event grouping: shipped after the first build failed in production

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

#### 2026-08-11 — One sensor is over half the corpus
- `api.msrc.microsoft.com/update-guide/rss` produced **3,561 of 6,757** lifetime articles across 9 runs — 52.7%, ~396 per cycle. The next largest sensor has produced 270 *lifetime*.
- This is per-CVE Patch Tuesday enumeration arriving as individual articles. It is volume, not intelligence, and it directly contradicts the standing "quality over quantity on sensors" directive — coverage is not emerging from good sensors well-operated, it is being buried by one.
- **Lesson:** a sensor's yield needs auditing as well as its liveness. A feed can be reliable, additive on paper, and still be wrong for the apparatus because of the *shape* of what it emits. Add intake volume to the criteria for admitting a feed.
- Decision pending in Pending Direction.

#### 2026-08-11 — Read what production already records before building a tool
- A candidate-feed validator script and a proposed `--check` flag on Acolyte were both drafted, then discarded unbuilt. `acolyte.py` already logs per-URL yield and per-URL failures every cycle, so a `grep` and an `awk` over `collector.log` answered feed liveness, lifetime yield, and dead-vs-quiet completely.
- The log also caught a wrong explanation. Two sensors showing 0 new across 9 runs were first written up as "collected once, then URL-deduped into silence." The log said otherwise: both logged `WARNING no text` on **every** cycle, meaning they yielded neither feed entries nor extractable page text and were re-fetched in full each run. The corrected reason was pushed to `cti/pnd.md`, the changelog and this file.
- **Lesson within the lesson:** a plausible mechanism is not evidence. The dedupe story fit the symptom and was wrong; one `grep` for the `no text` warning settled it. Check the log before writing a cause into three documents.
- **Lesson:** the collector's own log is the sensor-health instrument. Query it before writing anything.

#### 2026-08-11 — `production` config is advisory, not enforced
- `core/arbites.py` loads the `production` block but reads only `report_title`. `item_target` and `sections` are referenced nowhere in `core/`.
- **Consequence for the edition-size question:** editing `item_target` changes nothing mechanically. A bigger *product* means changing doctrine plus analyst behaviour. The two are separate levers and only one is code.
- **Superseded 2026-08-17.** This entry named `scoring.settings.surface_n` as the sole code-enforced production knob. That knob was a rank cut — a cap — and Vox Policy §7 forbids caps, so it was removed from the engine. The code-enforced knobs are now `scoring.settings.surface_min_score` (a threshold) and `scoring.force_surface` (guaranteed inclusions). The reasoning above still holds; only the lever changed.
- Consistent with "synthesis stays manual" — the production block is documentation for the human stage.

#### 2026-08-11 — When clones disagree, check commit dates before assuming
- The collector host was found running 82 sensors against the repo's 48. This read as unpushed host drift; it was the opposite. The host had never pulled since publication (history was rewritten at first release, so a plain pull will not fast-forward) and was still running the pre-drop county-feed config. The repo was ahead the whole time.
- A second check compounded it: a `grep -c` line count matched by coincidence and masked the mismatch.
- **Lesson:** compare commit timestamps before deciding which clone is ahead, and verify *content* — a count can collide.

#### Recency gate: enforce by publish-date, not collect-date
- A June FortiBleed advisory (pub. 2026-06-18) surfaced in edition v20260810. Root cause: "current week" was effectively windowed on the *collection* date, and the score carries no recency term — so a feed re-serving an old item (advisory update, re-list, roundup, KEV resurfacing) lands it in the current corpus, where it ranks on relevance.
- Fix logged as a **Codex Layer-4 rule** (recency gate — flag items published outside the cycle window as "STALE — confirm current hook," never hard-drop; keep old-CVE/new-exploitation re-emergences). **The rule lives in the Codex; this is the breadcrumb.**
- Interim (until Arbites codes it): synthesis-layer check — cut items published outside the cycle week unless they carry a fresh this-week hook.
- Cogitator Stage 3 updated with the recency gate; Arbites backlog carries the build.

#### 2026-08 — Pre-filter (Arbites) built and tuned on live corpus
- Keyword scoring has substring-collision failure modes: "cisco" matched inside "San Francisco," "hack" inside culinary usage, "ics" inside other words. Fixed with word-boundary matching for short/ambiguous terms.
- Tier-1 (California-direct) must require California as the SUBJECT of an incident (in the title, or in close proximity to an incident word), not a passing mention. A national article that merely lists "...including California..." must not inherit tier-1. This protects genuine AOR items from being outranked by national name-drops.
- Empty-title feed artifacts get floored and flagged, not ranked.
- Result: genuine California SLTT incidents (school-district and hospital ransomware) now surface correctly at the top.

#### 2026-08 — External review (Gemini) incorporated
- **Accepted:** upstream pre-filter/staging script (built as Arbites); ransomware leak-site aggregator as a new AOR sensor; cross-section dedup discipline; primary-source elevation.
- **Rejected:** additive 0–100 scoring model with tier floors — it would reverse the deliberate convergence-wins design. The valid sub-point (multiplicative scores look falsely precise) is handled by treating the score as an ordering aid, which is already doctrine.
- **Deferred:** fuzzy dedup (Jaccard/Levenshtein) — over-engineered; revisit only if a real false-merge is observed. **Revisited 2026-08-11 — see below.**

#### 2026-08 — County keyword feeds dropped
- 34 county Google News query feeds returned local human-interest news, not cyber incidents. Root cause: keyword search on a general index treats cyber terms as soft hints, not hard filters. Architecturally wrong, not tunable. Rebuild AOR coverage via curated reliable sources + authoritative breach registry.

#### 2026-08 — Collection doctrine settled
- Quality over quantity: strict on sensors, generous on items. Reliable + additive is the bar for adding a feed. Coverage emerges from good sensors well-operated, not from adding feeds.

#### 2026-08 — Dedup hardened
- Added normalized-title dedup alongside URL-hash dedup (Google News links are redirect tokens, so URL-hash alone let the same story survive across feeds). Confirmed: a large backfill run dropped ~98% on the immediate second pass.

---

*End of Mandate. This document + the Codex + the `pnd.md` sensors are sufficient for any session to run the cycle. Keep it current — it is the memory of the intelligence cycle.*

---

## Repo hygiene — reviewed and closed 2026-08-11

- **Edition publishing stays manual.** `cti/editions/WCTI_v20260813.md` (renamed from `..._STAGING.md` on 2026-08-17) and `The_Seal.png` (commit `23b61f3`) were placed in the repo deliberately, by hand. **Do not automate edition publishing** and do not propose it. Editions reach the repo when the analyst puts them there.
- **`CCIC` reference in `WCTI_v20260813.md` — reviewed, left as-is.** Line 17 names the CCIC 34-county AOR. Raised as a possible scrub violation (the CCIC title was stripped from the Cogitator during scrubbing, per CHANGELOG 2026-08-11); reviewed by the analyst and accepted. **Do not re-raise.** Note for context: the AOR is 34 counties — this is why the dropped county keyword feeds numbered 34, not a partial rollout.

*(Per-domain status/backlog lives here in the Mandate; the Cogitator is the shared, domain-neutral cycle map at `diagrams/cogitator.drawio`.)*

---

---

## Reasoning relocated from `pnd.md`, 2026-09-01

*`cti/pnd.md` became `cti/pnd.yaml` — configuration and comments only. Everything below is the prose that surrounded those values, moved here **verbatim and uncompressed**. Nothing was rewritten in the move, so a claim can be checked against what it said before. Compressing this, and re-keying it by the setting each entry concerns, is a separate change.*

### From `pnd.md` — CTI — Sanctum domain file

*One file. Everything the CTI effort needs to run, in the order the intelligence
cycle runs it. The engines in `core/` read only the fenced `yaml` and `sensors`
blocks below; every other line is for the person reading it.*

**BLUF:** Stage 1 says what we need to know. Stage 2 says where to look. Stage 3a
says what the machine does with what it found. Stage 3b says what the person does
with it. Nothing else about CTI lives anywhere else.

### From `pnd.md` — The eight tenets

Every decision in this file answers to these. They are copied from the repository
`README.md` so that nobody has to leave this file to check one.

1. **The engine knows nothing about any subject.** One configuration file per subject is the only thing that changes, and it declares settings — it never contains logic.
2. **Human in the loop.** A person decides every item — the score only puts them in order. Nothing in the code calls a language model or spends a token.
3. **Nothing is hidden.** Every item shows why it scored what it did, and everything set aside is still listed by name.
4. **Show everything that qualifies; narrow later.** The number of items is a result, not a target. If the output is too big, change the priorities — never cap the list.
5. **Be picky about sources, not about articles.** Drop a noisy source without hesitation; keep the marginal article from a good one.
6. **It stops at the vox.** Sanctum prepares; it does not conclude.
7. **Keep it small.** Don't build until something needs it. Delete what has stopped being used — leftovers mislead whoever reads them next.
8. **Nothing identifying goes in the repo.** No secrets, no personal or infrastructure detail. Verify rather than assume; changes that alter behaviour are proven by tests.

### From `pnd.md` — How to read this file

| Stage | Section below | What the engine reads |
|---|---|---|
| 1 · Planning & Direction | Stage 1 | `manifest:` (runtime and storage) |
| 2 · Collection | Stage 2 | `manifest.collection:` and the ```` ```sensors ```` block |
| 3a · Processing | Stage 3a | `scoring:` and `vocab:` |
| 3b · Exploitation | Stage 3b | `production.report_title` only |

Dated history — what changed, when, and what it cost — is **not** here. It is in
[`CHANGELOG.md`](CHANGELOG.md). What survived the history is in the tenets above.

---

### From `pnd.md` — Stage 1 — Planning & Direction

*What we need to know, who decided it, and where the machine keeps its things.*

### From `pnd.md` — HOW TO USE THIS DOCUMENT (for a fresh chat session)

1. Read the Standing Directives — they are the current operative rules. Apply them.
2. Read Pending Direction — that's what this cycle or the next should act on.
3. When the cycle ends, add lessons to the Log and update directives/pending as needed.
4. If a directive here conflicts with an ad-hoc request, the directive is the retained decision — confirm before overriding.

---

### From `pnd.md` — WEEKLY CADENCE (the operative schedule)

| When | Step |
|------|------|
| **Wednesday 0400 PT** | **Collector runs. Collection cutoff = ICOD** ("information current as of"). Corpus windowed on the 7 days ending here. |
| **Wednesday, complete by 0500** (same run) | **Staging document written** by `arbites.py` — 3a, machine, deterministic. Pushed to the staging store. |
| **Wednesday 0600** | **Vox created** from the staging document — 3b, operator plus a model, per `../docs/EXPLOITATION.md`. |
| **Wednesday, rest of day** | **Individual review / amend** — analyst verification and edits. |
| **Thursday morning** | **Team review.** |
| **Thursday afternoon** | **Distribution** — finished report sent. This is the product's **title date**. |

**Three dates — keep them distinct:**
- **Title date = distribution (Thursday).** What the product is dated.
- **ICOD line = collection cutoff (that week's Wednesday 0400 PT).** Carried in the product body: "information current as of …".
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

### From `pnd.md` — STANDING DIRECTIVES (current operative rules)

##### Chat is a consumer of requirements, never a source

**The rule itself is R13 in [`../docs/EXPLOITATION.md`](../docs/EXPLOITATION.md)**,
where it reaches every domain and every clone rather than only this one. It is
not restated here — one rule, one file.

**What is CTI-specific:** requirements are defined in §1.2, the requirements tree,, the
scoring model that implements them in `cti/pnd.md`, and each tier declares the
requirement it answers with `serves:` and the elements with `serves_eei:` — by
identifier only, never by statement. The staging document emits both. The vox
copies them.

##### Collection
- **Quality over quantity on sensors.** A feed earns its place only if reliable AND additive (offers a vantage the others don't). Drop noisy sensors rather than filter them.
- **Trusted sources ingested wholesale; AOR relevance decided at scoring**, not by keyword pre-filtering at collection.
- **Verify every feed URL against the current host's actual egress** before loading (some sources 403 datacenter/server IPs even when they work from a browser).
- **Collection window: the 7 days ending Wednesday 0400 PT (ICOD).** The window closes at the 0400 cutoff and the staging document is built from that closed corpus in the same run. **The cutoff is 0400 and not 0500 because a run takes 36 minutes** (collection 20m01s, scoring 16m04s, measured 2026-08-26) and `compute_cycle_window` walks back a **whole week** if the declared cutoff time has not yet passed when scoring runs. Starting at 0400 puts the finished staging document in the staging store before 0500, which is when it is wanted.
- **Dropped and why:** 34 county Google News keyword feeds — keyword search on a general news index returns the county's whole news firehose, not its cyber incidents. Wrong instrument for precision local detection. Do not reintroduce keyword-query feeds.

##### Analysis / Scoring
- **Multiplicative scoring** (tier weight × product of elevation multipliers). Convergence wins by design — a heavily-elevated lower-tier item can outrank a bare higher-tier item. This is intentional.
- **The score is an ordering aid, not a measurement.** The analyst always overrides it.
- **Prefer false positives to false negatives on items.** Missing a real AOR threat is far costlier than surfacing an extra item to skim.
- **Strict on sensors, generous on items.** Quality gate applies to feeds, not to individual articles from good feeds.
- **One event, one entry.** Place an incident in the section matching its dominant value; fold secondary angles in. Do not repeat it across sections.
- **Recency by publication date, not collection date.** Flag items published outside the collection window as "STALE — confirm current hook"; never hard-drop (keep old-CVE/new-exploitation re-emergences). Rule lives in Codex Layer 4.
- **Arbites (pre-filter) known limits the analyst must catch:** keyword scoring can mis-tag on proximity (e.g., a national article discussing California near an incident word looks tier-1 — check the title), and national threat-landscape roundups score mid-pack. These are expected; the human gate catches them.

##### Production
- **NO CAP ON THE REVIEW SURFACE — trust the weights.** *(Vox Policy §7. Supersedes the item targets this document carried until 2026-08-17.)* There is no fixed limit on items per section or overall. Every item that qualifies — by score, or by the mandatory-surface rule below — appears, however many that is. If 20 high-weight items qualify, 20 surface. **The count is an OUTPUT of the scoring and the rules, never a target imposed on top of them.**
  - The former targets (~5–6 per section, ~15–18 total) were exactly such a cap and have been removed here and from `pnd.md` (and from `codex.md`, before that file was retired).
  - Surface-vs-drop is now a **score threshold** — `scoring.settings.surface_min_score` — plus guaranteed inclusions. Never a rank cut.
- **If the surface is too large or too noisy, tune Sanctum — do not cap.** Adjust the weights, the mandatory-surface vocabulary, or the exclusion operators. Capping hides what the scoring did and destroys the feedback that tunes it. **The uncapped surface IS the diagnostic.**
- **Mandatory-surface rule — inclusion, not ranking.** An item is force-surfaced regardless of score if it meets any of: **(M1)** an in-AOR entity is the subject of a cyberattack, breach or disruption; **(M2)** in-the-wild exploitation, weaponised public PoC, or KEV addition **and** the affected product is in the SLTT-relevant technology vocabulary; **(M3)** a specific incident confirms an SLTT sector was targeted or impacted. Score still orders everything, so a forced low-scoring item sits at the bottom of the surface with its ranking/relevance disagreement visible — which is the tuning signal. **Known limit: these rules can only fire on vocabulary the domain has already declared** — see §3a.2, the vocabulary section,, Open finding 1.
- **"Restraint is the product" governs the DISTRIBUTED product only.** Restraint is the finished report's virtue, applied by the cyber team as editorial judgment after review. It is never an automated cap on what surfaces. The distributed target (5–8 items, Thursday) sits **outside Sanctum's scope** and is recorded here for reference only.
- **A wider surface does not lower the standard.** The added entries are lower-ranked items from the *same* sorted queue — lower tier and/or fewer elevation signals, not lower-quality sourcing. Every entry still shows its scoring reasoning so the analyst can audit where the cut falls.
###### Content standards — owned by §3b.2 Vox policy §7

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
- **Three dates on the distribution product:** title = distribution (Thursday); ICOD line in body = collection cutoff (Wednesday 0400 PT); LTIOV never printed.
- **Citations nested per entry** (not consolidated endnotes).
- **Source-access check before publishing:** confirm every cited URL is publicly reachable. On 403/paywall/login wall, find an alternative citation for the same reporting. A citation the audience can't open is not usable.
- **Synthesis stays manual** (no API/tokens) — deliberate choice, not a limitation to fix by default.

##### Dissemination
- **Distribution target: Thursday afternoon** (after Wednesday staging, Wednesday individual review, Thursday-morning team review).
- **Product is TLP:CLEAR** — freely shareable, no distribution restriction.

---

### From `pnd.md` — PENDING DIRECTION (act on these; move to Log when done)

- ~~**Verify + load curated AOR trusted sources**~~ — **DONE 2026-08-11.** Loaded and verified live against host egress: `news.caloes.ca.gov/feed/`, `cdt.ca.gov/newsroom/feed/`, `statescoop.com/feed/`, `cisecurity.org/feed/alert`. All four produced on the first cycle. Rejected: `cdt.ca.gov/feed/` (site-wide feed, last updated Apr 2025 — the newsroom sub-feed is the live one) and both GovTech feed paths (0 entries / 404). CA regional press deliberately **not** expanded — the statewide thematic queries already cover it, and individual outlets are largely paywalled. Re-check yield after several cycles; drop any that prove noisy.
- **Fix `process_page` re-collection** (`core/acolyte.py`) — page-type sources are deduped on URL hash, so a page is collected once and never revisited. Blocks every portal source below. **Design settled 2026-08-25, deliberately not built:** identity must key on the page's CONTENT, not its URL. Naive content hashing is not enough — a news index page changes on every visit (dates, navigation, promoted items), so it would write a near-duplicate record every run. It needs a similarity threshold, and that threshold has to be measured against a real page on the collector host rather than guessed in an authoring sandbox.
- **Cal-CSIC cyber advisories** — `caloes.ca.gov/…/cyber-advisories/`. **Confirmed alive and publishing through August 2026.** PDF/DOCX links under month accordions that render out of chronological order; no RSS, no pagination, email-only subscription. Acolyte's existing page-collection path can take it once the dedupe fix above lands — extracting the index page may yield enough, since titles and dates are what the scorer consumes. Prove that before building PDF parsing.
- Build CA AG breach-registry scraper — authoritative AOR breach sensor (web portal, not RSS). **Keep separate from Cal-CSIC**; do not build a shared "portal scraper" abstraction until a second use case forces it.
- Add ransomware leak-site aggregator (e.g. Ransomware.live) filtered for California — early-warning AOR sensor (catches victims before local press).
- ~~**Set a collection timeout**~~ — **DONE 2026-08-25.** `socket.setdefaulttimeout` is set in `acolyte.main()` to twice the configured fetch timeout. A process-wide default is the only lever that reaches `feedparser.parse`, which honours no timeout argument. Real: `news.sophos.com` was measured tarpitting at 120s per attempt while a browser user-agent was being sent.
- **Fix the `run.sh` mode bit** — committed as 644 in every commit, so `./run.sh <domain>` fails on a fresh clone or after `git reset --hard`. Hidden until now because the systemd unit invokes `bash` explicitly. Fix with `git update-index --chmod=+x run.sh`.
- ~~**Decide MSRC volume**~~ — **DONE 2026-08-25: dropped, but NOT on volume.** The lifetime total (4,346 items over 21 runs) is a **backfill artifact already dismissed 2026-08-17** — 3,482 arrived on the sensor's first poll and 744 the day after Patch Tuesday; ongoing volume is about six a day. What settled it was **sole source of zero distinct surfaced events across 21 runs**, measured by `tools/sensor_health.py`. Two further findings closed it: every item link is a JavaScript shell that no fetch strategy recovers, and Microsoft's own CVRF API would deliver the same per-CVE flood more cleanly rather than fix it. Full record and the reasons not to reintroduce it are in `cti/pnd.md`. Microsoft coverage is unaffected — Microsoft Threat Intelligence is a separate sensor and stays.
- **Decide county coverage approach** — direction is high-confidence county-specific sensors rather than keyword queries, but **which counties are in the AOR** must be settled before researching 58 county newsrooms. The dropped keyword set covered 34 of 58 and omitted the population centres.
- ~~**Implement the Arbites recency flag**~~ — **DONE 2026-08-10.** Implemented in `core/arbites.py` (flag stale-by-publish-date vs the cycle window, never drop; configurable in `cti/pnd.md` → `scoring.settings.recency`). Verified by `tests/recency_test.py`; score parity preserved.
- Build distribution template + TLP:CLEAR presentation layer.
- Consider extending Arbites to scaffold a rough Vox draft (reduce chat tether without adding an API).
- Corpus still holds stale county-feed articles; they age out of the 7-day window — expect cleaner Arbites output over the following days.
- Analyst pass on edition v20260810 — merge cross-section duplicates (A/E + G/K), elevate primary sources, verify the Minnesota water-utilities claim.
- Consider widening the recency window — the current 7-day window flags many still-relevant 1–2-week-old items as STALE; a longer window may fit CTI better (tune empirically).
- **Set `max_publish_age_days` from measurement, not from the cycle window.** Added 2026-08-25 at 7 days, matching the cycle window because that is what the direction said. The two answer different questions: the recency gate asks "is this still current?" and LABELS it, the collection cutoff asks "is this certainly worthless?" and DELETES it. Only one is destructive and only one had a measured basis. **This is also the first place in Sanctum that drops rather than flags** — a deliberate break with tenet 8, recorded as a doctrine change. Every item the audit complained about was published before 2026, so any cutoff between 8 and 237 days would have caught all of them; that range constrains nothing. Run `tools/lag_check.py` and take the smallest cutoff that deletes 0.0% of surfacing items, plus margin. Rejections are now named in the log (`grep REJECTED-AGE`), so the cost of whatever number is chosen can be audited rather than assumed.
- **Prune candidates, measured 2026-08-25, none acted on.** Sensors have been added all week and none removed; tenet 6 is quality over quantity. `hackread` — 10 entries, 0 fresh, 0 usable words on every strategy. The Register — 92% removal rate, already carrying a two-cycle stay. MSRC — see above. Read `tools/sensor_health.py` across several cycles before cutting anything, and prefer removing a feed that is both silent AND unusable over one that is merely quiet.
- **Is AI-assistant security in scope?** The scoring model has **no AI or LLM vocabulary at all** — no prompt injection, assistant, copilot, model, or vendor names. Any item in that class scores tier 4 and dies in the drop list whatever sensor delivers it; a Malwarebytes article on prompt injection against Grok and Gemini was scored live at 1.00 against a 2.0 threshold. The audience is adopting these tools through Workspace and Microsoft 365, and the framing fits §6.3's vendor-accountability clause. If the answer is yes, this is a vocabulary work order and it matters more than any sensor addition.
- **Realign `sector` and `ci` to CISA standard names.** Both groups use ad-hoc terms — `water utility`, `school district`, `sheriff's department`, `transit agency`. Standing direction 2026-08-25 is to use CISA sectors, subsectors, segments and assets. Verified taxonomy in the project at `cti/references/cisa_sector_taxonomy.md`. Note the trap: articles say "school district", not "Education Services and Facilities Subsector", so a word list of CISA names alone would match almost nothing — the likely shape is colloquial terms as matchers with the CISA name as the group label. Would also close the open education gap with a standard name.
- **Decide whether the exploitation multiplier reads the KEV catalogue.** `core/reflist.py` and the `reference_lists.kev` manifest entry fetch and cache CISA's Known Exploited Vulnerabilities catalogue (1,675 entries, refreshed daily, verified reachable). **Nothing in `core/rules.py` reads it** — the scoring change is P&D's. Run `tools/kev_impact.py` first: it reports where the word group and the catalogue AGREE, where the catalogue is right and the word group stayed silent (MISSED), and where the word group fired with nothing catalogued (OVERCLAIMED), then re-scores the MISSED set to show how many items would newly surface. Note the argument against a straight replacement: an article can describe real exploitation before CISA catalogues it, and there the wording is the only signal there is.
- Host monitoring — deferred.

### From `pnd.md` — Collection posture

Cast a wide net. Any credible cyber-threat reporting is in scope at the collection layer — **trusted sources are ingested wholesale and AOR relevance is decided at scoring**, never by keyword pre-filtering at collection. Filtering and prioritization happen downstream, against the tree below.

### From `pnd.md` — Terminology

- **KIQ** — Key Intelligence Question. Enduring, top-level. Governs collection scope.
- **PIR** — Priority Intelligence Requirement. What the brief exists to answer.
- **SIR** — Specific Intelligence Requirement. A narrower question that decomposes a PIR.
- **EEI** — Essential Element of Information. The specific collectable fact that answers an SIR.
- Each EEI carries `[Sensor: …]` (what collects it; **ACTIVE / PARTIAL / PENDING / ABSENT**) and `[Scoring: …]` (how it is weighted) and/or `[Standard: …]` (a production rule governing it).

---

### From `pnd.md` — KIQ-1: What cyber threats endanger California SLTT organizations and the critical infrastructure they operate or depend on?

##### PIR-1 — Direct impact to California organizations

*What incidents, breaches, or targeting have directly affected California-based organizations or entities?*

**SIR-1.1 — Which California SLTT / critical-infrastructure organizations reported a breach or incident this window?**

- **EEI-1.1.a** — Breach notifications affecting Californians (org, date, type, records). `[Sensor: CA AG breach-registry scraper — PENDING]` `[Scoring: Tier-1 CA-direct]`
  *Blocked by the `process_page` re-collection defect — the registry is a web portal, and page sources are currently collected once and never revisited.*
- **EEI-1.1.b** — Extortion/leak-site posts naming California victims. `[Sensor: ransomware leak-site aggregator, CA-filtered — PENDING]` `[Scoring: Tier-1 + ransomware/CI]`
- **EEI-1.1.c** — Regional/local press reports of incidents at CA local-gov / school / utility / tribal entities. `[Sensor: curated CA regional press — PENDING]` `[Scoring: Tier-1 CA-direct]`
  *StateScoop (loaded 2026-08-11) is SLTT trade press, not CA regional press. This EEI remains unserved.*
- **EEI-1.1.d** — Official CA advisories naming an affected CA entity. `[Sensor: Cal OES + CDT + MS-ISAC — **ACTIVE** as of 2026-08-11; Cal-CSIC — PENDING]` `[Scoring: Tier-1, primary source]`
  *Loaded and verified against host egress: `news.caloes.ca.gov/feed/`, `cdt.ca.gov/newsroom/feed/`, `cisecurity.org/feed/alert` + `/feed/advisories`. **Cal-CSIC advisories remain unserved** — confirmed publishing through August 2026, but PDF/DOCX on an HTML index with no RSS. Same `process_page` blocker as EEI-1.1.a.*

**SIR-1.2 — Is the affected organization inside the 34-county CCIC AOR?**

- **EEI-1.2.a** — Org county/location matched against the 34-county list. `[Sensor: derived at scoring — **ACTIVE**]` `[Scoring: AOR-county match — all 34 counties present in the `geo` group]`
  *Known precision gap: several county names are not California-exclusive. `kings county` is Brooklyn; `lake county` is Illinois, Florida, Indiana and Ohio; `trinity county` is also Texas; `sierra county` is also New Mexico. Any of these plus an incident term in proximity scores **Tier-1 AOR-direct**. The reasoning line makes it auditable, but the analyst must catch it. City coverage is also thin — five cities across a 34-county AOR.*
- **EEI-1.2.b** — In-AOR vs. near-AOR vs. out-of-AOR-but-CA classification. `[Scoring: annotation — e.g., Suisun/Solano = near-AOR]`

**SIR-1.3 — What is the verified operational impact, versus what is merely claimed?**

- **EEI-1.3.a** — Confirmed disruption (systems down, public-safety/911 impact, operational degradation), verified against a primary source. `[Standard: verify specific impact claims before publishing; soften or cut unverifiable specifics — anti-FUD]`
- **EEI-1.3.b** — Attribution status: confirmed / suspected / unknown; never state suspected as fact. `[Standard: attribution discipline]`

---

##### PIR-2 — SLTT sector targeting anywhere (leading indicator)

*What threat activity is targeting SLTT-relevant sectors anywhere, as a leading indicator for the AOR?*

**SIR-2.1 — Which SLTT sectors are being targeted this window (water/wastewater, K-12/higher-ed, local gov, tribal/territorial)?**

- **EEI-2.1.a** — Reported attacks/targeting of a named SLTT sector, any geography. `[Sensor: national trusted feeds — ACTIVE; StateScoop — **ACTIVE** 2026-08-11; K-12 Dive, WaterISAC — PENDING; GovTech — **REJECTED**]` `[Scoring: Tier-2 sector]`
  *GovTech advertises no working feed — both candidate paths returned 0 entries and HTTP 404 on 2026-08-11. Do not retry without new evidence.*
- **EEI-2.1.b** — Sector ISAC/agency advisories (WaterISAC, MS-ISAC, CISA sector alerts). `[Sensor: MS-ISAC + CISA — **ACTIVE** (4 feeds); WaterISAC — PENDING]` `[Scoring: Tier-2, primary source]`

**SIR-2.2 — Does the targeted sector/technology generalize to the AOR?**

- **EEI-2.2.a** — Whether the targeted tech/config is common in AOR SLTT orgs (e.g., internet-exposed PLCs in small water systems). `[Scoring: low-maturity SLTT tech multiplier]`
  *This is the leading-indicator logic — out-of-state targeting matters because the same exposure exists here.*

**SIR-2.3 — Is this an isolated incident or a widening campaign?**

- **EEI-2.3.a** — Multiple incidents sharing TTPs/sector across geographies. `[Analytic: convergence — supports "widening campaign" framing, e.g., the multistate water attacks]`

---

##### PIR-3 — Actively-exploited vulnerabilities in SLTT-common technology

*What in-the-wild / KEV vulnerabilities affect technology common in low-maturity SLTT environments?*

**SIR-3.1 — What is actively exploited in the wild this window?**

- **EEI-3.1.a** — CISA KEV additions (CVE, date, exploitation status, ransomware-use flag). `[Sensor: **ABSENT** — verified 2026-08-11]` `[Scoring: KEV multiplier]`
  *There is no dedicated KEV sensor. The block carries `cisa.gov/cybersecurity-advisories/all.xml` and `us-cert.cisa.gov/ncas/current-activity.xml`; neither is the KEV catalog. KEV additions reach the corpus only when an advisory or aggregator mentions them — precisely the single-aggregator dependence the ICD 203 review flagged. Cheap to close.*
- **EEI-3.1.b** — Vendor PSIRT advisories confirming in-the-wild exploitation. `[Sensor: vendor PSIRTs — **ACTIVE** (MSRC, Cisco, Palo Alto, Fortinet)]` `[Scoring: KEV/exploitation]`
  *Caveat: MSRC alone produced 52.7% of lifetime corpus volume. Coverage is not the problem here; proportion is. Pending P&D decision.*

**SIR-3.2 — Does the affected technology exist in low-maturity SLTT environments?**

- **EEI-3.2.a** — Whether the product is commonly deployed by SLTT orgs (edge appliances, on-prem SharePoint, RMM, routers). `[Scoring: low-maturity SLTT tech multiplier]`
- **EEI-3.2.b** — Provider/product-specificity: which providers/versions are affected, and does the audience use them? `[Standard: provider-dependent relevance — a webmail/product item is relevant only if it hits providers the audience runs (e.g., Google Workspace, Microsoft 365); MSP-only software is low-relevance if few distro orgs use MSPs]`

**SIR-3.3 — What is the remediation posture?**

- **EEI-3.3.a** — Patch availability + KEV remediation deadline. `[Standard: actionability — frame as vendor-accountability ask ("confirm your vendor/IT provider patched X")]`

---

##### PIR-4 — Broad/national threats with SLTT relevance

*What national-scale threats carry material relevance to SLTT defenders?*

**SIR-4.1 — What national-scale threats materially affect SLTT defenders?**

- **EEI-4.1.a** — National advisories/campaigns with an SLTT nexus. `[Sensor: national feeds — **ACTIVE**]` `[Scoring: Tier-4]`
- **EEI-4.1.b** — Audience-portfolio relevance filter: does it reach the SLTT audience, or is it developer-only / defense-industrial-only / vendor-opinion? `[Standard: audience filter — developer-targeted (e.g., npm poisoning) and defense-industrial-base (e.g., CMMC) items are out-of-portfolio unless they reach SLTT through a vendor]`

---

### From `pnd.md` — Byproduct 1 — Sensor-build roadmap (prioritized)

Each pending sensor is the essential means of collecting one or more EEIs. Priority = how much AOR-specificity it unlocks.

0. **Fix `process_page` re-collection** (`core/acolyte.py:114`) — **prerequisite, not a sensor.** Page-type sources are deduped on URL hash, so a portal is captured once and never revisited. Both of the next two items are portals and are useless until this lands.
1. **CA AG breach-registry scraper** — serves EEI-1.1.a. The single highest-value build: the only authoritative, AOR-direct breach sensor. PIR-1 has almost no active collection without it.
2. **Cal-CSIC advisories** — serves EEI-1.1.d. Confirmed alive and publishing through Aug 2026. Extracting the index page may yield enough, since titles and dates are what the scorer consumes — prove that before building PDF parsing.
3. **Ransomware leak-site aggregator, CA-filtered** — serves EEI-1.1.b. Early-warning AOR-direct (victims appear before local press).
4. **CISA KEV as a primary feed** — serves EEI-3.1.a. Currently absent; reduces single-aggregator dependence. Cheapest item on this list.
5. **Curated CA regional press** — serves EEI-1.1.c. Still unserved; StateScoop does not cover it.
6. **Remaining sector trade press** (K-12 Dive, WaterISAC) — serves EEI-2.1.a/b.

~~Curated official CA feeds (Cal OES, CDT, MS-ISAC)~~ — **DONE 2026-08-11.**

### From `pnd.md` — Byproduct 2 — Coverage-gap finding

Decomposition makes the gap explicit: **three of four EEIs under SIR-1.1 — the AOR-direct core of PIR-1 — remain PENDING.** (EEI-1.1.d was closed 2026-08-11.) The pipeline answers PIR-1 largely by luck: when a statewide query or national outlet happens to name a California entity.

Therefore the CTI domain is presently **California-statewide-and-national collection with AOR-aware scoring, not AOR-specific collection.** Closing this gap is a collection problem (build the SIR-1.1 sensors), not a scoring problem — scoring is ready and has been.

### From `pnd.md` — Byproduct 3 — Production standards captured (from analyst-gate feedback)

The decomposition absorbs cyber-team lessons as EEI-level standards, so they persist as doctrine rather than one-off edits:

- **Anti-FUD verification** (EEI-1.3.a): verify specific impact claims (e.g., a 911 outage) against a primary source; soften or cut what can't be confirmed.
- **Attribution discipline** (EEI-1.3.b): suspected ≠ confirmed; never state suspected attribution as fact.
- **Provider-dependent relevance** (EEI-3.2.b): product-specific items are relevant only if the audience uses the affected product/provider.
- **Audience-portfolio filter** (EEI-4.1.b): topicality ≠ relevance; developer-only and defense-industrial-only items are out of portfolio.

### From `pnd.md` — 1.3 Runtime and storage

Where the corpus lives and how collection is tuned. `base_dir` is the one
host-coupled value; override it per host with the `SANCTUM_BASE` env var (wins
over this) so the repo itself stays portable. To move Sanctum to another server:
set `SANCTUM_BASE` (or edit `base_dir`), point `rclone_remote` at your storage,
`pip install -r requirements.txt`, and run.


**`reference_lists` — declared, fetched, and NOT yet used for scoring.** The
`kev` entry points at CISA's Known Exploited Vulnerabilities catalogue: 1,675
entries, refreshed daily, verified reachable from the collector host on
2026-08-25. The scoring model currently earns its 1.5x exploitation multiplier
by matching phrases in prose, which has already been measured wrong — a real
CISA advisory said *"Active Threat"* rather than *"actively exploited"* and the
item fell from 7.8 to 1.5. The catalogue answers that question authoritatively.

Nothing in `core/rules.py` reads this list. **Whether the multiplier fires on
catalogue membership instead of, or alongside, the `kev` word group is a
Planning & Direction decision**, and `tools/kev_impact.py` measures what the
change would do to the real corpus so the decision is made against a number.

**`max_publish_age_days` — reports from outside the cycle window do not enter
the corpus.** Standing direction, 2026-08-25. Enforced at collection, before
any HTTP request is made, so a back catalogue costs nothing and never reaches
the archive. The audit that prompted it found 58 of 96 Google News items and
512 of 680 Huntress items published before 2026 — one of them a February 2023
article that force-surfaced at the top of the candidate queue.

Two deliberate exceptions. An entry whose publication date cannot be parsed is
**kept**, because dropping on a date we failed to read would silently delete a
whole feed the first time a publisher changed its format. And rejected items
are **not** written to `seen.txt`: re-testing a date each run costs no requests,
whereas marking them seen would make this policy irreversible.

**`fetch` — how a body is retrieved, and how failure is recognised.** The
collector previously stored whatever came back, which was frequently not an
article: a Cloudflare interlude, a JavaScript shell, or a raw `<a href=...>`
tag from a feed summary. Those are now detected and discarded, and each item
records *why* its body is missing. See `core/fetch.py` for the strategy order.
`impersonate` and `decode_google_news` need optional packages from
`requirements.txt`; without them those strategies are skipped and collection
still runs.

**`user_agent` is empty on purpose, and that is a measured result rather than
an oversight.** Benchmarked against all 56 sensors on 2026-08-25, sending a
browser string was a net loss: `news.sophos.com` went from 2902 words to
blocked — and tarpitted, 120 seconds per attempt instead of 0.4 — and
`cybersecuritynews.com` from 777 words to an instant refusal. Every sensor the
string helped was recovered anyway by the TLS-impersonation retry, which is a
browser at the handshake as well as in the header.

---

---

### From `pnd.md` — Stage 2 — Collection

*Where to look, how hard, and how far back.*

### From `pnd.md` — 2.1 Collection settings

The window, the recency gate, and how each fetch behaves. Split out of the
manifest block above only so it sits with the sensors it governs — the loader
merges every `yaml` block in this file into one config, so `manifest:` appearing
twice is not a duplicate, it is one map assembled in two places.

### From `pnd.md` — 2.2 Sensors

The feeds the collector reads. One URL per line inside the fenced `sensors` block;
blank lines and `#` comments are ignored. **This block is the single source of the
feed list** — edit feeds here. Add a feed only if it is reliable AND additive; verify
it against the host's egress first; drop noisy sources. Do not reintroduce the dropped
34 county Google-News keyword feeds.

Dropped 2026-08-25 — `api.msrc.microsoft.com/update-guide/rss`. **Do not reintroduce
without new evidence.** Two reasons, both measured over 21 cycles.

**First, read this correction, because the obvious argument for dropping it is wrong.**
The often-quoted figure — MSRC is roughly half the corpus — is a **backfill artifact and
was already investigated and dismissed on 2026-08-17.** 3,482 articles arrived on
2026-08-05 from the sensor's first poll and 744 on 2026-08-12, the day after Patch
Tuesday; every other day is 0–36. Ongoing volume is about six items a day. **Volume is
not why this feed was dropped**, and the lifetime totals in `tools/sensor_health.py`
still carry those two bursts. Anyone re-examining this should start here rather than
rediscover the contradiction and reopen a settled decision.

The two reasons that hold:
- **Nothing usable comes out.** Every item links to
  `msrc.microsoft.com/update-guide/vulnerability/CVE-…`, a JavaScript single-page
  application with no server-rendered text. The collector was storing the string
  *"You need to enable JavaScript to run this app"* as the article body. Benchmarked
  2026-08-25 across every fetch strategy — plain, browser user agent, TLS impersonation
  — and **none recovers it**; short of running a headless browser there is nothing there.
- **Zero unique contribution.** Sole source of **no** distinct surfaced event across 21
  runs, and a contributor to three. Measured by `tools/sensor_health.py`, which did not
  exist when this decision was first raised — **this is the evidence that settled it**,
  and the shape of the feed is why: one item per CVE, carrying no severity, no
  exploitation status and no judgement about which of a hundred-plus Patch Tuesday
  entries matter. When a Microsoft flaw genuinely matters,
  BleepingComputer, The Hacker News, Talos and Rapid7 all cover it with context and all
  four are already carried here.

The reasons this feed *sounds* essential — Microsoft patches, SLTT estates run Windows —
are exactly why it needs a written record. **Coverage of Microsoft is not lost.**
`microsoft.com/en-us/security/blog/feed/` (Microsoft Threat Intelligence) is a separate
sensor and stays; `lowmat_tech` already carries `sharepoint` and `exchange server`, so a
Microsoft flaw the news covers still elevates. The residual gap — a critical Microsoft
vulnerability nobody writes up and that KEV has not yet listed — occurred **zero times in
21 runs**. If that gap ever needs closing, the answer is Microsoft's CVRF API
(`api.msrc.microsoft.com/cvrf/v3.0/`, verified reachable 2026-08-25) used as a **lookup**,
one document per month — not a feed that emits the flood more cleanly.

Also dropped 2026-08-11, verified against 9 cycles of `collector.log` — do not reintroduce
without new evidence:

- `thecyberwire.com/feeds/rss.xml` — 0 new in 9 runs, and **0 lifetime**. Returns no parseable
  feed entries, so Acolyte falls through to `process_page`, which then extracts no text either.
  Logs `WARNING no text` on every single cycle from 2026-08-05 onward. This path is retired.
  **Corrected 2026-08-23:** a live feed does exist at `feeds.megaphone.fm/cyberwire-daily-podcast`,
  publishing daily with substantive descriptions. It was refused for a different and better
  reason: every item is a multi-story daily roundup. One item would fire `kev`, `incident`,
  `ransom` and `supplychain` at once and ride the multiplier stack to a high score every day,
  with no single event to place in a section and no per-story URL to cite. Its selected-reading
  list is also drawn from outlets already collected here. Do not reintroduce on the grounds
  that "a feed exists now" — the shape is the objection.
- Google-News query `("CISA Region 9" OR "CISA California")` — 0 new in 9 runs, 0 lifetime, and
  the identical `no text` failure every cycle. The query matches nothing, so Google returns an
  empty feed, which falls to the page path and yields nothing extractable. Too narrow.

Considered and declined 2026-08-26 — `malwarebytes.com/blog/feed/index.xml`. **Measured
before adding rather than after.** Write this one down carefully, because the feed is sound:
it passes every mechanical test and fails the only test that matters.

- **Mechanically it is one of the better feeds available.** HTTP 200 from the collector host,
  20 parseable entries, newest 0.1 days old, bodies extracting at 445 to 2,560 words on plain
  trafilatura — no browser user agent, no TLS impersonation, no strategy required. Single-topic
  posts with dated, citable per-story URLs, so it passes the shape test that refused CyberWire.
  Roughly six items a day and no back-catalogue burst beyond the first poll. One item in twenty
  is a weekly roundup carrying 45 words, which is the CyberWire objection in miniature.
- **Every one of its 20 items scored between 1.00 and 1.50 against a 2.00 threshold. Zero would
  surface.** All twenty landed in tier 4, *broad/national with SLTT relevance* — the floor. Only
  two multipliers fired across the entire feed: one low-maturity SLTT technology and one
  supply-chain. Measured by loading the live CTI scoring model and scoring the real feed
  contents, before the sensor was added to anything.
- **The reason is audience, not quality.** Malwarebytes Labs writes for individuals — phishing
  lures, consumer scams, mobile banking trojans, personal privacy. The model floors anything
  with no AOR hook, correctly, because this is a California SLTT brief. Items that look in scope
  by their titles do not survive it: a healthcare breach exposing medical records and Social
  Security numbers scored 1.00 because it is national with no California link, and 2,560 words
  of loader threat research scored the same.
- **The one thing that would change this answer** is the open Planning & Direction question on
  whether AI-assistant security is in scope. Three of the twenty items are in that class. If
  that decision comes back yes, this feed is worth **re-measuring — not re-arguing.** Do not
  reintroduce on the grounds that the feed is good. It is good. Against this mandate it is
  also empty.

Wanted but not collectable — checked 2026-08-23, do not re-search without new evidence:

- **Dragos** (`dragos.com`) publishes no RSS feed. Ten conventional paths tested from the
  collector host — `/blog/feed/`, `/feed/`, `/blog/rss.xml`, `/blog/index.xml`, `/rss.xml`,
  `/blog/atom.xml`, `/index.xml`, `/blog/rss/`, `dragos.com/feed`, `/resources/feed/` — all
  404 or redirect to nothing. This is the one vendor whose telemetry covers the water,
  wastewater and utility sectors named in the `sector` group, and its OT threat landscape
  reporting is the reference work in that space, so the loss is real and worth recording.
  **It is blocked on the same engine gap as Cal-CSIC:** `process_page` never revisits a page
  source, so page-type collection is a one-shot. That fix now has a second use case forcing
  it, which is the bar this repo sets for building something.

Note: a source that returns neither feed entries nor extractable text is **retried in full every
cycle** — `process_page` returns before recording the URL in `seen.txt`, so there is no
suppression. Both of the above burned a fetch per cycle for nine cycles.


Added 2026-08-19, verified from the collector host before loading (9 items, HTTP 200
on `industrialcyber.co/feed/`; the `/rss/` path 307s to nothing and `/feed/rss/` 301s to
the same content):

- `industrialcyber.co/feed/` — industrial and operational-technology trade press. Serves
  PIR-2 sector targeting, where coverage was thin: before this the only ICS/OT-relevant
  sensors were the SANS Internet Storm Center feed and one California water-and-utility
  news query. **Watch for two things** — whether it is additive or mostly re-reports what
  The Record and Hacker News already carry, and whether its vendor-heavy items clear the
  audience-portfolio filter. Re-assess after three cycles.


---

### From `pnd.md` — Stage 3a — Processing

*Deterministic. No model, no judgement, no tokens. Produces the staging document.*

### From `pnd.md` — 3a.1 Scoring model

The multiplicative model, verbatim from the CTI doctrine: a base **tier weight**
(highest qualifying tier only; tiers don't stack) times the product of any
**elevation multipliers** (absent = neutral). Tier 1 requires California to be the
**subject of an incident** — either California in the title *and* an incident word
present, or a California term within ~120 chars of an incident word in the body —
not a passing mention. Groups are keyword lists; short/ambiguous ones match on
word boundaries.

**Score = (tier weight) × (product of elevation multipliers)**

### From `pnd.md` — Why the model is shaped this way

*Moved here from `codex.md` Layers 3–4 on 2026-08-17, when that file was retired.
The rationale now sits beside the values it explains, so tuning a number and
leaving the reasoning stale is no longer possible.*

**Convergence wins, and the tier spacing is chosen to allow it.** 8/4/2/1 is
deliberately narrow enough that a heavily-elevated lower-tier item **can**
outrank a bare higher-tier one. That is intended: a multi-signal active campaign
against an out-of-state school is allowed to lead over a quiet in-AOR breach
carrying no urgency signals. Convergence across requirements is a stronger
priority signal than geography alone.

Worked, using the values below:

| Item | Calculation | Score |
|---|---|---|
| CA water utility breach, no elevation signals | 8.0 × 1 | **8.0** |
| Out-of-state school ransomware on common tech (KEV + low-maturity + ransomware) | 4.0 × 1.5 × 1.5 × 1.3 | **11.7** — *outranks the bare CA item, by design* |
| National KEV vuln in SLTT-common tech (KEV + low-maturity) | 2.0 × 1.5 × 1.5 | **4.5** |
| Broad supply-chain story | 1.0 × 1.3 | **1.3** |

**Tiers are not additive with each other.** An item takes its single highest
qualifying tier weight — something both AOR-direct and sector-targeting is tier 1,
not 8+4. Only the elevation multipliers stack.

**An absent multiplier is neutral (×1.0), never suppressive.** A maximally
relevant item with no urgency signals must never be scored toward zero.

**Round up on uncertainty.** If an item's tier or a multiplier is ambiguous,
score it as though the higher interpretation were true. Ambiguity resolves
toward visibility, not away from it — same asymmetry as the surfacing rules:
a false positive costs a few seconds of skimming, a false negative means a real
threat never reaches the analyst.

**Why there is no score handicap.** Discounting automated scores by a flat factor
assumes the bias runs consistently in one direction. It does not — scoring errors
are inconsistent, sometimes high and sometimes low, so a handicap gives false
comfort while catching none of the real errors. Transparency is the chosen
safeguard instead: visible reasoning on every surfaced item, plus a full drop
list. That catches what a correction factor would miss.

**The drop list is mandatory and is what makes a generous cut safe.** Everything
below the threshold is still listed by title. *Dropped* never means *invisible* —
the analyst eyeballs the discards in seconds and rescues anything mis-scored.

**`serves_eei` declares only what a SCORING RULE can honestly attest.** An
essential element whose evidence comes from a named external sensor — a breach
registry, a leak-site aggregator, a vendor advisory feed — is **sensor-bound**,
and no scoring rule may claim it. Measured 2026-08-31 against the 19 elements in
§1.2, the requirements tree: **3 are scoring-derived and claimable, 9 are sensor-bound
(three of those sensors PENDING and one ABSENT), 6 are analyst standards** the
engine cannot attest at all. That distribution IS the coverage gap Byproduct 2
of §1.2, the requirements tree, describes in prose — the pipeline answers PIR-1 largely by
luck — now countable instead of asserted.

**A sensor cannot yet declare the elements it serves**, because the sensor block
is a flat list of URLs with no place to hang metadata. Until it can, the
sensor-bound elements stay unclaimed rather than falsely claimed.

**The SIR and the PIR are never declared.** `EEI-1.2.a` sits under `SIR-1.2`
under `PIR-1` by its own numbering. Deriving them costs nothing; storing them
would put one fact in two files.

**Each tier declares the intelligence requirement it answers.** The four tiers
and the four priority requirements in §1.2, the requirements tree, are the same four things
and always were — the tier `name` paraphrased the requirement instead of naming
it, so an item's requirement was computed at every scoring pass and never
written down anywhere a reader could see. `serves:` is that name. It changes no
score; it is read only when the staging document says which requirement a
candidate answered.

**`serves:` carries the identifier only, never the requirement's statement.**
§1.2, the requirements tree, is the single source of truth for what PIR-1 *says*. Copying
the sentence here would put the same fact in two files, which is the drift the
two-file split exists to prevent.

**PIR-4 is the floor, not a subject.** Tier 4 is `require: always` — everything
that qualified for nothing else. It has no vocabulary of its own and should not
be given any.

### From `pnd.md` — Open finding 1 — the `incident` group covers one third of the problem

**Severity: high. Unresolved. P&D decision.**

The 13 terms in `incident` are all *confidentiality* language — things stolen,
leaked, breached, ransomed. The group has effectively no coverage of
**availability** (service knocked offline, denial of service, outage) or
**integrity** (defacement, data tampering, wiped systems).

Checked against MITRE ATT&CK's Impact tactic (TA0040, 15 techniques), which
describes what happens to a victim: **none of the 15 concepts have a matching
term in the group.** Absent: defacement, denial of service, disk wipe, data
destruction, service stop, firmware corruption, inhibit system recovery, data
manipulation, resource hijacking, financial theft, account access removal,
system shutdown, email bombing.

**Why this matters more than it looks.** The `incident` group is one half of
force-surface rules M1 and M3 (`pnd.md` → `scoring.force_surface`). A DDoS that
takes a county's 911 dispatch offline does not match `incident`, so **M1 does not
fire and the item lands in the drop list** — the exact scenario Vox Policy §7
names as the highest-priority verification case. The policy calls M1 "the hard
guarantee that every AOR incident surfaces." That guarantee is bounded by this
word list, not by the rule.

Found by probe: an article headlined *"Small California town website defaced"*
scored 1.0 and dropped. `geo` matched; `incident` did not.

**Recommended approach:** use the ATT&CK Impact list as a *checklist of concepts*
only. Its labels are analyst taxonomy ("Inhibit System Recovery"), not the words
reporters write ("couldn't restore from backups"). Target roughly 25 curated
prose terms, not a bulk import — see the caution under Open finding 3.

---

### From `pnd.md` — Open finding 2 — `" calif "` does not do what it looks like

**Severity: medium. Accepted for now, recorded below.**

The term is written with leading and trailing spaces, which reads as an attempt
at word-boundary matching. `core/rules.py` calls `.strip()` on every term before
matching, so the padding is discarded and the term becomes the bare 5-character
substring `calif`. At 5 characters it is above the auto-boundary length, so it
falls back to substring matching — the precise behaviour the spaces were meant
to prevent.

Verified: `" calif "` matches *"califon new jersey"*.

`california` and `californian` are already in the group, so the marginal value of
`calif` is the abbreviated *"Calif."* form in wire copy. Two clean fixes exist —
add `calif` to `word_boundary_terms`, or replace it with `calif.` — and either
changes matching, so neither is made here.

`"csu "` and `"uc "` are padded the same way but are harmless: both are under the
auto-boundary length once stripped, so they get whole-word matching regardless.

---

### From `pnd.md` — Open finding 3 — `geo` carries known collisions and now sits in the highest-cost position

**Severity: medium-high. Unresolved. P&D decision.**

§1.2, the requirements tree, (EEI-1.2.a) already documents that several of the 34
county names are not California-exclusive:

| Term | Also | 
|---|---|
| `kings county` | Brooklyn, New York |
| `lake county` | Illinois, Florida, Indiana, Ohio |
| `trinity county` | Texas |
| `sierra county` | New Mexico |

**What changed on 2026-08-17.** `geo` was wired into force-surface rule M1. Per
`../docs/VOCABULARY.md` §2, force-surface is the highest-cost position in Sanctum —
the only one where the score cannot correct a bad match, because overriding the
score is the rule's entire purpose. Every collision in `geo` is now inherited by
M1, and an out-of-state Lake County ransomware story will be force-surfaced.

Under the triage rule (§1), exact synonyms **do** exist here — `kings county,
california`, or pairing the county term with a state term via a `proximity` or
`all` atom. So §1 says these should be tightened. Doing so changes matching and
weakens M1's coverage in exchange for precision, which is a Planning & Direction
trade, not a maintenance edit.

**Also noted:** city coverage is thin — five cities across a 34-county AOR.

---

### From `pnd.md` — How a keyword gets attributed to a requirement

*Added 2026-08-26.*

**A keyword's intelligence requirement is decided by which group it lands in.**
Nothing else attributes it. The tier rules that consume a group are the
requirements, so putting a term in `geo` makes it PIR-1 vocabulary and putting it
in `sector` makes it PIR-2 vocabulary, whether or not anyone intended that.

That was true before this section existed and it was written down nowhere. The
mapping could only be recovered by walking every rule tree by hand across two
files, and on 2026-08-26 a session doing exactly that got it wrong twice in one
sitting. **A fact that must be derived is a fact that will eventually be derived
wrongly.** So each group now declares its attribution in the block below, and
`tools/vocab_check.py` warns when one does not.

**The question to ask of a new keyword:** does this word tell me *which*
requirement is in play, or does it make an already-relevant item more urgent?

- **First case — it belongs in a requirement-defining group** and that group
  names the requirement. `geo` and `incident` serve PIR-1. `sector` and
  `incident_broad` serve PIR-2. `exploit_strong` and `lowmat_tech` serve PIR-3.
- **Second case — it is an elevation term and has no single requirement.**
  `ci`, `ransom`, `supplychain`, `cve` and `cisa_source` change how an item
  ranks, never which question it answers. Attributing one of these to a
  requirement is a category error, not a judgement call.

**Three groups sit outside both.** `listicle` is an exclusion — it exists only to
be negated. `ttp` shapes the product rather than the score, suggesting a vox
section. `kev` and `targeting` are consumed by no rule at all, both on purpose
and both with the reason recorded below.

**Why the declaration sits on the group and not in the requirements tree.** It is
reasoning about a group, and it belongs beside the group it describes. Writing it
as prose up in §1.2 would have created a second copy that nobody opens while
editing a word list, which is how `kev` and `targeting` came to be invisible in
the first place. Until 2026-09-01 this reasoning lived in a separate §3a.2, the vocabulary section,
for the same purpose; the file boundary is gone, the separation of *terms* from
*reasoning about terms* is not.

**The judgement is not automatable and is not meant to be.** Deciding whether
`outage` serves PIR-1 or PIR-2 is intelligence judgement. What the guard enforces
is only that the judgement was made and recorded — never what it should be.

---

### From `pnd.md` — Group review status

---

### From `pnd.md` — Stage 3b — Exploitation

*A person and a model, working the staging document into the vox.*

### From `pnd.md` — 3b.1 Production

Shapes the staging output and the human synthesis stage: the pre-filter report
title, the section taxonomy the analyst arranges items into, and the item-count
targets.

**No target on the review surface** (Vox Policy §7). The staging document and the
vox are review surfaces, and the number of items in them is an **output** of the
scoring and the force-surface rules — never a target set on top. This table
previously read *"~5–6 per content section, ~15–18 total"*; that was a cap, the
policy forbids caps, and it is gone:

| Artifact | When | Size |
|---|---|---|
| **Staging document** (3a) | Wednesday, complete by 0500 | **Uncapped.** Everything clearing `surface_min_score` or matching a `force_surface` rule |
| **Vox** (3b) | Wednesday 0600 | **Uncapped.** The operator cuts on judgement, not to a number |
| **Distributed report** | Thursday | 5–8 items — "restraint is the product" applies here, and this is **outside Sanctum's scope** |

If the surface is too large, tune the weights, the vocabulary, or the exclusion
operators. Do not reintroduce a cap: a cap hides what the scoring did and
destroys the feedback that tunes it. **The uncapped surface is the diagnostic.**

A wider surface pulls in **lower-ranked items from the same sorted
queue** — lower tier and/or fewer elevation signals. It does not lower the
standard. Every entry still
shows its scoring reasoning (tier + which multipliers fired) so the analyst can
audit where the cut falls.

*`arbites.py` reads only `report_title` from this block. What the surface actually
contains is decided by `scoring.settings.surface_min_score` and the `force_surface`
rules — a threshold plus guaranteed inclusions, never a count.*

### From `pnd.md` — 3b.2 Vox policy

---

### From `pnd.md` — 1. What the Vox is (and is not)

- **Is:** a weekly review surface of collected, prioritized open-source cyber threat items for a low-maturity SLTT audience, handed to the cyber team for review and amendment.
- **Is not:** a finished intelligence product. No analytic assessment, no confidence judgments, no handling markings. The cyber team adds assessment and produces the distributed report.
- **Audience:** non-technical SLTT leaders and staff (county/city government, school districts, small utilities). Everything below serves that reader.

### From `pnd.md` — 2. Cadence & dates

- Collection cutoff / **ICOD** (information current as of): Wednesday 0400 Pacific. The staging document is complete by 0500.
- Produced: Wednesday 0600. Team review: Thursday morning. Distribution: Thursday afternoon.
- **Title date = distribution date (Thursday).** ICOD appears in the header. LTIOV is planning doctrine only — never on the product.

### From `pnd.md` — 3. Naming

- Reader-facing heading: **"WCTI — Weekly Cyber Threat Intelligence."** The word "vox" is internal shorthand only and never appears in the reader-facing document.
- Filename of the PRODUCT: `WCTI_v[YYYYMMDD]` — date is the distribution (Thursday) date.
- Filename of the STAGING DOCUMENT: `WCTI_[YYYYMMDD]_STAGING` — date is the date it was
  **created**, not the distribution date. The two documents are dated on different
  principles because they answer different questions. The product's date tells the reader
  when it reached them. The staging document's date tells the analyst when this queue was
  built — so regenerating a cycle after a scoring change produces a second, distinctly
  named file rather than silently overwriting the first. **The intelligence cycle week is
  tracked by the analyst, not encoded in the artifact name.** The compliance report takes
  the same date as the staging document it reports on.
- No "CCIC" prefix until AOR-direct sensors exist and the product can genuinely focus on a single AOR.

### From `pnd.md` — 4. Header (reader-facing only — no internal plumbing)

The header carries ONLY:
1. Heading: `WCTI — Weekly Cyber Threat Intelligence`
2. Filename + distribution date + ICOD.
3. A one-paragraph summary of what the document is and how it was derived.
4. A short note on the scores.

**Excluded from the header:** internal pipeline artifact paths (e.g., staging-document filenames), internal stage labels, and any Sanctum-internal jargon. A reader who never touches Sanctum should not see machinery.

### From `pnd.md` — 5. Structure

Fixed sections, in order, each ordered internally by priority:
- **NEWS** — incidents, breaches, advisories, announcements.
- **CTA TTPs** — cyber threat actor tactics/techniques (tradecraft).
- **LATEST ATTACKS OR RISKS** — vulnerabilities and active exploitation.
- **KEYWORDS** — wave-top only (vendor/sector names acceptable; not specific products/malware/techniques).

### From `pnd.md` — 6. Per-entry format

Each entry has, in order:
1. **ID + headline** (`YYYYMMDD-[A]` sequential).
2. **Body**, written from the article body — never the headline. If the corpus has no usable body on a topic, the item is dropped.
3. **"Why an SLTT organization should care"** clause — mandatory, tied to this audience, framed as vendor accountability / procurement and foundational controls (CIS IG1), not developer-level fixes.
4. **Score** — the pipeline relevance score plus tier and the multipliers behind it. The score orders; it does not measure.
5. **Citations** — nested per entry, as live openable links (outlet, headline, date, URL). Never a link the reader cannot open.
6. **Flags** where needed (verification, review-note, attribution).

### From `pnd.md` — 7. Content standards (locked)

- **The review surface is worked, not sampled.** Every candidate the staging
  document suggests for a section is read. A section written with far fewer
  entries than were suggested — 28 suggested, one written — is **a failure to
  work the section, not a thin week.** A legitimately thin section is stated
  plainly with the counts: *"28 suggested, 3 qualified, 25 off-target."* Never a
  silent one-item section, and never padded with weak items to fill space. The
  suggested counts are in the compliance report; the reading is the analyst's.
  **This is R14 of `../docs/EXPLOITATION.md`, binding here.**
- **Requirements are consumed, never authored.** The staging document names the
  requirement each candidate answers and the elements it satisfied. The vox
  copies them; it does not derive them from the tier, the score, or memory.
  **This is R13 of `../docs/EXPLOITATION.md`, binding here.**
- **Body, not headline.** Read the source. No body, no entry.
- **One event, one entry.** Fold same-event reports; place each event once, in the section matching its dominant value.
- **Recency.** Filter on publication date within the collection window. Out-of-window items are flagged, not silently dropped; they stay only with a fresh this-week hook (new exploitation, new victim, new KEV).
- **Serious-impact verification.** Independently verify serious impact claims (911/public-safety outages, casualties, service disruption, breach scope, attribution) against a primary or authoritative source before inclusion. If not clearly substantiated, attribute ("per the city's statement…") or soften — never state as fact. Verify the wording does not inflate the source ("affected 911 routing" ≠ "911 went down"). Re-check status if the item has aged since first drafted; "not confirmed" can go stale.
- **Attribution discipline.** Suspected ≠ confirmed. Represent the actual state of evidence — neither assert nor flatly deny where reporting indicates but officials have not confirmed.
- **Provider/product relevance.** A product-specific item is relevant only if the audience uses the affected product/provider.
- **Audience-portfolio filter.** Developer-only (e.g., package poisoning) and defense-industrial-only (e.g., CMMC) items are out of portfolio unless they reach SLTT through a vendor. Topicality ≠ relevance.
- **Plain language.** Acronyms spelled out on first use; technical mechanisms named but translated.
- **No cap on the review surface — trust the weights.** The review surface has NO fixed limit on items per section or overall. Every item that qualifies — by score or by the mandatory-surface rule below — appears, however many that is. If 20 high-weight items qualify, 20 surface. The count is an OUTPUT of the scoring and rules, never a target imposed on top of them.
- **Fix volume by tuning Sanctum, not by capping.** If the review surface is too large or too noisy, that is the signal to adjust the weights, the mandatory-surface vocabulary, or the exclusion operators — never to silently cap the output. Capping hides what the scoring did and destroys the feedback that tunes it. The uncapped surface IS the diagnostic.
- **Mandatory-surface rule (inclusion, not ranking).** An item is force-surfaced — never left in the drop list regardless of score — if it meets ANY of: **(M1)** a California/in-AOR entity is the SUBJECT of a cyberattack, breach, or disruption — the hard guarantee that every AOR incident surfaces; **(M2)** in-the-wild exploitation, a weaponized public PoC, or a KEV addition AND the affected product is in the SLTT-relevant technology vocabulary; **(M3)** a specific incident confirms an SLTT sector (water, K-12, local/tribal government, public safety) was targeted or impacted. M2 does NOT fire on CVSS/severity alone — an exploitation signal is required, which keeps it high-signal. Subject-of-incident logic and the recency gate apply, so passing national name-drops and years-old items do not trigger it. This decides surface-vs-drop only; the score still ORDERS everything, so convergence-wins ranking is fully intact.
- **SLTT-relevant technology vocabulary.** M2 keys on a maintained priority lexicon of software/tech that SLTT organizations run (e.g., GeoServer, WordPress, on-prem SharePoint, webmail platforms, RMM tools, common firewalls/VPNs, edge routers). This is the CTI analog of a domain word list — per-domain config, refined with the exclusion operator to trim noise, and grown as the discard log reveals gaps.
- **Interim (until the pipeline implements M1–M3):** the analyst applies the mandatory-surface rule by hand — reviewing the drop list for M1–M3 items and rescuing them, marking the low score so the ranking/relevance disagreement stays visible.
- **Restraint lives in the distributed product, applied by the team.** Restraint is the finished report's virtue, not the review surface's: after review, the cyber team narrows to a focused set for the non-technical audience. That editorial cut is a human judgment on the output, never an automated cap on what surfaces for review.
- **Sourcing.** Primary-source elevation; verify aggregator/roundup items against the primary advisory. Flag vendor-stat methodology limits.

### From `pnd.md` — 8. Change control

This policy is the authority for the Vox. Format or standard changes originate as a P&D decision, are recorded in the Mandate/lessons log, and only then take effect. Mid-production requests that conflict with this spec are flagged against it, not silently adopted. This is the mechanism that prevents creep.
