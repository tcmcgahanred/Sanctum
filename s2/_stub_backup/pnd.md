# S2 — Planning & Direction (P&D)  ·  TEMPLATE / STUB

*Sanctum · S2 domain config. **NOT operational.** This is the empty P&D template
for the future CANG Aviation S2 effort. The `core/` engines are already agnostic —
fill in the blocks below with real S2 requirements and `run.sh s2` will run the
same collect→score machinery for this domain. Do not build until S2 is a real,
active requirement (see `../ROADMAP.md`).*

**BLUF:** Copy the structure of `../cti/pnd.md`, swap in S2 sensors, an IPB-flavored
scoring model, and S2 production sections. Nothing here is filled in.

---

## Manifest

```yaml
manifest:
  domain: s2
  base_dir: /opt/ravenor            # or wherever S2 runs; override with $SANCTUM_BASE
  sensors_file: references/sensors.txt  # FALLBACK ONLY — put feeds in the ## Sensors block below
  corpus:
    backend: rclone
    rclone_remote: gdrive:s2-corpus   # give S2 its own corpus store
  collection:
    window_days: 7
    min_title_len: 15
    suffix_separators: [" - ", " | ", " — "]
```

---

## Sensors — Collection feed list

The S2 feed list. One URL per line inside the fenced `sensors` block; blank lines
and `#` comments ignored. Fill this in with S2's sources.

```sensors
# Add S2 feed URLs here, one per line.
```

---

## Scoring  (IPB, not CTI — replace every group and rule)

The engine reads the SAME schema as CTI: `tiers[]` (highest qualifying wins),
`multipliers[]`, `groups{}`, `word_boundary_terms[]`, `settings{}`. The doctrine
differs — S2 prioritizes against IPB frameworks (MCOO, OAKOC, METT-TC, ASCOPE,
PMESII-PT), not SLTT sectors. The placeholders below show the shape; the terms are
illustrative only and must be defined against real S2 information requirements.

```yaml
scoring:
  tiers:
    - id: 1
      name: "AO-direct (named area of interest / unit)"
      weight: 8.0
      require:
        any:
          - {group: aoi, scope: blob}     # define aoi terms for the real AO
    - id: 2
      name: "PIR-relevant activity"
      weight: 4.0
      require:
        any:
          - {group: pir_activity, scope: blob}
    - id: 4
      name: "broad/background"
      weight: 1.0
      require: always

  multipliers:
    - name: "time-sensitive"
      factor: 1.5
      when: {group: time_sensitive, scope: blob}

  settings:
    surface_n: 55
    empty_title: {score: 0.5, tier: 4, flag: "FLAG: empty title (verify source)"}

  word_boundary_terms: []

  groups:
    aoi: []            # named areas of interest / units / geography  — FILL IN
    pir_activity: []   # activity that answers S2 PIRs                 — FILL IN
    time_sensitive: [] # indicators of immediacy                       — FILL IN
```

---

## Production

```yaml
production:
  report_title: "S2 — Pre-Filtered Candidate Queue"
  item_target: [5, 8]
  sections: []        # S2 staging sections (define against IPB products) — FILL IN
  notes: >
    Sanctum stops at the staging document. Finished S2 products (IPB overlays:
    MCOO/OAKOC/etc.) are produced manually downstream, out of scope for the engine.
```
