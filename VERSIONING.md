# Versioning

**Git is the source of truth.** From the first commit forward, commit history is authoritative. No hand-maintained version numbers, no per-file changelogs. `CHANGELOG.md` is the curated-highlights layer; `git log` is the full record.

## Minimal artifact header

Each code/doc artifact carries one header line with a one-time starting-version anchor. After that, versioning flows through Git — the anchor is never hand-incremented.

```
Sanctum · Arbites · v0.4 (starting anchor; history via git)
```

- In `.py` files: a top comment line.
- In `.md` files: an italic line under the title.
- In `.drawio`: a note element on the canvas or a comment in the XML.

## Starting-version anchors (applied at first commit)

Best-effort anchors reflecting work done to date — approximations, not exact revision counts. Git is exact from here.

| Artifact | Start version | Basis |
|----------|---------------|-------|
| **Acolyte** (`acolyte.py`) | **v1.1** | Operational before this effort (URL-hash dedup, deployed); +1 feature this session (title-dedup). |
| **Arbites** (`arbites.py`) | **v0.4** | Built this session; +3 real tuning revisions on live corpus. Pre-1.0 until a full production cycle. |
| **Requirements** (`requirements.md`) | **v1.0** | Was `decomposition.md` + `codex.md` Layers 1-2. Consolidated 2026-08-17; `codex.md` retired, its scoring rationale moved into `pnd.md`. |
| **Cogitator** (`cogitator.drawio`) | **v0.5** | Built this session; ~4 updates (stage insertion, status, backlog, review integration). |
| **Mandate** (`mandate.md`) | **v1.0** | Standing planning & direction record; consolidated this session. |
| **Vox** editions | **publish-date keyed** | `vYYYYMMDD` is *product-edition* versioning, keyed to the distribution (Thursday) date, separate from code versioning. |

The first commit applies these anchors; Git carries versioning forward. Anchors are applied to each artifact's header **as it is imported** into this tree.

**Note:** Acolyte and Arbites are the domain-agnostic engines in `core/` (`core/acolyte.py`, `core/arbites.py`, plus `core/rules.py` and `core/pnd.py`); the domain-specific scoring model lives as data in each `<domain>/pnd.md`. `run.sh` is the domain dispatcher (`run.sh <domain>`). Behavior is covered by `tests/diff_scores.py`.
