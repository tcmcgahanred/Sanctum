#!/usr/bin/env python3
# Sanctum · tests/fetch_test.py · collection-side guards; history via git
"""
Guards for the collection fixes of 2026-08-25.

WHY THESE EXIST. A corpus audit found 169 of 1303 items in the window with no
usable body, across four hosts failing four different ways, all of which the
pipeline recorded identically. The tests below pin the behaviour that stops
each of those from recurring silently. Every case is derived from a real
record in the corpus, not invented — the strings marked OBSERVED are verbatim
from what the collector actually stored.

Runs offline. No test here makes a network request: a guard that needs the
internet is a guard that gets skipped on the day it matters.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.acolyte import article, published_dt, too_old            # noqa: E402
from core.fetch import (STATUS_CHALLENGE, STATUS_EMPTY, STATUS_JS_SHELL,  # noqa: E402
                        STATUS_OK, _classify, is_google_news_url,
                        nobody_reason, strip_html)

FAILS = []


def check(label, got, want):
    ok = got == want
    print("  %-4s %-62s got=%r" % ("ok" if ok else "FAIL", label, got))
    if not ok:
        FAILS.append((label, got, want))


NOW = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)


def entry(days_ago=None, raw=None):
    e = {}
    if days_ago is not None:
        e["published_parsed"] = (NOW - timedelta(days=days_ago)).utctimetuple()
    if raw is not None:
        e["published"] = raw
    return e


print("\n-- feed summaries are HTML, and must not be stored as prose --")
# OBSERVED: what the collector stored as the "body" of a Google News item.
GNEWS_SUMMARY = ('<a href="https://news.google.com/rss/articles/CBMihAFBVV95cUxP'
                 'VU9PaWNfQzdjbTl1dFVFTDFwRTQx">Kings and Tulare County residents'
                 ' can get free tax help</a>&nbsp;-&nbsp;yourcentralvalley.com')
check("markup is gone", "<" in strip_html(GNEWS_SUMMARY), False)
check("entities decoded", "&nbsp;" in strip_html(GNEWS_SUMMARY), False)
check("anchor text survives",
      strip_html(GNEWS_SUMMARY).startswith("Kings and Tulare County"), True)
check("empty in, empty out", strip_html(""), "")
check("None in, empty out", strip_html(None), "")

print("\n-- failure pages must never be stored as bodies --")
# OBSERVED, msrc.microsoft.com
check("MSRC JavaScript shell",
      _classify("You need to enable JavaScript to run this app.")[1], STATUS_JS_SHELL)
# OBSERVED, industrialcyber.co
check("Cloudflare interlude",
      _classify("Just a moment..\nWe're verifying your browser. You'll be "
                "redirected shortly.\nIf you are not redirected,\nclick here\n.")[1],
      STATUS_CHALLENGE)
check("a failure page yields no text",
      _classify("You need to enable JavaScript to run this app.")[0], "")
check("empty extraction", _classify("")[1], STATUS_EMPTY)
check("whitespace-only extraction", _classify("   \n  ")[1], STATUS_EMPTY)

print("\n-- ...and a real article must survive containing the same words --")
# THE GUARD THAT MATTERS. Signature matching without a length check would
# delete genuine reporting about bot protection. Silently deleting real
# articles is a worse failure than the one being fixed.
LONG_REAL = ("word " * 400) + " the operators bypassed the just a moment "\
            "challenge and the enable javascript interstitial entirely."
check("400-word article naming the signatures", _classify(LONG_REAL)[1], STATUS_OK)
check("...and its text is returned intact", _classify(LONG_REAL)[0] == LONG_REAL, True)
# OBSERVED, darkreading.com — a real one-sentence dek, not a failure page.
DEK = ("A malicious application delivers four-stage Android spyware via phony "
       "Google Play sites, exploiting civilian fear during Iranian missile strikes.")
check("a short but genuine dek is not a failure", _classify(DEK)[1], STATUS_OK)

print("\n-- aggregator wrappers are recognised --")
check("Google News RSS article",
      is_google_news_url("https://news.google.com/rss/articles/CBMixgFBVV95cU?oc=5"), True)
check("Google News search page (not an article)",
      is_google_news_url("https://news.google.com/rss/search?q=California"), False)
check("an ordinary publisher",
      is_google_news_url("https://www.bleepingcomputer.com/news/x"), False)
check("garbage input", is_google_news_url(""), False)

print("\n-- reports outside the cycle window do not enter the corpus --")
check("2 days old, cutoff 7", too_old(entry(2), 7, now=NOW), False)
check("6.9 days old, cutoff 7", too_old(entry(6.9), 7, now=NOW), False)
check("7.1 days old, cutoff 7", too_old(entry(7.1), 7, now=NOW), True)
# OBSERVED: the February 2023 article that force-surfaced at the top of the queue.
check("Feb 2023 article, cutoff 7",
      too_old(entry(raw="Fri, 10 Feb 2023 08:00:00 GMT"), 7, now=NOW), True)
check("...and the raw RFC 2822 string is what caught it",
      published_dt(entry(raw="Fri, 10 Feb 2023 08:00:00 GMT")).year, 2023)
print("  -- unknown dates are KEPT: dropping on a date we failed to parse would")
print("     silently delete a whole feed the day a publisher changed its format")
check("unparseable date", too_old(entry(raw="nonsense"), 7, now=NOW), False)
check("no date at all", too_old({}, 7, now=NOW), False)
check("cutoff disabled leaves everything", too_old(entry(1290), None, now=NOW), False)
check("cutoff of 0 is treated as disabled", too_old(entry(1290), 0, now=NOW), False)

print("\n-- the corpus record says WHY a body is missing --")
rec = article("feed", "T", "https://x/y", "", "", fetch_status="blocked",
              body_source="summary")
check("status recorded", rec["fetch_status"], "blocked")
check("body source recorded", rec["body_source"], "summary")
check("no final_url when unchanged", "final_url" in rec, False)
rec2 = article("feed", "T", "https://news.google.com/rss/articles/Z", "", "body",
               final_url="https://realpublisher.example/story")
check("final_url recorded when resolved", rec2["final_url"],
      "https://realpublisher.example/story")

print("\n-- ...and the staging document translates it for the analyst --")
check("a blocked publisher reads as a sensor fault",
      "SENSOR PROBLEM" in nobody_reason({"fetch_status": "blocked"}), True)
check("a short article does not",
      "SENSOR PROBLEM" in nobody_reason({"fetch_status": "ok"}), False)
check("a feed-summary body is disclosed",
      "feed summary" in nobody_reason({"fetch_status": "blocked",
                                       "body_source": "summary"}), True)
check("a record collected before fetch tracking says nothing rather than guessing",
      nobody_reason({"title": "old record"}), "")

print()
if FAILS:
    print("RESULT: FAIL — %d check(s)" % len(FAILS))
    for label, got, want in FAILS:
        print("   %s: got %r, want %r" % (label, got, want))
    sys.exit(1)
print("RESULT: PASS — collection guards hold")
