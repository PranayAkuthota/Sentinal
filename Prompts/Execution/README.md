# Daily Submitter Prompts — Canonical Path

**Use these six files for every new Sentinel submitter task.**  
They are the production daily path. Do not invent a parallel mega-prompt.

| Prefer | Avoid for daily work |
|--------|----------------------|
| `Prompts/Execution/01_boot_and_structural_audit.md` … `06_answers_package_and_learn.md` (one chat per step) | One giant custom prompt |
| Stage detail in `workflows/stages/` + `Prompts/modules/` | Re-deriving Ultra policy from chat memory |

Single-shot alternatives (only when you intentionally skip pauseable checkpoints):  
`Prompts/Submitter_First_Pass.md` / `Prompts/Submitter_Platform_Revision.md` — still follow S0–S12.

---

## How to run a task

```text
@Prompts/Execution/01_boot_and_structural_audit.md   + ZIP + metadata
  → inspect 01__handoff.md
@Prompts/Execution/02_source_and_instruction.md  (after checkpoint_ready --next 02)
@Prompts/Execution/03_spec_alignment.md
@Prompts/Execution/04_tri_field_verdict.md  ← verdicts; no edits before this
@Prompts/Execution/05_branch_fix_and_validate.md  ← edits + oracle/NOP
@Prompts/Execution/06_answers_package_and_learn.md  ← answers + ZIP + learning
```

Before **02–06**:

```bash
python3 automation/checkpoint_ready.py --task-name TASK --next NN
```

Stop if it fails. **05/06** also require Public == Duplicate.

Handoffs: `work/<task>/session/execution/NN__handoff.md`  
Template: `templates/execution_handoff.md`  
Must include `status: complete | blocked | partial`.

---

## Fixable upload ZIP (every package / revision)

```text
work/task ready_to_submit/<task-name>__corrected.zip
```

- Created/refreshed only in **06** via `package-fixable` (delete-first).
- Mirror: `task_outputs/<task>/updated_zip_file/`
- Valid-as-is: no corrected ZIP. Invalid: evidence under `invalid_evidence/` only.
- Before upload: walk `docs/SUBMITTER_BLOCKERS.md`.

---

## Hard rules (all six prompts)

1. Scripts never choose Public / Internal / Duplicate.  
2. Never mutate `extracted_original/` or overwrite `original/*.zip`.  
3. Never invent oracle/NOP rewards or handling times.  
4. No packaging before **06**; no Fixable edits before **04**.  
5. Snorkel narrative fields = human EC paragraphs (workflow §13).  
6. Live platform field labels win over stored templates.  
7. Reuse `knowledge/patterns/INDEX.md` — do not rediscover known traps.

---

## Stage map

| Step | File | Stages |
|------|------|--------|
| **01** | `Prompts/Execution/01_boot_and_structural_audit.md` | S0–S2 |
| **02** | `Prompts/Execution/02_source_and_instruction.md` | S3–S4 |
| **03** | `Prompts/Execution/03_spec_alignment.md` | S5–S7 |
| **04** | `Prompts/Execution/04_tri_field_verdict.md` | S8 |
| **05** | `Prompts/Execution/05_branch_fix_and_validate.md` | S9–S10 |
| **06** | `Prompts/Execution/06_answers_package_and_learn.md` | S11–S12 |

Full guide: `docs/EXECUTION_LAYER.md` · Commands: `docs/COMMANDS.md` · Policy: `.cursor/rules/Review_Guidelines.mdc`
