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
    parsed = feedparser.parse(url)
    if not parsed.entries:
        return None
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
    return saved


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
    for url in urls:
        try:
            n = process_feed(url, seen, seen_titles, run_dir, ctx, log)
            n = process_page(url, seen, run_dir, ctx, log) if n is None else n
            log.info("%s -> %d new", url, n)
            total += n
        except Exception as e:
            log.error("source failed %s: %s", url, e)
    log.info("run done — %d new in %s", total, run_dir)
    print(f"[{cfg['domain']}] {total} new articles -> {run_dir}")

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
