# P-012: Faithfulness fixes that restate fixture values flip Q9/Q10 (contract vs instance)

**Status:** approved (expert-authored from live revision; promote via INDEX)  
**Promoted:** 2026-08-06  
**Reusable:** yes  
**Distinct from:** P-011 (overreach sync) — this is the *opposite-direction* oscillation when
fixing faithfulness by copying test instance values into the instruction.

## Pattern

Round 1 Agent Judge: **REMOVE / overreach** — “tests enforce values the instruction never
states.” Natural fix: add those values to `instruction.md`.

Round 2 Static Quality Check: **Q9/Q10 FAIL** — “the instruction lists the exact
NVT/NPT required fields and values that mirror `NVT_REQUIRED_KEYS` / `NVT_REQUIRED_VALUES`
— leaking internal test logic.” Faithfulness improves; packaging/prescriptiveness axes
and static QC bounce the other way on the **same text**.

The two checks pull in opposite directions when the instruction restates a **fixture
instance** (literal `ethane.inp`, `Temperature 300`, checklist shaped like the test dict)
instead of the **public output contract**.

## Resolution (guidelines already allow this)

Documenting a required output format / schema / API response shape is **necessary and is
NOT leakage**. Over-prescription is copying exact assertion strings / fixture values from
tests **unless** they are a genuine public/API contract.

Discriminator — keep information that is:

1. a **documented default** of the public writer, or
2. **derivable** from an input the instruction already names (Charmm base name →
   `Parameters` / `Coordinates` / `Structure`; `Temperature` arg → conf `Temperature`;
   FF 1-4 scaler → `1-4scaling`), or
3. a **force-field-derived** value the instruction already documents.

Drop or reframe anything that is only the test fixture’s concrete instance.

Presentation: group by function with brief prose (run control, structure inputs, cutoffs,
electrostatics), not a flat key/value dump that mirrors the test dictionary 1:1.

## Cite

Task `0cf2e9a3` (mbuild GOMC writers), round 1 REMOVE(overreach) → round 2 DISCUSS +
static 13/15 Q9/Q10 fail after stating NVT checklist values.

## Additional instances (six-revision batch — summarised, not quoted)

These came from submitter notes on simultaneous revision returns (full judge report
bodies were not pasted into the framework session). Treat as mechanical summaries,
not verbatim judge text:

- **eb599683 — Q10:** instruction requires the error message to contain
  `'unsupported'` and `'format'`; the test asserts
  `match=r'(?i)unsupported.*format'`. Same oscillation class: stating the test’s
  literal match words in the instruction to fix faithfulness risks Q10 leakage.
- **a8d30c64 — Q9:** instruction text amounting to “Update styles under
  `src/style/`” is navigation hand-holding (path-as-navigation), not a public API
  import path.

Framework guard: `judge_prep` blocks Q10 error-message literal-word requirements;
Q9 filesystem paths near imperatives are candidates only (P-011 rehearsal confirms).

## When it applies

Any revision where faithfulness is fixed by pasting graded assertion literals into the
instruction, especially writer/CLI output tasks with large required-field sets. Also
when error-message word lists or edit-path walkthroughs are added to clear overreach.
