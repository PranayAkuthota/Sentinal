# Round-chain outcomes (backfill)

Built by chaining `task_outputs/_judge_calibration_ledger.jsonl` rounds per task.
Judge **citations** only — verdict can improve while a defect persists, or worsen
while one citation resolved.

- Consecutive pairs chained: **22**
- Citation outcomes: **resolved=104**, **not_resolved=13**, **regressed=5**

## Honesty

These outcomes are **observed** from consecutive captured rounds. They still do not
prove which edit caused a resolution unless `fixes_applied` was recorded for that
round. Handoff-reconstructed fixes exist only for 1e6ecbbd (JF014/015) and
eb599683 (JF052/053/059) — and those tip rounds have **no following response yet**.

## Per pair

| task | from → to | verdicts | resolved | not_resolved | regressed | new |
|------|-----------|----------|----------|--------------|-----------|-----|
| 004e50af | `2026-08-06T13:56:36Z` → `2026-08-07T04:36:05Z` | DISCUSS→OK | 8 | 0 | 0 | 4 |
| 004e50af | `2026-08-07T04:36:05Z` → `2026-08-07T09:10:18Z` | OK→OK | 2 | 2 | 0 | 2 |
| 004e50af | `2026-08-07T09:10:18Z` → `2026-08-07T12:27:37Z` | OK→OK | 4 | 0 | 0 | 4 |
| 004e50af | `2026-08-07T12:27:37Z` → `2026-08-07T12:57:16Z` | OK→DISCUSS | 4 | 0 | 0 | 4 |
| 004e50af | `2026-08-07T12:57:16Z` → `2026-08-07T14:55:52Z` | DISCUSS→OK | 4 | 0 | 0 | 5 |
| 004e50af | `2026-08-07T14:55:52Z` → `2026-08-07T16:24:15Z` | OK→OK | 4 | 1 | 0 | 2 |
| 0cf2e9a3 | `2026-08-05T19:17:17Z` → `2026-08-06T06:21:58Z` | REMOVE→DISCUSS | 10 | 1 | 3 | 7 |
| 1e6ecbbd | `2026-08-07T04:41:53Z` → `2026-08-07T08:59:05Z` | DISCUSS→DISCUSS | 6 | 0 | 0 | 5 |
| 1e6ecbbd | `2026-08-07T08:59:05Z` → `2026-08-07T12:22:49Z` | DISCUSS→DISCUSS | 5 | 0 | 0 | 5 |
| 1e6ecbbd | `2026-08-07T12:22:49Z` → `2026-08-07T14:07:46Z` | DISCUSS→DISCUSS | 4 | 1 | 0 | 1 |
| 1e6ecbbd | `2026-08-07T14:07:46Z` → `2026-08-08T04:05:34Z` | DISCUSS→DISCUSS | 2 | 0 | 0 | 3 |
| 1e6ecbbd | `2026-08-08T04:05:34Z` → `2026-08-08T15:38:28Z` | DISCUSS→DISCUSS | 1 | 2 | 0 | 0 |
| 965e30ce | `2026-08-06T13:55:45Z` → `2026-08-07T04:33:00Z` | REMOVE→DISCUSS | 7 | 0 | 0 | 6 |
| 965e30ce | `2026-08-07T04:33:00Z` → `2026-08-07T04:55:33Z` | DISCUSS→DISCUSS | 5 | 1 | 0 | 5 |
| 965e30ce | `2026-08-07T04:55:33Z` → `2026-08-07T09:02:47Z` | DISCUSS→DISCUSS | 6 | 0 | 0 | 4 |
| c6889dd0 | `2026-08-06T10:01:16Z` → `2026-08-08T16:40:17Z` | REMOVE→OK | 4 | 0 | 2 | 8 |
| d41a2c3a | `2026-08-06T14:05:23Z` → `2026-08-07T09:06:18Z` | DISCUSS→OK | 6 | 0 | 0 | 7 |
| d41a2c3a | `2026-08-07T09:06:18Z` → `2026-08-07T12:24:57Z` | OK→OK | 6 | 1 | 0 | 3 |
| eb599683 | `2026-08-06T09:49:40Z` → `2026-08-08T04:02:17Z` | OK→OK | 7 | 1 | 0 | 7 |
| f2478b33 | `2026-08-07T13:43:52Z` → `2026-08-07T14:51:51Z` | REMOVE→DISCUSS | 5 | 0 | 0 | 4 |
| f2478b33 | `2026-08-07T14:51:51Z` → `2026-08-08T04:27:00Z` | DISCUSS→REMOVE | 4 | 0 | 0 | 3 |
| f2478b33 | `2026-08-08T04:27:00Z` → `2026-08-08T16:12:01Z` | REMOVE→REMOVE | 0 | 3 | 0 | 1 |

## Evidenced working (resolved citations with clear family)

Examples where a prior citation did not recur (not proof of a specific patch):

- **resolved** `004e50af` `2026-08-06T13:56:36Z`: helper-library semantics checked only with source substrings IntMap/ternary/StringMap/toHex; invalid helpers can pass
- **resolved** `004e50af` `2026-08-06T13:56:36Z`: environment/repo/lib/kotlin/.gradle and build/reports ship into agent-readable filesystem
- **resolved** `0cf2e9a3` `2026-08-05T19:17:17Z`: fail-open scan: test_save_charmm_psf loops for 8 !NATOM then else: pass — empty .psf can pass
- **resolved** `0cf2e9a3` `2026-08-05T19:17:17Z`: fail-open scan: test_save_charmm_pdb keyed on CRYST1 with else: pass — empty .pdb can pass
- **resolved** `0cf2e9a3` `2026-08-05T19:17:17Z`: fail-open scan: test_save_basic_NVT if/elif startswith chain ends else: pass with no final presence assert — empty .conf
- **resolved** `0cf2e9a3` `2026-08-05T19:17:17Z`: same fail-open shape on test_save_basic_NPT / GCMC / GEMC_NVT
- **resolved** `0cf2e9a3` `2026-08-05T19:17:17Z`: check UA psf/pdb for same fail-open pattern as AA writers
- **resolved** `0cf2e9a3` `2026-08-05T19:17:17Z`: solve.sh reverse-apply fallback makes re-run non-idempotent
- **resolved** `1e6ecbbd` `2026-08-07T04:41:53Z`: solve.sh git apply -R can undo already-applied solution
- **resolved** `965e30ce` `2026-08-06T13:55:45Z`: verifier also runs unrelated legacy tests for index APIs, time formatting, and timeseries docstrings [tests/config.json:
- **resolved** `c6889dd0` `2026-08-06T10:01:16Z`: allow_extra_failures true leaves blank-line full-message policy.error tool.call done/finish ungraded
- **resolved** `d41a2c3a` `2026-08-06T14:05:23Z`: solve.sh reverse-apply fallback can revert an already-patched tree

## Evidenced failing / oscillating

- **not_resolved** `004e50af` 2026-08-07T04:36:05Z→2026-08-07T09:10:18Z: FAIL EASY - Requires at least MEDIUM; claude-opus-4-8 100% (4/4); codex-gpt-5-5 100% (4/4)
- **not_resolved** `004e50af` 2026-08-07T04:36:05Z→2026-08-07T09:10:18Z: helper names escape_haxe_keyword and make_haxe_user_type_name part of contract but tests never asser
- **not_resolved** `004e50af` 2026-08-07T14:55:52Z→2026-08-07T16:24:15Z: Difficulty FAIL EASY: claude-opus 75% (3/4), gpt 100% (4/4); need worse model <=50%
- **regressed** `0cf2e9a3` 2026-08-05T19:17:17Z→2026-08-06T06:21:58Z: UA propanol PSF/PDB specifics not in instruction: charges 0.265/-0.700/0.435, at ⇒ Static Q9/Q10 FAIL: instruction lists exact NVT/NPT required fields and values t
- **regressed** `0cf2e9a3` 2026-08-05T19:17:17Z→2026-08-06T06:21:58Z: NVT conf asserts defaults not listed in instruction: CBMC_First=12, DisFreq/RotF ⇒ Static Q9/Q10 FAIL: instruction lists exact NVT/NPT required fields and values t
- **not_resolved** `0cf2e9a3` 2026-08-05T19:17:17Z→2026-08-06T06:21:58Z: instruction enumerates ~75 optional GOMC input-variable names in exact order and _get_default_variab
- **regressed** `0cf2e9a3` 2026-08-05T19:17:17Z→2026-08-06T06:21:58Z: instruction requires VDWGeometricSigma False but writer only emits when true ⇒ Static Q9/Q10 FAIL: instruction lists exact NVT/NPT required fields and values t
- **not_resolved** `1e6ecbbd` 2026-08-07T12:22:49Z→2026-08-07T14:07:46Z: prompt dictates ghost-cell, Context brand, with_context, enumerated builders
- **not_resolved** `1e6ecbbd` 2026-08-08T04:05:34Z→2026-08-08T15:38:28Z: freestanding ambient Context::new / Arc Mutex design not enforced; wrapper around new could pass
- **not_resolved** `1e6ecbbd` 2026-08-08T04:05:34Z→2026-08-08T15:38:28Z: model_difficulty medium vs difficulty hard; baselines n/3 irregular
- **not_resolved** `965e30ce` 2026-08-07T04:33:00Z→2026-08-07T04:55:33Z: aggregate_risk groups/sums vs retain contributor rows
- **regressed** `c6889dd0` 2026-08-06T10:01:16Z→2026-08-08T16:40:17Z: instruction says text.delta append via e.g. data.text but test asserts data.delt ⇒ instruction says because the suite calls that helper / called directly by the su
- **regressed** `c6889dd0` 2026-08-06T10:01:16Z→2026-08-08T16:40:17Z: raw JSON array accepted by test/oracle but instruction says fenced only else Non ⇒ instruction says because the suite calls that helper / called directly by the su
- **not_resolved** `d41a2c3a` 2026-08-07T09:06:18Z→2026-08-07T12:24:57Z: Set medium with 3/4 Opus and 2/4 GPT
- **not_resolved** `eb599683` 2026-08-06T09:49:40Z→2026-08-08T04:02:17Z: MP4 probe never asserts fps
- **not_resolved** `f2478b33` 2026-08-08T04:27:00Z→2026-08-08T16:12:01Z: uses_catalog_sql_api requires catalog_sql_prepare plus catalog_sql_execute not named in prompt
- **not_resolved** `f2478b33` 2026-08-08T04:27:00Z→2026-08-08T16:12:01Z: fork-safety tests require literal catalog_close before and catalog_open after worker-spawn
- **not_resolved** `f2478b33` 2026-08-08T04:27:00Z→2026-08-08T16:12:01Z: helpers must be discoverable in catalog.c/summary.c with SQL in C string literals

## Case library mapping (rough)

| Case family | Signal in chain |
|-------------|-----------------|
| 03 Difficulty FAIL EASY | FAIL EASY / 100% (4/4) recurring not_resolved |
| 05↔06 oscillation | regressed rows + Q9/Q10 new after unstated→stated |
| 08 solve.sh reverse | reverse-apply resolved when absent next round |
| 13 fail-open | fail-open scan resolved 0cf2e9a3 round1→2 |
| 02 editing-boundary | new stash/repo-edit cites after prior OK |

