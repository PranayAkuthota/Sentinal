# S10 — Deterministic Runtime Validation

## Purpose
Execute oracle and NOP (or document why not) and record evidence. Never invent rewards.

## Inputs
- Branch package root (`working_copy/` for Fixable; original for Valid-as-is checks)
- Docker available locally when claiming Executed

## Outputs
- `session/validation_logs/` artifacts
- `record-validation` entries with status + evidence paths + rewards when real

## Validation
### Valid as-is
- Oracle reward `1.0` and NOP `0.0` **required** (Executed)

### Fixable
- Strongly recommended before upload; platform will also run checks

### Invalid
- Runtime optional; do not claim a passing corrected oracle

## Failure
Missing Docker; flaky network installs; invented rewards; claiming Executed without logs.

## Recovery
Label `not_run` honestly; fix Dockerfile/timeouts within policy; re-run. Never fabricate `reward.txt`.

## Automation
`local_oracle_nop.py`, `record-validation`. Interpretation remains expert.
