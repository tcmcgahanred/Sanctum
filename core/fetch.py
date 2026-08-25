#!/usr/bin/env python3
# Sanctum · core/fetch.py · v1 · domain-agnostic; history via git
"""
Fetch — one job: get an article body, and say what happened when it can't.

WHY THIS EXISTS. The collector used to call trafilatura and keep whatever came
back. Whatever came back was not always an article. On 2026-08-25 a corpus
audit found 169 of 1303 items in the window carrying no usable body, and each
host was failing in a different way that the pipeline recorded identically:

    news.google.com      a redirect wrapper; the stored "body" was a raw
                         <a href=...> tag from the feed summary
    msrc.microsoft.com   a single-page app; the stored body was
                         "You need to enable JavaScript to run this app."
    industrialcyber.co   a Cloudflare interlude; the stored body was
                         "Just a moment.. We're verifying your browser."
    darkreading.com      the fetch returned nothing at all (default user
                         agent refused), leaving only a one-sentence feed dek

All four looked the same downstream: a short `text` field. The 40-word floor in
the staging annotations caught them only because failure pages happen to be
short. A longer consent wall would have sailed past that floor and reached the
analyst looking like an article. That is the defect this module closes.

WHAT IT GUARANTEES.
  1. A failure page is never stored as a body. It is detected and discarded.
  2. Every fetch records WHY it produced what it produced, so a broken sensor
     is distinguishable from a genuinely thin article. Those two need opposite
     responses — one is repaired, the other is dropped by the analyst — and
     until now nothing downstream could tell them apart.
  3. Optional dependencies degrade. If curl_cffi or googlenewsdecoder are not
     installed, their strategies are skipped and the rest still runs. The
     collector must never fail to collect because an extra is missing.

WHAT IT DOES NOT DO. It does not judge length, relevance or freshness. It has
no opinion on whether a body is good enough to write from — that is the
staging annotation's job, and the analyst's after that.
"""

import html as _html
import re
from urllib.parse import urlparse

# --- fetch strategies, every one imported defensively --------------------
# NOTHING here is imported at module scope in a way that can fail. The pure
# helpers below — strip_html, _classify, is_google_news_url, nobody_reason —
# are plain string logic with no dependencies, and the commit gate tests them
# on the AUTHORING machine, which has no collector dependencies installed and
# should never need them. An import that fails here would put the gate out of
# reach of the only machine that can commit.
#
# A dependency that is genuinely required still fails loudly: acolyte checks
# for the ones it cannot work without at startup and refuses to run.
try:
    import trafilatura
    from trafilatura.settings import use_config
except Exception:                       # pragma: no cover
    trafilatura = None
    use_config = None

try:                                    # TLS-fingerprint-impersonating client
    from curl_cffi import requests as _curl
except Exception:                       # pragma: no cover - absence is normal
    _curl = None

try:                                    # Google News redirect resolver
    from googlenewsdecoder import gnewsdecoder as _gnews_decode
except Exception:                       # pragma: no cover - absence is normal
    _gnews_decode = None

try:                                    # last-resort readability extractor
    from readability import Document as _Readability
except Exception:                       # pragma: no cover - absence is normal
    _Readability = None


# A plain, honest desktop browser string. trafilatura ships with `user_agents`
# EMPTY, which makes it announce itself as a scraping library; several
# publishers refuse that outright. This is not evasion — the collector is a
# single polite reader, and it still obeys the per-host sleep below.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)

# Substrings that mark a page as an interstitial rather than an article.
# Checked ONLY against short extractions (see _classify) — a real article about
# Cloudflare or CAPTCHAs must not be mistaken for one.
FAILURE_SIGNATURES = (
    "enable javascript to run this app",
    "you need to enable javascript",
    "please enable javascript",
    "just a moment",
    "verifying your browser",
    "checking your browser before accessing",
    "attention required",
    "enable javascript and cookies to continue",
    "please enable cookies",
    "ddos protection by cloudflare",
    "are you a robot",
    "access to this page has been denied",
    "unusual traffic from your computer",
)

# Below this word count a page is *eligible* to be judged an interstitial.
# Above it, signature text is assumed to be article content.
FAILURE_MAX_WORDS = 120

STATUS_OK = "ok"                    # a real body came back
STATUS_EMPTY = "empty"              # fetched fine, extractor found nothing
STATUS_BLOCKED = "blocked"          # the fetch itself returned nothing
STATUS_CHALLENGE = "challenge"      # bot check / consent interstitial
STATUS_JS_SHELL = "js_shell"        # single-page app; no server-rendered text
STATUS_REDIRECT_ONLY = "redirect_only"   # aggregator wrapper, unresolvable
STATUS_ERROR = "error"              # the strategy raised


# Why a body is missing, in the analyst's language. The distinction that
# matters is BROKEN SENSOR versus THIN ARTICLE: the first is repaired, the
# second is the analyst's call to cut. Before `fetch_status` existed, both
# arrived as an identically short `text` field and nothing could tell them
# apart — which is how four separate host failures went unnoticed for weeks.
NOBODY_REASONS = {
    "redirect_only": "aggregator link — publisher URL not resolved; chase the source",
    "blocked": "publisher refused the fetch — SENSOR PROBLEM, not a thin article",
    "challenge": "bot challenge intercepted the fetch — SENSOR PROBLEM, retry it",
    "js_shell": "page needs JavaScript; no server-rendered text — SENSOR PROBLEM",
    "empty": "fetched cleanly, but no article text was found",
    "error": "the fetch raised — SENSOR PROBLEM",
    "ok": "the article itself is genuinely short",
}


def nobody_reason(art):
    """
    A short phrase explaining a missing body, or "" when the record predates
    fetch tracking. Reads the corpus record only — never re-fetches.
    """
    status = art.get("fetch_status")
    if not status:
        return ""
    reason = NOBODY_REASONS.get(status, status)
    if art.get("body_source") == "summary":
        reason += "; text shown is the feed summary, not the article"
    return reason


def strip_html(raw):
    """
    Turn a feed summary into plain text.

    Feed summaries are HTML. Google News summaries are ONE ANCHOR TAG, so the
    old code stored `<a href="https://news.google.com/rss/articles/CBMi...">`
    as an article body and counted its markup as thirteen words. Stripping the
    tags does not conjure a body — it just stops the pipeline from lying about
    having one.
    """
    if not raw:
        return ""
    txt = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", str(raw))
    txt = re.sub(r"(?s)<[^>]+>", " ", txt)
    txt = _html.unescape(txt)
    return re.sub(r"\s+", " ", txt).strip()


def is_google_news_url(url):
    """A Google News RSS item link — a redirect wrapper, never an article."""
    try:
        p = urlparse(str(url))
    except Exception:
        return False
    return p.netloc.endswith("news.google.com") and "/rss/articles/" in p.path


def _classify(text):
    """
    Decide whether an extraction is a body or an interstitial.

    The word-count guard is the whole trick. "Just a moment" on a 40-word page
    is Cloudflare; the same phrase inside a 900-word incident write-up is
    prose. Signature matching without the guard would quietly delete real
    articles, which is a worse failure than the one being fixed.
    """
    if not text or not text.strip():
        return "", STATUS_EMPTY
    words = text.split()
    if len(words) <= FAILURE_MAX_WORDS:
        low = text.lower()
        for sig in FAILURE_SIGNATURES:
            if sig in low:
                status = (STATUS_JS_SHELL if "javascript" in sig
                          else STATUS_CHALLENGE)
                return "", status
    return text, STATUS_OK


def _traf_config(opts):
    cfg = use_config()
    cfg.set("DEFAULT", "USER_AGENTS", opts.get("user_agent", DEFAULT_USER_AGENT))
    cfg.set("DEFAULT", "DOWNLOAD_TIMEOUT", str(int(opts.get("timeout", 20))))
    cfg.set("DEFAULT", "SLEEP_TIME", str(float(opts.get("sleep_time", 1.0))))
    cfg.set("DEFAULT", "MAX_REDIRECTS", str(int(opts.get("max_redirects", 5))))
    # trafilatura discards extractions under MIN_EXTRACTED_SIZE (default 250
    # characters) and returns None. Short vendor advisories are real articles;
    # let them through and let the analyst's word floor make the call.
    cfg.set("DEFAULT", "MIN_EXTRACTED_SIZE", str(int(opts.get("min_extracted_size", 80))))
    return cfg


def _extract_html(raw_html, url):
    """Run the extractors over already-downloaded HTML, best first."""
    if not raw_html:
        return ""
    if trafilatura is None:
        return _readability_only(raw_html)
    try:
        out = trafilatura.extract(raw_html, url=url, include_comments=False,
                                  favor_recall=True)
        if out and out.strip():
            return out
    except Exception:
        pass
    if _Readability is not None:
        try:
            summary_html = _Readability(raw_html).summary()
            out = strip_html(summary_html)
            if out and out.strip():
                return out
        except Exception:
            pass
    return ""


def _readability_only(raw_html):
    """The fallback path when trafilatura is not installed at all."""
    if _Readability is None:
        return ""
    try:
        return strip_html(_Readability(raw_html).summary())
    except Exception:
        return ""


def _strategy_trafilatura(url, opts):
    if trafilatura is None:
        return "", STATUS_ERROR
    try:
        raw = trafilatura.fetch_url(url, config=_traf_config(opts))
    except Exception:
        return "", STATUS_ERROR
    if not raw:
        return "", STATUS_BLOCKED
    return _classify(_extract_html(raw, url))


def _strategy_impersonate(url, opts):
    """
    Refetch with a real browser's TLS and HTTP/2 fingerprint.

    Some publishers do not look at the user-agent string at all; they look at
    how the TLS handshake is shaped, which no plain Python client reproduces.
    This is the strategy that decides whether Dark Reading is recoverable.
    """
    if _curl is None:
        return "", STATUS_BLOCKED
    profile = opts.get("impersonate") or "chrome"
    try:
        resp = _curl.get(url, impersonate=profile,
                         timeout=int(opts.get("timeout", 20)),
                         allow_redirects=True)
    except Exception:
        return "", STATUS_ERROR
    if resp.status_code >= 400 or not resp.text:
        return "", STATUS_BLOCKED
    return _classify(_extract_html(resp.text, str(resp.url)))


def resolve_google_news(url, opts):
    """
    Turn a Google News wrapper into the publisher's own URL.

    Returns the resolved URL, or None. Google re-encodes these links whenever
    it feels like it, so this is expected to break someday; when it does the
    item is recorded as `redirect_only` and stays visible as a tip rather than
    silently becoming a bodyless candidate.
    """
    if _gnews_decode is None:
        return None
    try:
        res = _gnews_decode(url, interval=float(opts.get("gnews_interval", 1)))
    except Exception:
        return None
    if isinstance(res, dict) and res.get("status") and res.get("decoded_url"):
        return res["decoded_url"]
    return None


def fetch_body(url, opts=None, log=None):
    """
    Get the body of `url`.

    Returns (text, status, final_url). `text` is "" for every status except
    `ok`. `final_url` is where the body actually came from, which differs from
    `url` when an aggregator link was resolved.

    Strategy order, stopping at the first real body:
        0. resolve an aggregator wrapper to the publisher's URL
        1. trafilatura with a browser user agent
        2. refetch with a browser TLS fingerprint (curl_cffi)
        3. readability as the extractor of last resort (inside 1 and 2)
    """
    opts = opts or {}
    final_url = url
    if is_google_news_url(url) and opts.get("decode_google_news", True):
        resolved = resolve_google_news(url, opts)
        if resolved:
            final_url = resolved
        else:
            return "", STATUS_REDIRECT_ONLY, url

    text, status = _strategy_trafilatura(final_url, opts)
    if status == STATUS_OK:
        return text, status, final_url

    if opts.get("impersonate", "chrome"):
        text2, status2 = _strategy_impersonate(final_url, opts)
        if status2 == STATUS_OK:
            return text2, status2, final_url
        # Keep the more specific diagnosis of the two attempts. "challenge"
        # tells you the host is reachable and gating; "blocked" does not.
        if status == STATUS_BLOCKED and status2 != STATUS_BLOCKED:
            status = status2

    if log is not None:
        log.info("no body [%s] %s", status, final_url)
    return "", status, final_url
