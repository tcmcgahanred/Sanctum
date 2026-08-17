# CTI — Vocabulary decisions

*Sanctum · CTI domain · the reasoning behind the word lists in `pnd.md`.*

**Version:** v1 — first pass. Established 2026-08-17 when the vocabulary method
(`../VOCABULARY.md`) was written down and `tools/vocab_check.py` was run against
this domain for the first time.

> **This file never repeats the term lists.** `pnd.md` is the single source of
> truth for terms. This file records *decisions about* terms — what was dropped
> and why, what collides, what is missing, when each group was last reviewed.
> Two copies of the same words drift within a month.

---

## v1 changelog

1. **Boundary list reduced from 11 entries to 4.** Seven were dead. `hack`,
   `leak` and `war` matched no live term in any group — the terms they guarded
   had been removed at some earlier point and the entries survived. `ics`,
   `grid`, `uc` and `csu` are four characters or fewer, where the matcher
   already applies word boundaries automatically, so the entries added nothing.
   All seven removals are provable no-ops; parity confirms scoring is unchanged.
   Remaining: `scada`, `ransom`, `court`, `cisco`.

2. **No terms added or removed from any group.** Everything below marked as a
   gap or a collision is *recorded, not fixed* — vocabulary content is a
   Planning & Direction decision and belongs in the CTI briefing chat.

---

## Open finding 1 — the `incident` group covers one third of the problem

**Severity: high. Unresolved. P&D decision.**

The 13 terms in `incident` are all *confidentiality* language — things stolen,
leaked, breached, ransomed. The group has effectively no coverage of
**availability** (service knocked offline, denial of service, outage) or
**integrity** (defacement, data tampering, wiped systems).

Checked against MITRE ATT&CK's Impact tactic (TA0040, 15 techniques), which
describes what happens to a victim: **none of the 15 concepts have a matching
term in the group.** Absent: defacement, denial of service, disk wipe, data
destruction, service stop, firmware corruption, inhibit system recovery, data
manipulation, resource hijacking, financial theft, account access removal,
system shutdown, email bombing.

**Why this matters more than it looks.** The `incident` group is one half of
force-surface rules M1 and M3 (`pnd.md` → `scoring.force_surface`). A DDoS that
takes a county's 911 dispatch offline does not match `incident`, so **M1 does not
fire and the item lands in the drop list** — the exact scenario Vox Policy §7
names as the highest-priority verification case. The policy calls M1 "the hard
guarantee that every AOR incident surfaces." That guarantee is bounded by this
word list, not by the rule.

Found by probe: an article headlined *"Small California town website defaced"*
scored 1.0 and dropped. `geo` matched; `incident` did not.

**Recommended approach:** use the ATT&CK Impact list as a *checklist of concepts*
only. Its labels are analyst taxonomy ("Inhibit System Recovery"), not the words
reporters write ("couldn't restore from backups"). Target roughly 25 curated
prose terms, not a bulk import — see the caution under Open finding 3.

---

## Open finding 2 — `" calif "` does not do what it looks like

**Severity: medium. Accepted for now, recorded below.**

The term is written with leading and trailing spaces, which reads as an attempt
at word-boundary matching. `core/rules.py` calls `.strip()` on every term before
matching, so the padding is discarded and the term becomes the bare 5-character
substring `calif`. At 5 characters it is above the auto-boundary length, so it
falls back to substring matching — the precise behaviour the spaces were meant
to prevent.

Verified: `" calif "` matches *"califon new jersey"*.

`california` and `californian` are already in the group, so the marginal value of
`calif` is the abbreviated *"Calif."* form in wire copy. Two clean fixes exist —
add `calif` to `word_boundary_terms`, or replace it with `calif.` — and either
changes matching, so neither is made here.

`"csu "` and `"uc "` are padded the same way but are harmless: both are under the
auto-boundary length once stripped, so they get whole-word matching regardless.

---

## Open finding 3 — `geo` carries known collisions and now sits in the highest-cost position

**Severity: medium-high. Unresolved. P&D decision.**

`cti/decomposition.md` (EEI-1.2.a) already documents that several of the 34
county names are not California-exclusive:

| Term | Also | 
|---|---|
| `kings county` | Brooklyn, New York |
| `lake county` | Illinois, Florida, Indiana, Ohio |
| `trinity county` | Texas |
| `sierra county` | New Mexico |

**What changed on 2026-08-17.** `geo` was wired into force-surface rule M1. Per
`../VOCABULARY.md` §2, force-surface is the highest-cost position in Sanctum —
the only one where the score cannot correct a bad match, because overriding the
score is the rule's entire purpose. Every collision in `geo` is now inherited by
M1, and an out-of-state Lake County ransomware story will be force-surfaced.

Under the triage rule (§1), exact synonyms **do** exist here — `kings county,
california`, or pairing the county term with a state term via a `proximity` or
`all` atom. So §1 says these should be tightened. Doing so changes matching and
weakens M1's coverage in exchange for precision, which is a Planning & Direction
trade, not a maintenance edit.

**Also noted:** city coverage is thin — five cities across a 34-county AOR.

---

## Group review status

```yaml
vocab:
  review_interval_days: 180
  groups:
    geo:
      reviewed: 2026-08-17
      review_interval_days: 180   # county/city lists change slowly
    incident:
      reviewed: 2026-08-17
      review_interval_days: 90    # see Open finding 1 — known incomplete
    sector:
      reviewed: 2026-08-17
    ci:
      reviewed: 2026-08-17
    ransom:
      reviewed: 2026-08-17
      review_interval_days: 90    # actor and brand names turn over fast
    kev:
      reviewed: 2026-08-17
      review_interval_days: 90
    lowmat_tech:
      reviewed: 2026-08-17
      review_interval_days: 90    # Vox Policy §7 calls this a maintained lexicon
    supplychain:
      reviewed: 2026-08-17

  accepted:
    - check: padded term
      subject: "' calif ' in geo"
      reason: >
        Known and understood — see Open finding 2. Both fixes change matching,
        so the decision belongs to P&D rather than to a maintenance pass. The
        marginal exposure is small: california/californian already match, and
        the residual false positives are place names containing "calif".
      date: 2026-08-17
```

*No terms are recorded under `dropped:` — v1 removed only boundary-list entries,
which are not terms.*

---

## Verification status

**Not yet validated against live output.** Per `../VOCABULARY.md` §7:

- [x] `tools/vocab_check.py` passes with the accepted finding recorded
- [x] Parity test confirms the boundary-list reduction changed no score
- [ ] Read the drop list before the candidate list for the next three cycles
- [ ] Confirm `surface_min_score: 2.0` produces a sane surface size — the value
      is provisional and has never been measured against the live corpus
- [ ] Count how often M1 fires on a passing mention rather than a subject — the
      rule is a co-occurrence approximation, not subject-of detection
