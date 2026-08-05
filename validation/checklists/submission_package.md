# Submission package checklist

## Answers
- [ ] `task_outputs/<task>/platform_answers.txt` complete for live form fields
- [ ] Narrative fields are human EC paragraphs (not LLM/audit tone)
- [ ] Files Changed lists every edited path (Fixable)
- [ ] Difficulty / Comments / Internal reason match evidence

## Blockers
- [ ] `docs/SUBMITTER_BLOCKERS.md` walked; open blockers = none (Fixable upload)

## ZIP — Fixable
- [ ] `preflight` reports `ready_to_package`
- [ ] Upload: `work/task ready_to_submit/<task>__corrected.zip` (delete-first refresh)
- [ ] Mirror under `task_outputs/<task>/updated_zip_file/`
- [ ] Flat contents: `instruction.md`, `task.toml`, `environment/`, `solution/`, `tests/`
- [ ] No `runs/`, reports, `__pycache__`, `.DS_Store`, `ground_truth.*`, misplaced `metadata.json`

## ZIP — Valid as-is
- [ ] No corrected ZIP produced

## ZIP — Invalid
- [ ] Evidence only under `invalid_evidence/`
- [ ] Not uploaded as a corrected valid package

## Learning
- [ ] `capture_learning.py` proposal written
- [ ] Archives / Ultra policy untouched
