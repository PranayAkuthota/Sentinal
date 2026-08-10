# Revision case library

Self-maintaining playbooks mined from this repo’s platform feedback
(`knowledge/judge_feedback/`), failure catalogue, and revision handoffs.
Not from memory or anecdote.

## Honesty (read this)

As of 2026-08-10 inventory + ledger round-chain backfill:

- **73** Part A failure instances (tip feedback + catalogue)
- **22** consecutive ledger pairs chained → see `OUTCOMES.md`
- Citation outcomes from chaining: **resolved=104**, **not_resolved=13**, **regressed=5**
- Tip `fixes_applied` still sparse — only handoff-reconstructed for 1e6ecbbd / eb599683,
  and those tip rounds have **no following response yet**

**Case “Fix” sections remain mostly reasoning** unless an Instances row cites a chained
outcome or a reconstructed fix. Prefer `OUTCOMES.md` for what actually recurred.

### Handoff-reconstructed fixes (next-round still unknown)

| Instance | Task | What was recorded |
|----------|------|-------------------|
| JF014 | 1e6ecbbd | 07 handoff: TRIM ArcMutex claim from instruction |
| JF015 | 1e6ecbbd | 07 handoff: delete irregular `pass_at_k_*` fields |
| JF052 | eb599683 | 07 handoff: restore `.python-version` / original HEAD |
| JF053 | eb599683 | 07 handoff: forward-only `solve.sh` |
| JF059 | eb599683 | 07 handoff: `difficulty` / `model_difficulty` = hard |

### Chained evidence that Fix guidance can trust (examples)

| Working (resolved next round) | Failing / oscillating |
|------------------------------|------------------------|
| Fail-open scan-loops (0cf2e9a3) | Difficulty FAIL EASY recurring (004e50af) |
| solve.sh reverse-apply absent next round | Faithfulness “state it” → Q9/Q10 (0cf2e9a3 regressed) |
| allow_extra_failures true cleared (c6889dd0) | catalog_sql_* overreach not_resolved (f2478b33) |

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
