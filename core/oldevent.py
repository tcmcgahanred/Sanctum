"""
Sanctum · core/oldevent.py · old events in new coverage

LABELS ONLY. Nothing here touches a score, a tier, a force-surface rule, the
ordering or the surface-vs-drop decision. Two labels are printed on candidates
in the staging document so the analyst can see, before writing an entry, that a
fresh article may be about an old event:

  SECONDARY COVERAGE  the headline uses words that report on an event after
                      the fact (a lawsuit, a settlement, an investigation
                      opened). Verify the event date before treating it as
                      this week's incident.
  ALREADY REPORTED?   the headline names the same organisation and incident as
                      an entry in a recent published edition. The matched
                      entry is printed beside the label, so a wrong match is
                      visible at a glance.

Work order from the briefing chat, 2026-10-28. Both labels were measured over
the four CTI cycles 7 to 28 October 2026 before they were built, with every
label read: secondary coverage 21 labels, 20 about an older event; already
reported 10 labels, 7 correct. A third check, "first seen in the corpus", was
measured and NOT built: 37 labels, 25 wrong, because title matching cannot tell
"a new event at the same vendor or by the same gang" from "the same event
again". See logs/CHANGELOG.md, 2026-10-28.

A domain opts in by declaring `old_event:` under
`production.staging_annotations`. Absent, nothing here runs.
"""
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.rules import _compiled


def secondary_hit(art, spec):
    """Return the matched words when the headline reads as secondary coverage.

    `spec` is the `secondary_coverage` block: a pattern and a scope, in the
    same `{match, scope}` form a detector uses. The match text is returned so
    the staging document can say WHICH word fired, which is what lets the
    analyst judge the label in one glance.
    """
    if not spec:
        return None
    pat = spec.get("pattern") or {}
    expr = pat.get("match") if isinstance(pat, dict) else pat
    if not expr:
        return None
    scope = (pat.get("scope") if isinstance(pat, dict) else None) or "title"
    if scope == "title":
        hay = str(art.get("title", ""))
    elif scope == "text":
        hay = str(art.get("text", ""))
    else:
        hay = f"{art.get('title', '')}  {art.get('text', '')}"
    m = _compiled(expr).search(hay)
    return m.group(0).lower() if m else None


_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'-]*")
_CAP = re.compile(r"[A-Z][A-Za-z0-9'-]+")
# A word immediately after a lowercase word, comma or semicolon and a space is
# mid-sentence, so its capital letter is a choice the writer made.
_MID = re.compile(r"(?<=[a-z,;] )([A-Za-z][A-Za-z0-9'-]+)")
_CVE = re.compile(r"cve-\d{4}-\d+", re.I)
_ENTRY = re.compile(r"^\*\*(\d{8})-([A-Z]+)\s+[—-]\s+(.+?)\*\*")


def _strip_suffix(title, seps):
    t = str(title or "").strip()
    for sep in seps:
        if sep in t:
            parts = t.split(sep)
            if len(parts[-1]) <= 40:
                t = sep.join(parts[:-1])
    return t


def _tokens(title, seps):
    t = _strip_suffix(title, seps)
    return {w for w in _TOKEN_RE.findall(t.lower()) if len(w) > 3}


def _collected(art):
    try:
        d = datetime.fromisoformat(art.get("collected", ""))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


class PriorEditions:
    """Match candidate headlines against entries in recent published editions.

    ENTITY PLUS INCIDENT, per the work order. A candidate and an entry must
    share at least two content words, at least one of them a NAME, and pass the
    same IDF-weighted similarity the near-duplicate grouping uses.

    A word is a NAME only if (a) fewer than 1% of corpus headlines use it and
    (b) article bodies write it capitalised mid-sentence at least 80% of the
    time. Test (b) exists because Title Case headlines capitalise every word:
    the first measured version trusted headline capitals and paired
    "Individuals" across unrelated breaches.

    Two headlines naming different CVE identifiers are never the same event.

    The statistics are taken over the whole corpus, as measured. Reading every
    corpus record costs about a minute on the collector at 16,000 articles.
    """

    def __init__(self, corpus_dir, editions_dir, spec, grouping, seps,
                 now=None):
        self.seps = seps
        self.weeks = int(spec.get("weeks", 6))
        self.entity_df = float(spec.get("entity_df", 0.01))
        self.name_ratio = float(spec.get("name_ratio", 0.8))
        name_days = int(spec.get("name_days", 30))
        self.thr = float(grouping.get("similarity", 0.15))
        self.minev = float(grouping.get("min_evidence", 8.0))
        now = now or datetime.now(timezone.utc)
        body_from = now - timedelta(days=name_days)

        df, n = {}, 0
        self.capc, self.lowc = {}, {}
        corpus_dir = Path(corpus_dir)
        if corpus_dir.exists():
            for day in sorted(corpus_dir.iterdir()):
                if not day.is_dir():
                    continue
                for jf in day.glob("*.json"):
                    try:
                        art = json.loads(jf.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    n += 1
                    for w in _tokens(art.get("title", ""), seps):
                        df[w] = df.get(w, 0) + 1
                    c = _collected(art)
                    if c is not None and c >= body_from:
                        self._count_case(str(art.get("text", ""))[:20000])
        self.df, self.n = df, n
        self.idf = {w: math.log(n / (1 + c)) for w, c in df.items()} if n else {}

        self.entries = []
        editions_dir = Path(editions_dir)
        if editions_dir.exists():
            for f in sorted(editions_dir.glob("*.md")):
                for ln in f.read_text(encoding="utf-8").splitlines():
                    m = _ENTRY.match(ln)
                    if not m:
                        continue
                    d = datetime.strptime(m.group(1), "%Y%m%d").replace(
                        tzinfo=timezone.utc)
                    self.entries.append((d, f"{m.group(1)}-{m.group(2)}",
                                         m.group(3), _tokens(m.group(3), seps)))

    def _count_case(self, text):
        for m in _MID.finditer(text):
            w = m.group(1)
            k = w.lower()
            if k.endswith("'s"):
                k = k[:-2]
            if w[0].isupper():
                self.capc[k] = self.capc.get(k, 0) + 1
            else:
                self.lowc[k] = self.lowc.get(k, 0) + 1

    def _is_name(self, k):
        c, l = self.capc.get(k, 0), self.lowc.get(k, 0)
        if c + l == 0:
            return True            # never in a body: rare, kept as a name
        return c / (c + l) >= self.name_ratio

    def names(self, title):
        out = set()
        for i, w in enumerate(_strip_suffix(title, self.seps).split()):
            if i == 0:
                continue
            m = _CAP.match(w)
            if not m:
                continue
            k = m.group(0).lower()
            if k.endswith("'s"):
                k = k[:-2]
            if (len(k) > 3 and self.df.get(k, 0) < max(self.entity_df * self.n, 10)
                    and self._is_name(k)):
                out.add(k)
        return out

    def _sim(self, a, b):
        inter = sum(self.idf.get(w, 0) for w in a & b)
        if inter < self.minev:
            return 0.0
        uni = sum(self.idf.get(w, 0) for w in a | b)
        return inter / uni if uni else 0.0

    def hit(self, title, ref):
        """Best-matching entry (id, headline) from editions dated in the
        `weeks` before `ref`, or None."""
        names = self.names(title)
        if not names:
            return None
        ts = _tokens(title, self.seps)
        cves = {x.lower() for x in _CVE.findall(title)}
        best, best_s = None, 0.0
        for d, eid, head, et in self.entries:
            if not (ref - timedelta(weeks=self.weeks) <= d < ref):
                continue
            if len(ts & et) < 2 or not (names & et):
                continue
            ecves = {x.lower() for x in _CVE.findall(head)}
            if cves and ecves and not (cves & ecves):
                continue
            s = self._sim(ts, et)
            if s >= self.thr and s > best_s:
                best, best_s = (eid, head), s
        return best
