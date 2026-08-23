#!/usr/bin/env bash
# Sanctum · tests/changelog_check.sh · the fourth guard
#
# Three changelog entries were written, reported written, and never reached the
# file. The scripts that wrote them printed "ok" whether or not the text they
# were replacing existed. Nothing noticed for days, and the only reason it
# surfaced at all was someone reading the file for another reason.
#
# This guard is deliberately dumb. It does not read the changelog, judge the
# entry, or care what the entry says. It asks one thing: you changed something,
# did you write it down? A smarter check would need maintaining, and the failure
# it prevents is not subtle.
#
# It never blocks. Exit is always 0. A warning you can ignore is the right
# weight for a habit — a gate that stopped a commit over a missing note would be
# bypassed within a week and then ignored entirely.
#
# Exempt, because writing a changelog entry for these would be noise:
#     logs/CHANGELOG.md   the file itself
#     */editions/         published work product, not a change to the apparatus
#     */corpus/           collected material

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$REPO_ROOT" || exit 0

CHANGELOG="logs/CHANGELOG.md"

staged="$(git diff --cached --name-only --diff-filter=ACMRD 2>/dev/null)"
[ -z "$staged" ] && exit 0

# Is the changelog itself among the staged files?
changelog_staged=0
while IFS= read -r f; do
    [ "$f" = "$CHANGELOG" ] && changelog_staged=1
done <<< "$staged"
[ "$changelog_staged" -eq 1 ] && exit 0

# Anything staged that is not exempt?
count=0
sample=""
while IFS= read -r f; do
    [ -z "$f" ] && continue
    case "$f" in
        "$CHANGELOG")            continue ;;
        editions/*|*/editions/*) continue ;;
        corpus/*|*/corpus/*)     continue ;;
    esac
    count=$((count + 1))
    [ "$count" -le 3 ] && sample="${sample}    ${f}"$'\n'
done <<< "$staged"

[ "$count" -eq 0 ] && exit 0

{
    echo "changelog: NOTE — ${count} changed file(s) staged, and ${CHANGELOG} is not among them."
    printf '%s' "$sample"
    [ "$count" -gt 3 ] && echo "    … and $((count - 3)) more"
    echo "changelog: this never blocks. If the change is worth remembering, write it down."
} >&2

exit 0
