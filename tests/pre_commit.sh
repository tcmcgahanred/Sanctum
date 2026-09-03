#!/usr/bin/env bash
# Sanctum · tests/pre_commit.sh · the commit gate
#
# Runs every check before work leaves this machine. The first two fail closed
# and can be overridden deliberately with `git commit --no-verify`. The third
# only ever warns.
#
#   domain_check.py      a domain file declares settings, never behaviour
#   vocab_check.py       no silent decay in a domain's word lists
#   geo_classify_test.py the geography confidence table is sound
#   cycle_dates_test.py  the staging document states its own ICOD and coverage
#   merge_test.py        one file per domain assembles, and nothing is declared twice
#   fetch_test.py        failure pages never become article bodies, and old
#                        reports never enter the corpus
#   changelog_check.sh   you changed something — did you write it down? (warns)
#
# There is no scrub check. It was removed 2026-08-23: it required every clone to
# author a local denylist before it could commit at all, which made a per-user
# secret a precondition for using the engine. Keeping what is private out of the
# repo is still a rule — it is tenet 8 — it is just not enforced by a script.
#
# The rules are named here in words rather than by tenet number on purpose. The
# numbering lives in README.md, and a number restated in a second file is a
# number that goes stale in one of them.
#
# INSTALL (once per clone):
#     git config core.hooksPath .githooks
#     mkdir -p .githooks && ln -sf ../tests/pre_commit.sh .githooks/pre-commit
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
    # Collection guards. Offline by design — a guard that needs the internet
    # is a guard that gets skipped on the day it matters.
    python3 "$REPO_ROOT/tests/fetch_test.py" >/dev/null || {
        echo "pre-commit: BLOCKED — tests/fetch_test.py failed; run it to see which check" >&2
        STATUS=1; }
    # Same class as fetch_test: engine behaviour, stdlib plus PyYAML, fails
    # closed. It guards the handover from stage 3a to 3b — the requirement, the
    # multiplier evidence, and the rule that an undeclared domain stays silent
    # rather than printing "Requirement met: None" on every candidate.
    python3 "$REPO_ROOT/tests/handover_test.py" >/dev/null || {
        echo "pre-commit: BLOCKED — tests/handover_test.py failed; run it to see which check" >&2
        STATUS=1; }
    # The homonym gate. A shark breaching the ocean force-surfaced as a California
    # cyber incident on 2026-08-31; force-surface is immune to the score by design,
    # so nothing downstream could have caught it. This holds the line in both
    # directions - the junk drops AND every genuine item an earlier attempt deleted
    # still surfaces.
    python3 "$REPO_ROOT/tests/geo_classify_test.py" >/dev/null || {
        echo "pre-commit: BLOCKED — tests/geo_classify_test.py failed; the geography table was hand-edited or a regeneration moved a known collision" >&2
        STATUS=1
    }

    python3 "$REPO_ROOT/tests/cycle_dates_test.py" >/dev/null || {
        echo "pre-commit: BLOCKED — tests/cycle_dates_test.py failed; the staging document no longer states its own ICOD, so the vox cannot be dated" >&2
        STATUS=1
    }

    python3 "$REPO_ROOT/tests/merge_test.py" >/dev/null || {
        echo "pre-commit: BLOCKED — tests/merge_test.py failed; a domain file declares something twice, or the one-file layout broke" >&2
        STATUS=1
    }

    python3 "$REPO_ROOT/tests/homonym_test.py" >/dev/null || {
        echo "pre-commit: BLOCKED — tests/homonym_test.py failed; run it to see which case" >&2
        STATUS=1; }
else
    echo "pre-commit: BLOCKED — python3 not found, cannot check domain files" >&2
    STATUS=1
fi

# Warns, never blocks — `|| true` is belt and braces on top of the script's own
# unconditional exit 0, so a future edit that introduces a non-zero path there
# still cannot stop a commit.
bash "$REPO_ROOT/tests/changelog_check.sh" || true

exit "$STATUS"
