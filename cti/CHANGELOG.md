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
