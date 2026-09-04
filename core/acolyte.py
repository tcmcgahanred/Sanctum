#!/usr/bin/env python3
# Sanctum · Acolyte (collector engine) · v1.1 · domain-agnostic; history via git
"""
Acolyte — OSINT feed collector. Domain-agnostic: all specifics (which feeds,
where the corpus lives, the collection window) come from a domain's P&D
(<domain>/pnd.md -> manifest). Run it as:

    python -m core.acolyte --domain cti

Collection logic (feed parse, full-text extract, URL-hash + normalized-title
dedupe, dated JSON corpus) is unchanged from the original CTI collector; only
the paths/feed-list/backend are now config-driven.
"""

import argparse
import calendar
import hashlib
import json
import logging
import re
import socket
import subprocess
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# feedparser is REQUIRED to collect, but it is imported defensively so the
# module can be imported on a machine that has no collector dependencies —
# the authoring laptop, where the commit gate runs. Absence is caught loudly
# in main() rather than at import, so a genuinely missing dependency still
# stops a collection run with a readable message instead of a traceback.
try:
    import feedparser
except Exception:                       # pragma: no cover
    feedparser = None

from core.fetch import (STATUS_OK, fetch_body, strip_html)
from core.pnd import load_domain, load_sensors

DEFAULT_SUFFIX_SEPARATORS = (" - ", " | ", " — ")
DEFAULT_MIN_TITLE_LEN = 15


def uid(url):
    return hashlib.sha256(url.encode()).hexdigest()


def content_uid(text):
    """Identity of a PAGE snapshot: what the page said, not where it lives.

    A portal keeps one URL forever and changes its contents, so the URL is the
    wrong identity for it — keying on the URL is exactly what made a page
    source collectable once and never again. Whitespace and case are
    normalised, so reflowed markup is not mistaken for new reporting.
    """
    norm = re.sub(r"\s+", " ", (text or "")).strip().lower()
    return hashlib.sha256(("page:" + norm).encode()).hexdigest()


def normalize_title(title, suffix_separators):
    if not title:
        return ""
    t = title.strip()
    for sep in suffix_separators:
        if sep in t:
            parts = t.split(sep)
            if len(parts[-1]) <= 40:
                t = sep.join(parts[:-1])
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def title_key(title, suffix_separators, min_title_len):
    norm = normalize_title(title, suffix_separators)
    if len(norm) < min_title_len:
        return None
    return hashlib.sha256(norm.encode()).hexdigest()


def extract(url, log, opts=None):
    """Body text only, for callers that do not care why it is missing."""
    text, _status, _final = fetch_body(url, opts or {}, log)
    return text


def published_dt(entry):
    """
    The entry's publication time as an aware UTC datetime, or None.

    Prefers feedparser's parsed struct over the raw string: the raw field is
    free-form and malformed often enough that the scorer carries a recency
    gate to cope with it. None means "we do not know", and every caller must
    treat not knowing as a reason to KEEP.
    """
    for key in ("published_parsed", "updated_parsed"):
        st = entry.get(key)
        if st:
            try:
                return datetime.fromtimestamp(calendar.timegm(st), tz=timezone.utc)
            except Exception:
                continue
    # Second attempt on the raw string. feedparser leaves `published_parsed`
    # unset when its own parser balks, but RSS dates are RFC 2822 and the
    # standard library reads that format, so this recovers the ones it drops.
    for key in ("published", "updated"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(str(raw))
        except Exception:
            continue
        if dt is None:
            continue
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return None


def too_old(entry, max_age_days, now=None):
    """
    True when the entry was published outside the collection window.

    Standing direction, 2026-08-25: reports from outside the intelligence
    cycle window do not enter the corpus. Enforced HERE, before the fetch, so
    a decade of back catalogue costs no HTTP requests and never reaches the
    archive.

    Unknown dates are KEPT, deliberately. Dropping on a date we could not
    parse would silently delete whole feeds the first time a publisher changed
    its date format, and a silent deletion is the one failure mode this
    project cannot tolerate.
    """
    if not max_age_days:
        return False
    dt = published_dt(entry)
    if dt is None:
        return False
    now = now or datetime.now(timezone.utc)
    return dt < now - timedelta(days=float(max_age_days))


def save(run_dir, art):
    # ENCODING IS DECLARED, NEVER INHERITED. `ensure_ascii=False` writes real
    # characters rather than escapes, so the file's encoding decides whether it
    # can be written and read back at all. Python's default here is the
    # PLATFORM's: UTF-8 on the collector host, cp1252 on Windows. The scorer has
    # always read the corpus as UTF-8, so an unstated encoding meant the two
    # halves agreed only by accident of operating system — and on Windows a
    # single em dash was enough to make a record unreadable.
    (run_dir / f"{art['id'][:16]}.json").write_text(
        json.dumps(art, indent=2, ensure_ascii=False), encoding="utf-8")


def article(source, title, url, published, text,
            fetch_status=STATUS_OK, body_source="fetch", final_url=None,
            rec_id=None):
    """
    One corpus record.

    `fetch_status` and `body_source` are new and deliberately verbose. Before
    them, a blocked publisher, a JavaScript shell, a bot challenge and a
    genuinely short article all produced an identical record — a short `text`
    field — so a broken sensor was indistinguishable from a thin one. Those
    two need opposite responses, so the record now says which it is.

    `rec_id` overrides the identity. It exists for page snapshots, which are
    identified by their CONTENT rather than their URL; a feed item passes
    nothing and keeps the URL hash it has always had.
    """
    rec = {"id": rec_id or uid(url), "source": source, "title": title.strip(),
           "url": url, "published": published,
           "collected": datetime.now(timezone.utc).isoformat(), "text": text,
           "fetch_status": fetch_status, "body_source": body_source}
    if final_url and final_url != url:
        rec["final_url"] = final_url
    return rec


def _load_set(path):
    return set(path.read_text(encoding="utf-8").split()) if path.exists() else set()


def _load_titleset(path):
    return set(path.read_text(encoding="utf-8").split("\n")) - {""} if path.exists() else set()


def process_feed(url, seen, seen_titles, run_dir, ctx, log):
    """
    Collect one feed. Returns a per-feed tally, or None if it is not a feed.

    Items rejected for age are NOT written to `seen.txt`. Re-testing a date on
    every run costs nothing (no request is made), whereas marking them seen
    would blacklist them permanently and make the age policy irreversible.
    """
    parsed = feedparser.parse(url)
    if not parsed.entries:
        return None
    tally = {"saved": 0, "too_old": 0, "no_body": 0, "undated": 0, "status": {}}
    for e in parsed.entries:
        link = e.get("link")
        if not link or uid(link) in seen:
            continue
        if too_old(e, ctx["max_age_days"]):
            # NAMED, not merely counted. A count tells you something was
            # deleted; it does not tell you what, so it cannot be audited and
            # the policy cannot be judged. Every rejection is greppable:
            #     grep REJECTED-AGE /opt/ravenor/logs/collector.log
            tally["too_old"] += 1
            log.info("REJECTED-AGE pub=%s title=%r url=%s",
                     (published_dt(e).date().isoformat() if published_dt(e) else "?"),
                     str(e.get("title", ""))[:120], link)
            continue
        if published_dt(e) is None:
            tally["undated"] += 1
        tkey = title_key(e.get("title", ""), ctx["sep"], ctx["min_title_len"])
        if tkey and tkey in seen_titles:
            continue

        text, status, final_url = fetch_body(link, ctx["fetch"], log)
        body_source = "fetch"
        if not text:
            # The feed summary is a dek, not an article. It is kept because it
            # is often the only description of the item, and marked so nothing
            # downstream mistakes it for a body worth writing from.
            text = strip_html(e.get("summary", ""))
            body_source = "summary" if text else "none"
            tally["no_body"] += 1
        tally["status"][status] = tally["status"].get(status, 0) + 1

        art = article(url, e.get("title", ""), link, e.get("published", ""),
                      text, fetch_status=status, body_source=body_source,
                      final_url=final_url)
        save(run_dir, art)
        with ctx["seen_path"].open("a", encoding="utf-8") as f:
            f.write(art["id"] + "\n")
        seen.add(art["id"])
        if tkey:
            with ctx["seen_titles_path"].open("a", encoding="utf-8") as f:
                f.write(tkey + "\n")
            seen_titles.add(tkey)
        tally["saved"] += 1
    return tally


def process_page(url, seen, run_dir, ctx, log, record=None):
    """
    Collect a source that is not a feed. Returns a tally.

    TWO BEHAVIOURS, and which one you get is DECLARED, never guessed:

      kind: page      A portal. Re-read on EVERY run and identified by its
                      CONTENT, so new material posted under an unchanging URL
                      is collected. Identical content saves nothing and is
                      counted as `unchanged`.

      anything else   The original fallback, untouched: a source that failed to
                      parse as a feed is collected ONCE, keyed on its URL.

    The distinction is not decoration. `process_feed` returns None whenever a
    feed yields no entries, including when a real feed is temporarily empty or
    broken — so this function also receives healthy feeds having a bad day.
    Re-reading those every run would write a fresh record whenever their error
    page reflowed. A portal therefore has to say it is one.
    """
    kind = (record or {}).get("kind") or "feed"

    if kind != "page":
        if uid(url) in seen:
            return {"saved": 0, "too_old": 0, "no_body": 0, "undated": 0,
                    "unchanged": 0, "status": {}}
        # A feed that stopped producing looks exactly like a portal from here,
        # and the difference matters, so say so once per run rather than
        # collecting in silence.
        log.warning("NOT-A-FEED collected once as a page — if this is a portal "
                    "whose contents change, declare `kind: page` on its sensor "
                    "record: %s", url)

    text, status, final_url = fetch_body(url, ctx["fetch"], log)
    if not text:
        log.warning("no text [%s] %s", status, url)
        return {"saved": 0, "too_old": 0, "no_body": 1, "undated": 0,
                "unchanged": 0, "status": {status: 1}}

    # A page snapshot is identified by what it said. A once-only fallback keeps
    # the URL identity it has always had.
    rec_id = content_uid(text) if kind == "page" else uid(url)
    if rec_id in seen:
        log.info("unchanged since last run, nothing saved: %s", url)
        return {"saved": 0, "too_old": 0, "no_body": 0, "undated": 0,
                "unchanged": 1, "status": {status: 1}}

    # A page has no headline, and an untitled record is floored and flagged by
    # the scorer — so a portal without a declared title can never surface,
    # however fresh it is. `title:` on the sensor record is how the domain says
    # what the page is. Absent, behaviour is unchanged: no title.
    title = str((record or {}).get("title") or "")
    art = article(url, title, url, "", text, fetch_status=status,
                  body_source="fetch", final_url=final_url, rec_id=rec_id)
    if kind == "page":
        art["body_source"] = "page"
    save(run_dir, art)
    with ctx["seen_path"].open("a", encoding="utf-8") as f:
        f.write(art["id"] + "\n")
    seen.add(art["id"])
    return {"saved": 1, "too_old": 0, "no_body": 0, "undated": 0,
            "unchanged": 0, "status": {status: 1}}


def main():
    ap = argparse.ArgumentParser(description="Sanctum Acolyte — domain-agnostic collector")
    ap.add_argument("--domain", help="domain name (folder under repo, e.g. cti)")
    ap.add_argument("--pnd", help="explicit path to a pnd.md (overrides --domain)")
    ap.add_argument("--no-push", action="store_true", help="skip the corpus push")
    args = ap.parse_args()

    if feedparser is None:
        raise SystemExit(
            "acolyte: feedparser is not installed, so no feed can be read.\n"
            "  install the collector dependencies first:\n"
            "    /opt/ravenor/venv/bin/pip install -r requirements.txt")

    cfg = load_domain(domain=args.domain, pnd_path=args.pnd)
    collection = cfg["manifest"].get("collection", {})
    # Both default to OFF at the engine. A domain that has not declared them
    # collects exactly as it did before — tenet 2, the engine performs the
    # same on every domain, and a new knob must not change one silently.
    max_age = collection.get("max_publish_age_days")
    ctx = {
        "sep": tuple(collection.get("suffix_separators", DEFAULT_SUFFIX_SEPARATORS)),
        "min_title_len": int(collection.get("min_title_len", DEFAULT_MIN_TITLE_LEN)),
        "max_age_days": float(max_age) if max_age else None,
        "fetch": collection.get("fetch", {}) or {},
        "seen_path": cfg["seen_path"],
        "seen_titles_path": cfg["seen_titles_path"],
    }

    cfg["log_path"].parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=cfg["log_path"], level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("sanctum.acolyte")

    # feedparser opens its own socket and honours no timeout argument, so a
    # publisher that accepts a connection and then stops talking hangs the
    # whole run. A process-wide default is the only lever that reaches it.
    socket.setdefaulttimeout(float(ctx["fetch"].get("timeout", 20)) * 2)

    run_dir = cfg["corpus_dir"] / date.today().isoformat()
    run_dir.mkdir(parents=True, exist_ok=True)

    seen = _load_set(cfg["seen_path"])
    seen_titles = _load_titleset(cfg["seen_titles_path"])
    urls = cfg["sensors"]                       # from pnd.md inline block (or file fallback)
    # Same sources, same order, as records. A domain that declares nothing gets
    # {"url": u} per source and behaves exactly as before.
    records = cfg.get("sensor_records") or [{"url": u} for u in urls]
    by_url = {r.get("url"): r for r in records}
    pages = sum(1 for r in records if r.get("kind") == "page")
    run = {"saved": 0, "too_old": 0, "no_body": 0, "undated": 0, "unchanged": 0}
    statuses = {}
    log.info("run start [%s] — %d sources (%s), %d declared as pages, %d seen, "
             "%d seen-titles, max_publish_age_days=%s",
             cfg["domain"], len(urls), cfg["sensors_source"], pages, len(seen),
             len(seen_titles), ctx["max_age_days"])
    for url in urls:
        try:
            rec = by_url.get(url) or {"url": url}
            # A declared page is never handed to the feed parser. Parsing it
            # would cost a request and, for a portal that happens to emit
            # something feed-shaped, would silently take the feed path instead.
            if rec.get("kind") == "page":
                t = process_page(url, seen, run_dir, ctx, log, record=rec)
            else:
                t = process_feed(url, seen, seen_titles, run_dir, ctx, log)
                if t is None:
                    t = process_page(url, seen, run_dir, ctx, log, record=rec)
            log.info("%s -> %d new, %d too old, %d no body, %d undated, "
                     "%d unchanged %s",
                     url, t["saved"], t["too_old"], t["no_body"], t["undated"],
                     t.get("unchanged", 0), t["status"] or "")
            for k in run:
                run[k] += t.get(k, 0)
            for k, v in t["status"].items():
                statuses[k] = statuses.get(k, 0) + v
        except Exception as e:
            log.error("source failed %s: %s", url, e)

    # The run summary is the sensor health report. A feed that silently starts
    # returning nothing usable is the failure this project is least able to
    # notice, so the counts are printed, not merely logged.
    breakdown = ", ".join(f"{k} {v}" for k, v in sorted(statuses.items()))
    log.info("run done — %d new, %d rejected as too old, %d with no body, "
             "%d undated, %d pages unchanged, in %s [%s]",
             run["saved"], run["too_old"], run["no_body"], run["undated"],
             run["unchanged"], run_dir, breakdown)
    print(f"[{cfg['domain']}] {run['saved']} new articles -> {run_dir}")
    print(f"[{cfg['domain']}] rejected as published outside the window: {run['too_old']}")
    nb_line = f"[{cfg['domain']}] collected with no usable body: {run['no_body']}"
    if breakdown:
        nb_line += f" — fetch outcomes: {breakdown}"
    print(nb_line)
    if run["too_old"]:
        print(f"[{cfg['domain']}]   -> each one is named in the log: "
              f"grep REJECTED-AGE {cfg['log_path']}")
    if run["undated"]:
        print(f"[{cfg['domain']}] kept despite an unparseable publish date: "
              f"{run['undated']} — these bypass the age cutoff by design")
    if pages:
        # A portal that never changes and a portal that broke look identical in
        # the corpus — both produce nothing — so the re-read is reported even
        # when it found nothing. Silence here is what cost the last one.
        print(f"[{cfg['domain']}] page sources re-read: {pages} — "
              f"{run['unchanged']} unchanged since the last run")

    # Corpus push (config-driven; portable). rclone remote comes from the manifest.
    corpus = cfg["manifest"].get("corpus", {})
    if not args.no_push and corpus.get("backend") == "rclone" and corpus.get("rclone_remote"):
        remote = corpus["rclone_remote"]
        try:
            subprocess.run(["rclone", "copy", str(cfg["corpus_dir"]), remote], check=True)
            print(f"[{cfg['domain']}] corpus pushed -> {remote}")
        except Exception as e:
            log.error("rclone push failed: %s", e)
            print(f"[{cfg['domain']}] WARNING: corpus push failed: {e}")


if __name__ == "__main__":
    main()
