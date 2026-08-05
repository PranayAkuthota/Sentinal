# P-009: Mode-only dirty trees are Fixable via reset not Invalid

**Status:** approved  
**Promoted:** 2026-08-01  
**Reusable:** yes

## Pattern

Working trees that are almost entirely file mode flips (100755 vs 100644) are usually Fixable with git reset --hard plus reflog removal — do not treat as content corruption or Not Fixable.

## When it applies

git status shows widespread mode changes without content diffs.

## What to do

Reset hard on working_copy repo; remove reflog; re-check hygiene before package.

## Do not promote into agent-facing instructions

Task UUIDs, golden patches, hidden tests, or PR spoilers.
