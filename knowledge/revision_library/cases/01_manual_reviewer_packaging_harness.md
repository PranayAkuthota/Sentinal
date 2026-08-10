# Case 01 · Manual Reviewer — packaging & harness

**Status:** CONFIRMED (n≥2)

Human reviewer sent it back with free-text packaging notes while Judge was often OK
(and Difficulty sometimes PASS HARD).

## Recognise it

Free-text Needs Revision, not a per-axis DISCUSS panel. Quoted from our ledger:

- `Every network setting is gone from task.toml`
- `Delete tests/grade.py; test.sh says no sibling`
- `Files Changed mismatched 36 f2p vs 20; network notes wrong`
- `grade.py does not enforce --raw-exit-code; nonzero raw must force reward 0`
- `task.toml missing difficulty_explanation; legacy difficulty hard vs model_difficulty medium`
- `tests.patch apply dies if tree_pr173_test.rs exists; rm -f before apply`
- Catalogue: corrected ZIPs shipped with network blocks removed (F-011)

## Read first

- `.cursor/rules/Review_Guidelines.mdc` (Harbor network blocks; never strip)
- `docs/SUBMITTER_BLOCKERS.md` (packaging / grade.py)
- `knowledge/patterns/P-003_fixable_packaging_strip_network_ensure_grade.md` (corrected)
- `knowledge/failures/F-011_corrected_zips_stripped_network_blocks_pre_2026_08_05.json`

## Diagnose before editing

1. Confirm Judge/Difficulty status — do not “harden” axes that already passed.
2. List each reviewer bullet; tag packaging vs editing-boundary (Case 02) vs test/instruction.
3. Open `task.toml`, `tests/test.sh`, `tests/grade.py`, Files Changed narrative.
4. Write: which Harbor blocks missing; whether grade.py is required sibling; metadata mismatches.

## Fix — pick ONE direction per defect

| Shape | Do this | Not that |
|-------|---------|----------|
| Network settings gone | Restore per-block: env `public`, agent `allowlist` + `allowed_hosts=["api.portkey.ai"]`, verifier `no-network` | Do not strip “for hygiene” |
| grade.py / test.sh | Align: embed or sibling as test.sh claims; enforce `--raw-exit-code` → reward 0 | Do not delete grade.py while test.sh forbids sibling |
| Files Changed / f2p count | Make narrative match graded list | Do not invent counts |
| Missing difficulty_explanation / os | Add honest fields; align difficulty labels | Do not invent pass_at_k (see Case 10) |
| apply dies if file exists | Pre-clean or make patch idempotent for that path | Do not leave flaky apply |

**Intent only — not validated next-round.** Recorded applied fixes elsewhere: none in this case’s IDs.

## Verify before repackaging

- [ ] `task.toml` network blocks present (static-check T3–T6)
- [ ] grade.py / test.sh agreement
- [ ] Files Changed matches fail_to_pass
- [ ] Re-run packaging hygiene; do not strip network
- [ ] Judge OK / Difficulty PASS preserved if they were already green

## Do not

- Treat this as a Judge coverage rewrite when Judge already OK.
- Strip `allowed_hosts` / `network_mode` from task.toml.
- Confuse with Case 02 (illegal repo/git edits).

## Instances

- 2026-08 · JF020 826cb164 · `Every network setting is gone from task.toml` · fix unknown · next unknown
- 2026-08 · JF021 826cb164 · tests.patch apply dies if tree exists · fix unknown · next unknown
- 2026-08 · JF023 826cb164 · tests/grade.py stray static check · fix unknown · next unknown
- 2026-08 · JF045 c6889dd0 · Files Changed mismatched 36 vs 20 · fix unknown · next unknown
- 2026-08 · JF046 c6889dd0 · Delete tests/grade.py · fix unknown · next unknown
- 2026-08 · JF047 c6889dd0 · missing difficulty_explanation; hard vs medium · fix unknown · next unknown
- 2026-08 · JF057 eb599683 · grade.py raw-exit-code · fix unknown · next unknown
- 2026-08 · JF059 eb599683 · missing os/difficulty_explanation; set hard · **applied** in 07 handoff · next **unknown**
- 2026-08-05 · FC011 F-011 · network blocks stripped pre-hygiene fix · ensure blocks · next unknown
