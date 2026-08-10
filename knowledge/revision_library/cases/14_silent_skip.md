# Case 14 · Silent skip / SkipTest soft-pass

**Status:** CONFIRMED-BY-RULE

Official Ultra / skill docs name **Silent skip** as one of the six auto-REMOVE patterns.
If a dependency is missing, the test must **fail**, not skip.

## Recognise it

Doc patterns: `@pytest.mark.skip`, `skipif`, catching `ImportError` and setting the module
to `None`, or any construct that lets substantive tests silently not run.

Catalogue F-002: `unittest.SkipTest when cmake/make missing in Harbor verifier that only
counts PASSED`.

## Read first

- `.cursor/skills/sentinel-ultra-review/reference/test-quality.md` (Silent skip)
- `.cursor/skills/sentinel-ultra-review/reference/fix-playbooks.md` § F6
- `knowledge/patterns/P-008_hard_fail_missing_build_tools_instead_of_skiptest.md`
- `knowledge/failures/F-002_skiptest_soft_pass_when_toolchain_missing.json`

## Diagnose before editing

1. Search tests.patch for skip/skipif/SkipTest/ImportError→None.
2. Check Dockerfile installs required toolchain.
3. Written finding: soft-pass paths listed.

## Fix — pick ONE direction per defect

- Delete skips; bake dependency into verifier image.
- Missing toolchain → hard fail, not SkipTest.

## Verify before repackaging

- [ ] No silent skip on substantive graded tests
- [ ] Image has tools tests need
- [ ] Auto-REMOVE silent_skip clear

## Do not

- Call SkipTest a “clean pass” when Harbor counts PASSED only.
- Treat as provisional — named auto-REMOVE.

## Instances

- FC002 F-002 · SkipTest when cmake/make missing · hard error + install tools · next unknown
  (`seen_count=2` in catalogue; still CONFIRMED-BY-RULE regardless)
