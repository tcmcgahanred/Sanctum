#!/usr/bin/env python3
# Sanctum · core/reflist.py · v1 · domain-agnostic; history via git
"""
Reference lists — facts the apparatus can look up instead of inferring.

WHY THIS EXISTS. The CTI scoring model raises a score by 1.5x for "KEV /
actively exploited". It decides that by matching phrases in prose:
"actively exploited", "known exploited", "in the wild". That is an inference
about a fact, and the inference has already been measured wrong — a real CISA
advisory said "Active Threat" rather than "actively exploited" and the item
fell from 7.8 to 1.5.

CISA publishes the Known Exploited Vulnerabilities catalogue as JSON. The
question "is this vulnerability actually being exploited" has an authoritative
answer, and the pipeline can read it rather than guess at it.

DOMAIN-AGNOSTIC, AND THE DOMAIN FILE STILL ONLY DECLARES. This module knows
nothing about CVEs, CISA, or cyber security. It knows how to: fetch a JSON
document, walk to a list inside it, take one field from each entry as a key,
and find those keys in an article using a pattern. All four of those are
declared in the domain's manifest as plain values — a URL, a path, a field
name, a regex. A second effort can point the same machinery at an entirely
different list of identifiers and the engine does not change.

    reference_lists:
      kev:
        url: https://.../known_exploited_vulnerabilities.json
        json_path: vulnerabilities     # walk to this list
        key_field: cveID               # take this field from each entry
        match_pattern: "CVE-\\\\d{4}-\\\\d{4,7}"   # find candidates in an article
        cache_hours: 12

CACHING IS NOT OPTIONAL. A scorer that reaches the network per article is a
scorer that fails when the network does, and a 1.6 MB download per run is
rude. The catalogue is cached on disk and refetched only when stale. If the
fetch fails and a cache exists, THE CACHE IS USED and the staleness is
reported — a slightly old exploitation list is enormously better than none.

NOT WIRED INTO SCORING. Nothing in `core/rules.py` reads this yet. Whether a
multiplier fires on catalogue membership instead of, or alongside, a word
group is a Planning & Direction decision, and `tools/kev_impact.py` exists to
put a number in front of that decision before it is made.
"""

import json
import re
import time
import urllib.request
from pathlib import Path

DEFAULT_CACHE_HOURS = 12
FETCH_TIMEOUT = 30


def cache_path(base_dir, name):
    return Path(base_dir) / "reflists" / f"{name}.json"


def _walk(doc, json_path):
    """Follow a dotted path to a list. Empty path means the document is one."""
    if not json_path:
        return doc
    node = doc
    for part in str(json_path).split("."):
        if isinstance(node, dict):
            node = node.get(part)
        else:
            return None
    return node


def fetch(name, spec, base_dir, log=None, force=False):
    """
    Return (keys, note). `keys` is a set of identifiers, possibly empty.
    `note` says where they came from and how old they are, for the caller to
    print — silence about staleness is how a stale list becomes a wrong answer.
    """
    path = cache_path(base_dir, name)
    hours = float(spec.get("cache_hours", DEFAULT_CACHE_HOURS))
    fresh = False
    if path.exists():
        age_h = (time.time() - path.stat().st_mtime) / 3600.0
        fresh = age_h < hours
    else:
        age_h = None

    if fresh and not force:
        return _read_cache(path, spec), f"cache, {age_h:.1f}h old"

    url = spec.get("url")
    if not url:
        return set(), "no url declared"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        raw = urllib.request.urlopen(req, timeout=FETCH_TIMEOUT).read()
        json.loads(raw.decode("utf-8", "replace"))     # parse before we trust it
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return _read_cache(path, spec), "fetched"
    except Exception as e:
        if log is not None:
            log.warning("reference list %s fetch failed: %s", name, e)
        if path.exists():
            # Deliberate: an old list beats no list, and the age is reported
            # rather than swallowed.
            return _read_cache(path, spec), f"FETCH FAILED, using cache {age_h:.1f}h old"
        return set(), f"FETCH FAILED and no cache ({e})"


def _read_cache(path, spec):
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    entries = _walk(doc, spec.get("json_path", ""))
    if not isinstance(entries, list):
        return set()
    field = spec.get("key_field")
    keys = set()
    for e in entries:
        if field and isinstance(e, dict):
            v = e.get(field)
        else:
            v = e
        if v:
            keys.add(str(v).strip().upper())
    return keys


def keys_in_article(art, spec):
    """Identifiers appearing in an article's title or body, uppercased."""
    pattern = spec.get("match_pattern")
    if not pattern:
        return set()
    hay = f"{art.get('title', '')} {art.get('text', '')}"
    try:
        return {m.group(0).upper() for m in re.finditer(pattern, hay, re.I)}
    except re.error:
        return set()
