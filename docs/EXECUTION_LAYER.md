# Interactive Execution Layer

**Purpose:** Pauseable, checkpoint-based daily workflow on top of the stable **S0–S12** architecture.

This layer does **not** change Sentinel logic, stages, rules, or skills. It only sequences work so you can run one focused Cursor conversation per checkpoint, inspect results, then continue.

**6 steps per task** (merged from the former 12 half-steps 01A…06B).

---

## Relation to S0–S12

| Execution step | Former IDs | Sentinel stages |
|----------------|------------|-----------------|
| **01** Boot & Structural Audit | 01A + 01B | S0, S1, S2 |
| **02** Source & Instruction | 02A + 02B | S3, S4 |
| **03** Spec Alignment | 03A + 03B + 04A | S5, S6, S7 |
| **04** Tri-Field Verdict | 04B | S8 |
| **05** Branch Fix & Validate | 05A + 05B | S9, S10 |
| **06** Answers, Package & Learn | 06A + 06B | S11, S12 |

Stage contracts remain authoritative: `workflows/stages/`.  
Workflow overview: `docs/WORKFLOW.md`.

---

## When to use which prompt

| Situation | Start at |
|-----------|----------|
| Brand-new ZIP + metadata | **01** |
| Intake+audit done; need PR/instruction | **02** |
| Analysis done through 03; need verdict | **04** |
| Verdict set; need Fixable edits + oracle/NOP | **05** (only after **04**) |
| Ready to fill platform form / ZIP / learn | **06** |
| Platform revision (Difficulty/Judge/Logs) | Prefer revision notes inside **02**–**05**; start **01** if new workspace or **02** if ZIP already preserved |

**Fixable upload ZIP destination (every time):** `work/task ready_to_submit/<task>__corrected.zip`  
Created/refreshed only in step **06** via `package-fixable`. See `Prompts/Execution/README.md`.

**Snorkel answer voice:** steps **01–06** draft and finalize narrative platform fields as human paragraphs (not LLM/audit tone). Canonical: `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` §13.

Reviewer mode: **do not** use this Execution layer for packaging. Use reviewer skill/rules instead.

---

## Execution order

Strict forward order for a full first pass:

```text
01 → 02 → 03 → 04 → 05 → 06
```

**Hard gate:** Do not run **05** (mutations + runtime) until **04** (verdicts) is complete and Public matches Duplicate.

Skip rules:

- Duplicate = Valid-as-is → after **04**, skip Fixable edits in **05** (confirm freeze only), still run oracle/NOP as required for Valid-as-is, then **06** (no corrected ZIP + learning; do not write ready_to_submit).
- Duplicate = Invalid/Not Fixable → **05** prepares evidence only (no “valid corrected” ZIP) + diagnostics as needed; **06** packages evidence under `invalid_evidence/` + learning.
- Duplicate = Fixable → **06** always places/refreshes the upload ZIP at `work/task ready_to_submit/<task>__corrected.zip`.

---

## Handoffs

After each step, write/update:

`work/<task>/session/execution/NN__handoff.md`  
(e.g. `01__handoff.md` … `06__handoff.md`)

Use `templates/execution_handoff.md`.

Minimum handoff fields:

- task_name  
- checkpoint_id (e.g. `03`)  
- status: complete | blocked | partial  
- key findings (bullets)  
- artifacts paths produced  
- open questions  
- next_checkpoint  

Next prompt must **read the previous handoff first** and not re-do completed analysis unless the handoff marks it stale.

### Machine readiness gate

Before starting checkpoint **NN** (for NN ≥ 02):

```bash
python3 automation/checkpoint_ready.py --task-name TASK --next NN
```

Requires prior handoffs to exist with `status: complete` (not `blocked`/`partial`). For **05** and **06**, also requires Public == Duplicate recorded. Do not skip ahead when this fails.

Legacy note: older sessions may still have `01A__handoff.md` … `06B__handoff.md`. Prefer the new `NN__handoff.md` names going forward; when resuming a mid-flight old session, map via the merge table above.

---

## Restart points

| If you stop after… | Resume with… |
|--------------------|--------------|
| 01 | 02 |
| 02 | 03 |
| 03 | 04 |
| 04 | 05 (or skip path per verdict) |
| 05 | 06 |

If `working_copy` was illegally edited before **04**: restore from `extracted_original` before continuing.

---

## Failure recovery

1. Mark handoff `status: blocked` with reason.  
2. Follow the step’s **Failure Handling** section.  
3. Do not invent validation rewards or verdicts.  
4. Re-run only the failed step (and any it invalidates).  
5. **05** content edits invalidate prior runtime/package claims — re-validate before **06**.

---

## Design goals (met by this layer)

- Smaller prompts (routers, not policy dumps)  
- Lower context (one checkpoint per chat when desired)  
- Pause/inspect between checkpoints  
- Preserve prior work via handoffs  
- Manage long reviews without mega-prompts  
- **≤6 calls per task** for daily use  

---

## Files

- Index: `Prompts/Execution/README.md`  
- Checkpoints: `Prompts/Execution/0{1..6}_*.md`  
- Handoff template: `templates/execution_handoff.md`  
- Commands: `docs/COMMANDS.md`  
- Policy: `.cursor/rules/Review_Guidelines.mdc` (unchanged)
