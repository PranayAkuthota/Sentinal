#!/usr/bin/env bash
# The pre-submission git checklist from Sentinel Ultra Guidelines § "Git — fixable in the repo".
# Every line must be clean or empty.
#
#   usage: git_hygiene.sh <task-root> [--fix]
#
# --fix applies ONLY the repairs the guidelines authorise:
#   remove remotes, delete refs beyond HEAD, strip filter.* drivers, expire the reflog,
#   gc, and realign task.toml's base commit to HEAD (the shipped repo is the source of truth).
# It NEVER touches tracked source files.

set -uo pipefail

ROOT="${1:-}"
FIX="${2:-}"
[ -z "$ROOT" ] && { echo "usage: $0 <task-root> [--fix]" >&2; exit 2; }
ROOT="$(cd "$ROOT" && pwd)"
REPO="$ROOT/environment/repo"
TOML="$ROOT/task.toml"

[ -d "$REPO" ] || { echo "FAIL  environment/repo/ not found under $ROOT" >&2; exit 2; }
if [ ! -e "$REPO/.git" ]; then
  echo "FAIL  .git missing — no repo for the agent to work in."
  echo "      Usually a zip tool that dropped dotfiles. Ensure environment/repo/ is a real"
  echo "      repo and .git/ is in the archive; re-zip with 'zip -rX' (never -D, never GUI)."
  exit 1
fi

PASS=0; FAILN=0
ok()   { printf '  \033[32mOK  \033[0m %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$1"; FAILN=$((FAILN+1)); }
note() { printf '       %s\n' "$1"; }

echo "git hygiene — $REPO"
echo

# 1 — HEAD resolves
if HEAD_SHA="$(git -C "$REPO" rev-parse --verify HEAD 2>/dev/null)"; then
  ok "HEAD resolves ($HEAD_SHA)"
else
  bad "HEAD does not resolve"
  note "fix: ensure the repo has at least one commit and HEAD points at it"
  echo; echo "$PASS passed, $FAILN failed"; exit 1
fi

# 2 — HEAD == base_commit_sha in task.toml
DECLARED="$(grep -Eo 'base_commit(_sha)?[[:space:]]*=[[:space:]]*"[0-9a-fA-F]{7,40}"' "$TOML" 2>/dev/null \
            | head -1 | grep -Eo '[0-9a-fA-F]{7,40}')"
if [ -z "$DECLARED" ]; then
  note "note: task.toml declares no base_commit_sha — nothing to compare"
elif [ "${HEAD_SHA:0:${#DECLARED}}" = "$DECLARED" ]; then
  ok "HEAD == declared base commit"
else
  bad "HEAD ($HEAD_SHA) != declared base commit ($DECLARED)"
  note "the shipped repo (HEAD) is the source of truth — realign task.toml to HEAD"
  if [ "$FIX" = "--fix" ]; then
    perl -0pi -e "s/(base_commit(?:_sha)?\s*=\s*\")[0-9a-fA-F]{7,40}(\")/\${1}$HEAD_SHA\${2}/" "$TOML" \
      && note "FIXED: task.toml base commit set to $HEAD_SHA"
  fi
fi

# 3 — no commits beyond HEAD
EXTRA="$(git -C "$REPO" rev-list --all --not HEAD 2>/dev/null)"
if [ -z "$EXTRA" ]; then
  ok "no commits beyond HEAD"
else
  bad "$(echo "$EXTRA" | wc -l | tr -d ' ') commit(s) beyond HEAD — these can leak the fix history"
  if [ "$FIX" = "--fix" ]; then
    git -C "$REPO" for-each-ref --format='%(refname:short)' refs/heads \
      | while read -r b; do [ "$b" = "$(git -C "$REPO" rev-parse --abbrev-ref HEAD)" ] || git -C "$REPO" branch -D "$b" >/dev/null 2>&1; done
    git -C "$REPO" tag | while read -r t; do git -C "$REPO" tag -d "$t" >/dev/null 2>&1; done
    git -C "$REPO" for-each-ref --format='%(refname)' refs/remotes \
      | while read -r r; do git -C "$REPO" update-ref -d "$r" >/dev/null 2>&1; done
    note "FIXED: deleted stray branches/tags/remote-refs (re-run to confirm)"
  fi
fi

# 4 — no remotes
REMOTES="$(git -C "$REPO" remote 2>/dev/null)"
if [ -z "$REMOTES" ]; then
  ok "no remotes"
else
  bad "remote(s) configured: $(echo "$REMOTES" | tr '\n' ' ')"
  if [ "$FIX" = "--fix" ]; then
    echo "$REMOTES" | while read -r r; do [ -n "$r" ] && git -C "$REPO" remote remove "$r"; done
    note "FIXED: removed all remotes"
  fi
fi

# 5 — no filter.* drivers
FILTERS="$(git -C "$REPO" config --local --get-regexp '^filter\.' 2>/dev/null)"
if [ -z "$FILTERS" ]; then
  ok "no filter.* drivers"
else
  bad "filter.* drivers present (arbitrary commands git may run)"
  echo "$FILTERS" | sed 's/^/         /'
  if [ "$FIX" = "--fix" ]; then
    echo "$FILTERS" | awk '{print $1}' | sed 's/\.[^.]*$//' | sort -u \
      | while read -r s; do git -C "$REPO" config --local --remove-section "$s" 2>/dev/null; done
    note "FIXED: removed filter.* sections"
  fi
fi

# 6 — clean working tree
DIRTY="$(git -C "$REPO" status --porcelain 2>/dev/null)"
if [ -z "$DIRTY" ]; then
  ok "clean working tree"
else
  bad "$(echo "$DIRTY" | wc -l | tr -d ' ') uncommitted/untracked entr(y/ies) — an uncommitted solution leaks the answer"
  echo "$DIRTY" | head -8 | sed 's/^/         /'
  note "fix by hand: git checkout -- . && git clean -fd   (verify nothing legitimate is lost first)"
fi

# 7 — no reflog
if [ -e "$REPO/.git/logs" ]; then
  bad ".git/logs present (reflog records rewound commits, e.g. the solution)"
  if [ "$FIX" = "--fix" ]; then
    git -C "$REPO" reflog expire --expire=now --all >/dev/null 2>&1
    git -C "$REPO" gc --prune=now >/dev/null 2>&1
    rm -rf "$REPO/.git/logs"
    note "FIXED: reflog expired, gc run, .git/logs removed"
  fi
else
  ok "no reflog"
fi

# 8 — .git under 100 MB
GITKB="$(du -sk "$REPO/.git" 2>/dev/null | awk '{print $1}')"
if [ -n "$GITKB" ] && [ "$GITKB" -lt 102400 ]; then
  ok ".git is $((GITKB/1024)) MB (< 100 MB)"
else
  bad ".git is $((GITKB/1024)) MB — over the 100 MB limit"
  if [ "$FIX" = "--fix" ]; then
    git -C "$REPO" gc --aggressive --prune=now >/dev/null 2>&1
    note "FIXED(attempted): git gc --aggressive --prune=now — re-run to confirm"
  else
    note "fix: git gc --aggressive --prune=now; if still large, strip big blobs or ship a"
    note "     fresh single-commit base history (then reset base_commit_sha in task.toml)"
  fi
fi

# 9 — tests patch applies
PATCH=""
for c in "$ROOT/tests/tests.patch" "$ROOT/tests/test.patch"; do [ -f "$c" ] && { PATCH="$c"; break; }; done
if [ -z "$PATCH" ]; then
  bad "no tests/tests.patch found"
else
  if OUT="$(git -C "$REPO" apply --check "$PATCH" 2>&1)"; then
    ok "$(basename "$PATCH") applies cleanly"
  else
    bad "$(basename "$PATCH") does not apply"
    echo "$OUT" | head -5 | sed 's/^/         /'
    note "fix: make HEAD == base commit first, then regenerate the patch against the shipped"
    note "     repo state (see fix-playbooks.md F10). NEVER hand-edit hunk offsets."
  fi
fi

echo
echo "$PASS passed, $FAILN failed"
[ "$FAILN" -eq 0 ] || exit 1
