# 01 — Boot & Structural Audit

**Canonical daily prompt · Stages S0–S2**  
**Chat mode:** one focused conversation. Pause after handoff before opening **02**.

## Purpose
Confirm submitter mode, preserve the ZIP immutably, run structural Harbor audit.  
**No verdict. No content fixes. No packaging.**

## Required inputs
- Absolute path to the task ZIP
- Platform metadata paste (when available)
- Submitter intent (ask once if unclear)

## Read first (do not dump into chat)
- `Prompts/Execution/README.md`
- `workflows/stages/S0_framework_boot.md`, `S1_intake_preserve.md`, `S2_structural_audit.md`
- `Prompts/modules/intake.md`, `structural_audit.md`
- `validation/checklists/structural_preflight.md`
- `docs/COMMANDS.md`
- `knowledge/patterns/INDEX.md` (P-001 patch apply, P-002 ungraded tests, P-005 paths)

## Do
1. Confirm mode = **submitter** (not reviewer).
2. Use `python3` + absolute paths. If multiple `work/*` sessions exist, plan to pass `--task-name` always.
3. Intake → prepare → audit:

```bash
python3 automation/sentinel_submitter.py intake --zip /ABS/PATH/task.zip
python3 automation/sentinel_submitter.py prepare --task-name TASK
python3 automation/sentinel_submitter.py audit --task-name TASK
```

4. Save metadata to `work/<TASK>/session/platform_input.txt` when provided.
5. Verify `original/`, `extracted_original/`, `working_copy/`, `session/` exist; never mutate `extracted_original/`.
6. Summarize only structural facts for the handoff:
   - task root / format dialect (current vs legacy)
   - f2p / p2p counts from config
   - instruction ↔ problem_statement sync
   - `tests.patch` **git-apply** status + hunk health (not patch-only — P-001)
   - ungraded `+def test_*` when `allow_extra_failures` (P-002)
   - network fields, metadata limits, git hygiene
7. Label evidence: Inspected / Executed / Not verified. **Do not** set Public/Internal/Duplicate.
8. Write `session/execution/01__handoff.md` using `templates/execution_handoff.md` with `status: complete|blocked|partial`.
9. Draft findings in **human EC voice** (will feed Snorkel later).

## Do not
- Edit instruction/tests/oracle/Dockerfile in this step
- Write anything under `work/task ready_to_submit/`
- Claim Valid/Fixable/Invalid from structure alone
- Re-run work from archives (`docs/history/`, old `task_outputs` ZIPs) as “the” task

## Expected outputs
- Preserved ZIP + SHA in session
- Audit artifacts under `work/<TASK>/analysis/` and/or `task_outputs/<TASK>/`
- Chat: short structural summary
- `01__handoff.md` with `task_name`, ZIP path, f2p count, top risks, audit paths

## Done when
- Intake did not overwrite original unless user forced re-intake
- Audit finished on `extracted_original`
- Handoff has `status: complete` (or honest `blocked`)
- No premature package / no verdicts

## Failure
| Symptom | Action |
|---------|--------|
| Corrupt / ambiguous ZIP | Stop; require explicit `--zip` |
| Prepare cannot find task root | Fix selection; handoff `blocked` |
| Audit crashes | Capture error; do not invent counts |

## Next
Open **02** only after inspecting `01__handoff.md`.  
`python3 automation/checkpoint_ready.py --task-name TASK --next 02`
