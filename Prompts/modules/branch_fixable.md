# Module: Branch Execution (S9)

Load during Execution **05** only after Execution **04** handoff is complete.

## Fixable
1. Edit `working_copy/` only — allowed files per Ultra policy.
2. Run `ensure-packaging-hygiene` and `sync-problem-statement` when instruction changed.
3. Keep existing p2p tests byte-identical; add f2p via `tests.patch`.
4. Ensure Harbor network blocks on `task.toml` (do **not** strip them); strip compose `network_mode="none"` if present; ensure `grade.py`; prefer `golden.patch` (P-003 / F-011).

## Valid as-is
Confirm freeze — no content mutations.

## Invalid/Not Fixable
Prepare evidence notes only — no “corrected valid” ZIP.

## Do not
- Touch `extracted_original/`
- Reduce/replace PR scope
- Skip hygiene on Fixable packages

## Handoff must include
Files changed list (path / what / why); hygiene commands run; residual risks.
