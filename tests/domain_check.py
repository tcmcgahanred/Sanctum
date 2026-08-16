#!/usr/bin/env python3
"""
Sanctum · tests/domain_check.py · domain-file guardrail

Enforces tenet 3: "Domain files declare, they never behave."

WHY THIS EXISTS
---------------
Tenet 2 promises a domain-agnostic engine: point Sanctum at a new domain and it
performs the same as on any other. That promise only holds while domain files
stay inert. A domain file that can *act* — an if-statement, a helper function, a
scoring tweak — moves domain knowledge out of the config and into behavior, and
the shared engine quietly stops being shared. Nobody notices until the second
domain behaves differently from the first for reasons nobody can point at.

While a domain file was YAML-inside-markdown, that was impossible by
construction: the format could not express logic. Python domain files are more
legible — a comment sits against the setting it explains instead of drifting
away from it in a prose section — but they hand back the ability to misbehave.
This check is the guardrail that buys the legibility without the risk.

WHAT IS ALLOWED
---------------
  - Comments and a module docstring (this is the point of the format).
  - Assignments whose value is a literal: strings, numbers, booleans, None,
    dicts, lists, tuples, sets, and nestings of those.
  - A reference to a name assigned earlier in the same file, so a shared term
    list can be defined once and used in several places.

WHAT IS REFUSED
---------------
  Imports, function and class definitions, if/for/while/try, calls of any kind,
  lambdas, comprehensions, ternaries, attribute access, subscripting, f-strings
  with expressions in them, and arithmetic.

  The rule is deliberately strict. Some refused constructs are harmless in
  isolation (joining two lists with `+`, say). Strictness is cheap to loosen
  once a real need appears, and expensive to reimpose after a domain file has
  grown a brain. Tenet 10: prove before you build.

USAGE
     tests/domain_check.py                    # check every domain file in the repo
     tests/domain_check.py path/to/pnd.py     # check specific files (incl. out-of-tree)
     tests/domain_check.py --staged           # check only what a commit would publish

EXIT CODES
     0  clean
     1  a domain file contains behavior, or a named file could not be read

Markdown domain files are reported as skipped: YAML cannot express logic, so
there is nothing for this check to find in them.
"""

import ast
import subprocess
import sys
from pathlib import Path

# Value nodes that describe data and nothing else.
LITERAL_NODES = (ast.Constant, ast.Dict, ast.List, ast.Tuple, ast.Set)

# Plain-language explanation per construct. The audience is whoever is standing
# up a domain, who may not be a programmer and should not need to be.
WHY = {
    "Import": "imports pull in outside behavior — a domain file must stand alone",
    "ImportFrom": "imports pull in outside behavior — a domain file must stand alone",
    "FunctionDef": "a function is behavior; behavior belongs in the engine",
    "AsyncFunctionDef": "a function is behavior; behavior belongs in the engine",
    "ClassDef": "a class is behavior; behavior belongs in the engine",
    "If": "a condition makes the file act differently in different situations",
    "For": "a loop is logic; write the values out instead",
    "While": "a loop is logic; write the values out instead",
    "Try": "error handling implies something can fail — settings cannot fail",
    "With": "this opens a resource; a domain file only describes settings",
    "Call": "calling something runs code at load time",
    "Lambda": "a lambda is a function in disguise",
    "IfExp": "a condition makes the file act differently in different situations",
    "ListComp": "a comprehension is a loop",
    "DictComp": "a comprehension is a loop",
    "SetComp": "a comprehension is a loop",
    "GeneratorExp": "a comprehension is a loop",
    "Attribute": "reaching into another object couples this file to code",
    "Subscript": "indexing computes a value instead of stating it",
    "BinOp": "arithmetic or concatenation computes a value instead of stating it",
    "BoolOp": "and/or is a condition",
    "Compare": "a comparison is a condition",
    "JoinedStr": "an f-string computes text; write the finished text out instead",
    "Await": "a domain file does no work, so it cannot wait on any",
    "Global": "this reaches outside the file",
    "Nonlocal": "this reaches outside the file",
    "Assert": "an assertion is a condition",
    "Raise": "raising is behavior",
    "Delete": "a domain file states what is, not what to remove",
}


class Violation:
    def __init__(self, line, construct, why):
        self.line = line
        self.construct = construct
        self.why = why


def _describe(node):
    """Human name for a node, plus why it is refused."""
    name = type(node).__name__
    return name, WHY.get(name, "this is behavior, not a setting")


def _check_value(node, defined, out):
    """Walk a value expression; record anything that is not inert data."""
    if isinstance(node, ast.Constant):
        return

    # -3 and +0.5 arrive as a unary operator wrapped around a number.
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        if isinstance(node.operand, ast.Constant) and isinstance(
            node.operand.value, (int, float)
        ):
            return

    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for elt in node.elts:
            _check_value(elt, defined, out)
        return

    if isinstance(node, ast.Dict):
        for k, v in zip(node.keys, node.values):
            if k is None:  # {**other} — a merge, which computes a value
                out.append(Violation(node.lineno, "dict merge",
                                     "merging computes a value instead of stating it"))
                continue
            _check_value(k, defined, out)
            _check_value(v, defined, out)
        return

    # A reference to something defined earlier in this same file. This is how a
    # shared term list gets used in more than one place without being retyped.
    if isinstance(node, ast.Name):
        if node.id not in defined:
            out.append(Violation(
                node.lineno, f"reference to '{node.id}'",
                "this name is not defined earlier in the file, so it reaches outside it"))
        return

    if isinstance(node, ast.Starred):
        out.append(Violation(node.lineno, "unpacking",
                             "unpacking computes a value instead of stating it"))
        return

    construct, why = _describe(node)
    out.append(Violation(getattr(node, "lineno", 0), construct, why))


def check_source(src, filename="<domain file>"):
    """Return a list of Violations. Empty list means the file is inert."""
    try:
        tree = ast.parse(src, filename=filename)
    except SyntaxError as e:
        return [Violation(e.lineno or 0, "syntax error", str(e.msg))]

    out = []
    defined = set()

    for stmt in tree.body:
        # A bare string on its own line is a docstring or a section note. Fine.
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) \
                and isinstance(stmt.value.value, str):
            continue

        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    defined.add(target.id)
                elif isinstance(target, (ast.Tuple, ast.List)):
                    for t in target.elts:
                        if isinstance(t, ast.Name):
                            defined.add(t.id)
                else:
                    c, why = _describe(target)
                    out.append(Violation(stmt.lineno, f"assignment to {c}", why))
            _check_value(stmt.value, defined, out)
            continue

        if isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Name):
                defined.add(stmt.target.id)
            if stmt.value is not None:
                _check_value(stmt.value, defined, out)
            continue

        if isinstance(stmt, ast.AugAssign):
            out.append(Violation(stmt.lineno, "+= assignment",
                                 "this modifies a value instead of stating it"))
            continue

        construct, why = _describe(stmt)
        out.append(Violation(stmt.lineno, construct, why))

    return out


def is_domain_file(path):
    """
    A domain file is a domain's P&D file: <domain>/pnd.md or <domain>/pnd.py.

    `core/pnd.py` is NOT one — it is the engine that *loads* domain files, and
    it is full of legitimate logic. Name collision, opposite meaning.
    """
    p = Path(path)
    if p.name not in ("pnd.py", "pnd.md"):
        return False
    return "core" not in p.parts


def discover(repo_root):
    """Every domain file tracked in the repo."""
    try:
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=repo_root, capture_output=True,
            text=True, check=True).stdout.split("\n")
    except Exception:
        tracked = [str(p.relative_to(repo_root)) for p in repo_root.rglob("pnd.*")]
    return [f for f in tracked if f and is_domain_file(f)]


def staged(repo_root):
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=repo_root, capture_output=True, text=True)
    return [f for f in r.stdout.split("\n") if f and is_domain_file(f)]


def main(argv):
    try:
        repo_root = Path(subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True,
            text=True, check=True).stdout.strip())
    except Exception:
        repo_root = Path.cwd()

    explicit = [a for a in argv if not a.startswith("--")]
    if explicit:
        files, scope = explicit, "named file(s)"
    elif "--staged" in argv:
        files, scope = staged(repo_root), "staged changes"
    else:
        files, scope = discover(repo_root), "all domain files"

    if not files:
        print(f"domain-check: no domain files to scan ({scope})")
        return 0

    failed = 0
    checked = 0
    skipped = []

    for f in files:
        p = Path(f)
        if not p.is_absolute():
            p = repo_root / f
        if p.suffix != ".py":
            skipped.append(f)
            continue
        try:
            src = p.read_text(encoding="utf-8")
        except Exception as e:
            print(f"domain-check: BLOCKED — cannot read {f}: {e}", file=sys.stderr)
            failed += 1
            continue

        checked += 1
        violations = check_source(src, filename=str(f))
        if not violations:
            continue

        if failed == 0:
            print("domain-check: BLOCKED — a domain file contains behavior\n",
                  file=sys.stderr)
        failed += 1
        print(f"  {f}", file=sys.stderr)
        for v in violations:
            print(f"    line {v.line}: {v.construct} — {v.why}", file=sys.stderr)
        print(file=sys.stderr)

    if failed:
        print(
            "Tenet 3: domain files declare, they never behave.\n"
            "A domain file may contain settings, comments, and references to a\n"
            "value defined earlier in the same file. Anything that computes,\n"
            "decides, or loops belongs in the engine, where every domain gets it.\n\n"
            "Deliberate override: git commit --no-verify",
            file=sys.stderr)
        return 1

    note = f", {len(skipped)} markdown domain file(s) skipped" if skipped else ""
    print(f"domain-check: clean ({checked} file(s) scanned{note})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
