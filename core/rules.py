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
    # `source` is the article's ORIGIN, not its content: feed URL plus source
    # label. It lets a rule require the authoritative publisher rather than any
    # article that mentions one - "CISA ordered a patch" in a trade write-up is
    # not the same signal as the directive from cisa.gov.
    source = (str(art.get("url", "")) + " " + str(art.get("source", ""))).lower()
    return title, {"title": title_l, "text": text_l, "blob": blob,
                   "source": source}, text_l


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
        # SCOPE. Default "text" is the original: body only, title never seen.
        # "blob" prepends the title. Opt-in, so older rules are untouched.
        hay = scopes.get(p.get("scope", "text"), text_l)
        # OCCURRENCES. Default False is the original and a real limitation:
        # only the FIRST occurrence of each a-term is tested, so a term in
        # boilerplate masks the same term beside an incident word.
        all_occ = bool(p.get("all_occurrences", False))
        max_occ = int(p.get("max_occurrences", 40))
        # The term is used VERBATIM, padding included. `geo` carries ' calif ',
        # 'uc ' and 'csu ' precisely so the spaces act as the boundary here.
        # Stripping them turns 'uc ' into a bare substring matching inside
        # "product" and "reduce", which fired M1 on 190 articles with no AOR
        # content at all. Found on the live corpus, by nothing else.
        for ct in a_terms:
            if not ct:
                continue
            idx = hay.find(ct)
            seen = 0
            while idx != -1:
                slice_ = hay[max(0, idx - window): idx + window]
                if matcher(slice_, b_terms) is not None:
                    return True
                if not all_occ:
                    break
                seen += 1
                if seen >= max_occ:
                    break
                idx = hay.find(ct, idx + 1)
        return False

    # combinators
    if "any" in atom:
        return any(_eval_atom(x, groups, matcher, scopes, text_l) for x in atom["any"])
    if "all" in atom:
        return all(_eval_atom(x, groups, matcher, scopes, text_l) for x in atom["all"])

    # Exclusion. `not` inverts the atom beneath it, so "match X unless Y" is
    # written  {all: [{group: X}, {not: {group: Y}}]}.
    #
    # WHY THIS EXISTS. Without it the only cure for a term that collides with an
    # unrelated meaning is to delete the term — and deleting the term silently
    # deletes the requirement it was standing for. Threat-actor names are the
    # standing example: several are also ordinary products, places or common
    # words, and they arrive through general feeds that are otherwise wanted, so
    # dropping the source is not available either. Collisions have so far been
    # resolved by finding a more precise synonym; where none exists the choice
    # was accept the noise or lose the requirement. This is the third option.
    #
    # NARROW EXCEPTION TO TENET 8 ("prefer false positives — flag, don't drop").
    # Exclusion removes nothing. It withholds a tier or a multiplier, so the
    # item is still collected, still scored, still listed, still shown with its
    # reasoning — just lower. Nothing leaves the corpus or the drop list.
    if "not" in atom:
        return not _eval_atom(atom["not"], groups, matcher, scopes, text_l)

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
        # Render only branches that fired. Rendering all of them printed
        # "sector:'None'@title" beside a rule that matched on proximity - a
        # reason naming a match that did not happen sends the analyst to
        # check the wrong thing (tenet 3).
        sat = [x for x in atom["any"] if _eval_atom(x, groups, matcher, scopes, text_l)]
        return " or ".join(_rule_matched_terms(x, groups, matcher, scopes, text_l)
                           for x in (sat or atom["any"]))
    if "all" in atom:
        return " and ".join(_rule_matched_terms(x, groups, matcher, scopes, text_l) for x in atom["all"])
    if "not" in atom:
        # This atom is only ever rendered because it was SATISFIED, and a
        # satisfied `not` means the excluded thing was absent. Name what was
        # ruled out — a reader auditing the score needs to see the exclusion
        # fired, not just the terms that hit (tenet 8: show the reasoning).
        inner = atom["not"]
        if isinstance(inner, dict) and "group" in inner:
            return f"not {inner['group']}"
        return "not (…)"
    return "?"


# ------------------------------------------------------------------
# Scoring
# ------------------------------------------------------------------
def matched_evidence(art, scoring):
    """
    Which declared vocabulary groups actually appear in this article, and one
    representative term from each. Display and handover only — reads nothing
    the scorer does not already read, changes no score.

    SEPARATE FUNCTION, NOT AN EXTRA RETURN VALUE. `score_article` is called from
    eleven places across seven files; widening its tuple would break every one
    of them to serve a document none of them writes.

    Reports every group present, INCLUDING groups that did not decide the tier.
    That is deliberate and it is why the staging document labels this line
    "vocabulary present" rather than "terms fired" — the reasoning behind the
    score is the reason string, and conflating the two would claim a term
    contributed when it did not (tenet 3: never send the reader to check the
    wrong thing).
    """
    groups = scoring.get("groups") or {}
    matcher = make_matcher(scoring.get("word_boundary_terms"))
    _title, scopes, _text_l = _scopes(art)
    found = {}
    for gname, terms in groups.items():
        hit = matcher(scopes["blob"], terms or [])
        if hit:
            found[gname] = hit
    return found


def satisfied_elements(art, scoring, force_rules=None):
    """
    The essential elements of information this article actually satisfied, as
    sorted identifiers — never their statements. `requirements.md` owns the
    tree; the manifest declares which elements each scoring rule implements;
    this reads the join. Nothing here derives a requirement, which is the whole
    point: chat consumes what the config supplies and authors nothing.

    Only the tier that WON contributes, plus every multiplier, floor and
    force-surface rule that actually fired. A rule that did not fire did not
    satisfy anything, and naming one that did not would send the analyst to
    check the wrong thing.

    The SIR and the PIR are not returned and must not be declared anywhere:
    EEI-1.2.a sits under SIR-1.2 under PIR-1 by its own numbering. Deriving
    them costs nothing; storing them would be a second copy of one fact.

    Returns [] when nothing is declared - a domain that has not mapped its
    elements is not broken, and s2 cannot be edited from the repo at all.
    """
    groups = scoring["groups"]
    matcher = make_matcher(scoring.get("word_boundary_terms"))
    _title, scopes, text_l = _scopes(art)
    out = set()

    for tier in scoring.get("tiers", []) or []:
        if _eval_atom(tier.get("require", "always"), groups, matcher, scopes, text_l):
            out.update(tier.get("serves_eei") or [])
            break                      # first qualifying tier wins, as in scoring

    for m in scoring.get("multipliers", []) or []:
        if _eval_atom(m["when"], groups, matcher, scopes, text_l):
            out.update(m.get("serves_eei") or [])

    for f in scoring.get("floors", []) or []:
        if _eval_atom(f["when"], groups, matcher, scopes, text_l):
            out.update(f.get("serves_eei") or [])

    for f in (force_rules if force_rules is not None
              else scoring.get("force_surface", []) or []):
        if _eval_atom(f["when"], groups, matcher, scopes, text_l):
            out.update(f.get("serves_eei") or [])

    return sorted(out)


def tier_requirement(tier_id, scoring):
    """
    The intelligence requirement a tier answers, as (id, name), or None.

    Reads the `serves:` field a tier may declare. **Absent is normal and must
    stay silent** — a domain that has not declared its requirements is not
    broken, and `s2` is git-ignored so it cannot be edited from the repo at all
    (running-log.md Blocker 20). A staging document that printed
    "Requirement met: None" on every candidate of an undeclared domain would be
    worse than printing nothing.
    """
    for t in scoring.get("tiers", []) or []:
        if t.get("id") == tier_id:
            serves = t.get("serves")
            return (str(serves), str(t.get("name", ""))) if serves else None
    return None


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
            # Name the words that fired, exactly as the tier reason does. Until
            # 2026-08-26 a multiplier reason said only "x1.5 low-maturity SLTT
            # tech" and never which product word triggered it, so half the
            # evidence behind a score was invisible — and the multiplier groups
            # are the vocabulary most worth refining.
            why = _rule_matched_terms(m["when"], groups, matcher, scopes, text_l)
            reasons.append(f"x{m['factor']} {m.get('name','mult')}"
                           + (f" ({why})" if why and why != "always" else ""))

    # FLOORS raise a score to a stated minimum and never lower one. A floor is
    # deliberately weaker than force-surface: the item becomes visible at the
    # bottom of the surface rather than guaranteed a place. For signals that
    # are authoritative but of unproven relevance - an official directive about
    # a product not on this domain's technology list.
    for f in scoring.get("floors", []) or []:
        if _eval_atom(f["when"], groups, matcher, scopes, text_l):
            fl = float(f.get("score", 0))
            if score < fl:
                whyf = _rule_matched_terms(f["when"], groups, matcher, scopes, text_l)
                reasons.append(f"floor {fl} {f.get('name','floor')}"
                               + (f" ({whyf})" if whyf and whyf != "always" else ""))
                score = fl

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
