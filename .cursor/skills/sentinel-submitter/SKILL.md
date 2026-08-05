---
name: sentinel-submitter
description: >-
  Run the Sentinel Ultra submitter workflow for a Harbor task ZIP (intake through
  packaging and learning capture). Use when the user acts as submitter or provides
  a task ZIP with platform metadata.
---

# Sentinel Submitter Skill

## Preconditions — stop if any fail

1. Workspace root is the Sentinel framework (has `automation/sentinel_submitter.py`).
2. User is in **submitter** mode (not reviewer packaging).
3. A task ZIP path or existing `work/<task>/` session is identified.
4. Multiple `work/*` sessions ⇒ `--task-name` will be used on every command.
5. Policy authority acknowledged: `Review_Guidelines.mdc` + official Ultra docs.

## Preferred daily path

Use `Prompts/Execution/` **01 → 06** (maps to S0–S12). Single-shot alternative: `Prompts/Submitter_First_Pass.md` or `Submitter_Platform_Revision.md`.

Before starting Execution **NN** (NN≥02):

```bash
python3 automation/checkpoint_ready.py --task-name TASK --next NN
```

## Hard rules

1. Never assign Public / Internal / Duplicate via scripts — expert only (`set-verdicts`).
2. Never mutate `extracted_original/` or overwrite `original/*.zip`.
3. Never invent oracle/NOP rewards or handling times.
4. Public must match Duplicate before Execution **05** mutations.
5. Snorkel narrative fields = human paragraphs (workflow §13).
6. End with platform answers + `capture_learning.py`.
7. Fixable Files Changed lists every edited file (path / what / why).
8. Platform revisions (P-010 / P-011): Agent Judge fails before Difficulty runs — fix Judge first until **every axis ≥ 3.5**; `discuss (overreach)` → sync instruction↔tests; do not invent Difficulty results when the platform says Difficulty was not run.

## Command spine

See `docs/COMMANDS.md`. Typical Fixable:

```text
intake → prepare → audit → (01–04 expert) → set-verdicts
  → working_copy edits → ensure-packaging-hygiene → sync-problem-statement
  → local_oracle_nop → record-validation → preflight → package-fixable
  → capture_learning
```

Upload ZIP: `work/task ready_to_submit/<TASK>__corrected.zip`.

## Stop conditions

- `checkpoint_ready` fails → fix prior handoff; do not skip ahead  
- Preflight not ready → do not package  
- Valid-as-is runtime missing → do not claim Valid-as-is complete  
