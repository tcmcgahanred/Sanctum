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
import hashlib
import json
import logging
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

import feedparser
import trafilatura

from core.pnd import load_domain, load_sensors

DEFAULT_SUFFIX_SEPARATORS = (" - ", " | ", " — ")
DEFAULT_MIN_TITLE_LEN = 15


def uid(url):
    return hashlib.sha256(url.encode()).hexdigest()


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


def extract(url, log):
    try:
        dl = trafilatura.fetch_url(url)
        return (trafilatura.extract(dl, include_comments=False) or "") if dl else ""
    except Exception as e:
        log.warning("extract failed %s: %s", url, e)
        return ""


def save(run_dir, art):
    (run_dir / f"{art['id'][:16]}.json").write_text(
        json.dumps(art, indent=2, ensure_ascii=False))


def article(source, title, url, published, text):
    return {"id": uid(url), "source": source, "title": title.strip(),
            "url": url, "published": published,
            "collected": datetime.now(timezone.utc).isoformat(), "text": text}


def _load_set(path):
    return set(path.read_text().split()) if path.exists() else set()


def _load_titleset(path):
    return set(path.read_text().split("\n")) - {""} if path.exists() else set()


def process_feed(url, seen, seen_titles, run_dir, ctx, log):
    """
    Collect one feed. Returns (saved, health) or (None, health) when the URL
    yielded no feed entries and the caller should try the page path.

    `health` is a dict the caller logs. It exists because "0 new" is ambiguous
    and was hiding dead sensors:

        a feed returning 50 items you have already seen   -> 0 new
        a feed returning nothing at all                   -> 0 new

    Identical in the log, opposite in meaning. The number that separates them is
    the DENOMINATOR — how many items the source returned before the seen-list
    filter — and it was being computed on every run and thrown away.

    This is the second time a raw count without its denominator has misled here;
    the first was match-frequency in the archive search, where a fall in hits was
    read as a real decline when collection volume had simply dropped. Same
    mistake, different place. When reporting a count, report what it is out of.

    feedparser also hands back status, the final URL after redirects, and a
    parse-error flag, all of which were being discarded. They cost nothing.
    """
    parsed = feedparser.parse(url)
    health = {
        "returned": len(parsed.entries),
        "status": getattr(parsed, "status", None),
        "bozo": bool(getattr(parsed, "bozo", 0)),
        "final_url": getattr(parsed, "href", None),
        "error": None,
    }
    if health["bozo"]:
        exc = getattr(parsed, "bozo_exception", None)
        health["error"] = f"{type(exc).__name__}: {exc}" if exc else "malformed feed"
    if not parsed.entries:
        return None, health
    saved = 0
    for e in parsed.entries:
        link = e.get("link")
        if not link or uid(link) in seen:
            continue
        tkey = title_key(e.get("title", ""), ctx["sep"], ctx["min_title_len"])
        if tkey and tkey in seen_titles:
            continue
        art = article(url, e.get("title", ""), link,
                      e.get("published", ""), extract(link, log) or e.get("summary", ""))
        save(run_dir, art)
        with ctx["seen_path"].open("a") as f:
            f.write(art["id"] + "\n")
        seen.add(art["id"])
        if tkey:
            with ctx["seen_titles_path"].open("a") as f:
                f.write(tkey + "\n")
            seen_titles.add(tkey)
        saved += 1
    return saved, health


def process_page(url, seen, run_dir, ctx, log):
    if uid(url) in seen:
        return 0
    text = extract(url, log)
    if not text:
        log.warning("no text %s", url)
        return 0
    art = article(url, "", url, "", text)
    save(run_dir, art)
    with ctx["seen_path"].open("a") as f:
        f.write(art["id"] + "\n")
    seen.add(art["id"])
    return 1


def main():
    ap = argparse.ArgumentParser(description="Sanctum Acolyte — domain-agnostic collector")
    ap.add_argument("--domain", help="domain name (folder under repo, e.g. cti)")
    ap.add_argument("--pnd", help="explicit path to a pnd.md (overrides --domain)")
    ap.add_argument("--no-push", action="store_true", help="skip the corpus push")
    args = ap.parse_args()

    cfg = load_domain(domain=args.domain, pnd_path=args.pnd)
    collection = cfg["manifest"].get("collection", {})
    ctx = {
        "sep": tuple(collection.get("suffix_separators", DEFAULT_SUFFIX_SEPARATORS)),
        "min_title_len": int(collection.get("min_title_len", DEFAULT_MIN_TITLE_LEN)),
        "seen_path": cfg["seen_path"],
        "seen_titles_path": cfg["seen_titles_path"],
    }

    cfg["log_path"].parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=cfg["log_path"], level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("sanctum.acolyte")

    run_dir = cfg["corpus_dir"] / date.today().isoformat()
    run_dir.mkdir(parents=True, exist_ok=True)

    seen = _load_set(cfg["seen_path"])
    seen_titles = _load_titleset(cfg["seen_titles_path"])
    urls = cfg["sensors"]                       # from pnd.md inline block (or file fallback)
    total = 0
    log.info("run start [%s] — %d sources (%s), %d seen, %d seen-titles",
             cfg["domain"], len(urls), cfg["sensors_source"], len(seen), len(seen_titles))
    dead = []
    for url in urls:
        try:
            n, health = process_feed(url, seen, seen_titles, run_dir, ctx, log)

            # A feed that parsed to zero entries used to fall through to the page
            # path SILENTLY, which is how a broken feed stopped being a broken
            # feed and quietly became "a page source that yielded nothing." That
            # reclassification is the reason a source can sit in the list for
            # months contributing nothing with no error anywhere. It still falls
            # through — sometimes a page really is the right path — but it says so.
            if n is None:
                log.warning("no feed entries %s (status=%s bozo=%s%s) — trying page path",
                            url, health["status"], health["bozo"],
                            f" err={health['error']}" if health["error"] else "")
                n = process_page(url, seen, run_dir, ctx, log)
                health["returned"] = n  # the page path yields at most one item

            log.info("%s -> %d new of %d returned (status=%s)",
                     url, n, health["returned"], health["status"])

            # ZERO RETURNED is the signal worth acting on. Zero NEW is normal —
            # it just means nothing has been published since the last run.
            if health["returned"] == 0:
                dead.append((url, health))
                log.warning("ZERO YIELD %s (status=%s bozo=%s%s)",
                            url, health["status"], health["bozo"],
                            f" err={health['error']}" if health["error"] else "")
            total += n
        except Exception as e:
            log.error("source failed %s: %s", url, e)
            dead.append((url, {"status": None, "bozo": False, "error": str(e)}))

    log.info("run done — %d new in %s; %d of %d sources returned nothing",
             total, run_dir, len(dead), len(urls))
    print(f"[{cfg['domain']}] {total} new articles -> {run_dir}")
    if dead:
        # Printed, not only logged. A sensor list that claims coverage it does
        # not have is the failure this whole change exists to surface, and a
        # warning nobody sees is not a warning.
        print(f"[{cfg['domain']}] WARNING: {len(dead)} of {len(urls)} sources "
              f"returned zero items:")
        for url, h in dead:
            detail = h.get("error") or f"status={h.get('status')}"
            print(f"    {url}  ({detail})")
        print(f"[{cfg['domain']}] Zero items is not the same as zero new. "
              f"Run tools/sensor_check.py for a full diagnosis.")

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
