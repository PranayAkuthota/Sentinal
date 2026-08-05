# Sentinel Submitter Framework — Architecture

**Last updated:** August 1, 2026  
**Audience:** engineers and agents extending this repo  
**Not policy:** Ultra validity rules live in `.cursor/rules/Review_Guidelines.mdc` and official `document 1/2/3.txt`.  
**Redesign record:** `docs/FRAMEWORK_REDESIGN_AUDIT.md`.

This file maps **which layer owns what**. For stage procedures see `docs/WORKFLOW.md`. For commands see `docs/COMMANDS.md`. For conventions see `docs/REPO_CONVENTIONS.md`.

---

## Design philosophy (Sentinel-native)

Borrowed as *engineering patterns* only (not product copy) from mature AI task harnesses:

1. **One always-on router** (`AGENTS.md` / `CLAUDE.md`) — short; links out.
2. **Layer ownership** — policy ≠ workflow ≠ prompts ≠ automation ≠ knowledge.
3. **Stage handoffs** — each stage has purpose, inputs, outputs, validation, failure, recovery.
4. **Deterministic gates vs expert judgement** — scripts never choose Public/Internal/Duplicate.
5. **Learning loop** — after each task, capture reusable patterns; never rewrite archives.

---

## Layer map

| Layer | Owns | Must not own |
|-------|------|----------------|
| Policy | Official Ultra docs + `.cursor/skills/sentinel-ultra-review/reference/` + `.cursor/rules/Review_Guidelines.mdc` | Commands, prompts, packaging scripts |
| Workflow | `docs/WORKFLOW.md`, `workflows/stages/*` | Verdict decisions |
| Prompts | `Prompts/` modules + thin orchestrators | Full Ultra policy text |
| Automation | `automation/*` + skill `scripts/check_task.py` via `static-check` | Semantic verdicts |
| Validation | `validation/checklists/*`, structural scripts, `checkpoint_ready`, `repo_tests` | “Valid as-is” confirmations |
| Knowledge | `knowledge/patterns`, `knowledge/failures`, `knowledge/proposals` | Task-specific secrets, PR spoilers for agents |
| Blockers | `docs/SUBMITTER_BLOCKERS.md` | Ultra policy restatement |
| Workspaces | `incoming_tasks/`, `work/`, `task_outputs/`, `completed_tasks/` | Framework rules |
| Skills | `.cursor/skills/sentinel-*` (incl. `sentinel-ultra-review`) | Inventing policy outside `reference/` |

Policy detail for Harbor format, test quality, git, and verdicts lives primarily under  
`.cursor/skills/sentinel-ultra-review/reference/`. Role `.mdc` files point there.

---

## Runtime data plane

```text
incoming_tasks/*.zip
        │ intake (preserve SHA)
        ▼
work/<task>/
  original/                 # immutable ZIP
  extracted_original/       # never mutate
  working_copy/             # Fixable edits only
  session/                  # platform_input, session.json, validation_logs
  analysis/                 # structural reports
        │ package / evidence
        ▼
task_outputs/<task>/
  platform_answers.txt
  reports, corrected ZIP or invalid evidence
        │ archive
        ▼
completed_tasks/
```

---

## Control plane

```text
AGENTS.md ──► CLAUDE.md ──► role mode (submitter | reviewer | framework)
                 │
                 ├─► docs/WORKFLOW.md (stages S0–S12 — stable)
                 ├─► Prompts/Execution/01…06 (daily interactive; maps onto S0–S12)
                 ├─► Prompts/* orchestrators + Prompts/modules/* (stage modules)
                 ├─► automation/sentinel_submitter.py (+ lib/) (gates + static-check)
                 ├─► .cursor/skills/sentinel-ultra-review/scripts/check_task.py
                 ├─► automation/checkpoint_ready.py (Execution handoffs)
                 ├─► automation/local_oracle_nop.py (runtime evidence)
                 ├─► automation/capture_learning.py / promote_learning.py
                 └─► knowledge/* (post-task learning)
```

---

## Invariants

- Never mutate `extracted_original/` or overwrite `original/*.zip`.
- Never put reports/session logs inside the upload ZIP.
- Never invent oracle/NOP rewards or handling times.
- Public Main Analysis must match Duplicate Analysis.
- Automation never assigns the three live verdict fields.
