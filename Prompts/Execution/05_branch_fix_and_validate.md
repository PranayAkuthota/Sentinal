# 05 — Branch Fix & Validate

**Canonical daily prompt · Stages S9–S10**  
**Requires finalized 04 verdicts.** Packaging is **not** this step — that is **06**.

## Purpose
Execute the Duplicate branch, then produce honest Docker/oracle/NOP evidence.  
Keep instruction / tests / oracle synchronized on Fixable.

## Gate (must pass)
```bash
python3 automation/checkpoint_ready.py --task-name TASK --next 05
```
(Also requires Public == Duplicate recorded.)

## Required inputs
- `04__handoff.md` with three fields + fix/blocker/confirm plan
- Docker available, or accept honest Not verified
- Revision passes: platform Judge/Difficulty/Logs when user provides them (P-010/P-011: Judge before Difficulty; target every axis ≥3.5; overreach → sync instruction↔tests; if Judge blocked Difficulty, fix Judge first)

## Read first
- `workflows/stages/S9_branch_execution.md`, `S10_runtime_validation.md`
- `Prompts/modules/branch_fixable.md`, `runtime_validation.md`
- `templates/fixable_checklist.md` (Fixable)
- `validation/checklists/runtime_validation.md`
- Operational Patterns + `knowledge/patterns/INDEX.md` (P-003 hygiene, P-008 SkipTest, P-009 mode-only dirty trees, P-010 Judge before Difficulty, P-011 overreach / ≥3.5)
- Branch sections in `Sentinel_Submitter_Platform_Workflow.mdc`

## Do

### A. Branch (S9)
1. Stop if **04** incomplete or Public ≠ Duplicate.
2. **Fixable** — edit only `working_copy/`:
   - Allowed: instruction + sync problem_statement, `tests.patch` / config / test.sh / grade.py, solve.sh / golden.patch, allowed Dockerfile/metadata, git hygiene
   - Forbidden: tracked `environment/repo` source edits; mutating existing p2p test files; reducing/replacing PR scope
   - After semantic edits:

```bash
python3 automation/sentinel_submitter.py ensure-packaging-hygiene --task-name TASK
python3 automation/sentinel_submitter.py sync-problem-statement --task-name TASK
```

   - Strip network fields; ensure grade.py; prefer `golden.patch` (P-003)
   - Mode-only dirty trees → reset/hygiene, not Invalid (P-009)
   - New tests: hard-fail missing deps (P-008), not SkipTest soft-pass
3. **Valid as-is** — freeze; no task file mutations.
4. **Invalid** — evidence notes only; no “corrected valid” ZIP.

### B. Runtime (S10)
5. Task root: Fixable → `working_copy/`; Valid-as-is → original package root as prepared by automation.
6. Run (prefer):

```bash
python3 automation/local_oracle_nop.py --task-name TASK --mode both
```

7. `record-validation` for docker_build / oracle / nop with **real** evidence paths + rewards.
8. Expectations: Valid-as-is **requires** oracle `1.0` and NOP `0.0`. Fixable: strongly recommended before **06**.
9. If Fixable oracle ≠ 1.0 after claimed fixes → stay in **05** (or `blocked`); do not hand off as Ready.
10. If NOP unexpectedly `1.0` → investigate vacuous grading; do not treat as success.
11. Write `05__handoff.md`: Files Changed (path / what / why, human voice) + short validation paragraph + target **06** ZIP path.
12. **Do not** preflight/package or write `work/task ready_to_submit/` here.

## Do not
- Mutate `extracted_original/`
- Fabricate rewards
- Package early into `task_outputs/.../updated_zip_file/` and call it done
- Expand scope with unrelated features

## Expected outputs
- Updated `working_copy/` (Fixable) or freeze/evidence notes
- `session/validation_logs/` when Executed
- Recorded validation entries
- `05__handoff.md`

## Done when
- Branch matches Duplicate
- `extracted_original/` untouched
- Runtime Executed with expected rewards **or** explicitly Not verified with reason
- Packaging deferred to **06**

## Failure
| Symptom | Action |
|---------|--------|
| Edited extracted_original | Stop; restore; `blocked` |
| Fix requires scope replacement | Return to **04** for Invalid |
| Content edit after green runtime | Re-run oracle/NOP before **06** |

## Next
`checkpoint_ready.py --task-name TASK --next 06` → open **06**.
