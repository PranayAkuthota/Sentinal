# Sentinel Framework Blueprint

**Date:** July 30, 2026  
**Reference:** Terminal repository used for **architecture patterns only** (no content copy).  
**Completed task artifacts:** not modified.

---

## 1. Architecture comparison (Terminal vs Sentinel)

| Dimension | Terminal (pattern) | Sentinel (before) | Sentinel (target / now) |
|-----------|--------------------|-------------------|-------------------------|
| Entry | Thin AGENTS + ARCHITECTURE map | AGENTS/CLAUDE + large rules | Same + `docs/ARCHITECTURE.md` ownership map |
| Workflow | Explicit numbered stages with handoffs | Branch-aware procedure in one large `.mdc` | **S0–S12** Sentinel-native stages |
| Prompts | Per-step prompt files | Few large prompts | Thin orchestrators + `Prompts/modules/` |
| Automation | Many single-purpose scripts + umbrella gates | One large gate script + helpers | Gate script + validate + hygiene + learning + doctor |
| Validation | Separated static/dynamic/approval | Mixed in procedure text | `docs/VALIDATION_STRATEGY.md` + checklists |
| Knowledge | Failures catalog + reference tasks | Mostly chat memory + audits | `knowledge/{patterns,failures,proposals}` |
| Skills | Opt-in Cursor skills | None (until now) | `sentinel-submitter/packager/reviewer` |
| Learning | Failure logging / meta review | Ad-hoc | S12 + `capture_learning.py` |
| Domain | Author **new** TB tasks | Review/fix Harbor tasks from PRs | Kept Sentinel-native (submitter/reviewer) |

**Engineering philosophy adopted (not copied):** layer ownership, stage contracts, thin routers, deterministic gates ≠ judgement, post-task learning without rewriting history.

---

## 2. Weakness analysis (Sentinel pre-redesign)

- Mega-rules / mega-prompts encourage skipped stages and duplicated reasoning  
- Weak separation of structural vs semantic validation  
- Multi-session / cwd / path friction  
- Patch-apply false greens; ungraded tests under `allow_extra_failures`  
- No formal learning inbox → knowledge dies in chat  
- Root cluttered with historical audit markdown  
- No doctor / health score for framework itself  
- Scaling to hundreds of tasks would amplify inconsistency  

---

## 3. New repository architecture

Control plane: policy → workflow → prompts → skills  
Data plane: incoming → work → task_outputs → completed  
Knowledge plane: proposals → patterns/failures  
Automation plane: gates, runtime validate, hygiene, learning, doctor  

---

## 4. Directory tree (framework)

```text
Sentinal/
  README.md
  AGENTS.md
  CLAUDE.md
  document 1|2|3.txt          # official Ultra (authoritative)
  .cursor/rules/              # policy + procedures + patterns
  .cursor/skills/sentinel-*/  # opt-in macros
  docs/                       # ARCHITECTURE, WORKFLOW, COMMANDS, …
  workflows/stages/S0–S12.md
  Prompts/                    # orchestrators + modules/
  templates/
  validation/checklists/
  knowledge/{patterns,failures,proposals}/
  automation/
  incoming_tasks/
  work/
  task_outputs/
  completed_tasks/
```

---

## 5. Workflow diagram

See `docs/WORKFLOW.md` (mermaid S0→S12).

---

## 6. Workflow stage descriptions

See `workflows/stages/*.md` (each: Purpose, Inputs, Outputs, Validation, Failure, Recovery, Automation).

---

## 7–9. Files created / modified / purpose

### Created (this redesign)

| File | Purpose |
|------|---------|
| `README.md` | New-engineer entry |
| `docs/ARCHITECTURE.md` | Layer ownership map |
| `docs/WORKFLOW.md` | S0–S12 + diagram |
| `docs/COMMANDS.md` | Canonical commands |
| `docs/REPO_CONVENTIONS.md` | Intentional conventions |
| `docs/VALIDATION_STRATEGY.md` | Structural vs semantic |
| `docs/LEARNING_SYSTEM.md` | Post-task learning rules |
| `docs/FRAMEWORK_BLUEPRINT.md` | This blueprint |
| `workflows/stages/S0–S12_*.md` | Stage contracts |
| `Prompts/modules/*.md` | Small stage prompts |
| `knowledge/**` | Learning plane |
| `validation/checklists/*.md` | Checklists |
| `.cursor/skills/sentinel-*/SKILL.md` | Role macros |
| `automation/capture_learning.py` | Proposal writer |
| `automation/sentinel_doctor.py` | Framework health |

### Modified

| File | Purpose of change |
|------|-------------------|
| `Prompts/Submitter_First_Pass.md` | Thin orchestrator → stages |
| `Prompts/Submitter_Platform_Revision.md` | Delta revision orchestrator |
| `Prompts/Command_Prompt.md` | Router |
| `AGENTS.md` / `CLAUDE.md` | Point at new architecture |
| `automation/README.md` | Document new scripts |

### Untouched by design

- `task_outputs/**` completed ZIPs  
- `work/**` task contents (except future sessions)  
- Ultra policy body in `Review_Guidelines.mdc` (still authoritative)  

---

## 10. Migration plan

1. Keep using existing `intake → package` commands (compatible).  
2. Prefer new stage docs/prompts for all **new** tasks.  
3. Run `capture_learning.py` at end of each task.  
4. Optionally move root `sentinel_*_audit.md` into `docs/history/` later (non-blocking).  
5. Do not re-package historical submissions unless a new assignment requires it.

---

## 11. Automation plan

| Automate | Do not automate |
|----------|-----------------|
| Intake, audit structure, hygiene, patch health, zip, oracle/NOP runners, learning proposals, doctor | Verdicts, instruction quality, coverage semantics, faithfulness, difficulty, Invalid scope calls |

---

## 12. Validation strategy

See `docs/VALIDATION_STRATEGY.md`.

---

## 13. Learning strategy

See `docs/LEARNING_SYSTEM.md`. Promote patterns after ≥2 sightings when possible.

---

## 14. Future scaling strategy

- Keep `work/` and `task_outputs/` per-task isolation  
- Archive aggressively to `completed_tasks/`  
- Grow `knowledge/failures` as the primary anti-regression memory  
- Add CI later: `sentinel_doctor.py` + import tests only (no task verdicts in CI)  
- Split `sentinel_submitter.py` into `automation/lib/` modules when file size hurts maintainability (Phase 3)

---

## 15. Repository health score

Run: `python3 automation/sentinel_doctor.py`  

Target after Phase 1 implementation: **≥90/100** (layout + imports).  
Semantic harness maturity increases with pattern promotions (Phases 2–4).

---

## 16. Implementation roadmap

### Phase 1 — Foundation (done in this change)

- Architecture docs, S0–S12, modular prompts, skills, learning inbox, doctor, checklists, README rewire

### Phase 2 — Hardening (done August 1, 2026 harden)

- Promoted recurring proposals into patterns/failures  
- Added `docs/history/` for old audit markdown  
- Tightened doctor checks (depth, skills, learning, tests)  
- `checkpoint_ready.py`, `promote_learning.py`, `SUBMITTER_BLOCKERS.md`

### Phase 3 — Modular automation + CI (done August 1, 2026 harden)

- Split helpers into `automation/lib/{verdicts,paths,package,hygiene,sync,toml_util,session}.py`  
- `repo_tests/` + `ci_checks/run_framework_checks.sh`  
- `aggregate_workflow_states.py` + `templates/reviewer_answer.txt`

### Phase 4 — Scale (by ~25 tasks)

- Optional instruction-lint **heuristics** (warnings only; never auto-rewrite)  
- Pattern library maturity review against live platform form drift  
- Further split remaining audit/preflight bodies from `sentinel_submitter.py` if file size hurts
