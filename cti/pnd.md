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
  reference_lists:                  # facts to look up instead of inferring
    kev:
      url: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
      json_path: vulnerabilities
      key_field: cveID
      match_pattern: "CVE-[0-9]{4}-[0-9]{4,7}"
      cache_hours: 12
  staging:                          # where the analyst picks the draft up
    backend: rclone
    rclone_remote: gdrive:ravenor-staging
    filename: "WCTI_{date}_STAGING.md"   # {date} -> YYYYMMDD (collection date)
  collection:
    window_days: 7                  # rolling collection window
    max_publish_age_days: 7         # reports older than this never enter the corpus
    min_title_len: 15               # below this, don't title-dedup
    suffix_separators: [" - ", " | ", " — "]
    fetch:
      user_agent: ""                # OFF. Setting one cost two sensors — see below
      timeout: 20                   # seconds per request
      sleep_time: 1.0               # polite pause between requests to one host
      max_redirects: 5
      min_extracted_size: 80        # characters; below this trafilatura returns nothing
      impersonate: chrome           # curl_cffi profile for the retry; "" disables it
      decode_google_news: true      # resolve news.google.com wrappers to the publisher
      gnews_interval: 1             # seconds between Google News resolutions
```

**`reference_lists` — declared, fetched, and NOT yet used for scoring.** The
`kev` entry points at CISA's Known Exploited Vulnerabilities catalogue: 1,675
entries, refreshed daily, verified reachable from the collector host on
2026-08-25. The scoring model currently earns its 1.5x exploitation multiplier
by matching phrases in prose, which has already been measured wrong — a real
CISA advisory said *"Active Threat"* rather than *"actively exploited"* and the
item fell from 7.8 to 1.5. The catalogue answers that question authoritatively.

Nothing in `core/rules.py` reads this list. **Whether the multiplier fires on
catalogue membership instead of, or alongside, the `kev` word group is a
Planning & Direction decision**, and `tools/kev_impact.py` measures what the
change would do to the real corpus so the decision is made against a number.

**`max_publish_age_days` — reports from outside the cycle window do not enter
the corpus.** Standing direction, 2026-08-25. Enforced at collection, before
any HTTP request is made, so a back catalogue costs nothing and never reaches
the archive. The audit that prompted it found 58 of 96 Google News items and
512 of 680 Huntress items published before 2026 — one of them a February 2023
article that force-surfaced at the top of the candidate queue.

Two deliberate exceptions. An entry whose publication date cannot be parsed is
**kept**, because dropping on a date we failed to read would silently delete a
whole feed the first time a publisher changed its format. And rejected items
are **not** written to `seen.txt`: re-testing a date each run costs no requests,
whereas marking them seen would make this policy irreversible.

**`fetch` — how a body is retrieved, and how failure is recognised.** The
collector previously stored whatever came back, which was frequently not an
article: a Cloudflare interlude, a JavaScript shell, or a raw `<a href=...>`
tag from a feed summary. Those are now detected and discarded, and each item
records *why* its body is missing. See `core/fetch.py` for the strategy order.
`impersonate` and `decode_google_news` need optional packages from
`requirements.txt`; without them those strategies are skipped and collection
still runs.

**`user_agent` is empty on purpose, and that is a measured result rather than
an oversight.** Benchmarked against all 56 sensors on 2026-08-25, sending a
browser string was a net loss: `news.sophos.com` went from 2902 words to
blocked — and tarpitted, 120 seconds per attempt instead of 0.4 — and
`cybersecuritynews.com` from 777 words to an instant refusal. Every sensor the
string helped was recovered anyway by the TLS-impersonation retry, which is a
browser at the handshake as well as in the header.

---

## Sensors — Collection feed list

The feeds the collector reads. One URL per line inside the fenced `sensors` block;
blank lines and `#` comments are ignored. **This block is the single source of the
feed list** — edit feeds here. Add a feed only if it is reliable AND additive; verify
it against the host's egress first; drop noisy sources. Do not reintroduce the dropped
34 county Google-News keyword feeds.

Dropped 2026-08-25 — `api.msrc.microsoft.com/update-guide/rss`. **Do not reintroduce
without new evidence.** Two reasons, both measured over 21 cycles.

**First, read this correction, because the obvious argument for dropping it is wrong.**
The often-quoted figure — MSRC is roughly half the corpus — is a **backfill artifact and
was already investigated and dismissed on 2026-08-17.** 3,482 articles arrived on
2026-08-05 from the sensor's first poll and 744 on 2026-08-12, the day after Patch
Tuesday; every other day is 0–36. Ongoing volume is about six items a day. **Volume is
not why this feed was dropped**, and the lifetime totals in `tools/sensor_health.py`
still carry those two bursts. Anyone re-examining this should start here rather than
rediscover the contradiction and reopen a settled decision.

The two reasons that hold:
- **Nothing usable comes out.** Every item links to
  `msrc.microsoft.com/update-guide/vulnerability/CVE-…`, a JavaScript single-page
  application with no server-rendered text. The collector was storing the string
  *"You need to enable JavaScript to run this app"* as the article body. Benchmarked
  2026-08-25 across every fetch strategy — plain, browser user agent, TLS impersonation
  — and **none recovers it**; short of running a headless browser there is nothing there.
- **Zero unique contribution.** Sole source of **no** distinct surfaced event across 21
  runs, and a contributor to three. Measured by `tools/sensor_health.py`, which did not
  exist when this decision was first raised — **this is the evidence that settled it**,
  and the shape of the feed is why: one item per CVE, carrying no severity, no
  exploitation status and no judgement about which of a hundred-plus Patch Tuesday
  entries matter. When a Microsoft flaw genuinely matters,
  BleepingComputer, The Hacker News, Talos and Rapid7 all cover it with context and all
  four are already carried here.

The reasons this feed *sounds* essential — Microsoft patches, SLTT estates run Windows —
are exactly why it needs a written record. **Coverage of Microsoft is not lost.**
`microsoft.com/en-us/security/blog/feed/` (Microsoft Threat Intelligence) is a separate
sensor and stays; `lowmat_tech` already carries `sharepoint` and `exchange server`, so a
Microsoft flaw the news covers still elevates. The residual gap — a critical Microsoft
vulnerability nobody writes up and that KEV has not yet listed — occurred **zero times in
21 runs**. If that gap ever needs closing, the answer is Microsoft's CVRF API
(`api.msrc.microsoft.com/cvrf/v3.0/`, verified reachable 2026-08-25) used as a **lookup**,
one document per month — not a feed that emits the flood more cleanly.

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

Considered and declined 2026-08-26 — `malwarebytes.com/blog/feed/index.xml`. **Measured
before adding rather than after.** Write this one down carefully, because the feed is sound:
it passes every mechanical test and fails the only test that matters.

- **Mechanically it is one of the better feeds available.** HTTP 200 from the collector host,
  20 parseable entries, newest 0.1 days old, bodies extracting at 445 to 2,560 words on plain
  trafilatura — no browser user agent, no TLS impersonation, no strategy required. Single-topic
  posts with dated, citable per-story URLs, so it passes the shape test that refused CyberWire.
  Roughly six items a day and no back-catalogue burst beyond the first poll. One item in twenty
  is a weekly roundup carrying 45 words, which is the CyberWire objection in miniature.
- **Every one of its 20 items scored between 1.00 and 1.50 against a 2.00 threshold. Zero would
  surface.** All twenty landed in tier 4, *broad/national with SLTT relevance* — the floor. Only
  two multipliers fired across the entire feed: one low-maturity SLTT technology and one
  supply-chain. Measured by loading the live CTI scoring model and scoring the real feed
  contents, before the sensor was added to anything.
- **The reason is audience, not quality.** Malwarebytes Labs writes for individuals — phishing
  lures, consumer scams, mobile banking trojans, personal privacy. The model floors anything
  with no AOR hook, correctly, because this is a California SLTT brief. Items that look in scope
  by their titles do not survive it: a healthcare breach exposing medical records and Social
  Security numbers scored 1.00 because it is national with no California link, and 2,560 words
  of loader threat research scored the same.
- **The one thing that would change this answer** is the open Planning & Direction question on
  whether AI-assistant security is in scope. Three of the twenty items are in that class. If
  that decision comes back yes, this feed is worth **re-measuring — not re-arguing.** Do not
  reintroduce on the grounds that the feed is good. It is good. Against this mandate it is
  also empty.

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
# MSRC update-guide RSS was dropped 2026-08-25. See the drop list above.
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
https://news.google.com/rss/search?q=%22California%22%20(ransomware%20OR%20%22data%20breach%22%20OR%20cyberattack)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(%22community%20college%22%20OR%20university%20OR%20CSU%20OR%20UC)%20(ransomware%20OR%20%22data%20breach%22)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20%22school%20district%22%20(ransomware%20OR%20cyberattack%20OR%20%22data%20breach%22)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(%22special%20district%22%20OR%20%22transit%20agency%22%20OR%20%22public%20works%22)%20(cyberattack%20OR%20ransomware%20OR%20breach)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(city%20OR%20county)%20(ransomware%20OR%20cyberattack%20OR%20%22data%20breach%22)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(court%20OR%20%22superior%20court%22%20OR%20sheriff%20OR%20%22police%20department%22)%20(ransomware%20OR%20cyberattack%20OR%20breach)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(election%20OR%20%22registrar%20of%20voters%22)%20(cyberattack%20OR%20breach%20OR%20hack)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20government%20(ransomware%20OR%20cyberattack)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(hospital%20OR%20health%20OR%20clinic)%20(ransomware%20OR%20%22data%20breach%22)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20tribal%20(casino%20OR%20nation%20OR%20government)%20(ransomware%20OR%20cyberattack%20OR%20breach)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
https://news.google.com/rss/search?q=California%20(water%20OR%20wastewater%20OR%20utility)%20(cyberattack%20OR%20hack%20OR%20breach)%20when%3A7d&hl=en-US&gl=US&ceid=US:en
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

**`serves_eei` declares only what a SCORING RULE can honestly attest.** An
essential element whose evidence comes from a named external sensor — a breach
registry, a leak-site aggregator, a vendor advisory feed — is **sensor-bound**,
and no scoring rule may claim it. Measured 2026-08-31 against the 19 elements in
`requirements.md`: **3 are scoring-derived and claimable, 9 are sensor-bound
(three of those sensors PENDING and one ABSENT), 6 are analyst standards** the
engine cannot attest at all. That distribution IS the coverage gap Byproduct 2
of `requirements.md` describes in prose — the pipeline answers PIR-1 largely by
luck — now countable instead of asserted.

**A sensor cannot yet declare the elements it serves**, because the sensor block
is a flat list of URLs with no place to hang metadata. Until it can, the
sensor-bound elements stay unclaimed rather than falsely claimed.

**The SIR and the PIR are never declared.** `EEI-1.2.a` sits under `SIR-1.2`
under `PIR-1` by its own numbering. Deriving them costs nothing; storing them
would put one fact in two files.

**Each tier declares the intelligence requirement it answers.** The four tiers
and the four priority requirements in `requirements.md` are the same four things
and always were — the tier `name` paraphrased the requirement instead of naming
it, so an item's requirement was computed at every scoring pass and never
written down anywhere a reader could see. `serves:` is that name. It changes no
score; it is read only when the staging document says which requirement a
candidate answered.

**`serves:` carries the identifier only, never the requirement's statement.**
`requirements.md` is the single source of truth for what PIR-1 *says*. Copying
the sentence here would put the same fact in two files, which is the drift the
two-file split exists to prevent.

**PIR-4 is the floor, not a subject.** Tier 4 is `require: always` — everything
that qualified for nothing else. It has no vocabulary of its own and should not
be given any.

```yaml
scoring:
  tiers:
    - id: 1
      name: "Direct impact to California organizations"
      serves: PIR-1
      serves_eei: ["EEI-1.2.a"]     # the 34-county match; 1.1.a-d are SENSOR-bound                 # requirements.md — Direct impact to CA organizations
      weight: 8.0
      require:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: cyber_context, scope: blob}   # cyber-domain floor, see prose above
          - any:
              - all:
                  - {group: geo, scope: title}
                  - {group: incident, scope: blob}
              - all:
                  - {group: geo, scope: blob}
                  - {group: incident, scope: blob}
                  - {proximity: {a: geo, b: incident, window: 120}}
    - id: 2
      name: "SLTT sector targeting anywhere (leading indicator)"
      serves: PIR-2
      serves_eei: []                # 2.1.a/b are SENSOR-bound, not scoring-derived                 # requirements.md — SLTT sector targeting anywhere
      weight: 4.0
      require:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: cyber_context, scope: blob}   # cyber-domain floor, see prose above
          - any:
              - all:
                  - {group: sector, scope: title}
                  - {group: incident_broad, scope: blob}
              - {proximity: {a: sector, b: incident_broad, window: 80,
                             scope: blob, all_occurrences: true}}
    - id: 3
      name: "Actively-exploited vulnerabilities in SLTT-common technology"
      serves: PIR-3
      serves_eei: []                # 3.1.a/b are SENSOR-bound (3.1.a has NO sensor)                 # requirements.md — Actively-exploited vulns in SLTT-common tech
      weight: 2.0
      require:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: cyber_context, scope: blob}   # cyber-domain floor, see prose above
          - {group: exploit_strong, scope: blob}
          - {group: lowmat_tech, scope: blob}
          - {proximity: {a: lowmat_tech, b: exploit_strong, window: 200,
                         scope: blob, all_occurrences: true}}
    - id: 4
      name: "Broad/national threats with SLTT relevance"
      serves: PIR-4
      serves_eei: []                # 4.1.a is SENSOR-bound                 # requirements.md — Broad/national threats with SLTT relevance
      weight: 1.0
      require: always

  multipliers:
    - name: "KEV / actively exploited"
      serves_eei: []                # both SENSOR-bound; 3.1.a has no sensor at all
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
      serves_eei: ["EEI-2.2.a", "EEI-3.2.a"]   # both scoring-derived
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
      serves_eei: []                # no element declares this multiplier
      factor: 1.3
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - any:
              - {group: supplychain, scope: title}
              - {proximity: {a: supplychain, b: incident_broad, window: 120,
                             scope: blob, all_occurrences: true}}
    - name: "ransomware vs public-sector/CI"
      serves_eei: []                # 1.1.b is SENSOR-bound (leak-site aggregator, PENDING)
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
      serves_eei: ["EEI-1.2.a"]
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: cyber_context, scope: blob}   # cyber-domain floor
          - any:
              - all:
                  - {group: geo, scope: title}
                  - {group: incident, scope: blob}
              - {proximity: {a: geo, b: incident, window: 120,
                             scope: blob, all_occurrences: true}}
    - name: "M2 exploited flaw affecting SLTT-relevant technology"
      serves_eei: ["EEI-3.2.a"]
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: cyber_context, scope: blob}   # cyber-domain floor
          - {group: exploit_strong, scope: blob}
          - {group: lowmat_tech, scope: blob}
          - {proximity: {a: lowmat_tech, b: exploit_strong, window: 200,
                         scope: blob, all_occurrences: true}}
    - name: "M3 SLTT sector in an incident"
      serves_eei: []                # 2.1.a is SENSOR-bound
      when:
        all:
          - {not: {group: listicle, scope: title}}
          - {group: cyber_context, scope: blob}   # cyber-domain floor
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
    # Tradecraft language - how an adversary operates, as distinct from what
    # happened to a victim (`incident`) or what is being exploited
    # (`exploit_strong`). Used only to suggest the CTA TTPs section; it feeds
    # no tier, no multiplier and no force-surface rule, so a false match costs
    # a section suggestion the analyst overrides, nothing more.
    ttp: ["lateral movement", "living off the land", "lolbin", "initial access",
          "privilege escalation", "persistence mechanism", "command and control",
          "credential harvesting", "credential theft", "web shell", "webshell",
          "infostealer", "info-stealer", "loader", "dropper", "beacon",
          "att&ck", "mitre att", "tradecraft", "tactics, techniques",
          "spearphishing", "spear-phishing", "social engineering",
          "defense evasion", "obfuscation", "dll sideloading", "dll side-loading",
          "process injection", "living-off-the-land"]
    # Matched against the `source` scope, never the article text.
    cisa_source: ["cisa.gov"]
    # CYBER-DOMAIN FLOOR. Added 2026-08-31. An item cannot reach tier 1, 2 or 3,
    # and cannot force-surface, unless it contains at least one of these. It is a
    # FLOOR, not a scorer - nothing here adds weight, and a generous list is the
    # safe direction because a miss here silently deletes a requirement while a
    # false positive merely leaves an item eligible to be scored on its merits.
    #
    # WHY. On 2026-08-31 "A Baby Great White Leapt from the Ocean Near a Boogie
    # Boarder" scored 8.0, tier 1, force-surfaced on M1: `geo:'california'` and
    # `incident:'breach'` - a shark BREACHING the ocean near a California beach.
    # "breach" is also a levee, a contract, a courtroom verdict and a code of
    # conduct. Measured against 776 items: this floor removes 16 of 137 surfaced
    # items and every one of the 16 is non-cyber - sharks, whale watching, two
    # lottery suits, Oakley v Nike, a reinsurance dispute, Justice Thomas.
    #
    # NOT the word "cyber" alone. That was tried first and measured: it would have
    # deleted the California DMV data breach, the LA Superior Court ransomware
    # shutdown, the Northern Inyo Hospital breach and all three tier-3 vulnerability
    # advisories - 44 items, roughly half of them the most in-scope in the set.
    # Incident reporting does not say "cyber"; journalists and policy writers do.
    #
    # EVERY FORM OF "hack" IS SPELLED OUT, and that is not tidiness. The matcher
    # gives any term of 4 characters or fewer automatic WORD-BOUNDARY matching, so
    # a bare "hack" does not match "hacks", "hacked" or "hacking" - it matches only
    # the standalone noun. Measured: with "hack" alone, "Attackers Targeted Over 100
    # US Water Systems in July Hacks" was deleted, a tier-2 water-sector item lost to
    # one plural noun. This is the same 4-character boundary rule behind Open finding
    # 2 in vocab.md. A stem is not a stem in this engine unless it is 5+ characters.
    cyber_context: ["cyber", "hacks", "hacked", "hacker", "hacking", "hack",
          "ransomware", "malware", "phish",
          "data breach", "security breach", "breach notification",
          "personal information", "social security", "patient record",
          "customer record", "credit card", "credential", "password",
          "database", "unauthorized access", "exfiltrat", "encrypted the",
          "threat actor", "security incident", "vulnerabilit", "exploit",
          "cve-", "patch", "denial of service", "ddos", "it systems",
          "computer system", "network", "server", "stolen data", "data theft",
          "identity theft", "information technology"]

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

  # ---- Staging annotations (Vox Policy §5 and §6.2) ----
  # Advisory only. Nothing here touches the score, the tier, the ordering or
  # the surface-vs-drop decision. These exist so two standards the analyst was
  # expected to remember become visible in the document instead.
  staging_annotations:
    # §6.2 "body, not headline". Below this many words of extracted text there
    # is nothing to write an entry FROM, and the item is marked [NO BODY].
    # 40 words is about two sentences - enough to tell a real article from a
    # feed stub or a failed extraction, low enough not to flag terse advisories.
    min_body_words: 40

    # §5 section suggestion. ORDERED - first match wins, and the last entry is
    # the catch-all. Rules use the same grammar as the scoring above, so a
    # section can be retuned exactly like a tier and the engine stays ignorant
    # of what CTI's sections are. S2 defines its own list in its own pnd.md.
    #
    # KEYWORDS is deliberately NOT here. Policy §5 describes it as wave-top
    # only - vendor and sector names, not items - so it is a summary block the
    # analyst writes, not a destination candidates get assigned to. The
    # compliance report still checks it appears in the edition.
    sections:
      - name: "LATEST ATTACKS OR RISKS"
        when:
          any:
            - {group: exploit_strong, scope: blob}
            - {group: cve, scope: blob}
      - name: "CTA TTPs"
        when: {group: ttp, scope: blob}
      # NEWS twice, deliberately. The first is a POSITIVE match - something
      # happened to somebody - and gets a clean tag. The second is the
      # catch-all and gets the "?" marker, so an item that merely failed to
      # match anything is visibly different from an item that is genuinely a
      # news event. Without the split every NEWS item would carry a "?" and
      # the marker would stop meaning anything.
      - name: "NEWS"
        when: {group: incident_broad, scope: blob}
      - name: "NEWS"
        when: always

    # §8 production gate. The pipeline fills the countable fields of the
    # compliance report; these are the judgments only a person can sign off.
    # Each is a locked standard from the Vox Policy, restated here as a check
    # rather than left for the analyst to recall.
    compliance_checklist:
      - "Every entry written from the article BODY, never the headline (§6.2)."
      - "One event, one entry - same-event reports folded, each event placed once (§7)."
      - "Every entry carries a 'why an SLTT organization should care' clause, framed as vendor accountability, procurement or IG1 controls (§6.3)."
      - "Citations nested per entry, as live links the reader can actually open (§6.5)."
      - "Serious-impact claims verified against a primary or authoritative source; wording does not inflate the source (§7)."
      - "Attribution discipline: suspected is not confirmed; the state of evidence is represented as it stands (§7)."
      - "Out-of-window items either carry a fresh this-week hook or are cut - not silently kept (§7)."
      - "Audience-portfolio filter applied: developer-only and defence-industrial-only items excluded unless they reach SLTT through a vendor (§7)."
      - "Product-specific items are relevant only if this audience uses the product (§7)."
      - "Acronyms spelled out on first use; mechanisms named but translated (§7)."
      - "All four sections present; an empty one says 'none this cycle' rather than being omitted (§5)."
      - "Three dates correct: title = distribution Thursday, ICOD in the header, LTIOV absent (§2)."
      - "Staging draft carries no handling markings (§1)."
      - "Reader-facing heading is 'WCTI - Weekly Cyber Threat Intelligence'; the word 'vox' appears nowhere (§3)."
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
