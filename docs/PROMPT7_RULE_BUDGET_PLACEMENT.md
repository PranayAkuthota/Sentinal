# Prompt 7 — Review_Guidelines rule-budget placement table

**Date:** 2026-08-06  
**Source:** `.cursor/rules/Review_Guidelines.mdc` (465 lines, `alwaysApply: true`)  
**Target:** one always-on rule ≤120 lines; remainder in skill `reference/` or `alwaysApply: false` rules.  
**Discipline:** place every statement before delete; zero UNPLACED.

Legend:
- **KEEP** → slim `.cursor/rules/Review_Guidelines.mdc` (always-on)
- **MOVE** → destination must receive full prose before source delete
- **ALREADY** → destination already carries equivalent prose; delete from always-on after confirm
- **DROP** → only pure HTML audit markers / duplicate restore stubs after MOVE

| # | Statement (abbrev) | Src line(s) | Destination |
|---|-------------------|-------------|-------------|
| 1 | Frontmatter `alwaysApply: true` | 1–3 | KEEP |
| 2 | Title Project Sentinel Contributor Guidelines | 4 | KEEP (retitled Always-On Policy) |
| 3 | Last updated / Ultra merge banner | 6 | KEEP (one-line dated note) |
| 4 | Authoritative combined policy intro | 8 | MOVE → `Sentinel_Ultra_Policy_Detail.mdc` § Authority |
| 5 | File roles bullets (official, this file, workflows, CLAUDE, docs) | 10–18 | MOVE → Policy_Detail § File roles |
| 6 | Official Ultra / live platform / skill reference outrank templates | 20 | KEEP (one line) + MOVE full → Policy_Detail § Authority |
| 7 | Supporting files defer to this file; only alwaysApply true | 22 | KEEP (one line) |
| 8 | Branch-aware cross-ref (Duplicate, ZIP, working_copy, network blocks, golden.patch, f2p, Public/Duplicate, preflight) | 24–34 | MOVE → Policy_Detail § Branch-aware + ALREADY workflow `.mdc` |
| 9 | Source Precedence heading + numbered stack 1–7 | 38–48 | MOVE → Policy_Detail § Precedence |
| 10 | Clarifications (user may select role; live form; never mix versions; current default; legacy inputs) | 50–60 | MOVE → Policy_Detail § Precedence clarifications |
| 11 | Project purpose (Harbor tasks from PRs; correctness > superficial difficulty) | 64–68 | MOVE → Policy_Detail § Purpose |
| 12 | Every task solvable/clear/leakage-free/verifiable/authentic | 70 | KEEP (folded into four principles one-liners) |
| 13 | Workflow Authoring→Delivery 1–5 | 72–78 | MOVE → Policy_Detail § Workflow stages |
| 14 | Harbor Framework tab / unfamiliar Harbor | 80 | ALREADY `reference/harbor-format.md` + `glossary.md` |
| 15 | Do not combine submitter and reviewer verdict systems | 86 | KEEP (Never list) |
| 16 | Submitter duties bullets | 88–99 | MOVE → Policy_Detail § Roles · Submitter; ALREADY Platform_Workflow |
| 17 | Reviewer duties (Accept/Needs Revision/Reject; SQS; optional Harbor) | 101–111 | MOVE → Policy_Detail § Roles · Reviewer; ALREADY Reviewer_Step_by_Step |
| 18 | Adjudicator duties | 113–119 | MOVE → Policy_Detail § Roles · Adjudicator; ALREADY glossary |
| 19 | Current Harbor Structure pointer + required paths | 123–131 | ALREADY `reference/harbor-format.md`; KEEP one pointer |
| 20 | Legacy compatibility short (init_state / solution.patch / tests/files) | 133–136 | MOVE → `reference/harbor-format.md` § Legacy artifacts (new) |
| 21 | Submitter Verdicts intro | 138–140 | KEEP (three one-liners) |
| 22 | Valid as-is criteria bullets | 142–154 | ALREADY `reference/verdict-rubric.md` § Valid as-is; KEEP one-liner only |
| 23 | Fixable intro + examples | 156–172 | ALREADY `reference/verdict-rubric.md` Fixable list; KEEP one-liner |
| 24 | Not Fixable criteria | 174–183 | ALREADY `reference/verdict-rubric.md`; KEEP one-liner |
| 25 | Legacy mapping note (old Valid/Invalid → current) | 185–189 | MOVE → `reference/verdict-rubric.md` § Legacy mapping (new if missing) |
| 26 | Reviewer Outcomes table + SQS + rebuttal | 193–205 | MOVE → Policy_Detail § Reviewer outcomes; ALREADY Reviewer_Step_by_Step |
| 27 | Source PR Scope and Difficulty bullets | 209–220 | MOVE → `reference/core-principles.md` § Scope (or Policy_Detail § Scope); KEEP never reduce/replace |
| 28 | Difficulty Handling After Corrections 1–6 | 222–233 | MOVE → Policy_Detail § Difficulty after corrections; ALREADY FAQ difficulty |
| 29 | Allowed changes list | 237–250 | MOVE → `reference/fix-playbooks.md` § Allowed edits (new) if missing; else Policy_Detail |
| 30 | Prohibited changes list | 252–260 | KEEP never-edit-repo + never-reduce-scope; MOVE rest → fix-playbooks / Policy_Detail |
| 31 | Instruction Requirements bullets | 264–271 | ALREADY `reference/core-principles.md` Clarity/Leakage; MOVE any gap → Policy_Detail |
| 32 | Test Requirements pointer + operational summary | 275–280 | ALREADY `reference/test-quality.md`; KEEP ≥3.5 / blocking axes |
| 33 | Oracle and Solution Requirements | 282–285 | ALREADY `reference/fix-playbooks.md` oracle |
| 34 | Environment Review pointer | 287–290 | ALREADY `reference/environment-and-git.md` |
| 35 | Task Metadata Limits prose + Harbor network | 292–298 | KEEP full **metadata table** (expanded); ALREADY harbor-format for narrative |
| 36 | Git Repository Hygiene | 300–303 | ALREADY `reference/environment-and-git.md` + `git_hygiene.sh` |
| 37 | Local Validation by Role + never invent rewards | 305–308 | KEEP never invent rewards; MOVE role table → Policy_Detail; ALREADY definition-of-fixed |
| 38 | Upload and Packaging | 310–314 | ALREADY `reference/checklists.md` § zip |
| 39 | Platform Evaluations order + Difficulty threshold | 316–320 | KEEP ≥3.5 bar; MOVE detail → Policy_Detail § Platform evals; ALREADY P-010/P-011 |
| 40 | Agent-Run Analysis | 322–324 | MOVE → Policy_Detail § Agent-run analysis; ALREADY checklists |
| 41 | Supplemental License options list | 326–345 | MOVE → `reference/harbor-format.md` § License options (new) |
| 42 | Category values table | 347–360 | MOVE → `reference/harbor-format.md` § Category values (new) |
| 43 | Legacy Compatibility Appendix short | 364–367 | MOVE → `reference/harbor-format.md` § Legacy + verdict-rubric legacy |
| 44 | Final Checklist items | 369–387 | ALREADY `reference/checklists.md` Before You Upload; MOVE any unique bullets → checklists |
| 45 | Restored policy footer intro | 389–392 | DROP after statements 46–58 placed |
| 46 | File-role restore bullets (this file / workflows / CLAUDE) | 394–407 | Covered by #5 MOVE |
| 47 | Official Ultra outrank templates (restore) | 409–410 | Covered by #6 |
| 48 | Precedence restore lines 3–6 | 412–422 | Covered by #9 |
| 49 | Default current layout (restore stub) | 424–425 | Covered by #19 ALREADY harbor-format |
| 50 | Legacy Artifact Compatibility full table | 427–439 | MOVE → `reference/harbor-format.md` § Legacy artifacts |
| 51 | How reverse init_state preserved (dup) | 444–445 | MOVE → harbor-format § Legacy (once) |
| 52 | Role distinction replaces never-run-local | 447–448 | MOVE → Policy_Detail § Local validation by role |
| 53 | Older Valid/Invalid only when live form presents | 450–451 | MOVE → verdict-rubric § Legacy mapping |
| 54 | Only-four-metadata-fields rule is NOT current policy | 453–454 | MOVE → harbor-format § Metadata (explicit denial) |
| 55 | H. Older General Observations heading | 456–460 | MOVE → Policy_Detail § Write-up standards |
| 56 | Do not invent numbered Invalid-issue details (reviewer automation) | 462–463 | MOVE → Policy_Detail § Write-up standards |
| 57 | deletion-audit HTML markers | 389, 465 | DROP after audit complete |

## New alwaysApply:false rules

| File | Description (sharp) | Receives |
|------|---------------------|----------|
| `.cursor/rules/Sentinel_Ultra_Policy_Detail.mdc` | Load for full Sentinel Ultra policy beyond the always-on budget: precedence, roles, scope/difficulty, allowed edits, platform evals, license/category pointers, legacy write-up standards | Rows marked MOVE → Policy_Detail |
| `.cursor/rules/Sentinel_Automation_Invariants.mdc` | Apply when editing `automation/**/*.py`: scripts never assign Public/Internal/Duplicate; never invent oracle/NOP rewards; absolute paths; require `--task-name` when multiple sessions | Framework invariants (new; not from Review_Guidelines body) |

## KEEP always-on content (must fit ≤120 lines)

1. Three submitter verdicts — one line each  
2. Four core principles — one line each  
3. Blocking Judge axes (`test_coverage`, `test_faithfulness`) + internal ≥3.5 bar  
4. Metadata limits table (cpus, memory, storage, gpus, timeouts, Harbor network blocks)  
5. Never list (tracked repo sources; reduce/replace PR scope; invent rewards; mix verdict systems)  
6. Pointers to Policy_Detail, role `.mdc`s, skill `reference/`, CLAUDE.md, Automation_Invariants  

## Gate before delete

- [x] Every row above has KEEP / MOVE / ALREADY / DROP  
- [x] UNPLACED count = 0  
- [x] MOVE destinations written (`Sentinel_Ultra_Policy_Detail.mdc`, `harbor-format.md`, `verdict-rubric.md`)  
- [x] Slim file `wc -l` ≤ 120 (including frontmatter)  
- [x] Automation glob rule present (`Sentinel_Automation_Invariants.mdc`)  

**Completed:** 2026-08-06 — always-on rewritten; old body deleted only after destinations existed.
