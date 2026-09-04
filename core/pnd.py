# Sanctum · core/pnd.py · (Planning & Direction config loader; history via git)
"""
Loads a domain's Planning & Direction (P&D) config.

A domain lives in <repo>/<domain>/ and its P&D is a single Markdown file,
<domain>/pnd.md, that reads like a document but carries the machine-readable
config inside fenced ```yaml blocks. This loader extracts and merges those
blocks; the surrounding prose is ignored by the engines (it's for humans).

Expected top-level keys across the yaml blocks:
  manifest:   host/runtime + storage (base_dir, sensors_file, corpus{...},
              collection{...})
  scoring:    tiers[], multipliers[], groups{}, word_boundary_terms[], settings{}
  production: report_title, sections[], staging_item_target,
              staging_per_section, distributed_item_target, notes.
              Only report_title is read by any engine; the rest inform the
              manual staging/analysis stage.

Portability: base_dir resolves from $SANCTUM_BASE first, then manifest.base_dir,
then the domain folder. Nothing is hardwired to a specific host.
"""

import os
import re
from pathlib import Path

try:
    import yaml
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "Sanctum needs PyYAML to read P&D config. Install it:\n"
        "  pip install pyyaml\n"
        "If the collector runs inside a virtualenv, use that venv's pip."
    ) from e


REPO_ROOT = Path(__file__).resolve().parent.parent
_YAML_BLOCK = re.compile(r"```ya?ml\s*\n(.*?)```", re.DOTALL)
_SENSORS_BLOCK = re.compile(r"```sensors\s*\n(.*?)```", re.DOTALL)


def extract_sensors(md_text):
    """Extract the feed list from a fenced ```sensors block in a pnd.md.

    One URL per line; blank lines and '#' comments ignored. Returns None if
    no sensors block is present (so the loader can fall back to a file).
    """
    blocks = _SENSORS_BLOCK.findall(md_text)
    if not blocks:
        return None
    urls = []
    for block in blocks:
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that REFUSES a mapping with a repeated key.

    PyYAML's default is to take the last one silently. That is how `incident:`
    came to appear twice in cti/vocab.md: sixteen entries were written, fifteen
    parsed, and nothing anywhere said so. A config file whose contents disagree
    with what it looks like is worse than a config file that fails to load.
    """


def _no_duplicate_keys(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise ValueError(
                f"duplicate key {key!r} at line {key_node.start_mark.line + 1} "
                f"of this yaml block. PyYAML would silently keep the last one. "
                f"Merge the two entries, or rename one.")
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicate_keys)


def _deep_merge(a, b, path=()):
    """Merge b into a. Dicts merge; anything else must not be redefined.

    Two yaml blocks declaring `manifest:` is deliberate — that is how the file
    splits by intelligence-cycle stage while still assembling one config. Two
    blocks declaring the same LEAF (a list, a number, a string) is not: one of
    them is dead text that reads as if it were in force. Refuse it.
    """
    for k, v in b.items():
        here = path + (k,)
        if k in a and isinstance(a[k], dict) and isinstance(v, dict):
            _deep_merge(a[k], v, here)
        elif k in a and a[k] != v:
            raise ValueError(
                f"'{'.'.join(here)}' is declared twice with different values "
                f"across yaml blocks. Only mappings may be assembled from more "
                f"than one block; a list or a scalar declared twice means one "
                f"of them is silently dead. Delete the one that is not in force.")
        else:
            a[k] = v
    return a


def parse_pnd(text, is_yaml):
    """Parse a domain file. A .yaml file IS the config; a .md file carries it
    in fenced blocks.

    Both go through _UniqueKeyLoader, so a key declared twice is refused either
    way. The .md path also refuses a leaf redefined ACROSS blocks; a single yaml
    document cannot express that, which is one fewer way to be wrong.
    """
    if is_yaml:
        data = yaml.load(text, Loader=_UniqueKeyLoader)
        if not isinstance(data, dict):
            raise ValueError("pnd.yaml is not a mapping")
        return data
    return extract_config(text)


def extract_config(md_text):
    """Extract + merge every fenced yaml block from a pnd.md into one dict.

    Duplicate keys are refused in both places they can hide: inside one block
    (_UniqueKeyLoader) and across blocks (_deep_merge). Both were silent before
    2026-09-01 and both had already cost a wrong count.
    """
    merged = {}
    blocks = _YAML_BLOCK.findall(md_text)
    if not blocks:
        raise ValueError("no ```yaml config blocks found in P&D markdown")
    for i, block in enumerate(blocks):
        try:
            data = yaml.load(block, Loader=_UniqueKeyLoader)
        except (yaml.YAMLError, ValueError) as e:
            raise ValueError(f"yaml block #{i+1} failed to parse: {e}") from e
        if data is None:
            continue
        if not isinstance(data, dict):
            raise ValueError(f"yaml block #{i+1} is not a mapping")
        _deep_merge(merged, data)
    return merged


def _validate(cfg, domain):
    if "manifest" not in cfg:
        raise ValueError(f"[{domain}] P&D missing 'manifest' block")
    if "scoring" not in cfg:
        raise ValueError(f"[{domain}] P&D missing 'scoring' block")
    sc = cfg["scoring"]
    for key in ("tiers", "groups", "multipliers"):
        if key not in sc:
            raise ValueError(f"[{domain}] scoring block missing '{key}'")
    # every group referenced by a rule must exist
    groups = set(sc["groups"])
    refs = set()

    def _walk(atom):
        if isinstance(atom, str):
            return
        if "group" in atom:
            refs.add(atom["group"])
        if "proximity" in atom:
            refs.add(atom["proximity"]["a"]); refs.add(atom["proximity"]["b"])
        for k in ("any", "all"):
            if k in atom:
                for x in atom[k]:
                    _walk(x)
        # An excluded group must exist too. A typo inside `not` would otherwise
        # never match anything, silently disabling the exclusion and letting the
        # noise back in with nothing on the page to say so.
        if "not" in atom:
            _walk(atom["not"])

    for t in sc["tiers"]:
        _walk(t.get("require", "always"))
    for m in sc["multipliers"]:
        _walk(m["when"])
    missing = refs - groups
    if missing:
        raise ValueError(f"[{domain}] rules reference undefined groups: {sorted(missing)}")


def load_domain(domain=None, pnd_path=None, repo_root=None):
    """
    Load and validate a domain's P&D. Returns a dict with the parsed blocks
    plus resolved runtime paths:
      { manifest, scoring, production, domain, domain_dir, base_dir,
        sensors_path, corpus_dir, seen_path, seen_titles_path, log_path,
        staging_out }
    """
    root = Path(repo_root) if repo_root else REPO_ROOT
    if pnd_path:
        pnd = Path(pnd_path)
        domain = domain or pnd.parent.name
        domain_dir = pnd.parent
    else:
        if not domain:
            raise ValueError("load_domain requires a domain name or pnd_path")
        domain_dir = root / domain
        # A domain ships EITHER pnd.yaml (config only) or pnd.md (config in
        # fenced blocks). yaml wins if both are present, and that is the only
        # ordering that lets a domain convert without a flag day.
        pnd = domain_dir / "pnd.yaml"
        if not pnd.exists():
            pnd = domain_dir / "pnd.md"
    if not pnd.exists():
        raise FileNotFoundError(f"P&D file not found: {pnd}")

    text = pnd.read_text(encoding="utf-8")
    cfg = parse_pnd(text, is_yaml=(pnd.suffix in (".yaml", ".yml")))
    _validate(cfg, domain)

    manifest = cfg["manifest"]

    # base_dir: env override wins (portability), then manifest, then domain dir.
    base_dir = Path(os.environ.get("SANCTUM_BASE")
                    or manifest.get("base_dir")
                    or domain_dir).expanduser()

    # sensors: absolute path used as-is; relative resolved against the domain dir.
    sensors_file = manifest.get("sensors_file", "config/sensors.txt")
    sensors_path = Path(sensors_file)
    if not sensors_path.is_absolute():
        sensors_path = domain_dir / sensors_path

    # Sensors, in order of preference:
    #   1. manifest.sensors  - a list of records (pnd.yaml). A record carries its
    #      url plus whatever else the domain wants to say about that feed; only
    #      `url` is required.
    #   2. a fenced ```sensors block - one URL per line (pnd.md).
    #   3. the external sensors_file named by the manifest.
    # `sensors` is a flat list of URLs in every case, so a domain can move
    # between shapes without the engine noticing. s2 still uses shape 2.
    #
    # `sensor_records` carries the SAME sources in the same order as dicts, so a
    # record can say something the collector acts on - `kind: page` and `title:`
    # today. Shapes 2 and 3 have nowhere to put those, so they yield {"url": u}
    # and behave exactly as before.
    sensors, sensors_source, records = None, None, None
    declared = manifest.get("sensors")
    if isinstance(declared, list) and declared:
        missing = [i for i, s in enumerate(declared)
                   if not (s.get("url") if isinstance(s, dict) else s)]
        if missing:
            raise ValueError(
                f"[{domain}] manifest.sensors entries at position(s) {missing} "
                f"have no `url`. A record without one is a feed that will never "
                f"be collected and nothing downstream would say so.")
        sensors = [s["url"] if isinstance(s, dict) else s for s in declared]
        records = [dict(s) if isinstance(s, dict) else {"url": s} for s in declared]
        sensors_source = f"{pnd.name} (manifest.sensors)"
    if sensors is None:
        sensors = extract_sensors(text)
        sensors_source = f"{pnd.name} (inline block)"
    if sensors is None:
        sensors = load_sensors(sensors_path) if sensors_path.exists() else []
        sensors_source = str(sensors_path) if sensors else "(none found)"
    if records is None:
        records = [{"url": u} for u in (sensors or [])]

    # A `kind` nobody implements is a setting that silently does nothing, which
    # is the failure mode this apparatus is least able to notice. Refuse it here.
    bad_kind = sorted({str(r.get("kind")) for r in records
                       if r.get("kind") not in (None, "feed", "page")})
    if bad_kind:
        raise ValueError(
            f"[{domain}] manifest.sensors declares kind {bad_kind}. "
            f"Only `feed` (the default) and `page` exist. A page is re-read every "
            f"run and deduplicated on its content; a feed is walked for items.")

    corpus_dir = base_dir / "corpus"
    result = {
        "manifest": manifest,
        "scoring": cfg["scoring"],
        "production": cfg.get("production", {}),
        "requirements": cfg.get("requirements", {}),
        "domain": domain,
        "domain_dir": domain_dir,
        "base_dir": base_dir,
        "sensors": sensors,
        "sensor_records": records,
        "sensors_source": sensors_source,
        "sensors_path": sensors_path,
        "corpus_dir": corpus_dir,
        "seen_path": base_dir / "seen.txt",
        "seen_titles_path": base_dir / "seen_titles.txt",
        "log_path": base_dir / "logs" / "collector.log",
        "staging_out": base_dir / "staging_candidates.md",
    }
    return result


def load_sensors(sensors_path):
    """Read a sensors file: one URL per line, '#' comments and blanks ignored."""
    lines = Path(sensors_path).read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]


if __name__ == "__main__":
    # Tiny helper: `python -m core.pnd --domain cti --get manifest.corpus.rclone_remote`
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain")
    ap.add_argument("--pnd")
    ap.add_argument("--get", help="dotted key path into the manifest/config")
    args = ap.parse_args()
    d = load_domain(domain=args.domain, pnd_path=args.pnd)
    if args.get:
        node = {"manifest": d["manifest"], "scoring": d["scoring"], "production": d["production"]}
        for part in args.get.split("."):
            node = node[part]
        print(node)
    else:
        print(json.dumps({k: str(v) for k, v in d.items()
                          if k not in ("scoring", "production", "manifest")}, indent=2))
