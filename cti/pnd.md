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
  Logs `WARNING no text` on every single cycle from 2026-08-05 onward. This path is retired.
  **Corrected 2026-08-23:** a live feed does exist at `feeds.megaphone.fm/cyberwire-daily-podcast`,
  publishing daily with substantive descriptions. It was refused for a different and better
  reason: every item is a multi-story daily roundup. One item would fire `kev`, `incident`,
  `ransom` and `supplychain` at once and ride the multiplier stack to a high score every day,
  with no single event to place in a section and no per-story URL to cite. Its selected-reading
  list is also drawn from outlets already collected here. Do not reintroduce on the grounds
  that "a feed exists now" — the shape is the objection.
- Google-News query `("CISA Region 9" OR "CISA California")` — 0 new in 9 runs, 0 lifetime, and
  the identical `no text` failure every cycle. The query matches nothing, so Google returns an
  empty feed, which falls to the page path and yields nothing extractable. Too narrow.

Wanted but not collectable — checked 2026-08-23, do not re-search without new evidence:

- **Dragos** (`dragos.com`) publishes no RSS feed. Ten conventional paths tested from the
  collector host — `/blog/feed/`, `/feed/`, `/blog/rss.xml`, `/blog/index.xml`, `/rss.xml`,
  `/blog/atom.xml`, `/index.xml`, `/blog/rss/`, `dragos.com/feed`, `/resources/feed/` — all
  404 or redirect to nothing. This is the one vendor whose telemetry covers the water,
  wastewater and utility sectors named in the `sector` group, and its OT threat landscape
  reporting is the reference work in that space, so the loss is real and worth recording.
  **It is blocked on the same engine gap as Cal-CSIC:** `process_page` never revisits a page
  source, so page-type collection is a one-shot. That fix now has a second use case forcing
  it, which is the bar this repo sets for building something.

Note: a source that returns neither feed entries nor extractable text is **retried in full every
cycle** — `process_page` returns before recording the URL in `seen.txt`, so there is no
suppression. Both of the above burned a fetch per cycle for nine cycles.


Added 2026-08-19, verified from the collector host before loading (9 items, HTTP 200
on `industrialcyber.co/feed/`; the `/rss/` path 307s to nothing and `/feed/rss/` 301s to
the same content):

- `industrialcyber.co/feed/` — industrial and operational-technology trade press. Serves
  PIR-2 sector targeting, where coverage was thin: before this the only ICS/OT-relevant
  sensors were the SANS Internet Storm Center feed and one California water-and-utility
  news query. **Watch for two things** — whether it is additive or mostly re-reports what
  The Record and Hacker News already carry, and whether its vendor-heavy items clear the
  audience-portfolio filter. Re-assess after three cycles.

```sensors
# --- National: government / CERT / SLTT ---
https://www.cisa.gov/cybersecurity-advisories/all.xml
https://us-cert.cisa.gov/ncas/current-activity.xml
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
https://krebsonsecurity.com/feed/
https://googleprojectzero.blogspot.com/feeds/posts/default
https://www.bleepingcomputer.com/feed/
https://statescoop.com/feed/
# Added 2026-08-23. Found by auditing which outlets a CyberWire daily roundup cited:
# five of ten stories came from these two, and neither was collected here.
# SecurityWeek: use the first-party path, not feeds.feedburner.com/securityweek (same
# content behind a 302, and no reason to add a Feedburner dependency). NOTE: its feed
# window holds only 10 items — safe while collection runs daily, not if that changes.
https://www.securityweek.com/feed/
# The Register: SECTION feed only. The whole-site feed at /headlines.atom is a general
# tech magazine — git tooling, Microsoft trivia — and does not belong in this corpus.
https://www.theregister.com/security/headlines.atom
https://industrialcyber.co/feed/

# --- National: vendor telemetry ---
# Added 2026-08-23, every path verified from the collector host first. These
# vendors run incident response and sensor networks this effort will never have.
# When they publish, it is primary source. Marketing overhead is the price and
# the scorer sorts it out.
#
# Huntress: SMB and MSP telemetry — the closest commercial visibility there is
# to a low-maturity SLTT environment. Its output lands directly on vocabulary
# already declared here: n-able, n-central, kaseya, connectwise, screenconnect
# in lowmat_tech; rmm, msp, managed service provider in supplychain.
# NOTE: the feed window is 680 items — the whole blog archive, served every
# fetch. That is a ONE-TIME intake, not a rate; steady state is a few a week.
# Roughly half the archive is company news and educational content, which will
# score low and drop. That was a decision, not an oversight.
https://www.huntress.com/blog/rss.xml
# Google Threat Intelligence (absorbed Mandiant). Use the cloudblog host: the
# cloud.google.com path returns HTTP 200 with ZERO entries — live URL, no
# content, the exact failure the item count exists to catch.
https://cloudblog.withgoogle.com/topics/threat-intelligence/rss/
# Cisco Talos research. Distinct from the Cisco PSIRT advisory feed above —
# that is disclosures, this is investigation. First-party path, not the
# Feedburner mirror, which serves identical content.
https://blog.talosintelligence.com/rss/
# Microsoft Threat Intelligence. Distinct from the MSRC feed above, which is
# the patch catalogue. Low volume and a real marketing fraction — the weakest
# of these four and the first to drop at review. The old msrc-blog host is dead.
https://www.microsoft.com/en-us/security/blog/feed/

# --- National: breach registry ---
# Named-victim breach disclosure. Low volume (~2-3 per cycle). NOTE: the item
# date is the date the breach was LOADED, not the date it happened, so the
# recency gate will not flag a years-old breach loaded yesterday. The first
# sentence of every description states the actual breach month — read it.
https://haveibeenpwned.com/feed/breaches/

# --- Regional AOR: official sources (example: California) ---
https://www.news.caloes.ca.gov/feed/
https://www.cdt.ca.gov/newsroom/feed/

# --- Regional AOR: municipal press (example: California) ---
# California City News, cybersecurity section. EXPECTED YIELD IS ~3 ITEMS PER YEAR:
# 12 items span Sep 2022 to Mar 2026. A column of `0 new of 12 returned` in the log is
# NORMAL for this sensor and is not a failure — it serves its whole back catalogue every
# fetch. Kept because nothing else here emits a named California municipal victim
# (Long Beach, El Cerrito, Contra Costa), and because it carries local-government policy
# items — closed-session law, grant programs — that no general news query surfaces.
# Review yield 2026-11-23.
https://www.californiacitynews.org/taxonomy/term/1717/feed

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
        all:
          - {not: {group: listicle, scope: title}}
          - any:
              - all:
                  - {group: geo, scope: title}
                  - {group: incident, scope: blob}
              - all:
                  - {group: geo, scope: blob}
                  - {group: incident, scope: blob}
                  - {proximity: {a: geo, b: incident, window: 120}}
    - id: 2
      name: "SLTT-sector targeting (sector as subject)"
      weight: 4.0
      require:
        all:
          - {not: {group: listicle, scope: title}}
          - any:
              - all:
                  - {group: sector, scope: title}
                  - {group: incident_broad, scope: blob}
              - {proximity: {a: sector, b: incident_broad, window: 80,
                             scope: blob, all_occurrences: true}}
    - id: 3
      name: "Exploited flaw in SLTT-common tech"
      weight: 2.0
      require:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: exploit_strong, scope: blob}
          - {group: lowmat_tech, scope: blob}
          - {proximity: {a: lowmat_tech, b: exploit_strong, window: 200,
                         scope: blob, all_occurrences: true}}
    - id: 4
      name: "broad/national with SLTT relevance"
      weight: 1.0
      require: always

  multipliers:
    - name: "KEV / actively exploited"
      factor: 1.5
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: exploit_strong, scope: blob}
          - any:
              - {proximity: {a: exploit_strong, b: cve, window: 200,
                             scope: blob, all_occurrences: true}}
              - {proximity: {a: exploit_strong, b: lowmat_tech, window: 200,
                             scope: blob, all_occurrences: true}}
    - name: "low-maturity SLTT tech"
      factor: 1.5
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - any:
              - {group: lowmat_tech, scope: title}
              - {proximity: {a: lowmat_tech, b: exploit_strong, window: 200,
                             scope: blob, all_occurrences: true}}
              - {proximity: {a: lowmat_tech, b: incident_broad, window: 120,
                             scope: blob, all_occurrences: true}}
    - name: "supply-chain / procurement"
      factor: 1.3
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - any:
              - {group: supplychain, scope: title}
              - {proximity: {a: supplychain, b: incident_broad, window: 120,
                             scope: blob, all_occurrences: true}}
    - name: "ransomware vs public-sector/CI"
      factor: 1.3
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - {proximity: {a: ransom, b: ci, window: 150,
                         scope: blob, all_occurrences: true}}

  # FLOORS raise a score to a minimum. They never lower one and never force the
  # surface - the item becomes visible for review at the bottom of the surface
  # instead of being guaranteed a place. Use where the signal is authoritative
  # but its relevance to this domain is unproven.
  floors:
    - name: "CISA directive on technology not on the SLTT list"
      score: 2.0
      when:
        all:
          - {not: {group: listicle, scope: title}}
          # AUTHORITATIVE SOURCE ONLY. A trade write-up saying "CISA ordered a
          # patch" is a secondary mention; this must be the directive itself.
          - {group: cisa_source, scope: source}
          - {group: exploit_strong, scope: blob}
          # Only when the product is NOT on the low-maturity list. When it is,
          # tier 3 and force-surface M2 already handle it and score higher.
          - {not: {group: lowmat_tech, scope: blob}}

  force_surface:
    - name: "M1 in-AOR entity in an incident"
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - any:
              - all:
                  - {group: geo, scope: title}
                  - {group: incident, scope: blob}
              - {proximity: {a: geo, b: incident, window: 120,
                             scope: blob, all_occurrences: true}}
    - name: "M2 exploited flaw affecting SLTT-relevant technology"
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: exploit_strong, scope: blob}
          - {group: lowmat_tech, scope: blob}
          - {proximity: {a: lowmat_tech, b: exploit_strong, window: 200,
                         scope: blob, all_occurrences: true}}
    - name: "M3 SLTT sector in an incident"
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - any:
              - all:
                  - {group: sector, scope: title}
                  - {group: incident_broad, scope: blob}
              - {proximity: {a: sector, b: incident_broad, window: 80,
                             scope: blob, all_occurrences: true}}

  settings:
    surface_min_score: 2.0
    empty_title: {score: 0.5, tier: 4, flag: "FLAG: empty title (feed artifact - verify source)"}
    recency:
      enabled: true
      window_days: 7
      cutoff_weekday: monday
      cutoff_time: "05:00"
      timezone: America/Los_Angeles
    grouping:
      enabled: true
      similarity: 0.15
      min_shared_tokens: 3
      min_evidence: 8.0
      max_group_size: 25
      max_group_display: 12

  word_boundary_terms: ["scada", "ransom", "cisco", "how to", "what is", "hacker"]

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
    # CONFIDENTIALITY language only, by decision. Availability terms (outage,
    # denial of service, ddos) are deliberately NOT here - see `targeting`.
    # This group feeds tier 1 and force-surface M1, which need only a place
    # name plus one of these words, so a California wildfire or public safety
    # power shutoff would become an AOR cyber incident.
    # P&D work order 2026-08-24, decision 4.
    incident: ["breach", "ransomware", "cyberattack", "cyber attack", "hacked",
               "hackers", "stolen data", "data theft", "blackmail", "defaced",
               "defacement",
               "data breach", "compromise", "exfiltrat", "extortion", "data leak",
               "data stolen", "records stolen", "security incident"]
    # Attack, disruption and availability language. Reaches rules ONLY through
    # `incident_broad`, which is used where the sector must already be the
    # subject - so availability terms can never reach tier 1.
    targeting: ["active threat", "outage", "denial of service", "ddos",
                "exploited against", "attacks against", "attack against",
                "campaign against", "targeted", "target of", "attack on",
                "attacks on", "hit by", "struck by", "victim of", "taken offline",
                "forced offline", "systems offline", "service disruption",
                "state of emergency", "disrupted operations", "shut down its",
                "knocked offline"]
    # The union of `incident` and `targeting`, PLUS the singular "hacker".
    # Keep it as that union: a term added to either parent belongs here too.
    # "hacker" lives ONLY here, never in `incident`, because it is noise-prone
    # - "ethical hacker", "hacker conference", the feed name "The Hacker News".
    # Confined here it can only fire where the sector is already the subject.
    # ON WATCH: if it over-fires next cycle, drop it and keep only "hackers".
    incident_broad: ["breach", "ransomware", "cyberattack", "cyber attack", "hacked",
                     "hackers", "hacker", "stolen data", "data theft", "blackmail",
                     "defaced", "defacement",
                     "data breach", "compromise", "exfiltrat", "extortion", "data leak",
                     "data stolen", "records stolen", "security incident",
                     "active threat", "outage", "denial of service", "ddos",
                     "exploited against", "attacks against", "attack against",
                     "campaign against", "targeted", "target of", "attack on",
                     "attacks on", "hit by", "struck by", "victim of", "taken offline",
                     "forced offline", "systems offline", "service disruption",
                     "state of emergency", "disrupted operations", "shut down its",
                     "knocked offline"]
    sector: ["water utility", "water utilities", "water district", "water authority",
             "water sector", "utility sector", "public works", "transit authority",
             "school system", "public schools",
             "water treatment", "water system", "drinking water", "wastewater",
             "utility district", "public utility", "electric utility",
             "school district", "k-12", "k12", "higher ed", "community college",
             "university", "municipal", "city government", "county government",
             "local government", "tribal government", "tribal nation",
             "public sector", "election office", "election systems",
             "registrar of voters", "transit agency", "special district",
             "sheriff's office", "sheriff's department", "police department",
             "superior court", "county court"]
    lowmat_tech: ["fortinet", "fortigate", "sonicwall", "mikrotik", "routeros", "openwrt",
                  "sharepoint", "exchange server", "vpn", "rdp", "n-able", "n-central",
                  "kaseya", "connectwise", "screenconnect", "wordpress", "plc",
                  "programmable logic controller", "scada", "ics", "operational technology",
                  "cisco", "netgear", "tp-link", "router", "firewall"]
    exploit_strong: ["actively exploited", "exploited in the wild", "in-the-wild",
                     "under active exploitation", "added to its known exploited",
                     "added to the known exploited", "kev catalog", "cisa kev",
                     "exploitation in the wild", "weaponized exploit",
                     "public proof-of-concept", "proof-of-concept exploit",
                     "exploit code is available", "being exploited",
                     "active threat", "active exploitation", "ongoing exploitation",
                     "observed exploitation", "actively targeting"]
    kev: ["cisa kev", "known exploited", "actively exploited", "exploited in the wild",
          "in-the-wild", "added to its known exploited", "kev catalog",
          "zero-day", "0-day", "under active exploitation"]
    cve: ["cve-"]
    # Matched against the `source` scope, never the article text.
    cisa_source: ["cisa.gov"]
    listicle: ["top 5", "top 7", "top 10", "top 12", "top 15", "top 20", "top 25",
               "biggest", "ranked", "you should know", "ultimate guide",
               "buyer's guide", "buyers guide", "roundup", "round-up",
               "best solutions", "best software", "best tools", "best vpn",
               "best antivirus", "best firewall", "best wireless", "best wi-fi",
               "best security", "cheat sheet", "what is", "how to",
               "explained:", "a beginner's guide", "everything you need to know"]
    supplychain: ["supply chain", "supply-chain", "npm", "pypi", "package", "dependency",
                  "third-party", "vendor compromise", "msp", "managed service provider",
                  "rmm", "procurement", "software supply"]
    ransom: ["ransomware", "ransom", "extortion", "encrypt", "leak site", "double extortion"]
    ci: ["critical infrastructure", "water utility", "water district", "water treatment",
         "wastewater", "drinking water", "power grid", "electric grid",
         "hospital", "healthcare", "public sector", "local government",
         "municipal", "school district", "public utility"]
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
  # ---- Stage 3b (exploitation) — the domain's answers to ../docs/EXPLOITATION.md ----
  # The generic method lives in docs/EXPLOITATION.md at the repo root. These are the
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
