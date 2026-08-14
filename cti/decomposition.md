# Sanctum CTI — Intelligence Requirements Decomposition (PIR → SIR → EEI)

*Sanctum · CTI · Planning & Direction work product. Statuses current as of 2026-08-11.*

Decomposes the standing PIRs into Specific Intelligence Requirements (SIRs) and Essential Elements of Information (EEIs), and maps each EEI to the sensor that collects it and the scoring signal that weights it. Scope is deliberately capped at the EEI layer — this is a solo weekly OSINT effort, not a full collection-management plan. The purpose is two concrete outputs: (1) a prioritized sensor-build roadmap, and (2) documented rationale for every scoring signal.

**Where this sits.** `codex.md` Layers 1–2 own the KIQ and PIR wording — they are restated here only as tree roots, not maintained in two places. This file owns the SIR and EEI layers. `pnd.md` is the implementation. **When requirements shift, revise here first, then update the config, then the Codex.** Do not maintain a second copy of the scoring signals — the EEI layer drives the config, it does not duplicate it.

## Terminology

- **KIQ** — Key Intelligence Question. Enduring, top-level. Governs collection scope.
- **PIR** — Priority Intelligence Requirement. What the brief exists to answer.
- **SIR** — Specific Intelligence Requirement. A narrower question that decomposes a PIR.
- **EEI** — Essential Element of Information. The specific collectable fact that answers an SIR.
- Each EEI carries `[Sensor: …]` (what collects it; **ACTIVE / PARTIAL / PENDING / ABSENT**) and `[Scoring: …]` (how it is weighted) and/or `[Standard: …]` (a production rule governing it).

---

## KIQ-1: What cyber threats endanger California SLTT organizations and the critical infrastructure they operate or depend on?

### PIR-1 — Direct impact to California organizations

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

### PIR-2 — SLTT sector targeting anywhere (leading indicator)

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

### PIR-3 — Actively-exploited vulnerabilities in SLTT-common technology

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

### PIR-4 — Broad/national threats with SLTT relevance

*What national-scale threats carry material relevance to SLTT defenders?*

**SIR-4.1 — What national-scale threats materially affect SLTT defenders?**

- **EEI-4.1.a** — National advisories/campaigns with an SLTT nexus. `[Sensor: national feeds — **ACTIVE**]` `[Scoring: Tier-4]`
- **EEI-4.1.b** — Audience-portfolio relevance filter: does it reach the SLTT audience, or is it developer-only / defense-industrial-only / vendor-opinion? `[Standard: audience filter — developer-targeted (e.g., npm poisoning) and defense-industrial-base (e.g., CMMC) items are out-of-portfolio unless they reach SLTT through a vendor]`

---

## Byproduct 1 — Sensor-build roadmap (prioritized)

Each pending sensor is the essential means of collecting one or more EEIs. Priority = how much AOR-specificity it unlocks.

0. **Fix `process_page` re-collection** (`core/acolyte.py:114`) — **prerequisite, not a sensor.** Page-type sources are deduped on URL hash, so a portal is captured once and never revisited. Both of the next two items are portals and are useless until this lands.
1. **CA AG breach-registry scraper** — serves EEI-1.1.a. The single highest-value build: the only authoritative, AOR-direct breach sensor. PIR-1 has almost no active collection without it.
2. **Cal-CSIC advisories** — serves EEI-1.1.d. Confirmed alive and publishing through Aug 2026. Extracting the index page may yield enough, since titles and dates are what the scorer consumes — prove that before building PDF parsing.
3. **Ransomware leak-site aggregator, CA-filtered** — serves EEI-1.1.b. Early-warning AOR-direct (victims appear before local press).
4. **CISA KEV as a primary feed** — serves EEI-3.1.a. Currently absent; reduces single-aggregator dependence. Cheapest item on this list.
5. **Curated CA regional press** — serves EEI-1.1.c. Still unserved; StateScoop does not cover it.
6. **Remaining sector trade press** (K-12 Dive, WaterISAC) — serves EEI-2.1.a/b.

~~Curated official CA feeds (Cal OES, CDT, MS-ISAC)~~ — **DONE 2026-08-11.**

## Byproduct 2 — Coverage-gap finding

Decomposition makes the gap explicit: **three of four EEIs under SIR-1.1 — the AOR-direct core of PIR-1 — remain PENDING.** (EEI-1.1.d was closed 2026-08-11.) The pipeline answers PIR-1 largely by luck: when a statewide query or national outlet happens to name a California entity.

Therefore the CTI domain is presently **California-statewide-and-national collection with AOR-aware scoring, not AOR-specific collection.** Closing this gap is a collection problem (build the SIR-1.1 sensors), not a scoring problem — scoring is ready and has been.

## Byproduct 3 — Production standards captured (from analyst-gate feedback)

The decomposition absorbs cyber-team lessons as EEI-level standards, so they persist as doctrine rather than one-off edits:

- **Anti-FUD verification** (EEI-1.3.a): verify specific impact claims (e.g., a 911 outage) against a primary source; soften or cut what can't be confirmed.
- **Attribution discipline** (EEI-1.3.b): suspected ≠ confirmed; never state suspected attribution as fact.
- **Provider-dependent relevance** (EEI-3.2.b): product-specific items are relevant only if the audience uses the affected product/provider.
- **Audience-portfolio filter** (EEI-4.1.b): topicality ≠ relevance; developer-only and defense-industrial-only items are out of portfolio.
