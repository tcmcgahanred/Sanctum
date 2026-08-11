#!/usr/bin/env bash
# Sanctum · run.sh <domain> · (runner; history via git)
#
# Runs the full cycle for one domain: collect -> score.
# The engines are domain-agnostic; everything specific comes from
# <domain>/pnd.md. Usage:
#     ./run.sh cti          # collect + score the CTI domain
#     ./run.sh s2           # (once s2/pnd.md is filled in)
#
# Run from the repo root (this script cd's there). Python must have the deps
# in requirements.txt. The corpus push (rclone) is handled inside Acolyte,
# using the remote declared in the domain manifest.
set -euo pipefail

DOMAIN="${1:?usage: run.sh <domain>   (e.g. run.sh cti)}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# Prefer the host venv python if present, else system python3.
PY="/opt/ravenor/venv/bin/python3"
[ -x "$PY" ] || PY="python3"

"$PY" -m core.acolyte --domain "$DOMAIN"
"$PY" -m core.arbites --domain "$DOMAIN"
