# Case 04 · Test coverage gap

**Status:** CONFIRMED (n≥2)

Requirements ungraded, weakly sampled, or mocks let a stub pass. Opposite of Case 05.

## Recognise it

Platform wording examples:

- `gpt: _get_default_variables_dict must include … but test required subset omits Pressure, Rcut, LRC, ChemPot, Fugacity`
- `get_asset mocks GsAsset so raw-dict passthrough passes`
- `SecurityMaster exchange/asset-type filters not verified on query`
- `chip data-context-slot and data-context-id not graded` (+ aria/icon/span/destroy/overflow siblings)
- `assertions only sample a few surfaces; partial migration … can still build and pass`
- `never verifies refactor away from Arc Mutex or construction only via with_context…`
- `Blocked at agentic judge. Verdict: discuss (coverage_gap). Oracle check not run.`
- Catalogue F-001: instruction asserts behaviors with no fail_to_pass coverage

## Read first

- `.cursor/skills/sentinel-ultra-review/reference/test-quality.md`
- `.cursor/skills/sentinel-ultra-review/reference/judge-axis-playbook.md` (test_coverage)
- `knowledge/patterns/P-006_prefer_trimming_untested_instruction_claims_over_thin_f2p_fi.md`
- `knowledge/patterns/P-013_gpt_binding_judge_on_test_axes.md`

## Diagnose before editing

1. List each coverage citation as a missing observable check.
2. Map citation → instruction sentence (or mark “instruction claims X, no f2p”).
3. Choose **add graded test** vs **trim untested claim** (P-006) — write the choice.
4. Confirm not faithfulness/overreach (Case 05) before adding asserts on private APIs.

## Fix — pick ONE direction per defect

| Shape | Direction A | Direction B |
|-------|-------------|-------------|
| Instruction claims X, no test | Add meaningful f2p for X (PR scope) | Remove/narrow claim (P-006) |
| Mock/stub lets wrong impl pass | Assert on real observable | — |
| Partial sample of surfaces | Broaden checks | Narrow instruction to sampled set |

Do **not** “fix coverage” by dumping fixture keys into the instruction (that becomes Case 06).

**Recorded applied fix:** JF014 — TRIM ArcMutex claim (1e6ecbbd 07). Next **unknown**.

## Verify before repackaging

- [ ] Every kept instruction requirement has graded coverage
- [ ] No new private-internals asserts (Case 05)
- [ ] instruction ≡ problem_statement
- [ ] static-check / judge-prep; oracle/NOP if Fixable

## Do not

- Merge with Case 05.
- Satisfy coverage by over-prescribing instruction (Case 06 oscillation risk).

## Instances

- JF005 0cf2e9a3 · subset omits Pressure/Rcut/… · unknown · unknown
- JF014 1e6ecbbd · Arc Mutex / with_context · **TRIM applied** · unknown
- JF016 7b88ff8e · partial blksz migration · unknown · unknown
- JF027–028 965e30ce · get_asset mock; SM filters · unknown · unknown
- JF031–036 a8d30c64 · blocked banner + chip/aria/span/destroy/overflow · unknown · unknown
- JF049 d41a2c3a · native/MINGW only · unknown · unknown
- JF056, JF058 eb599683 · weak still/sample; cli_video untested · unknown · unknown
- FC001 F-001 · instruction without f2p · recovery stated · unknown
