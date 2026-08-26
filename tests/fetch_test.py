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
                        DEFAULT_USER_AGENT, _traf_config,
                        available_strategies, nobody_reason, strip_html,
                        try_strategy)
from core.reflist import keys_in_article                           # noqa: E402

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

print("\n-- the user agent stays OFF unless a host is measured to need it --")
# MEASURED 2026-08-25 across all 56 sensors. Sending a browser user-agent is
# the obvious fix and it was a net loss: news.sophos.com 2902 words ->
# blocked (and tarpitting, 120s per attempt), cybersecuritynews.com 777 ->
# blocked. A Chrome header over a Python TLS handshake is a mismatch, and the
# mismatch is the signal. This guard exists so the obvious fix cannot be
# quietly reinstated without someone reading why it was removed.
check("no user agent is sent by default", DEFAULT_USER_AGENT, "")
check("...and the config does not carry one either",
      _traf_config({}).get("DEFAULT", "USER_AGENTS"), "")
check("an explicitly configured host UA is still honoured",
      _traf_config({"user_agent": "X/1.0"}).get("DEFAULT", "USER_AGENTS"), "X/1.0")

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

print("\n-- the module has a real interface, not a decorative one --")
# tools/sensor_bench.py used to call the underscore-prefixed functions
# directly. If the only caller has to open the hood, the separation was not a
# separation. These pin the public surface so it cannot rot back.
_avail = available_strategies()
check("availability is reported for every strategy",
      sorted(_avail), ["google_news_decode", "impersonate",
                       "readability_fallback", "trafilatura"])
check("every value is a plain boolean",
      all(isinstance(v, bool) for v in _avail.values()), True)
try:
    try_strategy("no_such_strategy", "https://x/y")
    check("an unknown strategy is refused loudly", "no error raised", "ValueError")
except ValueError:
    check("an unknown strategy is refused loudly", "ValueError", "ValueError")

print("\n-- reference lists: a fact looked up, not a phrase inferred --")
_spec = {"json_path": "vulnerabilities", "key_field": "cveID",
         "match_pattern": "CVE-[0-9]{4}-[0-9]{4,7}"}
_art = {"title": "Defending Against an Active Threat to Siemens S7 PLCs",
        "text": "CVE-2026-1234 affects controllers; see also cve-2019-0708."}
check("identifiers are found in title and body",
      sorted(keys_in_article(_art, _spec)), ["CVE-2019-0708", "CVE-2026-1234"])
check("case is normalised so the catalogue can be matched",
      "CVE-2019-0708" in keys_in_article(_art, _spec), True)
check("no pattern declared means no keys, never a crash",
      keys_in_article(_art, {}), set())
check("an article naming nothing yields nothing",
      keys_in_article({"title": "no identifiers here", "text": ""}, _spec), set())
# THE CASE THAT MOTIVATED THIS. A real CISA advisory said "Active Threat", not
# "actively exploited", so the word group stayed silent and the item fell from
# 7.8 to 1.5. The identifier was in the text the whole time.
check("...and the OBSERVED miss is catchable by identifier",
      "CVE-2026-1234" in keys_in_article(_art, _spec), True)
check("a malformed pattern is survived, not raised",
      keys_in_article(_art, dict(_spec, match_pattern="CVE-[")), set())

print()
if FAILS:
    print("RESULT: FAIL — %d check(s)" % len(FAILS))
    for label, got, want in FAILS:
        print("   %s: got %r, want %r" % (label, got, want))
    sys.exit(1)
print("RESULT: PASS — collection guards hold")
