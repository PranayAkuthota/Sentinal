# S1 — Intake & Preserve

## Purpose
Preserve the original submission ZIP immutably and create an isolated work session.

## Inputs
- Task ZIP path (absolute preferred)
- Optional platform metadata blob (paste into `session/platform_input.*`)

## Outputs
- `work/<task>/original/<zip>` (never overwrite)
- `work/<task>/extracted_original/` (never mutate)
- `work/<task>/session/session.json` (+ SHA of original ZIP)
- Task root resolved under extracted tree

## Validation
- SHA256 of preserved ZIP recorded
- Extracted tree contains a Harbor `task/` or flat task root
- `extracted_original/` is read-only by convention thereafter

## Failure
Corrupt ZIP; ambiguous nested task roots; accidental write into `extracted_original/`.

## Recovery
Re-intake from the user-supplied original; delete broken session only if original ZIP still intact. Never “fix” by editing `extracted_original/`.

## Automation
`sentinel_submitter.py intake`, `prepare`, `select-task`.
