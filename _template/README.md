# [DOMAIN]

*Sanctum domain. One paragraph: what this domain watches, and for whom.*

## Who this serves

The reader, their maturity, and what success looks like. **"They were not
surprised" and "they acted" are different standards** and lead to different
scoring — say which one applies.

## Where it stops

**At the vox.** Every domain does — tenet 9, not a per-domain choice. 3a makes
the staging document (machine, reproducible, not committed); 3b makes the vox
(human, committed to `editions/`). Whatever happens to the vox afterward is
stages 4-6 and outside Sanctum.

## Running it

```
./run.sh <domain>
```

## Files

| File | What it holds |
|---|---|
| `pnd.md` | Everything the engine reads |
| `vocab.md` | Why the word lists say what they say |
| `decomposition.md` | Requirements down to the collectable-fact layer |
| `mandate.md` | Standing directives and the lessons log |

See `../DOMAINS.md` for the full contract and for which document owns which
fact.

## Adapting it

What to swap to point this domain at a different area of interest — usually the
geography group and the area-specific sensors. The engine and the shared
doctrine never change.
