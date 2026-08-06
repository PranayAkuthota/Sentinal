# P-013: GPT is the binding judge on both test axes

**Status:** approved (expert-authored from six simultaneous revisions; promote via INDEX)  
**Promoted:** 2026-08-06  
**Reusable:** yes  
**Distinct from:** P-010 / P-011 (Judge-before-Difficulty and overreach sync) — this is
about **which panel member** sets the binding score when models disagree.

## Pattern

Across six tasks returned in revision at once, the panel split systematically on the
blocking axes:

- **Summarised, not quoted:** Claude scored coverage/faithfulness in the **4–5** range;
  GPT scored **2–3**; every blocking verdict followed GPT’s lower score.

(Exact per-axis numbers and prose were not pasted as full judge reports into the
framework session — do not reconstruct wording from memory.)

Self-review that averages models or leans on the optimistic member under-predicts
removes/discusses. The binding reading is the strict one.

## Self-review bar (adopt before packaging)

1. Would every graded assertion still hold for a competent engineer who read **only**
   `instruction.md` (no test source, no spoilers)?
2. Does a stub / no-op implementation still **fail every** graded test?

If either answer is no, expect GPT (and the live panel) to score coverage or
faithfulness below the ≥ 3.5 revision bar even when Claude looks generous.

## Cite

Six-task simultaneous revision batch (ids as evidence only): `eb599683`, `004e50af`,
`c6889dd0`, `d41a2c3a`, `a8d30c64`, `965e30ce`. Mechanical co-causes encoded as
V15/V16, V9 source-ratio, Q9/Q10 guards, private-internals candidates, packaging
`.git` leakage — see Commit A detectors and `docs/SUBMITTER_BLOCKERS.md` §C 16j–16o.

## When it applies

Any Agent Judge revision where models disagree on `test_coverage` or
`test_faithfulness`, and whenever local rehearsal axes sit ≥ 4.0 while prior live
joins showed GPT-driven 2–3 on those axes (see also F-013 optimism note).
