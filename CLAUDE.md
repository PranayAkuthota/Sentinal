# Project Sentinel — Cursor Orchestration Controller

**Last updated:** August 5, 2026 (sentinel-ultra-review skill merge + static-check)

If this file conflicts with official Ultra docs or `.cursor/skills/sentinel-ultra-review/reference/`, follow those. Then `.cursor/rules/Review_Guidelines.mdc`.

This file routes work. It does **not** redefine Ultra policy.

## Authority stack

1. Official Ultra docs + live platform fields  
2. `.cursor/skills/sentinel-ultra-review/reference/` (Harbor format, checklists, verdict rubric, test quality)  
3. Current user instruction, only when it does not conflict with authoritative project requirements  
4. `.cursor/rules/Review_Guidelines.mdc`  
5. Role workflow (`.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` / `Sentinel_Reviewer_Step_by_Step.mdc`)  
6. `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc`  
7. `docs/WORKFLOW.md` stages + `docs/EXECUTION_LAYER.md`  
8. `Prompts/` modules + Execution checkpoints  
9. `knowledge/` patterns (approved)  

## Start maps

- Architecture: `docs/ARCHITECTURE.md`  
- Commands: `docs/COMMANDS.md`  
- Mechanical gate: `python3 automation/sentinel_submitter.py static-check --task-name TASK`  
- Ultra EC skill: `.cursor/skills/sentinel-ultra-review/`  
- Redesign record: `docs/FRAMEWORK_REDESIGN_AUDIT.md`  
- Blockers: `docs/SUBMITTER_BLOCKERS.md`  

## Modes

### Submitter

Triggers: “I am working as a submitter…”, process/prepare/audit submission, ZIP + metadata provided.

Daily: `Prompts/Execution/` **01→06** with `checkpoint_ready` between steps.  
Orchestrators: `Submitter_First_Pass.md` / `Submitter_Platform_Revision.md`.  
Skills: `.cursor/skills/sentinel-submitter`, `.cursor/skills/sentinel-ultra-review`, `.cursor/skills/sentinel-packager`.  
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
  → static-check → local_oracle_nop → record-validation → preflight → package-*
  → capture_learning → (optional) promote_learning → status/archive
```

`preflight` / `package-fixable` refuse `ready_to_package` while any static-check **FIXABLE** or **NOT_FIXABLE** finding is open. **ADVISORY** findings warn only.

## Outputs

Chat: full platform answers block (Snorkel narrative fields = human paragraphs; workflow §13).  
Disk: `task_outputs/<task>/` reports + ZIP mirrors; Fixable upload ZIP at `work/task ready_to_submit/<task>__corrected.zip`.  
Learning: `knowledge/proposals/` then human promotion to patterns/failures.
