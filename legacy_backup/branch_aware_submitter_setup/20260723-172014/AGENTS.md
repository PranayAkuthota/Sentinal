# Project Sentinel Instructions

Follow the Project Sentinel orchestration and operating-mode rules in `CLAUDE.md`.

`CLAUDE.md` must explicitly load the relevant role-specific rule files before work begins (see **Mandatory Role-Specific Rule Loading** in `CLAUDE.md`).

Use these Cursor rules:

- `.cursor/rules/Review_Guidelines.mdc` for authoritative Sentinel policy
- `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` for the complete **read-only** submitter platform-answer workflow (`ZIP + platform metadata → read-only audit → task assessment → paste-ready form answers`)
- `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` for quick-reference checklists and field mapping
- `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` for reviewer-specific procedure

## Submitter Mode (entry)

When you provide a Sentinel task ZIP, platform metadata (Original Directory Name, Category, Difficulty, Task Tags, Languages, Metadata), and say any equivalent of **I am working as a submitter. Start working.**, Cursor must:

1. Read `Review_Guidelines.mdc`, `Sentinel_Submitter_Platform_Workflow.mdc`, and `Sentinel_Expert_Contributor_Reference.mdc`
2. Inspect the ZIP and task, verify platform metadata against the package, decide Valid as-is / Fixable / Not Fixable for the **original** task
3. Perform a complete read-only audit, classify the original task and produce paste-ready submitter answers **in the chat response**. Do not modify the supplied task.

Submitter Mode is:

- **Read-only**
- **No task edits**
- **No corrected ZIP**
- **Fixable means report the issues only**
- **Chat-only answers** — do not create `sentinel_platform_answers.txt`, `sentinel_submitter_audit.md`, `sentinel_findings.md`, `sentinel_submitter_session.json`, or similar output files

You should not need to paste another long workflow prompt.

The official Sentinel Ultra documents dated July 22, 2026 (`document 1.txt`, `document 2.txt`, `document 3.txt`) override conflicting legacy rules.

Never mix submitter and reviewer verdicts, workflows or output templates.
