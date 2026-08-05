# P-001: tests.patch must pass git apply (not patch-only)

**Status:** approved  
**Reusable:** yes

## Pattern

Corrected packages require `git apply --check` success on `tests/tests.patch`. GNU `patch` alone is insufficient (rename/hunk dialect mismatches).

## What to do

Rebuild the patch from a clean base + final test tree; block Fixable preflight until git-apply passes.
