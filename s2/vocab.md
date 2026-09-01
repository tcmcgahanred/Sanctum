# S2 — Vocabulary decisions

*Sanctum · `s2` · the reasoning behind the word lists in `pnd.md`.*

**Version:** v3 — 2026-08-19. Threat groups split into designation and generic
halves after cycle 1; see Finding 10. Version v2 — 2026-08-18. Findings 1–4 closed against `core/rules.py` by
test; Findings 8 and 9 opened in their place, recording limits of the proximity
mechanism itself.

> **This file never repeats the term lists.** `pnd.md` is the single source of
> truth for terms. This records *decisions about* terms — what was dropped and
> why, what collides, when each group was last reviewed. Two copies of the same
> words drift within a month, and the copy nobody runs is the one that gets
> edited. See `../VOCABULARY.md`.

---

## v1 changelog

1. Initial vocabulary built — **19 groups, by enumeration, not by the indicator
   method.** `../VOCABULARY.md` §3 marks the indicator method RECOMMENDED, NOT
   VALIDATED, and it remains unvalidated: this domain did not use it. The
   requirements tree in `requirements.md` was built afterward and independently,
   so the two have not been reconciled. **Someone should still find out whether
   the indicator method works.**

2. Groups split for trend analysis, not for scoring. Seven separate threat
   groups score identically to one combined group. They are separate so the
   corpus can be filtered per category — "is man-portable reporting rising while
   vehicle-mounted reporting is flat" is unanswerable from a single group.

3. All seven threat groups designated **priority vocabulary**. Rationale: every
   group on that list describes something that kills or degrades Army aircraft.
   Distinctions that matter tactically — destroys versus degrades — do not
   change whether an analyst should see the item.

4. **Word-boundary lists rebuilt on the correct rule.** Earlier drafts listed
   terms of four characters or fewer, which do nothing — the matcher applies
   boundaries automatically at ≤4. The list is for terms longer than four
   characters that appear inside longer words. Every pre-correction boundary
   list in this domain is void.

---

## Open findings

*One heading per unresolved issue. Record, do not silently fix — vocabulary
content is a Planning & Direction decision.*

### Finding 1 — Declaration multiplier pairing

**Severity: high. CLOSED 2026-08-18.**

`declaration_terms` holds ordinary reporting verbs that appear in an enormous
share of all news writing — officials issue warnings about weather, economics,
and public health daily. Unpaired, the signal fires on most of the corpus and
carries no information.

**Resolved:** a multiplier's `when:` block is evaluated by the same function as
a tier's `require:`, so conjunctions, nesting, negation and proximity are all
available. There is no reduced grammar for multipliers. The signal is now live,
paired with `actor_adversary`.

Exclusion would have been the wrong tool: "match X unless Y" requires
enumerating everything that is not an adversary, which is unbounded. This is
"match X only when Y is also present" — a conjunction.

### Finding 2 — Tier 1 proximity

**Severity: medium. CLOSED 2026-08-18, superseded by Findings 8 and 9.**

Proximity matching exists, with a default window matching the figure chosen
during the survey. Tier 1 now uses it, with a second branch covering titles
because proximity never searches them.

Two limits of the implementation are recorded separately below — they are
properties of the mechanism, not defects in this domain's use of it.

### Finding 3 — Tier 3 nesting

**Severity: medium. CLOSED 2026-08-18.**

`any:` and `all:` recurse through the same evaluator, so a tier with two
alternate conjunction branches is one tier. Splitting into two tiers of equal
weight would have been wrong: tier assignment stops at the first match, so the
second would be unreachable for anything the first already caught, and the
reasoning line would name only one branch.

### Finding 4 — Cross-group duplicate terms

**Severity: medium. CLOSED 2026-08-18 — but see the standing rule.**

Tiers cannot double-count: the tier loop breaks on the first match, so a term
present in five groups still yields one weight. Multipliers can and do: each is
evaluated independently and its factor multiplied in.

The fourteen terms shared between `chokepoints` and `geo_indopacom` are safe
**only because geography feeds a tier and chokepoints feed a multiplier.**

> **STANDING RULE: do not add a geography multiplier.** The moment geography
> feeds one, those fourteen terms multiply twice off a single phrase, and
> nothing in the output explains it — the reasoning line shows two multiplier
> names, not that they fired on the same words. If a geography multiplier is
> ever wanted, collapse it and the chokepoint multiplier into one rule with
> `any:` over both groups.

### Finding 8 — Proximity tests only the first occurrence of each term

**Severity: medium. Unresolved — accepted, monitor.**

The matcher locates each a-side term with a first-index search and stops. An
adversary named early in passing, and again beside an event word later in the
article, **is missed.**

The limit is per-term, not per-group, so a large a-side vocabulary yields many
anchor points and materially reduces the risk. It does not eliminate it.

**Watch for this specifically:** read the drop list for the first cycles looking
for articles that name an adversary more than once.

### Finding 9 — Proximity a-side has no word-boundary protection

**Severity: medium. Mitigated by design.**

The a-side term is located by raw substring search with no boundary matcher;
the b-side does use it. A short or embeddable a-side term can therefore anchor
the window on the wrong text.

**Mitigated by putting `event_words` on the a-side rather than
`actor_adversary`.** The actor group contains a term that raw-matches inside an
extremely common English word, which would have anchored windows on unrelated
text throughout the corpus. Event verbs are longer and mostly not embeddable.

**Do not reverse the a-side and b-side without re-checking this.**

### Finding 10 — Tier 2 had no adversary requirement

**Severity: high. CLOSED 2026-08-19.**

Cycle 1 surfaced ten items. **All ten were US or allied stories.** A domestic
counter-drone cannon programme, a missile designed to *evade* air defences, and
domestic missile production contracts all scored as adversary capability.

**Cause.** Tier 2's rule was a bare `any:` across the threat groups. The word
"adversary" appeared in the tier's name and nowhere in its rule. The groups mixed
two kinds of term:

- **Designations** — self-identifying as adversary systems.
- **Generic capability terms** — "air defense system", "counter-UAS",
  "surface-to-air missile". These describe **anyone's** systems, including ours.

**Fix.** Each threat group split into a designation half and a generic half.
Tier 2 became a two-branch rule: designations qualify alone; generic capability
terms require `actor_adversary` alongside. Verified against the actual cycle 1
titles — all four friendly items now fail, adversary items still pass on both
branches.

**Lesson.** A rule can pass every automated check and still be semantically
wrong. `vocab_check` validates structure, not meaning. Only running it found
this, and it took ten titles.

### Finding 11 — Group names were living inside term lists

**Severity: medium. CLOSED 2026-08-19.**

Eight group names had been scraped into term lists as terms — one group's name
was a live term inside another group. Harmless at runtime, since no article
contains those strings, but they inflate term counts and mislead on review.

**`vocab_check` cannot catch this** — a group name is a valid, non-empty string.
A check that rejects any term matching a declared group name would be cheap and
is worth raising upstream.

### Finding 12 — Two cycles, zero hits above the catch-all tier

**Severity: high. Unresolved — this is a collection problem.**

Across 27 articles from two cycles: **no Tier 1, no Tier 2, no Tier 3.** Not one
article contained a rotary-wing term. After the Tier 2 fix the surface is empty.

That is the scoring model reporting honestly. A single Western trade-press feed
can only answer the capability requirement, which is the domain's lowest-ranked.
It structurally cannot answer adversary posture, environmental and basing
factors, or lessons from current conflicts.

**Do not respond by lowering `surface_min_score`.** That manufactures a surface
out of items correctly judged irrelevant. The count is an output, never a target.

The fix is sensors. See `requirements.md` Byproduct 1.

### Finding 13 — One configured sensor failed silently

**Severity: medium. CLOSED 2026-08-19 by removal.**

A maritime sector feed was configured and contributed nothing. It redirects to a
new host, the collector does not follow redirects, and the destination sits
behind bot protection that returns 403 to the collector while serving browsers
normally.

**No error was raised at any point.** The sensor list claimed coverage that did
not exist. Removed, with the reason recorded in the sensors block.

Two upstream findings: the collector does not follow redirects, and it does not
flag a configured feed that returns zero items across a cycle. Both are silent,
and both let a sensor list lie about coverage.

### Finding 5 — Recurrence is not expressible in per-item scoring

**Severity: medium. Unresolved.**
multiple reports. That is longitudinal. Scoring is per-item and per-cycle with no
memory of changing frequency. The corpus supports the analysis because it is
permanent; the tooling does not perform it. Raised with Sanctum as a capability
request.

### Finding 6 — Agile combat employment acronym omitted

**Severity: low. Unresolved.**

The acronym collides with the card sense, the pilot sense, and ordinary usage.
The spelled-out form is included instead. If reporting uses the acronym
predominantly, `env_basing` under-fires and the acronym needs reconsidering under
the exclusion operator rather than plain inclusion.

### Finding 7 — Coverage tags in requirements.md are estimates

**Severity: low. Unresolved.**

Every ACTIVE / PARTIAL / ABSENT tag is reasoned from what the sensor set is
expected to carry, not measured. Re-tag after three cycles; expect several
PARTIALs to resolve to ABSENT.

---

## Collision table

Checked against the classes in `../VOCABULARY.md` §1. The triage rule: **drop a
noisy term only when an exact synonym exists.** Where none does, keep it, accept
the noise, and note it here so the next reader knows it was a decision.

**One deliberate inversion of that rule, in `geo_indopacom`.** The triage rule
assumes score can correct a bad match. Inside a `force_surface` rule it cannot —
a bad match is guaranteed to reach the reader. For place names the standing rule
is therefore the opposite: **exclude and accept the gap.** Do not "fix" this back.

| Term | Collides with | Status |
|---|---|---|
| Osa | Osaka — severe in this AOR | DROPPED. Exact designation retained instead. |
| Tor, bare | Anonymity network; surname; inside "torpedo", "history" | DROPPED. Hyphenated variants retained. |
| Lancet, bare | The Lancet — major medical journal, arrives via general-news feeds that cannot be declined | DROPPED. Hyphenated and internal designations retained. |
| Shahed, bare | Common Persian given name and surname | DROPPED. Numbered variants retained. |
| AAA | Batteries; motor club; credit ratings | DROPPED. Spelled-out forms retained. |
| NATO reporting codenames (18) | All ordinary English; one is a US Navy aircraft; one is a film | DROPPED. Numeric designations are exact — zero capability lost. |
| Aircraft nicknames (9) | Software foundation; salmon; a wind; a bird; three Native American nations; a film; an NHL team | DROPPED. Type designations retained. |
| Bare demonyms (4) | Economic, cultural, culinary, sporting coverage. Paired with an event word in a tier rule, an ordinary trade story would qualify | DROPPED. Institutional forms retained. |
| Midway | "midway through", "midway point" | DROPPED. |
| Java | The programming language — enormous technical-press volume | DROPPED. |
| Manila | Envelopes, folders, rope | DROPPED. |
| Clark, Darwin, bare | Extremely common surname; Charles Darwin | DROPPED. Full base names retained. |
| Sulu | *Star Trek* character | DROPPED. Maritime compound retained. |
| Victoria, Perth | Ambiguous across three continents | DROPPED. |
| Scarborough, bare | Towns in England, Canada, Maine | DROPPED. Compound retained. |
| Olympic committee acronym | The committee itself — would co-fire with the fixed-date group on exactly the wrong items | DROPPED. Spelled-out form retained. |
| anniversary, summit, surge, alert, swarm — bare | Ordinary English | DROPPED. Compound forms retained where they exist. |
| Two large sea names | Appear in a very large share of AOR reporting | Excluded from the chokepoint multiplier; retained in the geography group where they do real work. |
| China | "china" — porcelain and tableware | **KEPT.** No exact synonym. Boundary applied. Tolerable because tableware rarely sits near an event verb. **Watch.** |
| PLAN | Ordinary English word | **KEPT.** No exact synonym; the spelled-out form does not appear in all reporting. Automatic boundary applies at ≤4 characters. **Highest-risk term in the config.** |
| FPV | Drone racing, gaming, consumer video | **KEPT.** No substitute — much of the most relevant reporting uses no other word. Noise accepted. |
| S-400 | A Mercedes-Benz model | **KEPT.** Military context usually disambiguates. Monitor. |
| Fujian | Also a PLAN aircraft carrier | **NOT A COLLISION** — both senses are in-domain. Noted so a later reviewer does not "fix" it. |
| Gerbera, ZALA, Alabuga, Tunguska | A flower; a surname and Hungarian county; a Russian town; the 1908 impact event | **KEPT.** Volume too low to matter. |

---

## Group review status

```yaml
vocab:
  review_interval_days: 180
  groups:
    geo_indopacom:
      reviewed: 2026-08-17
      review_interval_days: 365
    event_words:
      reviewed: 2026-08-17
      review_interval_days: 365
    actor_adversary:
      reviewed: 2026-08-17
    platform_rotary_wing:
      reviewed: 2026-08-17
    conflict_markers:
      reviewed: 2026-08-17
      review_interval_days: 90
    env_basing:
      reviewed: 2026-08-17
    threat_manpads:
      reviewed: 2026-08-17
    threat_sam:
      reviewed: 2026-08-17
    threat_aaa_cuas:
      reviewed: 2026-08-17
    threat_ew:
      reviewed: 2026-08-17
    threat_small_arms:
      reviewed: 2026-08-17
    threat_uas_loitering:
      reviewed: 2026-08-17
      review_interval_days: 90
    threat_sa_designations:
      reviewed: 2026-08-17
    threat_manpads_generic:
      reviewed: 2026-08-19
    threat_sam_generic:
      reviewed: 2026-08-19
    threat_aaa_cuas_generic:
      reviewed: 2026-08-19
    threat_ew_generic:
      reviewed: 2026-08-19
    threat_small_arms_generic:
      reviewed: 2026-08-19
    threat_uas_loitering_generic:
      reviewed: 2026-08-19
    declaration_terms:
      reviewed: 2026-08-17
    escalation_terms:
      reviewed: 2026-08-17
    coercive_acts:
      reviewed: 2026-08-17
    first_occurrence:
      reviewed: 2026-08-17
    fixed_date_events:
      reviewed: 2026-08-17
      review_interval_days: 90
    chokepoints:
      reviewed: 2026-08-17

  # Short intervals: conflict_markers because the set of active conflicts
  # changes; threat_uas_loitering because half its designations did not exist
  # eighteen months ago; fixed_date_events because dates pass and exercise names
  # change, and none of that errors — the group simply stops matching, silently,
  # against an irregular pull cadence that will not surface the absence.
  #
  # Long intervals: place names and ordinary verbs are stable.

  dropped: []

  accepted: []
```

**Note on `dropped:`.** Left empty deliberately. Every term listed in the
collision table above was excluded during initial construction and was never
live in `pnd.md`. `dropped:` records terms removed *after* they were in service,
which is the drift this two-file split exists to catch. Populate it on the first
removal, not retroactively.

---

## Verification status

**Not validated until tested against live output** (`../VOCABULARY.md` §7):

- [ ] `tools/vocab_check.py s2` passes
- [ ] Known-good items score where expected
- [ ] Drop list read before the candidate list for the first three cycles
- [ ] `surface_min_score` measured against the real corpus, not left provisional
- [x] Findings 1–4 resolved against `core/rules.py` — closed 2026-08-18
- [ ] Finding 8 — drop list read for articles naming an adversary more than once
- [ ] `PLAN` false-positive rate assessed — highest-risk term in the config
- [ ] `China` checked for tableware collisions
- [ ] Chokepoint multiplier assessed for near-universal firing; a signal that
      fires on most items carries no information and should be dropped
