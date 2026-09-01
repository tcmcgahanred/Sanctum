# WCTI Vox — Policy & Format Specification

*Authoritative spec for the weekly Vox. Its purpose is to lock structure and standards so the product does not creep. Any change to what follows is a Planning & Direction decision, made in the CTI briefing chat and logged; it is not changed ad hoc mid-production. If a request would alter this spec, flag it against this policy first.*

---

## 1. What the Vox is (and is not)

- **Is:** a weekly review surface of collected, prioritized open-source cyber threat items for a low-maturity SLTT audience, handed to the cyber team for review and amendment.
- **Is not:** a finished intelligence product. No analytic assessment, no confidence judgments, no handling markings. The cyber team adds assessment and produces the distributed report.
- **Audience:** non-technical SLTT leaders and staff (county/city government, school districts, small utilities). Everything below serves that reader.

## 2. Cadence & dates

- Collection cutoff / **ICOD** (information current as of): Monday 0500 Pacific.
- Produced: Monday. Team review: Wednesday. Distribution: Thursday.
- **Title date = distribution date (Thursday).** ICOD appears in the header. LTIOV is planning doctrine only — never on the product.

## 3. Naming

- Reader-facing heading: **"WCTI — Weekly Cyber Threat Intelligence."** The word "vox" is internal shorthand only and never appears in the reader-facing document.
- Filename of the PRODUCT: `WCTI_v[YYYYMMDD]` — date is the distribution (Thursday) date.
- Filename of the STAGING DOCUMENT: `WCTI_[YYYYMMDD]_STAGING` — date is the date it was
  **created**, not the distribution date. The two documents are dated on different
  principles because they answer different questions. The product's date tells the reader
  when it reached them. The staging document's date tells the analyst when this queue was
  built — so regenerating a cycle after a scoring change produces a second, distinctly
  named file rather than silently overwriting the first. **The intelligence cycle week is
  tracked by the analyst, not encoded in the artifact name.** The compliance report takes
  the same date as the staging document it reports on.
- No "CCIC" prefix until AOR-direct sensors exist and the product can genuinely focus on a single AOR.

## 4. Header (reader-facing only — no internal plumbing)

The header carries ONLY:
1. Heading: `WCTI — Weekly Cyber Threat Intelligence`
2. Filename + distribution date + ICOD.
3. A one-paragraph summary of what the document is and how it was derived.
4. A short note on the scores.

**Excluded from the header:** internal pipeline artifact paths (e.g., staging-document filenames), internal stage labels, and any Sanctum-internal jargon. A reader who never touches Sanctum should not see machinery.

## 5. Structure

Fixed sections, in order, each ordered internally by priority:
- **NEWS** — incidents, breaches, advisories, announcements.
- **CTA TTPs** — cyber threat actor tactics/techniques (tradecraft).
- **LATEST ATTACKS OR RISKS** — vulnerabilities and active exploitation.
- **KEYWORDS** — wave-top only (vendor/sector names acceptable; not specific products/malware/techniques).

## 6. Per-entry format

Each entry has, in order:
1. **ID + headline** (`YYYYMMDD-[A]` sequential).
2. **Body**, written from the article body — never the headline. If the corpus has no usable body on a topic, the item is dropped.
3. **"Why an SLTT organization should care"** clause — mandatory, tied to this audience, framed as vendor accountability / procurement and foundational controls (CIS IG1), not developer-level fixes.
4. **Score** — the pipeline relevance score plus tier and the multipliers behind it. The score orders; it does not measure.
5. **Citations** — nested per entry, as live openable links (outlet, headline, date, URL). Never a link the reader cannot open.
6. **Flags** where needed (verification, review-note, attribution).

## 7. Content standards (locked)

- **The review surface is worked, not sampled.** Every candidate the staging
  document suggests for a section is read. A section written with far fewer
  entries than were suggested — 28 suggested, one written — is **a failure to
  work the section, not a thin week.** A legitimately thin section is stated
  plainly with the counts: *"28 suggested, 3 qualified, 25 off-target."* Never a
  silent one-item section, and never padded with weak items to fill space. The
  suggested counts are in the compliance report; the reading is the analyst's.
- **Requirements are consumed, never authored.** The staging document names the
  requirement each candidate answers and the elements it satisfied. The vox
  copies them; it does not derive them from the tier, the score, or memory. See
  the standing directive of the same name in `cti/mandate.md`.
- **Body, not headline.** Read the source. No body, no entry.
- **One event, one entry.** Fold same-event reports; place each event once, in the section matching its dominant value.
- **Recency.** Filter on publication date within the collection window. Out-of-window items are flagged, not silently dropped; they stay only with a fresh this-week hook (new exploitation, new victim, new KEV).
- **Serious-impact verification.** Independently verify serious impact claims (911/public-safety outages, casualties, service disruption, breach scope, attribution) against a primary or authoritative source before inclusion. If not clearly substantiated, attribute ("per the city's statement…") or soften — never state as fact. Verify the wording does not inflate the source ("affected 911 routing" ≠ "911 went down"). Re-check status if the item has aged since first drafted; "not confirmed" can go stale.
- **Attribution discipline.** Suspected ≠ confirmed. Represent the actual state of evidence — neither assert nor flatly deny where reporting indicates but officials have not confirmed.
- **Provider/product relevance.** A product-specific item is relevant only if the audience uses the affected product/provider.
- **Audience-portfolio filter.** Developer-only (e.g., package poisoning) and defense-industrial-only (e.g., CMMC) items are out of portfolio unless they reach SLTT through a vendor. Topicality ≠ relevance.
- **Plain language.** Acronyms spelled out on first use; technical mechanisms named but translated.
- **No cap on the review surface — trust the weights.** The review surface has NO fixed limit on items per section or overall. Every item that qualifies — by score or by the mandatory-surface rule below — appears, however many that is. If 20 high-weight items qualify, 20 surface. The count is an OUTPUT of the scoring and rules, never a target imposed on top of them.
- **Fix volume by tuning Sanctum, not by capping.** If the review surface is too large or too noisy, that is the signal to adjust the weights, the mandatory-surface vocabulary, or the exclusion operators — never to silently cap the output. Capping hides what the scoring did and destroys the feedback that tunes it. The uncapped surface IS the diagnostic.
- **Mandatory-surface rule (inclusion, not ranking).** An item is force-surfaced — never left in the drop list regardless of score — if it meets ANY of: **(M1)** a California/in-AOR entity is the SUBJECT of a cyberattack, breach, or disruption — the hard guarantee that every AOR incident surfaces; **(M2)** in-the-wild exploitation, a weaponized public PoC, or a KEV addition AND the affected product is in the SLTT-relevant technology vocabulary; **(M3)** a specific incident confirms an SLTT sector (water, K-12, local/tribal government, public safety) was targeted or impacted. M2 does NOT fire on CVSS/severity alone — an exploitation signal is required, which keeps it high-signal. Subject-of-incident logic and the recency gate apply, so passing national name-drops and years-old items do not trigger it. This decides surface-vs-drop only; the score still ORDERS everything, so convergence-wins ranking is fully intact.
- **SLTT-relevant technology vocabulary.** M2 keys on a maintained priority lexicon of software/tech that SLTT organizations run (e.g., GeoServer, WordPress, on-prem SharePoint, webmail platforms, RMM tools, common firewalls/VPNs, edge routers). This is the CTI analog of a domain word list — per-domain config, refined with the exclusion operator to trim noise, and grown as the discard log reveals gaps.
- **Interim (until the pipeline implements M1–M3):** the analyst applies the mandatory-surface rule by hand — reviewing the drop list for M1–M3 items and rescuing them, marking the low score so the ranking/relevance disagreement stays visible.
- **Restraint lives in the distributed product, applied by the team.** Restraint is the finished report's virtue, not the review surface's: after review, the cyber team narrows to a focused set for the non-technical audience. That editorial cut is a human judgment on the output, never an automated cap on what surfaces for review.
- **Sourcing.** Primary-source elevation; verify aggregator/roundup items against the primary advisory. Flag vendor-stat methodology limits.

## 8. Change control

This policy is the authority for the Vox. Format or standard changes originate as a P&D decision, are recorded in the Mandate/lessons log, and only then take effect. Mid-production requests that conflict with this spec are flagged against it, not silently adopted. This is the mechanism that prevents creep.
