# S2 — Requirements decomposition

*Sanctum · `s2` · Planning & Direction work product.*

Decomposes the standing requirements into narrower questions and then into the
specific collectable facts that answer them, mapping each to the sensor that
collects it and the scoring signal that weights it.

**Two concrete outputs, and they are the reason to do this at all:** a
prioritised sensor-build roadmap, and a documented rationale for every scoring
signal.

**Where this sits.** This file owns the WHOLE tree — KIQ, PIRs, SIRs, EEIs.
`pnd.md` is the implementation and owns every number, term and threshold;
**nothing here restates one.** **When requirements shift, revise here first,
then the config.**

**Version:** v1 — established 2026-08-17.

## Terminology

- **KIQ** — enduring top-level question. Governs collection scope.
- **PIR** — Priority Intelligence Requirement. What the product exists to answer.
- **SIR** — a narrower question decomposing a PIR.
- **EEI** — the specific collectable fact that answers an SIR.

Each EEI carries `[Sensor: … ACTIVE / PARTIAL / PENDING / ABSENT]` and
`[Scoring: …]` and/or `[Standard: …]`.

**Method note.** Decomposition was requirement-driven. Sensor coverage was
tagged as a **second pass**, after the tree existed — deliberately, so that
coverage gaps would surface rather than be designed around. Every sensor in this
domain is the same type (open web feed), so the tag records *whether anything
collected reports that fact*, not which sensor owns it.

**Scope note.** The reader is the S2 section of a combat aviation brigade,
working strategic-to-operational. Tactical-level detail is explicitly lower
value. EEIs are written at the echelon the reader works at.

---

## KIQ-1: What risks and threats should the brigade be aware of to prepare for war in the INDOPACOM area of responsibility?

---

### PIR-1 — Adversary posture and activity in the AOR

*What shifts in adversary posture or activity have occurred in the AOR?*

**Rank 1 of 4.** Housed in Tier 1 — the only tier requiring both AOR geography
and rotary-wing relevance.

**SIR-1.1 — What forces or systems have moved into, out of, or within the AOR?**

- **EEI-1.1.a** — A named unit or weapon system arrives at, or departs from, a
  named location in the AOR. `[Sensor: primary-source + imagery-derived analysis
  — PARTIAL]` `[Scoring: Tier 1 — adversary term in proximity to a geography
  term plus event word]`
- **EEI-1.1.b** — A change in permanent basing, garrison, or theatre command
  laydown. `[Sensor: official + trade press — PARTIAL]` `[Scoring: Tier 1]`
- **EEI-1.1.c** — Naval or air movement through a named strait or chokepoint.
  `[Sensor: maritime sector press — ACTIVE]` `[Scoring: Tier 1 × chokepoint
  multiplier]`
- **EEI-1.1.d** — Aviation units specifically — rotary-wing or counter-air
  formations — relocating within the AOR. `[Sensor: — ABSENT]` `[Scoring:
  Tier 1]`

**SIR-1.2 — What activity indicates a change in readiness?**

- **EEI-1.2.a** — An exercise is announced or observed, with scale, participants,
  and location. `[Sensor: official + wire — PARTIAL]` `[Scoring: Tier 1 ×
  escalation multiplier]`
- **EEI-1.2.b** — Mobilisation, reserve call-up, or conscription change.
  `[Sensor: primary-source — PARTIAL]` `[Scoring: Tier 1 × escalation]`
- **EEI-1.2.c** — A snap or no-notice exercise, or an exercise conducted outside
  its normal season. `[Sensor: — ABSENT]` `[Scoring: Tier 1 × escalation ×
  fixed-date window]`
- **EEI-1.2.d** — Evacuation of nationals, or advisories issued to shipping or
  aviation. `[Sensor: wire — PARTIAL]` `[Scoring: Tier 1 × escalation]`

**SIR-1.3 — What has the adversary declared?**

- **EEI-1.3.a** — A ministry, spokesman, or named leader states an intention,
  threat, warning, or red line. `[Sensor: adversary primary-source — PARTIAL]`
  `[Scoring: any tier × declared intent]`
- **EEI-1.3.b** — Publication of doctrine, a white paper, or a defence budget
  with stated priorities. `[Sensor: primary-source + analysis — PARTIAL]`
  `[Scoring: Tier 1]`

**SIR-1.4 — What infrastructure change enables future operations?**

- **EEI-1.4.a** — Airfield construction, expansion, hardening, or shelter
  building at a named AOR site. `[Sensor: imagery-derived analysis — PARTIAL]`
  `[Scoring: Tier 1]`
- **EEI-1.4.b** — New or expanded fuel, munitions, or logistics storage
  supporting air operations. `[Sensor: — ABSENT]` `[Scoring: Tier 1]`

---

### PIR-2 — Environmental and basing factors degrading rotary-wing operations

*What conditions in the AOR would degrade our ability to fly, sustain, or base
rotary-wing aircraft?*

**Rank 2 of 4.** Housed in Tier 3 as an alternate branch. **This is the
requirement with the worst coverage in the domain — see Byproduct 2.**

**SIR-2.1 — What environmental conditions degrade aircraft performance or availability?**

- **EEI-2.1.a** — Documented corrosion, salt, or humidity effects on rotorcraft
  at Pacific sites. `[Sensor: — ABSENT]` `[Scoring: Tier 3 environmental branch]`
- **EEI-2.1.b** — Density altitude, heat, or humidity conditions affecting lift
  margin or payload at named locations. `[Sensor: — ABSENT]` `[Scoring: Tier 3]`
- **EEI-2.1.c** — Seasonal patterns — typhoon season, monsoon — that constrain
  flight operations in the AOR. `[Sensor: — ABSENT]` `[Scoring: Tier 3]`
- **EEI-2.1.d** — Volcanic ash, dust, or brownout conditions affecting engines
  or visibility. `[Sensor: — ABSENT]` `[Scoring: Tier 3]`

**SIR-2.2 — What basing constraints affect employment?**

- **EEI-2.2.a** — Condition, capacity, or availability of airfields and
  potential FARP sites in the AOR. `[Sensor: — ABSENT]` `[Scoring: Tier 3]`
- **EEI-2.2.b** — Access agreements, rotational basing, or host-nation basing
  changes. `[Sensor: wire + trade press — PARTIAL]` `[Scoring: Tier 3]`
- **EEI-2.2.c** — Sustainment distance, resupply constraint, or logistics
  vulnerability affecting aviation units. `[Sensor: — ABSENT]` `[Scoring: Tier 3]`
- **EEI-2.2.d** — Dispersed or austere basing concepts being tested or adopted.
  `[Sensor: trade press — PARTIAL]` `[Scoring: Tier 3]`

**SIR-2.3 — What has degraded existing infrastructure?**

- **EEI-2.3.a** — Storm, seismic, or flood damage to an airfield or port in the
  AOR. `[Sensor: wire — PARTIAL]` `[Scoring: Tier 3]`

---

### PIR-3 — What current conflicts show about rotary-wing survivability and employment

*What are helicopters in active conflicts teaching us about how they survive and
how they are being used?*

**Rank 3 of 4.** Housed in Tier 3. Relevant by analogy — no adversary of ours
and no part of our theatre required.

**SIR-3.1 — How are rotary-wing aircraft being lost?**

- **EEI-3.1.a** — A confirmed rotary-wing loss with the engaging system
  identified. `[Sensor: conflict OSINT + wire — PARTIAL]` `[Scoring: Tier 3]`
- **EEI-3.1.b** — The phase of mission at which the aircraft was engaged —
  ingress, hover, landing, egress. `[Sensor: — ABSENT]` `[Scoring: Tier 3]`
- **EEI-3.1.c** — Countermeasure or survivability equipment performance, success
  or failure. `[Sensor: — ABSENT]` `[Scoring: Tier 3]`
- **EEI-3.1.d** — Losses attributed to small arms or unguided fire rather than
  guided systems. `[Sensor: conflict OSINT — PARTIAL]` `[Scoring: Tier 3]`

**SIR-3.2 — How is rotary wing being employed successfully?**

- **EEI-3.2.a** — Adaptation in tactics — terrain flight, standoff launch, night
  employment, decoys. `[Sensor: — ABSENT]` `[Scoring: Tier 3]`
- **EEI-3.2.b** — Mission profiles being flown, and which are being abandoned as
  unsurvivable. `[Sensor: — ABSENT]` `[Scoring: Tier 3]`
- **EEI-3.2.c** — Manned–unmanned teaming employed in an active conflict.
  `[Sensor: trade press — PARTIAL]` `[Scoring: Tier 3]`

**SIR-3.3 — What is threatening aircraft that are not flying?**

- **EEI-3.3.a** — A strike on an airfield, FARP, or assembly area holding
  aircraft. `[Sensor: wire + conflict OSINT — PARTIAL]` `[Scoring: Tier 3]`
- **EEI-3.3.b** — Loitering munition or FPV employment against parked or
  taxiing aircraft. `[Sensor: conflict OSINT — PARTIAL]` `[Scoring: Tier 3 ×
  first-occurrence]`
- **EEI-3.3.c** — Deep strike against aviation infrastructure well behind the
  line of contact. `[Sensor: wire — PARTIAL]` `[Scoring: Tier 3]`

---

### PIR-4 — Adversary capabilities that specifically threaten rotary-wing operations

*What can the adversary field that would kill or degrade our helicopters?*

**Rank 4 of 4.** Housed in Tier 2 — platform-anchored, not theatre-anchored.
Deliberately global: a system that kills someone else's helicopters today is a
system that kills ours later.

**SIR-4.1 — What systems have entered or are entering service?**

- **EEI-4.1.a** — A counter-air system moves from development to fielding or
  operational status. `[Sensor: trade press + imagery-derived — PARTIAL]`
  `[Scoring: Tier 2 × first-occurrence]`
- **EEI-4.1.b** — First public appearance, unveiling, or parade display of a
  counter-air system. `[Sensor: imagery-derived + primary-source — PARTIAL]`
  `[Scoring: Tier 2 × first-occurrence]`
- **EEI-4.1.c** — A system enters service with a unit type that would engage
  Army aviation specifically. `[Sensor: — ABSENT]` `[Scoring: Tier 2]`

**SIR-4.2 — What capability has been demonstrated?**

- **EEI-4.2.a** — A test or live-fire event with stated range, altitude, or
  engagement performance. `[Sensor: primary-source + trade press — PARTIAL]`
  `[Scoring: Tier 2 × first-occurrence]`
- **EEI-4.2.b** — Combat employment of a counter-air system against any
  rotary-wing target. `[Sensor: conflict OSINT — PARTIAL]` `[Scoring: Tier 2 or
  Tier 3, whichever is higher]`
- **EEI-4.2.c** — A capability claim that exceeds what the system was previously
  credited with. `[Sensor: analysis — PARTIAL]` `[Scoring: Tier 2 ×
  first-occurrence]`

**SIR-4.3 — Where are these systems proliferating?**

- **EEI-4.3.a** — Export, transfer, or licensed production of a counter-air
  system to a state in or adjacent to the AOR. `[Sensor: trade press — PARTIAL]`
  `[Scoring: Tier 2, Tier 1 if the recipient is in the AOR]`
- **EEI-4.3.b** — Recurrence of a specific system in a specific area across
  multiple reports over time. `[Sensor: no feed can serve this — ABSENT]`
  `[Scoring: not expressible in per-item scoring — see Finding 1]`
- **EEI-4.3.c** — A system appearing with a non-state or irregular actor.
  `[Sensor: conflict OSINT — PARTIAL]` `[Scoring: Tier 2]`

**SIR-4.4 — What integration multiplies these capabilities?**

- **EEI-4.4.a** — Air defence networking, sensor fusion, or IADS integration
  reporting. `[Sensor: analysis — PARTIAL]` `[Scoring: Tier 2]`
- **EEI-4.4.b** — Electronic warfare, GPS denial, or spoofing capability
  affecting aviation navigation or datalinks. `[Sensor: trade press + analysis —
  PARTIAL]` `[Scoring: Tier 2]`
- **EEI-4.4.c** — Counter-UAS capability that would defeat organic unmanned
  systems. `[Sensor: trade press — PARTIAL]` `[Scoring: Tier 2]`

---

## Byproduct 1 — Sensor-build roadmap

Each pending sensor is the essential means of collecting one or more EEIs.
Priority = how much specificity it unlocks.

**1. Aviation professional and doctrinal press.**
Unlocks the largest block of ABSENT EEIs in the domain — EEI-2.1.a through
2.1.d, 2.2.a, 2.2.c, 3.1.b, 3.1.c, 3.2.a, 3.2.b. These facts are discussed in
aviation professional literature and almost nowhere in general defence press.
**Highest priority: it is the only route to PIR-2 and to the analytical half of
PIR-3.**

**2. Conflict OSINT — loss documentation.**
Unlocks EEI-3.1.a, 3.1.d, 3.3.b, 4.2.b, 4.3.c. Mainstream defence press reports
rotary-wing losses patchily and without the engaging system. Documentation
accounts do it systematically.

**3. Adversary primary-source feeds — specific outlets, not the category.**
The declared-intent multiplier is the strongest signal in the config and
depends entirely on EEI-1.3.a. Western press reports declarations second-hand,
selectively, and late.

**4. Host-nation and regional press within the AOR.**
Unlocks EEI-2.2.b, 2.3.a, and improves 1.1.a. Basing access and infrastructure
damage are reported locally well before they reach wire services.

**5. Environmental and meteorological sources for the AOR.**
Unlocks EEI-2.1.c and supports 2.1.b. Likely requires structured data rather
than a feed — see Finding 2.

**6. Imagery-derived analysis.**
Already PARTIAL through one sensor. Broadening it improves EEI-1.1.a, 1.4.a,
and 4.1.b — the facts that are visible before they are announced.

---

## Byproduct 2 — Coverage-gap finding

**The point of this whole exercise.** Count the EEIs under your highest-priority
requirement that have no active sensor.

| PIR | Rank | EEIs | ACTIVE | PARTIAL | ABSENT |
|---|---|---|---|---|---|
| **PIR-1** — Adversary posture in AOR | 1 | 12 | 1 | 8 | 3 |
| **PIR-2** — Environmental and basing | 2 | 9 | 0 | 3 | 6 |
| **PIR-3** — Lessons from current conflicts | 3 | 10 | 0 | 6 | 4 |
| **PIR-4** — Capabilities threatening rotary wing | 4 | 12 | 0 | 10 | 2 |
| **Total** | | **43** | **1** | **27** | **15** |

### Finding: one EEI in the entire domain has confident coverage.

Of forty-three collectable facts, exactly one is ACTIVE. Twenty-seven are
PARTIAL — meaning something in the sensor set would probably report the fact,
sometimes, without reliability. Fifteen have no coverage at all.

### Finding: PIR-2 is effectively uncollected.

**Six of nine EEIs are ABSENT and none are ACTIVE.** This is the second-ranked
requirement in the domain. Every EEI concerning environmental degradation of
aircraft — corrosion, density altitude, seasonal constraint, brownout — has no
sensor. The three PARTIALs are basing-access and storm-damage items that arrive
incidentally through general news, not because anything is collecting against
the requirement.

The tiering work already placed PIR-2 in Tier 3 deliberately, and that decision
stands. **But no tier weight can rank an item that was never collected.** This
requirement is currently answered by luck.

### Finding: PIR-3's analytical half is missing.

The *facts* of rotary-wing losses are PARTIAL — reported, inconsistently. The
*lessons* are ABSENT: phase of mission, countermeasure performance, tactical
adaptation, which mission profiles have been abandoned. The reader's stated
purpose is not being surprised, and the surprise-preventing content is precisely
the analytical layer nothing collects.

### Finding: PIR-4 is the healthiest requirement and it is ranked last.

Ten of twelve EEIs are PARTIAL, the best coverage in the domain, because
defence trade press exists to report exactly this. Worth noting the inversion:
**coverage is strongest where the requirement ranks lowest.**

### Assessment

**This is a collection problem, not a scoring problem.** Ranking and tuning
operate only on what already arrived — they cannot reveal a requirement nothing
is collecting against. The scoring model built in Parts 3 and 4 is sound and
will order well whatever arrives. It will not fill these gaps, and no amount of
vocabulary work will either.

**The sensor roadmap above is the real remaining work in this domain.**

---

## Open findings

### Finding 1 — Recurrence is not expressible in per-item scoring

**Severity: medium. Unresolved.**

EEI-4.3.b asks whether a system recurs in an area across multiple reports. That
is a longitudinal question. Scoring is per-item and per-cycle, with no memory
that a term's frequency is rising. The corpus supports the analysis because it
is permanent; the tooling does not perform it.

Raised with the Sanctum session as a capability request. Until it exists, this
EEI is answered by an analyst reading across editions, not by the system.

### Finding 2 — Some EEIs may not be feed-shaped at all

**Severity: medium. Unresolved.**

Several ABSENT EEIs under PIR-2 describe conditions rather than events —
density altitude at a site, seasonal patterns, airfield capacity. These are
reference data, not news. A feed may be the wrong instrument, and the honest
answer may be that this requirement is served by a different product entirely.

Recording rather than fixing: whether to build a sensor, accept the gap, or
answer the requirement outside Sanctum is a Planning & Direction call.

### Finding 3 — Coverage tags are estimates, not measurements

**Severity: low. Unresolved.**

Every ACTIVE / PARTIAL / ABSENT tag above is reasoned from what the sensor set
is expected to carry. None has been tested against collected output. Re-tag
after three cycles against what actually arrived; expect several PARTIALs to
resolve to ABSENT.
