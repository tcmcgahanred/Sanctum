# Sanctum — Planning & Direction Survey

**What this is.** A self-contained intake instrument. Work through it and you will have a complete, working `pnd.md` for your own Sanctum domain — the one file the engines read.

**Two ways to use it, both valid:**

- **Fill it in yourself.** Every question states what a good answer looks like and what gets rejected. Answer them in order; assemble the output using the contract at the end.
- **Hand it to an LLM.** Paste this whole document into any capable model and say *"run this survey with me."* Section 0 tells the model how to conduct it. You do not need Sanctum, this repo, or any particular vendor for that step — the output is plain markdown you bring back here.

**Time:** 45–90 minutes. Most of it is Part 2. That is the work, not overhead.

**What you need before starting:** nothing installed. Just the ability to answer honestly about who your product is for.

---

## 0. Instructions for the LLM conducting this survey

*(Skip this section if you are filling the survey in yourself.)*

You are conducting a structured intelligence-requirements interview. Your output is a `pnd.md` configuration file for an OSINT collection-and-triage system called Sanctum.

**How Sanctum works, so you can reason about the answers.** It collects from a fixed list of sources on a schedule, stores everything, then scores every item against the user's requirements and produces a ranked candidate queue for a human analyst. It filters nothing at collection. It never decides — it orders. Scoring is: an item takes the weight of the *highest relevance tier it qualifies for*, and that weight is then multiplied by every *urgency signal* that fires. Convergence therefore beats bare relevance: an item satisfying several requirements at once can outrank one that is merely on-topic.

**Conduct the interview like this:**

- **One question at a time.** Do not dump the whole survey at them.
- **Push back on vague answers.** This is the single most important thing you do. A survey that accepts the first answer produces a useless configuration. Each question below has explicit rejection criteria — apply them. If an answer fails, say why and ask again.
- **Do not invent domain content.** You do not know their area of operations, their sources, or their vocabulary. Ask. Where they are stuck, offer *examples of the shape* of an answer, never a made-up specific.
- **Stop at Part 0 if it fails.** If they cannot name a consumer and a decision, tell them plainly that the requirements cannot be written yet and that this is a reason to pause, not to push through. Do not soften this.
- **At the end**, emit the complete `pnd.md` per the Output Contract, then list what they still need to verify themselves.

**A worked example runs through this document** — a cyber-threat-intelligence domain serving local-government partners across a defined region. Use it to show shape. Do not let it colour their content.

---

## Part 0 — The gate

**Everything downstream derives from these three answers. If they are weak, stop here.**

### 0.1 Who reads the product?

Name a person, role, or team. Not "leadership." Not "anyone interested."

> *Worked example: the cyber team supporting local-government and critical-infrastructure partners across a defined multi-county region.*

**Rejected if:** the answer is a category rather than a set of actual people who will actually read it.

### 0.2 What decision does it inform, or what behaviour does it change?

If nothing changes as a result of someone reading this, you are building a newsletter, which is fine — but say so, because it changes what "good" means.

> *Worked example: partners decide what to patch, what to warn staff about, and what to ask their IT vendor this week.*

**Rejected if:** you cannot finish the sentence *"because they read this, they will ______."*

### 0.3 What happens if it is late or missing?

This calibrates how much effort the whole apparatus deserves.

**Rejected if:** the honest answer is "nothing." That is a legitimate finding. It means this should be a low-effort habit, not a built system.

---

## Part 1 — The Key Intelligence Question

### 1.1 State the one enduring question this domain exists to answer.

One. Broad enough to be stable for a year; narrow enough to exclude most of the world.

> *Worked example: "What cyber threats endanger local-government organisations in our region and the critical infrastructure they operate or depend on?"*

**Rejected if:**
- It can be answered yes/no. That is a PIR, not a KIQ.
- You need two. Two KIQs means two domains — build them separately, they will want different sources and different scoring.
- It would still be true and useful for an organisation with a completely different mission. Too broad.

---

## Part 2 — Priority Intelligence Requirements

**This is the long pole. Budget most of your time here.** Everything mechanical downstream is derived from these.

### 2.1 Decompose the KIQ into 3–5 questions.

Each PIR is a narrower question whose answer contributes to the KIQ. Together they should cover it without heavy overlap.

> *Worked example:*
> 1. *What incidents have directly affected organisations in our region?*
> 2. *What threat activity targets our sectors anywhere — as a leading indicator?*
> 3. *What actively-exploited vulnerabilities affect technology our audience actually runs?*
> 4. *What national-scale threats carry material relevance to our audience?*

**Rejected if:**
- Fewer than 3 — the KIQ is not decomposed, it is restated.
- More than 6 — you are listing topics, not prioritising.
- Any PIR cannot be answered from **open sources**. Sanctum reads public feeds and web pages. A requirement needing internal telemetry, classified reporting, or paid intelligence cannot be served here. Cut it or note it as out of scope.
- Two PIRs would be satisfied by the same article every time. Merge them.

### 2.2 For each PIR, what would a *good* answer look like this week?

Write one sentence per PIR describing a specific item that would satisfy it. These become your test cases later.

**Rejected if:** you cannot imagine a realistic item. Either the PIR is unanswerable from open sources, or it is not really a requirement.

### 2.3 Rank the PIRs.

Which one, if you could only answer one, would you keep? This ordering drives tier weights in Part 3.

---

## Part 3 — What earns top billing

Sanctum sorts everything into **relevance tiers**. Highest qualifying tier wins; tiers do not stack.

### 3.1 What makes something maximally relevant — your Tier 1?

Usually the answer is *proximity*: this happened to us, or to something we own, or inside our boundary. But proximity is not always geographic — it can be an organisation, a platform, a named actor, a supply relationship.

> *Worked example: our region is the subject of an incident — not merely mentioned in passing.*

**Rejected if:** more than roughly one in ten items would qualify. Then it is not Tier 1, it is Tier 2. Tier 1 should be rare and should always deserve reading.

**Critical follow-up:** *how would a keyword matcher tell the difference between your Tier 1 and a passing mention?* A national article listing twenty regions including yours must not qualify. This is the single most common way a scoring model fails. Options: require the term in the **title**; or require it within ~120 characters of an event word in the body. Pick one.

### 3.2 Tiers 2 and 3 — relevant but not direct.

> *Worked example: Tier 2 = our sector is targeted anywhere. Tier 3 = a vulnerability is being exploited in technology our audience commonly runs.*

### 3.3 Tier 4 — the catch-all.

One tier must accept everything, so nothing falls through unscored. This is where broad background lands.

### 3.4 Weights.

Default is 8 / 4 / 2 / 1 — each tier twice the one below. Keep it unless you have a reason.

**Understand what the spacing means:** the full stack of urgency multipliers in Part 4 is worth roughly 3.8×, slightly under two tier steps. So a maximally-urgent Tier 4 item lands just below a bare Tier 2 item. Convergence can beat one level of relevance, never two. If you widen the tier gaps, urgency matters less; if you narrow them, it matters more.

---

## Part 4 — Urgency signals

Multipliers applied on top of the tier weight. Absent is neutral — never a penalty.

### 4.1 What makes an item *more* urgent, independent of relevance?

Three to five signals. Each must be detectable from an article's text.

> *Worked example: confirmed active exploitation (×1.5); affects low-maturity technology our audience runs (×1.5); supply-chain or vendor compromise (×1.3); ransomware against public-sector or critical infrastructure (×1.3).*

**Rejected if:**
- More than six. You are re-encoding relevance as urgency.
- A signal fires on most items. Then it carries no information — drop it.
- You cannot state the words that would appear in an article carrying that signal. If you cannot name the words, the matcher cannot find them.

### 4.2 Factors.

1.5 for strong signals, 1.3 for moderate. Avoid anything above 2.0 — a single signal should not outrank a whole tier.

---

## Part 5 — Vocabulary

Every tier and multiplier refers to a named **group** of terms. This is where your requirements become machine-readable.

### 5.1 For each group, list the actual words.

Be generous — 10 to 40 terms is normal. Include misspellings, abbreviations, and both spaced and unspaced forms ("cyber attack" and "cyberattack").

**Two traps, both of which have bitten this system in production:**

**Short terms match inside longer words.** `uc` matches inside "auction"; `ics` inside "physics"; `cisco` inside "Francisco". Any term of four characters or fewer, and any term you can imagine appearing inside a longer word, goes in the `word_boundary_terms` list.

**Names are not unique across regions.** A county, city or organisation name may exist in several places. Check yours. If "Kings County" means Brooklyn to most of the world, a matcher will happily score Brooklyn stories as local.

### 5.2 What must never be treated as relevant?

Things adjacent to your domain but out of portfolio. You will not encode these as rules — Sanctum has no exclusion operator — but write them down as analyst guidance.

> *Worked example: developer-targeted supply-chain items that never reach our audience; defence-contracting compliance news.*

---

## Part 6 — Sources

### 6.1 Where does reporting about your domain actually appear?

List by category: official and authoritative; sector-specific; trade press; general news; primary vendor sources.

**Be strict.** A source earns its place only if it is **reliable AND additive** — offering a vantage the others do not. Twenty good sources beat two hundred. Sanctum stores everything it collects and never deletes it, so a noisy feed costs you permanently.

**Rejected if:** you cannot say what a source gives you that another does not.

### 6.2 Which of these publish a feed?

RSS or Atom is the happy path. A plain web page also works — Sanctum will extract its text — but a page is currently collected only once and not revisited, so an index page that updates is not yet a good sensor.

### 6.3 Verify every URL against the machine that will run collection.

Not your laptop. Many sources serve a browser and return 403 to a datacentre address.

```bash
python3 -c "
import feedparser
for u in ['https://example.org/feed']:
    d = feedparser.parse(u)
    print(len(d.entries), 'entries  HTTP', getattr(d,'status','---'), u)"
```

Zero entries means it is not a feed. Fix it or drop it.

### 6.4 What do you need that no feed provides?

Be honest here — it is usually the most valuable thing. Authoritative registries, portals, and databases often have no feed, and knowing that up front tells you where the real build cost is.

---

## Part 7 — The product

### 7.1 What sections does your brief have?

> *Worked example: NEWS; TACTICS; LATEST ATTACKS OR RISKS; KEYWORDS.*

### 7.2 Two item targets, not one.

Keep these separate — conflating them is a known failure:

- **Staging draft** (the review surface): generous. Enough material to cut down from.
- **Distributed product**: restrained. What actually ships.

> *Worked example: ~5–6 per section at staging (~15–18 total); 5–8 total distributed.*

### 7.3 Cadence.

When is the collection cutoff, when is the draft built, when does review happen, when does it ship? Keep the dates distinct and know which one appears on the product.

---

## Part 8 — Runtime

Mechanical. No judgement required.

- **Domain name** — lowercase, no spaces. Becomes the folder name and must match `manifest.domain`.
- **base_dir** — where corpus, dedupe state and logs live. Outside the repo.
- **Corpus backend** — `rclone` with a remote, or `local`.
- **Collection window** — days of corpus to score. 7 is the default.
- **Recency gate** — flags items *published* outside the window as stale. Set the cutoff day and time, or omit the block to disable.

---

## Output contract

Assemble the answers into a single `pnd.md`. Prose is ignored by the engines; only the fenced blocks are read — so keep the reasoning next to the configuration it explains.

````markdown
# <DOMAIN> — Planning & Direction

<Part 0 answers: consumer, decision, consequence of absence.>
<Part 1: the KIQ.>
<Part 2: the PIRs, ranked, each with its "good answer looks like" sentence.>

```yaml
manifest:
  domain: <name>
  base_dir: /path/to/runtime
  corpus:
    backend: rclone            # or: local
    rclone_remote: remote:bucket
  collection:
    window_days: 7
    min_title_len: 15
    suffix_separators: [" - ", " | ", " — "]
```

## Sensors

```sensors
# --- category ---
https://example.org/feed
```

## Scoring

```yaml
scoring:
  tiers:
    - id: 1
      name: "<what maximal relevance means>"
      weight: 8.0
      require:
        any:
          - all:
              - {group: <proximity>, scope: title}
              - {group: <event>, scope: blob}
          - all:
              - {group: <proximity>, scope: blob}
              - {group: <event>, scope: blob}
              - {proximity: {a: <proximity>, b: <event>, window: 120}}
    - id: 2
      name: "<sector or category relevance>"
      weight: 4.0
      require:
        any:
          - {group: <sector>, scope: blob}
    - id: 4
      name: "broad / background"
      weight: 1.0
      require: always

  multipliers:
    - name: "<urgency signal>"
      factor: 1.5
      when: {group: <signal>, scope: blob}

  settings:
    surface_n: 55
    empty_title: {score: 0.5, tier: 4, flag: "FLAG: empty title (verify source)"}
    recency:
      enabled: true
      window_days: 7
      cutoff_weekday: monday
      cutoff_time: "09:00"
      timezone: <IANA timezone>
    grouping:
      enabled: true
      similarity: 0.15
      min_shared_tokens: 3
      min_evidence: 8.0
      max_group_size: 25
      max_group_display: 12

  word_boundary_terms: ["<short or ambiguous terms>"]

  groups:
    <proximity>: []
    <event>: []
    <sector>: []
    <signal>: []
```

## Production

```yaml
production:
  report_title: "<DOMAIN> — Pre-Filtered Candidate Queue"
  staging_item_target: [15, 18]
  staging_per_section: [5, 6]
  distributed_item_target: [5, 8]
  sections: ["<A>", "<B>", "<C>"]
  deliverable_name: "<DOMAIN>_v[YYYYMMDD]_STAGING"
```
````

**Scopes:** `title` matches the headline only; `blob` matches headline and body together. Use `title` where a term only counts as the subject.

---

## Before you trust it

1. **It parses, and every referenced group exists.**
   `python3 -m core.pnd --domain <name> --get manifest.domain`

2. **No group is empty.** Configuration validates fine with empty term lists, then scores everything into the catch-all tier and looks like it is working.
   ```bash
   python3 -c "
   import sys; sys.path.insert(0,'.')
   from core.pnd import load_domain
   d = load_domain(domain='<name>')
   print('sensors:', len(d['sensors']))
   print('groups: ', {k: len(v) for k, v in d['scoring']['groups'].items()})"
   ```

3. **Your Part 2.2 examples score where you expect.** Write each into the corpus by hand and re-score. If your imagined Tier 1 item does not come out Tier 1, the rules do not say what you think they say.

4. **Run three or four cycles before judging it.** Read the drop list more closely than the candidates — a good item below the cut is the most informative signal you will get.

---

## What this survey does not give you

Requirements, not answers. Sanctum orders a queue; it does not understand your domain and it does not write your product. The human gate is the point, not a limitation.

Expect the first two or three editions to be mediocre. Tuning against real output is the work — this survey just makes sure you are tuning something coherent rather than guessing.
