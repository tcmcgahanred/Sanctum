# Sanctum — CTI Effort (Effort 1)

*The operational weekly OSINT cyber-threat-intelligence cycle — an example Sanctum domain, tuned for a State/Local/Tribal/Territorial (SLTT) audience across a regional Area of Responsibility (AOR).*

**BLUF:** This folder is a **domain instance** — configuration and outputs, no engine code. The generic engines live in `../core/` and are pointed at this domain with `../run.sh cti`. Everything CTI-specific — requirements, feeds, scoring, vocabulary and the product spec — is in the single `pnd.md`.

## What's here

| File | Role |
|------|------|
| `pnd.md` | **Everything.** The requirements, the sensors, the scoring model, the vocabulary reasoning and the product spec — laid out in the order the intelligence cycle runs them. The engines read only the fenced `yaml` and `sensors` blocks; every other line is for the person reading it. |
| `CHANGELOG.md` | Dated history. Nothing here is operative — it exists so a decision can be traced, not so it has to be re-read before acting. |
| `editions/WCTI_v*.md` | The voxes actually put out, keyed to the distribution date. |

**Merged 2026-09-01.** This folder used to hold five markdown files —
`requirements.md`, `mandate.md`, `vocab.md`, `vox_policy.md` and `pnd.md`. They
are now one, because a fact you have to go and find in another file is a fact
that gets decided wrongly. The parsed config was verified identical across the
merge: same 55 sensors, same scoring model, same vocabulary. **A domain may still
split its files** — `s2` does, and `tools/vocab_check.py` reads either shape.

## How P&D drives the cycle

`pnd.md` is laid out by stage, and each stage owns its config block:

| Stage | Section | What the engine reads |
|---|---|---|
| 1 · Planning & Direction | Stage 1 | `manifest:` — where the corpus lives, where staging goes |
| 2 · Collection | Stage 2 | `manifest.collection:` and the `sensors` feed list |
| 3a · Processing | Stage 3a | `scoring:` — tiers (8/4/2/1), keyword groups, multipliers, the cyber-domain gate — and `vocab:`, the per-group requirement attribution |
| 3b · Exploitation | Stage 3b | `production.report_title` only; the rest of the section is the human standard |

Change what lands first by editing `scoring` — the rationale lives beside the
values, so there is nothing to keep in sync. Change what's collected by editing
the `sensors` block.

## Tuning it for another AOR

This example is tuned for a California SLTT AOR (the `geo` keyword group is California geography). To adapt it to a different region, swap the `geo` group and the AOR-specific sensors in `pnd.md` — the engine and the rest of the doctrine are unchanged.

## Deliverable naming

Two documents, two names, never interchangeable (`pnd.md` §3b.2, the vox policy, §3):

| | Made by | Reader-facing title | Filename |
|---|---|---|---|
| **Staging document** (3a) | `arbites.py` | `WCTI — Staging Document (candidate queue)` | dated by collection day, pushed to the staging store, **not committed** |
| **Vox** (3b) | operator + model | `WCTI — Weekly Cyber Threat Intelligence` | `WCTI_v[YYYYMMDD]`, date = **distribution (Thursday)**, committed to `editions/` |

"Vox" is internal shorthand and never appears in the reader-facing document. No `CCIC` prefix until AOR-direct sensors exist. The `_STAGING` suffix belongs to the 3a document only and must never appear on a vox.
