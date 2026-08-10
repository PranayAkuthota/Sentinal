# Revision case library

Self-maintaining playbooks mined from this repo’s platform feedback
(`knowledge/judge_feedback/`), failure catalogue, and revision handoffs.
Not from memory or anecdote.

## Honesty (read this)

As of 2026-08-10 inventory + ledger round-chain backfill + Fix-section grading:

- **73** Part A instances; **22** chained pairs → `OUTCOMES.md`
- Citation outcomes: **resolved=104**, **not_resolved=13**, **regressed=5**
- Every Fix option should be tagged **EVIDENCED WORKING** / **EVIDENCED FAILING** / **UNTESTED**

### Cases whose guidance includes EVIDENCED FAILING options

These teach a move that **did not work** (or is the defect). Prefer the rewritten defaults:

| Case | Failing guidance | Data |
|------|------------------|------|
| **05** | Default “state arbitrary values in the instruction” | **3 regressed** on `0cf2e9a3` → Q9/Q10 |
| **05** | catalog_sql_* “state API names / soften locations” as known cure | **3 not_resolved** on `f2478b33` last pair |
| **03** | Trim/harden as if it clears FAIL EASY | FAIL EASY **recurred** on `004e50af` |
| **06** | Leaving / introducing suite-leak “helper” phrasing | **2 regressed** on `c6889dd0` |
| **10** | Leaving medium≠hard / irregular baselines | **not_resolved** on `1e6ecbbd` |

### EVIDENCED WORKING (trust more)

| Case | What cleared next round |
|------|-------------------------|
| **13** | Fail-open scans (×5 family, `0cf2e9a3`) |
| **08** | solve.sh reverse-apply (×3 tasks) |
| **04** | `allow_extra_failures=true` (`c6889dd0`); unrelated suites (`965e30ce`) |
| **01** | `.gradle`/`build/reports` junk (`004e50af`) |

### Handoff-reconstructed fixes (next-round still unknown)

JF014, JF015, JF052, JF053, JF059 — applied on tip; no following response yet.

## Layout

| Path | What | Entry point |
|------|------|-------------|
| `cases/` | Task defects | **From** platform / reviewer feedback via `ROUTER.md` |
| `pitfalls/` | Our process failures | **Before/after** working a task — never routed from feedback |
| `ROUTER.md` | Stage → case | First file when a response arrives |

## Status labels (top of every file)

| Label | Meaning |
|-------|---------|
| **CONFIRMED** | ≥2 independent instances in our history |
| **CONFIRMED-BY-RULE** | Named auto-fail / auto-REMOVE in official Ultra docs (any n) |
| **PROVISIONAL** | n=1 in our history only; no official auto-fail backing |
| **PROVISIONAL-THIN** | n=2 but thin/shared wording only |

## Contradiction pair

**Case 05** (faithfulness — state the contract) ⚠ **Case 06** (Q9/Q10 — get leaks out).
Doing both blindly caused the only known next-round failure (JF004). Both files cross-warn.

## Maintenance

After capturing platform feedback:

1. `ROUTER.md` → open case(s) **before** edits (pitfalls only in setup).
2. Match → append dated **Instances** row; if fix differed, update guidance **or** run
   `python3 automation/revision_library_maintain.py contradict …` (never silent overwrite).
3. No match → new **PROVISIONAL** case from the template.
4. At packaging: `python3 automation/record_revision_fixes.py --task-name TASK --fix '…||cite=…'`
   (one `--fix` per citation).
5. Next capture chains tip→history and fills `next_round_result`.
6. Coverage: `python3 automation/revision_library_coverage.py` (fails on orphans).
7. Second independent instance on a provisional case:
   `python3 automation/revision_library_maintain.py promote --case NN --instance-a … --instance-b …`

Round-chain backfill / outcomes: `OUTCOMES.md`, `automation/backfill_judge_round_outcomes.py`.
