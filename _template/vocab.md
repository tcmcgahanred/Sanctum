# [DOMAIN] — Vocabulary decisions

*Sanctum · `_template` · the reasoning behind the word lists in `pnd.md`.*

**Version:** v1 — established [DATE].

> **This file never repeats the term lists.** `pnd.md` is the single source of
> truth for terms. This records *decisions about* terms — what was dropped and
> why, what collides, when each group was last reviewed. Two copies of the same
> words drift within a month, and the copy nobody runs is the one that gets
> edited. See `../VOCABULARY.md`.

---

## v1 changelog

1. Initial vocabulary built. Record how — by enumeration, or derived from
   indicators (`../VOCABULARY.md` §3). If by the indicator method, **say so** —
   that method has never been validated and someone needs to find out whether it
   works.

---

## Open findings

*One heading per unresolved issue. Record, do not silently fix — vocabulary
content is a Planning & Direction decision.*

### Finding 1 — [title]

**Severity: [low/medium/high]. [Unresolved / Accepted / Closed DATE].**

What is wrong, what evidence showed it, and what the options are. If two clean
fixes exist and both change matching, that is a P&D call and belongs upstream,
not in a maintenance pass.

---

## Collision table

Checked against the classes in `../VOCABULARY.md` §1. The triage rule: **drop a
noisy term only when an exact synonym exists.** Where none does, keep it, accept
the noise, and note it here so the next reader knows it was a decision.

| Term | Collides with | Status |
|---|---|---|
| | | |

---

## Group review status

```yaml
vocab:
  review_interval_days: 180        # domain-wide default
  groups:
    primary:
      reviewed: 2026-01-01         # SET THIS AS YOU CREATE THE GROUP.
                                   # A date added later is a guess.
    secondary:
      reviewed: 2026-01-01
    urgency:
      reviewed: 2026-01-01
      review_interval_days: 90     # override for groups that age fast

  # Terms removed from pnd.md, with the reason. vocab_check.py errors if any of
  # these is still live — that is the drift this two-file split exists to stop.
  dropped: []

  # Findings you have seen and consciously accepted. Downgraded to NOTED; they
  # keep printing on every run. Silence is not on the menu.
  accepted: []
```

---

## Verification status

**Not validated until tested against live output** (`../VOCABULARY.md` §7):

- [ ] `tools/vocab_check.py <domain>` passes
- [ ] Known-good items score where expected
- [ ] Drop list read before the candidate list for the first three cycles
- [ ] `surface_min_score` measured against the real corpus, not left provisional
