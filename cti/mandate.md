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
| **Monday 0900** | **Collection cutoff = ICOD** ("information current as of"). Corpus windowed on the 7 days ending here. |
| **Monday** (after 0900) | **Staging draft (Vox) produced** from the closed corpus. |
| **Monday–Tuesday** | **Individual review / amend** — analyst verification and edits. |
| **Wednesday** | **Team review.** |
| **Thursday afternoon** | **Distribution** — finished report sent. This is the product's **title date**. |

**Three dates — keep them distinct:**
- **Title date = distribution (Thursday).** What the product is dated.
- **ICOD line = collection cutoff (that week's Monday 0900).** Carried in the product body: "information current as of …".
- **LTIOV** (latest time information is of value) — **planning doctrine only. Never printed on the product.**

**Staging deliverable filename:** `WCTI_v[YYYYMMDD]_STAGING`, where the date is the **distribution (Thursday)** date — e.g. `WCTI_v20260813_STAGING`. "Vox" stays the internal artifact concept; this is the exported deliverable name.

---

## STANDING DIRECTIVES (current operative rules)

### Collection
- **Quality over quantity on sensors.** A feed earns its place only if reliable AND additive (offers a vantage the others don't). Drop noisy sensors rather than filter them.
- **Trusted sources ingested wholesale; AOR relevance decided at scoring**, not by keyword pre-filtering at collection.
- **Verify every feed URL against the current host's actual egress** before loading (some sources 403 datacenter/server IPs even when they work from a browser).
- **Collection window: the 7 days ending Monday 0900 (ICOD).** The window closes at the Monday 0900 cutoff; the staging draft is built from that closed corpus.
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
- **"Restraint is the product": 5–8 items per edition** (15 acceptable only for an inaugural catch-up).
- **Every item needs a "why an SLTT org cares" clause** tied to the low-maturity California SLTT audience. Items without SLTT relevance get cut.
- **Plain language, minimal-tooling recommendations** (IG1 CIS controls preferred). Audience consumes vendor software; they don't write code. Emphasis on vendor accountability and procurement governance.
- **Staging (Vox draft) = content only, no handling markings.** Distribution product is a separate template with TLP:CLEAR, deeper analysis, and presentation polish. Never conflate the two.
- **Three dates on the distribution product:** title = distribution (Thursday); ICOD line in body = collection cutoff (Monday 0900); LTIOV never printed.
- **Citations nested per entry** (not consolidated endnotes).
- **Source-access check before publishing:** confirm every cited URL is publicly reachable. On 403/paywall/login wall, find an alternative citation for the same reporting. A citation the audience can't open is not usable.
- **Synthesis stays manual** (no API/tokens) — deliberate choice, not a limitation to fix by default.

### Dissemination
- **Distribution target: Thursday afternoon** (after Monday staging, Mon–Tue individual review, Wednesday team review).
- **Product is TLP:CLEAR** — freely shareable, no distribution restriction.

---

## PENDING DIRECTION (act on these; move to Log when done)

- Verify + load curated AOR trusted sources (MS-ISAC, Cal OES, CDT, CA regional press) — replaces the dropped county feeds. Category 3 (official CA) first; drop any that prove noisy after a cycle.
- Build CA AG breach-registry scraper — authoritative AOR breach sensor (web portal, not RSS).
- Add ransomware leak-site aggregator (e.g. Ransomware.live) filtered for California — early-warning AOR sensor (catches victims before local press).
- ~~**Implement the Arbites recency flag**~~ — **DONE 2026-08-10.** Implemented in `core/arbites.py` (flag stale-by-publish-date vs the cycle window, never drop; configurable in `cti/pnd.md` → `scoring.settings.recency`). Verified by `tests/recency_test.py`; score parity preserved.
- Build distribution template + TLP:CLEAR presentation layer.
- Consider extending Arbites to scaffold a rough Vox draft (reduce chat tether without adding an API).
- Corpus still holds stale county-feed articles; they age out of the 7-day window — expect cleaner Arbites output over the following days.
- Analyst pass on edition v20260810 — merge cross-section duplicates (A/E + G/K), elevate primary sources, verify the Minnesota water-utilities claim.
- Consider widening the recency window — the current 7-day window flags many still-relevant 1–2-week-old items as STALE; a longer window may fit CTI better (tune empirically).
- Host monitoring — deferred.

*(Per-domain status/backlog lives here in the Mandate; the Cogitator is the shared, domain-neutral cycle map at `diagrams/cogitator.drawio`.)*

---

## LESSONS / DECISIONS LOG (dated; newest first)

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
- **Deferred:** fuzzy dedup (Jaccard/Levenshtein) — over-engineered; revisit only if a real false-merge is observed.

### 2026-08 — County keyword feeds dropped
- 34 county Google News query feeds returned local human-interest news, not cyber incidents. Root cause: keyword search on a general index treats cyber terms as soft hints, not hard filters. Architecturally wrong, not tunable. Rebuild AOR coverage via curated reliable sources + authoritative breach registry.

### 2026-08 — Collection doctrine settled
- Quality over quantity: strict on sensors, generous on items. Reliable + additive is the bar for adding a feed. Coverage emerges from good sensors well-operated, not from adding feeds.

### 2026-08 — Dedup hardened
- Added normalized-title dedup alongside URL-hash dedup (Google News links are redirect tokens, so URL-hash alone let the same story survive across feeds). Confirmed: a large backfill run dropped ~98% on the immediate second pass.

---

*End of Mandate. This document + the Codex + the `pnd.md` sensors are sufficient for any session to run the cycle. Keep it current — it is the memory of the intelligence cycle.*
