# Module — Judge rehearsal (single-model Quality Check panel simulation)

**Stage:** S10.5  
**Inputs:** `task_outputs/<TASK>/judge_prep.json` (+ `.md`), `instruction.md`, `tests/tests.patch`,
`tests/config.json`, `solution/` listing, optional `judge_prep_decisions.json`  
**Output:** `task_outputs/<TASK>/judge_rehearsal.md`  
**Patterns:** P-010 (Judge before Difficulty), P-011 (overreach / ≥3.5), P-006 (no filler f2p)

You are **not** the real two-model platform panel. Label every deliverable as a
**single-model rehearsal**. Still simulate disagreement: run **two** scoring passes with
different adversarial framings, then reconcile.

## Preconditions

1. `judge_prep.json` exists. If `hard_stopped: true`, stop — fix hard-stop inputs first.
2. Read §0 banner: open FIXABLE static-check ids block packaging but the map may still be useful.
3. If `map_stats.low_confidence`, treat scores as provisional and require human review notes.
4. Never invent filler fail-to-pass tests to raise counts (P-006). Prefer trimming untested
   instruction claims or adding real assertions tied to an R#.

## Pass A — adversarial coverage (“stub solution”)

Assume a stub / minimal implementation that barely touches the instruction surface.
Ask: **which graded tests still pass?** For each R# with status `gap`, assume the
requirement is unmet. Score axes with a **coverage-hostile** lens:

- Drive `test_coverage` down when unexplained gaps remain.
- Do not invent asserts the prep map did not support.

## Pass B — adversarial faithfulness (“instruction-only engineer”)

Assume a competent engineer who read **only** `instruction.md` (plus public codebase
contracts named there). Ask: **which graded assertions punish them unfairly?** For each
`overreach_candidate`, assume faithfulness damage. Score with a **faithfulness-hostile** lens.

## Reconcile (adjudicator simulation)

For each of the 10 axes, take Pass A and Pass B scores (1–5).

- If |A − B| ≥ 2 on an axis → mark **NEEDS_HUMAN_REVIEW** for that axis (do not silently average away the disagreement).
- Otherwise use the midpoint rounded to one decimal (or the more conservative score if midpoint is ambiguous).

### Axes (score all)

| Axis | Group |
|------|--------|
| realism, clarity, self_containedness, prescriptiveness | Instruction |
| test_coverage, test_faithfulness | Tests (verdict drivers) |
| spec_faithfulness, no_gaming, robustness | Oracle |
| packaging | Packaging |

One-line justification per axis citing `file:line` or `R#`/`A#` from judge_prep.

### Platform verdict logic (test axes ONLY)

- **REMOVE** (NEEDS_REVISION): reconciled score on either test axis ≤ 2.0, OR either pass
  scored an axis ≤ 2 matching an essential auto-REMOVE pattern (cite `auto_remove` HIT).
- **DISCUSS** (NEEDS_REVISION): either pass scored either test axis ≤ 2, OR reconciled
  score on either test axis ≤ 3.0.
- **OK:** both test axes > 3.0 with no pass at ≤ 2.

### Operational bar (P-010 / P-011) — stricter than OK

Refuse to package while **any** of the 10 reconciled axes is **below 3.5**.
“3 with reservations” is not shippable.

## Minimal edits (axes below 4)

For each axis &lt; 4, give **one** concrete minimal edit:

- Coverage gap → exact assertion sketch tied to the R# (not a filler suite).
- Faithfulness / overreach → **either** add an observable requirement to the instruction
  **or** relax/ungrade the A# — never both in one step; never PR spoilers / hidden test names.
- Packaging hard-cap → delete the listed stray path (or restore tracked-only if misflagged).

## Output template (`judge_rehearsal.md`)

```markdown
# Judge rehearsal — <TASK>
Model: single-model rehearsal (not the live Opus/GPT panel)
Generated: <ISO8601>

## Pass A (coverage-hostile) scores
| axis | score | cite |
...

## Pass B (faithfulness-hostile) scores
| axis | score | cite |
...

## Reconciled
| axis | A | B | final | Δ≥2 human review? |
...

## Verdict
platform_logic: REMOVE | DISCUSS | OK
operational_bar_3_5: PASS | REFUSE_PACKAGE
notes: ...

## Minimal edits
1. ...
```

## Do not

- Claim the live platform already scored this task
- Skip Pass B or collapse to one pass
- Add filler f2p only to raise counts
- Overwrite `judge_prep_decisions.json`
- Dump implementation spoilers into the instruction to “fix” overreach
