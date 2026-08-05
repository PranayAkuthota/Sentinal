# Module: Runtime Validation (S10)

Load during Execution **05** after branch content is stable.

## Do
1. Prefer `python3 automation/local_oracle_nop.py --task-name TASK --mode both`.
2. `record-validation` for docker_build / oracle / nop with real evidence paths.
3. Valid as-is: require oracle `1.0` and NOP `0.0`.
4. Fixable: strongly recommended before packaging.

## Do not
- Invent rewards or claim Executed without logs
- Proceed to package if Valid-as-is runtime failed

## Handoff must include
Reward values (or honest `not_run`), log paths, flakiness notes.
