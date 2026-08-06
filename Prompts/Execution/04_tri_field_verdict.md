# 04 — Tri-Field Verdict

**Canonical daily prompt · Stage S8**  
**Hard gate:** no Fixable mutations and no packaging until this step completes with Public == Internal == Duplicate (same semantic branch).

## Purpose
Expert-only assignment of the three live platform fields. Record them; choose the **05** branch.

## Gate (must pass)
```bash
python3 automation/checkpoint_ready.py --task-name TASK --next 04
```

## Required inputs
- Handoffs **01**, **02**, **03** (all `complete` unless explicitly waived with reason)
- `task_outputs/<TASK>/static_check_report.md` (from **01**)
- `task_outputs/<TASK>/judge_prep.md` (from **03** diagnostic run)
- Live platform label wording (follow the form in front of you)

## Read first
- `workflows/stages/S8_tri_field_verdict.md`
- `Prompts/modules/verdict.md`
- `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` — three fields / branches
- `.cursor/rules/Review_Guidelines.mdc` — Submitter Verdicts (Valid as-is / Fixable / Not Fixable)
- `templates/platform_answers_fixable.txt` (field shape only)

## Do
1. Synthesize 01–03; re-open files only if handoffs conflict.
2. **Weigh mechanical evidence** (informs the choice; never makes it — you still choose):
   - Open static-check **FIXABLE** findings → direct Fixable evidence
   - judge-prep coverage gaps and overreach **candidates** → Fixable evidence on the instruction/tests axis
   - A packaging **hard-cap** → Fixable (delete the artifact; if tracked, remove it and realign
     `base_commit_sha` — that is git hygiene, which is fixable)
   - **None of these alone makes a task Not Fixable.** Not Fixable has exactly two causes:
     (a) the only way to make the task valid is to **reduce or replace PR scope**, or
     (b) an environment issue on the **Not-Fixable** list.
     Bias to **Fixable** when correction stays inside allowed files.
3. Choose **Public Main Analysis**, **Internal Validity** (+ reason), **Duplicate Analysis** using **live** labels.
4. Ensure **all three agree** on the same semantic branch (Public ≡ Internal ≡ Duplicate). Do **not** set Internal=`Invalid` with Public/Duplicate=`Fixable`.
5. Map Not Fixable → live **Invalid/Not Fixable** on Public/Duplicate and **Invalid** on Internal (or exact live wording).
6. Write Internal reason as a normal human paragraph that matches the agreed label (if Internal is `Fixable`, do not call the task “internally invalid”).
7. Record (script records only — you choose values; `set-verdicts` enforces `all_validity_fields_agree`):

```bash
python3 automation/sentinel_submitter.py set-verdicts --task-name TASK \
  --public-analysis "..." \
  --internal-validity "..." \
  --duplicate-analysis "..." \
  --reason "..."
```

8. State **05** branch contract:
   - **Fixable** → prioritized fix list (instruction / tests / oracle / env / metadata)
   - **Valid as-is** → confirmation plan (oracle 1.0 + NOP 0.0 required in **05**)
   - **Invalid/Not Fixable** → blocker summary (evidence only in **06**)
9. Packaging expectation for **06** (do not package now):
   - Fixable → `work/task ready_to_submit/<task>__corrected.zip`
   - Valid-as-is → no corrected ZIP
   - Invalid → `task_outputs/<task>/invalid_evidence/` only
10. Write `04__handoff.md` with exact three fields + branch + fix/blocker list.

## Do not
- Let automation choose the three fields
- Edit `working_copy/` in this step
- Mix reviewer outcomes (Accept / Needs Revision / Reject) into submitter fields
- Guess when evidence is incomplete — return to **02** or **03**
- Treat judge-prep `prep_passed=false` alone as Not Fixable

## Expected outputs
- Verdicts in session / workflow_state
- Chat statement of three fields + Internal reason
- `04__handoff.md` (branch contract)

## Done when
- All three fields set; Internal reason non-empty
- Public ≡ Internal ≡ Duplicate (same semantic branch)
- `set-verdicts` succeeded
- No content mutations; no ZIP

## Failure
| Symptom | Action |
|---------|--------|
| Any of Public / Internal / Duplicate disagree | `blocked`; reconcile before **05** |
| Thin evidence | `partial`; reopen weak prior step |

## Next
`checkpoint_ready.py --task-name TASK --next 05` → open **05**.
