# S2 — Planning & Direction

*Sanctum · `s2` · the only file the engine reads.*

**BLUF:** This declares what the S2 domain cares about. Nothing here describes
engine behaviour. The requirements tree lives in `requirements.md`; the
reasoning behind the word lists lives in `vocab.md`; **every number, term and
threshold lives here and nowhere else.**

**Reader.** The S2 section of an Army combat aviation brigade. Awareness, not
decision support — success is *"they were not surprised,"* not *"they acted."*
The section works strategic-to-operational; battalions handle
operational-to-tactical, so tactical detail is lower value here. Platforms of
interest are utility, cargo, and attack rotary wing plus organic unmanned.

**Schema questions resolved 2026-08-18** against `core/rules.py` by test, not by
reading. Proximity, nesting, and multiplier conjunctions are all supported;
tiers cannot double-count and multipliers can. Every rule below reflects those
answers.

**The first runs test the sensors, not the scoring model.** `requirements.md`
finds one of 43 collectable facts confidently covered and fifteen with none.
With collection that thin, `force_surface` will rarely fire and 948 terms cannot
rank an article the sensors never fetched. A quiet surface is a collection
finding, not a scoring defect.

---

## Manifest

```yaml
manifest:
  domain: s2
  base_dir: /opt/ravenor-s2            # Linux path — collection runs on the
                                       # collector host, not the authoring
                                       # workstation. Differs from CTI's
                                       # /opt/ravenor: shared base_dir means
                                       # shared seen-lists and one domain
                                       # silently starves the other.
                                       # NOTE: SANCTUM_BASE, if set on the host,
                                       # OVERRIDES this. Confirm it is unset or
                                       # both domains land in one directory and
                                       # this config is silently ignored.
  corpus:
    backend: rclone
    rclone_remote: gdrive:ravenor-s2-corpus
  staging:
    backend: rclone
    rclone_remote: gdrive:ravenor-s2-staging
    filename: "S2_{date}_STAGING.md"
  collection:
    window_days: 35                    # NOT the 7-day default. The pull is
                                       # roughly monthly and irregular; at 7,
                                       # most of the month goes unscored.
    min_title_len: 15
    suffix_separators: [" - ", " | ", " — "]
```

---

## Sensors — collection feed list

**Every URL below is UNVERIFIED against the collector host's egress.** Verify
before the first run; several defence publishers return 403 to datacentre
addresses while serving browsers normally.

**Coverage warning.** `requirements.md` Byproduct 2 finds that of 43 collectable
facts in this domain, one has confident coverage and fifteen have none. This
sensor set does not answer PIR-2 at all. **Sources are this domain's real
constraint — vocabulary cannot compensate, because the collector never reads the
word groups.**

```sensors
# Verified reachable and confirmed to return XML from the collector host,
# 2026-08-19. Re-verify from the HOST, never a browser: several defence
# publishers serve browsers normally and return 403 to datacentre addresses.

# --- trade press ---
https://www.defensenews.com/arc/outboundfeeds/rss/

# --- imagery-derived / first-look at hardware ---
https://www.twz.com/feed

# --- adversary primary source ---
https://www.ecns.cn/rss/rss.xml

# --- adversary systems and air-domain specialist ---
https://chinese-military-aviation.blogspot.com/feeds/posts/default?alt=rss
https://www.china-arms.com/feed/

# --- regional strategic analysis ---
# ASPI posts several times a week on Indo-Pacific security specifically.
# Nothing else in this list gives regional strategic assessment.
https://www.aspistrategist.org.au/feed/

# --- China analysis ---
# Lower volume than ASPI. Chokepoint and maritime coverage should finally give
# the chokepoint multiplier something to act on.
https://chinapower.csis.org/feed/

# --- rotary-wing professional press ---
# Skews civil (HEMS, SAR, offshore). Added to address zero Tier 3 hits across
# two cycles - not one article in 27 contained a rotary-wing term. Watch
# whether it is additive or merely loud.
https://verticalmag.com/feed/

# --- REJECTED, do not re-add without re-testing ---
# blog.usni.org/feed - 301s to www.usni.org/feed, which returns 403 behind bot
#   protection. Serves browsers, blocks the collector. Removed 2026-08-19.
# english.chinamil.com.cn/rss.xml - PLA Daily. TLS certificate does not match
#   the hostname; http and eng. variants return 404 meta-refresh pages. The
#   endpoint appears to be gone. THIS WAS THE INTENDED SOURCE FOR THE
#   DECLARED-INTENT SIGNAL, which remains without a proper feed.
# china.org.cn/rss/1201719.xml - returns HTML, not a feed.
# ainonline.com/rss.xml - 404.
# rotorhub.com/feed - real feed, but overlaps verticalmag heavily and is
#   explicitly civil and parapublic. Held under 6.1: cannot say what it gives
#   that verticalmag does not.
# understandingwar.org - ISW. /feed and /feed without www both return HTML,
#   /rss.xml returns 403. Content is a good fit; no usable feed found 2026-08-19.
# iiss.org/rss/ - 403.
# csis.org/analysis/feed - 404. The chinapower subdomain feed works.
# rand.org/topics/china.xml - returns the channel title and no items. Empty or
#   unparseable. Not worth debugging.

# --- UNDER REVIEW, decide after cycle 4 ---
# ecns.cn - largest single source at ~50 articles in one cycle and contributed
#   NOTHING above the catch-all floor. It is a general news agency, not a
#   military organ. Under 6.1 a high-volume non-additive feed should be dropped.
#   Kept for now only because it is the sole adversary primary source remaining.
# chinese-military-aviation.blogspot.com - collected ZERO articles in its first
#   cycle. A specialist blog returning nothing is a sensor failure, not rarity.
#   Diagnose before the next cycle.

# --- STILL MISSING, see requirements.md Byproduct 1 ---
# 1. A military rotary-wing professional source. Vertical is civil-leaning and
#    the military-specific publications are subscription-only.
# 2. Conflict OSINT loss documentation. The accounts that systematically record
#    rotary-wing losses publish on social platforms with no feed. This EEI may
#    need a mechanism other than a sensor.
# 3. Adversary military primary source, to replace PLA Daily.
# 4. Host-nation and regional press within the AOR.
```

---

## Scoring

An item takes the weight of the **highest tier it qualifies for** — tiers are
not additive. Multipliers stack multiplicatively on top. Absent multipliers are
neutral, never a penalty.

**Design intent, tiers.** Tier rank encodes how *directly* an item hits, not how
much the reader cares. A high-ranked requirement legitimately sits in a low tier
— PIR-2 is ranked second and lives in Tier 3 because environmental conditions
are genuinely less direct than an adversary act. That is not an error; do not
"fix" it.

**Design intent, Tier 2.** Deliberately platform-anchored rather than
theatre-anchored: the aviation mission is constant, the theatre is an
assignment. A system that kills someone else's helicopters today is a system
that kills ours later. Geography stops mattering below Tier 1.

```yaml
scoring:
  tiers:
    # PROXIMITY CONFIRMED AVAILABLE. Two deliberate choices below.
    #
    # a-side is event_words, NOT actor_adversary. The a-side term is located by
    # raw substring search with no word-boundary protection; the b-side uses the
    # boundary matcher. actor_adversary contains "PLAN", which raw-matches inside
    # "planning" and would anchor the window on the wrong text. Event verbs are
    # longer and mostly not embeddable, so they are the safer anchor.
    #
    # Only the FIRST occurrence of each a-side term is tested. That is a
    # per-term limit, not per-group: with a large event vocabulary the rule gets
    # many anchor points, which materially reduces the risk. It does not
    # eliminate it — an adversary named early in passing and again beside an
    # event word later will still be missed.
    #
    # Proximity never searches the title, so the second branch covers the case
    # where both terms appear in a headline. Titles are short, so co-occurrence
    # there is inherently proximate.
    # CYCLE 4 FINDING — actor group corrected 2026-08-19.
    # Tier 1 returned ZERO across four cycles and ~300 articles. Cause: the
    # actor group held institutional names only (PLA, PLAN, China Coast Guard),
    # because bare demonyms had been excluded as too noisy. State names were in
    # the geography group instead. So an analytical piece on "China's increased
    # military activities in the Indo-Pacific" — which answers the top-ranked
    # requirement completely — matched geography twice and no actor at all, and
    # scored as a catch-all item.
    #
    # State names added to the actor group. An INDOPACOM state name now
    # satisfies both the actor and the geography condition from one word, which
    # is intended: naming the state establishes both. Non-AOR adversaries
    # (Russia, Iran) still require separate INDOPACOM geography, which is also
    # intended.
    #
    # WATCH: this could over-fire. "China" plus any event verb in proximity now
    # reaches 8.0. Accepted deliberately — four cycles of zero is measured, the
    # risk of over-firing is speculative, and under a "not surprised" standard a
    # miss costs more than a false positive. Reassess after two cycles.
    #
    # Tier 1 is deliberately PLATFORM-AGNOSTIC. It asks whether the adversary is
    # moving in our theatre, which matters whether or not aircraft are named.
    # The rotary-wing lens lives in Tier 3 and in force_surface, where it
    # discriminates. Putting it here too is what made the top requirement
    # unreachable by the top tier.
    - id: 1
      name: "adversary activity or capability change inside INDOPACOM affecting rotary wing"
      weight: 8.0
      require:
        any:
          - all:
              - {group: geo_indopacom, scope: blob}
              - proximity: {a: event_words, b: actor_adversary, window: 120}
          - all:
              - {group: actor_adversary, scope: title}
              - {group: geo_indopacom, scope: title}

    # CYCLE 1 FINDING — REWRITTEN 2026-08-19.
    # The previous rule was a bare any: across the threat groups, with no
    # adversary requirement at all. The word "adversary" was in the tier's name
    # and nowhere in its rule. Result: a US counter-drone cannon, a DARPA
    # missile designed to EVADE air defences, and US missile production
    # contracts all scored as adversary capability. Ten of ten surfaced items
    # in cycle 1 were US or allied stories.
    #
    # Cause: the threat groups mixed two kinds of term. Designations like the
    # HQ, S-, Igla and SA- series self-identify as adversary systems. Generic
    # capability terms — "air defense system", "counter-UAS", "surface-to-air
    # missile" — describe anyone's kit, including ours.
    #
    # Fix: designations qualify alone; generic capability terms must appear
    # alongside an adversary actor.
    - id: 2
      name: "adversary capability threatening rotary wing, anywhere"
      weight: 4.0
      require:
        any:
          # branch A — named adversary systems, self-identifying
          - any:
              - {group: threat_manpads, scope: blob}
              - {group: threat_sam, scope: blob}
              - {group: threat_aaa_cuas, scope: blob}
              - {group: threat_ew, scope: blob}
              - {group: threat_small_arms, scope: blob}
              - {group: threat_uas_loitering, scope: blob}
              - {group: threat_sa_designations, scope: blob}
          # branch B — capability class, adversary attribution required
          - all:
              - any:
                  - {group: threat_manpads_generic, scope: blob}
                  - {group: threat_sam_generic, scope: blob}
                  - {group: threat_aaa_cuas_generic, scope: blob}
                  - {group: threat_ew_generic, scope: blob}
                  - {group: threat_small_arms_generic, scope: blob}
                  - {group: threat_uas_loitering_generic, scope: blob}
              - {group: actor_adversary, scope: blob}

    # NESTING CONFIRMED: any and all recurse through the same evaluator, so two
    # alternate conjunction branches belong in ONE tier. Do not split this into
    # two tiers of equal weight — tier assignment stops at the first match, so
    # the second would be unreachable for anything the first already caught, and
    # the reasoning line would name only one branch.
    # CYCLE 3 FINDING — REWRITTEN 2026-08-19.
    # The previous rule required conflict_markers AND platform_rotary_wing
    # anywhere in the body, with no proximity. Bare "helicopter" plus one
    # generic conflict word is satisfied by almost any long-form defence
    # article. Observed false positives: a carrier's island superstructure
    # ('ongoing conflict' + 'helicopter'), a Polish frigate ('countermeasure' +
    # 'helicopter'), and homeland drone defence ('shot down' + 'helicopter').
    # None is a rotary-wing lesson.
    #
    # Fix: proximity, same mechanism as Tier 1. A helicopter named in paragraph
    # two and "destroyed" in paragraph nine is not a rotary-wing loss.
    #
    # a-side is the conflict and environment groups, NOT platform. The a-side
    # gets raw substring search with no word-boundary protection; platform
    # contains short designations that would anchor windows wrongly.
    #
    # Third branch covers titles, which proximity never searches. Titles are
    # short, so co-occurrence there is inherently proximate.
    - id: 3
      name: "rotary-wing lessons from active conflict, or AOR conditions degrading rotary-wing operations"
      weight: 2.0
      require:
        any:
          # active-conflict branch
          - proximity: {a: conflict_markers, b: platform_rotary_wing, window: 120}
          # active-conflict branch, title scope
          - all:
              - {group: conflict_markers, scope: title}
              - {group: platform_rotary_wing, scope: title}
          # AOR environmental branch
          - all:
              - proximity: {a: env_basing, b: platform_rotary_wing, window: 120}
              - {group: geo_indopacom, scope: blob}

    - id: 4
      name: "in scope, no stronger anchor"
      weight: 1.0
      require: always

  multipliers:
    # FACTORS REDUCED AND ONE SIGNAL DROPPED — 2026-08-19, cycle 3.
    #
    # The stack was six signals at 1.5/1.3, which multiplies to 6.43x, not the
    # ~4.9x recorded in earlier comments. That figure was an arithmetic error
    # carried since Part 4. 6.43x exceeds two tier steps, so relevance had
    # stopped ordering the queue: an observed catch-all item with five signals
    # scored 6.43 and outranked every Tier 2 and Tier 3 item in the cycle.
    #
    # The chokepoint signal is dropped outright. It fired on five of ten
    # candidates. A signal that fires on most items carries no information, and
    # in an INDOPACOM domain strait names are background, not signal. The names
    # remain in the geography group, where they do real work — no coverage is
    # lost. This also resolves the cross-group duplication recorded in vocab.md.
    #
    # Remaining five at 1.4 / 1.2 multiply to 3.39x — under two tier steps, so
    # a fully-lit catch-all item can no longer beat a bare Tier 2.

    - name: "adversary declares intent, threat or warning"
      factor: 1.4
      when:
        all:
          - {group: declaration_terms, scope: blob}
          - {group: actor_adversary, scope: blob}

    - name: "escalation indicators"
      factor: 1.4
      when: {group: escalation_terms, scope: blob}

    # WATCH: fired on four of ten candidates in cycle 3. If it stays that high
    # it needs pairing with actor_adversary, the same fix applied to declared
    # intent. Not changed yet - one cycle is not enough evidence.

    - name: "coercive or hostile act against US forces, allies or partners"
      factor: 1.2
      when: {group: coercive_acts, scope: blob}

    - name: "first occurrence or fielding"
      factor: 1.2
      when: {group: first_occurrence, scope: blob}

    - name: "fixed-date event window"
      factor: 1.2
      when: {group: fixed_date_events, scope: blob}

  # Inclusion, never ranking. Deliberately narrow: a threat system that actually
  # engaged something is the one case where a low score would be wrong no matter
  # what else the item lacks. Both halves are required — a threat system alone
  # is ordinary Tier 2 material.
  #
  # Highest-cost position in the config for a noisy term: the score cannot
  # correct a bad match here. Nothing enters these groups without a collision
  # audit in vocab.md.
  force_surface:
    - name: "threat system engaged an aircraft"
      require:
        all:
          - any:
              # designations
              - {group: threat_manpads, scope: blob}
              - {group: threat_sam, scope: blob}
              - {group: threat_aaa_cuas, scope: blob}
              - {group: threat_small_arms, scope: blob}
              - {group: threat_uas_loitering, scope: blob}
              # capability class — no adversary term required here, because the
              # conflict and platform conditions below already do that work. An
              # aircraft taking ground fire in an active conflict is worth
              # reading whoever was flying it.
              - {group: threat_manpads_generic, scope: blob}
              - {group: threat_sam_generic, scope: blob}
              - {group: threat_aaa_cuas_generic, scope: blob}
              - {group: threat_small_arms_generic, scope: blob}
              - {group: threat_uas_loitering_generic, scope: blob}
          - {group: conflict_markers, scope: blob}
          # WIDENED 2026-08-19 to any aircraft, not rotary wing only. A fixed-wing
          # aircraft downed by a man-portable system tells you about the system,
          # and that is worth guaranteed inclusion. Volume stays low because the
          # conflict and threat conditions above still both have to hold.
          - any:
              - {group: platform_rotary_wing, scope: blob}
              - {group: platform_fixed_wing, scope: blob}

  settings:
    # PROVISIONAL. Not measured against a real corpus. At 2.0 a bare Tier 4
    # item (1.0) does not surface, but a Tier 4 item with any two multipliers
    # does. Re-measure after three cycles. Tune weights and vocabulary, never
    # cap the count — the uncapped surface is the diagnostic.
    surface_min_score: 2.0
    empty_title: {score: 0.5, tier: 4, flag: "FLAG: empty title (feed artifact — verify source)"}
    recency:
      enabled: true
      window_days: 35          # MUST track collection.window_days above, or
                               # most of the corpus is flagged stale on every
                               # run. Flags only; never drops.
      cutoff_weekday: monday
      cutoff_time: "05:00"
      timezone: UTC
    grouping:
      enabled: true
      min_similarity: 0.55
      min_shared_tokens: 3
      min_evidence: 8.0
      max_group_size: 25
      max_group_display: 12

  # Terms longer than 4 characters that can appear inside a longer word. The
  # matcher applies boundaries automatically at <=4, so shorter entries do
  # nothing. Rationale for each is in vocab.md.
  word_boundary_terms:
    - "China"
    - "Verba"
    - "Palau"
    - "Samoa"
    - "Tonga"
    - "Matsu"
    - "Nauru"
    - "Miyako"
    - "Brunei"
    - "Kinmen"
    - "Pratas"
    - "Sosna"
    - "debut"
    - "plenum"
    - "Malabar"
    - "Vostok"
    - "Zapad"

  groups:
    # 19 groups. Terms live here and only here — vocab.md records decisions
    # about them and never repeats them.
    #
    # POPULATE FROM: s2_vocab_loadbearing.md Part A (3 groups),
    # vocab_threat_systems_v4.md (7 groups),
    # s2_vocab_remaining.md Part A (9 groups).
    #
    # An empty group passes the loader's reference check and then matches
    # nothing, so a rule using it reads as active and is inert.
    # tools/vocab_check.py treats that as an error.

    geo_indopacom:
      - "force_surface"
      - "China"
      - "PRC"
      - "Taiwan"
      - "ROC"
      - "Japan"
      - "Philippines"
      - "South Korea"
      - "Republic of Korea"
      - "North Korea"
      - "DPRK"
      - "Australia"
      - "Indonesia"
      - "Malaysia"
      - "Vietnam"
      - "Thailand"
      - "Singapore"
      - "Brunei"
      - "Cambodia"
      - "Myanmar"
      - "Burma"
      - "Laos"
      - "Bangladesh"
      - "Sri Lanka"
      - "Maldives"
      - "Papua New Guinea"
      - "New Zealand"
      - "Palau"
      - "Micronesia"
      - "Nauru"
      - "Kiribati"
      - "Tuvalu"
      - "Vanuatu"
      - "Tonga"
      - "Samoa"
      - "Fujian"
      - "Guangdong"
      - "Hainan"
      - "Zhejiang"
      - "Jiangsu"
      - "Shandong"
      - "Yunnan"
      - "Xinjiang"
      - "Tibet"
      - "Hong Kong"
      - "Macau"
      - "Inner Mongolia"
      - "Luzon"
      - "Mindanao"
      - "Palawan"
      - "Batanes"
      - "Okinawa"
      - "Kyushu"
      - "Hokkaido"
      - "Honshu"
      - "Guam"
      - "Saipan"
      - "Tinian"
      - "Wake Island"
      - "Diego Garcia"
      - "Senkaku"
      - "Diaoyu"
      - "Spratly"
      - "Nansha"
      - "Paracel"
      - "Xisha"
      - "Second Thomas Shoal"
      - "Ayungin"
      - "Scarborough Shoal"
      - "Woody Island"
      - "Mischief Reef"
      - "Fiery Cross"
      - "Subi Reef"
      - "Itu Aba"
      - "Pratas"
      - "Dongsha"
      - "Kinmen"
      - "Quemoy"
      - "Matsu"
      - "Pescadores"
      - "Penghu"
      - "Yonaguni"
      - "Ishigaki"
      - "Miyako"
      - "Bougainville"
      - "Guadalcanal"
      - "Timor-Leste"
      - "Sumatra"
      - "Sulawesi"
      - "Mindoro"
      - "Basilan"
      - "Jolo"
      - "South China Sea"
      - "East China Sea"
      - "Philippine Sea"
      - "Yellow Sea"
      - "Sea of Japan"
      - "Taiwan Strait"
      - "Luzon Strait"
      - "Bashi Channel"
      - "Miyako Strait"
      - "Osumi Strait"
      - "Tsushima Strait"
      - "Korea Strait"
      - "Malacca Strait"
      - "Strait of Malacca"
      - "Sunda Strait"
      - "Lombok Strait"
      - "Makassar Strait"
      - "Celebes Sea"
      - "Sulu Sea"
      - "Andaman Sea"
      - "Bay of Bengal"
      - "Coral Sea"
      - "Timor Sea"
      - "Arafura Sea"
      - "first island chain"
      - "second island chain"
      - "nine-dash line"
      - "ten-dash line"
      - "Kadena Air Base"
      - "Yokota Air Base"
      - "Misawa Air Base"
      - "Iwakuni"
      - "Camp Zama"
      - "Torii Station"
      - "Camp Humphreys"
      - "Osan Air Base"
      - "Kunsan Air Base"
      - "Andersen Air Force Base"
      - "Clark Air Base"
      - "Subic Bay"
      - "Basa Air Base"
      - "Antonio Bautista"
      - "RAAF Darwin"
      - "RAAF Tindal"
      - "Robertson Barracks"
      - "Wheeler Army Airfield"
      - "Schofield Barracks"
      - "Joint Base Pearl Harbor-Hickam"
      - "INDOPACOM"
      - "INDO-PACOM"
      - "Indo-Pacific"
      - "Indo Pacific"
      - "USARPAC"
      - "PACAF"
      - "PACFLT"
      - "Western Pacific"
      - "WESTPAC"
    event_words:
      - "deployed"
      - "deploying"
      - "deployment"
      - "stationed"
      - "positioned"
      - "repositioned"
      - "relocated"
      - "moved"
      - "transferred"
      - "arrived"
      - "dispatched"
      - "forward-deployed"
      - "rotated"
      - "surged"
      - "fielded"
      - "fielding"
      - "commissioned"
      - "entered service"
      - "operational"
      - "activated"
      - "stood up"
      - "established"
      - "unveiled"
      - "revealed"
      - "delivered"
      - "inducted"
      - "accepted"
      - "conducted"
      - "carried out"
      - "launched"
      - "tested"
      - "test-fired"
      - "fired"
      - "exercised"
      - "patrolled"
      - "transited"
      - "overflew"
      - "intercepted"
      - "scrambled"
      - "intruded"
      - "incursion"
      - "crossed"
      - "breached"
      - "violated"
      - "constructed"
      - "built"
      - "expanded"
      - "upgraded"
      - "reclaimed"
      - "militarized"
      - "hardened"
      - "broke ground"
      - "increased"
      - "escalated"
      - "intensified"
      - "stepped up"
      - "accelerated"
      - "resumed"
      - "suspended"
      - "halted"
      - "withdrew"
      - "reduced"
    actor_adversary:
      - "China"
      - "PRC"
      - "Beijing"
      - "Russia"
      - "Russian Federation"
      - "Moscow"
      - "North Korea"
      - "DPRK"
      - "Pyongyang"
      - "Iran"
      - "Tehran"
      - "PLA"
      - "People's Liberation Army"
      - "PLAAF"
      - "PLA Air Force"
      - "PLAN"
      - "PLA Navy"
      - "PLARF"
      - "PLA Rocket Force"
      - "PLAGF"
      - "PLA Ground Force"
      - "Information Support Force"
      - "PLASSF"
      - "Strategic Support Force"
      - "Eastern Theater Command"
      - "Southern Theater Command"
      - "Central Military Commission"
      - "Ministry of National Defense"
      - "China Coast Guard"
      - "CCG"
      - "maritime militia"
      - "People's Armed Forces Maritime Militia"
      - "PAFMM"
      - "Chinese Communist Party"
      - "CCP"
      - "Xi Jinping"
      - "Russian Armed Forces"
      - "VKS"
      - "Russian Aerospace Forces"
      - "Pacific Fleet"
      - "Eastern Military District"
      - "Russian Ministry of Defence"
      - "Russian Ministry of Defense"
      - "Korean People's Army"
      - "KPA"
      - "KPAAF"
      - "Korean People's Army Air Force"
      - "Workers' Party of Korea"
      - "Kim Jong Un"
      - "IRGC"
      - "Islamic Revolutionary Guard Corps"
      - "Iranian Armed Forces"
    platform_fixed_wing:
      - "fighter jet"
      - "warplane"
      - "combat aircraft"
      - "transport aircraft"
      - "tanker aircraft"
      - "surveillance aircraft"
      - "F-15"
      - "F-16"
      - "F-22"
      - "F-35"
      - "A-10"
      - "C-130"
      - "C-17"
      - "P-8"
      - "Su-27"
      - "Su-30"
      - "Su-34"
      - "Su-35"
      - "Su-57"
      - "MiG-29"
      - "MiG-31"
      - "J-10"
      - "J-11"
      - "J-15"
      - "J-16"
      - "J-20"
      - "H-6"
      - "Y-20"
      - "KJ-500"
    platform_rotary_wing:
      - "UH-60"
      - "MH-60"
      - "HH-60"
      - "CH-47"
      - "AH-64"
      - "UH-72"
      - "AH-6"
      - "MH-6"
      - "Mi-8"
      - "Mi-17"
      - "Mi-24"
      - "Mi-28"
      - "Mi-35"
      - "Ka-50"
      - "Ka-52"
      - "Z-8"
      - "Z-9"
      - "Z-10"
      - "Z-19"
      - "Z-20"
      - "WZ-10"
      - "WZ-19"
      - "helicopter"
      - "helicopters"
      - "rotorcraft"
      - "rotary-wing"
      - "rotary wing"
      - "helo"
      - "attack helicopter"
      - "transport helicopter"
      - "utility helicopter"
      - "troop-carrying helicopter"
      - "tiltrotor"
      - "tilt-rotor"
      - "RQ-7"
      - "MQ-1C"
      - "Gray Eagle"
      - "Grey Eagle"
      - "FTUAS"
      - "tactical UAS"
      - "air assault"
      - "air movement"
      - "MEDEVAC"
      - "CASEVAC"
      - "aeromedical evacuation"
      - "aerial resupply"
      - "sling load"
      - "terrain flight"
      - "nap-of-the-earth"
      - "manned-unmanned teaming"
      - "MUM-T"
      - "aviation brigade"
      - "aviation regiment"
      - "army aviation"
      - "rotary-wing aviation"
    conflict_markers:
      - "shot down"
      - "shootdown"
      - "shoot-down"
      - "downed"
      - "brought down"
      - "went down"
      - "crashed"
      - "crash-landed"
      - "destroyed"
      - "wreckage"
      - "combat loss"
      - "operational loss"
      - "hit by"
      - "struck by"
      - "engaged by"
      - "damaged in"
      - "active conflict"
      - "ongoing conflict"
      - "front line"
      - "frontline"
      - "line of contact"
      - "contested airspace"
      - "combat operations"
      - "war zone"
      - "battlefield"
      - "offensive"
      - "counteroffensive"
      - "ceasefire"
      - "hostilities"
      - "sortie"
      - "sorties"
      - "mission profile"
      - "tactics"
      - "TTP"
      - "tactics techniques and procedures"
      - "lessons learned"
      - "after-action"
      - "countermeasure"
      - "countermeasures"
      - "survivability"
      - "attrition"
      - "loss rate"
      - "standoff"
    env_basing:
      - "density altitude"
      - "high and hot"
      - "high-hot"
      - "hot and high"
      - "power margin"
      - "lift margin"
      - "payload penalty"
      - "performance degradation"
      - "icing conditions"
      - "aircraft icing"
      - "airframe icing"
      - "brownout"
      - "whiteout"
      - "degraded visual environment"
      - "salt spray"
      - "salt fog"
      - "corrosion"
      - "corrosive"
      - "humidity"
      - "sand ingestion"
      - "foreign object damage"
      - "typhoon"
      - "super typhoon"
      - "monsoon"
      - "tropical cyclone"
      - "wet season"
      - "storm season"
      - "crosswind"
      - "tailwind"
      - "austere basing"
      - "austere airfield"
      - "dispersed basing"
      - "distributed basing"
      - "expeditionary basing"
      - "agile combat employment"
      - "forward arming and refueling"
      - "FARP"
      - "forward operating site"
      - "cooperative security location"
      - "runway"
      - "taxiway"
      - "revetment"
      - "hardened aircraft shelter"
      - "hangar"
      - "ramp space"
      - "parking apron"
      - "matting"
      - "landing zone"
      - "pickup zone"
      - "sustainment"
      - "resupply"
      - "logistics tail"
      - "fuel bladder"
      - "aviation fuel"
      - "contested logistics"
      - "tyranny of distance"
      - "maintenance availability"
      - "readiness rate"
      - "mission capable rate"
    threat_manpads:
      - "QW-1"
      - "QW-1M"
      - "QW-2"
      - "QW-3"
      - "QW-11"
      - "QW-18"
      - "QW-19"
      - "Qianwei"
      - "Qian Wei"
      - "FN-6"
      - "FN-16"
      - "HN-5"
      - "HN-6"
      - "Hongying"
      - "Hong Ying"
      - "Igla"
      - "Igla-1"
      - "Igla-S"
      - "9K38"
      - "9K310"
      - "9K338"
      - "Verba"
      - "9K333"
      - "9M336"
      - "Strela-2"
      - "Strela-3"
      - "Strela-10"
      - "9K32"
      - "9K34"
      - "9K36"
      - "HT-16PGJ"
      - "Hwasung-Chong"
      - "Igla copy"
      - "Misagh-1"
      - "Misagh-2"
      - "Anza"
      - "Anza-2"
      - "Grom"
      - "Chiron"
      - "Shingung"
    threat_sam:
      - "HQ-2"
      - "HQ-6"
      - "HQ-7"
      - "HQ-9"
      - "HQ-9B"
      - "HQ-11"
      - "HQ-12"
      - "HQ-16"
      - "HQ-16A"
      - "HQ-16B"
      - "HQ-17"
      - "HQ-17A"
      - "HQ-19"
      - "HQ-20"
      - "HQ-22"
      - "HQ-61"
      - "HHQ-9"
      - "HHQ-10"
      - "Hongqi"
      - "Hong Qi"
      - "KS-1"
      - "KS-1A"
      - "FK-3"
      - "FD-2000"
      - "FT-2000"
      - "S-300"
      - "S-300PMU"
      - "S-300V"
      - "S-350"
      - "S-400"
      - "S-500"
      - "Triumf"
      - "Favorit"
      - "Vityaz"
      - "Antey-2500"
      - "Tor-M1"
      - "Tor-M2"
      - "9K330"
      - "9K331"
      - "9K332"
      - "Buk"
      - "Buk-M1"
      - "Buk-M2"
      - "Buk-M3"
      - "9K37"
      - "Pantsir"
      - "Pantsir-S1"
      - "Pantsir-S2"
      - "9K33"
      - "Sosna"
      - "Sosna-R"
      - "9M337"
      - "Pechora"
      - "S-75"
      - "S-125"
      - "S-200"
      - "Pongae-5"
      - "Pongae-6"
      - "Pon'gae-5"
      - "Pon'gae-6"
      - "KN-06"
      - "Pyoljji"
      - "Pyoljji-1-2"
      - "Lightning-5"
      - "Lightning-6"
      - "Taebaeksan"
      - "Taepaekasan"
    threat_aaa_cuas:
      - "Tunguska"
      - "2K22"
      - "Shilka"
      - "ZSU-23-4"
      - "ZU-23"
      - "ZSU-57"
      - "Derivatsiya"
      - "PGZ-95"
      - "PGZ-09"
      - "PGZ-04"
      - "LD-2000"
      - "LD-3000"
      - "Type 625"
      - "Type 730"
      - "Type 1130"
      - "M1989"
      - "M1992"
      - "KS-19"
      - "ZPU-1"
      - "ZPU-2"
      - "ZPU-4"
    threat_ew:
      - "Krasukha"
      - "Krasukha-4"
      - "Murmansk-BN"
      - "Borisoglebsk-2"
      - "Zhitel"
      - "Leer-3"
      - "RB-341V"
      - "Tirada-2"
      - "Silok"
      - "Pole-21"
      - "Repellent"
    threat_small_arms:
      - "RPG-7"
      - "RPG-29"
      - "RPG-32"
      - "PG-7VR"
      - "DShK"
      - "DShKM"
      - "KPV"
      - "KPVT"
      - "NSV"
      - "Kord"
      - "PKM"
      - "Type 54"
      - "Type 77"
      - "W85"
    threat_uas_loitering:
      - "CH-901"
      - "FH-901"
      - "BG-201"
      - "WS-43"
      - "ASN-301"
      - "CY-200"
      - "Novasky"
      - "Wing Loong"
      - "GJ-11"
      - "GJ-2"
      - "WZ-7"
      - "FH-97"
      - "Jiutian"
      - "Lancet-1"
      - "Lancet-3"
      - "Lancet-3M"
      - "Izdeliye 51"
      - "Izdeliye 52"
      - "Izdeliye 53"
      - "ZALA"
      - "Zala Aero"
      - "Orlan-10"
      - "Orlan-30"
      - "Gerbera"
      - "Geran-1"
      - "Geran-2"
      - "Geran-3"
      - "Alabuga"
      - "Shahed-131"
      - "Shahed-136"
      - "HESA Shahed"
      - "Saetbyol-4"
      - "Saetbyol-9"
      - "Kumsong"
    threat_sa_designations:
      - "SA-2"
      - "SA-3"
      - "SA-6"
      - "SA-7"
      - "SA-8"
      - "SA-10"
      - "SA-11"
      - "SA-13"
      - "SA-14"
      - "SA-15"
      - "SA-16"
      - "SA-17"
      - "SA-18"
      - "SA-19"
      - "SA-20"
      - "SA-21"
      - "SA-22"
      - "SA-23"
      - "SA-24"
      - "SA-26"
      - "SA-27"
      - "SA-29"
      - "CH-SA-8"
      - "CH-SA-11"
      - "CH-SA-12"
      - "CH-SA-16"
    threat_manpads_generic:
      - "MANPADS"
      - "MANPAD"
      - "man-portable air defense"
      - "man-portable air-defence"
      - "shoulder-fired missile"
      - "shoulder launched"
      - "shoulder-launched"
    threat_sam_generic:
      - "surface-to-air missile"
      - "surface to air missile"
      - "SAM battery"
      - "SAM system"
      - "SHORAD"
      - "IADS"
      - "integrated air defense"
      - "integrated air defence"
      - "air defense system"
      - "air defence system"
      - "transporter erector launcher"
    threat_aaa_cuas_generic:
      - "anti-aircraft artillery"
      - "antiaircraft artillery"
      - "anti-aircraft gun"
      - "counter-UAS"
      - "counter UAS"
      - "C-UAS"
      - "counter-drone"
      - "counter drone"
      - "drone interceptor"
      - "self-propelled anti-aircraft"
    threat_ew_generic:
      - "electronic warfare"
      - "electronic attack"
      - "jamming"
      - "jammer"
      - "GPS jamming"
      - "GPS denial"
      - "GPS spoofing"
      - "spoofing"
      - "navigation warfare"
      - "NAVWAR"
      - "SATCOM interference"
      - "communications jamming"
      - "datalink jamming"
      - "electromagnetic spectrum"
      - "EMS operations"
      - "signal interference"
    threat_small_arms_generic:
      - "small arms fire"
      - "ground fire"
      - "heavy machine gun"
      - "machine gun fire"
      - "rocket-propelled grenade"
      - "rocket propelled grenade"
      - "RPG fire"
      - "shot down by small arms"
      - "struck by ground fire"
      - "took fire"
    threat_uas_loitering_generic:
      - "loitering munition"
      - "loitering munitions"
      - "one-way attack"
      - "one way attack"
      - "OWA drone"
      - "kamikaze drone"
      - "suicide drone"
      - "FPV drone"
      - "FPV"
      - "first-person view drone"
      - "drone swarm"
      - "swarming attack"
      - "mothership drone"
      - "mother drone"
      - "drone carrier"
      - "attritable"
      - "attritable drone"
      - "anti-aircraft FPV"
      - "interceptor drone"
      - "hard-kill interceptor"
    declaration_terms:
      - "warned"
      - "warns"
      - "warning"
      - "threatened"
      - "threatens"
      - "threat to"
      - "vowed"
      - "vows"
      - "pledged"
      - "pledges"
      - "declared"
      - "declares"
      - "asserted"
      - "insisted"
      - "cautioned"
      - "red line"
      - "will not hesitate"
      - "reserves the right"
      - "serious consequences"
      - "grave consequences"
      - "will pay the price"
      - "all necessary measures"
      - "will take resolute"
      - "resolute measures"
      - "firm countermeasures"
      - "will not stand idly"
      - "crossing the line"
      - "provocation will be met"
      - "ultimatum"
      - "final warning"
      - "retaliate"
      - "retaliation"
      - "countermeasures against"
      - "lodged a protest"
      - "solemn representations"
      - "stern representations"
      - "demarche"
      - "summoned the ambassador"
      - "spokesperson"
      - "spokesman"
      - "ministry spokesperson"
      - "defence ministry said"
      - "defense ministry said"
      - "foreign ministry said"
      - "state media reported"
    escalation_terms:
      - "mobilisation"
      - "mobilization"
      - "mobilised"
      - "mobilized"
      - "partial mobilisation"
      - "partial mobilization"
      - "reserve call-up"
      - "reservists"
      - "called up"
      - "conscription"
      - "draft notice"
      - "force generation"
      - "buildup"
      - "build-up"
      - "troop buildup"
      - "reinforcement"
      - "war footing"
      - "combat readiness"
      - "heightened readiness"
      - "readiness level"
      - "alert level"
      - "combat alert"
      - "high alert"
      - "state of emergency"
      - "martial law"
      - "wartime footing"
      - "snap exercise"
      - "no-notice exercise"
      - "unannounced exercise"
      - "large-scale exercise"
      - "joint exercise"
      - "live-fire exercise"
      - "increased tempo"
      - "stepped-up activity"
      - "record number of"
      - "airspace closure"
      - "airspace restriction"
      - "NOTAM"
      - "notice to airmen"
      - "exclusion zone"
      - "live-fire zone"
      - "navigational warning"
      - "evacuation order"
      - "evacuate nationals"
      - "advised to leave"
      - "travel advisory"
      - "shipping advisory"
    coercive_acts:
      - "unsafe intercept"
      - "unprofessional intercept"
      - "intercepted"
      - "intercept of"
      - "dangerous manoeuvre"
      - "dangerous maneuver"
      - "close approach"
      - "unsafe approach"
      - "cut across"
      - "crossed the bow"
      - "shadowed"
      - "ramming"
      - "rammed"
      - "collided with"
      - "water cannon"
      - "blocked the"
      - "blocking manoeuvre"
      - "blocking maneuver"
      - "swarmed"
      - "boxed in"
      - "seized"
      - "detained the crew"
      - "boarded the vessel"
      - "impounded"
      - "military-grade laser"
      - "lasing"
      - "dazzled"
      - "directed a laser"
      - "released flares"
      - "dispensed chaff"
      - "airspace incursion"
      - "airspace violation"
      - "territorial violation"
      - "entered territorial waters"
      - "crossed the median line"
      - "median line crossing"
      - "ADIZ incursion"
      - "air defence identification zone"
      - "grey-zone"
      - "gray-zone"
      - "harassment of"
      - "harassed"
    first_occurrence:
      - "for the first time"
      - "first-ever"
      - "first ever"
      - "first time"
      - "previously unseen"
      - "not previously observed"
      - "newly identified"
      - "new variant"
      - "unveiled"
      - "revealed"
      - "debut"
      - "debuted"
      - "made its first appearance"
      - "first public"
      - "maiden flight"
      - "first flight"
      - "first test"
      - "first launch"
      - "entered service"
      - "entered operational service"
      - "initial operating capability"
      - "full operational capability"
      - "declared operational"
      - "commissioned"
      - "newly fielded"
      - "began fielding"
      - "serial production"
      - "mass production"
      - "prototype"
      - "testbed"
      - "technology demonstrator"
      - "pre-production"
      - "under evaluation"
    fixed_date_events:
      - "presidential election"
      - "legislative election"
      - "general election"
      - "midterm election"
      - "referendum"
      - "inauguration"
      - "leadership transition"
      - "succession"
      - "party congress"
      - "national congress"
      - "plenum"
      - "plenary session"
      - "National People's Congress"
      - "Two Sessions"
      - "Politburo meeting"
      - "National Day"
      - "founding anniversary"
      - "Army Day"
      - "Victory Day"
      - "Shangri-La Dialogue"
      - "ASEAN Summit"
      - "East Asia Summit"
      - "APEC summit"
      - "G7 summit"
      - "G20 summit"
      - "Quad summit"
      - "AUKUS"
      - "defence ministers meeting"
      - "bilateral summit"
      - "state visit"
      - "RIMPAC"
      - "Balikatan"
      - "Talisman Sabre"
      - "Cobra Gold"
      - "Malabar"
      - "Orient Shield"
      - "Yama Sakura"
      - "Keen Edge"
      - "Keen Sword"
      - "Freedom Shield"
      - "Han Kuang"
      - "Joint Sword"
      - "Strait Thunder"
      - "Vostok"
      - "Zapad"
      - "Summer Olympics"
      - "Winter Olympics"
      - "Asian Games"
```

---

## Production

**No item targets.** The review surface is uncapped by design; restraint belongs
to the vox, applied by a person.

```yaml
production:
  audience: >
    The S2 section of an Army combat aviation brigade — trained all-source
    analysts who will build their own analytical product from this. Assume full
    command of intelligence and aviation terminology; no glossing required.
    They work strategic-to-operational, so pitch above tactical detail. The
    standard they are held to is not being surprised, so a relevance clause
    should say what this changes about what they should expect, not what they
    should do.
  relevance_clause: "Why this matters to you:"
  show_scores: true
  report_title: "S2 — Staging Document (candidate queue)"
  vox_title: "INDOPACOM Threat Awareness — Army Aviation"
  deliverable_name: "S2_v[YYYYMMDD]"
  sections:
    - "ADVERSARY POSTURE — INDOPACOM"
    - "ENVIRONMENT & BASING"
    - "LESSONS FROM CURRENT CONFLICTS"
    - "THREATS TO ROTARY WING"
  notes: >
    Sections follow the PIR order in requirements.md. Note that section order
    reflects requirement priority while tier weight reflects directness of hit,
    so the section a reader considers most important is not the section that
    will carry the highest-scoring items. That is expected.

    vox_title is provisional — name it whatever the section should see on the
    product.
