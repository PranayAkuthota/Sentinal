# S5 — Verifier Alignment

## Purpose
Build instruction→tests coverage and tests→instruction faithfulness maps. Assess fail-to-pass count quality and `allow_extra_failures` risk.

## Inputs
- Instruction
- `tests/config.json`, `tests/tests.patch`, `tests/test.sh`, `grade.py` if present
- Structural audit warnings (ungraded tests, patch health)

## Outputs
- Coverage gaps and faithfulness/overreach findings
- Meaningful f2p count vs guideline (≥10) and live “more than 10” (≥11 when claiming)
- Proposed Fixable test/config actions (notes only until S9)

## Validation
- Every critical instruction behavior has an enforcing graded assertion
- Every graded assertion is stated/implied/derivable
- Prefer promoting existing meaningful patch tests into `fail_to_pass` over filler
- Existing p2p sources remain byte-identical on corrected packages

## Failure
Critical tests ungraded under `allow_extra_failures`; overreach; <10 meaningful f2p; filler-only inflation.

## Recovery
Fixable: expand `tests.patch` / `fail_to_pass` within PR scope; never edit existing p2p test files.

## Automation
Structural discovery (ungraded names, git-apply health). Semantics are expert.
