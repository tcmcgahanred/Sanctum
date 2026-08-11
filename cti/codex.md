# Weekly Cyber Threat Intelligence — Standing Intelligence Requirements

*Sanctum · Codex · v0.3 (starting anchor; history via git)*

_Governs the synthesis/analysis layer of the weekly brief. Collection (the `sensors` block in `pnd.md`) stays deliberately broad; this artifact controls what gets prioritized, elevated, and placed once items are in the corpus. Edit this to change what lands first — do not rewrite the workflow._

_Last updated: 2026-08-10_

---

## Layer 1 — Key Intelligence Questions (KIQ)

Enduring, high-level. Governs collection scope (wide net). Rarely changes.

- **KIQ-1:** What cyber threats endanger California State, Local, Tribal, and Territorial (SLTT) organizations and the critical infrastructure they operate or depend on?

Collection posture: cast a wide net. Any credible cyber-threat reporting is in scope at the collection layer. Filtering and prioritization happen downstream, here.

---

## Layer 2 — Priority Intelligence Requirements (PIR)

What the brief exists to answer. Applied during exploitation/analysis.

- **PIR-1:** What incidents, breaches, or targeting have directly affected California-based organizations or entities?
- **PIR-2:** What threat activity is targeting SLTT-relevant sectors — water/wastewater, K-12 and higher education, county/city/local government, tribal, and territorial entities — anywhere (as a leading indicator for the AOR)?
- **PIR-3:** What actively-exploited vulnerabilities (in-the-wild / CISA KEV) affect technology commonly deployed in low-maturity SLTT environments?
- **PIR-4:** What broad or national-level threats carry material relevance to SLTT defenders?

---

## Layer 3 — Prioritization Model ("lands first")

Determines ranking and placement within the brief. Scoring is **multiplicative**: a base **tier weight** is multiplied by the product of any applicable **elevation signals**. This rewards *convergence* — an item satisfying several requirements at once outranks one that scores on a single axis — consistent with the Intent × Opportunity × Capability convergence model used elsewhere in threat analysis.

**Score = (tier weight) × (product of elevation multipliers)**

### Base tier weights

| Tier | Requirement | Weight |
|------|-------------|--------|
| 1 | **AOR — direct.** An organization or entity in the AOR (California, in this example) directly affected. | **8.0** |
| 2 | **SLTT sector targeting.** Water/wastewater, K-12/higher ed, or local/tribal/territorial government targeted anywhere — a leading indicator for the AOR even when the named victim is out-of-state. | **4.0** |
| 3 | **Actively-exploited vulns in SLTT-common tech.** In-the-wild / CISA KEV, in technology low-maturity SLTT orgs actually run. | **2.0** |
| 4 | **Broad/national threats with SLTT relevance.** Clears the relevance bar; no stronger anchor. | **1.0** |

An item takes the weight of the **highest tier it qualifies for** (tiers are not additive with each other — an item that is both CA-direct and sector-targeting is tier 1, not 8+4).

### Elevation multipliers

Applied on top of the tier weight. **Absent = 1.0 (neutral) — a missing signal never suppresses a relevant item.** Present signals multiply the score up:

| Signal | Multiplier |
|--------|-----------|
| Actively exploited in the wild / on CISA KEV | **×1.5** |
| Affects technology commonly deployed in low-maturity SLTT orgs | **×1.5** |
| Supply chain / procurement-relevant (vendor-accountability angle) | **×1.3** |
| Ransomware against public-sector or critical-infrastructure targets | **×1.3** |

Multiple signals stack multiplicatively (e.g., KEV + low-maturity = ×2.25).

### Design intent: convergence wins

Tier spacing (8/4/2/1) is deliberately narrow enough that a heavily-elevated lower-tier item **can** outrank a bare higher-tier item. This is intended — a multi-signal active campaign against an out-of-state school (tier 2, several signals) is allowed to lead over a quiet California breach with no urgency signals (tier 1, no signals). Convergence across requirements is the strongest priority signal, above raw geography alone.

**Worked examples:**

- CA water utility breach, no elevation signals → 8.0 × 1 = **8.0**
- Out-of-state school ransomware on common tech (KEV + low-maturity + ransomware) → 4.0 × 1.5 × 1.5 × 1.3 = **11.7** *(outranks the bare CA item — by design)*
- National KEV vuln in SLTT-common tech (KEV + low-maturity) → 2.0 × 1.5 × 1.5 = **4.5**
- Broad supply-chain story (supply-chain signal) → 1.0 × 1.3 = **1.3**

---

## Layer 4 — Pre-Filter Cut Doctrine (governs any automated pre-scoring)

If scoring is ever run automatically upstream of synthesis (a pre-filter script on the host that scores the corpus and writes a candidate shortlist), these rules govern the cut. They also govern in-chat scoring. The goal: **relieve volume without ever hiding a real threat.**

**Governing asymmetry — prefer false positives to false negatives.** A false positive costs the analyst a few seconds of skimming. A false negative means a real AOR threat never reaches the analyst's eyes. These costs are wildly asymmetric, so the cut is biased toward *keeping*, not dropping.

**Strict on sensors, generous on items.** The quality-over-quantity doctrine governs *sources* — drop noisy feeds without hesitation. It does NOT govern *items* — keep borderline articles from reliable feeds. A good sensor's marginal item is worth surfacing; a bad sensor gets cut entirely. These operate at different layers and are not in tension.

**Specific cut rules:**
- **Wide cutoff.** Surface the top ~50–60 candidates, not a tight top-10 or top-30. Enough to relieve the 300–500 raw-article firehose, wide enough that anything plausibly publishable sits far above the cut line.
- **Round up on uncertainty.** If an item's tier or a multiplier is ambiguous, score it as if the higher interpretation were true. Ambiguity resolves toward visibility, not away from it.
- **Recency gate — by publication date, not collection date.** The brief carries only current-cycle reporting, and "current" is enforced on the item's **publication date** vs. the collection window (**the 7 days ending Monday 0900, the ICOD cutoff**) — *not* on when it was collected. A feed re-serving an older item (advisory update, re-list, news roundup, KEV resurfacing) can drop a stale story into the current corpus; the score alone won't catch it, because relevance carries no recency term. Items published outside the window are **flagged "STALE — confirm current hook," never hard-dropped** — an old CVE with a *new* this-week development (fresh KEV addition, new active-exploitation report, new named victim) is legitimately current and stays. Missing/garbage feed dates → treat as unknown and flag for review, never silently keep or drop. (Consistent with prefer-false-positives: flag, don't hide.) *Origin: a June FortiBleed advisory surfaced in edition v20260810.* **Implemented 2026-08-10 in `core/arbites.py`; window configured in `pnd.md` → `scoring.settings.recency`.**
- **Mandatory drop list.** Everything below the cut is still listed by title (titles only). "Dropped" never means "invisible." The analyst can eyeball discards in seconds and rescue anything mis-scored. This is the safety net that makes a generous cut fail-safe.
- **Scoring must show its reasoning.** Every surfaced candidate displays its tier, which multipliers fired, and why. The analyst checks the *reasoning*, not just the number — so a mis-tag (e.g., wrongly flagged KEV) is caught by inspection. A score the analyst cannot audit is an opaque gate and is not permitted.
- **Analyst override is absolute.** The analyst promotes or kills any item regardless of score. The pre-filter orders and relieves volume; it never decides.

**Why not a score handicap.** A flat discount on automated scores assumes consistent directional bias; scoring errors are actually inconsistent (sometimes high, sometimes low). A handicap gives false comfort without catching the real errors. Transparency (visible reasoning + drop list) catches what a handicap would miss, so transparency is the chosen safeguard, not a correction factor.

---


- **Two item targets — staging is generous, distribution is restrained.** The **staging doc (Monday)** is a *review surface*: **~5–6 items per content section, ~15–18 total** across NEWS, CTA TTPs and LATEST ATTACKS OR RISKS (KEYWORDS is wave-tops, no target). The **distributed report (Thursday)** is the *product*: **5–8 items total** — this is where "restraint is the product" applies. The count narrows through the week; that funnel is the intent. Extending the staging cut line pulls in the next-lower-ranked items from the *same* sorted queue — lower tier and/or fewer elevation signals — so it does not relax the standard. Every staging entry still carries its scoring reasoning (tier + which multipliers fired) so the analyst can audit where the cut falls.
- **One event, one entry.** A single incident often has both a "news" angle and a "TTP" angle (e.g., a supply-chain attack is both an announcement and a set of tradecraft). Place each event in the section matching its dominant value and fold the secondary angle into that single entry. Do not run the same event in two sections — it inflates the item count and reads as padding.
- These requirements drive **selection, ranking, and placement** — not collection. An item absent from the corpus can't be prioritized; that's a `sensors`-block question, not a PIR question.
- The score is a **prioritization aid, not a hard gate.** It orders items and decides what gets cut first when trimming — toward ~15–18 at staging, then toward 5–8 at distribution. Analyst judgment overrides the number — a low-scoring item with obvious operational significance still makes the brief.
- Tiers are **not additive with each other** — an item takes its single highest qualifying tier weight. Only the elevation multipliers stack.
- Absent elevation signals are **neutral (×1.0)**, never suppressive — a maximally-relevant item with no urgency signals is never scored to zero.
- This artifact is carried by the recurring synthesis task. When requirements shift, edit here and update the task's reference — the workflow itself doesn't change. Weights and multipliers are meant to be **tuned empirically** over the first several editions, the same way the collection-side IR schema evolves from the discard log.
