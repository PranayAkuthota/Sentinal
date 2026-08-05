# Sentinel Submitter — Platform Revision Orchestrator

**Use for:** improving a task after Difficulty / Agentic Judge / Logs feedback (original + prior corrected ZIP may exist).

**Do not use for:** brand-new ZIP first pass → `Submitter_First_Pass.md`.

## Load order

Same policy/workflow as first pass. Emphasize modules: `source_alignment`, `instruction_review`, `verifier_alignment`, `oracle_review`, `runtime_validation`, `package_answers`.

Reuse `knowledge/patterns/P-010_agent_judge_before_difficulty.md` and `P-011_agent_judge_overreach_…` when platform feedback is Judge-related.

## Platform eval order (Aug 4 2026)

1. **Agent Judge first.** If Judge fails, Difficulty is **not** run.
2. Marker: `Blocked at the agentic judge. Not run: difficulty screen (cheap single-arm rollout).`
3. Revise and re-upload until **all Agent Judge axes are ≥ 3.5** (blocking: test_coverage + test_faithfulness; never ship “3 with reservations”).
4. If verdict is `discuss (overreach)` → run P-011 playbook (Tests→Instruction map; remove/ungrade overreach **or** state observable public contract; no implementation spoilers).
5. Only then interpret Difficulty: **4 trials per model**; worse model must still be **≤50%** pass rate (threshold unchanged).

When Judge blocked Difficulty, do not wait for difficulty logs — they were not produced.

## Execute (delta-aware)

1. S0 Boot  
2. S1 Preserve originals (never overwrite)  
3. Diff original vs prior corrected (manual/expert)  
4. Classify feedback: Judge-only vs Judge+Difficulty vs Difficulty-only  
5. Re-run S3–S7 focusing on report citations (Judge citations first if both present)  
6. S8 Verdict (often remains Fixable)  
7. S9 Fixable edits in `working_copy/` only — keep or raise difficulty; no filler; no scope reduction  
8. S10–S12 validate, package, learn  

## Non-negotiables

- Do not reduce difficulty via vagueness  
- Blocking judge axes: test coverage & faithfulness — **axis scores ≥ 3.5** before Difficulty  
- Overreach: sync instruction ↔ tests ↔ oracle together (P-011); coverage-only chase is a trap  
- Target quality uplift without solution leakage  
- Checklist every cited report issue: fixed or explicitly out of scope  
- Final Snorkel narrative answers = human paragraphs (workflow §13); not LLM/audit tone  
- Do not claim Difficulty ran when the platform says it was not run  

