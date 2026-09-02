#!/usr/bin/env python3
"""
Sanctum · tools/vocab_check.py · the vocabulary guard

Checks a domain's word lists for the decay modes that manual review does not
catch. See ../docs/VOCABULARY.md for the method this enforces.

WHY THIS EXISTS
---------------
Vocabulary is the highest-leverage and least-examined part of Sanctum. Scoring
is visible and gets argued about; word lists are typed once and never read
again. Every failure mode below is SILENT — the group keeps matching something,
so it looks like it works, and detecting the problem means noticing an absence.

This was not a precaution. A completed domain build in another session found
stale word-boundary entries by hand, on the fourth revision, having read the
file three times before that. This tool finds them in a tenth of a second.

WHAT IT CHECKS
--------------
  orphaned boundary term   an entry equal to no live term — dead, and it implies
                           a term is present when it is not              [ERROR]
  empty group              declared but has no terms; any rule referencing it
                           silently never fires                          [ERROR]
  dropped term still live  recorded as DROPPED in vocab.md but still in pnd.md —
                           the exact drift the two-file split prevents   [ERROR]
  redundant boundary term  <=4 chars, where the matcher already applies word
                           boundaries automatically                       [WARN]
  stale group              review date older than the configured interval [WARN]
  unattributed group       no `serves:` and no `role:` — a keyword added here
                           cannot be traced to an intelligence requirement [WARN]
  group consumed by no     declared, holds terms, and no rule anywhere reads
  rule                     it. NOTED instead when vocab.md says it is
                           deliberate and says why                        [WARN]

The first two need no vocab.md. The rest do.

WHY BOUNDARY ENTRIES GO DEAD
----------------------------
`word_boundary_terms` is matched against a WHOLE term string in a group, not
against substrings of one. An entry `hack` does nothing for a group term
`hacked` — the strings are not equal, and `hacked` is long enough to use
substring matching anyway. So an entry survives a term's deletion, and a later
reader reads the boundary list as evidence that term is still live.

USAGE
    tools/vocab_check.py                 # every domain in the repo
    tools/vocab_check.py --tracked-only  # only domains git tracks (the commit gate)
    tools/vocab_check.py cti             # one domain
    tools/vocab_check.py --pnd path/to/pnd.md
    tools/vocab_check.py --today 2026-12-01   # for testing staleness

A gitignored domain — a second effort kept out of the public repo, a stub that
is not operational yet — is still checked on a manual run, because its defects
are real. It is skipped by the commit gate, because it cannot reach the repo the
gate protects.

EXIT CODES
    0  no errors (warnings may still be printed)
    1  at least one error, or a domain failed to load
"""

import argparse
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pnd import load_domain, REPO_ROOT   # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    raise SystemExit("vocab_check needs PyYAML: pip install pyyaml")

_YAML_BLOCK = re.compile(r"```ya?ml\s*\n(.*?)```", re.DOTALL)

# The matcher in core/rules.py applies word boundaries automatically at this
# length or below. Keep these in step: if that threshold ever changes, an
# explicit entry that was redundant becomes load-bearing.
AUTO_BOUNDARY_MAX_LEN = 4

ERROR, WARN, NOTED = "ERROR", "WARN", "NOTED"


class Finding:
    def __init__(self, severity, domain, check, subject, detail):
        self.severity = severity
        self.domain = domain
        self.check = check
        self.subject = subject
        self.detail = detail

    def __str__(self):
        return (f"  {self.severity:<5}  {self.check:<24}  {self.subject}\n"
                f"         {self.detail}")


def load_vocab(vocab_path):
    """
    Parse the `vocab:` block from a domain's vocab.md, OR from its pnd.md when
    the domain keeps everything in one file.

    Two shapes are supported on purpose. `cti` merged its five markdown files
    into one on 2026-09-01; `s2` is git-ignored, cannot be edited from the repo,
    and still keeps a separate vocab.md. A fallback serves both without a flag
    day. Returns {} when neither carries a `vocab:` block — the block is
    optional, and the checks that need it simply do not run. A domain is not
    broken for lacking one; it is only unguarded.
    """
    if not vocab_path.exists():
        for name in ("pnd.yaml", "pnd.md"):
            if (vocab_path.parent / name).exists():
                vocab_path = vocab_path.parent / name
                break
    if not vocab_path.exists():
        return {}
    text = vocab_path.read_text(encoding="utf-8")
    # A .yaml domain file IS one document; a .md one carries fenced blocks.
    if vocab_path.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(text)
        return (data or {}).get("vocab", {}) or {}
    merged = {}
    for i, block in enumerate(_YAML_BLOCK.findall(text)):
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as e:
            raise ValueError(f"{vocab_path.name} yaml block #{i+1}: {e}") from e
        if isinstance(data, dict) and "vocab" in data:
            merged.update(data["vocab"] or {})
    return merged


def _as_date(v):
    """Accept a real date or an ISO string; return None for anything else."""
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    try:
        return datetime.strptime(str(v).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


ROLES = ("elevation", "exclusion", "production", "unused", "gate")


def referenced_groups(cfg):
    """
    Every group named by any rule anywhere in a domain's config.

    Walks the WHOLE loaded config, not just `scoring`. That is deliberate and
    it was learned the hard way: a first pass walked `scoring` and `manifest`
    only, and reported `ttp` as consumed by nothing. `ttp` is consumed — by the
    section suggester, which lives under the separate top-level `production`
    key. A checker that looks only where it expects to find things reports
    absences that are not there, which is worse than not checking at all.
    """
    seen = set()

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("group"), str):
                seen.add(o["group"])
            prox = o.get("proximity")
            if isinstance(prox, dict):
                for side in ("a", "b"):
                    if isinstance(prox.get(side), str):
                        seen.add(prox[side])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for key in ("scoring", "manifest", "production"):
        walk(cfg.get(key))
    return seen


def check_domain(domain, cfg, vocab, today):
    findings = []
    scoring = cfg["scoring"]
    groups = scoring.get("groups") or {}

    # Every live term, lowercased, mapped to the groups holding it.
    live = {}
    for gname, terms in groups.items():
        for t in (terms or []):
            live.setdefault(str(t).strip().lower(), []).append(gname)

    # --- empty groups -------------------------------------------------
    # An empty group is worse than a missing one: core/pnd.py validates that
    # every referenced group EXISTS, so an empty group passes that check and
    # then matches nothing. The rule reads as active and is inert.
    for gname, terms in sorted(groups.items()):
        if not terms:
            findings.append(Finding(
                ERROR, domain, "empty group", gname,
                "declared with no terms — any rule referencing it never fires, "
                "but passes the loader's reference check"))

    # --- padded terms --------------------------------------------------
    # The matcher calls .strip() on every term before matching, so leading or
    # trailing spaces are silently discarded. Someone writing " term " is
    # reaching for word-boundary behaviour and not getting it: after stripping,
    # a term longer than the auto-boundary length falls back to plain substring
    # matching, which is exactly what the padding was meant to prevent.
    for gname, terms in sorted(groups.items()):
        for t in (terms or []):
            raw = str(t)
            stripped = raw.strip()
            if raw == stripped or not stripped:
                continue
            if len(stripped.lower()) <= AUTO_BOUNDARY_MAX_LEN:
                findings.append(Finding(
                    WARN, domain, "padded term", f"{raw!r} in {gname}",
                    f"padding is stripped before matching. Harmless here — "
                    f"{stripped!r} is {len(stripped)} chars, so boundaries apply "
                    f"automatically — but the spaces imply a guard that is not "
                    f"doing the work."))
            else:
                findings.append(Finding(
                    ERROR, domain, "padded term", f"{raw!r} in {gname}",
                    f"padding is stripped before matching, leaving the bare "
                    f"substring {stripped!r} ({len(stripped)} chars, above the "
                    f"<={AUTO_BOUNDARY_MAX_LEN} auto-boundary length). It now "
                    f"matches inside longer words. Add {stripped!r} to "
                    f"word_boundary_terms, or use a more precise term."))

    # --- boundary list drift ------------------------------------------
    for entry in (scoring.get("word_boundary_terms") or []):
        key = str(entry).strip().lower()
        if key not in live:
            findings.append(Finding(
                ERROR, domain, "orphaned boundary term", repr(entry),
                "equal to no live term in any group. The entry does nothing, and "
                "it implies that term is still in the vocabulary."))
        elif len(key) <= AUTO_BOUNDARY_MAX_LEN:
            findings.append(Finding(
                WARN, domain, "redundant boundary term", repr(entry),
                f"{len(key)} chars — the matcher applies boundaries automatically "
                f"at <={AUTO_BOUNDARY_MAX_LEN}. Entry adds nothing "
                f"(live in: {', '.join(sorted(set(live[key])))})."))

    # --- dropped terms that are still live ----------------------------
    for rec in (vocab.get("dropped") or []):
        if not isinstance(rec, dict):
            continue
        term = str(rec.get("term", "")).strip().lower()
        if term and term in live:
            findings.append(Finding(
                ERROR, domain, "dropped term still live", repr(rec.get("term")),
                f"recorded as dropped in vocab.md but still present in pnd.md "
                f"(group: {', '.join(sorted(set(live[term])))}). "
                f"Remove it from pnd.md, or remove the dropped record."))

    gmeta = vocab.get("groups") or {}

    # --- requirement attribution ---------------------------------------
    # WHY. A keyword lands in a group, and the rules that consume that group
    # decide which intelligence requirement an item can answer. So the group IS
    # the attribution — but nothing said so, and the mapping could only be
    # recovered by walking every rule tree by hand across two files. A fact that
    # must be derived is a fact that will eventually be derived wrongly; on
    # 2026-08-26 it was, twice, in one session.
    #
    # Each group declares exactly one of:
    #     serves: [PIR-1]     it decides WHICH requirement an item answers
    #     role: elevation     it changes rank, never which requirement
    #     role: exclusion     it appears only under a `not`
    #     role: production    it shapes the product, not the score
    #     role: unused        consumed by no rule, on purpose (needs a reason)
    #     role: gate          a precondition every item must pass; adds no weight
    #
    # WARN, never ERROR. An unattributed group is documentation debt, not a
    # broken engine, and a gate that blocks a commit over documentation gets
    # --no-verify'd — the failure that retired the scrub check on 2026-08-23.
    #
    # Silent until the domain has declared at least one, so a domain that has
    # never used the convention is not buried in warnings on the first run.
    # Same bootstrap rule as the review dates below.
    declared_any = any(
        (gmeta.get(g) or {}).get("serves") or (gmeta.get(g) or {}).get("role")
        for g in groups)
    if declared_any:
        for gname in sorted(groups):
            meta = gmeta.get(gname) or {}
            serves, role = meta.get("serves"), meta.get("role")
            if serves and role:
                findings.append(Finding(
                    WARN, domain, "attribution conflict", gname,
                    f"declares both serves={serves!r} and role={role!r}. A group "
                    f"either decides which requirement is answered or it does "
                    f"not. Pick one."))
            elif not serves and not role:
                findings.append(Finding(
                    WARN, domain, "unattributed group", gname,
                    "no `serves:` and no `role:` in vocab.md. Someone adding a "
                    "keyword here cannot tell which intelligence requirement "
                    "they are feeding."))
            elif role and role not in ROLES:
                findings.append(Finding(
                    WARN, domain, "unknown group role", f"{gname}: {role!r}",
                    f"not one of {', '.join(ROLES)}."))

    # --- groups no rule consumes ---------------------------------------
    # A group nobody reads is invisible: it keeps its terms, keeps its review
    # date, and contributes nothing. `kev` has been in exactly this state since
    # 2026-08-24 — deliberately, recorded in vocab.md, retained because a group
    # that turns out to be two groups gets split rather than half-deleted. That
    # is a fine reason and the point of this check is not to argue with it. The
    # point is that the reason must be WRITTEN, not remembered.
    #
    # Declared and unused prints as NOTED and keeps printing — accepted findings
    # are downgraded, never silenced (standing decision, 2026-08-17).
    #
    # Skipped entirely when the domain declares no rules at all. "Consumed by
    # nothing" is only a finding relative to something — a domain with no tiers
    # and no multipliers is a stub or a fixture being built, not a domain with
    # dead vocabulary, and burying it in warnings is the bootstrap failure this
    # file already guards against for review dates.
    has_rules = bool(scoring.get("tiers") or scoring.get("multipliers"))
    consumed = referenced_groups(cfg) if has_rules else set(groups)
    for gname in sorted(groups):
        if gname in consumed:
            continue
        meta = gmeta.get(gname) or {}
        because = str(meta.get("unused_because", "")).strip()
        if meta.get("role") == "unused" and because:
            findings.append(Finding(
                NOTED, domain, "group consumed by no rule", gname,
                f"declared unused on purpose: {because}"))
        else:
            findings.append(Finding(
                WARN, domain, "group consumed by no rule", gname,
                f"{len(groups[gname] or [])} term(s), referenced by no tier, "
                f"multiplier, floor, force-surface or production rule. Either "
                f"wire it in, or declare `role: unused` with `unused_because:` "
                f"in vocab.md so the next reader knows it is deliberate."))

    # --- declared elements must exist in the requirements tree ---------
    # `serves_eei` is a join, and a join to a typo is worse than no join: the
    # staging document would print an identifier the analyst cannot look up, and
    # nothing would say it was wrong. Silent unless the domain declares any.
    req_path = cfg.get("domain_dir")
    declared = set()
    for coll in ("tiers", "multipliers", "floors", "force_surface"):
        for rule in (scoring.get(coll) or []):
            declared.update(rule.get("serves_eei") or [])
    if declared and req_path:
        # Three shapes, in order of how much they can be trusted:
        #   1. a declared `requirements:` tree — the identifiers ARE the data,
        #      so a typo in the tree is caught rather than silently matched.
        #   2. requirements.md — a split domain. Scraped by regex.
        #   3. pnd.md — a merged-but-still-markdown domain. Also scraped.
        # Scraping matches an identifier anywhere in the file, including inside
        # a sentence that merely mentions it, so shape 1 is strictly better.
        tree, source = None, None
        declared_tree = cfg.get("requirements") or {}
        if declared_tree:
            tree = set()
            for pir in declared_tree.get("pirs", []) or []:
                for sir in pir.get("sirs", []) or []:
                    for eei in sir.get("eeis", []) or []:
                        if eei.get("id"):
                            tree.add(eei["id"])
            source = "the declared requirements tree"
        rp = None
        if tree is None:
            for name in ("requirements.md", "pnd.md"):
                if (Path(req_path) / name).exists():
                    rp = Path(req_path) / name
                    break
            if rp is None:
                findings.append(Finding(
                    WARN, domain, "no requirements tree", "requirements",
                    "rules declare serves_eei but the domain declares no "
                    "requirements tree and has no markdown file to scrape."))
            else:
                tree = set(re.findall(r"EEI-\d+\.\d+\.[a-z]",
                                      rp.read_text(encoding="utf-8")))
                source = rp.name
        if tree is not None:
            for eei in sorted(declared - tree):
                findings.append(Finding(
                    WARN, domain, "element not in the tree", eei,
                    f"declared by a scoring rule but not defined in "
                    f"{source}. The staging document would print an "
                    f"identifier nobody can look up."))

    # --- staleness -----------------------------------------------------
    # A WARN, never an ERROR. A date passing is not a reason to block a commit;
    # it is a reason to look. Blocking here would train people to --no-verify,
    # which switches off every other check with it.
    default_interval = vocab.get("review_interval_days")
    for gname in sorted(groups):
        meta = gmeta.get(gname) or {}
        interval = meta.get("review_interval_days", default_interval)
        reviewed = _as_date(meta.get("reviewed")) if meta.get("reviewed") else None
        if interval is None:
            continue
        if reviewed is None:
            if gmeta:  # only nag once the domain has started recording dates
                findings.append(Finding(
                    WARN, domain, "no review date", gname,
                    "no `reviewed:` date in vocab.md — staleness cannot be "
                    "assessed for this group"))
            continue
        age = (today - reviewed).days
        if age > int(interval):
            findings.append(Finding(
                WARN, domain, "stale group", gname,
                f"last reviewed {reviewed} — {age} days ago, interval is "
                f"{interval}. Decay in a word list is silent; the group keeps "
                f"matching something either way."))

    # --- acknowledged findings -----------------------------------------
    # A guard nobody can satisfy is a guard people route around, and here the
    # route around is `--no-verify`, which disables every other check too. So a
    # finding the domain has consciously accepted is downgraded to NOTED rather
    # than left blocking — but it must be written down, with a reason, and it
    # keeps printing. Silence is not on the menu; that is the whole point.
    accepted = [a for a in (vocab.get("accepted") or []) if isinstance(a, dict)]
    for f in findings:
        for a in accepted:
            if (str(a.get("check", "")).strip().lower() == f.check.lower()
                    and str(a.get("subject", "")).strip() in f.subject):
                f.severity = NOTED
                f.detail = (f"ACCEPTED {a.get('date', 'undated')}: "
                            f"{a.get('reason', 'no reason recorded')}\n"
                            f"         (underlying: {f.detail})")
                break

    return findings


def git_tracked(repo_root, rel_path):
    """
    True if git tracks this path. False on any error — if we cannot ask git,
    we do not get to claim a file is untracked.
    """
    try:
        r = subprocess.run(["git", "-C", str(repo_root), "ls-files", "--error-unmatch",
                            str(rel_path)],
                           capture_output=True, text=True)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def discover_domains(repo_root, tracked_only=False):
    """
    Every <domain>/pnd.yaml or <domain>/pnd.md in the repo, by folder name.

    BOTH shapes are discovered. Looking for only one is how this check silently
    stopped covering cti on 2026-09-01 the moment it converted to yaml: no
    error, no warning, just a domain quietly dropping out of the guard.

    `tracked_only` skips domains git does not track. The commit gate uses it:
    a gitignored domain cannot reach the public repo, so it cannot be the gate's
    business, and blocking a commit over a file git will never see just teaches
    people to reach for --no-verify — which switches off every other check too.

    A manual run still checks everything, because an untracked domain's defects
    are real and the operator should be able to see them.
    """
    out = []
    seen = set()
    for p in sorted(list(repo_root.glob("*/pnd.yaml")) + list(repo_root.glob("*/pnd.md"))):
        if p.parent.name in seen:
            continue
        seen.add(p.parent.name)
        # A leading underscore means "not a domain" (docs/DOMAINS.md). It exists
        # so a folder holding domain-shaped files without being a domain — scratch,
        # a backup, a work in progress — is not reported as broken forever.
        if p.parent.name.startswith("_"):
            continue
        if tracked_only and not git_tracked(repo_root, p.relative_to(repo_root)):
            continue
        out.append(p.parent.name)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Check a Sanctum domain's vocabulary for silent decay.")
    ap.add_argument("domain", nargs="?", help="domain name (default: all in repo)")
    ap.add_argument("--pnd", help="explicit path to a pnd.md (overrides domain)")
    ap.add_argument("--today", help="YYYY-MM-DD, for testing staleness")
    ap.add_argument("--tracked-only", action="store_true",
                    help="skip domains git does not track (used by the commit gate)")
    args = ap.parse_args(argv)

    today = date.today()
    if args.today:
        parsed = _as_date(args.today)
        if parsed is None:
            print(f"vocab_check: --today must be YYYY-MM-DD, got {args.today!r}",
                  file=sys.stderr)
            return 1
        today = parsed

    if args.pnd:
        targets = [(Path(args.pnd).resolve().parent.name, Path(args.pnd).resolve())]
    elif args.domain:
        d = REPO_ROOT / args.domain
        targets = [(args.domain, d / "pnd.yaml" if (d / "pnd.yaml").exists()
                    else d / "pnd.md")]
    else:
        names = discover_domains(REPO_ROOT, tracked_only=args.tracked_only)
        if not names:
            scope = "tracked " if args.tracked_only else ""
            print(f"vocab_check: no {scope}<domain>/pnd.yaml or pnd.md found")
            return 0
        targets = [(n, (REPO_ROOT / n / "pnd.yaml")
                    if (REPO_ROOT / n / "pnd.yaml").exists()
                    else (REPO_ROOT / n / "pnd.md")) for n in names]

    findings, failed = [], False
    for name, pnd_path in targets:
        try:
            cfg = load_domain(pnd_path=str(pnd_path))
            vocab = load_vocab(pnd_path.parent / "vocab.md")
        except Exception as e:
            print(f"vocab_check: [{name}] could not load — {e}", file=sys.stderr)
            failed = True
            continue
        findings.extend(check_domain(name, cfg, vocab, today))

    errors = [f for f in findings if f.severity == ERROR]
    warns = [f for f in findings if f.severity == WARN]
    noted = [f for f in findings if f.severity == NOTED]

    checked = ", ".join(n for n, _ in targets)
    if not findings:
        print(f"vocab_check: PASS — {checked}: no vocabulary defects")
        return 1 if failed else 0

    for group_name, bucket in (("ERRORS", errors), ("WARNINGS", warns),
                               ("ACCEPTED — recorded in vocab.md, still true", noted)):
        if bucket:
            print(f"\n{group_name}")
            for f in bucket:
                print(f)

    print(f"\nvocab_check: {len(errors)} error(s), {len(warns)} warning(s), "
          f"{len(noted)} accepted — across: {checked}")
    if errors:
        print("Errors block the commit. See docs/VOCABULARY.md §5 for what each means.")
    return 1 if (errors or failed) else 0


if __name__ == "__main__":
    sys.exit(main())
