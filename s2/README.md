# S2

*Sanctum domain. Watches for risks and threats an Army combat aviation brigade
should be aware of in preparing for war in the INDOPACOM area of responsibility —
adversary posture in theatre, conditions that degrade rotary-wing operations,
what current conflicts are teaching about helicopter survivability, and the
capabilities that specifically threaten Army aviation.*

## Who this serves

The S2 section of an Army combat aviation brigade. Trained all-source analysts
who will build their own analytical product from the vox — assume full command
of intelligence and aviation terminology, no glossing required. The brigade
works strategic-to-operational; battalions handle operational-to-tactical, so
tactical detail is lower value here.

**The standard is "they were not surprised," not "they acted."** This domain
informs; it does not recommend. That choice runs through the whole
configuration: a miss costs the requirement, a false positive costs seconds of
skimming, and the scoring is tuned accordingly. A relevance clause should say
what an item changes about what the reader should *expect* — not what they
should do.

## Where it stops

**At the vox.** Every domain does — tenet 9, not a per-domain choice. 3a makes
the staging document (machine, reproducible, not committed); 3b makes the vox
(human, committed to `editions/`). Whatever happens to the vox afterward is
stages 4–6 and outside Sanctum.

## Running it

```
./run.sh s2
```

Collection runs on the collector host, not on an authoring workstation. The
pull is roughly monthly and irregular, which is why `collection.window_days` is
set well above the seven-day default — at 7, most of the month would go
unscored and the recency gate would mark the remainder stale.

## Files

| File | What it holds |
|---|---|
| `pnd.yaml` | Everything the engine reads, including the `vocab:` block that records why the word lists say what they say |
| `requirements/` | One requirement, one file, plus `_tree.yaml` holding the PIRs, their indicators and which rules sit under each |

See `../docs/DOMAINS.md` for the full contract and for which document owns which
fact.

## Read this before judging the output

`requirements/` decomposes the requirements into 43 collectable facts, one file
each, and tags every one with sensor coverage. **One is confidently covered. Fifteen have
none.** The second-ranked requirement — conditions that degrade rotary-wing
operations — is effectively uncollected.

That is a collection finding, not a scoring defect. Ranking operates only on
what already arrived, and no vocabulary can surface something the sensors never
fetched. **Expect the early surfaces to be thin, and read that as a statement
about the sensor set.** The sensor-build roadmap is Byproduct 1 in
`requirements/_tree.yaml`.

## Adapting it

To point this domain at a different area of interest, swap the geography group
and the area-specific sensors. The platform, threat-system, and conflict groups
travel unchanged — they describe what threatens rotary wing anywhere, which is
deliberate: the aviation mission is constant, the theatre is an assignment.

The engine and the shared doctrine never change.

---

# Mandate — the S2 cycle


*Sanctum · `s2` · standing planning & direction record.*

*The continuity mechanism: any session handed this Mandate can run the cycle at
full quality without re-deriving decisions. Update it at the feedback stage of
every cycle; it feeds the planning stage of the next.*

---

### How to use this document

1. Read the Standing Directives — they are the current operative rules.
2. Read Pending Direction — that is what this cycle or the next should act on.
3. When the cycle ends, add lessons to the Log and update the directives.
4. **If a directive here conflicts with an ad-hoc request, the directive is the
   retained decision** — confirm before overriding.

---

### Cadence

| When | Step |
|------|------|
| Continuous | Collection runs on the host timer |
| On demand, roughly monthly, irregular | Analyst triggers a cycle |
| Cycle start | Read this Mandate, then the drop list, then the candidate queue |
| 3a | Staging document — machine artifact, not committed |
| 3b | Vox — committed to `editions/` |
| Cycle end | Update the Lessons Log; revise directives if anything changed |

**No fixed ship date and no deadline.** The reader's standard is awareness, not
action, so there is no decision this product must beat. The pull interval, not a
calendar, drives `collection.window_days`.

**Keep the dates distinct:** the title date, the ICOD (collection cutoff, in the
body), and LTIOV (planning doctrine only, never printed).

---

### Standing directives

#### Collection

- **Quality over quantity on sensors; generous on items.** A feed earns its place
  only if reliable AND additive. Drop noisy sensors rather than filter them — but
  keep borderline *articles* from good feeds. These operate at different layers.
- **Audit a sensor's yield, not just its liveness.** A feed can be reliable,
  additive on paper, and still wrong because of the *shape* of what it emits.
- **Sensors are this domain's binding constraint, not scoring.** One of 43
  collectable facts has confident coverage. A thin surface is a collection
  finding. Do not respond to it by loosening the scoring model.
- **Verify every URL from the collector host, not a browser.** Several defence
  publishers serve browsers normally and return 403 to datacentre addresses.

#### Analysis / scoring

- **The score is an ordering aid, not a measurement.** The analyst always overrides.
- **Prefer false positives to false negatives.** A false positive costs seconds of
  skimming; a miss costs the requirement.
- **No cap on the review surface.** The item count is an output of the scoring,
  never a target. If it is too large, tune — do not cap.
- **Tier rank encodes directness, not priority.** A high-ranked requirement
  legitimately sits in a low tier. This looks like an error and is not — do not
  "fix" it.
- **Drop a noisy term only when an exact synonym exists.** Where none does, keep
  it and accept the noise. See the `vocab:` block in `pnd.yaml` for the worked cases.
- **One deliberate inversion of that rule, in the geography group:** exclude
  ambiguous place names and accept the gap. The triage rule assumes the score can
  correct a bad match; inside a `force_surface` rule it cannot.
- **Do not add a geography multiplier.** Fourteen terms are shared with the
  chokepoint group and are safe only because geography feeds a tier. See
  the `vocab:` block in `pnd.yaml` Finding 4.
- **Do not reverse the proximity a-side and b-side** without re-reading the `vocab:` block in `pnd.yaml`
  Finding 9. The a-side has no word-boundary protection.

#### Production

- This domain has **no `policy.md` yet.** Content standards are unwritten. Until
  one exists, the audience and relevance-clause guidance in the `production:` block of
  `s2/pnd.yaml` is the operative standard — see Pending Direction.
- **Say what an item changes about what the reader should expect**, not what they
  should do. The standard is awareness, not action.

---

### Pending direction

*(act on these; move to the Log when done)*

1. **Host setup, before any run.** Create `/opt/ravenor-s2` with correct
   ownership. **Confirm `SANCTUM_BASE` is unset** — if set, it overrides
   `base_dir` and both domains land in one directory while the config looks
   correct. Add a service unit and timer.
2. **First three cycles: read the drop list before the candidate queue.** A good
   item below the cut is the most informative signal available.
3. **Watch for the proximity first-occurrence limit** (the `vocab:` block in `pnd.yaml` Finding 8).
   Look specifically for dropped articles that name an adversary more than once.
4. **Measure `surface_min_score`.** It is provisional and has never been tested
   against a real corpus.
5. **Assess the chokepoint multiplier.** If it fires on most items it carries no
   information and should be dropped.
6. **Re-tag sensor coverage in `requirements/_tree.yaml` against what actually arrived.**
   Every tag is currently an estimate. Expect several PARTIALs to resolve to
   ABSENT.
7. **Work the sensor roadmap** — Byproduct 1 in `requirements/_tree.yaml`. Priority 1 is
   aviation professional and doctrinal press: it unlocks the largest uncovered
   block, most of PIR-2 and the analytical half of PIR-3.
8. **Write a `policy.md`** once the first vox exists and there is something real
   to standardise against.

---

### Lessons / decisions log

*(dated, newest first — this is the memory of the cycle)*

#### 2026-08-18 — A file that parses can still be empty of content

`requirements/_tree.yaml` sat in the domain folder as an unfilled template while every
other file was complete. Nothing errored. `vocab_check` passed. It was caught by
eye, days later.

**Lesson:** when a domain is built by copying another, sweep the whole folder for
placeholder markers before treating any file as done.

#### 2026-08-18 — Designing around a schema you have not tested costs real work

Four rules were written defensively against limits the engine turned out not to
have. Proximity matching, nested `all:` inside `any:`, and multiplier
conjunctions are all supported. The strongest signal in the domain sat
deliberately disabled for a day because its syntax was assumed unavailable.

**Lesson:** verify the engine's grammar by test before designing around its
absence. The cost of asking is minutes; the cost of assuming was a rewrite.

#### 2026-08-18 — Reusing an output filename installed a stale file

A revised config was published under the same name as its predecessor. The
earlier version was the one installed, and produced 39 spurious errors that
looked like genuine defects. The giveaway was that the errors named terms that
had been removed in the revision.

**Lesson:** version every output filename. When a check fails, compare what the
tool reports against what the file should contain — an impossible error usually
means the wrong file, not a wrong rule.

#### 2026-08-17 — Decompose to collectable facts before tuning the scoring

Building the requirements tree surfaced that one of 43 collectable facts had
confident sensor coverage and that the second-ranked requirement was
uncollected. None of that was visible from the scoring model, which was sound.

**Lesson:** ranking and tuning operate only on what already arrived. **They
cannot reveal a requirement nothing is collecting against.** Do the coverage
audit before the first run, not after a disappointing one.

#### 2026-08-17 — Memorable names collide; designations do not

Two separate groups had to be rebuilt because the natural vocabulary was
nicknames and reporting names. One aircraft nickname is a major software
foundation, another a bird, three are Native American nations; one weapon
reporting name is a friendly aircraft. Every one had an exact numeric equivalent
that cost nothing.

**Lesson:** names are chosen to be memorable, which is exactly what makes them
collide with ordinary language. Prefer designations. This is the cheapest class
of vocabulary fix there is — the synonym already exists.

#### 2026-08-17 — The word-boundary rule was applied backwards

Boundary lists were built listing short terms, on the assumption that short
terms need protection. The matcher already applies boundaries automatically
below a length threshold; the list is for *longer* terms that appear inside
other words. Every list built this way did nothing.

**Lesson:** read the template's own comments before building against it. The
rule was stated plainly in the file being copied.

