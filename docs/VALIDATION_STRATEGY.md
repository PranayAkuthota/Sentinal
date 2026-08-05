# Validation strategy

## Classes of evidence

| Class | Meaning |
|-------|---------|
| Inspected | Read files / patches |
| Inferred | Reasonable deduction (label as such) |
| Executed | Ran command locally |
| Confirmed by supplied logs | Platform/user logs |
| Not verified | Could not run |

Never invent Executed results.

## Structural validation (automation OK)

- Required Harbor files
- Instruction ↔ problem_statement sync
- `tests.patch` **git apply --check**
- Patch hunk health
- Ungraded tests vs `fail_to_pass`
- Metadata limits; network field absence on Fixable corrected
- Git hygiene
- Packaging zip shape

## Runtime validation (automation OK; interpretation expert)

- Docker image build
- Oracle reward on graded f2p
- NOP reward on graded f2p

## Semantic validation (expert ONLY)

- Instruction quality / leakage / over-prescription
- Coverage & faithfulness maps
- Oracle faithfulness vs gaming
- Tri-field verdicts
- Difficulty / scope expansion choices

## Checkpoint readiness

Before Execution **02–06**, run `automation/checkpoint_ready.py`. Prior handoffs must exist with `status: complete`. Steps **05/06** also require Public == Duplicate.

## Pre-submit blockers

Walk `docs/SUBMITTER_BLOCKERS.md` before claiming a Fixable upload is ready.

## Framework regression

`repo_tests/` covers mechanical helpers (verdict normalization, checkpoint parsing, doctor smoke). Never encodes task verdicts.

## Checklists

See `validation/checklists/`.
