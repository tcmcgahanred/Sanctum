# Sanctum · core/rules.py · (matching + scoring engine; history via git)
"""
Domain-agnostic scoring engine.

The engine holds NO domain knowledge. All tiers, keyword groups, elevation
multipliers, and tier-assignment rules come from a domain's P&D config
(see core/pnd.py). This module only knows how to:
  - match keyword groups against an article (with the same word-boundary
    semantics the CTI pre-filter used), and
  - evaluate a small rule tree (any / all / not / group / proximity /
    pattern / always)
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
# A compiled-pattern cache. Patterns come from a domain file, so the set is
# small and fixed for a run; recompiling one per article per atom would be the
# only expensive thing in this module.
_PATTERN_CACHE = {}


def _compiled(expr):
    """Compile a domain-supplied regular expression, case-insensitively.

    A BAD PATTERN IS A LOUD FAILURE, not a silent non-match. A requirement
    whose detector never fires because its pattern does not compile would
    report as an uncollected requirement forever, and nothing would say why.
    """
    rx = _PATTERN_CACHE.get(expr)
    if rx is None:
        try:
            rx = re.compile(expr, re.IGNORECASE)
        except re.error as e:
            raise ValueError(
                f"detector pattern {expr!r} is not a valid regular "
                f"expression: {e}") from None
        _PATTERN_CACHE[expr] = rx
    return rx


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

    # KEYWORDS. A literal list of terms, written in the rule rather than named
    # somewhere else. This is what lets a rule be read on its own: you can see
    # what it searches for without opening another file. Same matching as a
    # `group`, same word-boundary rule for short terms.
    #
    # `group` is still here and still correct for a list used by several rules,
    # and for one too large to write out - the derived place table is 1,672
    # rows. The choice: inline if used once, a named group if used twice or
    # more, a library pointer if maintained outside this repository.
    if "keywords" in atom:
        scope = atom.get("scope", "blob")
        if scope not in scopes:
            raise KeyError(f"keywords references unknown scope '{scope}'")
        return matcher(scopes[scope], atom["keywords"] or []) is not None

    # PATTERN. For a fact that is an identifier rather than a vocabulary: a
    # MITRE ATT&CK technique code, a CVE, a CPE string. Set membership with
    # nothing to tune, which is why an identifier can carry a requirement on
    # its own where an ordinary word never can.
    #
    # Scope is DECLARED, never inherited, because the two existing atoms
    # disagree about their default - `group` defaults to blob, `proximity`
    # defaults to text - and a third silent default would be worse than none.
    # Written bare (`pattern: "..."`) the scope is blob, the widest.
    if "pattern" in atom:
        pat = atom["pattern"]
        expr = pat["match"] if isinstance(pat, dict) else pat
        scope = (pat.get("scope") if isinstance(pat, dict) else None) or "blob"
        if scope not in scopes:
            raise KeyError(f"pattern references unknown scope '{scope}'")
        return _compiled(expr).search(scopes[scope]) is not None
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
    if "pattern" in atom:
        pat = atom["pattern"]
        expr = pat["match"] if isinstance(pat, dict) else pat
        scope = (pat.get("scope") if isinstance(pat, dict) else None) or "blob"
        m = _compiled(expr).search(scopes[scope])
        return f"pattern:'{m.group(0) if m else None}'@{scope}"
    if "keywords" in atom:
        scope = atom.get("scope", "blob")
        hit = matcher(scopes[scope], atom["keywords"] or [])
        return f"keywords:'{hit}'@{scope}"
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


def _claimed(rule):
    """
    The requirements a scoring rule claims to detect.

    `serves_sir:` is the name. `serves_eei:` is the name it had before the
    requirements tree moved to PIR / indicator / SIR, and it is still read so
    that a domain which has not been converted keeps working untouched - the
    second domain cannot be edited from this repo at all. Fallback, never a
    flag day. A rule declaring both is a mistake, so both are taken.
    """
    return (rule.get("serves_sir") or []) + (rule.get("serves_eei") or [])


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
            out.update(_claimed(tier))
            break                      # first qualifying tier wins, as in scoring

    for m in scoring.get("multipliers", []) or []:
        if _eval_atom(m["when"], groups, matcher, scopes, text_l):
            out.update(_claimed(m))

    for f in scoring.get("floors", []) or []:
        if _eval_atom(f["when"], groups, matcher, scopes, text_l):
            out.update(_claimed(f))

    for f in (force_rules if force_rules is not None
              else scoring.get("force_surface", []) or []):
        if _eval_atom(f["when"], groups, matcher, scopes, text_l):
            out.update(_claimed(f))

    return sorted(out)


# ------------------------------------------------------------------
# Sigma-shaped detection: named blocks above, one condition line below
# ------------------------------------------------------------------
def _tokenise(expr):
    """Split a condition line into names, operators and parentheses."""
    return re.findall(r"\(|\)|\b(?:and|or|not)\b|[A-Za-z_][A-Za-z0-9_]*", expr)


def _parse_condition(tokens, pos=0):
    """
    A three-level grammar, standard precedence: not binds tightest, then and,
    then or.

        expr   := term   (or term)*
        term   := factor (and factor)*
        factor := not factor | ( expr ) | NAME

    Returns (node, next_position). A node is ("name", str), ("not", node),
    ("and", [nodes]) or ("or", [nodes]).
    """
    def factor(i):
        if i >= len(tokens):
            raise ValueError("condition ended unexpectedly")
        tok = tokens[i]
        if tok == "not":
            node, i = factor(i + 1)
            return ("not", node), i
        if tok == "(":
            node, i = expr(i + 1)
            if i >= len(tokens) or tokens[i] != ")":
                raise ValueError("condition has an unclosed '('")
            return node, i + 1
        if tok in ("and", "or", ")"):
            raise ValueError(f"condition has {tok!r} where a block name was expected")
        return ("name", tok), i + 1

    def term(i):
        node, i = factor(i)
        parts = [node]
        while i < len(tokens) and tokens[i] == "and":
            node, i = factor(i + 1)
            parts.append(node)
        return (parts[0] if len(parts) == 1 else ("and", parts)), i

    def expr(i):
        node, i = term(i)
        parts = [node]
        while i < len(tokens) and tokens[i] == "or":
            node, i = term(i + 1)
            parts.append(node)
        return (parts[0] if len(parts) == 1 else ("or", parts)), i

    node, i = expr(pos)
    if i != len(tokens):
        raise ValueError(f"condition has trailing tokens: {' '.join(tokens[i:])}")
    return node, i


_CONDITION_CACHE = {}


def _condition(expr):
    node = _CONDITION_CACHE.get(expr)
    if node is None:
        toks = _tokenise(str(expr))
        if not toks:
            raise ValueError("condition is empty")
        node, _ = _parse_condition(toks)
        _CONDITION_CACHE[expr] = node
    return node


def eval_detection(detection, groups, matcher, scopes, text_l):
    """
    Evaluate a Sigma-shaped detection block.

    A detection is named blocks plus one `condition:` line naming them:

        detection:
          technique_code:
            pattern: '\bT\d{4}(\.\d{3})?\b'
          listicle:
            keywords: [top 10, biggest, ranked]
            scope: title
          condition: technique_code and not listicle

    WHY THIS SHAPE. The old one nested the logic inline, so a rule was four
    levels of any/all/not and you had to hold the structure in your head. Here
    the blocks are named pieces and the condition is a sentence. It is the
    same evaluator underneath; only the writing changes.

    A block is any rule atom: `keywords`, `group`, `pattern`, `proximity`, or
    a nested `any`/`all`/`not`. A `proximity` block may name OTHER BLOCKS in
    the same detection as its `a` and `b`, which keeps a rule self-contained.

    A condition naming a block that does not exist RAISES. A silent false
    would report the requirement as unanswered forever with nothing saying why.
    """
    if not isinstance(detection, dict):
        raise ValueError("detection must be a mapping of named blocks plus "
                         "a `condition:` line")
    if "condition" not in detection:
        raise ValueError("detection has no `condition:` line naming which of "
                         f"its blocks must match: {sorted(detection)}")
    blocks = {k: v for k, v in detection.items() if k != "condition"}
    if not blocks:
        raise ValueError("detection declares a condition but no blocks")

    # A proximity block may reference sibling blocks rather than global groups.
    # Resolve those to term lists first, so `a:` and `b:` mean the same thing
    # whether they name a group or a `keywords` block in this rule.
    local = dict(groups)
    for name, blk in blocks.items():
        if isinstance(blk, dict) and "keywords" in blk:
            local[name] = blk["keywords"] or []

    cache = {}

    def value(name):
        if name not in cache:
            if name not in blocks:
                raise ValueError(
                    f"condition names {name!r}, which is not a block in this "
                    f"detection. Blocks here: {sorted(blocks)}")
            cache[name] = _eval_atom(blocks[name], local, matcher, scopes, text_l)
        return cache[name]

    def walk(node):
        kind = node[0]
        if kind == "name":
            return value(node[1])
        if kind == "not":
            return not walk(node[1])
        if kind == "and":
            return all(walk(x) for x in node[1])
        return any(walk(x) for x in node[1])

    return walk(_condition(detection["condition"]))


def logsource_match(rule_ls, art_ls):
    """
    Does the article come from the kind of source this rule needs?

    Both sides declare the same two axes. `any` on either side matches
    anything, which is how a rule that genuinely reads everything - a MITRE
    technique identifier turns up wherever it turns up - says so out loud
    rather than by omission.

    AN UNKNOWN ARTICLE DOES NOT MATCH A SCOPED RULE. If the sensor that
    collected it is not in the manifest any more, we cannot confirm it came
    from the right kind of source, and guessing yes is how a rule for a breach
    registry ends up reading press. The coverage report counts these
    separately so the number is visible rather than absorbed.
    """
    wanted = {a: rule_ls.get(a) for a in ("scope", "kind")} if rule_ls else {}
    wanted = {a: v for a, v in wanted.items() if v not in (None, "any")}
    if not wanted:
        # Declares nothing, or `any` on both axes: it reads everything,
        # including an article whose sensor is no longer in the manifest.
        return True
    if art_ls is None:
        return False
    return all(art_ls.get(a) == v for a, v in wanted.items())


def requirement_coverage(art, requirements, scoring, force_rules=None,
                         detectable=None, sensor_classes=None):
    """
    Which requirements this one article satisfied, and what that leaves.

    TWO WAYS A REQUIREMENT CAN BE SATISFIED, and they are deliberately
    different jobs:

      `detect:` on the requirement itself - an expression written to answer
                THAT FACT, in the same atom language the scoring rules use.
                It does not have to change any score. A MITRE ATT&CK technique
                code is a one-line pattern and should never move a score, so
                no scoring rule would ever want to own it.

      `serves_sir:` on a scoring rule - a rule that fired and claims it can
                honestly attest the requirement. This is the older path and it
                stays, because where a scoring rule genuinely IS the detector,
                writing the expression twice would be two copies of one fact.

    The two are a union. A requirement reachable both ways is satisfied by
    either.

    AN INDICATOR IS NOT A COUNT. `satisfied_by: all` means its requirements are
    components, so every one must be present. `satisfied_by: any` means they
    are alternative routes to one fact, so one is enough. A report that treated
    both as a percentage would call them both half answered and be wrong about
    one of them.

    FOUR STATES PER INDICATOR, because one silence would hide three different
    situations:
      satisfied       every requirement that could be tested passed, and every
                      requirement under it could be tested
      needs_detector  everything testable passed, but at least one requirement
                      under the same `all` has no detector yet. The gap is a
                      detector to write, not a quiet week.
      unsatisfied     the test ran and did not pass
      no_detector     nothing under it can be tested at all - no requirement
                      has a `detection:` block and none is claimed by a
                      scoring rule. This is a build gap, NOT a quiet week, and
                      counting it as a miss would make collection look worse
                      than it is.

    `needs_detector` replaces `needs_analyst`, which asked whether a person
    had to decide. Nothing declares that any more: every requirement is
    machine decidable and `status: blocked` names the input a rule is waiting
    for. The old `all` arithmetic ALSO had a defect this fixes - it required a
    hit from every requirement under the indicator including ones nothing
    could test, so an indicator with one working detector and one unwritten
    one read `unsatisfied`, which is a miss, when the honest answer is that
    half of it was never built.

    `detectable` is the set of requirement ids some scoring rule COULD claim,
    computed once per run by `detectable_requirements`. Passing it is what
    separates "nothing matched" from "nothing could".
    """
    groups = scoring["groups"]
    matcher = make_matcher(scoring.get("word_boundary_terms"))
    _title, scopes, text_l = _scopes(art)

    by_rule = set(satisfied_elements(art, scoring, force_rules))
    detectable = set(detectable if detectable is not None else by_rule)
    # The kind of source this article came from. `source` holds the sensor's
    # own URL - core/acolyte.py passes it at both call sites - so this is an
    # exact lookup, not an inference.
    art_ls = (sensor_classes or {}).get(str(art.get("source", "")))

    met, tested = set(), set()
    for pir in (requirements or {}).get("pirs", []) or []:
        for ind in pir.get("indicators", []) or []:
            for sir in ind.get("sirs", []) or []:
                sid = sir.get("id")
                if not sid:
                    continue
                # `detection:` is the Sigma shape - named blocks plus a
                # condition line. `detect:` was the first shape, a bare atom,
                # and is still read so nothing has to convert on a flag day.
                det = sir.get("detection")
                if det is not None:
                    detectable.add(sid)
                    # THE LOGSOURCE IS THE FIRST FILTER, before any term is
                    # matched, exactly as it is in Sigma. A rule that needs a
                    # breach registry does not get to read press.
                    if not logsource_match(sir.get("logsource"), art_ls):
                        continue
                    tested.add(sid)
                    if eval_detection(det, groups, matcher, scopes, text_l):
                        met.add(sid)
                elif sir.get("detect") is not None:
                    tested.add(sid)
                    detectable.add(sid)
                    if _eval_atom(sir["detect"], groups, matcher, scopes, text_l):
                        met.add(sid)
                if sid in by_rule:
                    met.add(sid)
                    tested.add(sid)

    indicators = {}
    for pir in (requirements or {}).get("pirs", []) or []:
        for ind in pir.get("indicators", []) or []:
            ids = [s.get("id") for s in (ind.get("sirs", []) or [])
                   if s.get("id")]
            reachable = [i for i in ids if i in detectable]
            unbuilt = [i for i in ids if i not in detectable]
            mode = ind.get("satisfied_by", "any")
            if not reachable:
                state = "no_detector"
            else:
                hits = [i for i in reachable if i in met]
                if mode == "all":
                    if len(hits) != len(reachable):
                        state = "unsatisfied"
                    elif unbuilt:
                        state = "needs_detector"
                    else:
                        state = "satisfied"
                else:
                    # Alternative routes to one fact. One is enough, and an
                    # unwritten sibling is thinner sourcing, not a hole.
                    state = "satisfied" if hits else "unsatisfied"
            indicators[ind["id"]] = state

    return {"sirs_met": sorted(met), "sirs_tested": sorted(tested),
            "indicators": indicators}


def detectable_requirements(requirements, scoring):
    """
    Every requirement id something COULD satisfy, whatever this article says.

    The union of requirements carrying a `detect:` block and requirements named
    by any scoring rule. Computed once per run, then handed to
    `requirement_coverage` so a report can say "nothing matched" and "nothing
    could" as different things.
    """
    out = set()
    for coll in ("tiers", "multipliers", "floors", "force_surface"):
        for rule in (scoring.get(coll) or []):
            out.update(_claimed(rule))
    for pir in (requirements or {}).get("pirs", []) or []:
        for ind in pir.get("indicators", []) or []:
            for sir in ind.get("sirs", []) or []:
                if sir.get("id") and (sir.get("detection") is not None
                                      or sir.get("detect") is not None):
                    out.add(sir["id"])
    return out


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
    that is <= now (the ICOD, e.g. Wednesday 0400 America/Los_Angeles).
    NOTE: cutoff_time must be at or before the hour the run STARTS. If the
    declared time has not yet passed when scoring runs, this walks back a
    whole week and the cycle windows on the previous week silently.
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
