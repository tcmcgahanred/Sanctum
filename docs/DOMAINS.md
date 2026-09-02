# Domains — what a domain folder contains and who owns what

*Sanctum · domain-agnostic*

**BLUF:** The engine requires exactly **one** file from a domain: `<domain>/pnd.md`.
Everything else is doctrine and work product, and until now nothing said what
those should be. This file is that contract. It also fixes the more damaging
gap — **which document owns which fact**, so the same number does not live in two
places and go stale in one of them.

---

## Why this exists

`cti/` was the first domain, and its folder is not a template — it is one
domain's history. Files accreted as the effort was worked. A second domain
starting from it would copy the accidents along with the design, and a person
creating a domain from scratch has no idea what is required, what is expected,
and what is CTI's own business.

The engine has been genuinely domain-agnostic for some time. **The gap was never
in the code; it was that nothing told a human what to build.**

---

## What the engine actually requires

One file.

```
<domain>/pnd.md
```

`../core/pnd.py` reads it, validates it, and resolves every runtime path from it.
Nothing in `../core/` opens any other file in a domain folder. That is the whole
machine contract, and it is deliberately that small — see tenet 2.

Everything below is a **human** contract. It exists because a domain that only
satisfies the machine is one nobody can maintain.

---

## The folder contract

| File | Status | What it is |
|---|---|---|
| `pnd.md` | **REQUIRED** | Planning & Direction. Manifest, sensors, scoring model, production block. The only file the engine reads. |
> **One file or several — the engine does not care.** Added 2026-09-01, when
> `cti` merged its five markdown files into one `pnd.md` laid out by
> intelligence-cycle stage. The loader reads every fenced `yaml` block in
> `pnd.md` and deep-merges them, so `manifest:` may legitimately appear twice;
> `tools/vocab_check.py` looks for the `vocab:` block and the requirements tree
> in the split files first and falls back to `pnd.md`. The table below describes
> the SPLIT shape, which `s2` still uses and which remains a valid choice. What
> is not a valid choice is the same fact written in two places.

| `vocab.md` | **EXPECTED** | The reasoning behind the word lists — collisions, dropped terms, per-group review dates, known gaps. Never the terms themselves. See `VOCABULARY.md`. |
| `README.md` | **EXPECTED** | What this domain is, who it serves, how to run it, how to adapt it. |
| `requirements.md` | **EXPECTED** | The whole requirements tree — KIQ → PIR → SIR → EEI — each collectable fact mapped to the sensor that serves it. **This is the file that makes a coverage gap visible** — see below. Owns no numbers. |
| `mandate.md` | **EXPECTED** | Standing operating directives plus the dated lessons log. The continuity mechanism: a fresh session handed this can run the cycle. |
| `policy.md` | **EXPECTED** | The product specification — format, structure, locked content standards. CTI's is `vox_policy.md`. A domain can run without one; it just means the vox's standards live in someone's head instead of in git. |
| `editions/` | **REQUIRED once the domain produces its first vox** | The committed record of what was actually put out, and the only way to answer "what did we say in August?" a year later. |
| `references/` | **LOCAL ONLY** | Working notes, feed candidate lists. Git-ignored by pattern — these carry host and internal detail. |

**A domain with only `pnd.md` runs.** It is not wrong, it is just undocumented,
and the first person to inherit it — including you in six months — pays for that.

**Every domain ends at a vox.** That is tenet 9 and it is not a per-domain
choice. A domain is not "done" at the staging document — the staging document is
a machine artifact, reproducible from the corpus, and it is not committed. The
vox is the deliverable, it is human-made, and it is what `editions/` records.
What happens to the vox afterward — assessment, formatting, distribution — is
stages 4 to 6 and is nobody's business here, in every domain equally.

### Why this file is the one that finds the gaps

Decomposing requirements down to the specific collectable fact is what makes a
coverage gap visible. Ranking, weighting and tuning cannot reveal a requirement
that nothing is collecting against — they operate only on what already arrived.

The CTI domain found this the hard way. Three of the four collectable facts under
its highest-priority requirement had no sensor at all, so the pipeline was
answering that requirement largely by luck: whenever a broad query or a national
outlet happened to name an in-area organisation. Scoring had been ready for
months; collection was the ceiling, and nothing in the scoring model could have
shown that.

**Any new subject should expect to find at least one requirement it is answering
by accident, and should go looking for it deliberately.**

---

## Who owns what — one fact, one home

This is the part that matters more than the file list. **A fact recorded in two
documents will be updated in one of them.** That is not a hypothetical: it is
what produced a roadmap describing a corpus that had not been transient for
months, a `.gitignore` comment saying the same, and a README describing a private
remote that had been public since publication.

| Fact | Owner | Everyone else |
|---|---|---|
| The whole requirements tree — KIQ, PIRs, SIRs, collectable facts, and which sensor serves each | `requirements.md` | Reference by name; do not restate the wording |
| **Tier weights, multiplier factors, group terms, thresholds, force-surface rules** | **`pnd.md`** | **Never restate a number.** Explain design *intent* freely; the values live in config because config is what executes |
| Product format and content standards | `policy.md` (if the domain has one) | Reference and state that the policy wins; do not reproduce the rules |
| Vocabulary collisions, dropped terms, review dates | `vocab.md` | — |
| Operating directives, cadence, lessons | `mandate.md` | — |
| Sensor list | the `sensors` block in `pnd.md` | Reference |

**The test:** if you change a value in `pnd.md`, does any other file now contain
a lie? If yes, that other file was restating instead of referencing.

### Violations found and closed — 2026-08-17

Applying the rule to CTI found three, all of them centred on one file:

1. **The Codex restated the scoring numbers.** The tier weights (8/4/2/1) and
   multiplier factors (1.5/1.5/1.3/1.3) lived in both `codex.md` and `pnd.md` —
   the same eight values in two places, so tuning the config silently made the
   Codex wrong. The oldest and worst of the three.
2. **The Codex and `mandate.md` both reproduced `vox_policy.md` §7.** Introduced
   the same day by the doctrine reconciliation, and recorded here rather than
   quietly left.
3. **The Codex's cut doctrine overlapped the policy's no-cap rule.** Same origin.

**Resolution: `codex.md` was retired.** Its requirements layers merged into
`requirements.md`, which now owns the whole tree; its scoring rationale —
convergence-wins, the worked examples, tiers-not-additive, round-up-on-
uncertainty, why-there-is-no-handicap, the mandatory drop list — moved into
`pnd.md`, beside the values it explains, where tuning a number and leaving the
reasoning stale is no longer possible; its content standards were already owned
by `vox_policy.md`, so `mandate.md`'s copy was thinned to a pointer.

Every block was inventoried before deletion and five would otherwise have been
lost: round-up-on-uncertainty, the no-handicap argument, tiers-not-additive, the
four worked examples, and the mandatory drop list. **Retiring a document means
rehoming its contents first, not deleting and hoping.**

*The suspected overlap was not the real one.* `codex.md` versus
`decomposition.md` looked like the duplication and was clean — the tell was that
the two needed a written rule to stay out of each other's way, which is what
pointed at the split being wrong rather than the content.

---

## Creating a new domain

1. **Copy `_template/` to `<domain>/`.** Folders whose name begins with `_` are
   not domains and are skipped by tooling.
2. **Run the Planning & Direction survey** (`PND_SURVEY.md`) to fill `pnd.md`.
   Do not write word lists first — see `VOCABULARY.md` §3, and note that the
   method there is marked unvalidated.
3. **Give every group a `reviewed:` date in `vocab.md`** as you create it. A date
   added later is a guess.
4. **Check it before running it:**
   ```
   python3 tools/vocab_check.py <domain>
   ```
   Expect no errors. Empty groups are an error precisely because they pass the
   loader's reference check and then match nothing.
5. **Confirm it loads and the numbers are what you meant:**
   ```
   python3 -c "
   import sys; sys.path.insert(0,'.')
   from core.pnd import load_domain
   c = load_domain(domain='<domain>')
   s = c['scoring']
   print('groups:', len(s['groups']), '| tiers:', len(s['tiers']),
         '| threshold:', s['settings'].get('surface_min_score'))
   "
   ```
6. **Read the drop list before the candidate list** for the first three cycles.
   A good item that fell below the cut is the most informative signal available.

### Give the domain its own corpus store

Two domains sharing a `base_dir` share the seen-lists, so one starves the other
of articles — it looks like a collection failure and is a configuration one. Set
a distinct `base_dir` and a distinct `corpus.rclone_remote` per domain. **There
is no guard for this yet**; it is on the backlog and is not needed until a second
domain actually runs.

### A domain that need not be public

Domain content publishes fine. If a particular domain should not, add its folder
to `.gitignore` — the `--pnd` flag means a domain file can live anywhere on disk,
so the engine, the doctrine and the guards stay fully public while that one
domain never enters the repo. Tooling that sweeps all domains skips gitignored
ones when run from the commit gate, and includes them on a manual run.

---

## The `_` prefix

A folder under the repo root containing a `pnd.md` is treated as a domain by
tooling that discovers domains. `_template/` would otherwise be swept up and
reported as a broken domain forever, since its groups are deliberately empty.

**Convention: a leading underscore means "not a domain."** Applied in
`../tools/vocab_check.py`; apply it to any future tool that discovers domains.
