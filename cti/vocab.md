# CTI — Vocabulary decisions

*Sanctum · CTI domain · the reasoning behind the word lists in `pnd.md`.*

**Version:** v1 — first pass. Established 2026-08-17 when the vocabulary method
(`../docs/VOCABULARY.md`) was written down and `tools/vocab_check.py` was run against
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

## v2 changelog - 2026-08-24, scoring precision

Two P&D work orders in one day. The first tightened matching after the staging
queue's top filled with false positives; the second approved the vocabulary that
stops the tightening from creating misses. **Every change is a precision change.
No requirement was dropped.**

1. **`sector` rewritten from bare nouns to compound terms.** The worst entry was
   `water`, which gave tier 2 (weight 4.0) to an Australian hotel with a water
   park and to a Comcast release about a water-cooled data centre. Dropped:
   `water`, `utility`, `utilities`, `college`, `tribal`, `election`, `transit`,
   `court`, `sheriff`. Added: `water utility`, `water district`,
   `water authority`, `water treatment`, `water system`, `water sector`,
   `drinking water`, `utility district`, `public utility`, `electric utility`,
   `utility sector`, `community college`, `school system`, `public schools`,
   `public works`, `tribal government`, `tribal nation`, `election office`,
   `election systems`, `transit agency`, `transit authority`, `superior court`,
   `county court`, `sheriff's office`, `sheriff's department`. **An ordinary
   English word cannot carry a sector requirement.**
2. **`ci` rewritten the same way**, for the same reason: it feeds the
   ransomware-versus-critical-infrastructure multiplier, where bare `water`,
   `utility`, `power`, `grid`, `school` and `government` fired on nearly
   anything.
3. **`kev` was doing two jobs**, mixing exploitation evidence with generic
   vulnerability vocabulary, so a buyer's guide saying "a zero-day is always a
   possibility" scored as an exploited flaw. **New group `exploit_strong`**
   carries only exploitation evidence. `kev` is retained, used by no rule.
   **When a group turns out to be two groups, split it; do not delete half.**
4. **`incident` gained theft and intrusion language** - `hackers`, `stolen data`,
   `data theft`, `blackmail`, `defaced`, `defacement`. The trigger was a real
   miss: *"Hackers Release Stolen Data From State's Largest School District"*
   matched `school district` in the title and then failed for want of an
   incident word, because the group held `hacked` (not "hackers") and
   `data stolen` (not "stolen data"). **Word order and plurality are not
   details here.**
5. **Availability language deliberately kept OUT of `incident`.** `outage`,
   `denial of service` and `ddos` live in `targeting` only. `incident` feeds
   tier 1 and force-surface M1, which need a place name plus one incident word,
   so `outage` there would turn every California wildfire or public safety power
   shutoff into an AOR cyber incident. In `targeting` the same words fire only
   where the sector is already the subject. Genuine cyber-caused outages still
   reach M1 through `ransomware`, `breach`, `hacked` and the new theft terms.
   P&D work order 2026-08-24, decision 4.
6. **`hacker` singular is confined to `incident_broad`, and is ON WATCH.** It is
   noise-prone - *ethical hacker*, *hacker conference*, the feed name *The Hacker
   News*. Held there it can only fire where the sector is already the subject and
   can never reach tier 1. **If it over-fires next cycle, drop the singular and
   keep only `hackers`.**
7. **New groups `targeting` and `incident_broad`.** The second is the union of
   the first two plus `hacker`, needed because the `proximity` atom takes one
   group per side. Keep it as that union.
8. **New group `listicle`** - headline shapes that are never incident reporting.
   Title-matched, used through `not`, so it withholds a tier rather than
   dropping anything.
9. **New groups `cve` and `cisa_source`.** `cve` tests whether exploitation
   language sits near a real identifier. `cisa_source` is matched against the
   article's SOURCE, never its text, so an official directive can be told apart
   from a trade write-up about one.
10. **Boundary list is now `scada`, `ransom`, `cisco`, `how to`, `what is`,
    `hacker`.** `court` was orphaned when bare `court` left `sector`; `cve-` is
    four characters and gets boundaries automatically. **The guard caught all of
    these** - none was found by reading.

### Still open after this pass

- **`incident` remains incomplete** - see Open finding 1. This pass closed the
  theft and defacement gap; wipers, destruction and recovery-inhibition are
  still absent, and availability language is confined to `targeting` by design.
  **Expect a few more gaps per cycle. The fix is always a term add, never a rule
  loosening.**
- **No education-sector term.** *"ShinyHunters Targets Education Sector with
  Oracle PeopleSoft Exploit"* falls from 15.21 to 1.0: `sector` has
  `school district`, `university` and `community college`, but not
  `education sector` or `higher education`. Raised before the work order and not
  among the approved terms, so not added. **P&D decision.**
- **`geo` does not cover the whole state, by design, and that now shows.**
  *"El Cerrito Blackmailed by Notorious Cyber Gang"* cannot surface: El Cerrito
  is in Contra Costa County, which is not among the 34 counties in `geo`. Adding
  `blackmail` did not help, because **the failure is geographic, not lexical**.
  Whether the AOR is 34 counties or wider is a P&D decision.

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

`cti/requirements.md` (EEI-1.2.a) already documents that several of the 34
county names are not California-exclusive:

| Term | Also | 
|---|---|
| `kings county` | Brooklyn, New York |
| `lake county` | Illinois, Florida, Indiana, Ohio |
| `trinity county` | Texas |
| `sierra county` | New Mexico |

**What changed on 2026-08-17.** `geo` was wired into force-surface rule M1. Per
`../docs/VOCABULARY.md` §2, force-surface is the highest-cost position in Sanctum —
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

## How a keyword gets attributed to a requirement

*Added 2026-08-26.*

**A keyword's intelligence requirement is decided by which group it lands in.**
Nothing else attributes it. The tier rules that consume a group are the
requirements, so putting a term in `geo` makes it PIR-1 vocabulary and putting it
in `sector` makes it PIR-2 vocabulary, whether or not anyone intended that.

That was true before this section existed and it was written down nowhere. The
mapping could only be recovered by walking every rule tree by hand across two
files, and on 2026-08-26 a session doing exactly that got it wrong twice in one
sitting. **A fact that must be derived is a fact that will eventually be derived
wrongly.** So each group now declares its attribution in the block below, and
`tools/vocab_check.py` warns when one does not.

**The question to ask of a new keyword:** does this word tell me *which*
requirement is in play, or does it make an already-relevant item more urgent?

- **First case — it belongs in a requirement-defining group,** and that group
  names the requirement. `geo` and `incident` serve PIR-1. `sector` and
  `incident_broad` serve PIR-2. `exploit_strong` and `lowmat_tech` serve PIR-3.
- **Second case — it is an elevation term and has no single requirement.**
  `ci`, `ransom`, `supplychain`, `cve` and `cisa_source` change how an item
  ranks, never which question it answers. Attributing one of these to a
  requirement is a category error, not a judgement call.

**Three groups sit outside both.** `listicle` is an exclusion — it exists only to
be negated. `ttp` shapes the product rather than the score, suggesting a vox
section. `kev` and `targeting` are consumed by no rule at all, both on purpose
and both with the reason recorded below.

**Why this lives here and not in `pnd.md` or `requirements.md`.** It is reasoning
about a group, and the standing decision of 2026-08-17 puts terms in `pnd.md` and
reasoning about terms here — two copies of the same fact drift within a month.
Writing it as prose in `requirements.md` would have created a second copy that
nobody opens while editing a word list, which is how `kev` and `targeting` came
to be invisible in the first place.

**The judgement is not automatable and is not meant to be.** Deciding whether
`outage` serves PIR-1 or PIR-2 is intelligence judgement. What the guard enforces
is only that the judgement was made and recorded — never what it should be.

---

## Group review status

```yaml
vocab:
  review_interval_days: 180
  groups:
    # Each group declares ONE of `serves:` or `role:`. See "How a keyword gets
    # attributed to a requirement" above for what the values mean and why the
    # declaration lives here rather than in pnd.md or requirements.md.
    geo:
      reviewed: 2026-08-17
      review_interval_days: 180   # county/city lists change slowly
      serves: [PIR-1]             # tier 1 and force-surface M1
    incident:
      reviewed: 2026-08-24        # theft/hacker terms added, v2 changelog
      review_interval_days: 90    # see Open finding 1 — known incomplete
      serves: [PIR-1]             # tier 1 and force-surface M1
    sector:
      reviewed: 2026-08-24        # rewritten to compound terms, v2 changelog
      serves: [PIR-2]             # tier 2 and force-surface M3
    incident_broad:
      reviewed: 2026-08-24
      review_interval_days: 90    # keep as union of incident + targeting, plus 'hacker'
      serves: [PIR-2]             # tier 2 and M3; ALSO elevates two multipliers
    exploit_strong:
      reviewed: 2026-08-24
      review_interval_days: 90    # the line between real exploitation and trend talk moves
      serves: [PIR-3]             # tier 3, force-surface M2, the CISA floor;
                                  # ALSO elevates both x1.5 multipliers
    lowmat_tech:
      reviewed: 2026-08-17
      review_interval_days: 90    # Vox Policy §7 calls this a maintained lexicon
      serves: [PIR-3]             # tier 3, force-surface M2, the CISA floor;
                                  # ALSO elevates both x1.5 multipliers
    ci:
      reviewed: 2026-08-24        # rewritten to compound terms, v2 changelog
      role: elevation             # ransomware vs public-sector/CI multiplier only
    ransom:
      reviewed: 2026-08-17
      review_interval_days: 90    # actor and brand names turn over fast
      role: elevation             # ransomware vs public-sector/CI multiplier only
    supplychain:
      reviewed: 2026-08-17
      role: elevation             # supply-chain / procurement multiplier only
    cve:
      reviewed: 2026-08-24
      review_interval_days: 365   # identifier format, not vocabulary
      role: elevation             # KEV / actively exploited multiplier only
    cisa_source:
      reviewed: 2026-08-24
      review_interval_days: 365   # a hostname, not vocabulary
      role: elevation             # the CISA-directive floor raises a score
    listicle:
      reviewed: 2026-08-24
      review_interval_days: 90    # headline fashions change; new shapes will appear
      role: exclusion             # only ever appears under a `not`
    ttp:
      reviewed: 2026-08-25
      review_interval_days: 90    # tradecraft naming follows the research, fast
      role: production            # suggests the "CTA TTPs" section; scores nothing
    kev:
      reviewed: 2026-08-17
      review_interval_days: 90
      role: unused
      unused_because: >
        Split into `exploit_strong` on 2026-08-24 because it was doing two jobs,
        mixing exploitation evidence with generic vulnerability vocabulary.
        Retained under the standing rule that when a group turns out to be two
        groups you split it rather than deleting half. NOTE: `zero-day` and
        `0-day` live here and nowhere else, so they currently fire no multiplier
        — reconcile with work order 3 in cti/pnd_work_orders_20260825.md before
        that decision is taken.
    targeting:
      reviewed: 2026-08-24
      review_interval_days: 90    # attack-verb phrasing follows the press, not the threat
      role: unused
      unused_because: >
        Availability language (outage, denial of service, taken offline, service
        disruption) is confined here by design. `incident_broad` was built as the
        union of `incident` and `targeting` and is what the rules read; this group
        is the reserve the union draws from. Wiring it into `incident` is Open
        finding 1 and a P&D decision, not a maintenance edit.

    # PIR-4 — broad/national with SLTT relevance — has NO group. Tier 4 is
    # `require: always`, the floor every item lands on when nothing else
    # qualifies. There is no vocabulary to attribute to it and there should not
    # be: it is the absence of the other three, not a subject of its own.

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

**Not yet validated against live output.** Per `../docs/VOCABULARY.md` §7:

- [x] `tools/vocab_check.py` passes with the accepted finding recorded
- [x] Parity test confirms the boundary-list reduction changed no score
- [ ] Read the drop list before the candidate list for the next three cycles
- [ ] Confirm `surface_min_score: 2.0` produces a sane surface size — the value
      is provisional and has never been measured against the live corpus
- [ ] Count how often M1 fires on a passing mention rather than a subject — the
      rule is a co-occurrence approximation, not subject-of detection
