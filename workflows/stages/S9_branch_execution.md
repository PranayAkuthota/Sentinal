# S9 — Branch Execution

## Purpose
Execute the branch chosen at S8 on `working_copy/` only (or evidence packaging path for Invalid).

## Inputs
- Recorded verdicts (Public == Duplicate)
- Fix plan from S3–S7
- Fresh `working_copy/` from `extracted_original` if not already prepared

## Outputs
### Fixable
- Edits only in allowed files (instruction, problem_statement sync, tests.patch/config/test.sh/grade.py, solve.sh/golden.patch, allowed Dockerfile/metadata, git hygiene)
- Hygiene: ensure Harbor network blocks; strip compose `network_mode="none"`; ensure `grade.py`; rename solution.patch→golden.patch

### Valid as-is
- Confirm freeze: no content mutations required

### Invalid/Not Fixable
- Evidence notes for `package-invalid` (not a corrected submission ZIP)

## Validation
- `extracted_original/` untouched
- Existing p2p test sources byte-identical
- Scope not replaced/reduced
- No solution leakage into agent-readable paths

## Failure
Edits before S8; edits to tracked repo sources; p2p mutation; inventing unrelated features.

## Recovery
Restore `working_copy/` from `extracted_original/` and redo allowed edits only.

## Automation
`ensure-packaging-hygiene`, `sync-problem-statement`. Content fixes are expert-driven.
