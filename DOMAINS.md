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

`core/pnd.py` reads it, validates it, and resolves every runtime path from it.
Nothing in `core/` opens any other file in a domain folder. That is the whole
machine contract, and it is deliberately that small — see tenet 2.

Everything below is a **human** contract. It exists because a domain that only
satisfies the machine is one nobody can maintain.

---

## The folder contract

| File | Status | What it is |
|---|---|---|
| `pnd.md` | **REQUIRED** | Planning & Direction. Manifest, sensors, scoring model, production block. The only file the engine reads. |
| `vocab.md` | **EXPECTED** | The reasoning behind the word lists — collisions, dropped terms, per-group review dates, known gaps. Never the terms themselves. See `VOCABULARY.md`. |
| `README.md` | **EXPECTED** | What this domain is, who it serves, how to run it, how to adapt it. |
| `decomposition.md` | **EXPECTED** | Requirements decomposed to the collectable-fact layer, each mapped to the sensor that collects it. **This is the file that makes a coverage gap visible** — see `ROADMAP.md`. |
| `mandate.md` | **EXPECTED** | Standing operating directives plus the dated lessons log. The continuity mechanism: a fresh session handed this can run the cycle. |
| `policy.md` | **OPTIONAL** | The product specification, where the domain produces a product with locked standards. CTI's is `vox_policy.md`. A domain terminal at the staging document may need none. |
| `editions/` | **OPTIONAL** | Committed voxes. Only for domains that produce one. A domain terminal at 3a has nothing to put here. |
| `references/` | **LOCAL ONLY** | Working notes, feed candidate lists. Git-ignored by pattern — these carry host and internal detail. |

**A domain with only `pnd.md` runs.** It is not wrong, it is just undocumented,
and the first person to inherit it — including you in six months — pays for that.

---

## Who owns what — one fact, one home

This is the part that matters more than the file list. **A fact recorded in two
documents will be updated in one of them.** That is not a hypothetical: it is
what produced a roadmap describing a corpus that had not been transient for
months, a `.gitignore` comment saying the same, and a README describing a private
remote that had been public since publication.

| Fact | Owner | Everyone else |
|---|---|---|
| Key Intelligence Questions, Priority Intelligence Requirements | `codex.md` | Reference by name; do not restate the wording |
| Specific requirements, collectable facts, which sensor serves each | `decomposition.md` | Reference; do not restate |
| **Tier weights, multiplier factors, group terms, thresholds, force-surface rules** | **`pnd.md`** | **Never restate a number.** Explain design *intent* freely; the values live in config because config is what executes |
| Product format and content standards | `policy.md` (if the domain has one) | Reference and state that the policy wins; do not reproduce the rules |
| Vocabulary collisions, dropped terms, review dates | `vocab.md` | — |
| Operating directives, cadence, lessons | `mandate.md` | — |
| Sensor list | the `sensors` block in `pnd.md` | Reference |

**The test:** if you change a value in `pnd.md`, does any other file now contain
a lie? If yes, that other file was restating instead of referencing.

### Known violations, recorded rather than hidden

Applying the rule to the CTI domain as it stands today finds three:

1. **`codex.md` Layer 3 restates the scoring numbers.** The tier weights
   (8/4/2/1) and multiplier factors (1.5/1.5/1.3/1.3) appear in both `codex.md`
   and `pnd.md`. Tune the config and the Codex silently becomes wrong. **This is
   the oldest and worst of the three.** Fix: keep the worked examples and the
   convergence-wins explanation, replace the tables with a pointer.

2. **`codex.md` Layer 5 and `mandate.md`'s Production block both reproduce
   `vox_policy.md` §7.** *Introduced 2026-08-17 by the doctrine reconciliation —
   my own doing, recorded here rather than quietly left.* Both copies name the
   policy as authoritative and carry the date they were reproduced, which bounds
   the damage, but it is still the pattern this section forbids. Fix: thin both
   to a reference.

3. **`codex.md` Layer 4 overlaps the policy's no-cap rule.** Same origin, same
   fix.

*`codex.md` versus `decomposition.md` was the suspected overlap and is actually
clean* — `decomposition.md` states its own boundary in its header and restates
the KIQ and PIRs only as tree roots, explicitly not maintained there. The real
duplication was between the Codex and the config.

None of the three are urgent; nothing is broken and every copy currently agrees.
Fix them on next touch, not as a special pass.

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
`tools/vocab_check.py`; apply it to any future tool that discovers domains.
