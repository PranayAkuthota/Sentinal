# P-006: Prefer trimming untested instruction claims over thin f2p filler

**Status:** approved  
**Promoted:** 2026-08-01  
**Reusable:** yes

## Pattern

When coverage gaps are prose-only (behaviors with no graded assertion), prefer rewriting the instruction to tested contracts over inventing shallow fail-to-pass tests just to pad coverage.

## When it applies

Instruction lists behaviors that have zero graded test overlap.

## What to do

Either add meaningful f2p within PR scope or delete/trim the untested claim before packaging.

## Do not promote into agent-facing instructions

Task UUIDs, golden patches, hidden tests, or PR spoilers.
