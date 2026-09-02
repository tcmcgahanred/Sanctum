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

DOCTRINE lives in the domain config; the engine only executes it:
  - Prefer false positives to false negatives (encoded in the domain rules).
  - Wide cutoff; mandatory drop list; every item shows its reasoning.
  - The score ORDERS the queue; the analyst decides. Never an opaque gate.

RECENCY GATE (Codex Layer 4 — implemented): in_window() still gathers the corpus
by COLLECTED date, but each item is additionally checked by PUBLISH date against
the cycle window (config: scoring.settings.recency, default 7 days ending the
declared cutoff_weekday at cutoff_time in the declared timezone; CTI runs
Wednesday 0400 America/Los_Angeles). Out-of-window items are flagged 'STALE — confirm
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
from core.fetch import nobody_reason
from core.rules import (score_article, matched_evidence, tier_requirement,
                        satisfied_elements,
                        compute_cycle_window, recency_tag,
                        make_matcher, _eval_atom, _scopes)


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

    `scored` is the score-sorted list of
    (score, tier, reasons, article, is_stale, surfaced).
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


def body_words(art):
    """Word count of the extracted body. Title deliberately excluded."""
    return len(str(art.get("text", "")).split())


def annotate(art, ann, groups, matcher):
    """
    Return (no_body, section, low_confidence) for one article.

    ADVISORY ONLY. Neither value touches the score, the tier, the ordering or
    the surface-vs-drop decision. They exist so two standards the analyst was
    expected to remember — "written from the body, never the headline" and
    "every section is populated or deliberately empty" — become visible in the
    document instead of being carried in someone's head.

    no_body        the extracted text is shorter than the configured floor, so
                   there is nothing to write an entry FROM. Vox Policy §6.2.
    section        a SUGGESTION, matched from an ordered list of rules in the
                   domain config. First match wins. The analyst confirms or
                   overrides; nothing downstream reads it.
    low_confidence the suggestion came from the fallback rather than a positive
                   match, or the item has no usable body — a section guessed
                   from a headline alone is a guess, and says so.
    """
    if not ann:
        return False, None, False
    floor = int(ann.get("min_body_words", 0) or 0)
    nb = floor > 0 and body_words(art) < floor

    section, low = None, False
    _t, scopes, text_l = _scopes(art)
    for entry in ann.get("sections", []) or []:
        when = entry.get("when", "always")
        if _eval_atom(when, groups, matcher, scopes, text_l):
            section = entry.get("name")
            # A bare `always` is the catch-all, not a finding about the item.
            low = (isinstance(when, str) and when.strip().lower() == "always")
            break
    if nb:
        low = True          # headline-only: any section is inference
    return nb, section, low


def compliance_path(out_path):
    """Sibling of the staging document, same stem, COMPLIANCE instead."""
    stem = out_path.stem
    stem = stem.replace("staging_candidates", "compliance_report")
    if stem == out_path.stem:
        stem = stem + "_compliance"
    return out_path.with_name(stem + out_path.suffix)


def push_compliance(manifest, out_path, today, log=print):
    """Push the compliance report beside the staging document it belongs to."""
    remote, name = staging_target(manifest, today)
    if not remote:
        return None
    name = name.replace("STAGING", "COMPLIANCE")
    if "COMPLIANCE" not in name:
        root, dot, ext = name.rpartition(".")
        name = f"{root}_COMPLIANCE{dot}{ext}" if dot else name + "_COMPLIANCE"
    dest = f"{remote.rstrip('/')}/{name}"
    try:
        subprocess.run(["rclone", "copyto", str(out_path), dest], check=True)
        log(f"compliance report pushed -> {dest}")
        return dest
    except Exception as e:
        log(f"WARNING: compliance push failed ({e}). Local copy is at {out_path}")
        return None


def build_compliance_report(cfg, ann_cfg, stats, nobody_items, section_counts):
    """
    The Vox Policy §8 production gate, pre-filled with what the pipeline knows.

    WHAT THIS IS AND IS NOT. The pipeline can count candidates, events, missing
    bodies and section coverage. It cannot know how many bodies a person read,
    what they wrote up, or why they excluded something. **Those fields are left
    blank on purpose.** A blank the analyst must fill is the point of a gate; a
    number the machine invented would defeat it.

    Nothing here passes or fails a cycle. It makes omissions visible before the
    edition ships, which is what §8 asks for.
    """
    L = []
    prod = cfg.get("production", {}) or {}
    # Take the product name off the front of the staging title so the report
    # reads "WCTI — Compliance Report", not "WCTI — Staging Document — ...".
    title = str(prod.get("report_title", cfg["domain"].upper()))
    L.append(f"# {title.split('—')[0].strip() or cfg['domain'].upper()} — Compliance Report")
    L.append("")
    L.append(f"*Generated {datetime.now(timezone.utc).isoformat()} · domain {cfg['domain']}.*")
    L.append("")
    L.append("> **This is a required artifact, not an optional one.** It is what the "
             "Wednesday review checks the edition against. A failed check is fixed or "
             "carried as an explicit note — never silently passed.")
    L.append("")
    L.append("> Fields marked **ANALYST** are deliberately blank. The pipeline cannot "
             "know how many bodies were read or why something was excluded, and a "
             "number it invented would defeat the purpose of the gate.")
    L.append("")
    L.append("## Queue coverage")
    L.append("")
    L.append("| Measure | Value | Filled by |")
    L.append("|---|---|---|")
    for label, value in stats:
        L.append(f"| {label} | {value} | pipeline |")
    for label in ("Bodies read", "Entries written", "Excluded with reason"):
        L.append(f"| {label} |  | **ANALYST** |")
    L.append("| Drop list reviewed | ☐ | **ANALYST** |")
    L.append("")
    L.append("## Section coverage")
    L.append("")
    L.append("| Section | Suggested candidates | In edition | Note |")
    L.append("|---|---|---|---|")
    declared = prod.get("sections", []) or []
    for name in declared:
        n = section_counts.get(name)
        if n is None:
            L.append(f"| {name} | — *not a candidate destination* |  |  |")
        else:
            L.append(f"| {name} | {n} |  | {'**zero candidates — say so explicitly**' if n == 0 else ''} |")
    L.append("")
    L.append("> Every declared section appears in the edition. An empty one is marked "
             "\"none this cycle\" — never omitted, because an omitted section is "
             "indistinguishable from an oversight.")
    L.append("")
    L.append("## Surfaced candidates with no usable body")
    L.append("")
    if not nobody_items:
        L.append("*None. Every surfaced candidate has extractable text.*")
    else:
        L.append("These have too little extracted text to write an entry FROM. Fetch the "
                 "body or drop the item — Vox Policy §6.2 forbids writing one up from its "
                 "headline.")
        L.append("")
        # Split by cause. A blocked publisher is an engineering ticket; a short
        # article is an editorial judgement. Listing them together taught the
        # reader to treat both as normal attrition, which is how four broken
        # sensors stayed invisible.
        sensor_faults = [i for i in nobody_items
                         if i[4] in ("blocked", "challenge", "js_shell", "error")]
        if sensor_faults:
            hosts = {}
            for i in sensor_faults:
                hosts[source_name(i[2])] = hosts.get(source_name(i[2]), 0) + 1
            L.append(f"> ⚠ **{len(sensor_faults)} of these are collection failures, not "
                     f"thin articles** — "
                     + ", ".join(f"{h} ({n})" for h, n in sorted(hosts.items()))
                     + ". That is a sensor to repair, not an item to cut.")
            L.append("")
        for score, title, url, reason, _status in nobody_items:
            L.append(f"- [{score}] {title}")
            L.append(f"  - {url}")
            if reason:
                L.append(f"  - *{reason}*")
    L.append("")
    L.append("## Edition-level checks")
    L.append("")
    checklist = ann_cfg.get("compliance_checklist", []) or []
    if not checklist:
        L.append("*No checklist configured for this domain.*")
    for item in checklist:
        L.append(f"- ☐ {item}")
    L.append("")
    return "\n".join(L)


def force_surface_match(art, force_rules, groups, matcher):
    """
    Name of the first force-surface rule this article matches, or None.

    Force-surface is INCLUSION, not ranking (Vox Policy §7). A match guarantees
    the item reaches the surface whatever it scored; the score still orders
    everything, so a forced low-score item lands at the bottom of the surface
    with its disagreement on show. That visible disagreement is the tuning
    signal — an item silently lost in the drop list is just a miss.

    IMPORTANT LIMIT: this can only fire on vocabulary the domain has already
    declared. A rule saying "an in-AOR entity in an incident" cannot surface an
    incident described with a word missing from the incident group. The
    guarantee is bounded by the word lists, not by the rule.

    A malformed rule is skipped rather than allowed to take down the cycle —
    the run must always produce a document.
    """
    if not force_rules:
        return None
    _, scopes, text_l = _scopes(art)
    for rule in force_rules:
        try:
            if _eval_atom(rule.get("when", {}), groups, matcher, scopes, text_l):
                return rule.get("name", "force-surface")
        except (KeyError, ValueError):
            continue
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
    # SURFACE-VS-DROP — a score threshold, never a count.
    #
    # This used to be `surface_n: 55` — the top 55 by rank surfaced, the rest
    # dropped. A rank cut is a cap, and a cap is forbidden by policy: it hides
    # what the scoring did and destroys the feedback that tunes it. Worse, it
    # made the force-surface guarantee below impossible — an in-AOR incident
    # ranked 56th was in the drop list no matter what rule it satisfied.
    #
    # Now: an item surfaces if it clears `surface_min_score` OR any
    # `force_surface` rule matches it. The count is an OUTPUT, not a target.
    # If the surface is too big, tune the weights or the rules — do not cap it.
    min_score = settings.get("surface_min_score")
    min_score = float(min_score) if min_score is not None else None
    out_path = Path(args.out) if args.out else cfg["staging_out"]
    report_title = production.get("report_title", f"{cfg['domain'].upper()} — Pre-Filtered Candidate Queue")

    # Recency gate (Codex Layer 4) — flag stale-by-publish-date, never drop.
    rec_cfg = settings.get("recency", {}) or {}
    recency_on = bool(rec_cfg.get("enabled", False))
    window_start = None
    if recency_on:
        window_start, cutoff = compute_cycle_window(datetime.now(timezone.utc), settings)

    # FORCE-SURFACE RULES — inclusion, never ranking.
    #
    # A domain may declare rules that guarantee an item reaches the surface
    # regardless of its score. They use the same atom grammar as tiers and
    # multipliers, so the engine learns no domain knowledge: the domain says
    # what must never be missed, the engine only honours it.
    #
    # Score still orders everything. A forced item with a low score sits at the
    # bottom of the surfaced list, marked, rather than being lost in the drop
    # list — which is the whole point: a ranking/relevance disagreement you can
    # see is a tuning signal, one you cannot see is a miss.
    force_rules = scoring.get("force_surface", []) or []
    fs_matcher = make_matcher(scoring.get("word_boundary_terms"))
    fs_groups = scoring["groups"]

    def forced_by(art):
        return force_surface_match(art, force_rules, fs_groups, fs_matcher)

    # Staging annotations (Vox Policy §5 and §6.2). Absent from the config =
    # no annotations and no behaviour change, so a domain that has not defined
    # them is unaffected.
    annotations = production.get("staging_annotations", {}) or {}
    ann_by_id = {}

    arts = load_window(cfg["corpus_dir"], window_days)
    scored = []
    stale_count = 0
    forced_count = 0
    for a in arts:
        s, tier, reasons = score_article(a, scoring)
        is_stale = False
        if recency_on:
            tag = recency_tag(a.get("published", ""), window_start)
            if tag:
                reasons.append(tag)
                is_stale = True
                stale_count += 1
        hit = forced_by(a)
        qualifies = (min_score is None) or (s >= min_score)
        if hit and not qualifies:
            reasons.append(f"FORCE-SURFACED: {hit} (score {s} is below the cut — "
                           f"ranking and relevance disagree here)")
            forced_count += 1
        elif hit:
            reasons.append(f"force-surface: {hit}")
        scored.append((s, tier, reasons, a, is_stale, bool(hit) or qualifies))
        nb, sec, low = annotate(a, annotations, fs_groups, fs_matcher)
        ann_by_id[id(a)] = (nb, sec, low)
    # Surfaced items first, each block still in score order. Keeping the
    # surfaced set contiguous means the grouping and rescue logic below — which
    # compares indices against the cut — needs no change at all.
    #
    # Ties on score are common (many items share a tier weight with no
    # multipliers) and grouping anchors on whichever member is seen first, so
    # title and URL break ties: the same corpus produces the same group heads
    # every run.
    scored.sort(key=lambda x: (not x[5], -x[0], str(x[3].get("title", "")),
                               str(x[3].get("url", ""))))
    surfaced_n = sum(1 for x in scored if x[5])
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

    # Annotation tallies over the SURFACED set only — the drop list is not
    # reviewed item by item, so counting it here would misreport the workload.
    surfaced_pre = [x for x in scored if x[5]]
    nobody_count = sum(1 for x in surfaced_pre if ann_by_id.get(id(x[3]), (False,))[0])
    section_counts = {}
    for entry in (annotations.get("sections", []) or []):
        section_counts[entry.get("name")] = 0
    for x in surfaced_pre:
        sec = ann_by_id.get(id(x[3]), (False, None, False))[1]
        if sec is not None:
            section_counts[sec] = section_counts.get(sec, 0) + 1

    lines = []
    recency_note = f" · {stale_count} flagged STALE" if recency_on else " · recency gate OFF"
    ann_note = ""
    if annotations:
        secs = ", ".join(f"{k} {v}" for k, v in section_counts.items())
        ann_note = f" · {nobody_count} with NO BODY · suggested sections: {secs}"
    lines.append(f"# {report_title}")
    lines.append(f"*Generated {datetime.now(timezone.utc).isoformat()} · domain {cfg['domain']} · "
                 f"window {window_days}d · {len(arts)} articles scored · "
                 f"{len(surfaced)} surfaced, {len(dropped)} in drop list"
                 f"{f' · {forced_count} force-surfaced below the cut' if forced_count else ''}"
                 f"{recency_note}"
                 f"{ann_note}"
                 f"{f' · {len(child_of)} event group(s)' if child_of else ''}"
                 f"{f' · {dissolved_groups} oversized cluster(s) dissolved' if dissolved_groups else ''}.*")
    lines.append("")
    cut_note = (f"Surfacing threshold: score ≥ {min_score}."
                if min_score is not None else "No score threshold — everything surfaced.")
    lines.append(f"> **{cut_note}** The count is an OUTPUT of the scoring, never a target. "
                 f"If this surface is too large or too noisy, tune the weights, the "
                 f"vocabulary or the exclusions — do not cap it. The uncapped surface "
                 f"IS the diagnostic.")
    lines.append("")
    lines.append("> Score ORDERS the queue; it does not decide. Read the reasoning, "
                 "check the drop list, override freely. Prefer false positives.")
    if recency_on:
        lines.append("> ⚠ STALE = published outside the cycle window. NOT dropped — "
                     "confirm a fresh this-week hook (new KEV/exploitation/victim) or cut it.")
    if annotations:
        lines.append("> **[NO BODY]** = no usable article text was extracted, so there is "
                     "nothing to write an entry FROM. Vox Policy §6.2: fetch the body or "
                     "drop the item — do not write it up from the headline.")
        lines.append("> **Suggested section** is a SUGGESTION for you to confirm or "
                     "override. A trailing `?` means it fell through to the default or the "
                     "item has no body, so the guess came from a headline.")
    lines.append("")
    if child_of:
        lines.append("> ⧉ = same event, reported separately. Grouped for review only — "
                     "nothing merged, nothing dropped. Apply 'one event, one entry': "
                     "pick the best-sourced copy, fold the rest in.")
        lines.append("")
    lines.append("---")
    lines.append("## CANDIDATES (top-scored — review these first)")
    lines.append("")
    for idx, (s, tier, reasons, a, is_stale, _sf) in enumerate(surfaced):
        if idx in grouped_idx and idx not in child_of:
            continue                     # a sibling; printed under its group head
        mark = "⚠ STALE " if is_stale else ""
        kids = child_of.get(idx, [])
        tag = f" ⧉ {len(kids) + 1} reports" if kids else ""
        nb, sec, low = ann_by_id.get(id(a), (False, None, False))
        nb_mark = "[NO BODY] " if nb else ""
        lines.append(f"### {mark}{nb_mark}[{s}] {a.get('title','(no title)')}{tag}")
        lines.append(f"- **Source:** {source_name(a.get('source',''))} · {a.get('published','?')}")
        if sec:
            lines.append(f"- **Suggested section:** {sec}{'?' if low else ''}")
        if nb:
            why = nobody_reason(a)
            if why:
                lines.append(f"- **No body because:** {why}")
        lines.append(f"- **URL:** {a.get('url','')}")
        if a.get("final_url"):
            lines.append(f"- **Publisher URL:** {a['final_url']}")
        # The three evidence lines, together, at the end of the entry. This is
        # the handover to stage 3b: everything below is something the analyst
        # cannot re-derive from the article, because it was computed here and
        # would otherwise be discarded. Until 2026-08-26 the tier was calculated
        # for every item, carried through this entire function, and never
        # printed — the one number tying an item to an intelligence requirement.
        req = tier_requirement(tier, scoring)
        if req:
            # Identifier plus the tier's own name. The requirement's STATEMENT
            # stays in requirements.md; repeating it here would be a second copy.
            lines.append(f"- **Requirement met:** {req[0]} — {req[1]}")
        # The elements beneath the requirement, as identifiers only. The SIR is
        # derivable from the numbering (EEI-1.2.a -> SIR-1.2 -> PIR-1), so it is
        # never declared and never stored twice. Silent when nothing is mapped.
        eei = satisfied_elements(a, scoring)
        if eei:
            lines.append("- **Elements satisfied:** " + " · ".join(eei))
        # Absent `serves:` prints nothing at all. A domain that has not declared
        # its requirements is not broken, and s2 cannot be edited from the repo.
        lines.append(f"- **Score reasoning:** {' | '.join(reasons)}")
        ev = matched_evidence(a, scoring)
        if ev:
            # "present", not "fired" — this lists every group the article
            # matches, including ones that decided nothing. The reason string
            # above is what justified the score; this is the handle for
            # vocabulary refinement.
            lines.append("- **Vocabulary present:** "
                         + " · ".join(f"{g}={t}" for g, t in sorted(ev.items())))
        shown = kids[:max_group_display]
        hidden = len(kids) - len(shown)
        for k in shown:
            ks, _kt, kr, ka, k_stale, _ksf = scored[k]
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
    for off, (s, tier, reasons, a, is_stale, _sf) in enumerate(dropped):
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

    # Vox Policy §8 production gate. Emitted with every edition, alongside the
    # staging document it reports on.
    if annotations:
        nobody_items = [(x[0], x[3].get("title", "(no title)"), x[3].get("url", ""),
                         nobody_reason(x[3]), x[3].get("fetch_status", ""))
                        for x in surfaced_pre
                        if ann_by_id.get(id(x[3]), (False,))[0]]
        stats = [
            ("Articles scored in window", len(arts)),
            ("Surfaced candidates", len(surfaced_pre)),
            ("Distinct events after grouping", len(surfaced_pre) - len(grouped_idx & set(range(surfaced_n)))),
            ("Force-surfaced below the cut", forced_count),
            ("Flagged STALE", stale_count),
            ("Surfaced with no usable body", nobody_count),
            ("In drop list", len(dropped)),
        ]
        comp_path = compliance_path(out_path)
        comp_path.write_text(
            build_compliance_report(cfg, annotations, stats, nobody_items, section_counts),
            encoding="utf-8")
        print(f"[{cfg['domain']}] compliance report -> {comp_path}")

    if not args.no_push:
        push_staging(cfg["manifest"], out_path, date.today(),
                     log=lambda m: print(f"[{cfg['domain']}] {m}"))
        if annotations:
            push_compliance(cfg["manifest"], compliance_path(out_path), date.today(),
                            log=lambda m: print(f"[{cfg['domain']}] {m}"))


if __name__ == "__main__":
    main()
