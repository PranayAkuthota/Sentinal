# Sentinel Submitter — Platform Revision Orchestrator

**Use for:** improving a task after Difficulty / Agentic Judge / Manual Reviewer / Logs feedback.

**Do not use for:** brand-new ZIP first pass → `Submitter_First_Pass.md`.

**Prefer the daily path:** `Prompts/Execution/07_platform_revision.md` (checkpoint + library).

## Load order

1. `knowledge/revision_library/ROUTER.md` (after capture — **before edits**)
2. Matching `cases/` file(s); `pitfalls/` only for process checks
3. Policy/workflow as first pass; patterns P-010, P-011, P-012, P-006

## Platform eval order (Aug 4 2026)

1. **Agent Judge first.** If Judge fails, Difficulty is **not** run.
2. Marker: `Blocked at the agentic judge. Not run: difficulty screen (cheap single-arm rollout).`
3. **Manual Reviewer** may still bounce after Judge OK / Difficulty PASS HARD — Cases 01–02.
4. Revise until **all Agent Judge axes are ≥ 3.5** (blocking: test_coverage + test_faithfulness).
5. `discuss (overreach)` → Case 05 / P-011 (one direction only; ⚠ Case 06).
6. Difficulty FAIL EASY after Judge OK → Case 03 (not a Judge coverage rewrite).
7. Only then interpret Difficulty trials (worse model ≤50%).

## Execute (delta-aware)

1. S0 Boot; preserve originals  
2. F-014: platform ZIP SHA vs mirror  
3. **Capture** `capture_judge_feedback.py` (chains prior tip → `next_round_result`)  
4. **Router → case(s)** — first action before fixing  
5. Classify stage; one-direction fix per citation  
6. S9 edits in `working_copy/` only  
7. S10–S10.5 validate; **06** package + `record_revision_fixes.py` per citation  
8. Append case Instances; `revision_library_coverage.py` must pass  

## Non-negotiables

- Library before edits; pitfalls never replace task cases  
- No silent Fix-section overwrite (`revision_library_maintain.py contradict`)  
- `fixes_applied` per citation at packaging; outcomes chained on next capture  
- Do not invent Difficulty/Oracle/rewards  
- Final Snorkel answers = human paragraphs (workflow §13)  
