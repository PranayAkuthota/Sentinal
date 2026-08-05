# S11 — Platform Answers & Package

## Purpose
Produce paste-ready platform answers and the correct ZIP artifact for the branch. Walk `docs/SUBMITTER_BLOCKERS.md` before claiming ready.

## Inputs
- Verdicts + findings + validation evidence
- Templates under `templates/`
- Preflight readiness for Fixable

## Outputs
### All branches
- `task_outputs/<task>/platform_answers.txt` (+ audit/findings/validation reports)
- Human EC voice for Snorkel narrative fields (workflow §13)

### Fixable
- `preflight` ⇒ `ready_to_package`
- Upload ZIP: `work/task ready_to_submit/<task>__corrected.zip` (delete-first refresh)
- Mirror: `task_outputs/<task>/updated_zip_file/`

### Valid as-is
- No corrected ZIP

### Invalid
- Evidence ZIP under `task_outputs/<task>/invalid_evidence/`

## Validation
- Flat zip contents (no outer `task/`, no `runs/`)
- `problem_statement.md` matches `instruction.md` on corrected packages
- Files Changed lists every edited path (Fixable)
- Blockers checklist clear

## Failure
Preflight blockers; wrong zip shape; LLM-tone paste; claiming Valid-as-is ZIP.

## Recovery
Fix cited blocker; re-run hygiene → validate → preflight → package.

## Automation
`preflight`, `package-fixable`, `package-invalid`. Answers prose is expert.
