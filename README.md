# Sentinel Ultra — Submitter Framework

AI-assisted framework for **Snorkel Sentinel Ultra** Expert Contributors working Harbor-format tasks.

## Start here

| Role | Open |
|------|------|
| New engineer | `docs/ARCHITECTURE.md` → `docs/WORKFLOW.md` → `docs/COMMANDS.md` |
| Submitter (daily, pauseable) | `Prompts/Execution/README.md` → `01`…`06` |
| Submitter (single-shot) | `Prompts/Submitter_First_Pass.md` |
| Platform revision | `Prompts/Submitter_Platform_Revision.md` |
| Pre-submit blockers | `docs/SUBMITTER_BLOCKERS.md` |
| Reviewer | `.cursor/skills/sentinel-reviewer` + reviewer rules |
| Agent router | `AGENTS.md` / `CLAUDE.md` |
| Redesign record | `docs/FRAMEWORK_REDESIGN_AUDIT.md` |

**Policy authority:** `.cursor/rules/Review_Guidelines.mdc` + official `document 1/2/3.txt`.

## Layout

```text
incoming_tasks/     drop ZIPs
work/               per-task workspaces (+ task ready_to_submit/)
task_outputs/       answers, reports, corrected/evidence ZIPs
completed_tasks/    archives
automation/         deterministic gates + lib/ (no verdicts)
docs/               architecture, workflow, blockers, learning
workflows/stages/   S0–S12 stage contracts
Prompts/            Execution 01–06 + modules/
templates/          output skeletons
validation/         checklists
knowledge/          patterns, failures, proposals
repo_tests/         framework regression tests
ci_checks/          doctor + pytest runner
.cursor/rules/      policy + procedures
.cursor/skills/     opt-in role macros
```

## Quick command path

```bash
python3 automation/sentinel_doctor.py
python3 automation/sentinel_submitter.py intake --zip /ABS/PATH/task.zip
python3 automation/checkpoint_ready.py --task-name TASK --next 02
# … see docs/COMMANDS.md …
python3 automation/capture_learning.py --task-name TASK
bash ci_checks/run_framework_checks.sh
```

## Invariants

- Scripts never choose Public / Internal / Duplicate
- Never mutate `extracted_original/` or overwrite original ZIPs
- Never put reports inside upload ZIPs
- Framework improves via `knowledge/proposals` → human promotion — not by rewriting history
