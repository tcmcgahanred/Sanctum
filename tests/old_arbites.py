#!/opt/ravenor/venv/bin/python3
# Sanctum · Arbites · v0.4 (starting anchor; history via git)
"""
Sanctum · Arbites — WCTI pre-filter / scorer.

Reads the rolling collection window from the corpus, scores every article
against the IR model (tier weight x elevation multipliers), and writes a
CANDIDATE SHORTLIST plus a full DROP LIST to a single markdown file the
analyst opens for synthesis.

DOCTRINE (frozen copy; the live rules now live in the domain config):
  - Prefer false positives to false negatives. Bias the cut toward KEEPING.
  - Strict on sensors, generous on items.
  - Wide cutoff (~50-60 surfaced). Round UP on uncertainty.
  - Mandatory drop list — "dropped" never means "invisible."
  - Every scored item shows its reasoning (tier + which signals fired).
  - The score ORDERS the queue; the analyst decides. Never an opaque gate.

  *** THIS IS A KEYWORD PRE-SCORER, NOT A JUDGMENT ENGINE. ***
  It uses coarse keyword matching to assign a provisional tier + signals.
  It WILL mis-tag some items. That is expected and acceptable BECAUSE the
  cut is wide and the drop list is visible — the analyst catches errors by
  reading the reasoning. Do not tighten this into a gate.

INTEGRATION / WHAT TO VERIFY ON THE CURRENT HOST:
  - CORPUS_ROOT and the dated-folder layout (corpus/YYYY-MM-DD/*.json).
  - The keyword lists below are STARTERS — tune them from real misses.
  - Runs AFTER collection, BEFORE synthesis. Wire to a systemd timer or run
    by hand. Output goes to OUT_PATH; analyst opens that file.

BACKLOG (Codex Layer 4 recency gate — NOT yet implemented here):
  in_window() below windows on the COLLECTED date (rolling WINDOW_DAYS).
  The recency gate wants windowing on the item's PUBLISH date vs. the cycle
  window (the 7 days ending Monday 0900), flagging out-of-window items as
  "STALE — confirm current hook" rather than dropping them. Add when built.
"""

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# ------------------------------------------------------------------
# CONFIG — verify these paths on the current host
# ------------------------------------------------------------------
BASE        = Path("/opt/ravenor")
CORPUS_ROOT = BASE / "corpus"                 # dated subfolders: YYYY-MM-DD/
OUT_PATH    = BASE / "staging_candidates.md"  # analyst opens this
WINDOW_DAYS = 7                               # rolling collection window
SURFACE_N   = 55                              # wide cutoff (doctrine: ~50-60)

# ------------------------------------------------------------------
# SCORING — mirrors the IR model. Keep in sync with the IR artifact.
# Tier weights (highest qualifying tier only; tiers do NOT stack).
# ------------------------------------------------------------------
TIER_WEIGHTS = {1: 8.0, 2: 4.0, 3: 2.0, 4: 1.0}

# Elevation multipliers (absent = 1.0 neutral; present multiplies up).
MULT_KEV          = 1.5   # actively exploited / CISA KEV
MULT_LOWMATURITY  = 1.5   # tech common in low-maturity SLTT orgs
MULT_SUPPLYCHAIN  = 1.3   # supply-chain / procurement angle
MULT_RANSOM_CI    = 1.3   # ransomware vs public-sector / CI

# ------------------------------------------------------------------
# KEYWORD SIGNALS — STARTER LISTS. Tune from real misses over editions.
# Lowercased substring matches against title+text.
# ------------------------------------------------------------------
# Tier 1: California-direct. High bar for confidence, but per doctrine we
# round UP — if CA + an org/incident word co-occur, treat as tier 1.
CA_TERMS = [
    "california", "californian", " calif ", "sacramento", "fresno",
    "modesto", "stockton", "bakersfield", "cal oes", "cal-csic", "ccic",
    "caltrans", "csu ", "uc ", "calmatters",
    # AOR counties (34) — county name + "county"
    "alpine county", "amador county", "butte county", "calaveras county",
    "colusa county", "el dorado county", "fresno county", "glenn county",
    "inyo county", "kern county", "kings county", "lake county",
    "lassen county", "madera county", "mariposa county", "mendocino county",
    "merced county", "modoc county", "mono county", "nevada county",
    "placer county", "plumas county", "sacramento county", "san joaquin county",
    "shasta county", "sierra county", "stanislaus county", "sutter county",
    "tehama county", "trinity county", "tulare county", "tuolumne county",
    "yolo county", "yuba county",
]
INCIDENT_TERMS = [
    "breach", "ransomware", "cyberattack", "cyber attack", "hacked",
    "data breach", "compromise", "exfiltrat", "extortion", "data leak",
    "data stolen", "records stolen", "security incident",
]

# Tier 2: SLTT sector targeting (anywhere).
SECTOR_TERMS = [
    "water", "wastewater", "utility", "utilities", "school district",
    "k-12", "k12", "higher ed", "university", "college", "municipal",
    "city government", "county government", "local government", "tribal",
    "public sector", "election", "registrar of voters", "transit",
    "special district", "sheriff", "police department", "court",
]

# Tier 3 signal: SLTT-common / low-maturity tech.
LOWMATURITY_TECH = [
    "fortinet", "fortigate", "sonicwall", "mikrotik", "routeros", "openwrt",
    "sharepoint", "exchange server", "vpn", "rdp", "n-able", "n-central",
    "kaseya", "connectwise", "screenconnect", "wordpress", "plc",
    "programmable logic controller", "scada", "ics", "operational technology",
    "cisco", "netgear", "tp-link", "router", "firewall",
]

# Elevation signals.
KEV_TERMS = [
    "cisa kev", "known exploited", "actively exploited", "exploited in the wild",
    "in-the-wild", "added to its known exploited", "kev catalog",
    "zero-day", "0-day", "under active exploitation",
]
SUPPLYCHAIN_TERMS = [
    "supply chain", "supply-chain", "npm", "pypi", "package", "dependency",
    "third-party", "vendor compromise", "msp", "managed service provider",
    "rmm", "procurement", "software supply",
]
RANSOM_TERMS = ["ransomware", "ransom", "extortion", "encrypt", "leak site", "double extortion"]
CI_TERMS = [
    "critical infrastructure", "water", "wastewater", "power", "grid",
    "hospital", "healthcare", "public sector", "government", "municipal",
    "school", "utility",
]


def _hit(text, terms):
    """
    Return the first matching term, or None.
    Uses word-boundary matching for SHORT/ambiguous terms (<=4 chars or
    flagged) to avoid substring collisions (e.g. 'ics' inside 'physics',
    'hack' inside culinary 'hack'). Longer distinctive terms use fast
    substring matching.
    """
    for t in terms:
        t = t.strip()
        if len(t) <= 4 or t in _WORD_BOUNDARY_TERMS:
            # \b word boundary; escape in case of regex chars
            if re.search(r"\b" + re.escape(t) + r"\b", text):
                return t
        else:
            if t in text:
                return t
    return None


# Terms that MUST match on word boundaries even if longer than 4 chars,
# because they collide as substrings inside common words.
_WORD_BOUNDARY_TERMS = {"hack", "ics", "scada", "grid", "leak", "ransom", "court", "uc", "csu", "cisco", "war"}


def score_article(art):
    """
    Assign a provisional tier + elevation signals from keyword matches.
    Returns (score, tier, reasons:list[str]).
    Doctrine: round UP on uncertainty — ambiguity resolves toward visibility.
    """
    title = str(art.get("title", "")).strip()
    title_l = title.lower()
    text_l = str(art.get("text", "")).lower()
    blob = (title + "  " + str(art.get("text", ""))).lower()
    reasons = []

    # Empty-title guard: feed artifacts with no title are data-quality
    # problems, not high-value items. Flag and floor them so they land in
    # the drop list for the analyst to notice, not silently ranked high.
    if not title:
        return 0.5, 4, ["FLAG: empty title (feed artifact — verify source)"]

    ca = _hit(blob, CA_TERMS)
    incident = _hit(blob, INCIDENT_TERMS)
    sector = _hit(blob, SECTOR_TERMS)
    lowmat = _hit(blob, LOWMATURITY_TECH)
    kev = _hit(blob, KEV_TERMS)

    # --- Tier 1 requires CA to be the SUBJECT *of an incident*. ---
    # Not enough for California to appear in the title (e.g. "California town").
    # Requires: (CA in title AND an incident word present anywhere), OR
    # (CA term and incident word in close proximity in the body).
    # This protects genuine AOR incidents from both national name-drops AND
    # generic California human-interest stories.
    ca_in_title = _hit(title_l, CA_TERMS)
    ca_is_subject = False
    ca_subject_reason = ""
    if ca_in_title and incident:
        ca_is_subject = True
        ca_subject_reason = f"CA in title ('{ca_in_title}') + incident ('{incident}')"
    elif ca and incident:
        # proximity check in the body: CA term within 120 chars of an incident term
        for ct in CA_TERMS:
            idx = text_l.find(ct)
            if idx == -1:
                continue
            window = text_l[max(0, idx - 120): idx + 120]
            near = _hit(window, INCIDENT_TERMS)
            if near:
                ca_is_subject = True
                ca_subject_reason = f"CA~incident proximity ('{ct}'~'{near}')"
                break

    # --- Tier assignment (highest qualifying only) ---
    if ca_is_subject:
        tier = 1
        reasons.append(f"T1 CA-direct ({ca_subject_reason})")
    elif sector:
        tier = 2
        reasons.append(f"T2 SLTT-sector ('{sector}')")
    elif kev and lowmat:
        tier = 3
        reasons.append(f"T3 KEV in SLTT-tech (kev:'{kev}' + tech:'{lowmat}')")
    else:
        tier = 4
        reasons.append("T4 broad/national")
        # Note if CA is mentioned but not the subject — useful analyst context
        if ca:
            reasons.append(f"(CA mentioned but not subject: '{ca}')")

    score = TIER_WEIGHTS[tier]

    # --- Elevation multipliers (stack; absent = neutral) ---
    if kev:
        score *= MULT_KEV
        reasons.append(f"x1.5 KEV ('{kev}')")
    if lowmat:
        score *= MULT_LOWMATURITY
        reasons.append(f"x1.5 low-maturity tech ('{lowmat}')")
    if _hit(blob, SUPPLYCHAIN_TERMS):
        score *= MULT_SUPPLYCHAIN
        reasons.append(f"x1.3 supply-chain ('{_hit(blob, SUPPLYCHAIN_TERMS)}')")
    if _hit(blob, RANSOM_TERMS) and _hit(blob, CI_TERMS):
        score *= MULT_RANSOM_CI
        reasons.append("x1.3 ransomware vs public-sector/CI")

    return round(score, 2), tier, reasons



def in_window(art, cutoff):
    """Keep if collected within the window. On any parse doubt, KEEP (round up)."""
    c = art.get("collected", "")
    try:
        dt = datetime.fromisoformat(c)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= cutoff
    except Exception:
        return True  # doctrine: uncertainty -> visibility


def load_window():
    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    arts = []
    if not CORPUS_ROOT.exists():
        return arts
    for day_dir in sorted(CORPUS_ROOT.iterdir()):
        if not day_dir.is_dir():
            continue
        for jf in day_dir.glob("*.json"):
            try:
                art = json.loads(jf.read_text(encoding="utf-8"))
            except Exception:
                continue
            if in_window(art, cutoff):
                arts.append(art)
    return arts


def source_name(url):
    return re.sub(r"^https?://(www\.)?", "", str(url)).split("/")[0]


def main():
    arts = load_window()
    scored = []
    for a in arts:
        s, tier, reasons = score_article(a)
        scored.append((s, tier, reasons, a))
    scored.sort(key=lambda x: x[0], reverse=True)

    surfaced = scored[:SURFACE_N]
    dropped = scored[SURFACE_N:]

    lines = []
    lines.append("# WCTI — Pre-Filtered Candidate Queue")
    lines.append(f"*Generated {datetime.now(timezone.utc).isoformat()} · "
                 f"window {WINDOW_DAYS}d · {len(arts)} articles scored · "
                 f"top {len(surfaced)} surfaced, {len(dropped)} in drop list.*")
    lines.append("")
    lines.append("> Score ORDERS the queue; it does not decide. Read the reasoning, "
                 "check the drop list, override freely. Prefer false positives.")
    lines.append("")
    lines.append("---")
    lines.append("## CANDIDATES (top-scored — review these first)")
    lines.append("")
    for s, tier, reasons, a in surfaced:
        lines.append(f"### [{s}] {a.get('title','(no title)')}")
        lines.append(f"- **Source:** {source_name(a.get('source',''))} · "
                     f"{a.get('published','?')}")
        lines.append(f"- **URL:** {a.get('url','')}")
        lines.append(f"- **Score reasoning:** {' | '.join(reasons)}")
        lines.append("")

    lines.append("---")
    lines.append("## DROP LIST (below cut — scan for anything mis-scored, rescue freely)")
    lines.append("")
    for s, tier, reasons, a in dropped:
        lines.append(f"- [{s}] {a.get('title','(no title)')} "
                     f"— {source_name(a.get('source',''))} — {a.get('url','')}")
    lines.append("")

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(arts)} scored -> {len(surfaced)} candidates, "
          f"{len(dropped)} dropped -> {OUT_PATH}")


if __name__ == "__main__":
    main()
