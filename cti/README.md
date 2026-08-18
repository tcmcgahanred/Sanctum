# Sanctum — CTI Effort (Effort 1)

*The operational weekly OSINT cyber-threat-intelligence cycle — an example Sanctum domain, tuned for a State/Local/Tribal/Territorial (SLTT) audience across a regional Area of Responsibility (AOR).*

**BLUF:** This folder is a **domain instance** — configuration and outputs, no engine code. The generic engines live in `../core/` and are pointed at this domain with `../run.sh cti`. Everything CTI-specific — feeds included — is in the single `pnd.md`.

## What's here

| File | Role |
|------|------|
| `pnd.md` | **Planning & Direction** — the single config file the engines read: `manifest` + the `sensors` feed list + `scoring` model + `production`. Config is in fenced blocks; prose is for humans. |
| `codex.md` | Intelligence requirements & doctrine (prose). Documents what `pnd.md`'s scoring block encodes (KIQ / PIRs / scoring / cut doctrine). |
| `decomposition.md` | **PIR → SIR → EEI decomposition.** Every EEI mapped to the sensor that collects it and the scoring signal that weights it. Drives the sensor-build roadmap and the rationale for each signal. **Requirements changes start here**, then the config, then the Codex. |
| `mandate.md` | Standing planning & direction record (directives + lessons log) — and the per-domain status/backlog tracker. |
| `editions/vox_v*.md` | The brief (Vox) — keyed to the distribution date. |

## How P&D drives the cycle

`pnd.md` holds the config blocks, one per working stage:

- **`manifest`** → Collection: where the corpus lives, the feed list, the collection window.
- **`scoring`** → Processing & Exploitation: tiers (8/4/2/1), keyword groups, elevation multipliers, and the "geo-subject-of-an-incident" rule — all as data.
- **`production`** → Analysis & Production: the staging report title, section taxonomy, and the 5–8 item target.

Change what lands first by editing `scoring` in `pnd.md` (keep `codex.md`'s prose in sync). Change what's collected by editing the `sensors` block in `pnd.md`.

## Tuning it for another AOR

This example is tuned for a California SLTT AOR (the `geo` keyword group is California geography). To adapt it to a different region, swap the `geo` group and the AOR-specific sensors in `pnd.md` — the engine and the rest of the doctrine are unchanged.

## Deliverable naming

Two documents, two names, never interchangeable (Vox Policy §3):

| | Made by | Reader-facing title | Filename |
|---|---|---|---|
| **Staging document** (3a) | `arbites.py` | `WCTI — Staging Document (candidate queue)` | dated by collection day, pushed to the staging store, **not committed** |
| **Vox** (3b) | operator + model | `WCTI — Weekly Cyber Threat Intelligence` | `WCTI_v[YYYYMMDD]`, date = **distribution (Thursday)**, committed to `editions/` |

"Vox" is internal shorthand and never appears in the reader-facing document. No `CCIC` prefix until AOR-direct sensors exist. The `_STAGING` suffix belongs to the 3a document only and must never appear on a vox.
