# Case 04 · Test coverage gap

**Status:** CONFIRMED (n≥2)

Requirements ungraded, weakly sampled, or mocks let a stub pass. Opposite of Case 05.

## Recognise it

- `… test required subset omits Pressure, Rcut…`
- `get_asset mocks GsAsset so raw-dict passthrough passes`
- `chip data-context-slot … not graded` (+ siblings)
- `never verifies refactor away from Arc Mutex…`
- `allow_extra_failures true leaves … ungraded` (ledger)
- `verifier also runs unrelated legacy tests…` (V16 shape)

## Read first

- `.cursor/skills/sentinel-ultra-review/reference/test-quality.md`
- `knowledge/patterns/P-006_*`, `P-013_*`, `P-002_*`
- `OUTCOMES.md`

## Diagnose before editing

1. List each coverage cite as a missing observable.
2. Choose **add graded test** vs **trim untested claim** (P-006).
3. Check grading config: `allow_extra_failures` and execution suite scope.

## Fix — pick ONE direction per defect

| Shape | Direction | Evidence |
|-------|-----------|----------|
| `allow_extra_failures=true` hides ungraded requirements | Set `false` + scope execution to task tests | **EVIDENCED WORKING** — cite **resolved** next round on `c6889dd0` (`2026-08-06`→`08-08`). |
| Unrelated suites in execution (V16) | Scope command to tests.patch paths only | **EVIDENCED WORKING** — unrelated legacy suite cite **resolved** on `965e30ce` first pair. |
| Instruction claims X, no test | Add f2p **or** trim claim (P-006) | Trim ArcMutex (JF014) **applied**; next **UNTESTED**. Adding f2p for mocks/filters mostly **UNTESTED** round-over-round. |
| Mock/stub lets wrong impl pass | Assert real observable | **UNTESTED** as proven clear (965e30ce still grew new coverage cites). |
| Dump fixture keys into instruction to “cover” | — | **EVIDENCED FAILING** path → Case 06 (do not). |

## Verify before repackaging

- [ ] Kept requirements have graded coverage
- [ ] `allow_extra_failures=false` and scoped execution
- [ ] No private-internals asserts (Case 05)
- [ ] instruction ≡ problem_statement

## Do not

- Merge with Case 05.
- Fix coverage by over-prescribing instruction.

## Instances

- JF005 0cf2e9a3 · subset omits… · unknown
- JF014 1e6ecbbd · ArcMutex TRIM **applied** · next unknown
- JF016 7b88ff8e · partial migration · unknown
- JF027 JF028 965e30ce · mock/filters · unknown
- JF031 a8d30c64 · blocked banner · unknown
- JF032 JF033 JF034 JF035 JF036 a8d30c64 · chip family · unknown
- JF049 d41a2c3a · native/MINGW · unknown
- JF056 JF058 eb599683 · weak still/cli · unknown
- FC001 F-001 · no f2p · unknown
- Chain c6889dd0 · allow_extra true · **resolved**
- Chain 965e30ce · unrelated suites · **resolved**
