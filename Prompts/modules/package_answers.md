# Module: Platform Answers & Package (S11)

Load during Execution **06**.

## Do
1. Walk `docs/SUBMITTER_BLOCKERS.md` (zero open blockers for Fixable upload).
2. Fill platform answers in **human EC paragraphs** (workflow §13) using templates.
3. Fixable: `preflight` → only if `ready_to_package` → `package-fixable`.
4. Cite upload path: `work/task ready_to_submit/<TASK>__corrected.zip`.
5. Valid-as-is: answers only (no corrected ZIP). Invalid: `package-invalid` evidence path.
6. Files Changed must list every edited file on Fixable.

## Do not
- Upload when preflight blocked
- Put reports/`runs/` inside the ZIP
- Use LLM/audit-bot tone in Snorkel paste fields

## Handoff must include
Answers path, ZIP path (or N/A), preflight result, blockers cleared.
