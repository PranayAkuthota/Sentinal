# 06 — Answers, Package & Learn

**Canonical daily prompt · Stages S11–S12**  
**Final step** for the submitter pass: platform answers, branch-correct ZIP, learning proposal.

## Purpose
Paste-ready Snorkel answers + correct artifact + reusable framework lessons.  
**Fixable upload path (every time, every revision):**

```text
work/task ready_to_submit/<task-name>__corrected.zip
```

## Gate (must pass)
```bash
python3 automation/checkpoint_ready.py --task-name TASK --next 06
```

## Required inputs
- `04__handoff.md`, `05__handoff.md`
- Validation evidence (Executed or honest Not verified)
- Optional friction notes for learning
- Live form field list in front of you

## Read first
- `docs/SUBMITTER_BLOCKERS.md` ← walk before Fixable upload (include 16b/c overreach + 30b–e Judge ≥3.5)
- `workflows/stages/S11_answers_package.md`, `S12_learning_capture.md`
- `Prompts/modules/package_answers.md`, `learning_capture.md`
- `templates/platform_answers_fixable.txt`, `submitter_audit.md`, `findings_and_changes.md`, `validation_summary.md`
- `validation/checklists/submission_package.md`
- `Sentinel_Submitter_Platform_Workflow.mdc` §13 (Snorkel voice)
- `docs/LEARNING_SYSTEM.md`, `knowledge/patterns/INDEX.md`

## Do

### A. Answers & package (S11)
1. Confirm branch from **04**. For Fixable: walk **SUBMITTER_BLOCKERS** A–I; open blockers must be none.
2. Fill **all** narrative platform fields as **human EC paragraphs** (not LLM/audit tone). Never invent times/rewards.
   - Difficulty, Comments for Reviewer, Internal reason, issue bodies, unfixable explanation, Valid-as-is notes
   - Avoid AI tells (“in order to ensure”, “comprehensive”, “holistic alignment”, stacked em-dashes, identical bullet cadence)
3. **Fixable Files Changed:** every edited path with what + why. Do not re-dump Validation Evidence. Valid-as-is/Invalid list: `None`.
4. Write `task_outputs/<TASK>/platform_answers.txt` + findings/audit/validation reports (same human voice).
5. **Fixable packaging:**

```bash
python3 automation/sentinel_submitter.py preflight --task-name TASK
# only if ready_to_package:
python3 automation/sentinel_submitter.py package-fixable --task-name TASK
```

   - Confirm upload ZIP: `work/task ready_to_submit/<TASK>__corrected.zip`
   - Mirror may exist under `task_outputs/<TASK>/updated_zip_file/` — cite **ready_to_submit** as upload path
   - Every revision: delete-first refresh of the same ready_to_submit file
6. **Invalid:** `package-invalid` → `invalid_evidence/` only (not ready_to_submit).
7. **Valid-as-is:** no corrected ZIP; state confirmations with evidence.
8. Paste full **SENTINEL SUBMITTER PLATFORM ANSWERS** block in chat (human voice).

### B. Learning (S12)
9. Capture proposal:

```bash
python3 automation/capture_learning.py --task-name TASK --notes "…"
```

10. Edit proposal: reusable only; strip UUIDs, spoilers, golden patches, hidden tests.
11. Optional human promote (never auto-edit Ultra policy):

```bash
python3 automation/promote_learning.py pattern --id P-0NN --title "…" --body "…"
python3 automation/promote_learning.py failure --id F-0NN --title "…" --category … \
  --symptom "…" --root-cause-class "…" --recovery "…"
```

12. Write `06__handoff.md`: readiness, ZIP path or none, blockers clearance line, proposal path.

## Do not
- Upload when preflight blocked
- Put `runs/`, reports, or caches in the ZIP
- Leave only the `task_outputs` mirror and call it the upload ZIP
- Auto-merge learning into `Review_Guidelines.mdc`
- Mutate `extracted_original/` or historical archives

## Expected outputs
- `platform_answers.txt` + reports
- Fixable: `work/task ready_to_submit/<TASK>__corrected.zip`
- Invalid evidence ZIP / Valid-as-is: none
- Chat answers block
- `knowledge/proposals/…__proposal.md`
- `06__handoff.md`

## Done when
- Answers match live form for the branch
- Narrative fields sound human
- Packaging rule satisfied; Fixable ZIP exists at ready_to_submit and is cited
- Proposal written; archives untouched
- Ready / Not ready stated honestly

## Failure
| Symptom | Action |
|---------|--------|
| Preflight blockers | Return to **05**; do not ship |
| Valid-as-is missing Executed oracle/NOP | Not ready — do not fabricate |
| Only mirror ZIP exists | Re-run `package-fixable` before telling user to upload |

## End
Submitter pass complete. Upload from `work/task ready_to_submit/` when Fixable and Ready.
