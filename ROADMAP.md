# Sanctum — Roadmap

Where Sanctum is headed. The apparatus is designed to be run as a real tool, not a one-off — so it is built to decouple cleanly from any particular host and to generalize across domains.

## Domain-agnostic apparatus (realized)

Sanctum is configurable for the domain it supports at **Planning & Direction**, and produces a valuable staging document regardless of domain. The intelligence cycle is domain-neutral: at every stage the split is the same — **domain-specific config riding on a shared engine.** The *what* (requirements, sources, weights) is domain-specific; the *how* (collect, dedupe, score, stage) is shared.

Planning & Direction is the single configuration surface. You set the domain there (mission, information requirements, sensor selection, scoring weights); every downstream stage reads that config:

- **Collection** — the sensors P&D selected.
- **Processing / Exploitation** — score the corpus against the requirements + weights.
- **Analysis & Production** — human gate → staging document.

**Scope boundary:** Sanctum stops at the **staging document** — valuable, requirement-relevant, transparently-scored reports for manual production. It does not build the finished product (a formatted brief, IPB overlays, etc.); that is the part that diverges hardest by domain and stays a human step.

**Success definition (the "keeper test"):**
> A staging document full of valuable, requirement-relevant, transparently-scored reports, ready for manual production — the same sentence whether the domain is CTI or S2; only the requirements and sensors swap.

## Near-term improvements

- **Curated AOR sources** — add reliable regional/official sources to fill local coverage gaps left by dropping noisy keyword feeds.
- **Authoritative breach/early-warning sensors** — e.g. a breach-registry scraper and a ransomware-leak-site aggregator filtered to the AOR. These are what make a domain uniquely valuable.
- **Distribution template** — the presentation/handling layer that turns a staging draft into the finished, marked product.
- Optionally extend the scorer to scaffold a rough draft (reduce the manual tether without adding an API).

## Standalone repo (done)

Sanctum lives in its own repository, independent of any larger lab or environment it happens to run in — so cloning it puts only Sanctum on a host, and history survives any host rebuild.

## Future: dedicated production node (deferred)

Longer term, the collector can move off any shared/experimental host onto a dedicated, hardened, internet-facing production node (a small cloud VM), self-serving or object-storing its corpus, with logs forwarded to monitoring. Treated as a defended asset, never an experiment. Deferred until the effort proves itself a keeper over several real cycles — staying on the current host carries near-zero technical debt (a transient corpus means no data migration; the storage backend is abstracted behind rclone, a one-line switch).

## Corpus bridge

The corpus is transient (a rolling window; it regenerates) and TLP:CLEAR, so secrecy isn't the driver. The storage backend is abstracted (rclone) — Drive today, object storage or a self-served corpus later, decided at migration.
