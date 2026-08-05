# 07 — Platform Revision

**Canonical daily prompt · Revision round after NEEDS_REVISION / Judge bounce**  
**Chat mode:** one focused conversation. Packaging stays in **06**.

## Purpose
Process platform feedback after a bounce: capture it into the ledger **first**, fix the
cited defects, re-validate via the **05** sequence, then hand off to **06** for
preflight / package / prediction / answers.  
**No packaging in this step.** Scripts never assign verdicts.

## Gate (must pass)
```bash
python3 automation/checkpoint_ready.py --task-name TASK --next 07
```
Requires `06__handoff.md` complete + Public == Duplicate recorded.  
Escape for pre-framework sessions: `--resume-revision "reason"` (see `checkpoint_ready --help`).

## Required inputs
- Pasted platform report (Quality Check per-axis with citations; Difficulty **only if it ran**; Static Checks)
- Prior corrected ZIP / `working_copy/` from the bounced upload
- `06__handoff.md` (or `--resume-revision` reason)
- Prior `task_outputs/<TASK>/judge_prediction.json` when present

## Read first
- `Prompts/Execution/README.md` (revision loop)
- `knowledge/patterns/P-010_agent_judge_before_difficulty.md`
- `knowledge/patterns/P-011_agent_judge_overreach_sync_instruction_tests_target_axis_sco.md`
- `knowledge/patterns/P-006_*` (trim untested claims over filler)
- `docs/SUBMITTER_BLOCKERS.md` items 16b–16h, 30b–e
- `Prompts/modules/judge_rehearsal.md`
- Optional single-shot: `Prompts/Submitter_Platform_Revision.md`
- `docs/VALIDATION_STRATEGY.md` (ledger / calibration)

## Do
1. **Capture feedback FIRST** — before any fix. Read the pasted platform report and
   **construct** the capture command (map axes → `--axes-json`; each cited defect → a
   `--citation`). Do not skip this; the ledger never fills if it is skipped.

```bash
python3 automation/capture_judge_feedback.py --task-name TASK \
  --verdict OK|DISCUSS|REMOVE \
  --verdict-reason weak_check|overreach|… \
  --axes-json '{"test_coverage":…,"test_faithfulness":…,"prescriptiveness":…}' \
  --citation 'quoted text||axis=test_faithfulness' \
  --notes '…'
# add --difficulty-run only when Difficulty actually ran; else omit or use --difficulty-unknown
python3 automation/judge_stats.py
```

   Report how the prediction compared to the actual. (`--file` is a possible later ergonomic
   improvement — not available this pass; agent-constructed flags are required.)

2. **P-010:** If the Judge blocked Difficulty, Judge citations are the **only** actionable
   feedback. Do not chase difficulty numbers that were never produced.

3. For **each** citation, choose **ONE** direction and justify it in one line:
   - **coverage gap** → add a real graded assertion, **or** trim the untested claim
     (P-006 prefers trimming over filler tests)
   - **overreach** → soften/remove the assertion, **or** state the requirement in the
     instruction (P-011)
   Never both sides of a pair. Chasing coverage without syncing the instruction is exactly
   what flipped tasks to overreach on the following round.

4. Re-run the **05** Fixable sequence on `working_copy/` (no packaging):

```bash
# after semantic edits:
python3 automation/sentinel_submitter.py ensure-packaging-hygiene --task-name TASK
python3 automation/sentinel_submitter.py sync-problem-statement --task-name TASK
python3 automation/sentinel_submitter.py static-check --task-name TASK
python3 automation/sentinel_submitter.py judge-prep --task-name TASK
# then Prompts/modules/judge_rehearsal.md → judge_rehearsal.md + .json
```

   Every Agent Judge axis **≥ 3.5** before re-upload. Record decisions in
   `judge_prep_decisions.json`. Note any SAMPLE_HIT.

5. **Do not package here.** Next → **06** for delete-first re-package, new prediction, and
   refreshed platform answers (including total-time adjusted for the additional revision work).

6. Write `07__handoff.md`: citations handled, capture/stats paths, axis bar, residual risks,
   next = **06**.

## Do not
- Fix before capturing feedback
- Re-upload while any Judge axis is below 3.5
- Claim Difficulty results the Judge blocked
- Leave `discuss (overreach)` unresolved
- Invent scores the report did not state
- Package into `work/task ready_to_submit/` in this step
- Mutate `extracted_original/`

## Expected outputs
- Updated `knowledge/judge_feedback/` entry + `judge_stats` comparison notes
- Fixed `working_copy/` + refreshed static-check / judge-prep / rehearsal
- `07__handoff.md`

## Done when
- Feedback captured before edits
- Each citation has a one-line one-direction fix
- Rehearsal axes ≥ 3.5 (or honest blocked)
- Packaging deferred to **06**

## Failure
| Symptom | Action |
|---------|--------|
| Capture skipped / ledger empty | Stop; run step 1 before any edit |
| Axis still &lt; 3.5 | Stay in **07**; P-011 sync; do not open **06** as Ready |
| Scope replacement required | Return to **04** for Invalid lean |
| Missing 06 handoff (legacy task) | `checkpoint_ready --next 07 --resume-revision "…"` |

## Next
`checkpoint_ready.py --task-name TASK --next 06` → open **06** (re-package + answers + prediction).
