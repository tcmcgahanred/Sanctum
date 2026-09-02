# Sanctum — CTI Effort (Effort 1)

*The operational weekly OSINT cyber-threat-intelligence cycle — an example Sanctum domain, tuned for a State/Local/Tribal/Territorial (SLTT) audience across a regional Area of Responsibility (AOR).*

**BLUF:** This folder is a **domain instance** — configuration and outputs, no engine code. The generic engines live in `../core/` and are pointed at this domain with `../run.sh cti`. Everything CTI-specific — requirements, feeds, scoring, vocabulary and the product spec — is in the single `pnd.yaml`.

## What's here

| File | Role |
|------|------|
| `pnd.yaml` | **Everything the cycle needs.** Requirements, sensors, scoring model, vocabulary and the product standard, in the order the intelligence cycle runs them. Configuration and comments only — a comment says what BREAKS if you change the value it sits on. |
| `CHANGELOG.md` | Dated history, and the reasoning behind every value. Nothing here is operative — it exists so a decision can be traced, not so it has to be re-read before acting. |
| `editions/WCTI_v*.md` | The voxes actually put out, keyed to the distribution date. |

**Converted 2026-09-01.** This folder used to hold five markdown files. They
are now one yaml file, because a fact you have to go and find in another file is
a fact that gets decided wrongly — and because a structure you fill in is a
template, while prose you imitate is a writing assignment. The parsed config was
verified identical across the conversion: same 55 sensors, same scoring model,
same 16 vocabulary groups, and 486 articles scored with zero differences.

Prose lives in two places and neither is here: **`README.md`** for anything a
person reads start to finish, and **`CHANGELOG.md`** for why a value is what it
is. A comment in `pnd.yaml` says only what breaks if you change the line it sits
on.

**A domain may still ship `pnd.md`** — `s2` does. The loader prefers `pnd.yaml`
and falls back, so a domain converts when it is ready and not before.

## How P&D drives the cycle

`pnd.md` is laid out by stage, and each stage owns its config block:

| Stage | Banner in `pnd.yaml` | The block it owns |
|---|---|---|
| 1 · Planning & Direction | `STAGE 1` | `requirements:` — KIQ / PIR / SIR / EEI, and the sensor roadmap. Then `manifest:` runtime and storage |
| 2 · Collection | `STAGE 2` | `manifest.collection:` and `manifest.sensors:` — 55 feed records |
| 3a · Processing | `STAGE 3a` | `scoring:` — tiers (8/4/2/1), keyword groups, multipliers, the cyber-domain gate — and `vocab:`, the per-group requirement attribution |
| 3b · Exploitation | `STAGE 3b` | `production:` — only `report_title` is read by an engine; the rest is the standard the analyst and the model are held to |

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
