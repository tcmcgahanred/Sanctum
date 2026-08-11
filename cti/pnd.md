# CTI — Planning & Direction (P&D)

*Sanctum · CTI domain config. This file is BOTH the human-readable P&D and the
machine config the engines consume. Prose is for you; the engines read only the
fenced `yaml` blocks below. The prose doctrine lives in `codex.md` / `mandate.md`;
this file is where Planning & Direction is turned into the parameters that drive
Collection, Processing & Exploitation, and Analysis & Production.*

**BLUF:** Everything domain-specific about the CTI effort lives here. The `core/`
engines are generic — swap this file (and `sensors.txt`) for another domain's and
the same code runs S2 or anything else.

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
word boundaries. Full rationale is in `codex.md` (Layers 3–4).

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

  settings:
    surface_n: 55
    empty_title: {score: 0.5, tier: 4, flag: "FLAG: empty title (feed artifact — verify source)"}
    recency:                       # Codex Layer 4 — flag stale-by-publish-date, never drop
      enabled: true
      window_days: 7               # cycle window length (ends at the cutoff below)
      cutoff_weekday: monday       # ICOD day
      cutoff_time: "09:00"         # ICOD time
      timezone: America/Los_Angeles

  word_boundary_terms: ["hack", "ics", "scada", "grid", "leak", "ransom", "court", "uc", "csu", "cisco", "war"]

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

**Two different targets — do not conflate them.** The staging doc is a *review
surface*; the distributed report is the *product*. The count narrows through the
week, and that funnel is the intent:

| Artifact | When | Target |
|---|---|---|
| **Staging doc** (Vox draft) | Monday | **~5–6 per content section, ~15–18 total** — generous, so the analyst and the cyber team have material to review, cut, and use to tune P&D |
| **Distributed report** | Thursday | **5–8 items total** — "restraint is the product" applies here |

Per-section targets cover the three content sections (NEWS, CTA TTPs, LATEST
ATTACKS OR RISKS). KEYWORDS is wave-tops, not items, and carries no target.

The extra staging entries are the **next-lower-ranked items from the same sorted
queue** — lower tier and/or fewer elevation signals. This extends the cut line
down an already-ranked list; it does not lower the standard. Every entry still
shows its scoring reasoning (tier + which multipliers fired) so the analyst can
audit where the cut falls.

*Both targets are advisory — no engine reads them (verified 2026-08-11: `arbites.py`
reads only `report_title` from this block). The only code-enforced production knob is
`scoring.settings.surface_n`, which sets candidate-queue depth. At 55 it already
supplies roughly 3× the new staging target, so no scoring change is required.*

```yaml
production:
  report_title: "WCTI — Pre-Filtered Candidate Queue"
  staging_item_target: [15, 18]        # Monday review surface — total across content sections
  staging_per_section: [5, 6]          # NEWS / CTA TTPs / LATEST ATTACKS OR RISKS
  distributed_item_target: [5, 8]      # Thursday finished report — "restraint is the product"
  sections: ["NEWS", "CTA TTPs", "LATEST ATTACKS OR RISKS", "KEYWORDS"]
  deliverable_name: "WCTI_v[YYYYMMDD]_STAGING"   # date = distribution (Thu)
  notes: >
    Staging = content only, no handling markings, generous item count (review
    surface). The distributed product narrows to 5-8 and adds handling markings.
    KEYWORDS is wave-tops, not items - no target applies. Three dates on the
    distribution product: title = distribution (Thursday); ICOD line = collection
    cutoff (Monday 0900); LTIOV planning-only, never printed.
```
