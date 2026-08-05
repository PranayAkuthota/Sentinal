# Project Sentinel Instructions

Follow the Project Sentinel orchestration and operating-mode rules in `CLAUDE.md`.

`CLAUDE.md` controls routing and must load the relevant role-specific rule files before work begins.

Use these Cursor rules:

- `.cursor/rules/Review_Guidelines.mdc` — authoritative Sentinel policy
- `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` — branch-aware submitter workflow
- `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` — quick-reference checklists and field mapping
- `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` — reviewer-specific procedure

File helpers (no verdict decisions): `automation/sentinel_submitter.py`

## Submitter Mode (entry)

When you provide a Sentinel task ZIP, platform metadata, and say any equivalent of **I am working as a submitter. Start working.**, Cursor must:

1. Read `Review_Guidelines.mdc`, `Sentinel_Submitter_Platform_Workflow.mdc`, and `Sentinel_Expert_Contributor_Reference.mdc`
2. Intake and preserve the original ZIP unchanged
3. Audit the original task completely
4. Determine Public Main Analysis; determine Internal Validity separately; set Duplicate Analysis to match Public Main Analysis
5. Follow the branch selected by **Duplicate Analysis**
6. Return all platform answers in chat and under `task_outputs/`

### Branch rules

- **Fixable** — permitted changes only in `work/<task>/working_copy/`; validate; create corrected flat ZIP under `task_outputs/<task>/updated_zip_file/`
- **Invalid/Not Fixable** — diagnose; prepare manual-review evidence package under `task_outputs/<task>/invalid_evidence/` (not a corrected valid ZIP)
- **Valid-as-is** — confirm requirements; make no task changes; create no new task ZIP

Original task ZIP must always be preserved. Generated files belong under `task_outputs/`. All answers must be returned in chat.

You should not need to paste another long workflow prompt.

The official Sentinel Ultra documents dated July 22, 2026 (`document 1.txt`, `document 2.txt`, `document 3.txt`) override conflicting legacy rules.

Never mix submitter and reviewer verdicts, workflows or output templates.
