# S6 — Oracle Faithfulness Review

## Purpose
Static review that the oracle (`solve.sh` + `golden.patch` / legacy `solution.patch`) implements required behavior without gaming.

## Inputs
- `solution/solve.sh`, `golden.patch` or `solution.patch`
- Instruction + verifier notes from S5
- Disposable apply checks only (never mutate `extracted_original/`)

## Outputs
- Oracle naming/dialect notes
- Faithfulness vs instruction; gaming risks
- Fix notes for S9 (if Fixable)

## Validation
- Oracle satisfies stated requirements
- No fixture-specific hardcoding as the strategy; no reading hidden goldens
- No live-network dependence
- Rename `solution.patch` → `golden.patch` on corrected current uploads

## Failure
Oracle mismatches instruction; gaming; unapplyable solution patch; solution material leaked into agent-readable paths.

## Recovery
Fixable: correct `solve.sh` / `golden.patch` on `working_copy/` after S8. Invalid if oracle cannot be aligned without replacing scope.

## Automation
Apply-check assist only. Do not run full reward scoring here (that is S10).
