# [DOMAIN] — Planning & Direction

*Sanctum · `_template` · copy this folder to `<domain>/` and fill it in.*

**BLUF:** This is the only file the engine reads. It declares what this domain
cares about; it never says how the engine behaves. Nothing here executes —
`tests/domain_check.py` refuses a domain file containing behaviour, and it means
it.

**Before you fill this in:** run the Planning & Direction survey
(`../PND_SURVEY.md`). Resist writing word lists first — see `../VOCABULARY.md`
§3 for why vocabulary should derive from requirements, and note that the method
there is marked **RECOMMENDED, NOT VALIDATED**.

---

## Manifest

Where the corpus lives and how collection is tuned. **Give this domain its own
`base_dir` and its own corpus remote** — two domains sharing either will share
seen-lists, and one will silently starve the other of articles.

```yaml
manifest:
  domain: TEMPLATE                    # must match the folder name
  base_dir: /path/to/runtime          # or override with $SANCTUM_BASE
  corpus:
    backend: rclone                   # rclone | local
    rclone_remote: remote:corpus-NAME # distinct per domain
  staging:                            # OPTIONAL — where the analyst collects the 3a output
    backend: rclone
    rclone_remote: remote:staging-NAME
    filename: "NAME_{date}_STAGING.md"  # {date} -> YYYYMMDD, dated so runs never clobber
  collection:
    window_days: 7                    # SET THIS TO YOUR REAL PULL INTERVAL.
                                      # The 7-day default silently under-scores
                                      # any domain pulled less often than weekly.
    min_title_len: 15
    suffix_separators: [" - ", " | ", " — "]
```

---

## Sensors — collection feed list

One URL per line. Blank lines and `#` comments ignored.

**Verify every URL against the collector host's actual egress before loading** —
some sources return 403 to datacenter IPs while working fine from a browser.

```sensors
# https://example.org/feed
```

---

## Scoring

The engine reads `tiers[]`, `multipliers[]`, `groups{}`, `force_surface[]`,
`word_boundary_terms[]` and `settings{}`. The schema is identical for every
domain; only the content differs.

**An item takes the weight of the highest tier it qualifies for** — tiers are
not additive with each other. Multipliers stack multiplicatively on top.

**Placement matters as much as the term** (`../VOCABULARY.md` §2). A noisy term
costs most inside a `force_surface` rule, where the score cannot correct it;
least inside a multiplier, where junk stays near the floor.

**Use proximity, not bare co-occurrence, for any condition needing two groups.**
Requiring both groups anywhere in a full body is barely a condition — in
production it matched one generic word and one platform word paragraphs apart,
in unrelated stories. Prefer:

```yaml
      require:
        any:
          - {proximity: {a: group_one, b: group_two, window: 120}}
          - all: [{group: group_one, scope: title}, {group: group_two, scope: title}]
```

The title branch is not optional. **Proximity searches the body only** and will
miss a headline-only match without it. Two more behaviours you cannot infer:
only the FIRST occurrence of each anchor-side term is tested, and the anchor
side has NO word-boundary protection while the other side does — so a short term
that was safe elsewhere can become unsafe as an anchor. Re-audit any group you
promote to the `a:` side.

**Watch groups that mix specific names with category nouns.** A designation says
whose thing it is; "system" or "platform" does not. A tier built on both will
surface your own side's stories, pass every check, and look correct — see
`../VOCABULARY.md` §1.

**Keep the multiplier stack under two tier steps.** Multiply every factor
together: if the product exceeds the ratio between your top tier and the one two
below it, a floor-tier item with all signals firing outranks genuinely relevant
items and relevance has stopped ordering the queue. `tools/vocab_check.py`
computes this and fails the commit if you cross it.

```yaml
scoring:
  tiers:
    - id: 1
      name: "most direct hit on the requirement"
      weight: 8.0
      require:
        any:
          - {group: primary, scope: blob}
    - id: 2
      name: "adjacent or leading-indicator"
      weight: 4.0
      require:
        any:
          - {group: secondary, scope: blob}
    - id: 4
      name: "in scope, no stronger anchor"
      weight: 1.0
      require: always          # the catch-all tier is mechanically always-match

  multipliers:
    # Absent = 1.0. A missing signal must never suppress a relevant item.
    - name: "urgency signal"
      factor: 1.5
      when: {group: urgency, scope: blob}

  # OPTIONAL. Inclusion, never ranking: a match guarantees the item reaches the
  # surface whatever it scored. Score still orders everything, so a forced
  # low-scoring item sits at the bottom of the surface with the disagreement
  # visible — which is the tuning signal.
  #
  # The guarantee is bounded by the vocabulary, not by the rule. A rule cannot
  # surface an event described with a word no group contains.
  force_surface: []

  settings:
    # A THRESHOLD, NEVER A COUNT. The number of surfaced items is an OUTPUT of
    # the scoring, not a target set over it. If the surface is too large, tune
    # the weights or the vocabulary — do not cap it. The uncapped surface is
    # the diagnostic.
    surface_min_score: 2.0
    empty_title: {score: 0.5, tier: 4, flag: "FLAG: empty title (feed artifact — verify source)"}
    recency:                   # flag stale-by-publish-date, never drop
      enabled: true
      window_days: 7
      cutoff_weekday: monday
      cutoff_time: "05:00"
      timezone: UTC
    grouping:                  # near-duplicate EVENT grouping — display only
      enabled: true
      min_similarity: 0.55
      min_shared_tokens: 3
      min_evidence: 8.0
      max_group_size: 25
      max_group_display: 12

  # Only terms that are BOTH live in a group AND longer than 4 characters belong
  # here — the matcher applies boundaries automatically at <=4, so a shorter
  # entry does nothing. Verified by tools/vocab_check.py.
  word_boundary_terms: []

  # Every declared group needs terms. An EMPTY group passes the loader's
  # reference check and then matches nothing, so a rule using it reads as active
  # and is inert. vocab_check.py treats that as an error.
  #
  # Do not write terms with leading or trailing spaces. The matcher strips them,
  # so " term " is not the word-boundary guard it looks like.
  groups:
    primary: []
    secondary: []
    urgency: []
```

---

## Production

Only `report_title` is read by any engine. The rest is the human stage's
reference — the audience, the section taxonomy, and the names of the two
documents.

**No item targets.** The review surface is uncapped by design; restraint belongs
to whatever finished product is built downstream, applied by a person.

```yaml
production:
  audience: >
    Who the "why should you care" clause is addressed to, and their maturity.
    Be specific — this drives the register of every recommendation.
  relevance_clause: "Why this matters to you:"
  show_scores: true
  report_title: "NAME — Staging Document (candidate queue)"   # 3a output
  vox_title: "NAME — Full Product Title"                      # 3b output, reader-facing
  deliverable_name: "NAME_v[YYYYMMDD]"                        # 3b filename
  sections: []
  notes: >
    Anything domain-specific that does not fit above. Every domain ends at a
    vox, so vox_title and deliverable_name are always required - the staging
    document is a machine artifact on the way there, not the deliverable.
```
