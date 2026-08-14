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
import re
from datetime import datetime, timedelta, timezone
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
# Dedup at collection catches identical URLs and identical normalized titles.
# It cannot catch four outlets writing four different headlines about ONE
# incident. Those arrive as separate articles and — because scoring keys on
# terms, not events — they scatter: the vaguest headline can outrank the one
# that actually names the victim, which then dies below the cut.
#
# This groups them for the analyst. It changes NO score and removes NO item;
# it only nests near-duplicates under their highest-scoring sibling so
# "one event, one entry" is a glance instead of an archaeology exercise.
# A grouped item that sits below the cut is pulled up and marked, because
# rescuing the best-sourced copy is the whole point.
#
# Signal: shared RARE tokens. Two items sharing >= min_shared distinctive
# tokens (each appearing in <= max_df articles across the scored set) are
# almost always the same event. Common words ("ransomware", "california")
# have high document frequency and are ignored automatically, so the
# threshold does not need per-domain tuning of a stopword list.
# ------------------------------------------------------------------
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'-]*")


def _tokens(title, suffix_separators=(" - ", " | ", " — ")):
    """Distinctive tokens from a title: publisher suffix stripped, short words out."""
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

    `scored` is the sorted list of (score, tier, reasons, article, is_stale).
    Returns {head_index: [member_index, ...]} keyed on the highest-scoring
    member, plus a set of every index that belongs to some group.
    Pure analysis — the caller decides how to render it.
    """
    gcfg = settings.get("grouping", {}) or {}
    if not gcfg.get("enabled", True):
        return {}, set()
    min_shared = int(gcfg.get("min_shared_rare", 2))
    # "Rare" must SCALE with the corpus. A fixed count breaks on the exact case
    # this exists for: an incident covered by four outlets puts the victim's
    # name in four titles, and an absolute max_df of 3 then classifies the most
    # distinctive token in the set as too common to use.
    max_df_abs = int(gcfg.get("max_df_abs", 8))
    max_df_frac = float(gcfg.get("max_df_frac", 0.02))
    # Buckets bigger than this are not distinctive enough to be worth the
    # pairwise comparison; skipping them bounds the work on a large corpus.
    max_bucket = int(gcfg.get("max_bucket", 60))

    toks = [_tokens(rec[3].get("title", ""), suffix_separators) for rec in scored]

    df = {}
    for ts in toks:
        for w in ts:
            df[w] = df.get(w, 0) + 1
    max_df = max(max_df_abs, int(len(scored) * max_df_frac))
    rare = [{w for w in ts if df[w] <= max_df} for ts in toks]

    # Union-find over items sharing enough rare tokens.
    parent = list(range(len(scored)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[max(ri, rj)] = min(ri, rj)      # lower index = higher score

    # Invert to a token -> items map so we only compare plausible pairs.
    buckets = {}
    for i, rs in enumerate(rare):
        for w in rs:
            buckets.setdefault(w, []).append(i)
    for members in buckets.values():
        if len(members) < 2 or len(members) > max_bucket:
            continue
        for a_i in range(len(members)):
            for b_i in range(a_i + 1, len(members)):
                i, j = members[a_i], members[b_i]
                if find(i) == find(j):
                    continue
                if len(rare[i] & rare[j]) >= min_shared:
                    union(i, j)

    clusters = {}
    for i in range(len(scored)):
        clusters.setdefault(find(i), []).append(i)

    groups = {h: sorted(m) for h, m in clusters.items() if len(m) > 1}
    grouped = {i for m in groups.values() for i in m}
    return groups, grouped


def main():
    ap = argparse.ArgumentParser(description="Sanctum Arbites — domain-agnostic scorer")
    ap.add_argument("--domain", help="domain name (folder under repo, e.g. cti)")
    ap.add_argument("--pnd", help="explicit path to a pnd.md (overrides --domain)")
    ap.add_argument("--out", help="output path (default: <base_dir>/staging_candidates.md)")
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
    scored.sort(key=lambda x: x[0], reverse=True)

    surfaced_n = min(surface_n, len(scored))
    seps = tuple(cfg["manifest"].get("collection", {}).get(
        "suffix_separators", (" - ", " | ", " — ")))
    groups, grouped_idx = group_near_duplicates(scored, settings, seps)

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
                 f"{f' · {len(child_of)} event group(s)' if child_of else ''}.*")
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
        for k in kids:
            ks, _kt, kr, ka, k_stale = scored[k]
            kmark = "⚠ STALE " if k_stale else ""
            note = " · **rescued from drop list**" if k in rescued else ""
            lines.append(f"  - ⧉ {kmark}[{ks}] {ka.get('title','(no title)')} "
                         f"— {source_name(ka.get('source',''))}{note}")
            lines.append(f"    - {ka.get('url','')}")
            lines.append(f"    - *{' | '.join(kr)}*")
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


if __name__ == "__main__":
    main()
