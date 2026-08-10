# Case 05 · Test faithfulness / overreach

**Status:** CONFIRMED (n≥2)

⚠ **Contradicts Case 06.** Dumping values/tokens into the instruction is how we
oscillated (0cf2e9a3: **3 regressed** citations → Q9/Q10).

Tests demand undeclared API, private structure, or literal tokens not in the instruction.

## Recognise it

- `bead_to_atom_name_dict required in UA Charmm constructor but never documented…`
- `UA atom-type letter assignment A->15.035 … pinned … instruction only names masses…`
- `ImageContext tests use manager[contextTray][containerEl] private access`
- `masked test enforces DMASKED_ALIAS regex / SLEEF_SUPPORTED_GNUABI_EXTENSIONS unstated`
- `uses_catalog_sql_api requires catalog_sql_prepare plus catalog_sql_execute[_once] specifically`
- `fork-safety tests require literal tokens catalog_close before and catalog_open after…`
- REMOVE / `overreach` (f2478b33)

## Read first

- `.cursor/skills/sentinel-ultra-review/reference/test-quality.md` (overreach)
- `.cursor/skills/sentinel-ultra-review/reference/judge-axis-playbook.md`
- `knowledge/patterns/P-011_*`, `P-012_*`
- This library: `06_q9_q10_instruction_overprescription.md`
- `OUTCOMES.md` (regressed / not_resolved rows)

## Diagnose before editing

1. Name the undeclared symbol / private path / literal token.
2. Is it a **real public API** the PR exposes, or a **test/fixture detail** (exact mass,
   letter, token order, private DOM)?
3. Default assumption: **fixture/arbitrary value** → soften test (see evidence below).
4. If you will expand the instruction, write the Case 06 re-check plan first.

## Fix — pick ONE direction per defect

| Direction | When | Evidence |
|-----------|------|----------|
| **B — Soften/remove the assertion (DEFAULT for arbitrary values)** | Exact masses, letter pins, match= tokens, private access, catalog_* literals, stub-internal shape | **EVIDENCED WORKING** as the safe default: avoids 05↔06 oscillation. Prefer this unless (A) applies. |
| **A — State public API contract in instruction (EXCEPTION)** | Named public function/behaviour the PR must expose — outcomes, not fixture dumps | **EVIDENCED FAILING** when used for arbitrary values: **3 regressions** on `0cf2e9a3` (unstated UA/NVT specifics → `Static Q9/Q10 FAIL… mirror NVT_REQUIRED_*`). Use only for true public API; never paste test key lists (P-012). |
| **catalog_sql_* / catalog_close-open token shape** | f2478b33 faithfulness REMOVE | **EVIDENCED FAILING** — **3 not_resolved** on `f2478b33` last pair (`2026-08-08T04:27`→`16:12`); a fourth cite appeared. Notes said “state API names / soften locations” — **that approach did not clear the cites**. Do not imply a known remedy; treat as open. Soften token/order asserts and/or state minimal public behaviour without file-location coupling — then re-check Case 06. |

**Default rewrite (data-backed):** for an arbitrary value the test pinned, **soften/remove the assert**. Stating it in the instruction is the exception for a real public API, and even then describe outcomes — not `NVT_REQUIRED_KEYS`-style dumps.

## Verify before repackaging

- [ ] Each cite resolved by B **or** exceptional A — not both blindly
- [ ] Re-scan instruction for Q9/Q10 (Case 06)
- [ ] catalog_sql_* family: do not claim “fixed by stating names” without new evidence
- [ ] judge-prep overreach / private_internals

## Do not

- Default to “put it in the instruction” — that is the failing pattern (count=3 regressed).
- Teach catalog_sql_* as a solved playbook — **not_resolved across rounds**.
- Ignore Case 06.

## Instances

- JF006 JF007 0cf2e9a3 · undocumented ctor / pinned letters · unknown · unknown
- JF037 a8d30c64 · private contextTray · unknown · unknown
- JF043 c6889dd0 · stub internal shape · unknown · unknown
- JF050 d41a2c3a · DMASKED_ALIAS unstated · unknown · unknown
- JF055 eb599683 · probe never called · unknown · unknown
- JF060 JF061 JF062 JF063 f2478b33 · catalog tokens · **EVIDENCED FAILING** not_resolved×3 · open
