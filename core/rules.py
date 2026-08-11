# Sanctum · core/rules.py · (matching + scoring engine; history via git)
"""
Domain-agnostic scoring engine.

The engine holds NO domain knowledge. All tiers, keyword groups, elevation
multipliers, and tier-assignment rules come from a domain's P&D config
(see core/pnd.py). This module only knows how to:
  - match keyword groups against an article (with the same word-boundary
    semantics the CTI pre-filter used), and
  - evaluate a small rule tree (any / all / group / proximity / always)
    to assign the single highest qualifying tier, then apply multipliers.

Faithful to the original hardcoded CTI arbites.py: same _hit semantics,
same blob/title/text scopes, same proximity behavior. Behavior-preservation
is verified by tests/diff_scores.py.
"""

import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None


# ------------------------------------------------------------------
# Keyword matching (ported verbatim from the original arbites._hit)
# ------------------------------------------------------------------
def make_matcher(word_boundary_terms):
    """Return a _hit(text, terms) closure.

    Short/ambiguous terms (<=4 chars, or explicitly listed) match on word
    boundaries to avoid substring collisions ('ics' in 'physics'); longer
    distinctive terms use fast substring matching. Terms are stripped, exactly
    as the original did.
    """
    wb = set(word_boundary_terms or [])

    def _hit(text, terms):
        for t in terms:
            t = t.strip()
            if not t:
                continue
            if len(t) <= 4 or t in wb:
                if re.search(r"\b" + re.escape(t) + r"\b", text):
                    return t
            else:
                if t in text:
                    return t
        return None

    return _hit


# ------------------------------------------------------------------
# Scope helpers
# ------------------------------------------------------------------
def _scopes(art):
    title = str(art.get("title", "")).strip()
    title_l = title.lower()
    text_l = str(art.get("text", "")).lower()
    blob = (title + "  " + str(art.get("text", ""))).lower()
    return title, {"title": title_l, "text": text_l, "blob": blob}, text_l


# ------------------------------------------------------------------
# Rule-tree evaluation
# ------------------------------------------------------------------
def _eval_atom(atom, groups, matcher, scopes, text_l):
    # bare string "always"
    if isinstance(atom, str):
        return atom.strip().lower() == "always"

    if "always" in atom:
        return bool(atom["always"])

    if "group" in atom:
        g = atom["group"]
        scope = atom.get("scope", "blob")
        if g not in groups:
            raise KeyError(f"rule references unknown group '{g}'")
        if scope not in scopes:
            raise KeyError(f"rule references unknown scope '{scope}'")
        return matcher(scopes[scope], groups[g]) is not None

    if "proximity" in atom:
        p = atom["proximity"]
        a_terms = groups[p["a"]]
        b_terms = groups[p["b"]]
        window = int(p.get("window", 120))
        # Faithful to the original: locate the 'a' term by RAW substring find
        # in the body text, take a +/-window slice, match 'b' inside it.
        for ct in a_terms:
            idx = text_l.find(ct)
            if idx == -1:
                continue
            slice_ = text_l[max(0, idx - window): idx + window]
            if matcher(slice_, b_terms) is not None:
                return True
        return False

    # combinators
    if "any" in atom:
        return any(_eval_atom(x, groups, matcher, scopes, text_l) for x in atom["any"])
    if "all" in atom:
        return all(_eval_atom(x, groups, matcher, scopes, text_l) for x in atom["all"])

    raise ValueError(f"unrecognized rule atom: {atom!r}")


def _rule_matched_terms(atom, groups, matcher, scopes, text_l):
    """Best-effort human reason string for a satisfied atom (display only)."""
    if isinstance(atom, str) or "always" in (atom if isinstance(atom, dict) else {}):
        return "always"
    if "group" in atom:
        scope = atom.get("scope", "blob")
        hit = matcher(scopes[scope], groups[atom["group"]])
        return f"{atom['group']}:'{hit}'@{scope}"
    if "proximity" in atom:
        p = atom["proximity"]
        return f"{p['a']}~{p['b']}"
    if "any" in atom:
        return " or ".join(_rule_matched_terms(x, groups, matcher, scopes, text_l) for x in atom["any"])
    if "all" in atom:
        return " and ".join(_rule_matched_terms(x, groups, matcher, scopes, text_l) for x in atom["all"])
    return "?"


# ------------------------------------------------------------------
# Scoring
# ------------------------------------------------------------------
def score_article(art, scoring):
    """
    Assign a provisional tier + elevation signals from a domain's scoring config.
    Returns (score: float, tier_id, reasons: list[str]).

    `scoring` is the parsed 'scoring' block: tiers[], multipliers[], groups{},
    word_boundary_terms[], settings{}.
    Doctrine: round UP on uncertainty is expressed in the domain's rules, not here.
    """
    groups = scoring["groups"]
    matcher = make_matcher(scoring.get("word_boundary_terms"))
    settings = scoring.get("settings", {})

    title, scopes, text_l = _scopes(art)
    reasons = []

    # Empty-title guard (config-driven floor). Feed artifacts with no title are
    # data-quality problems — flag and floor so they land in the drop list.
    if not title:
        et = settings.get("empty_title", {"score": 0.5, "tier": 4,
                                          "flag": "FLAG: empty title (feed artifact — verify source)"})
        return float(et.get("score", 0.5)), et.get("tier", 4), [et.get("flag", "FLAG: empty title")]

    # Tier assignment — first qualifying tier wins (highest listed first).
    tier_id = None
    weight = None
    for tier in scoring["tiers"]:
        require = tier.get("require", "always")
        if _eval_atom(require, groups, matcher, scopes, text_l):
            tier_id = tier["id"]
            weight = float(tier["weight"])
            reasons.append(f"T{tier_id} {tier.get('name','')} "
                           f"({_rule_matched_terms(require, groups, matcher, scopes, text_l)})".rstrip())
            break
    if tier_id is None:  # no tier matched and none was 'always' — treat as lowest
        last = scoring["tiers"][-1]
        tier_id, weight = last["id"], float(last["weight"])
        reasons.append(f"T{tier_id} {last.get('name','')} (fallback)")

    score = weight

    # Elevation multipliers (stack; absent = neutral).
    for m in scoring.get("multipliers", []):
        if _eval_atom(m["when"], groups, matcher, scopes, text_l):
            score *= float(m["factor"])
            reasons.append(f"x{m['factor']} {m.get('name','mult')}")

    return round(score, 2), tier_id, reasons


# ------------------------------------------------------------------
# Recency gate (Codex Layer 4) — flag by PUBLISH date, never drop.
# Additive only: it appends a reason string; it changes no score and cuts
# nothing. Origin: a June FortiBleed advisory surfaced in the August edition
# because "current" was windowed on collection date, not publication date.
# ------------------------------------------------------------------
_WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
             "friday": 4, "saturday": 5, "sunday": 6}


def compute_cycle_window(now_utc, settings):
    """
    Return (window_start_utc, cutoff_utc) for the current cycle.

    cutoff = the most recent <cutoff_weekday> at <cutoff_time> in <timezone>
    that is <= now (the ICOD, e.g. Monday 0900 America/Los_Angeles).
    window_start = cutoff - window_days.
    """
    rec = settings.get("recency", {}) or {}
    tzname = rec.get("timezone", "UTC")
    tz = ZoneInfo(tzname) if (ZoneInfo and tzname) else timezone.utc
    now_local = now_utc.astimezone(tz)

    wd = _WEEKDAYS.get(str(rec.get("cutoff_weekday", "monday")).lower(), 0)
    cutoff_time = str(rec.get("cutoff_time", "09:00"))
    hh, mm = (int(x) for x in cutoff_time.split(":")[:2]) if ":" in cutoff_time else (9, 0)

    days_back = (now_local.weekday() - wd) % 7
    candidate = now_local.replace(hour=hh, minute=mm, second=0, microsecond=0) - timedelta(days=days_back)
    if candidate > now_local:
        candidate -= timedelta(days=7)
    cutoff = candidate
    window_days = int(rec.get("window_days", settings.get("window_days", 7)))
    window_start = cutoff - timedelta(days=window_days)
    return window_start.astimezone(timezone.utc), cutoff.astimezone(timezone.utc)


def _parse_pub(s):
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    try:  # RFC-822 (typical RSS: "Mon, 09 Aug 2026 14:03:00 GMT")
        dt = parsedate_to_datetime(s)
        if dt is not None:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    try:  # ISO-8601 fallback
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def recency_tag(published, window_start):
    """
    Return a STALE reason string if the item is outside the cycle window, an
    'unknown date' flag if the publish date can't be parsed, or None if current.
    NEVER returns a signal to drop — flag only; the analyst confirms a fresh hook.
    """
    dt = _parse_pub(published)
    if dt is None:
        return "STALE? — publish date unknown, verify current hook"
    if dt < window_start:
        return f"STALE — confirm current hook (pub {dt.date().isoformat()})"
    return None
