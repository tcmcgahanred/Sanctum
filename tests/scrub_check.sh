#!/usr/bin/env bash
# Sanctum · tests/scrub_check.sh · pre-commit scrub guard
#
# Blocks a commit that would publish identifying detail to a public repo.
# Tenet 11: "the public face carries no identifying or infra detail."
#
# The patterns themselves are NOT in this repo. They live in `.scrub-denylist`,
# which is git-ignored — publishing the list of things you are hiding defeats
# the purpose. Copy `.scrub-denylist.example` and fill it in locally.
#
# INSTALL: not installed on its own. `tests/pre_commit.sh` is the commit gate
# and runs this guard plus the domain-file guard — install that one instead.
# You still need the denylist:  cp .scrub-denylist.example .scrub-denylist
#
# USAGE
#     tests/scrub_check.sh          # scan STAGED content (what a commit would publish)
#     tests/scrub_check.sh --all    # audit every tracked file in the working tree
#     tests/scrub_check.sh --head   # audit the current commit's tree
#
# EXIT CODES
#     0  clean
#     1  a denied pattern was found, or the denylist is missing
#
# FAIL-CLOSED BY DESIGN. A missing denylist blocks the commit rather than
# passing quietly. Silent-pass is precisely how identifying detail survived
# in this repo from the first commit onward.
#
# Bypass with `git commit --no-verify` if you must. Do so deliberately.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "scrub-check: not inside a git repository" >&2; exit 1; }
cd "$REPO_ROOT"

DENYLIST="${SANCTUM_DENYLIST:-$REPO_ROOT/.scrub-denylist}"
MODE="${1:---staged}"

red()  { printf '\033[31m%s\033[0m\n' "$*"; }
bold() { printf '\033[1m%s\033[0m\n' "$*"; }

if [ ! -f "$DENYLIST" ]; then
    red "scrub-check: BLOCKED — no denylist found at $DENYLIST"
    cat >&2 <<'EOF'

This guard fails closed: without a denylist it cannot verify anything, so it
refuses rather than letting the commit through unchecked.

Fix (once):
    cp .scrub-denylist.example .scrub-denylist
    #  then edit .scrub-denylist and add your real terms

.scrub-denylist is git-ignored and must stay that way.
EOF
    exit 1
fi

# Read the denylist.
#   plain line  -> a POSIX extended regex to deny
#   '!' prefix  -> a path prefix to EXCLUDE from scanning
#   '#' / blank -> ignored
PATTERNS=()
EXCLUDES=()
while IFS= read -r line; do
    line="${line%%$'\r'}"                      # tolerate CRLF from Windows editors
    [ -z "${line// }" ] && continue
    case "$line" in
        \#*) continue ;;
        !*)  EXCLUDES+=("${line#!}") ; continue ;;
    esac
    PATTERNS+=("$line")
done < "$DENYLIST"

is_excluded() {
    local f="$1" e
    for e in ${EXCLUDES+"${EXCLUDES[@]}"}; do
        case "$f" in "$e"*) return 0 ;; esac
    done
    return 1
}

if [ "${#PATTERNS[@]}" -eq 0 ]; then
    red "scrub-check: BLOCKED — $DENYLIST contains no patterns"
    echo "An empty denylist checks nothing. Add terms or remove the hook." >&2
    exit 1
fi

JOINED="$(IFS='|'; echo "${PATTERNS[*]}")"

# Build the file list for the chosen mode.
case "$MODE" in
    --staged)
        mapfile -t FILES < <(git diff --cached --name-only --diff-filter=ACMR)
        SCOPE="staged changes" ;;
    --all)
        mapfile -t FILES < <(git ls-files)
        SCOPE="all tracked files" ;;
    --head)
        mapfile -t FILES < <(git ls-tree -r HEAD --name-only)
        SCOPE="HEAD tree" ;;
    *)
        echo "usage: $0 [--staged|--all|--head]" >&2; exit 1 ;;
esac

if [ "${#FILES[@]}" -eq 0 ]; then
    echo "scrub-check: nothing to scan ($SCOPE)"
    exit 0
fi

HITS=0
SKIPPED=0
for f in "${FILES[@]}"; do
    if is_excluded "$f"; then SKIPPED=$((SKIPPED + 1)); continue; fi
    if [ "$MODE" = "--staged" ]; then
        MATCHES="$(git show ":$f" 2>/dev/null | grep -nIiE "$JOINED" 2>/dev/null)"
    else
        [ -f "$f" ] || continue
        MATCHES="$(grep -nIiE "$JOINED" -- "$f" 2>/dev/null)"
    fi
    [ -z "$MATCHES" ] && continue
    if [ "$HITS" -eq 0 ]; then
        red "scrub-check: BLOCKED — denied pattern(s) found in $SCOPE"
        echo
    fi
    bold "  $f"
    printf '%s\n' "$MATCHES" | while IFS= read -r m; do
        echo "    ${m:0:160}"
    done
    echo
    HITS=$((HITS + 1))
done

if [ "$HITS" -gt 0 ]; then
    cat >&2 <<'EOF'
Remove or redact the flagged text, then re-stage and commit.

Note: removing it from HEAD does NOT remove it from history. If the string has
already been pushed to a public remote, treat it as disclosed — a history
rewrite reduces exposure, it does not undo it.

Deliberate override: git commit --no-verify
EOF
    exit 1
fi

echo "scrub-check: clean ($(( ${#FILES[@]} - SKIPPED )) file(s) scanned, ${#PATTERNS[@]} pattern(s), $SKIPPED excluded)"
exit 0
