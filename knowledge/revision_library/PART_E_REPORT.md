# Part E — Verification report

**Date:** 2026-08-10  
**Branch:** `framework/revision-case-library` → merge to `main`

## Coverage

`python3 automation/revision_library_coverage.py` → **73/73 OK** (0 orphans).

Every Part A id in `INSTANCE_INDEX.json` appears in `cases/` or `pitfalls/`.

## Distinctness

No two cases prescribe the same default fix for the same defect shape:

| Shape | Case | Default move |
|-------|------|--------------|
| Ungraded / allow_extra / unrelated suite | 04 | Scope grading + tests or trim claims |
| Undeclared / private / literal tokens | 05 | Soften assert (not dump into instruction) |
| Q9/Q10 / how-to / suite-leak | 06 | Remove leak; soften test if values needed |
| FAIL EASY after Judge OK | 03 | Trim then harden (honest: not clearing yet) |
| Editing-boundary | 02 | Restore/realign |
| Reviewer packaging | 01 | Harness/metadata/caches |
| solve.sh -R | 08 | Idempotent forward-only |
| Fail-open | 13 | Presence asserts |

## Recognisability (platform strings → case)

| Case | Routing quote |
|------|---------------|
| 03 | `Difficulty FAIL EASY…` / `Requires at least MEDIUM; opus 4/4` |
| 04 | `not graded` / `allow_extra_failures true` / `unrelated legacy tests` |
| 05 | `never documented` / `catalog_sql_prepare` / `private access` |
| 06 | `Static Q9/Q10 FAIL` / `suite calls that helper` |
| 08 | `solve.sh reverse applies golden.patch` |
| 13 | `else: pass` / fail-open scan |

## Honesty — EVIDENCED FAILING cases (named)

1. **Case 05** — “state arbitrary values in instruction” (3 regressed, 0cf2e9a3)  
2. **Case 05** — catalog_sql_* known-remedy implication (3 not_resolved, f2478b33)  
3. **Case 03** — trim/harden as if FAIL EASY clears (recurred, 004e50af)  
4. **Case 06** — suite-leak helper phrasing path (2 regressed, c6889dd0)  
5. **Case 10** — leaving medium≠hard / irregular baselines (not_resolved, 1e6ecbbd)

Single-instance / provisional cases: 15, 16 (thin), pitfalls 11/12/18.  
Claims without tip `fixes_applied`: most Fix options still **UNTESTED** except graded rows above.

## Router dry-run (3 historical responses)

| Task / response | Stage | Router → | Expected |
|-----------------|-------|----------|----------|
| `0cf2e9a3` tip DISCUSS + Q9/Q10 + faithfulness | Agentic Judge | 06 + 05 (⚠ pair); not pitfall 12 as edit target | OK |
| `004e50af` tip OK + `Difficulty FAIL EASY: Opus 75%…` | Difficulty after Judge OK | **03** only | OK |
| `f2478b33` tip REMOVE + catalog_sql_* tokens | Agentic Judge overreach | **05** (flag EVIDENCED FAILING open) | OK |

**Misroutes:** none on these three.  
**Note:** Manual Reviewer OK+Needs Revision (e.g. eb599683 tip) → §3 → Cases 01/02/05/08 as notes split — not re-tested here as a fourth.

## Fix-guidance grading

Applied in case files 01, 03, 04, 05, 06, 08, 10, 13 and README honesty table.
