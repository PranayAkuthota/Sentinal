# S4 — Instruction Quality Review

## Purpose
Evaluate `instruction.md` for clarity, solvability contracts, leakage, and over-prescription. Expert-only semantic judgement.

## Inputs
- `instruction.md` and `environment/problem_statement.md`
- Source alignment notes (S3)
- Runs/logs if present (optional context)

## Outputs
- Findings: leakage, missing contracts, LLM tone, over-prescription
- Rewrite plan notes (applied only after Fixable verdict in S9)
- Confirm whether `problem_statement.md` must be resynced later

## Validation
- Observable outcomes stated; public schemas documented when required
- No PR URLs, commit SHAs, hidden test names, or solution spoilers
- Not a step-by-step implementation guide unless the public contract demands it
- Sounds like real engineering communication

## Failure
Unresolved leakage; missing required schemas; instruction references nonexistent APIs; robotic templated prose that hides the ask.

## Recovery
On Fixable branch: rewrite instruction + sync `problem_statement.md`. Do not edit before S8 verdicts.

## Automation
None for quality. Optional future heuristics are warnings only.
