# Pitfall 12 · Rehearsal optimism

**Status:** PROVISIONAL (n=1 live join)

**Not a task defect.** Rehearsal predicted OK while live Judge returned DISCUSS.
True, and useless as something to “edit in the zip.” Route the **citations** to cases/.

## Recognise it

F-013: at-upload `judge_prediction.json` predicted_verdict=OK with rehearsal axes ≥4.0 on
blocking test axes; live Agent Judge DISCUSS with both at 3.0 (0cf2e9a3). Citation recall 0/8.

## Read first

- `knowledge/failures/F-013_rehearsal_ok_live_discuss_optimistic_axes.json`
- `docs/VALIDATION_STRATEGY.md`
- `ROUTER.md` §0

## Diagnose before editing

1. Compare prediction vs live verdict/axes.
2. List live citations — those are the task work.
3. Do not invent a zip change named “make rehearsal less optimistic.”

## Fix — pick ONE direction per defect

Process only: treat the miss as calibration; fix cited task defects via cases 04–06 etc.;
keep future rehearsal conservative on blocking axes. Do not raise packaging bars from one join.

## Verify before repackaging

- [ ] Live citations mapped to cases and addressed (intent recorded)
- [ ] New prediction written honestly for next upload

## Do not

- Send a reviser here instead of Case 04/05/06.
- Conclude “rehearsal is broken so ignore Judge.”

## Instances

- 2026-08-06 · FC013 F-013 · 0cf2e9a3 OK→DISCUSS axes 4.5→3.0 · calibration note · next unknown
