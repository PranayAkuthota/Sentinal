# Case 15 · tests.patch fails git apply

**Status:** PROVISIONAL (n=1 catalogue family; related apply flakiness in JF021 is Case 01)

`tests.patch` applies with GNU patch but fails `git apply --check` (renames/hunk headers).

## Recognise it

Catalogue F-003: `GNU patch applies but git apply --check fails (renames/hunk headers)`.

Nearby but different: JF021 `tests.patch apply dies if tree_pr173_test.rs exists; rm -f before apply` → route packaging apply hygiene to Case 01 unless dialect check fails.

## Read first

- `knowledge/patterns/P-001_tests_patch_must_pass_git_apply.md`
- `knowledge/failures/F-003_tests_patch_git_apply_failure_after_patch_only_green.json`

## Diagnose before editing

1. On base commit: `git apply --check` tests.patch.
2. If only “file exists” conflict, prefer Case 01 pre-clean — not this case.
3. Written finding: dialect/rename vs dirty tree.

## Fix — pick ONE direction per defect

Rebuild `tests.patch` so `git apply --check` passes on the task base commit.

## Verify before repackaging

- [ ] `git apply --check` clean on base
- [ ] Harbor test.sh apply path still works
- [ ] Graded tests still present after apply

## Do not

- Ship after “patch-only green” without git-apply check.
- Confuse with Case 01 file-exists pre-clean.

## Instances

- FC003 F-003 · git apply --check fails after patch-only green · rebuild patch · next unknown
  (`seen_count=3` in catalogue — if treated as our history n≥2, promote to CONFIRMED on next pass; kept PROVISIONAL until Part A rows are split per occurrence)
