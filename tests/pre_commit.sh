#!/usr/bin/env bash
# Sanctum · tests/pre_commit.sh · the commit gate
#
# Runs every guard that must pass before work leaves this machine. Both guards
# fail closed and both can be overridden deliberately with `git commit --no-verify`.
#
#   scrub_check.sh    tenet 11 — no identifying or infra detail reaches the public repo
#   domain_check.py   tenet  3 — no domain file contains behavior
#
# INSTALL (once per clone):
#     git config core.hooksPath .githooks
#     mkdir -p .githooks && ln -sf ../tests/pre_commit.sh .githooks/pre-commit
#     cp .scrub-denylist.example .scrub-denylist   # then edit it
#
#   Git-for-Windows: same commands in Git Bash; copy instead of link if symlinks
#   are awkward.
#
# Both guards run even if the first one fails, so one commit attempt tells you
# everything that is wrong rather than making you discover problems one at a time.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "pre-commit: not inside a git repository" >&2; exit 1; }
cd "$REPO_ROOT"

STATUS=0

bash "$REPO_ROOT/tests/scrub_check.sh" --staged || STATUS=1

if command -v python3 >/dev/null 2>&1; then
    python3 "$REPO_ROOT/tests/domain_check.py" --staged || STATUS=1
else
    echo "pre-commit: BLOCKED — python3 not found, cannot check domain files" >&2
    STATUS=1
fi

exit "$STATUS"
