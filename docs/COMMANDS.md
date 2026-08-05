# Sentinel Commands

Use `python3` and **absolute paths**. Pass `--task-name` whenever multiple `work/*` sessions exist.

Interactive daily flow (does not change S0–S12): `docs/EXECUTION_LAYER.md` and `Prompts/Execution/`.

## Core submitter gate script

```bash
python3 automation/sentinel_submitter.py intake --zip /ABS/PATH/task.zip
python3 automation/sentinel_submitter.py prepare --task-name TASK
python3 automation/sentinel_submitter.py audit --task-name TASK
python3 automation/sentinel_submitter.py set-verdicts --task-name TASK \
  --public-analysis Fixable|Invalid/Not Fixable|Valid as-is \
  --internal-validity Invalid|Fixable|Valid-as-is \
  --duplicate-analysis Fixable|Invalid/Not Fixable|Valid-as-is \
  --reason "evidence-based"
python3 automation/sentinel_submitter.py ensure-packaging-hygiene --task-name TASK   # Fixable only
python3 automation/sentinel_submitter.py sync-problem-statement --task-name TASK     # Fixable only
python3 automation/sentinel_submitter.py record-validation --task-name TASK \
  --check docker_build|oracle|nop|... --status passed|failed|not_run --evidence PATH [--reward N]
python3 automation/sentinel_submitter.py preflight --task-name TASK
python3 automation/sentinel_submitter.py package-fixable --task-name TASK
# → work/task ready_to_submit/<TASK>__corrected.zip  (canonical upload; delete-first refresh)
# → task_outputs/<TASK>/updated_zip_file/<TASK>__corrected.zip  (mirror)
python3 automation/sentinel_submitter.py package-invalid --task-name TASK
python3 automation/sentinel_submitter.py status --task-name TASK
python3 automation/sentinel_submitter.py archive --task-name TASK
```

### Packaging destinations

| Branch | Path |
|--------|------|
| Fixable (upload) | `work/task ready_to_submit/<TASK>__corrected.zip` |
| Fixable (mirror) | `task_outputs/<TASK>/updated_zip_file/<TASK>__corrected.zip` |
| Invalid evidence | `task_outputs/<TASK>/invalid_evidence/<TASK>__unfixable_evidence.zip` |
| Valid-as-is | no corrected ZIP |

## Runtime validation

```bash
python3 automation/local_oracle_nop.py --task-name TASK --mode both
```

## Execution checkpoint readiness

```bash
python3 automation/checkpoint_ready.py --task-name TASK --next 02   # or 03..06
```

Verifies prior `session/execution/NN__handoff.md` files exist with `status: complete`.  
For `--next 05` or `06`, also requires Public == Duplicate via `set-verdicts`.

## Learning (post-task)

```bash
python3 automation/capture_learning.py --task-name TASK
python3 automation/promote_learning.py pattern --id P-0NN --title "…" --body "…"
python3 automation/promote_learning.py failure --id F-0NN --title "…" --category tests_patch \
  --symptom "…" --root-cause-class "…" --recovery "…"
```

`capture_learning` writes a **proposal** under `knowledge/proposals/` only.  
`promote_learning` assists human promotion into `knowledge/patterns/` or `knowledge/failures/`.  
Neither modifies historical ZIPs nor auto-edits Ultra policy.

Pre-submit blockers: `docs/SUBMITTER_BLOCKERS.md`. Failure catalog: `docs/FAILURE_CATALOG.md`.

## Doctor (repo health)

```bash
python3 automation/sentinel_doctor.py
```

Scores layout, stage/module depth, skills, learning artifacts, checkpoint tooling, and repo_tests (not layout alone).

## Framework tests / CI

```bash
bash ci_checks/run_framework_checks.sh
# or unittest fallback:
python3 ci_checks/run_unittest_suite.py
# or pytest if installed:
python3 -m pytest repo_tests/ -q
```

## Cross-task aggregate (optional, read-only)

```bash
python3 automation/aggregate_workflow_states.py
python3 automation/aggregate_workflow_states.py --json
```

Never uses aggregates to auto-assign verdicts.
