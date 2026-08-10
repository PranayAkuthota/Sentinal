# Revision case library

Self-maintaining playbooks mined from this repo’s platform feedback
(`knowledge/judge_feedback/`), failure catalogue, and revision handoffs.
Not from memory or anecdote.

## Honesty (read this)

As of 2026-08-10 inventory:

- **73** failure instances in Part A
- **0** with `next_round_result = yes`
- **1** with `next_round_result = no` (JF004 — Q9/Q10 oscillation)
- Almost all `fixes_applied` null in feedback records

**Every “Fix” section is reasoning plus handoff intent, not a validated remedy.**
Do not treat guidance as proven until capture populates `fixes_applied` and a later
response sets `next_round_result`.

### Only instances with any recorded applied fix

Even these have **unknown** next-round outcomes:

| Instance | Task | What was recorded |
|----------|------|-------------------|
| JF014 | 1e6ecbbd | 07 handoff: TRIM ArcMutex claim from instruction |
| JF015 | 1e6ecbbd | 07 handoff: delete irregular `pass_at_k_*` fields |
| JF052 | eb599683 | 07 handoff: restore `.python-version` / original HEAD |
| JF053 | eb599683 | 07 handoff: forward-only `solve.sh` |
| JF059 | eb599683 | 07 handoff: `difficulty` / `model_difficulty` = hard |

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

After capturing platform feedback: match → append Instances row; no match → new
provisional case. See Part D wiring in Execution 07 / `capture_judge_feedback`.
Coverage check: `python3 automation/revision_library_coverage.py` (added in Part D).
