#!/usr/bin/env python3
# Sanctum · Arbites (scorer engine) · v0.4 · domain-agnostic; history via git
"""
Arbites — pre-filter / scorer. Domain-agnostic: the scoring model (tiers,
keyword groups, multipliers, tier-assignment rules) comes entirely from a
domain's P&D (<domain>/pnd.md -> scoring). Run it as:

    python -m core.arbites --domain cti

Reads the rolling collection window from the corpus, scores every article via
core.rules.score_article against the domain's config, and writes a CANDIDATE
SHORTLIST + full DROP LIST to a single markdown file for the analyst.

DOCTRINE lives in the domain config + codex.md; the engine only executes it:
  - Prefer false positives to false negatives (encoded in the domain rules).
  - Wide cutoff; mandatory drop list; every item shows its reasoning.
  - The score ORDERS the queue; the analyst decides. Never an opaque gate.

RECENCY GATE (Codex Layer 4 — implemented): in_window() still gathers the corpus
by COLLECTED date, but each item is additionally checked by PUBLISH date against
the cycle window (config: scoring.settings.recency, default 7 days ending Monday
0900 America/Los_Angeles). Out-of-window items are flagged 'STALE — confirm
current hook' in their reasoning and marked in the output — never dropped, never
re-scored. Origin: a June FortiBleed advisory surfaced in the August edition.
"""

import argparse
import json
import math
import re
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from core.pnd import load_domain
from core.rules import score_article, compute_cycle_window, recency_tag


def in_window(art, cutoff):
    """Keep if collected within the window. On any parse doubt, KEEP (round up)."""
    c = art.get("collected", "")
    try:
        dt = datetime.fromisoformat(c)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= cutoff
    except Exception:
        return True


def load_window(corpus_root, window_days):
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    arts = []
    if not corpus_root.exists():
        return arts
    for day_dir in sorted(corpus_root.iterdir()):
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


# ------------------------------------------------------------------
# Near-duplicate GROUPING (display only — never merges, never drops)
#
# Collection dedup catches identical URLs and identical normalized titles.
# It cannot catch several outlets writing different headlines about ONE
# incident. Those arrive as separate articles and — because scoring keys on
# terms, not events — they SCATTER: the vaguest headline can outrank the one
# that actually names the victim, which then dies below the cut.
#
# This groups them for the analyst. It changes NO score and removes NO item;
# it nests near-duplicates under their highest-scoring sibling so that
# "one event, one entry" is a glance rather than an excavation. A grouped
# item sitting below the cut is pulled up and marked, because rescuing the
# best-sourced copy is the whole point.
#
# DESIGN NOTES (both learned the hard way on a live corpus, 2026-08-13):
#
#   1. NO TRANSITIVITY. An earlier version used union-find: A~B and B~C put
#      A, B and C in one group. Across 1,432 real articles that chained into
#      a single cluster of 520 items. Membership is therefore anchored to a
#      group's HEAD — an item joins a head it resembles directly, or starts
#      its own group. Chains cannot form.
#
#   2. RARITY IS THE WRONG SIGNAL. That same version called a token
#      "distinctive" if it appeared in few titles. But a heavily-covered
#      incident puts its distinctive token in MANY titles — that is what
#      heavy coverage means — so the strongest evidence was discarded as
#      too common. Similarity is now IDF-weighted Jaccard: shared words
#      count in proportion to how informative they are, and unshared
#      distinctive words (a different city, a different vendor) actively
#      push two items apart.
#
# Tuned against 29 hand-labelled titles from the production corpus:
# precision 1.00, recall 0.64 across a broad threshold plateau. Tuned for
# PRECISION deliberately — a missed grouping costs nothing beyond the status
# quo, while a false grouping hides an item under an unrelated head.
# ------------------------------------------------------------------
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'-]*")


def _tokens(title, suffix_separators=(" - ", " | ", " — ")):
    """Content tokens from a title: publisher suffix stripped, short words out."""
    t = str(title or "").strip()
    for sep in suffix_separators:
        if sep in t:
            parts = t.split(sep)
            if len(parts[-1]) <= 40:
                t = sep.join(parts[:-1])
    return {w for w in _TOKEN_RE.findall(t.lower()) if len(w) > 3}


def group_near_duplicates(scored, settings, suffix_separators=(" - ", " | ", " — ")):
    """
    Cluster scored items that look like the same event.

    `scored` is the score-sorted list of (score, tier, reasons, article, is_stale).
    Returns ({head_index: [member_index, ...]}, {every grouped index},
    dissolved_count). Pure analysis — the caller decides how to render it.
    """
    gcfg = settings.get("grouping", {}) or {}
    if not gcfg.get("enabled", True):
        return {}, set(), 0
    threshold = float(gcfg.get("similarity", 0.15))
    min_shared = int(gcfg.get("min_shared_tokens", 3))
    # Ratio alone is not enough. Formulaic feeds (vendor "Security Update
    # Guide" entries, advisory boilerplate) produce titles that are ~90%
    # identical while sharing almost no INFORMATION. Requiring a floor on the
    # summed IDF of the shared words means the overlap has to be meaningful,
    # not just large.
    min_evidence = float(gcfg.get("min_evidence", 8.0))
    # A single real event rarely draws more than a couple of dozen reports in
    # one collection window. A cluster far larger than that is the similarity
    # measure locking onto a TEMPLATE (formulaic vendor advisories) rather than
    # an event. Such groups are dissolved rather than shown: presenting 150
    # unrelated advisories as "one event" is worse than not grouping at all.
    max_group_size = int(gcfg.get("max_group_size", 25))

    toks = [_tokens(rec[3].get("title", ""), suffix_separators) for rec in scored]
    n = len(toks)
    if n < 2:
        return {}, set(), 0

    df = {}
    for ts in toks:
        for w in ts:
            df[w] = df.get(w, 0) + 1
    idf = {w: math.log(n / (1 + c)) for w, c in df.items()}

    def similarity(a, b):
        """IDF-weighted Jaccard, gated on absolute shared information.

        Returns 0.0 unless the shared words carry at least `min_evidence`
        of summed IDF — boilerplate overlap scores high as a ratio and low
        as evidence, and only the second one means 'same event'.
        """
        inter = sum(idf[w] for w in a & b)
        if inter < min_evidence:
            return 0.0
        union = sum(idf[w] for w in a | b)
        return inter / union if union else 0.0

    # Inverted index over heads so each item only meets plausible candidates.
    heads = []                       # head indices, in score order
    head_by_token = {}               # token -> [head index, ...]
    members = {}

    for i in range(n):
        ti = toks[i]
        if not ti:
            heads.append(i)
            members[i] = [i]
            continue

        candidates = {}
        for w in ti:
            for h in head_by_token.get(w, ()):
                candidates[h] = candidates.get(h, 0) + 1

        best_head, best_sim = None, 0.0
        for h, shared in candidates.items():
            if shared < min_shared:
                continue
            sim = similarity(ti, toks[h])
            if sim >= threshold and sim > best_sim:
                best_head, best_sim = h, sim

        if best_head is None:
            heads.append(i)
            members[i] = [i]
            for w in ti:
                head_by_token.setdefault(w, []).append(i)
        else:
            members[best_head].append(i)

    groups, dissolved = {}, 0
    for h, m in members.items():
        if len(m) <= 1:
            continue
        if len(m) > max_group_size:
            dissolved += 1          # template match, not an event — leave items ungrouped
            continue
        groups[h] = m
    grouped = {i for m in groups.values() for i in m}
    return groups, grouped, dissolved


# ------------------------------------------------------------------
# Staging hand-off
#
# The staging document is written to the collector host, which is a headless,
# outbound-only box. The analyst edits on a different machine. Without a push
# the document has to be copied by hand every cycle, which is exactly the kind
# of manual step that gets skipped on a busy Monday.
#
# Acolyte already pushes the corpus this way; this is the same mechanism for
# the one artifact a human actually opens.
#
# The remote filename is DATED, not fixed. A fixed name would be overwritten by
# the next daily run — including on top of a document the analyst had already
# started editing in a synced folder. Dating it means each cycle lands beside
# the last and nothing clobbers work in progress.
# ------------------------------------------------------------------
def staging_target(manifest, today):
    """
    Resolve (remote_base, filename) for the staging push, or (None, None) if
    the domain hasn't configured one. Pure — no side effects, so the naming is
    testable without touching the network.

    Config (in the domain manifest):
        staging:
          backend: rclone
          rclone_remote: <remote>:<path>
          filename: "STAGING_{date}.md"     # {date} -> YYYYMMDD
    """
    st = (manifest or {}).get("staging", {}) or {}
    if st.get("backend") != "rclone":
        return None, None
    remote = st.get("rclone_remote")
    if not remote:
        return None, None
    template = str(st.get("filename", "staging_{date}.md"))
    return remote, template.replace("{date}", today.strftime("%Y%m%d"))


def push_staging(manifest, out_path, today, log=print):
    """Copy the staging document to the configured remote under a dated name."""
    remote, name = staging_target(manifest, today)
    if not remote:
        return None
    dest = f"{remote.rstrip('/')}/{name}"
    try:
        subprocess.run(["rclone", "copyto", str(out_path), dest], check=True)
        log(f"staging pushed -> {dest}")
        return dest
    except Exception as e:
        # Same posture as the corpus push: warn, never fail the cycle. The
        # document is already written locally; a failed copy is an
        # inconvenience, not a lost cycle.
        log(f"WARNING: staging push failed ({e}). Local copy is at {out_path}")
        return None


def main():
    ap = argparse.ArgumentParser(description="Sanctum Arbites — domain-agnostic scorer")
    ap.add_argument("--domain", help="domain name (folder under repo, e.g. cti)")
    ap.add_argument("--pnd", help="explicit path to a pnd.md (overrides --domain)")
    ap.add_argument("--out", help="output path (default: <base_dir>/staging_candidates.md)")
    ap.add_argument("--no-push", action="store_true", help="skip the staging push")
    args = ap.parse_args()

    cfg = load_domain(domain=args.domain, pnd_path=args.pnd)
    scoring = cfg["scoring"]
    settings = scoring.get("settings", {})
    production = cfg.get("production", {})

    window_days = int(cfg["manifest"].get("collection", {}).get("window_days",
                      settings.get("window_days", 7)))
    surface_n = int(settings.get("surface_n", 55))
    out_path = Path(args.out) if args.out else cfg["staging_out"]
    report_title = production.get("report_title", f"{cfg['domain'].upper()} — Pre-Filtered Candidate Queue")

    # Recency gate (Codex Layer 4) — flag stale-by-publish-date, never drop.
    rec_cfg = settings.get("recency", {}) or {}
    recency_on = bool(rec_cfg.get("enabled", False))
    window_start = None
    if recency_on:
        window_start, cutoff = compute_cycle_window(datetime.now(timezone.utc), settings)

    arts = load_window(cfg["corpus_dir"], window_days)
    scored = []
    stale_count = 0
    for a in arts:
        s, tier, reasons = score_article(a, scoring)
        is_stale = False
        if recency_on:
            tag = recency_tag(a.get("published", ""), window_start)
            if tag:
                reasons.append(tag)
                is_stale = True
                stale_count += 1
        scored.append((s, tier, reasons, a, is_stale))
    # Deterministic order: score desc, then title, then URL. Ties are common
    # (many items share a tier weight with no multipliers) and grouping anchors
    # on whichever member is seen first — so without a stable tiebreak the same
    # corpus could produce different group heads run to run.
    scored.sort(key=lambda x: (-x[0], str(x[3].get("title", "")), str(x[3].get("url", ""))))

    surfaced_n = min(surface_n, len(scored))
    seps = tuple(cfg["manifest"].get("collection", {}).get(
        "suffix_separators", (" - ", " | ", " — ")))
    groups, grouped_idx, dissolved_groups = group_near_duplicates(scored, settings, seps)
    # Hard bound on how much of the report one group may occupy. Grouping is a
    # heuristic; this caps the blast radius if it ever over-clusters again.
    max_group_display = int((settings.get("grouping", {}) or {}).get("max_group_display", 12))

    # A group is anchored by its highest-scoring member. If that anchor is
    # surfaced, every sibling rides along — including ones below the cut.
    # Nothing is removed from the drop list count by grouping alone.
    child_of = {}
    rescued = set()
    for head, members in groups.items():
        if head >= surfaced_n:
            continue                     # whole group is below the cut; leave it there
        kids = [m for m in members if m != head]
        child_of[head] = kids
        rescued.update(m for m in kids if m >= surfaced_n)

    surfaced = scored[:surfaced_n]
    dropped = scored[surfaced_n:]

    lines = []
    recency_note = f" · {stale_count} flagged STALE" if recency_on else " · recency gate OFF"
    lines.append(f"# {report_title}")
    lines.append(f"*Generated {datetime.now(timezone.utc).isoformat()} · domain {cfg['domain']} · "
                 f"window {window_days}d · {len(arts)} articles scored · "
                 f"top {len(surfaced)} surfaced, {len(dropped)} in drop list{recency_note}"
                 f"{f' · {len(child_of)} event group(s)' if child_of else ''}"
                 f"{f' · {dissolved_groups} oversized cluster(s) dissolved' if dissolved_groups else ''}.*")
    lines.append("")
    lines.append("> Score ORDERS the queue; it does not decide. Read the reasoning, "
                 "check the drop list, override freely. Prefer false positives.")
    if recency_on:
        lines.append("> ⚠ STALE = published outside the cycle window. NOT dropped — "
                     "confirm a fresh this-week hook (new KEV/exploitation/victim) or cut it.")
    lines.append("")
    if child_of:
        lines.append("> ⧉ = same event, reported separately. Grouped for review only — "
                     "nothing merged, nothing dropped. Apply 'one event, one entry': "
                     "pick the best-sourced copy, fold the rest in.")
        lines.append("")
    lines.append("---")
    lines.append("## CANDIDATES (top-scored — review these first)")
    lines.append("")
    for idx, (s, tier, reasons, a, is_stale) in enumerate(surfaced):
        if idx in grouped_idx and idx not in child_of:
            continue                     # a sibling; printed under its group head
        mark = "⚠ STALE " if is_stale else ""
        kids = child_of.get(idx, [])
        tag = f" ⧉ {len(kids) + 1} reports" if kids else ""
        lines.append(f"### {mark}[{s}] {a.get('title','(no title)')}{tag}")
        lines.append(f"- **Source:** {source_name(a.get('source',''))} · {a.get('published','?')}")
        lines.append(f"- **URL:** {a.get('url','')}")
        lines.append(f"- **Score reasoning:** {' | '.join(reasons)}")
        shown = kids[:max_group_display]
        hidden = len(kids) - len(shown)
        for k in shown:
            ks, _kt, kr, ka, k_stale = scored[k]
            kmark = "⚠ STALE " if k_stale else ""
            note = " · **rescued from drop list**" if k in rescued else ""
            lines.append(f"  - ⧉ {kmark}[{ks}] {ka.get('title','(no title)')} "
                         f"— {source_name(ka.get('source',''))}{note}")
            lines.append(f"    - {ka.get('url','')}")
            lines.append(f"    - *{' | '.join(kr)}*")
        if hidden:
            lines.append(f"  - ⧉ *…and {hidden} more report(s) of this event — "
                         f"all remain listed in the drop list below.*")
        lines.append("")

    lines.append("---")
    lines.append("## DROP LIST (below cut — scan for anything mis-scored, rescue freely)")
    lines.append("")
    for off, (s, tier, reasons, a, is_stale) in enumerate(dropped):
        idx = surfaced_n + off
        mark = "⚠ STALE " if is_stale else ""
        note = "  ⧉ *(also shown grouped above)*" if idx in rescued else ""
        lines.append(f"- {mark}[{s}] {a.get('title','(no title)')} "
                     f"— {source_name(a.get('source',''))} — {a.get('url','')}{note}")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[{cfg['domain']}] {len(arts)} scored -> {len(surfaced)} candidates, "
          f"{len(dropped)} dropped -> {out_path}")

    if not args.no_push:
        push_staging(cfg["manifest"], out_path, date.today(),
                     log=lambda m: print(f"[{cfg['domain']}] {m}"))


if __name__ == "__main__":
    main()
