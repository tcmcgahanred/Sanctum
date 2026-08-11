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
  production: report_title, sections[], item_target, notes (informs the
              staging/analysis stage)

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
        "  /opt/ravenor/venv/bin/pip install pyyaml   (or: pip install pyyaml)"
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


def _deep_merge(a, b):
    for k, v in b.items():
        if k in a and isinstance(a[k], dict) and isinstance(v, dict):
            _deep_merge(a[k], v)
        else:
            a[k] = v
    return a


def extract_config(md_text):
    """Extract + merge every fenced yaml block from a pnd.md into one dict."""
    merged = {}
    blocks = _YAML_BLOCK.findall(md_text)
    if not blocks:
        raise ValueError("no ```yaml config blocks found in P&D markdown")
    for i, block in enumerate(blocks):
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as e:
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
        pnd = domain_dir / "pnd.md"
    if not pnd.exists():
        raise FileNotFoundError(f"P&D file not found: {pnd}")

    text = pnd.read_text(encoding="utf-8")
    cfg = extract_config(text)
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

    # Sensors: prefer an inline ```sensors block in pnd.md (single-file P&D);
    # fall back to the external sensors_file only if no inline block exists.
    sensors = extract_sensors(text)
    sensors_source = "pnd.md (inline)"
    if sensors is None:
        sensors = load_sensors(sensors_path) if sensors_path.exists() else []
        sensors_source = str(sensors_path) if sensors else "(none found)"

    corpus_dir = base_dir / "corpus"
    result = {
        "manifest": manifest,
        "scoring": cfg["scoring"],
        "production": cfg.get("production", {}),
        "domain": domain,
        "domain_dir": domain_dir,
        "base_dir": base_dir,
        "sensors": sensors,
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
