# Changelog — Sanctum

Notable changes to the Sanctum intelligence apparatus. **Git is the source of truth**; this file is the curated-highlights layer and `git log` is the full record. Brief editions (Vox) are keyed by distribution date (`vYYYYMMDD`), separate from code versioning.

## Initial release

A domain-agnostic OSINT collection-and-triage apparatus.

- **Domain-agnostic engine.** All logic lives in `core/` (`acolyte` collector, `arbites` scorer, `rules` matcher/scorer, `pnd` config loader). The engines hold no domain knowledge; each domain supplies a single `pnd.md` (manifest + sensors + scoring + production).
- **Collector (Acolyte).** RSS/Atom + page collection, full-text extraction (trafilatura), URL-hash **and** normalized-title deduplication, dated JSON corpus, push to a corpus store via rclone. Runs unattended on a systemd timer.
- **Pre-filter / scorer (Arbites).** Config-driven multiplicative scoring (tier weights × elevation multipliers) with a wide cut (~55 surfaced), a mandatory drop list, and visible per-item reasoning. No API — local scoring only.
- **Recency gate.** Flags items whose *publication* date falls outside the cycle window as "STALE — confirm current hook"; never drops them (preserves legitimately-current re-emergences).
- **Single-file P&D.** A domain's entire configuration — feeds, scoring model, output shape — lives in one `pnd.md`. Adding a domain is: drop in `<domain>/pnd.md` and run `run.sh <domain>`.
- **CTI effort (operational).** An SLTT cyber-threat-intelligence cycle: ~49 trusted national/sector feeds, a convergence-based scoring model, and a staged weekly brief. Tuned as an example for a California SLTT AOR.
- **S2 effort (stub).** An IPB-flavored P&D template, pre-wired for a future aviation-intelligence domain.
- **Verification.** A parity test proves the config-driven scorer reproduces the original hardcoded logic exactly; a recency test covers the publish-date gate.
