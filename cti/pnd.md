# CTI — Sanctum domain file

*One file. Everything the CTI effort needs to run, in the order the intelligence
cycle runs it. The engines in `core/` read only the fenced `yaml` and `sensors`
blocks below; every other line is for the person reading it.*

**BLUF:** Stage 1 says what we need to know. Stage 2 says where to look. Stage 3a
says what the machine does with what it found. Stage 3b says what the person does
with it. Nothing else about CTI lives anywhere else.

## The eight tenets

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

## How to read this file

| Stage | Section below | What the engine reads |
|---|---|---|
| 1 · Planning & Direction | Stage 1 | `manifest:` (runtime and storage) |
| 2 · Collection | Stage 2 | `manifest.collection:` and the ```` ```sensors ```` block |
| 3a · Processing | Stage 3a | `scoring:` and `vocab:` |
| 3b · Exploitation | Stage 3b | `production.report_title` only |

Dated history — what changed, when, and what it cost — is **not** here. It is in
[`CHANGELOG.md`](CHANGELOG.md). What survived the history is in the tenets above.

---

## Stage 1 — Planning & Direction

*What we need to know, who decided it, and where the machine keeps its things.*

### 1.1 Mandate and cadence

#### HOW TO USE THIS DOCUMENT (for a fresh chat session)

1. Read the Standing Directives — they are the current operative rules. Apply them.
2. Read Pending Direction — that's what this cycle or the next should act on.
3. When the cycle ends, add lessons to the Log and update directives/pending as needed.
4. If a directive here conflicts with an ad-hoc request, the directive is the retained decision — confirm before overriding.

---

#### WEEKLY CADENCE (the operative schedule)

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

#### STANDING DIRECTIVES (current operative rules)

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

#### PENDING DIRECTION (act on these; move to Log when done)

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

### 1.2 Requirements tree

#### Collection posture

Cast a wide net. Any credible cyber-threat reporting is in scope at the collection layer — **trusted sources are ingested wholesale and AOR relevance is decided at scoring**, never by keyword pre-filtering at collection. Filtering and prioritization happen downstream, against the tree below.

#### Terminology

- **KIQ** — Key Intelligence Question. Enduring, top-level. Governs collection scope.
- **PIR** — Priority Intelligence Requirement. What the brief exists to answer.
- **SIR** — Specific Intelligence Requirement. A narrower question that decomposes a PIR.
- **EEI** — Essential Element of Information. The specific collectable fact that answers an SIR.
- Each EEI carries `[Sensor: …]` (what collects it; **ACTIVE / PARTIAL / PENDING / ABSENT**) and `[Scoring: …]` (how it is weighted) and/or `[Standard: …]` (a production rule governing it).

---

#### KIQ-1: What cyber threats endanger California SLTT organizations and the critical infrastructure they operate or depend on?

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

#### Byproduct 1 — Sensor-build roadmap (prioritized)

Each pending sensor is the essential means of collecting one or more EEIs. Priority = how much AOR-specificity it unlocks.

0. **Fix `process_page` re-collection** (`core/acolyte.py:114`) — **prerequisite, not a sensor.** Page-type sources are deduped on URL hash, so a portal is captured once and never revisited. Both of the next two items are portals and are useless until this lands.
1. **CA AG breach-registry scraper** — serves EEI-1.1.a. The single highest-value build: the only authoritative, AOR-direct breach sensor. PIR-1 has almost no active collection without it.
2. **Cal-CSIC advisories** — serves EEI-1.1.d. Confirmed alive and publishing through Aug 2026. Extracting the index page may yield enough, since titles and dates are what the scorer consumes — prove that before building PDF parsing.
3. **Ransomware leak-site aggregator, CA-filtered** — serves EEI-1.1.b. Early-warning AOR-direct (victims appear before local press).
4. **CISA KEV as a primary feed** — serves EEI-3.1.a. Currently absent; reduces single-aggregator dependence. Cheapest item on this list.
5. **Curated CA regional press** — serves EEI-1.1.c. Still unserved; StateScoop does not cover it.
6. **Remaining sector trade press** (K-12 Dive, WaterISAC) — serves EEI-2.1.a/b.

~~Curated official CA feeds (Cal OES, CDT, MS-ISAC)~~ — **DONE 2026-08-11.**

#### Byproduct 2 — Coverage-gap finding

Decomposition makes the gap explicit: **three of four EEIs under SIR-1.1 — the AOR-direct core of PIR-1 — remain PENDING.** (EEI-1.1.d was closed 2026-08-11.) The pipeline answers PIR-1 largely by luck: when a statewide query or national outlet happens to name a California entity.

Therefore the CTI domain is presently **California-statewide-and-national collection with AOR-aware scoring, not AOR-specific collection.** Closing this gap is a collection problem (build the SIR-1.1 sensors), not a scoring problem — scoring is ready and has been.

#### Byproduct 3 — Production standards captured (from analyst-gate feedback)

The decomposition absorbs cyber-team lessons as EEI-level standards, so they persist as doctrine rather than one-off edits:

- **Anti-FUD verification** (EEI-1.3.a): verify specific impact claims (e.g., a 911 outage) against a primary source; soften or cut what can't be confirmed.
- **Attribution discipline** (EEI-1.3.b): suspected ≠ confirmed; never state suspected attribution as fact.
- **Provider-dependent relevance** (EEI-3.2.b): product-specific items are relevant only if the audience uses the affected product/provider.
- **Audience-portfolio filter** (EEI-4.1.b): topicality ≠ relevance; developer-only and defense-industrial-only items are out of portfolio.

### 1.3 Runtime and storage

Where the corpus lives and how collection is tuned. `base_dir` is the one
host-coupled value; override it per host with the `SANCTUM_BASE` env var (wins
over this) so the repo itself stays portable. To move Sanctum to another server:
set `SANCTUM_BASE` (or edit `base_dir`), point `rclone_remote` at your storage,
`pip install -r requirements.txt`, and run.

```yaml
manifest:
  domain: cti
  base_dir: /opt/ravenor            # current host; override with $SANCTUM_BASE
  sensors_file: references/sensors.txt  # FALLBACK ONLY — feeds live in the ## Sensors block below
  corpus:
    backend: rclone                 # rclone | local | (s3 future)
    rclone_remote: gdrive:ravenor-corpus
  reference_lists:                  # facts to look up instead of inferring
    kev:
      url: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
      json_path: vulnerabilities
      key_field: cveID
      match_pattern: "CVE-[0-9]{4}-[0-9]{4,7}"
      cache_hours: 12
  staging:                          # where the analyst picks the draft up
    backend: rclone
    rclone_remote: gdrive:ravenor-staging
    filename: "WCTI_{date}_STAGING.md"   # {date} -> YYYYMMDD (collection date)
```

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

## Stage 2 — Collection

*Where to look, how hard, and how far back.*

### 2.1 Collection settings

The window, the recency gate, and how each fetch behaves. Split out of the
manifest block above only so it sits with the sensors it governs — the loader
merges every `yaml` block in this file into one config, so `manifest:` appearing
twice is not a duplicate, it is one map assembled in two places.

```yaml
manifest:
  collection:
    window_days: 7                  # rolling collection window
    max_publish_age_days: 7         # reports older than this never enter the corpus
    min_title_len: 15               # below this, don't title-dedup
    suffix_separators: [" - ", " | ", " — "]
    fetch:
      user_agent: ""                # OFF. Setting one cost two sensors — see below
      timeout: 20                   # seconds per request
      sleep_time: 1.0               # polite pause between requests to one host
      max_redirects: 5
      min_extracted_size: 80        # characters; below this trafilatura returns nothing
      impersonate: chrome           # curl_cffi profile for the retry; "" disables it
      decode_google_news: true      # resolve news.google.com wrappers to the publisher
      gnews_interval: 1             # seconds between Google News resolutions
```

### 2.2 Sensors

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

```sensors
# --- National: government / CERT / SLTT ---
https://www.cisa.gov/cybersecurity-advisories/all.xml
https://us-cert.cisa.gov/ncas/current-activity.xml
https://www.cisecurity.org/feed/alert
https://www.kb.cert.org/vulfeed
https://www.nist.gov/blogs/cybersecurity-insights/rss.xml
https://jvn.jp/en/rss/jvn.rdf

# --- National: vendor PSIRTs ---
# MSRC update-guide RSS was dropped 2026-08-25. See the drop list above.
https://sec.cloudapps.cisco.com/security/center/psirtrss20/CiscoSecurityAdvisory.xml
https://security.paloaltonetworks.com/rss.xml
https://www.fortiguard.com/rss/ir.xml

# --- National: exploitation evidence ---
https://www.greynoise.io/blog/rss.xml
https://www.rapid7.com/blog/rss/
https://www.zerodayinitiative.com/rss/published/
https://blog.qualys.com/feed

# --- National: news / research ---
https://therecord.media/feed/
https://unit42.paloaltonetworks.com/feed/
https://feeds.feedburner.com/TheHackersNews
https://isc.sans.edu/rssfeed_full.xml
https://www.schneier.com/feed/atom/
https://www.darkreading.com/rss.xml
https://securelist.com/feed/
https://news.sophos.com/en-us/category/threat-research/feed/
https://www.crowdstrike.com/blog/feed/
https://www.recordedfuture.com/feed/
https://www.tenable.com/blog/feed
https://feeds.feedburner.com/hackread
https://feeds.feedburner.com/TroyHunt
https://www.infosecurity-magazine.com/rss/news/
https://cybersecuritynews.com/feed/
https://bartblaze.blogspot.com/feeds/posts/default
https://krebsonsecurity.com/feed/
https://googleprojectzero.blogspot.com/feeds/posts/default
https://www.bleepingcomputer.com/feed/
https://statescoop.com/feed/
# Added 2026-08-23. Found by auditing which outlets a CyberWire daily roundup cited:
# five of ten stories came from these two, and neither was collected here.
# SecurityWeek: use the first-party path, not feeds.feedburner.com/securityweek (same
# content behind a 302, and no reason to add a Feedburner dependency). NOTE: its feed
# window holds only 10 items — safe while collection runs daily, not if that changes.
https://www.securityweek.com/feed/
# The Register: SECTION feed only. The whole-site feed at /headlines.atom is a general
# tech magazine — git tooling, Microsoft trivia — and does not belong in this corpus.
https://www.theregister.com/security/headlines.atom
https://industrialcyber.co/feed/

# --- National: vendor telemetry ---
# Added 2026-08-23, every path verified from the collector host first. These
# vendors run incident response and sensor networks this effort will never have.
# When they publish, it is primary source. Marketing overhead is the price and
# the scorer sorts it out.
#
# Huntress: SMB and MSP telemetry — the closest commercial visibility there is
# to a low-maturity SLTT environment. Its output lands directly on vocabulary
# already declared here: n-able, n-central, kaseya, connectwise, screenconnect
# in lowmat_tech; rmm, msp, managed service provider in supplychain.
# NOTE: the feed window is 680 items — the whole blog archive, served every
# fetch. That is a ONE-TIME intake, not a rate; steady state is a few a week.
# Roughly half the archive is company news and educational content, which will
# score low and drop. That was a decision, not an oversight.
https://www.huntress.com/blog/rss.xml
# Google Threat Intelligence (absorbed Mandiant). Use the cloudblog host: the
# cloud.google.com path returns HTTP 200 with ZERO entries — live URL, no
# content, the exact failure the item count exists to catch.
https://cloudblog.withgoogle.com/topics/threat-intelligence/rss/
# Cisco Talos research. Distinct from the Cisco PSIRT advisory feed above —
# that is disclosures, this is investigation. First-party path, not the
# Feedburner mirror, which serves identical content.
https://blog.talosintelligence.com/rss/
# Microsoft Threat Intelligence. Distinct from the MSRC feed above, which is
# the patch catalogue. Low volume and a real marketing fraction — the weakest
# of these four and the first to drop at review. The old msrc-blog host is dead.
https://www.microsoft.com/en-us/security/blog/feed/

# --- National: breach registry ---
# Named-victim breach disclosure. Low volume (~2-3 per cycle). NOTE: the item
# date is the date the breach was LOADED, not the date it happened, so the
# recency gate will not flag a years-old breach loaded yesterday. The first
# sentence of every description states the actual breach month — read it.
https://haveibeenpwned.com/feed/breaches/

# --- Regional AOR: official sources (example: California) ---
https://www.news.caloes.ca.gov/feed/
https://www.cdt.ca.gov/newsroom/feed/

# --- Regional AOR: municipal press (example: California) ---
# California City News, cybersecurity section. EXPECTED YIELD IS ~3 ITEMS PER YEAR:
# 12 items span Sep 2022 to Mar 2026. A column of `0 new of 12 returned` in the log is
# NORMAL for this sensor and is not a failure — it serves its whole back catalogue every
# fetch. Kept because nothing else here emits a named California municipal victim
# (Long Beach, El Cerrito, Contra Costa), and because it carries local-government policy
# items — closed-session law, grant programs — that no general news query surfaces.
# Review yield 2026-11-23.
https://www.californiacitynews.org/taxonomy/term/1717/feed

# --- Regional AOR: statewide / sector queries (example: California) ---
https://news.google.com/rss/search?q=%22California%22%20(ransomware%20OR%20%22data%20breach%22%20OR%20cyberattack)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(%22community%20college%22%20OR%20university%20OR%20CSU%20OR%20UC)%20(ransomware%20OR%20%22data%20breach%22)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20%22school%20district%22%20(ransomware%20OR%20cyberattack%20OR%20%22data%20breach%22)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(%22special%20district%22%20OR%20%22transit%20agency%22%20OR%20%22public%20works%22)%20(cyberattack%20OR%20ransomware%20OR%20breach)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(city%20OR%20county)%20(ransomware%20OR%20cyberattack%20OR%20%22data%20breach%22)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(court%20OR%20%22superior%20court%22%20OR%20sheriff%20OR%20%22police%20department%22)%20(ransomware%20OR%20cyberattack%20OR%20breach)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(election%20OR%20%22registrar%20of%20voters%22)%20(cyberattack%20OR%20breach%20OR%20hack)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20government%20(ransomware%20OR%20cyberattack)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(hospital%20OR%20health%20OR%20clinic)%20(ransomware%20OR%20%22data%20breach%22)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20tribal%20(casino%20OR%20nation%20OR%20government)%20(ransomware%20OR%20cyberattack%20OR%20breach)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(water%20OR%20wastewater%20OR%20utility)%20(cyberattack%20OR%20hack%20OR%20breach)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
```

---

## Stage 3a — Processing

*Deterministic. No model, no judgement, no tokens. Produces the staging document.*

### 3a.1 Scoring model

The multiplicative model, verbatim from the CTI doctrine: a base **tier weight**
(highest qualifying tier only; tiers don't stack) times the product of any
**elevation multipliers** (absent = neutral). Tier 1 requires California to be the
**subject of an incident** — either California in the title *and* an incident word
present, or a California term within ~120 chars of an incident word in the body —
not a passing mention. Groups are keyword lists; short/ambiguous ones match on
word boundaries.

**Score = (tier weight) × (product of elevation multipliers)**

### Why the model is shaped this way

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

```yaml
scoring:
  tiers:
    - id: 1
      name: "Direct impact to California organizations"
      serves: PIR-1
      serves_eei: ["EEI-1.2.a"]     # the 34-county match; 1.1.a-d are SENSOR-bound                 # §1.2 — Direct impact to CA organizations
      weight: 8.0
      require:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: cyber_context, scope: blob}   # cyber-domain floor, see prose above
          - any:
              - all:
                  - {group: geo, scope: title}
                  - {group: incident, scope: blob}
              - all:
                  - {group: geo, scope: blob}
                  - {group: incident, scope: blob}
                  - {proximity: {a: geo, b: incident, window: 120}}
    - id: 2
      name: "SLTT sector targeting anywhere (leading indicator)"
      serves: PIR-2
      serves_eei: []                # 2.1.a/b are SENSOR-bound, not scoring-derived                 # §1.2 — SLTT sector targeting anywhere
      weight: 4.0
      require:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: cyber_context, scope: blob}   # cyber-domain floor, see prose above
          - any:
              - all:
                  - {group: sector, scope: title}
                  - {group: incident_broad, scope: blob}
              - {proximity: {a: sector, b: incident_broad, window: 80,
                             scope: blob, all_occurrences: true}}
    - id: 3
      name: "Actively-exploited vulnerabilities in SLTT-common technology"
      serves: PIR-3
      serves_eei: []                # 3.1.a/b are SENSOR-bound (3.1.a has NO sensor)                 # §1.2 — Actively-exploited vulns in SLTT-common tech
      weight: 2.0
      require:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: cyber_context, scope: blob}   # cyber-domain floor, see prose above
          - {group: exploit_strong, scope: blob}
          - {group: lowmat_tech, scope: blob}
          - {proximity: {a: lowmat_tech, b: exploit_strong, window: 200,
                         scope: blob, all_occurrences: true}}
    - id: 4
      name: "Broad/national threats with SLTT relevance"
      serves: PIR-4
      serves_eei: []                # 4.1.a is SENSOR-bound                 # §1.2 — Broad/national threats with SLTT relevance
      weight: 1.0
      require: always

  multipliers:
    - name: "KEV / actively exploited"
      serves_eei: []                # both SENSOR-bound; 3.1.a has no sensor at all
      factor: 1.5
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: exploit_strong, scope: blob}
          - any:
              - {proximity: {a: exploit_strong, b: cve, window: 200,
                             scope: blob, all_occurrences: true}}
              - {proximity: {a: exploit_strong, b: lowmat_tech, window: 200,
                             scope: blob, all_occurrences: true}}
    - name: "low-maturity SLTT tech"
      serves_eei: ["EEI-2.2.a", "EEI-3.2.a"]   # both scoring-derived
      factor: 1.5
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - any:
              - {group: lowmat_tech, scope: title}
              - {proximity: {a: lowmat_tech, b: exploit_strong, window: 200,
                             scope: blob, all_occurrences: true}}
              - {proximity: {a: lowmat_tech, b: incident_broad, window: 120,
                             scope: blob, all_occurrences: true}}
    - name: "supply-chain / procurement"
      serves_eei: []                # no element declares this multiplier
      factor: 1.3
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - any:
              - {group: supplychain, scope: title}
              - {proximity: {a: supplychain, b: incident_broad, window: 120,
                             scope: blob, all_occurrences: true}}
    - name: "ransomware vs public-sector/CI"
      serves_eei: []                # 1.1.b is SENSOR-bound (leak-site aggregator, PENDING)
      factor: 1.3
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - {proximity: {a: ransom, b: ci, window: 150,
                         scope: blob, all_occurrences: true}}

  # FLOORS raise a score to a minimum. They never lower one and never force the
  # surface - the item becomes visible for review at the bottom of the surface
  # instead of being guaranteed a place. Use where the signal is authoritative
  # but its relevance to this domain is unproven.
  floors:
    - name: "CISA directive on technology not on the SLTT list"
      score: 2.0
      when:
        all:
          - {not: {group: listicle, scope: title}}
          # AUTHORITATIVE SOURCE ONLY. A trade write-up saying "CISA ordered a
          # patch" is a secondary mention; this must be the directive itself.
          - {group: cisa_source, scope: source}
          - {group: exploit_strong, scope: blob}
          # Only when the product is NOT on the low-maturity list. When it is,
          # tier 3 and force-surface M2 already handle it and score higher.
          - {not: {group: lowmat_tech, scope: blob}}

  force_surface:
    - name: "M1 in-AOR entity in an incident"
      serves_eei: ["EEI-1.2.a"]
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: cyber_context, scope: blob}   # cyber-domain floor
          - any:
              - all:
                  - {group: geo, scope: title}
                  - {group: incident, scope: blob}
              - {proximity: {a: geo, b: incident, window: 120,
                             scope: blob, all_occurrences: true}}
    - name: "M2 exploited flaw affecting SLTT-relevant technology"
      serves_eei: ["EEI-3.2.a"]
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: cyber_context, scope: blob}   # cyber-domain floor
          - {group: exploit_strong, scope: blob}
          - {group: lowmat_tech, scope: blob}
          - {proximity: {a: lowmat_tech, b: exploit_strong, window: 200,
                         scope: blob, all_occurrences: true}}
    - name: "M3 SLTT sector in an incident"
      serves_eei: []                # 2.1.a is SENSOR-bound
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: cyber_context, scope: blob}   # cyber-domain floor
          - any:
              - all:
                  - {group: sector, scope: title}
                  - {group: incident_broad, scope: blob}
              - {proximity: {a: sector, b: incident_broad, window: 80,
                             scope: blob, all_occurrences: true}}

  settings:
    surface_min_score: 2.0
    empty_title: {score: 0.5, tier: 4, flag: "FLAG: empty title (feed artifact - verify source)"}
    recency:
      enabled: true
      window_days: 7
      cutoff_weekday: wednesday
      cutoff_time: "04:00"
      timezone: America/Los_Angeles
    grouping:
      enabled: true
      similarity: 0.15
      min_shared_tokens: 3
      min_evidence: 8.0
      max_group_size: 25
      max_group_display: 12

  word_boundary_terms: ["scada", "ransom", "cisco", "how to", "what is", "hacker"]

  groups:
    geo: ["california", "californian", " calif ", "sacramento", "fresno",
          "modesto", "stockton", "bakersfield", "cal oes", "cal-csic", "ccic",
          "caltrans", "csu ", "uc ", "calmatters",
          "alpine county", "amador county", "butte county", "calaveras county",
          "colusa county", "el dorado county", "fresno county", "glenn county",
          "inyo county", "kern county", "kings county", "lake county",
          "lassen county", "madera county", "mariposa county", "mendocino county",
          "merced county", "modoc county", "mono county", "nevada county",
          "placer county", "plumas county", "sacramento county", "san joaquin county",
          "shasta county", "sierra county", "stanislaus county", "sutter county",
          "tehama county", "trinity county", "tulare county", "tuolumne county",
          "yolo county", "yuba county"]
    # CONFIDENTIALITY language only, by decision. Availability terms (outage,
    # denial of service, ddos) are deliberately NOT here - see `targeting`.
    # This group feeds tier 1 and force-surface M1, which need only a place
    # name plus one of these words, so a California wildfire or public safety
    # power shutoff would become an AOR cyber incident.
    # P&D work order 2026-08-24, decision 4.
    incident: ["breach", "ransomware", "cyberattack", "cyber attack", "hacked",
               "hackers", "stolen data", "data theft", "blackmail", "defaced",
               "defacement",
               "data breach", "compromise", "exfiltrat", "extortion", "data leak",
               "data stolen", "records stolen", "security incident"]
    # Attack, disruption and availability language. Reaches rules ONLY through
    # `incident_broad`, which is used where the sector must already be the
    # subject - so availability terms can never reach tier 1.
    targeting: ["active threat", "outage", "denial of service", "ddos",
                "exploited against", "attacks against", "attack against",
                "campaign against", "targeted", "target of", "attack on",
                "attacks on", "hit by", "struck by", "victim of", "taken offline",
                "forced offline", "systems offline", "service disruption",
                "state of emergency", "disrupted operations", "shut down its",
                "knocked offline"]
    # The union of `incident` and `targeting`, PLUS the singular "hacker".
    # Keep it as that union: a term added to either parent belongs here too.
    # "hacker" lives ONLY here, never in `incident`, because it is noise-prone
    # - "ethical hacker", "hacker conference", the feed name "The Hacker News".
    # Confined here it can only fire where the sector is already the subject.
    # ON WATCH: if it over-fires next cycle, drop it and keep only "hackers".
    incident_broad: ["breach", "ransomware", "cyberattack", "cyber attack", "hacked",
                     "hackers", "hacker", "stolen data", "data theft", "blackmail",
                     "defaced", "defacement",
                     "data breach", "compromise", "exfiltrat", "extortion", "data leak",
                     "data stolen", "records stolen", "security incident",
                     "active threat", "outage", "denial of service", "ddos",
                     "exploited against", "attacks against", "attack against",
                     "campaign against", "targeted", "target of", "attack on",
                     "attacks on", "hit by", "struck by", "victim of", "taken offline",
                     "forced offline", "systems offline", "service disruption",
                     "state of emergency", "disrupted operations", "shut down its",
                     "knocked offline"]
    sector: ["water utility", "water utilities", "water district", "water authority",
             "water sector", "utility sector", "public works", "transit authority",
             "school system", "public schools",
             "water treatment", "water system", "drinking water", "wastewater",
             "utility district", "public utility", "electric utility",
             "school district", "k-12", "k12", "higher ed", "community college",
             "university", "municipal", "city government", "county government",
             "local government", "tribal government", "tribal nation",
             "public sector", "election office", "election systems",
             "registrar of voters", "transit agency", "special district",
             "sheriff's office", "sheriff's department", "police department",
             "superior court", "county court"]
    lowmat_tech: ["fortinet", "fortigate", "sonicwall", "mikrotik", "routeros", "openwrt",
                  "sharepoint", "exchange server", "vpn", "rdp", "n-able", "n-central",
                  "kaseya", "connectwise", "screenconnect", "wordpress", "plc",
                  "programmable logic controller", "scada", "ics", "operational technology",
                  "cisco", "netgear", "tp-link", "router", "firewall"]
    exploit_strong: ["actively exploited", "exploited in the wild", "in-the-wild",
                     "under active exploitation", "added to its known exploited",
                     "added to the known exploited", "kev catalog", "cisa kev",
                     "exploitation in the wild", "weaponized exploit",
                     "public proof-of-concept", "proof-of-concept exploit",
                     "exploit code is available", "being exploited",
                     "active threat", "active exploitation", "ongoing exploitation",
                     "observed exploitation", "actively targeting"]
    kev: ["cisa kev", "known exploited", "actively exploited", "exploited in the wild",
          "in-the-wild", "added to its known exploited", "kev catalog",
          "zero-day", "0-day", "under active exploitation"]
    cve: ["cve-"]
    # Tradecraft language - how an adversary operates, as distinct from what
    # happened to a victim (`incident`) or what is being exploited
    # (`exploit_strong`). Used only to suggest the CTA TTPs section; it feeds
    # no tier, no multiplier and no force-surface rule, so a false match costs
    # a section suggestion the analyst overrides, nothing more.
    ttp: ["lateral movement", "living off the land", "lolbin", "initial access",
          "privilege escalation", "persistence mechanism", "command and control",
          "credential harvesting", "credential theft", "web shell", "webshell",
          "infostealer", "info-stealer", "loader", "dropper", "beacon",
          "att&ck", "mitre att", "tradecraft", "tactics, techniques",
          "spearphishing", "spear-phishing", "social engineering",
          "defense evasion", "obfuscation", "dll sideloading", "dll side-loading",
          "process injection", "living-off-the-land"]
    # Matched against the `source` scope, never the article text.
    cisa_source: ["cisa.gov"]
    # CYBER-DOMAIN FLOOR. Added 2026-08-31. An item cannot reach tier 1, 2 or 3,
    # and cannot force-surface, unless it contains at least one of these. It is a
    # FLOOR, not a scorer - nothing here adds weight, and a generous list is the
    # safe direction because a miss here silently deletes a requirement while a
    # false positive merely leaves an item eligible to be scored on its merits.
    #
    # WHY. On 2026-08-31 "A Baby Great White Leapt from the Ocean Near a Boogie
    # Boarder" scored 8.0, tier 1, force-surfaced on M1: `geo:'california'` and
    # `incident:'breach'` - a shark BREACHING the ocean near a California beach.
    # "breach" is also a levee, a contract, a courtroom verdict and a code of
    # conduct. Measured against 776 items: this floor removes 16 of 137 surfaced
    # items and every one of the 16 is non-cyber - sharks, whale watching, two
    # lottery suits, Oakley v Nike, a reinsurance dispute, Justice Thomas.
    #
    # NOT the word "cyber" alone. That was tried first and measured: it would have
    # deleted the California DMV data breach, the LA Superior Court ransomware
    # shutdown, the Northern Inyo Hospital breach and all three tier-3 vulnerability
    # advisories - 44 items, roughly half of them the most in-scope in the set.
    # Incident reporting does not say "cyber"; journalists and policy writers do.
    #
    # EVERY FORM OF "hack" IS SPELLED OUT, and that is not tidiness. The matcher
    # gives any term of 4 characters or fewer automatic WORD-BOUNDARY matching, so
    # a bare "hack" does not match "hacks", "hacked" or "hacking" - it matches only
    # the standalone noun. Measured: with "hack" alone, "Attackers Targeted Over 100
    # US Water Systems in July Hacks" was deleted, a tier-2 water-sector item lost to
    # one plural noun. This is the same 4-character boundary rule behind Open finding
    # 2 in §3a.2. A stem is not a stem in this engine unless it is 5+ characters.
    cyber_context: ["cyber", "hacks", "hacked", "hacker", "hacking", "hack",
          "ransomware", "malware", "phish",
          "data breach", "security breach", "breach notification",
          "personal information", "social security", "patient record",
          "customer record", "credit card", "credential", "password",
          "database", "unauthorized access", "exfiltrat", "encrypted the",
          "threat actor", "security incident", "vulnerabilit", "exploit",
          "cve-", "patch", "denial of service", "ddos", "it systems",
          "computer system", "network", "server", "stolen data", "data theft",
          "identity theft", "information technology"]

    listicle: ["top 5", "top 7", "top 10", "top 12", "top 15", "top 20", "top 25",
               "biggest", "ranked", "you should know", "ultimate guide",
               "buyer's guide", "buyers guide", "roundup", "round-up",
               "best solutions", "best software", "best tools", "best vpn",
               "best antivirus", "best firewall", "best wireless", "best wi-fi",
               "best security", "cheat sheet", "what is", "how to",
               "explained:", "a beginner's guide", "everything you need to know"]
    supplychain: ["supply chain", "supply-chain", "npm", "pypi", "package", "dependency",
                  "third-party", "vendor compromise", "msp", "managed service provider",
                  "rmm", "procurement", "software supply"]
    ransom: ["ransomware", "ransom", "extortion", "encrypt", "leak site", "double extortion"]
    ci: ["critical infrastructure", "water utility", "water district", "water treatment",
         "wastewater", "drinking water", "power grid", "electric grid",
         "hospital", "healthcare", "public sector", "local government",
         "municipal", "school district", "public utility"]
```

### 3a.2 Vocabulary

#### Open finding 1 — the `incident` group covers one third of the problem

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

#### Open finding 2 — `" calif "` does not do what it looks like

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

#### Open finding 3 — `geo` carries known collisions and now sits in the highest-cost position

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

#### How a keyword gets attributed to a requirement

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

#### Group review status

```yaml
vocab:
  review_interval_days: 180
  groups:
    # Each group declares ONE of `serves:` or `role:`. See "How a keyword gets
    # attributed to a requirement" above for what the values mean and why the
    # declaration lives beside the group rather than in the requirements tree.
    geo:
      reviewed: 2026-08-17
      review_interval_days: 180   # county/city lists change slowly
      serves: [PIR-1]             # tier 1 and force-surface M1
    incident:
      reviewed: 2026-08-24        # theft/hacker terms added, v2 changelog
      review_interval_days: 90    # see Open finding 1 — known incomplete
      serves: [PIR-1]             # tier 1 and force-surface M1
    sector:
      reviewed: 2026-08-24        # rewritten to compound terms, v2 changelog
      serves: [PIR-2]             # tier 2 and force-surface M3
    incident_broad:
      reviewed: 2026-08-24
      review_interval_days: 90    # keep as union of incident + targeting, plus 'hacker'
      serves: [PIR-2]             # tier 2 and M3; ALSO elevates two multipliers
    exploit_strong:
      reviewed: 2026-08-24
      review_interval_days: 90    # the line between real exploitation and trend talk moves
      serves: [PIR-3]             # tier 3, force-surface M2, the CISA floor;
                                  # ALSO elevates both x1.5 multipliers
    lowmat_tech:
      reviewed: 2026-08-17
      review_interval_days: 90    # Vox Policy §7 calls this a maintained lexicon
      serves: [PIR-3]             # tier 3, force-surface M2, the CISA floor;
                                  # ALSO elevates both x1.5 multipliers
    ci:
      reviewed: 2026-08-24        # rewritten to compound terms, v2 changelog
      role: elevation             # ransomware vs public-sector/CI multiplier only
    ransom:
      reviewed: 2026-08-17
      review_interval_days: 90    # actor and brand names turn over fast
      role: elevation             # ransomware vs public-sector/CI multiplier only
    supplychain:
      reviewed: 2026-08-17
      role: elevation             # supply-chain / procurement multiplier only
    cve:
      reviewed: 2026-08-24
      review_interval_days: 365   # identifier format, not vocabulary
      role: elevation             # KEV / actively exploited multiplier only
    cisa_source:
      reviewed: 2026-08-24
      review_interval_days: 365   # a hostname, not vocabulary
      role: elevation             # the CISA-directive floor raises a score
    cyber_context:
      reviewed: 2026-08-31
      review_interval_days: 90    # the words reporters use for a hack turn over
      role: gate                  # a precondition, not a scorer - adds no weight
    listicle:
      reviewed: 2026-08-24
      review_interval_days: 90    # headline fashions change; new shapes will appear
      role: exclusion             # only ever appears under a `not`
    ttp:
      reviewed: 2026-08-25
      review_interval_days: 90    # tradecraft naming follows the research, fast
      role: production            # suggests the "CTA TTPs" section; scores nothing
    kev:
      reviewed: 2026-08-17
      review_interval_days: 90
      role: unused
      unused_because: >
        Split into `exploit_strong` on 2026-08-24 because it was doing two jobs,
        mixing exploitation evidence with generic vulnerability vocabulary.
        Retained under the standing rule that when a group turns out to be two
        groups you split it rather than deleting half. NOTE: `zero-day` and
        `0-day` live here and nowhere else, so they currently fire no multiplier
        — reconcile with work order 3 in cti/pnd_work_orders_20260825.md before
        that decision is taken.
    targeting:
      reviewed: 2026-08-24
      review_interval_days: 90    # attack-verb phrasing follows the press, not the threat
      role: unused
      unused_because: >
        Availability language (outage, denial of service, taken offline, service
        disruption) is confined here by design. `incident_broad` was built as the
        union of `incident` and `targeting` and is what the rules read; this group
        is the reserve the union draws from. Wiring it into `incident` is Open
        finding 1 and a P&D decision, not a maintenance edit.

    # PIR-4 — broad/national with SLTT relevance — has NO group. Tier 4 is
    # `require: always`, the floor every item lands on when nothing else
    # qualifies. There is no vocabulary to attribute to it and there should not
    # be: it is the absence of the other three, not a subject of its own.

  accepted:
    - check: padded term
      subject: "' calif ' in geo"
      reason: >
        Known and understood — see Open finding 2. Both fixes change matching,
        so the decision belongs to P&D rather than to a maintenance pass. The
        marginal exposure is small: california/californian already match, and
        the residual false positives are place names containing "calif".
      date: 2026-08-17
```

---

## Stage 3b — Exploitation

*A person and a model, working the staging document into the vox.*

### 3b.1 Production

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

```yaml
production:
  # ---- Stage 3b (exploitation) — the domain's answers to ../docs/EXPLOITATION.md ----
  # The generic method lives in docs/EXPLOITATION.md at the repo root. These are the
  # only parts of it that are CTI-specific.
  audience: >
    Low-maturity State/Local/Tribal/Territorial (SLTT) organisations in the AOR —
    counties, cities, school and special districts. They consume vendor software;
    they do not write code. Recommendations must be plain-language and
    minimal-tooling (IG1 CIS controls preferred), and lean on vendor
    accountability and procurement governance rather than engineering effort.
  relevance_clause: "Why an SLTT organization should care:"
  show_scores: true                    # R6 — carry the 3a score and reasoning per item
  # -----------------------------------------------------------------------------
  # Two documents, two names. 3a makes the staging document; 3b makes the vox.
  # Use these EXACTLY as written — no prefixes, no additions, no org initials.
  # "Vox" is INTERNAL shorthand and must never appear in the reader-facing
  # product (Vox Policy §3). No "CCIC" prefix until AOR-direct sensors exist.
  report_title: "WCTI — Staging Document (candidate queue)"   # 3a output, title
  vox_title: "WCTI — Weekly Cyber Threat Intelligence"         # 3b output, reader-facing heading
  # Vox Policy §7: NO fixed limit on items per section or overall. The former
  # staging_item_target [15,18] and staging_per_section [5,6] were exactly the
  # caps the policy forbids and have been removed. Restraint belongs to the
  # distributed product, applied by the team as editorial judgment — it is not
  # an automated cap on what surfaces for review.
  distributed_item_target: [5, 8]      # Thursday product — OUTSIDE Sanctum's scope; recorded for reference only
  sections: ["NEWS", "CTA TTPs", "LATEST ATTACKS OR RISKS", "KEYWORDS"]

  # ---- Staging annotations (Vox Policy §5 and §6.2) ----
  # Advisory only. Nothing here touches the score, the tier, the ordering or
  # the surface-vs-drop decision. These exist so two standards the analyst was
  # expected to remember become visible in the document instead.
  staging_annotations:
    # §6.2 "body, not headline". Below this many words of extracted text there
    # is nothing to write an entry FROM, and the item is marked [NO BODY].
    # 40 words is about two sentences - enough to tell a real article from a
    # feed stub or a failed extraction, low enough not to flag terse advisories.
    min_body_words: 40

    # §5 section suggestion. ORDERED - first match wins, and the last entry is
    # the catch-all. Rules use the same grammar as the scoring above, so a
    # section can be retuned exactly like a tier and the engine stays ignorant
    # of what CTI's sections are. S2 defines its own list in its own pnd.md.
    #
    # KEYWORDS is deliberately NOT here. Policy §5 describes it as wave-top
    # only - vendor and sector names, not items - so it is a summary block the
    # analyst writes, not a destination candidates get assigned to. The
    # compliance report still checks it appears in the edition.
    sections:
      - name: "LATEST ATTACKS OR RISKS"
        when:
          any:
            - {group: exploit_strong, scope: blob}
            - {group: cve, scope: blob}
      - name: "CTA TTPs"
        when: {group: ttp, scope: blob}
      # NEWS twice, deliberately. The first is a POSITIVE match - something
      # happened to somebody - and gets a clean tag. The second is the
      # catch-all and gets the "?" marker, so an item that merely failed to
      # match anything is visibly different from an item that is genuinely a
      # news event. Without the split every NEWS item would carry a "?" and
      # the marker would stop meaning anything.
      - name: "NEWS"
        when: {group: incident_broad, scope: blob}
      - name: "NEWS"
        when: always

    # §8 production gate. The pipeline fills the countable fields of the
    # compliance report; these are the judgments only a person can sign off.
    # Each is a locked standard from the Vox Policy, restated here as a check
    # rather than left for the analyst to recall.
    compliance_checklist:
      - "Every entry written from the article BODY, never the headline (§6.2)."
      - "One event, one entry - same-event reports folded, each event placed once (§7)."
      - "Every entry carries a 'why an SLTT organization should care' clause, framed as vendor accountability, procurement or IG1 controls (§6.3)."
      - "Citations nested per entry, as live links the reader can actually open (§6.5)."
      - "Serious-impact claims verified against a primary or authoritative source; wording does not inflate the source (§7)."
      - "Attribution discipline: suspected is not confirmed; the state of evidence is represented as it stands (§7)."
      - "Out-of-window items either carry a fresh this-week hook or are cut - not silently kept (§7)."
      - "Audience-portfolio filter applied: developer-only and defence-industrial-only items excluded unless they reach SLTT through a vendor (§7)."
      - "Product-specific items are relevant only if this audience uses the product (§7)."
      - "Acronyms spelled out on first use; mechanisms named but translated (§7)."
      - "All four sections present; an empty one says 'none this cycle' rather than being omitted (§5)."
      - "Three dates correct: title = distribution Thursday, ICOD in the header, LTIOV absent (§2)."
      - "Staging draft carries no handling markings (§1)."
      - "Reader-facing heading is 'WCTI - Weekly Cyber Threat Intelligence'; the word 'vox' appears nowhere (§3)."
  deliverable_name: "WCTI_v[YYYYMMDD]"           # 3b output, filename. date = distribution (Thu)
  notes: >
    Staging document and vox are content only, no handling markings, and are
    UNCAPPED - the item count is an output of the scoring and force-surface
    rules, never a target (Vox Policy section 7). The distributed product
    narrows to 5-8 and adds handling markings, and is outside Sanctum's scope.
    KEYWORDS is wave-tops, not items. Three dates on the distribution product:
    title = distribution (Thursday); ICOD line = collection cutoff
    (Wednesday 0400 PT); LTIOV planning-only, never printed.
```

### 3b.2 Vox policy

---

#### 1. What the Vox is (and is not)

- **Is:** a weekly review surface of collected, prioritized open-source cyber threat items for a low-maturity SLTT audience, handed to the cyber team for review and amendment.
- **Is not:** a finished intelligence product. No analytic assessment, no confidence judgments, no handling markings. The cyber team adds assessment and produces the distributed report.
- **Audience:** non-technical SLTT leaders and staff (county/city government, school districts, small utilities). Everything below serves that reader.

#### 2. Cadence & dates

- Collection cutoff / **ICOD** (information current as of): Wednesday 0400 Pacific. The staging document is complete by 0500.
- Produced: Wednesday 0600. Team review: Thursday morning. Distribution: Thursday afternoon.
- **Title date = distribution date (Thursday).** ICOD appears in the header. LTIOV is planning doctrine only — never on the product.

#### 3. Naming

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

#### 4. Header (reader-facing only — no internal plumbing)

The header carries ONLY:
1. Heading: `WCTI — Weekly Cyber Threat Intelligence`
2. Filename + distribution date + ICOD.
3. A one-paragraph summary of what the document is and how it was derived.
4. A short note on the scores.

**Excluded from the header:** internal pipeline artifact paths (e.g., staging-document filenames), internal stage labels, and any Sanctum-internal jargon. A reader who never touches Sanctum should not see machinery.

#### 5. Structure

Fixed sections, in order, each ordered internally by priority:
- **NEWS** — incidents, breaches, advisories, announcements.
- **CTA TTPs** — cyber threat actor tactics/techniques (tradecraft).
- **LATEST ATTACKS OR RISKS** — vulnerabilities and active exploitation.
- **KEYWORDS** — wave-top only (vendor/sector names acceptable; not specific products/malware/techniques).

#### 6. Per-entry format

Each entry has, in order:
1. **ID + headline** (`YYYYMMDD-[A]` sequential).
2. **Body**, written from the article body — never the headline. If the corpus has no usable body on a topic, the item is dropped.
3. **"Why an SLTT organization should care"** clause — mandatory, tied to this audience, framed as vendor accountability / procurement and foundational controls (CIS IG1), not developer-level fixes.
4. **Score** — the pipeline relevance score plus tier and the multipliers behind it. The score orders; it does not measure.
5. **Citations** — nested per entry, as live openable links (outlet, headline, date, URL). Never a link the reader cannot open.
6. **Flags** where needed (verification, review-note, attribution).

#### 7. Content standards (locked)

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

#### 8. Change control

This policy is the authority for the Vox. Format or standard changes originate as a P&D decision, are recorded in the Mandate/lessons log, and only then take effect. Mid-production requests that conflict with this spec are flagged against it, not silently adopted. This is the mechanism that prevents creep.

