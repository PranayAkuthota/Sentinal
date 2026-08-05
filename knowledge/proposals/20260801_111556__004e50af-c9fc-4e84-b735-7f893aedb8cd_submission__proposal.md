# Learning proposal (pending human review)

- Generated: 20260801_111556 UTC
- Task ref: thrift Haxe codegen Fixable pass (do not promote UUID into pattern titles)
- Branch recorded: Fixable
- Structural f2p count: 16

## Candidate reusable patterns

1. Prefer trimming untested instruction claims over inventing thin f2p when coverage gaps are prose-only (import shadowing / typedef skip / special float round-trips).
2. Compiler-build verifier suites often need verifier.timeout_sec well above 300 when cmake+make runs inside tests — bump within the 1800 cap when packaging Fixable.
3. tests.patch headers that cite upstream PR/JIRA numbers are low-risk but cheap to scrub when regenerating the patch; prefer AssertionError over SkipTest for missing build tools so Harbor SKIPPED cannot look like a soft pass.
4. Dirty trees that are almost entirely 100755→100644 mode flips are Fixable via `git reset --hard` + reflog removal — do not treat as content corruption.

## Automation opportunities (deterministic only)

- Flag instruction phrases that mention behaviors with zero graded test name overlap (heuristic coverage gap warning).
- Warn when verifier.timeout_sec < 600 and tests.patch / test.sh invoke cmake|make|configure.

## Suggested failure catalog entries

- category: Instruction specification
  symptom: Instruction asserts behaviors (import suppression, typedef import skip, special float round-trip) with no fail_to_pass coverage
  recovery: Rewrite instruction to tested contracts, or add meaningful f2p within PR scope

- category: Unit test setup
  symptom: unittest.SkipTest when cmake/make missing in Harbor verifier that only counts PASSED
  recovery: Raise hard error; ensure Dockerfile installs the toolchain

## Agent notes (redacted)

Local oracle helper initially called `python` missing in image — workspace tooling fix to `python3`, not a task ZIP change.

## Workflow state warnings (structural)

allow_extra_failures=true — expert still owns coverage; all patch tests were graded in this task (16 f2p + 3 p2p).

---

**Promotion rule:** Human merges accepted items into `knowledge/patterns/` or `knowledge/failures/`.
Never auto-edit `.cursor/rules/Review_Guidelines.mdc`.
