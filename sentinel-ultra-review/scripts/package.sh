#!/usr/bin/env bash
# Package a corrected Sentinel Ultra task exactly as the Tasking Guide requires.
#
#   usage: package.sh <task-root> <out.zip>
#
# The archive must contain the FLAT CONTENTS of the task root — not the folder itself,
# and not runs/. It must unpack directly to instruction.md, task.toml, environment/,
# solution/, tests/.
#
# Uses `zip -rX` deliberately: -D (and GUI "Compress") drop empty directory entries such
# as .git/refs/ left by `git gc`, which breaks the repository on the platform even though
# the uncompressed copy works locally.

set -euo pipefail

ROOT="${1:-}"; OUT="${2:-}"
if [ -z "$ROOT" ] || [ -z "$OUT" ]; then
  echo "usage: $0 <task-root> <out.zip>" >&2; exit 2
fi
ROOT="$(cd "$ROOT" && pwd)"
case "$OUT" in /*) ;; *) OUT="$(pwd)/$OUT" ;; esac

command -v zip >/dev/null || { echo "error: 'zip' is not installed" >&2; exit 2; }
[ -f "$ROOT/task.toml" ] || { echo "error: $ROOT has no task.toml — point at the task root" >&2; exit 2; }

fail=0
say()  { printf '  %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$1"; fail=1; }
ok()   { printf '  \033[32mOK  \033[0m %s\n' "$1"; }

echo "pre-zip checks"

# required contents
for f in instruction.md task.toml environment/Dockerfile environment/problem_statement.md \
         solution/solve.sh solution/golden.patch tests/test.sh tests/tests.patch tests/config.json; do
  [ -e "$ROOT/$f" ] && ok "$f" || bad "$f missing"
done
[ -d "$ROOT/environment/repo/.git" ] && ok "environment/repo/.git present" \
                                     || bad "environment/repo/.git missing"

# problem_statement must be byte-identical to instruction
if [ -f "$ROOT/instruction.md" ] && [ -f "$ROOT/environment/problem_statement.md" ]; then
  if cmp -s "$ROOT/instruction.md" "$ROOT/environment/problem_statement.md"; then
    ok "problem_statement.md == instruction.md"
  else
    bad "problem_statement.md differs from instruction.md (cp instruction.md environment/problem_statement.md)"
  fi
fi

# runs/ must not be inside the task root
[ -d "$ROOT/runs" ] && bad "runs/ is inside the task root — it must NOT be in the zip" \
                    || ok "no runs/ inside the task root"

# draft filenames
[ -f "$ROOT/solution/solution.patch" ] && bad "solution/solution.patch present — rename to golden.patch" || true

# stray artifacts
STRAY="$(find "$ROOT" \( -name '__pycache__' -o -name '*.pyc' -o -name '.DS_Store' \
  -o -name '.pytest_cache' -o -name '.mypy_cache' -o -name '.ruff_cache' \
  -o -name '.venv' -o -name 'node_modules' -o -name '.idea' -o -name '.vscode' \
  -o -name '*.swp' -o -name '*~' -o -name '*.orig' -o -name '*.bak' \) -not -path '*/.git/*' 2>/dev/null || true)"
if [ -n "$STRAY" ]; then
  bad "stray developer artifacts present (a single one hard-caps the packaging axis at 1):"
  echo "$STRAY" | head -10 | sed 's/^/         /'
else
  ok "no stray developer artifacts"
fi

if [ "$fail" -ne 0 ]; then
  echo
  echo "Refusing to package — fix the FAIL lines above first."
  exit 1
fi

echo
echo "packaging"
rm -f "$OUT"
( cd "$ROOT" && zip -rX "$OUT" . -x '*.DS_Store' '__MACOSX/*' >/dev/null )
say "wrote $OUT ($(du -h "$OUT" | awk '{print $1}'))"

echo
echo "post-zip verification"

# capture the listing once — piping into `grep -q` under `pipefail` makes unzip SIGPIPE
LIST="$(unzip -l "$OUT")"
NAMES="$(printf '%s\n' "$LIST" | awk 'NR>3 && NF>=4 && $1 ~ /^[0-9]+$/ {print $4}')"

# must unpack flat
TOP="$(printf '%s\n' "$NAMES" | sed 's|/.*|/|' | sort -u | grep -v '^$' || true)"
if printf '%s\n' "$TOP" | grep -qx 'task/'; then
  bad "archive wraps a task/ folder — it must hold the FLAT contents"
else
  ok "archive holds flat contents (top level: $(printf '%s ' $TOP))"
fi

if printf '%s\n' "$NAMES" | grep -Eq '^(\./)?runs/'; then
  bad "runs/ is inside the archive"
else
  ok "no runs/ in the archive"
fi

if printf '%s\n' "$NAMES" | grep -Eq '^(\./)?instruction\.md$'; then
  ok "instruction.md at top level"
else
  bad "instruction.md not at the archive's top level"
fi

# the empty git directory entries must survive (this is why -D and GUI zip are forbidden)
REFS="$(printf '%s\n' "$NAMES" | grep -c 'refs/' || true)"
if [ "$REFS" -gt 0 ]; then
  ok "git directory entries preserved ($REFS 'refs/' entries)"
else
  bad "no 'refs/' entries in the archive — empty git dirs were dropped; the repo will break on the platform"
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "Ready to upload: $OUT"
  echo "Re-upload as <all-task-content>. Run evals with 'Send to reviewer' UNCHECKED until"
  echo "Difficulty, Oracle, and Quality checks all pass."
else
  echo "Archive written but verification FAILED — do not upload."
  exit 1
fi
