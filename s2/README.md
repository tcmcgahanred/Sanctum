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
| `pnd.md` | Everything the engine reads |
| `vocab.md` | Why the word lists say what they say |
| `requirements.md` | KIQ → PIR → SIR → EEI, each mapped to a sensor |
| `mandate.md` | Standing directives and the lessons log |

See `../DOMAINS.md` for the full contract and for which document owns which
fact.

## Read this before judging the output

`requirements.md` decomposes the requirements into 43 collectable facts and
tags each with sensor coverage. **One is confidently covered. Fifteen have
none.** The second-ranked requirement — conditions that degrade rotary-wing
operations — is effectively uncollected.

That is a collection finding, not a scoring defect. Ranking operates only on
what already arrived, and no vocabulary can surface something the sensors never
fetched. **Expect the early surfaces to be thin, and read that as a statement
about the sensor set.** The sensor-build roadmap is Byproduct 1 in
`requirements.md`.

## Adapting it

To point this domain at a different area of interest, swap the geography group
and the area-specific sensors. The platform, threat-system, and conflict groups
travel unchanged — they describe what threatens rotary wing anywhere, which is
deliberate: the aviation mission is constant, the theatre is an assignment.

The engine and the shared doctrine never change.
