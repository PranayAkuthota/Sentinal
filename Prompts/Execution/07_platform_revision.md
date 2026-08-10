# 07 — Platform Revision

**Canonical daily prompt · Revision round after NEEDS_REVISION / Judge bounce**  
**Chat mode:** one focused conversation. Packaging stays in **06**.

## Purpose
Process platform feedback after a bounce: **route via the revision case library**, capture
into the ledger, fix cited defects, re-validate via **05**, then hand off to **06**.  
**No packaging in this step.** Scripts never assign verdicts.

## Gate (must pass)
```bash
python3 automation/checkpoint_ready.py --task-name TASK --next 07 \
  --platform-zip /ABS/PATH/TO/platform_downloaded/TASK__corrected.zip
```
Requires `06__handoff.md` complete + Public == Duplicate recorded.  
**F-014 / pitfall 11:** if `task_outputs/TASK/updated_zip_file/TASK__corrected.zip` exists,
SHA-256 **must** match `--platform-zip` or the checkpoint **FAILS LOUDLY**.

## Required inputs
- Pasted platform report (Quality / Judge citations; Difficulty **only if it ran**; reviewer notes)
- **Platform-downloaded** corrected ZIP via `--platform-zip`
- `06__handoff.md` (or `--resume-revision` reason)
- Prior `judge_prediction.json` when present

## Read first
- **`knowledge/revision_library/ROUTER.md`** ← **FIRST action after capture**
- `knowledge/revision_library/README.md` (honesty / contradiction pair Case 05↔06)
- `knowledge/revision_library/pitfalls/` (process checks — never “the defect to edit”)
- `Prompts/Execution/README.md`
- `knowledge/patterns/P-010_*`, `P-011_*`, `P-006_*`, `P-012_*`
- `docs/SUBMITTER_BLOCKERS.md`
- `docs/VALIDATION_STRATEGY.md`

## Do

0. **Verify the package (pitfall 11)** — `checkpoint_ready --next 07 --platform-zip …`.
   Confirm oracle/NOP were real if you claimed them (pitfall 18) — do not invent numbers.

1. **Capture feedback FIRST** (before edits). Construct flags from the pasted report:

```bash
python3 automation/capture_judge_feedback.py --task-name TASK \
  --verdict OK|DISCUSS|REMOVE \
  --verdict-reason weak_check|overreach|coverage_gap|… \
  --axes-json '{"test_coverage":…,"test_faithfulness":…,"prescriptiveness":…}' \
  --citation 'quoted platform text||axis=test_faithfulness' \
  --notes '…'
# --difficulty-run only when Difficulty actually ran
python3 automation/judge_stats.py
```

   Capture **archives the prior tip** into `knowledge/judge_feedback/history/` and chains
   citations into `next_round_result` (resolved / not_resolved / regressed). Report the chain
   tally. If rehearsal predicted OK and live DISCUSS, note pitfall 12 — still fix **citations**.

2. **Library FIRST (before any fixing)**  
   Open `ROUTER.md`. Classify stage (Judge / Manual Reviewer / Difficulty). Open the matching
   **case** file(s). Do not open a pitfall as the edit target.  
   If nothing matches → create a new **PROVISIONAL** case from the case template; do not force-fit.  
   If the fix you want **contradicts** case guidance →  
   `python3 automation/revision_library_maintain.py contradict …` (exits 1; do not overwrite).

3. **P-010:** If Judge blocked Difficulty, Judge citations are the only actionable feedback.

4. For **each** citation, choose **ONE** direction (case Fix section) and write one line:
   - coverage → Case 04 (add assert **or** trim claim)
   - faithfulness/overreach → Case 05 (state contract **or** soften test) ⚠ Case 06
   - Q9/Q10 / how-to / suite-leak → Case 06 ⚠ Case 05
   - Manual Reviewer packaging → Case 01; editing-boundary → Case 02
   - Difficulty FAIL EASY after Judge OK → Case 03  
   Never both sides of a contradicting pair.

5. Re-run **05** Fixable sequence on `working_copy/` (no packaging): hygiene, sync,
   static-check, judge-prep, rehearsal. Axes ≥ 3.5 before re-upload.

6. **Do not package here.** → **06** for re-package + prediction + answers.  
   At packaging time **must** record per-citation fixes on the tip:

```bash
python3 automation/record_revision_fixes.py --task-name TASK \
  --fix 'one-line change||file=path||axis=test_coverage||cite=substring of citation'
```

7. Write `07__handoff.md`: router case ids, citations, one-direction fixes, capture paths,
   chain tally, residual risks, next = **06**.

8. Append a dated row to each used case’s **Instances** section. Second independent hit on a
   PROVISIONAL case → `revision_library_maintain.py promote`.  
   Coverage gate: `python3 automation/revision_library_coverage.py` (must stay green).

## Do not
- Fix before capture **or** before router/case read
- Route feedback to pitfalls (11/12/18)
- Revise stale `updated_zip_file` without SHA match
- Silently overwrite case Fix guidance (use contradict)
- Invent Difficulty/Oracle/rewards
- Package in this step

## Expected outputs
- Updated `knowledge/judge_feedback/` tip + history chain
- Case Instances rows / possible new provisional case
- Fixed `working_copy/` + static-check / judge-prep / rehearsal
- `07__handoff.md`

## Done when
- Feedback captured; router case chosen; one-direction fix per citation
- Rehearsal axes ≥ 3.5 (or honest blocked)
- Packaging deferred to 06 with `record_revision_fixes` planned/done there

## Failure
| Symptom | Action |
|---------|--------|
| SHA mismatch | Stop; re-import platform ZIP (pitfall 11) |
| Coverage script orphans | Add Instances id or new provisional case |
| Contradiction pending | Human decides before editing Fix section |
