#!/usr/bin/env python3
"""
Sanctum · tests/merge_test.py

One domain, one file — and the guard that makes that safe.

WHY THIS EXISTS
---------------
On 2026-09-01 `cti` merged five markdown files into one `pnd.md` laid out by
intelligence-cycle stage. The merge is only safe because of one property of the
loader: it extracts EVERY fenced yaml block and deep-merges them, so `manifest:`
can appear twice — once in Stage 1 for storage, once in Stage 2 for the
collection settings — and still assemble one config. That is the mechanic the
whole file layout rests on, so it is tested here rather than assumed.

The same mechanic is how a fact can go silently missing. Deep-merge overwrote
without complaint, and PyYAML keeps the LAST of a repeated key without
complaint. Both had already cost something: `incident:` appeared twice in
cti/vocab.md, sixteen entries were written, fifteen parsed, and nothing anywhere
said so. Merging five files into one raises that risk, which is why the guard
landed in the same change as the merge and not after it.

WHAT IS CHECKED
---------------
  split manifest       two blocks declaring `manifest:` assemble into one map
  duplicate in block   a key repeated inside ONE mapping is refused
  duplicate across     a leaf redefined by a later block is refused
  identical across     the same leaf twice with the SAME value is allowed, so a
                       harmless restatement never blocks a commit
  the real domain      cti loads, carries its vocabulary, and still has 55
                       sensors — the merge moved text, never values

    tests/merge_test.py        # exit 0 = one file per domain is safe
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pnd import extract_config, extract_sensors, load_domain   # noqa: E402

FAILURES = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
    if not ok:
        print(f"        got:  {got!r}")
        print(f"        want: {want!r}")
        FAILURES.append(label)


def raises(label, md, needle):
    """The loader must refuse, and its complaint must name the offending key."""
    try:
        extract_config(md)
    except ValueError as e:
        ok = needle in str(e)
        print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
        if not ok:
            print(f"        message did not mention {needle!r}: {e}")
            FAILURES.append(label)
        return
    print(f"  FAIL  {label}")
    print("        it loaded. A silent overwrite is exactly what this guards.")
    FAILURES.append(label)


def run():
    print("\nA config may be assembled from more than one block")
    split = """
```yaml
manifest:
  domain: t
  corpus:
    backend: local
```
prose the engines ignore
```yaml
manifest:
  collection:
    window_days: 7
```
"""
    cfg = extract_config(split)
    check("both halves of manifest are present",
          sorted(cfg["manifest"]), ["collection", "corpus", "domain"])
    check("...and the nested map from the first block survived",
          cfg["manifest"]["corpus"], {"backend": "local"})
    check("...and the one from the second block arrived",
          cfg["manifest"]["collection"], {"window_days": 7})

    print("\nA key repeated inside ONE mapping is refused")
    # The real case: cti/vocab.md declared `incident:` twice. PyYAML kept the
    # second. Sixteen groups were written and fifteen were in force.
    raises("a repeated key does not silently keep the last one", """
```yaml
vocab:
  groups:
    incident: [a]
    other: [b]
    incident: [c]
```
""", "incident")

    print("\nA leaf redefined by a LATER block is refused")
    raises("a redefined list is refused, not overwritten", """
```yaml
scoring:
  word_boundary_terms: [one]
```
```yaml
scoring:
  word_boundary_terms: [two]
```
""", "word_boundary_terms")
    raises("a redefined scalar is refused too", """
```yaml
manifest:
  domain: alpha
```
```yaml
manifest:
  domain: beta
```
""", "manifest.domain")

    # Refusing a restatement that changes nothing would block commits over
    # something harmless, and a guard people route around is worse than none.
    print("\nRestating the same value changes nothing and is allowed")
    same = extract_config("""
```yaml
manifest:
  domain: alpha
```
```yaml
manifest:
  domain: alpha
  base_dir: /tmp
```
""")
    check("the identical value is accepted", same["manifest"]["domain"], "alpha")
    check("...and the block's other keys still land",
          same["manifest"]["base_dir"], "/tmp")

    print("\nThe real domain, after the merge")
    text = (Path(__file__).resolve().parent.parent / "cti" / "pnd.md").read_text()
    real = extract_config(text)
    check("cti/pnd.md carries all four top-level blocks",
          sorted(real), ["manifest", "production", "scoring", "vocab"])
    check("...the vocabulary came with it", len(real["vocab"]["groups"]), 16)
    check("...and every sensor survived", len(extract_sensors(text)), 55)
    cfg = load_domain(domain="cti")
    check("the domain still loads through the normal path",
          cfg["scoring"]["settings"]["recency"]["cutoff_weekday"], "wednesday")

    print()
    if FAILURES:
        print(f"FAIL — {len(FAILURES)} problem(s)")
        for f in FAILURES:
            print(f"    {f}")
        return 1
    print("PASS — one file per domain assembles correctly, and nothing can be "
          "declared twice without saying so")
    return 0


if __name__ == "__main__":
    sys.exit(run())
