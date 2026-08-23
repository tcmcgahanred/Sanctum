#!/usr/bin/env bash
# Sanctum · tests/pre_commit.sh · the commit gate
#
# Runs every guard before work leaves this machine. The first three fail closed
# and can be overridden deliberately with `git commit --no-verify`. The fourth
# only ever warns.
#
#   scrub_check.sh       nothing identifying goes in the repo
#   domain_check.py      a domain file declares settings, never behaviour
#   vocab_check.py       no silent decay in a domain's word lists
#   changelog_check.sh   you changed something — did you write it down? (warns)
#
# The rules are named here in words rather than by tenet number on purpose. The
# numbering lives in README.md, and a number restated in a second file is a
# number that goes stale in one of them.
#
# INSTALL (once per clone):
#     git config core.hooksPath .githooks
#     mkdir -p .githooks && ln -sf ../tests/pre_commit.sh .githooks/pre-commit
#     cp .scrub-denylist.example .scrub-denylist   # then edit it
#
#   Git-for-Windows: same commands in Git Bash; copy instead of link if symlinks
#   are awkward.
#
# Every guard runs even if an earlier one fails, so one commit attempt tells you
# everything that is wrong rather than making you discover problems one at a time.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "pre-commit: not inside a git repository" >&2; exit 1; }
cd "$REPO_ROOT"

STATUS=0

bash "$REPO_ROOT/tests/scrub_check.sh" --staged || STATUS=1

if command -v python3 >/dev/null 2>&1; then
    python3 "$REPO_ROOT/tests/domain_check.py" --staged || STATUS=1
    # Runs against every TRACKED domain, not just staged files: a vocabulary
    # defect is a property of the whole word list, and an edit to one group can
    # orphan a boundary entry in a file nobody touched this commit.
    #
    # --tracked-only matters. A gitignored domain — a second effort held out of
    # the public repo, a stub that is not operational yet — cannot reach the
    # repo this gate protects, so it must not be able to block a commit. Run the
    # tool by hand, with no flag, to see those domains too.
    python3 "$REPO_ROOT/tools/vocab_check.py" --tracked-only || STATUS=1
else
    echo "pre-commit: BLOCKED — python3 not found, cannot check domain files" >&2
    STATUS=1
fi

# Warns, never blocks — `|| true` is belt and braces on top of the script's own
# unconditional exit 0, so a future edit that introduces a non-zero path there
# still cannot stop a commit.
bash "$REPO_ROOT/tests/changelog_check.sh" || true

exit "$STATUS"
