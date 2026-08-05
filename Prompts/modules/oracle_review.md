# Module: Oracle Review (S6)

Load during Execution **03** / stage S6.

## Do
1. Confirm `golden.patch` vs legacy `solution.patch` naming.
2. Read `solve.sh`; assess apply path and faithfulness to instruction.
3. Flag gaming (fixture hardcoding, hidden goldens, network oracle).
4. Disposable apply checks only — never mutate `extracted_original/`.

## Do not
- Run full oracle reward scoring here (S10 / Execution **05**)
- Ship solution material into agent-readable repo paths

## Handoff must include
Oracle dialect; faithfulness/gaming notes; Fixable oracle edit plan if any.
