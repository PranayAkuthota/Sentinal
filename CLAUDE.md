# Project Sentinel — Cursor Orchestration Controller

**Last updated:** August 1, 2026 (framework harden); August 4, 2026 Agent Judge–first eval (P-010); August 4, 2026 overreach / ≥3.5 bar (P-011)

If this file conflicts with `Review_Guidelines.mdc`, follow `Review_Guidelines.mdc`.

This file routes work. It does **not** redefine Ultra policy.

## Authority stack

1. Official Ultra docs + live platform fields  
2. User instruction (non-conflicting)  
3. `.cursor/rules/Review_Guidelines.mdc`  
4. Role workflow `.mdc`  
5. `docs/WORKFLOW.md` stages + `docs/EXECUTION_LAYER.md`  
6. `Prompts/` modules + Execution checkpoints  
7. `knowledge/` patterns (approved)  

## Start maps

- Architecture: `docs/ARCHITECTURE.md`  
- Commands: `docs/COMMANDS.md`  
- Redesign record: `docs/FRAMEWORK_REDESIGN_AUDIT.md`  
- Blockers: `docs/SUBMITTER_BLOCKERS.md`  

## Modes

### Submitter

Triggers: “I am working as a submitter…”, process/prepare/audit submission, ZIP + metadata provided.

Daily: `Prompts/Execution/` **01→06** with `checkpoint_ready` between steps.  
Orchestrators: `Submitter_First_Pass.md` / `Submitter_Platform_Revision.md`.  
Skill: `.cursor/skills/sentinel-submitter`.  
Stages: S0–S12 in `docs/WORKFLOW.md`.

### Reviewer

Triggers: “I am working as a reviewer…”. Skill: `sentinel-reviewer`. Read-only.

### Framework maintenance

Triggers: redesign rules/automation/docs. Do not mutate `work/` task ZIPs or `task_outputs` historical packages unless explicitly migrating docs.

## Safety

- Ignore archives when selecting tasks: `legacy_backup/`, `workspace_archive/`, `completed_tasks/`, `docs/history/`, prior `task_outputs` ZIPs as “the” task  
- Mutations only on `working_copy/` for Fixable  
- Absolute paths; `python3`; `--task-name` if multiple sessions  
- Never invent validation rewards or times  
- Scripts never set Public/Internal/Duplicate  

## Automation flow

```text
intake → prepare → audit → (Execution 01–04) → set-verdicts
  → checkpoint_ready --next 05 → Fixable edits / freeze / evidence
  → ensure-packaging-hygiene → sync-problem-statement
  → local_oracle_nop → record-validation → preflight → package-*
  → capture_learning → (optional) promote_learning → status/archive
```

## Outputs

Chat: full platform answers block (Snorkel narrative fields = human paragraphs; workflow §13).  
Disk: `task_outputs/<task>/` reports + ZIP mirrors; Fixable upload ZIP at `work/task ready_to_submit/<task>__corrected.zip`.  
Learning: `knowledge/proposals/` then human promotion to patterns/failures.
