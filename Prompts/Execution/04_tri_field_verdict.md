# 04 — Tri-Field Verdict

**Canonical daily prompt · Stage S8**  
**Hard gate:** no Fixable mutations and no packaging until this step completes with Public == Duplicate.

## Purpose
Expert-only assignment of the three live platform fields. Record them; choose the **05** branch.

## Gate (must pass)
```bash
python3 automation/checkpoint_ready.py --task-name TASK --next 04
```

## Required inputs
- Handoffs **01**, **02**, **03** (all `complete` unless explicitly waived with reason)
- Live platform label wording (follow the form in front of you)

## Read first
- `workflows/stages/S8_tri_field_verdict.md`
- `Prompts/modules/verdict.md`
- `Sentinel_Submitter_Platform_Workflow.mdc` — three fields / branches
- `Review_Guidelines.mdc` — Submitter Verdicts (Valid as-is / Fixable / Not Fixable)
- `templates/platform_answers_fixable.txt` (field shape only)

## Do
1. Synthesize 01–03; re-open files only if handoffs conflict.
2. Choose **Public Main Analysis**, **Internal Validity** (+ reason), **Duplicate Analysis** using **live** labels.
3. Ensure Public matches Duplicate (same semantic branch).
4. Map Not Fixable → live **Invalid/Not Fixable** (or exact live wording).
5. Write Internal reason as a normal human paragraph (what you saw, why that label).
6. Record (script records only — you choose values):

```bash
python3 automation/sentinel_submitter.py set-verdicts --task-name TASK \
  --public-analysis "..." \
  --internal-validity "..." \
  --duplicate-analysis "..." \
  --reason "..."
```

7. State **05** branch contract:
   - **Fixable** → prioritized fix list (instruction / tests / oracle / env / metadata)
   - **Valid as-is** → confirmation plan (oracle 1.0 + NOP 0.0 required in **05**)
   - **Invalid/Not Fixable** → blocker summary (evidence only in **06**)
8. Packaging expectation for **06** (do not package now):
   - Fixable → `work/task ready_to_submit/<task>__corrected.zip`
   - Valid-as-is → no corrected ZIP
   - Invalid → `task_outputs/<task>/invalid_evidence/` only
9. Write `04__handoff.md` with exact three fields + branch + fix/blocker list.

## Do not
- Let automation choose the three fields
- Edit `working_copy/` in this step
- Mix reviewer outcomes (Accept / Needs Revision / Reject) into submitter fields
- Guess when evidence is incomplete — return to **02** or **03**

## Expected outputs
- Verdicts in session / workflow_state
- Chat statement of three fields + Internal reason
- `04__handoff.md` (branch contract)

## Done when
- All three fields set; Internal reason non-empty
- Public ≡ Duplicate
- `set-verdicts` succeeded
- No content mutations; no ZIP

## Failure
| Symptom | Action |
|---------|--------|
| Public ≠ Duplicate | `blocked`; reconcile before **05** |
| Thin evidence | `partial`; reopen weak prior step |

## Next
`checkpoint_ready.py --task-name TASK --next 05` → open **05**.
