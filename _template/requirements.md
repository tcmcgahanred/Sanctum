# [DOMAIN] — Requirements decomposition

*Sanctum · `_template` · Planning & Direction work product.*

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

## Terminology

- **KIQ** — enduring top-level question. Governs collection scope.
- **PIR** — Priority Intelligence Requirement. What the product exists to answer.
- **SIR** — a narrower question decomposing a PIR.
- **EEI** — the specific collectable fact that answers an SIR.

Each EEI carries `[Sensor: … ACTIVE / PARTIAL / PENDING / ABSENT]` and
`[Scoring: …]` and/or `[Standard: …]`.

---

## KIQ-1: [the enduring question]

### PIR-1 — [name]

*[the requirement as a question]*

**SIR-1.1 — [narrower question]**

- **EEI-1.1.a** — [the collectable fact]. `[Sensor: … — PENDING]` `[Scoring: …]`

---

## Byproduct 1 — Sensor-build roadmap

Each pending sensor is the essential means of collecting one or more EEIs.
Priority = how much specificity it unlocks.

1. …

## Byproduct 2 — Coverage-gap finding

**The point of this whole exercise.** Count the EEIs under your highest-priority
requirement that have no active sensor. If most of them are PENDING, the domain
is answering its top requirement by luck, and that is a *collection* problem
that no amount of scoring work will fix.

Ranking and tuning operate only on what already arrived. **They cannot reveal a
requirement nothing is collecting against.** Expect to find at least one.
