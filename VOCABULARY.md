# Vocabulary — how a domain builds and maintains its word lists

*Sanctum · domain-agnostic method*

**BLUF:** A domain's vocabulary is the only thing standing between a real event
and the drop list. This file is the method for building it, the decision rules
for resolving collisions, and the checks that stop it decaying. It holds no
domain knowledge — each domain's terms live in its `pnd.md`, and each domain's
*reasoning* lives in its `vocab.md`.

**AUTHORITY:** §1 and §2 were extracted from a completed domain build in another
session and are validated by use. §3 is a recommendation that **has never been
run**. The confidence marks below are load-bearing; do not let later work quietly
promote a hypothesis to a proven procedure.

---

## Why this exists in writing

Sanctum recognises an event only if a word in the article appears in a declared
group. That makes vocabulary the highest-leverage and least-examined part of the
system: scoring is visible and argued about, while the word lists are typed once
and never reviewed.

The failure mode is silent. A group that has gone stale still matches
*something*, so it looks like it works. Detecting the problem means noticing an
absence, which is the thing humans are worst at. Everything below exists to turn
that invisible failure into a visible one.

---

## 1. The triage rule — VALIDATED

> **Drop a noisy term only when an exact synonym exists. Where no substitute
> exists, keep the term and accept the noise.**

**Why.** A false positive costs one queue slot and a few seconds to skip. A miss
costs the requirement the domain was built to serve. The loss functions are
asymmetric, and only one of them is visible — junk announces itself, gaps do not.
This is tenet 8 applied to word lists.

**Why the synonym test is the right pivot.** The intuitive question — *"how noisy
is this term?"* — has no honest answer before you have data. The answerable
question is *"does a precise alternative exist?"* If yes, dropping the ambiguous
form is free: you trade a vague label for an exact one and lose nothing. If no,
the choice is genuinely between noise and a gap, and the asymmetry settles it.

| Situation | Test result | Action |
|---|---|---|
| Ambiguous term, exact designation available | Synonym exists | Drop the ambiguous form |
| Ambiguous term, only broader forms available | No synonym | Keep, accept noise, monitor |
| Term whose collisions arrive through sources you need | No source-level fix | Precision is the only lever — see the exclusion operator |

**Collision classes to check every new group against:**

- Terms that are ordinary words in the target language
- Terms identical to well-known publications, products, or organisations
- Terms that name an entity on your own side as well as the one you track
- Terms that are common personal or place names
- Short terms that appear inside longer words
- Acronyms with high-volume civilian meanings
- **Place names that are not unique to your area of interest** — a county or city
  name that exists in four other jurisdictions will match all five

**Corollary — boundary lists decay.** `word_boundary_terms` entries for terms
that have since been dropped are harmless at runtime but actively misleading on
review: a later reader treats the boundary list as evidence those terms are live.
Verify boundary lists programmatically after every edit. Manual review does not
catch this — see §5.

---

## 2. The placement principle — VALIDATED

> **A term's disruption cost is a function of where it sits, not just how often
> it collides.**

The same term can be unacceptable in one position and harmless in another.

| Position | Effect of a noisy term | Cost |
|---|---|---|
| **Force-surface rule** | Guarantees the item reaches the surface **regardless of score** | **Highest — the score cannot correct it** |
| **Relevance tier** | Promotes an irrelevant item from the floor weight to the tier weight | **High** — displacement scales with the tier gap |
| **Tier with bare full-text matching** | No structural filter at all | **Exposed surface** |
| **Tier with a proximity or scope rule** | Structure filters much of the noise before the term matters | **Partly self-protecting** |
| **Urgency multiplier** | Applies to whatever tier the item already earned; junk stays at the floor | **Low** — floor weight × a modest factor is still near the floor |

**The first row is new and it is the important one.** Every other position is
subject to the score: a noisy term in a tier promotes junk, but the threshold and
the ordering still push it down. A noisy term inside a force-surface rule is
immune to all of that by design — force-surface exists precisely to override the
score. It is the only position in Sanctum where the usual corrective does not
apply.

**Consequences:**

- A term entering a force-surface rule deserves the strictest collision review in
  the system. Apply §1 to it before it lands, not after.
- Where a term is valuable but noisy, prefer to give it work from a multiplier.
  The signal is retained and the failure mode is bounded.
- A force-surface rule built on a broad group inherits **every** collision in that
  group. Check the group, not just the rule.

---

## 3. Deriving vocabulary from indicators — RECOMMENDED, NOT VALIDATED

**The gap.** The Planning & Direction survey moves from tier conditions straight
to term lists. With no intermediate step, vocabulary gets produced by category
brainstorming — enumerate the things, enumerate the places. That works, but it is
untethered from the requirement, and nothing checks whether the resulting list
actually serves it.

**The proposed method**, drawn from established collection-management practice:

```
Requirement  →  Indicator  →  Specific observable  →  Terms
```

- **Requirement** — what the reader needs to know. Usually a question.
- **Indicator** — the thing whose presence or change would answer it. Names a
  phenomenon, not a search string.
- **Specific observable** — the indicator restated as something detectable
  without judgement. Thresholds, named entities, discrete events.
- **Terms** — the words that would appear in text reporting that observable.

**The rung that matters is the third.** An indicator like *"conditions that stop
operations"* is not collectable. Restated as a stated threshold on a stated
variable, it becomes something a matcher can find. The discipline is forcing
every indicator through that conversion before a single term is written.

**Why this is marked unvalidated — read this before relying on it.** The gap was
identified *after* a vocabulary had already been built by enumeration. The method
did not build that vocabulary and has never been tested against a real corpus.

Two Sanctum domains now have a requirements decomposition on file. **Neither
validates this method.** Both enumerated their terms first and wrote the
decomposition afterward, which is the reverse of what §3 proposes. Having the
artifact is not the same as having used the procedure. §3 remains a hypothesis
until some domain builds a group through it from a standing start and the result
is measured against the corpus.

**What it appears to buy, if it holds:**

- Traceability from each term back to the requirement that justifies it
- A coverage check — an indicator with no terms is a visible gap
- A pruning criterion — a term serving no observable has no defence

---

## 4. Granularity — decide it late, not early

> **Granularity serves trending. Consolidation serves scoring.**

Splitting one broad group into several narrower ones **scores identically** — the
same items match at the same weights. It changes nothing about the queue. What it
changes is what you can ask the archive later: a single broad group can say the
category matched, but not whether one sub-category is rising while another is
flat.

That tension is real for tools that record which group matched at collection
time. **It does not bind Sanctum, because Sanctum records nothing.**
`core/lexicanum.py` recomputes matches on demand by re-running the live matcher
over the retained corpus. A group invented this morning can be run against
everything collected last year.

**So the granularity decision is reversible.** Split a group in six months, run
the archive search with `--since`, and the historical series comes back for the
new sub-groups. Scoring was already indifferent. Both directions are cheap.

**Therefore the mechanism does not force this question at build time, and should
not.** Forcing an irreversible-feeling choice at the moment the operator knows
least is bad design; here the choice is not even irreversible. What the mechanism
does instead:

- States plainly, at the point of decision, that regrouping is cheap and
  retroactive — so nobody over-engineers a taxonomy up front out of fear
- Asks the domain to record in `vocab.md` **when** a group was split or merged,
  so a later reader can interpret a discontinuity in a trend line

**One condition, and it is absolute.** This property holds *only while the corpus
is retained*. Retroactive analysis is a direct dividend of permanent retention. A
domain that prunes its corpus loses it, and then granularity really does become a
build-time decision. Any change to retention policy must be checked against this
section first.

---

## 5. What gets checked programmatically

Manual review does not catch vocabulary decay — that is an observed finding, not
a precaution. `tools/vocab_check.py` runs these checks against any domain:

| Check | Failure it catches |
|---|---|
| **Orphaned boundary term** | A `word_boundary_terms` entry equal to no live term. The entry is dead and implies a term is present when it is not. |
| **Redundant boundary term** | An entry of four characters or fewer. The matcher already applies boundaries at that length, so the entry adds nothing. |
| **Empty group** | A declared group with no terms. It matches nothing, and any rule referencing it silently never fires. |
| **Dropped term still live** | A term recorded as DROPPED in the domain's `vocab.md` but still present in `pnd.md`. This is the drift the two-file split exists to prevent. |
| **Stale group** | A group whose recorded review date is older than the domain's configured interval. |

The first three run with no `vocab.md` at all. The last two need one.

**Group staleness** deserves its own note. Two decay patterns are both silent:
calendar-anchored groups, whose dates simply pass; and fast-moving-technology
groups, where reporting migrates to names the group does not contain. Neither
raises an error, because the group keeps matching *something*. The risk compounds
when collection pulls are irregular, since there is no rhythm against which the
absence would become obvious. A review date per group is the cheapest available
defence.

---

## 6. What each domain declares

Two files, and the split matters.

**`<domain>/pnd.md`** — the terms. Single source of truth. The engine reads this
and nothing else.

**`<domain>/vocab.md`** — the *reasoning*. Version history, the collision table,
dropped terms and why, per-group review dates, known gaps, verification status.

> **`vocab.md` never repeats the term lists.** Two copies of the same words drift
> within a month, and the copy nobody runs is the one that gets edited. It records
> decisions *about* terms — which is exactly what a diff of `pnd.md` cannot tell
> you a year later.

Per-group metadata lives in a fenced `yaml` block in `vocab.md`:

```yaml
vocab:
  review_interval_days: 90      # domain-wide default
  groups:
    example_group:
      reviewed: 2026-08-17
      owner: "role or person"
      review_interval_days: 30  # optional per-group override for fast decay
  dropped:
    - term: "an ambiguous term"
      reason: "collides with an ordinary word; exact designation available"
      replaced_by: "the exact designation"
      date: 2026-08-17
```

---

## 7. Validation guidance

None of the above substitutes for testing against real output.

- Write a small number of known-good items into the corpus and confirm they score
  where you expect.
- **Read the drop list before the candidate list** for the first several cycles.
  A good item that fell below the cut is the most informative signal available,
  and it is the only way to catch the failure mode that matters most.
- Run `tools/vocab_check.py` after every vocabulary edit. It is wired into the
  commit gate, but catching it before the commit is cheaper.
- Watch knowingly-noisy retentions specifically. If one proves unusable, the
  fallback is constraining it structurally (§2) — moving it to a multiplier, or
  pairing it with a second required term — **not** dropping it. A term kept under
  §1 was kept because it has no substitute, and that has not changed.
