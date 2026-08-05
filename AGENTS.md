# Project Sentinel Instructions

Follow `CLAUDE.md` for mode routing. Policy authority: official Ultra docs + `.cursor/skills/sentinel-ultra-review/reference/` + `.cursor/rules/Review_Guidelines.mdc`. Legacy never overrides Ultra.

## Must

1. **Canonical prompts for every new task:** `Prompts/Execution/` **01 → 06** (one chat per step). Do not invent a mega-prompt.
2. Before Execution **02–06**: `python3 automation/checkpoint_ready.py --task-name TASK --next NN`.
3. Automation never assigns Public / Internal / Duplicate.
4. Never mutate `extracted_original/` or overwrite original ZIPs.
5. Never invent oracle/NOP rewards.
6. Fixable upload ZIP: `work/task ready_to_submit/<task>__corrected.zip` (delete-first).
7. Walk `docs/SUBMITTER_BLOCKERS.md` before Fixable upload.
8. Snorkel narrative fields = human paragraphs (workflow §13).
9. End tasks with `capture_learning.py`; promote via `promote_learning.py` (human).
10. Long framework health: `python3 automation/sentinel_doctor.py`.
11. Before Fixable `preflight` / upload: `static-check` then `judge-prep` (S10.5); write `judge_rehearsal.md` + `.json` via `Prompts/modules/judge_rehearsal.md`. After platform Judge returns: `capture_judge_feedback.py` (see `docs/VALIDATION_STRATEGY.md`). Do not calibrate against historical bounced packages.

## Map

| Need | Open |
|------|------|
| Architecture | `docs/ARCHITECTURE.md` |
| Redesign audit | `docs/FRAMEWORK_REDESIGN_AUDIT.md` |
| Stages S0–S12 | `docs/WORKFLOW.md` |
| Commands | `docs/COMMANDS.md` |
| Blockers | `docs/SUBMITTER_BLOCKERS.md` |
| Harbor format / mechanical checks | `.cursor/skills/sentinel-ultra-review/` |
| Daily interactive | `Prompts/Execution/README.md` (`01`→`06`) |
| First-pass / revision | `Prompts/Submitter_First_Pass.md` / `Submitter_Platform_Revision.md` |
| Execution layer | `docs/EXECUTION_LAYER.md` |
| Patterns | `knowledge/patterns/INDEX.md` |
| Reviewer | `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` |
| Skills | `.cursor/skills/sentinel-*` |

## Reviewer (short)

Read-only. Accept / Needs Revision / Reject. No corrected ZIP. Template: `templates/reviewer_answer.txt`.
