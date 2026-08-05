# Sentinel Submitter Automation

Deterministic gates and helpers. **Never decides verdicts.**

See `docs/COMMANDS.md` and `docs/ARCHITECTURE.md`.

## Scripts

| Script | Role |
|--------|------|
| `sentinel_submitter.py` | Intake, audit, verdicts record, hygiene, preflight, package |
| `lib/` | Shared helpers (verdicts, paths, package, hygiene, sync, toml) |
| `local_oracle_nop.py` | Docker oracle/NOP evidence |
| `docker_grade_f2p.py` | In-container f2p grader helper |
| `checkpoint_ready.py` | Execution handoff readiness before 02–06 |
| `capture_learning.py` | Post-task proposal from real state only (never `(edit)` placeholders) |
| `write_judge_prediction.py` | Upload-time Judge prediction (`judge_prediction.json`) |
| `capture_judge_feedback.py` | Canonical record → `knowledge/judge_feedback/` + prediction join |
| `judge_stats.py` | Forward calibration: predicted vs actual P/R |
| `promote_learning.py` | Human-assisted promote → patterns/failures |
| `sentinel_doctor.py` | Framework health score (depth-aware) |

## Simple path

```bash
python3 automation/sentinel_doctor.py
python3 automation/sentinel_submitter.py intake --zip /ABS/PATH/task.zip
python3 automation/sentinel_submitter.py prepare --task-name TASK
python3 automation/sentinel_submitter.py audit --task-name TASK
python3 automation/checkpoint_ready.py --task-name TASK --next 02
# expert: Execution 02–04 …
python3 automation/sentinel_submitter.py set-verdicts --task-name TASK ...
python3 automation/checkpoint_ready.py --task-name TASK --next 05
python3 automation/sentinel_submitter.py ensure-packaging-hygiene --task-name TASK
python3 automation/local_oracle_nop.py --task-name TASK --mode both
python3 automation/sentinel_submitter.py preflight --task-name TASK
python3 automation/sentinel_submitter.py package-fixable --task-name TASK
python3 automation/capture_learning.py --task-name TASK
```

Expert review remains required for all semantic judgements.

## Framework tests

```bash
python3 -m pytest repo_tests/ -q
bash ci_checks/run_framework_checks.sh
```
