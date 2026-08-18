# Sanctum — Roadmap

Where Sanctum is headed. The apparatus is designed to be run as a real tool, not a one-off — so it is built to decouple cleanly from any particular host and to generalize across domains.

## Domain-agnostic apparatus (realized)

Sanctum is configurable for the domain it supports at **Planning & Direction**, and produces a valuable staging document regardless of domain. The intelligence cycle is domain-neutral: at every stage the split is the same — **domain-specific config riding on a shared engine.** The *what* (requirements, sources, weights) is domain-specific; the *how* (collect, dedupe, score, stage) is shared.

Planning & Direction is the single configuration surface. You set the domain there (mission, information requirements, sensor selection, scoring weights); every downstream stage reads that config:

- **Collection** — the sensors P&D selected.
- **Processing / Exploitation** — score the corpus against the requirements + weights.
- **Analysis & Production** — human gate → staging document.

**Scope boundary:** Sanctum stops at the **staging document** — valuable, requirement-relevant, transparently-scored reports for manual production. It does not build the finished product (a formatted brief, domain-specific overlays, etc.); that is the part that diverges hardest by domain and stays a human step.

**Success definition (the "keeper test"):**
> A staging document full of valuable, requirement-relevant, transparently-scored reports, ready for manual production — the same sentence whatever the domain; only the requirements and sensors swap.

## Near-term improvements

- **Curated AOR sources** — add reliable regional/official sources to fill local coverage gaps left by dropping noisy keyword feeds.
- **Authoritative breach/early-warning sensors** — e.g. a breach-registry scraper and a ransomware-leak-site aggregator filtered to the AOR. These are what make a domain uniquely valuable.
- **Distribution template** — the presentation/handling layer that turns a vox into the finished, marked product. Outside Sanctum's scope; listed because it is the next thing downstream.
- Optionally extend the scorer to scaffold a rough draft (reduce the manual tether without adding an API).

### Sensor-build roadmap — per domain, derived from requirements

A domain's sensor priorities are not a roadmap item in the abstract; they fall out of decomposing its requirements. Each pending sensor is the essential means of collecting one or more Essential Elements of Information, and the priority order is how much AOR-specificity each one unlocks.

**The CTI domain's ordered list lives in [`cti/decomposition.md`](cti/decomposition.md) — Byproduct 1.** It is not repeated here; a second copy would drift. Summary of where it stands: a prerequisite engine fix (`process_page` re-collection) blocks the top two sensors, both of which are web portals rather than feeds.

### A finding worth carrying across domains

The CTI decomposition surfaced something the scoring model could never have shown:

> **Three of four EEIs under the AOR-direct core of PIR-1 remain PENDING.** The pipeline answers its highest-priority requirement largely by luck — when a statewide query or a national outlet happens to name an in-AOR entity.

So the CTI domain is presently **statewide-and-national collection with AOR-aware scoring, not AOR-specific collection.** That is a *collection* gap, not a scoring gap — scoring has been ready for some time.

**The general lesson:** decomposing requirements to the collectable-fact layer is what makes a coverage gap visible. Ranking, weighting and tuning cannot reveal a requirement that nothing is collecting against — they operate only on what already arrived. Any new domain should expect to find at least one requirement it is answering by accident, and should look for it deliberately.

## Standalone repo (done)

Sanctum lives in its own repository, independent of any larger lab or environment it happens to run in — so cloning it puts only Sanctum on a host, and history survives any host rebuild.

## Future: dedicated production node (deferred)

Longer term, the collector can move off any shared/experimental host onto a dedicated, hardened, internet-facing production node (a small cloud VM), self-serving or object-storing its corpus, with logs forwarded to monitoring. Treated as a defended asset, never an experiment. Deferred until the effort proves itself a keeper over several real cycles — staying on the current host carries low technical debt, since the storage backend is abstracted behind rclone and switching it is close to a one-line change.

**The corpus itself does have to migrate.** An earlier version of this section said it did not, on the grounds that the corpus was transient — see the correction below.

## Corpus bridge

The corpus is **permanent**, and that is load-bearing. `core/lexicanum.py` recomputes matches on demand rather than recording them at collection time, so a vocabulary group invented today can be run against everything collected last year. That property — retroactive analysis, and the ability to re-group a vocabulary later without losing the history — exists **only while the corpus is retained**. Pruning it would silently destroy the capability and would turn vocabulary granularity into a permanent build-time decision. See [`VOCABULARY.md`](VOCABULARY.md) §4 before changing retention.

*Corrected 2026-08-17. This section previously described the corpus as "transient (a rolling window; it regenerates)," which was true of an early design and has not been true for some time. The collection **window** rolls — the corpus does not. The stale wording had propagated into `.gitignore` as well and was corrected there in the same pass.*

The corpus is TLP:CLEAR, so secrecy is not the driver for where it lives. The storage backend is abstracted (rclone) — Drive today, object storage or a self-served corpus later, decided at migration.
