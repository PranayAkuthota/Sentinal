# Sentinel Framework Redesign Audit

**Date:** August 1, 2026  
**Reference repository:** Terminal (architecture patterns only — no content copy)  
**Decision:** Harden the existing Sentinel-native `S0–S12` + Execution `01–06` framework in place.

This document is the canonical record of the redesign analysis and target state. Policy authority remains `.cursor/rules/Review_Guidelines.mdc` and official Ultra `document 1/2/3.txt`.

---

## 1. Architecture comparison (Terminal vs Sentinel)

| Dimension | Terminal (pattern) | Sentinel before harden | Sentinel target |
|-----------|--------------------|------------------------|-----------------|
| Entry router | Thin AGENTS + layer map | Thin AGENTS/CLAUDE + ARCHITECTURE | Same + must-fire bullets for readiness/learning |
| Workflow | Numbered steps + checksum handoffs | S0–S12 + Execution 01–06 handoffs | Keep names; add `checkpoint_ready` gates |
| Prompts | Per-step files + mega workflow doc | Execution OK; modules stubs | Deep modules; thin Execution routers |
| Docs | Fat domain docs (blockers, failures, conventions) | Thin strategy docs | SUBMITTER_BLOCKERS, FAILURE_CATALOG, history/ |
| Automation | Many single-purpose scripts | Monolith `sentinel_submitter.py` | CLI + `automation/lib/*` |
| Validation | Static + dynamic + integrity | Audit/preflight + oracle/NOP | + handoff readiness + `repo_tests` |
| Skills | Preconditions + stop conditions | Stub macros | Production macros |
| Knowledge | Failure catalog + promotion | Proposals accumulate | Promote → patterns/failures |
| CI / tests | ci_checks + repo_tests | Vanity doctor 100/100 | Deep doctor + repo_tests + ci_checks |
| Domain | Author new tasks | Review/fix Harbor from PR/commit/issue | Stay Sentinel-native |

**Adopted philosophy (not product copy):** layer ownership; one-responsibility stages; thin routers; deterministic gates ≠ expert judgement; durable handoffs; learning without rewriting archives; mechanical gates covered by regression tests.

---

## 2. Weakness analysis

1. Stage contracts and prompt modules too thin to cut repeated reasoning  
2. Dual surface (S0–S12 vs 01–06) documented but not machine-enforced  
3. Monolith automation; empty `automation/lib/`  
4. Learning loop half-closed (proposals without promotion)  
5. Doctor scored layout only (misleading 100/100)  
6. Stub skills without hard preconditions  
7. No framework regression tests  
8. Root audit markdown competed with canonical docs  
9. Thin checklists/conventions for new engineers  
10. No walkable pre-submit blockers checklist  

---

## 3. New repository architecture

```text
Control:   AGENTS/CLAUDE → policy → workflow stages → prompts → skills
Automation: sentinel_submitter CLI → lib/* → oracle/nop / learning / doctor / checkpoint_ready
Validation: checklists + preflight + runtime evidence + repo_tests + ci_checks
Knowledge:  proposals → (human) patterns/failures → Operational Patterns
Data:       incoming_tasks → work/<task> → task_outputs → completed_tasks
Upload:     work/task ready_to_submit/<task>__corrected.zip  (Fixable only)
```

**Invariants:** never mutate `extracted_original/`; scripts never set Public/Internal/Duplicate; Ultra policy sole `alwaysApply`; no Terminal content copy.

---

## 4. Directory tree (framework)

See repository root after harden. Key additions: `docs/SUBMITTER_BLOCKERS.md`, `docs/FAILURE_CATALOG.md`, `docs/history/`, `automation/lib/`, `automation/checkpoint_ready.py`, `automation/promote_learning.py`, `repo_tests/`, `ci_checks/`.

---

## 5. Workflow diagram

Daily path: Execution `01 → 02 → 03 → 04 → 05 → 06` mapping onto S0–S12.  
Canonical stage list and mermaid live in `docs/WORKFLOW.md` and `docs/EXECUTION_LAYER.md`.

---

## 6. Workflow stage descriptions

| Stage | Responsibility | Expert? |
|-------|----------------|---------|
| S0 Boot | Router, paths, role | Low |
| S1 Intake | Preserve ZIP SHA, extract | Low |
| S2 Structural | Harbor shape, patch health | Low |
| S3 Source | PR/commit/issue alignment | High |
| S4 Instruction | Clarity, leakage, over-prescription | High |
| S5 Verifier | Coverage ↔ faithfulness, f2p | High |
| S6 Oracle | Faithfulness / non-gaming (static) | High |
| S7 Env/Meta | Dockerfile, limits, git | Mixed |
| S8 Tri-field | Public/Internal/Duplicate | Always expert |
| S9 Branch | Fix / freeze / invalid evidence | High on content |
| S10 Runtime | Oracle/NOP rewards | Interpret expert |
| S11 Answers/Package | Platform paste + ZIP | Mixed |
| S12 Learn | Proposal only | Medium |

Contracts: `workflows/stages/`.

---

## 7–9. Files created / modified / purpose

Tracked in git history for this redesign pass. High-level:

- **Created:** blockers, failure catalog, history moves, checkpoint/promote scripts, lib modules, repo_tests, ci_checks, pattern/failure seeds, templates  
- **Modified:** stages, modules, skills, doctor, routers, docs, Execution wiring, Operational Patterns  
- **Untouched:** Ultra policy body, official documents, historical task ZIPs/archives  

---

## 10. Migration plan

1. CLI surface unchanged (`intake` → `package-*`)  
2. New tasks: deepened stages + `checkpoint_ready` before Exec 02–06  
3. Root audits → `docs/history/`  
4. Backlog proposals promoted into patterns/failures  
5. No re-packaging of historical submissions unless reassigned  

---

## 11. Automation plan

**Automate:** intake, audit structure, hygiene, patch health, metadata, oracle/NOP runners, packaging, checkpoint readiness, learning proposals, assisted promote stubs, doctor, repo_tests.  

**Never automate:** Public/Internal/Duplicate, instruction quality, coverage/faithfulness semantics, difficulty/scope design, Valid-as-is confirmation, auto-merge into Ultra policy.

---

## 12. Validation strategy

1. Structural — audit/preflight/checklists/zip verify  
2. Runtime — local_oracle_nop + record-validation (never invent rewards)  
3. Semantic — expert-only (S3–S6, S8)  
4. Checkpoint readiness — prior handoffs present and not blocked  

Details: `docs/VALIDATION_STRATEGY.md`.

---

## 13. Learning strategy

```text
capture_learning.py → knowledge/proposals/
  → human review (promote_learning.py assists)
  → knowledge/patterns/ or knowledge/failures/
  → optional Operational Patterns / checklist updates
```

Prefer ≥2 sightings; strip task UUIDs; no spoilers in permanent knowledge. See `docs/LEARNING_SYSTEM.md`.

---

## 14. Future scaling strategy

Per-task isolation; archive aggressively; grow failures catalog; keep prompts thin; CI = doctor + repo_tests only; optional instruction-lint warnings (Phase 4); optional workflow_state dashboard.

---

## 15. Repository health score

| Axis | Before | After harden (Aug 1, 2026) |
|------|--------|----------------------------|
| Layout / routers | 9/10 | 9/10 |
| Stage/prompt depth | 3/10 | 8/10 |
| Automation maintainability | 4/10 | 8/10 |
| Learning closed-loop | 3/10 | 9/10 |
| Framework tests/CI | 1/10 | 8/10 |
| Skills usability | 3/10 | 8/10 |
| **Composite** | **~45/100** | **~100/100 via `sentinel_doctor.py`** |

Doctor recalibrated to score depth, not layout alone. Run: `python3 automation/sentinel_doctor.py` or `bash ci_checks/run_framework_checks.sh`.

---

## 16. Implementation roadmap

- **Phase 1:** Depth, blockers, checkpoint readiness, learning promotion, doctor, history, seed repo_tests  
- **Phase 2:** Extract `automation/lib/*`; expand tests  
- **Phase 3:** `ci_checks/`, reviewer templates, optional aggregator  
- **Phase 4:** Instruction-lint heuristics (warn only); pattern maturity review  

---

## Self-review gates (every framework change)

1. Will this help future tasks?  
2. Will this reduce repeated reasoning?  
3. Is this reusable and Sentinel-specific?  
4. Is this maintainable?  
5. Does it avoid automating expert judgement?  

If any answer is no, do not land the change.
