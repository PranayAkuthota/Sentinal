# P-007: Compiler-build verifiers often need higher verifier.timeout_sec

**Status:** approved  
**Promoted:** 2026-08-01  
**Reusable:** yes

## Pattern

When tests invoke cmake/make/configure inside the Harbor verifier, verifier.timeout_sec of 300 is often insufficient. Bump within the Ultra max of 1800 when packaging Fixable.

## When it applies

test.sh or tests.patch drive native builds.

## What to do

Set verifier.timeout_sec high enough for cold container builds; keep agent.timeout_sec within caps.

## Do not promote into agent-facing instructions

Task UUIDs, golden patches, hidden tests, or PR spoilers.
