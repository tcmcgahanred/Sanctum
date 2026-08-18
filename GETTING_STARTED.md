# Getting Started — Standing Up Sanctum for Your Own Domain

**BLUF:** Sanctum collects open sources on a schedule, scores every item against requirements *you* define, and hands you a ranked candidate queue to review. It does not write your product. This guide takes you from a clone to a working domain in about an hour, most of which is spent thinking about your requirements rather than typing.

**Who this is for:** anyone comfortable in a terminal who can edit a YAML block. You do not need to read or write Python. You will never edit a file under `core/`.

---

## What you are actually building

Sanctum has exactly two moving parts:

- **`core/`** — the engine. Domain-agnostic, holds no knowledge of any subject. You do not touch it.
- **`<yourdomain>/pnd.md`** — your Planning & Direction file. One markdown document holding everything the engine needs: where things live, which sources to read, how to score what comes back, and what the output should look like.

Standing up a domain means writing one `pnd.md`. That is the whole job.

**What Sanctum will not do.** It stops at a *staging document* — a ranked, reasoned candidate queue. It does not write your finished report, and that is deliberate: the last mile diverges too much between domains to automate well, and it is the part where human judgment earns its keep. Synthesis stays manual. There is no LLM call anywhere in the pipeline.

---

## 1. Prerequisites

- Linux host (or WSL) with Python 3.9+
- ~1 GB disk for a rolling corpus
- Outbound HTTPS to your sources
- Optional: [`rclone`](https://rclone.org/) if you want the corpus archived off-box

---

## 2. Install

```bash
git clone https://github.com/tcmcgahanred/Sanctum.git
cd Sanctum
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Three dependencies: `feedparser`, `trafilatura`, `pyyaml`.

> **Note:** `run.sh` ships without its executable bit. Invoke it as `bash run.sh <domain>`, or run `chmod +x run.sh` once.

---

## 3. Pick where runtime data lives

Sanctum keeps its corpus, dedupe state, and logs **outside** the repo, in a directory called `base_dir`. Nothing there is version-controlled, so you can wipe or move the repo without losing data.

```bash
mkdir -p /opt/sanctum        # or ~/sanctum-data, or anywhere writable
```

You will point at this in the manifest. You can also override it per host without touching config:

```bash
export SANCTUM_BASE=/opt/sanctum
```

The env var wins over the manifest — that is how the same repo runs on a laptop and a server.

---

## 4. Create your domain

```bash
mkdir mydomain
cp s2/pnd.md mydomain/pnd.md
```

`s2/pnd.md` is a deliberately empty template. Now work through its four blocks in order.

### 4a. Manifest — where things live

```yaml
manifest:
  domain: mydomain                  # must match the folder name
  base_dir: /opt/sanctum            # from step 3
  corpus:
    backend: rclone                 # or: local
    rclone_remote: myremote:mydomain-corpus
  collection:
    window_days: 7                  # rolling corpus retention
    min_title_len: 15               # below this, skip title-dedup
    suffix_separators: [" - ", " | ", " — "]
```

Set `backend: local` if you do not want off-box archiving — the corpus then just stays in `base_dir` and nothing is pushed.

`suffix_separators` matter more than they look. Many sources append `" - Publisher"` to headlines; stripping that is what lets Sanctum recognise the same story arriving from three feeds.

### 4b. Sensors — what to read

One URL per line inside the fenced `sensors` block. Blank lines and `#` comments are ignored.

````markdown
```sensors
# --- Official / authoritative ---
https://example.gov/advisories/feed
https://example.org/alerts.xml

# --- Trade press ---
https://example.com/feed/
```
````

**RSS and Atom are the happy path.** A plain web page also works — if a URL yields no feed entries, Sanctum falls back to extracting the page's readable text as a single item. (Caveat: a page source is currently collected only once and not revisited. See Known Limits.)

**Verify every URL against the machine that will run collection, not your laptop.** Plenty of sources serve a browser fine and return 403 to a datacenter IP.

```bash
.venv/bin/python3 -c "
import feedparser
for u in ['https://example.gov/advisories/feed']:
    d = feedparser.parse(u)
    print(len(d.entries), 'entries  HTTP', getattr(d,'status','---'), u)"
```

Anything returning zero entries is not a feed. Fix it or drop it before loading.

**Be strict here.** A source earns its place only if it is reliable *and* additive — offering a vantage the others do not. Twenty well-chosen sources beat two hundred. Coverage comes from good sensors well-operated, not from volume; the scoring model cannot rescue a corpus full of noise.

### 4c. Scoring — the part that takes real thought

This is where your domain knowledge goes. Budget most of your time here.

**The model is multiplicative:** an item takes the weight of the *highest tier it qualifies for*, then that weight is multiplied by every elevation signal that fires.

```
score = tier_weight × multiplier₁ × multiplier₂ × …
```

**Groups** are named term lists. Everything else refers to them:

```yaml
groups:
  aoi:            ["greenfield county", "port of example", "riverside plant"]
  pir_activity:   ["outage", "intrusion", "disruption", "closure"]
  time_sensitive: ["ongoing", "active", "emergency", "declared"]
```

**Tiers** are relevance bands. Lower `id` = higher priority. One tier must be a catch-all with `require: always`.

```yaml
tiers:
  - id: 1
    name: "Directly in my area of interest"
    weight: 8.0
    require:
      any:
        - {group: aoi, scope: blob}
  - id: 2
    name: "Answers a priority requirement"
    weight: 4.0
    require:
      any:
        - {group: pir_activity, scope: blob}
  - id: 4
    name: "Broad / background"
    weight: 1.0
    require: always
```

**Multipliers** are urgency signals layered on top. An absent signal is neutral (×1.0) and never suppresses an item.

```yaml
multipliers:
  - name: "time-sensitive"
    factor: 1.5
    when: {group: time_sensitive, scope: blob}
```

**Why multiplicative?** Because convergence should win. A tier-2 item carrying three urgency signals (4.0 × 1.5 × 1.5 × 1.3 = 11.7) outranks a bare tier-1 item (8.0). An item satisfying several requirements at once is usually more important than one scoring on geography alone. If that is wrong for your domain, widen the tier spacing.

**`scope: blob`** matches against title and body together. Use `scope: title` when a term only counts as a headline subject.

**`word_boundary_terms`** exists because substring matching bites. Without it, `cisco` matches inside `Francisco`. Put every short or ambiguous term in that list:

```yaml
word_boundary_terms: ["ics", "ot", "ai", "cisco"]
```

**Settings:**

```yaml
settings:
  surface_n: 55                     # how deep the candidate queue goes
  empty_title:
    score: 0.5
    tier: 4
    flag: "FLAG: empty title (verify source)"
  recency:                          # optional — omit to disable the gate
    enabled: true
    window_days: 7
    cutoff_weekday: monday
    cutoff_time: "09:00"
    timezone: "America/Los_Angeles"
```

`surface_n` is the only production-side number the engine actually enforces. Set it well above your target item count — you want more candidates than you will keep.

The **recency gate** checks each item's *publication* date against your cycle window and flags anything outside it as `STALE — confirm current hook`. It never drops. This catches a feed re-serving a months-old advisory that scores high on relevance because relevance carries no time term. **If you omit the `recency` block entirely, the gate is off** and the staging header will say so.

### 4d. Production — what the output should look like

```yaml
production:
  report_title: "MYDOMAIN — Pre-Filtered Candidate Queue"
  staging_item_target: [15, 18]
  staging_per_section: [5, 6]
  distributed_item_target: [5, 8]
  sections: ["SECTION A", "SECTION B", "SECTION C"]
  deliverable_name: "MYDOMAIN_v[YYYYMMDD]_STAGING"
```

**Change `report_title`** — the template ships with the stub's title and it is easy to miss.

These values are **advisory**. No engine reads them; they document the target for whoever does synthesis. Keep two distinct numbers: a generous *staging* target (a review surface, so you have material to cut from) and a restrained *distributed* target (the actual product). The count should narrow as the week progresses.

---

## 5. Validate before running

```bash
.venv/bin/python3 -m core.pnd --domain mydomain --get manifest.domain
.venv/bin/python3 -m core.pnd --domain mydomain --get production
```

This parses every YAML block and checks that each group referenced by a rule actually exists. A typo'd group name fails loudly here rather than silently scoring nothing.

**It does not check that your groups have terms in them.** A domain with empty groups loads fine, runs fine, and scores every item at tier 4 — a flat, useless queue. Confirm your term lists are populated:

```bash
.venv/bin/python3 -c "
import sys; sys.path.insert(0,'.')
from core.pnd import load_domain
d = load_domain(domain='mydomain')
print('sensors:', len(d['sensors']))
print('groups: ', {k: len(v) for k, v in d['scoring']['groups'].items()})
print('sections:', d['production']['sections'])"
```

Any group at `0` is a group you forgot.

---

## 6. First run

```bash
bash run.sh mydomain
```

Two stages: collect, then score.

```
[mydomain] 214 new articles -> /opt/sanctum/corpus/2026-08-11
[mydomain] corpus pushed -> myremote:mydomain-corpus
[mydomain] 214 scored -> 55 candidates, 159 dropped -> /opt/sanctum/staging_candidates.md
```

The first run backfills whatever each source currently offers, so it will be your largest. Expect it to take **15–30 minutes** — every article is fetched individually for full-text extraction. That is normal, not a hang. Watch progress from another terminal:

```bash
tail -f /opt/sanctum/logs/collector.log
```

Ctrl-C is safe. Dedupe state is written per article, so a partial run resumes cleanly.

To re-score without re-collecting — which is what you want while tuning:

```bash
.venv/bin/python3 -m core.arbites --domain mydomain
```

No network, instant, run it as often as you like.

---

## 7. Read the output

`staging_candidates.md` has two parts, and both matter.

**CANDIDATES** — everything above the cut, ranked, each showing its reasoning:

```
### [23.4] Riverside plant outage after intrusion
- **Source:** example.com · 2026-08-10
- **URL:** https://example.com/story
- **Score reasoning:** T1 aoi (blob) × time-sensitive 1.5 × ongoing 1.3
```

That reasoning line is the point. It tells you *why* something ranked, so you can tell a real hit from a keyword accident.

**DROP LIST** — everything below the cut, still visible. Sanctum flags rather than hides; nothing is silently discarded. Scan it. A good item appearing there means your scoring needs work, and that is the most valuable feedback you get.

**The score orders the queue. You decide.** Promote, kill, and reorder freely. A low-scoring item with obvious significance still makes your product.

---

## 8. Tune over the first few cycles

Expect the first two or three editions to be mediocre. Tuning is the work.

- **Real items landing in the drop list** → your tiers are too narrow, or a term is missing from a group.
- **Junk at the top** → usually substring collision. Add the offending term to `word_boundary_terms`.
- **Everything scoring the same** → your groups are too thin, or everything is falling through to the catch-all tier.
- **A source contributing nothing** → check its lifetime yield and drop it. The log has been recording this all along:

```bash
awk '/ -> [0-9]+ new$/ {n=$(NF-1); u=$(NF-3); tot[u]+=n; runs[u]++}
     END {for (x in tot) printf "%6d new  %3d runs  %s\n", tot[x], runs[x], x}' \
  /opt/sanctum/logs/collector.log | sort -n
```

Zero across many runs means dead or wrong. One source producing half your corpus means it is drowning the others — that is a volume problem, not a coverage win.

- **Failures** are logged explicitly:

```bash
grep "source failed" /opt/sanctum/logs/collector.log
grep "no text"       /opt/sanctum/logs/collector.log
```

**Write down why you dropped something.** Put it in the prose above your `sensors` block. Otherwise you will re-add it in six months and rediscover the same problem.

---

## 9. Automate it

Once the output is worth reading, put it on a timer.

`/etc/systemd/system/sanctum.service`:

```ini
[Unit]
Description=Sanctum collection cycle
After=network-online.target

[Service]
Type=oneshot
User=sanctum
WorkingDirectory=/home/sanctum/Sanctum
ExecStart=/usr/bin/bash /home/sanctum/Sanctum/run.sh mydomain
```

`/etc/systemd/system/sanctum.timer`:

```ini
[Unit]
Description=Run Sanctum nightly

[Timer]
OnCalendar=*-*-* 00:02:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now sanctum.timer
systemctl list-timers sanctum.timer
```

Note `ExecStart` invokes `bash` explicitly, so the missing executable bit does not matter here.

**Never run the cycle as root.** It writes into `base_dir` as whatever user invoked it; a root run leaves root-owned files that break the next timer run.

---

## 10. Adding a second domain

Repeat section 4. Nothing else changes — same engine, same commands, separate `base_dir` and corpus store. That is the entire point of the design.

---

## Known limits

Worth knowing before you hit them:

| Limit | Impact |
|---|---|
| **Page sources are collected once.** Non-feed URLs are deduped on the URL itself, so a page that updates is never re-read. | Do not use a regularly-updating index page as a sensor yet. |
| **No collection timeout.** A stalled source can block the sequential run. | If a cycle runs far past 30 minutes, check the log's last line for the URL it is stuck on. |
| **`run.sh` is not executable** as cloned. | Use `bash run.sh`, or `chmod +x` once. |
| **Empty groups fail silently.** Config validation checks that referenced groups *exist*, not that they contain terms. | Run the check in section 5. |
| **No LLM anywhere.** Scoring is keyword and rule based. | It orders a queue; it does not understand your domain. That is what you are for. |

---

## Where to go next

- **`README.md`** — architecture and the eleven tenets the design follows
- **`cti/pnd.md`** — a fully worked, operational domain. The best reference for what a real scoring model looks like
- **`cti/requirements.md`** — how one domain's requirements were structured (KIQ → PIR → SIR → EEI)
- **`cti/mandate.md`** — how standing decisions and lessons get recorded across cycles
- **`ROADMAP.md`** — where this is going, and the "keeper test" for whether it earns further investment
