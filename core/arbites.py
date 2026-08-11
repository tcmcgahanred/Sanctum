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

    surfaced = scored[:surface_n]
    dropped = scored[surface_n:]

    lines = []
    recency_note = f" · {stale_count} flagged STALE" if recency_on else " · recency gate OFF"
    lines.append(f"# {report_title}")
    lines.append(f"*Generated {datetime.now(timezone.utc).isoformat()} · domain {cfg['domain']} · "
                 f"window {window_days}d · {len(arts)} articles scored · "
                 f"top {len(surfaced)} surfaced, {len(dropped)} in drop list{recency_note}.*")
    lines.append("")
    lines.append("> Score ORDERS the queue; it does not decide. Read the reasoning, "
                 "check the drop list, override freely. Prefer false positives.")
    if recency_on:
        lines.append("> ⚠ STALE = published outside the cycle window. NOT dropped — "
                     "confirm a fresh this-week hook (new KEV/exploitation/victim) or cut it.")
    lines.append("")
    lines.append("---")
    lines.append("## CANDIDATES (top-scored — review these first)")
    lines.append("")
    for s, tier, reasons, a, is_stale in surfaced:
        mark = "⚠ STALE " if is_stale else ""
        lines.append(f"### {mark}[{s}] {a.get('title','(no title)')}")
        lines.append(f"- **Source:** {source_name(a.get('source',''))} · {a.get('published','?')}")
        lines.append(f"- **URL:** {a.get('url','')}")
        lines.append(f"- **Score reasoning:** {' | '.join(reasons)}")
        lines.append("")

    lines.append("---")
    lines.append("## DROP LIST (below cut — scan for anything mis-scored, rescue freely)")
    lines.append("")
    for s, tier, reasons, a, is_stale in dropped:
        mark = "⚠ STALE " if is_stale else ""
        lines.append(f"- {mark}[{s}] {a.get('title','(no title)')} "
                     f"— {source_name(a.get('source',''))} — {a.get('url','')}")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[{cfg['domain']}] {len(arts)} scored -> {len(surfaced)} candidates, "
          f"{len(dropped)} dropped -> {out_path}")


if __name__ == "__main__":
    main()
