# CTI — Planning & Direction (P&D)

*Sanctum · CTI domain config. This file is BOTH the human-readable P&D and the
machine config the engines consume. Prose is for you; the engines read only the
fenced `yaml` blocks below. The requirements tree lives in `requirements.md`, the operating doctrine in `mandate.md`, the product spec in `vox_policy.md`;
this file is where Planning & Direction is turned into the parameters that drive
Collection, Processing & Exploitation, and Analysis & Production.*

**BLUF:** Everything domain-specific about the CTI effort lives here. The `core/`
engines are generic — swap this file (and `sensors.txt`) for another domain's and
the same code runs any other domain.

---

## Manifest — runtime, storage, portability

Where the corpus lives and how collection is tuned. `base_dir` is the one
host-coupled value; override it per host with the `SANCTUM_BASE` env var (wins
over this) so the repo itself stays portable. To move Sanctum to another server:
set `SANCTUM_BASE` (or edit `base_dir`), point `rclone_remote` at your storage,
`pip install -r requirements.txt`, and run.

```yaml
manifest:
  domain: cti
  base_dir: /opt/ravenor            # current host; override with $SANCTUM_BASE
  sensors_file: references/sensors.txt  # FALLBACK ONLY — feeds live in the ## Sensors block below
  corpus:
    backend: rclone                 # rclone | local | (s3 future)
    rclone_remote: gdrive:ravenor-corpus
  staging:                          # where the analyst picks the draft up
    backend: rclone
    rclone_remote: gdrive:ravenor-staging
    filename: "WCTI_{date}_STAGING.md"   # {date} -> YYYYMMDD (collection date)
  collection:
    window_days: 7                  # rolling collection window
    min_title_len: 15               # below this, don't title-dedup
    suffix_separators: [" - ", " | ", " — "]
```

---

## Sensors — Collection feed list

The feeds the collector reads. One URL per line inside the fenced `sensors` block;
blank lines and `#` comments are ignored. **This block is the single source of the
feed list** — edit feeds here. Add a feed only if it is reliable AND additive; verify
it against the host's egress first; drop noisy sources. Do not reintroduce the dropped
34 county Google-News keyword feeds.

Also dropped 2026-08-11, verified against 9 cycles of `collector.log` — do not reintroduce
without new evidence:

- `thecyberwire.com/feeds/rss.xml` — 0 new in 9 runs, and **0 lifetime**. Returns no parseable
  feed entries, so Acolyte falls through to `process_page`, which then extracts no text either.
  Logs `WARNING no text` on every single cycle from 2026-08-05 onward. The publisher (now N2K
  CyberWire) no longer advertises any RSS feed on its site; this path appears retired.
- Google-News query `("CISA Region 9" OR "CISA California")` — 0 new in 9 runs, 0 lifetime, and
  the identical `no text` failure every cycle. The query matches nothing, so Google returns an
  empty feed, which falls to the page path and yields nothing extractable. Too narrow.

Note: a source that returns neither feed entries nor extractable text is **retried in full every
cycle** — `process_page` returns before recording the URL in `seen.txt`, so there is no
suppression. Both of the above burned a fetch per cycle for nine cycles.

On notice: `packetstormsecurity.com/feeds/news/` (1 new in 9 runs).

```sensors
# --- National: government / CERT / SLTT ---
https://www.cisa.gov/cybersecurity-advisories/all.xml
https://us-cert.cisa.gov/ncas/current-activity.xml
https://www.cisecurity.org/feed/advisories
https://www.cisecurity.org/feed/alert
https://www.kb.cert.org/vulfeed
https://www.nist.gov/blogs/cybersecurity-insights/rss.xml
https://jvn.jp/en/rss/jvn.rdf

# --- National: vendor PSIRTs ---
https://api.msrc.microsoft.com/update-guide/rss
https://sec.cloudapps.cisco.com/security/center/psirtrss20/CiscoSecurityAdvisory.xml
https://security.paloaltonetworks.com/rss.xml
https://www.fortiguard.com/rss/ir.xml

# --- National: exploitation evidence ---
https://www.greynoise.io/blog/rss.xml
https://www.rapid7.com/blog/rss/
https://www.zerodayinitiative.com/rss/published/
https://blog.qualys.com/feed

# --- National: news / research ---
https://therecord.media/feed/
https://unit42.paloaltonetworks.com/feed/
https://feeds.feedburner.com/TheHackersNews
https://isc.sans.edu/rssfeed_full.xml
https://www.schneier.com/feed/atom/
https://www.darkreading.com/rss.xml
https://securelist.com/feed/
https://news.sophos.com/en-us/category/threat-research/feed/
https://www.crowdstrike.com/blog/feed/
https://www.recordedfuture.com/feed/
https://www.tenable.com/blog/feed
https://feeds.feedburner.com/hackread
https://feeds.feedburner.com/TroyHunt
https://www.infosecurity-magazine.com/rss/news/
https://cybersecuritynews.com/feed/
https://bartblaze.blogspot.com/feeds/posts/default
https://packetstormsecurity.com/feeds/news/
https://seclists.org/rss/fulldisclosure.rss
https://krebsonsecurity.com/feed/
https://googleprojectzero.blogspot.com/feeds/posts/default
https://www.bleepingcomputer.com/feed/
https://statescoop.com/feed/

# --- Regional AOR: official sources (example: California) ---
https://www.news.caloes.ca.gov/feed/
https://www.cdt.ca.gov/newsroom/feed/

# --- Regional AOR: statewide / sector queries (example: California) ---
https://news.google.com/rss/search?q=%22California%22%20(ransomware%20OR%20%22data%20breach%22%20OR%20cyberattack)&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(%22community%20college%22%20OR%20university%20OR%20CSU%20OR%20UC)%20(ransomware%20OR%20%22data%20breach%22)&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20%22school%20district%22%20(ransomware%20OR%20cyberattack%20OR%20%22data%20breach%22)&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(%22special%20district%22%20OR%20%22transit%20agency%22%20OR%20%22public%20works%22)%20(cyberattack%20OR%20ransomware%20OR%20breach)&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(city%20OR%20county)%20(ransomware%20OR%20cyberattack%20OR%20%22data%20breach%22)&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(court%20OR%20%22superior%20court%22%20OR%20sheriff%20OR%20%22police%20department%22)%20(ransomware%20OR%20cyberattack%20OR%20breach)&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(election%20OR%20%22registrar%20of%20voters%22)%20(cyberattack%20OR%20breach%20OR%20hack)&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20government%20(ransomware%20OR%20cyberattack)&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(hospital%20OR%20health%20OR%20clinic)%20(ransomware%20OR%20%22data%20breach%22)&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20tribal%20(casino%20OR%20nation%20OR%20government)%20(ransomware%20OR%20cyberattack%20OR%20breach)&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(water%20OR%20wastewater%20OR%20utility)%20(cyberattack%20OR%20hack%20OR%20breach)&hl=en-US&gl=US&ceid=US:en
```

---

## Scoring — Processing & Exploitation

The multiplicative model, verbatim from the CTI doctrine: a base **tier weight**
(highest qualifying tier only; tiers don't stack) times the product of any
**elevation multipliers** (absent = neutral). Tier 1 requires California to be the
**subject of an incident** — either California in the title *and* an incident word
present, or a California term within ~120 chars of an incident word in the body —
not a passing mention. Groups are keyword lists; short/ambiguous ones match on
word boundaries.

**Score = (tier weight) × (product of elevation multipliers)**

### Why the model is shaped this way

*Moved here from `codex.md` Layers 3–4 on 2026-08-17, when that file was retired.
The rationale now sits beside the values it explains, so tuning a number and
leaving the reasoning stale is no longer possible.*

**Convergence wins, and the tier spacing is chosen to allow it.** 8/4/2/1 is
deliberately narrow enough that a heavily-elevated lower-tier item **can**
outrank a bare higher-tier one. That is intended: a multi-signal active campaign
against an out-of-state school is allowed to lead over a quiet in-AOR breach
carrying no urgency signals. Convergence across requirements is a stronger
priority signal than geography alone.

Worked, using the values below:

| Item | Calculation | Score |
|---|---|---|
| CA water utility breach, no elevation signals | 8.0 × 1 | **8.0** |
| Out-of-state school ransomware on common tech (KEV + low-maturity + ransomware) | 4.0 × 1.5 × 1.5 × 1.3 | **11.7** — *outranks the bare CA item, by design* |
| National KEV vuln in SLTT-common tech (KEV + low-maturity) | 2.0 × 1.5 × 1.5 | **4.5** |
| Broad supply-chain story | 1.0 × 1.3 | **1.3** |

**Tiers are not additive with each other.** An item takes its single highest
qualifying tier weight — something both AOR-direct and sector-targeting is tier 1,
not 8+4. Only the elevation multipliers stack.

**An absent multiplier is neutral (×1.0), never suppressive.** A maximally
relevant item with no urgency signals must never be scored toward zero.

**Round up on uncertainty.** If an item's tier or a multiplier is ambiguous,
score it as though the higher interpretation were true. Ambiguity resolves
toward visibility, not away from it — same asymmetry as the surfacing rules:
a false positive costs a few seconds of skimming, a false negative means a real
threat never reaches the analyst.

**Why there is no score handicap.** Discounting automated scores by a flat factor
assumes the bias runs consistently in one direction. It does not — scoring errors
are inconsistent, sometimes high and sometimes low, so a handicap gives false
comfort while catching none of the real errors. Transparency is the chosen
safeguard instead: visible reasoning on every surfaced item, plus a full drop
list. That catches what a correction factor would miss.

**The drop list is mandatory and is what makes a generous cut safe.** Everything
below the threshold is still listed by title. *Dropped* never means *invisible* —
the analyst eyeballs the discards in seconds and rescues anything mis-scored.

```yaml
scoring:
  tiers:
    - id: 1
      name: "AOR-direct (CA subject of an incident)"
      weight: 8.0
      require:
        any:
          - all:
              - {group: geo, scope: title}
              - {group: incident, scope: blob}
          - all:
              - {group: geo, scope: blob}
              - {group: incident, scope: blob}
              - {proximity: {a: geo, b: incident, window: 120}}
    - id: 2
      name: "SLTT-sector targeting"
      weight: 4.0
      require:
        any:
          - {group: sector, scope: blob}
    - id: 3
      name: "KEV in SLTT-common tech"
      weight: 2.0
      require:
        all:
          - {group: kev, scope: blob}
          - {group: lowmat_tech, scope: blob}
    - id: 4
      name: "broad/national with SLTT relevance"
      weight: 1.0
      require: always

  multipliers:
    - name: "KEV / actively exploited"
      factor: 1.5
      when: {group: kev, scope: blob}
    - name: "low-maturity SLTT tech"
      factor: 1.5
      when: {group: lowmat_tech, scope: blob}
    - name: "supply-chain / procurement"
      factor: 1.3
      when: {group: supplychain, scope: blob}
    - name: "ransomware vs public-sector/CI"
      factor: 1.3
      when: {all: [{group: ransom, scope: blob}, {group: ci, scope: blob}]}

  # ---------------------------------------------------------------------
  # FORCE-SURFACE — Vox Policy §7 mandatory-surface rule. Inclusion, not
  # ranking: a match guarantees the item reaches the surface regardless of
  # score. Score still orders everything, so a forced low-score item sits at
  # the bottom of the surface, marked — a visible ranking/relevance
  # disagreement, which is a tuning signal rather than a miss.
  #
  # ⚠ M1 and M3 ARE APPROXIMATIONS. The policy specifies "subject-of-incident
  # logic" — that the AOR entity is the SUBJECT of the attack. Sanctum has no
  # subject detection; these rules fire on CO-OCCURRENCE of a place (or sector)
  # and an incident word in the same article. They will over-fire on national
  # round-ups that mention California in passing. Over-firing is the safe
  # direction (tenet 8) but the surface will carry noise until subject-of
  # detection exists. This is a Planning & Direction item, not a config tweak.
  #
  # ⚠ M2 IS PARTIAL. The policy wants in-the-wild exploitation OR a weaponised
  # public PoC OR a KEV addition. Only `kev` exists as a group today; there is
  # no exploitation vocabulary. M2 therefore fires on KEV + SLTT-relevant tech
  # and misses the other two triggers.
  force_surface:
    - name: "M1 in-AOR entity in an incident"
      when: {all: [{group: geo, scope: blob}, {group: incident, scope: blob}]}
    - name: "M2 KEV listing affecting SLTT-relevant technology"
      when: {all: [{group: kev, scope: blob}, {group: lowmat_tech, scope: blob}]}
    - name: "M3 SLTT sector in an incident"
      when: {all: [{group: sector, scope: blob}, {group: incident, scope: blob}]}

  settings:
    # SURFACE-VS-DROP is a score threshold, never a count. Vox Policy §7
    # forbids a cap: "the count is an OUTPUT of the scoring and rules, never a
    # target imposed on top of them." `surface_n: 55` was exactly such a cap,
    # and it also made the force-surface guarantee below impossible.
    #
    # PROVISIONAL VALUE — 2.0 is the tier-3 weight, so an item surfaces if it
    # reached tier 3 or better, or if multipliers lifted a tier-4 item to 2.0.
    # This has never been measured against the live corpus. Check the surfaced
    # count on the first real run and tune. If the surface is too big, tune the
    # weights or the vocabulary; do NOT reintroduce a cap.
    surface_min_score: 2.0
    empty_title: {score: 0.5, tier: 4, flag: "FLAG: empty title (feed artifact — verify source)"}
    recency:                       # Codex Layer 4 — flag stale-by-publish-date, never drop
      enabled: true
      window_days: 7               # cycle window length (ends at the cutoff below)
      cutoff_weekday: monday       # ICOD day
      cutoff_time: "05:00"         # ICOD time — matches the 0500 collector run
      timezone: America/Los_Angeles
    grouping:                      # near-duplicate EVENT grouping — display only
      enabled: true                # never merges, never drops, never re-scores
      similarity: 0.15             # IDF-weighted Jaccard on titles; >= this joins a group head
      min_shared_tokens: 3         # ...and at least this many words in common, as a floor
      min_evidence: 8.0            # ...and the shared words must carry this much information
                                   #    (blocks formulaic advisory titles that overlap heavily
                                   #     but say nothing distinctive in common)
      max_group_size: 25           # a cluster bigger than this is template-matching, not an
                                   #    event — dissolved, items shown normally, noted in header
      max_group_display: 12        # cap children shown per group; the rest stay in the drop list

  # Only terms that are BOTH live in a group AND longer than 4 characters
  # belong here — core/rules.py applies boundaries automatically at <=4, so a
  # shorter entry does nothing. Seven of the previous eleven entries were dead:
  # "hack", "leak" and "war" matched no live term at all, and "ics", "grid",
  # "uc", "csu" were already covered by the length rule. All seven removals are
  # provable no-ops and the parity test confirms scoring is unchanged.
  # Verified by tools/vocab_check.py — reasoning in cti/vocab.md.
  word_boundary_terms: ["scada", "ransom", "court", "cisco"]

  groups:
    geo: ["california", "californian", " calif ", "sacramento", "fresno",
          "modesto", "stockton", "bakersfield", "cal oes", "cal-csic", "ccic",
          "caltrans", "csu ", "uc ", "calmatters",
          "alpine county", "amador county", "butte county", "calaveras county",
          "colusa county", "el dorado county", "fresno county", "glenn county",
          "inyo county", "kern county", "kings county", "lake county",
          "lassen county", "madera county", "mariposa county", "mendocino county",
          "merced county", "modoc county", "mono county", "nevada county",
          "placer county", "plumas county", "sacramento county", "san joaquin county",
          "shasta county", "sierra county", "stanislaus county", "sutter county",
          "tehama county", "trinity county", "tulare county", "tuolumne county",
          "yolo county", "yuba county"]
    incident: ["breach", "ransomware", "cyberattack", "cyber attack", "hacked",
               "data breach", "compromise", "exfiltrat", "extortion", "data leak",
               "data stolen", "records stolen", "security incident"]
    sector: ["water", "wastewater", "utility", "utilities", "school district",
             "k-12", "k12", "higher ed", "university", "college", "municipal",
             "city government", "county government", "local government", "tribal",
             "public sector", "election", "registrar of voters", "transit",
             "special district", "sheriff", "police department", "court"]
    lowmat_tech: ["fortinet", "fortigate", "sonicwall", "mikrotik", "routeros", "openwrt",
                  "sharepoint", "exchange server", "vpn", "rdp", "n-able", "n-central",
                  "kaseya", "connectwise", "screenconnect", "wordpress", "plc",
                  "programmable logic controller", "scada", "ics", "operational technology",
                  "cisco", "netgear", "tp-link", "router", "firewall"]
    kev: ["cisa kev", "known exploited", "actively exploited", "exploited in the wild",
          "in-the-wild", "added to its known exploited", "kev catalog",
          "zero-day", "0-day", "under active exploitation"]
    supplychain: ["supply chain", "supply-chain", "npm", "pypi", "package", "dependency",
                  "third-party", "vendor compromise", "msp", "managed service provider",
                  "rmm", "procurement", "software supply"]
    ransom: ["ransomware", "ransom", "extortion", "encrypt", "leak site", "double extortion"]
    ci: ["critical infrastructure", "water", "wastewater", "power", "grid",
         "hospital", "healthcare", "public sector", "government", "municipal",
         "school", "utility"]
```

---

## Production — Analysis & Production

Shapes the staging output and the human synthesis stage: the pre-filter report
title, the section taxonomy the analyst arranges items into, and the item-count
targets.

**No target on the review surface** (Vox Policy §7). The staging document and the
vox are review surfaces, and the number of items in them is an **output** of the
scoring and the force-surface rules — never a target set on top. This table
previously read *"~5–6 per content section, ~15–18 total"*; that was a cap, the
policy forbids caps, and it is gone:

| Artifact | When | Size |
|---|---|---|
| **Staging document** (3a) | Monday 0500 | **Uncapped.** Everything clearing `surface_min_score` or matching a `force_surface` rule |
| **Vox** (3b) | Monday | **Uncapped.** The operator cuts on judgement, not to a number |
| **Distributed report** | Thursday | 5–8 items — "restraint is the product" applies here, and this is **outside Sanctum's scope** |

If the surface is too large, tune the weights, the vocabulary, or the exclusion
operators. Do not reintroduce a cap: a cap hides what the scoring did and
destroys the feedback that tunes it. **The uncapped surface is the diagnostic.**

A wider surface pulls in **lower-ranked items from the same sorted
queue** — lower tier and/or fewer elevation signals. It does not lower the
standard. Every entry still
shows its scoring reasoning (tier + which multipliers fired) so the analyst can
audit where the cut falls.

*`arbites.py` reads only `report_title` from this block. What the surface actually
contains is decided by `scoring.settings.surface_min_score` and the `force_surface`
rules — a threshold plus guaranteed inclusions, never a count.*

```yaml
production:
  # ---- Stage 3b (exploitation) — the domain's answers to ../EXPLOITATION.md ----
  # The generic method lives in EXPLOITATION.md at the repo root. These are the
  # only parts of it that are CTI-specific.
  audience: >
    Low-maturity State/Local/Tribal/Territorial (SLTT) organisations in the AOR —
    counties, cities, school and special districts. They consume vendor software;
    they do not write code. Recommendations must be plain-language and
    minimal-tooling (IG1 CIS controls preferred), and lean on vendor
    accountability and procurement governance rather than engineering effort.
  relevance_clause: "Why an SLTT organization should care:"
  show_scores: true                    # R6 — carry the 3a score and reasoning per item
  # -----------------------------------------------------------------------------
  # Two documents, two names. 3a makes the staging document; 3b makes the vox.
  # Use these EXACTLY as written — no prefixes, no additions, no org initials.
  # "Vox" is INTERNAL shorthand and must never appear in the reader-facing
  # product (Vox Policy §3). No "CCIC" prefix until AOR-direct sensors exist.
  report_title: "WCTI — Staging Document (candidate queue)"   # 3a output, title
  vox_title: "WCTI — Weekly Cyber Threat Intelligence"         # 3b output, reader-facing heading
  # Vox Policy §7: NO fixed limit on items per section or overall. The former
  # staging_item_target [15,18] and staging_per_section [5,6] were exactly the
  # caps the policy forbids and have been removed. Restraint belongs to the
  # distributed product, applied by the team as editorial judgment — it is not
  # an automated cap on what surfaces for review.
  distributed_item_target: [5, 8]      # Thursday product — OUTSIDE Sanctum's scope; recorded for reference only
  sections: ["NEWS", "CTA TTPs", "LATEST ATTACKS OR RISKS", "KEYWORDS"]
  deliverable_name: "WCTI_v[YYYYMMDD]"           # 3b output, filename. date = distribution (Thu)
  notes: >
    Staging document and vox are content only, no handling markings, and are
    UNCAPPED - the item count is an output of the scoring and force-surface
    rules, never a target (Vox Policy section 7). The distributed product
    narrows to 5-8 and adds handling markings, and is outside Sanctum's scope.
    KEYWORDS is wave-tops, not items. Three dates on the distribution product:
    title = distribution (Thursday); ICOD line = collection cutoff
    (Monday 0500 PT); LTIOV planning-only, never printed.
```
