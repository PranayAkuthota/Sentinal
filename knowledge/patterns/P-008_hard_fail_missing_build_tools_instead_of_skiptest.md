# P-008: Hard-fail missing build tools instead of SkipTest

**Status:** approved  
**Promoted:** 2026-08-01  
**Reusable:** yes

## Pattern

unittest.SkipTest or soft skips when cmake/make is missing can look like a soft pass under graders that count PASSED only. Prefer raising an error so missing toolchain fails closed.

## When it applies

Verifier suites depend on system toolchains installed in the Dockerfile.

## What to do

Raise AssertionError/RuntimeError; ensure Dockerfile installs the toolchain offline.

## Do not promote into agent-facing instructions

Task UUIDs, golden patches, hidden tests, or PR spoilers.
