# Case 02 · Editing-boundary violations

**Status:** CONFIRMED (n≥2)

We touched what we may never touch: tracked `environment/repo`, stash of solution,
mass deletes of tracked trees, or broken git ref packaging.

## Recognise it

- `stash commit a86ae6b1 WIP on main contains solution diff`
- `22 tracked files under web/frontend/src/features/runs deleted`
- `environment/repo was changed at tracked source level; restore original HEAD 464509679b48ae647a545d270aa8a1817fecc5a8 with .python-version`
- `refs/remotes/origin/HEAD null pointer`

## Read first

- `.cursor/rules/Review_Guidelines.mdc` — never edit tracked source under `environment/repo/`
- `docs/SUBMITTER_BLOCKERS.md` packaging / base_commit_sha
- Sentinel packager hygiene notes for `.git` leakage

## Diagnose before editing

1. Diff `environment/repo` against `base_commit_sha` / stated HEAD.
2. Search stash, WIP commits, deleted tracked paths, `refs/remotes/origin/HEAD`.
3. Separate from Case 01 (metadata/harness) — this is restore/realign, not “add grade.py.”
4. Write the illegal paths and the restore target SHA.

## Fix — pick ONE direction per defect

| Shape | Do this |
|-------|---------|
| Tracked source edited | Restore files from original HEAD; keep required tracked files (e.g. `.python-version`) |
| Stash/WIP holds solution | Drop stash/WIP from package; solution only in `golden.patch` / `solve.sh` |
| Mass tracked deletes | Restore tree; realign `base_commit_sha` if needed |
| Broken origin/HEAD | Repair or omit unsafe ref packaging per Harbor packaging rules |

Prevention ≠ artifact sweep: stop editing repo; don’t “clean” by deleting tracked features.

**Recorded applied fix:** JF052 restore HEAD + `.python-version` (eb599683 07 handoff). Next-round **unknown**.

## Verify before repackaging

- [ ] `environment/repo` matches allowed base; no solution diff in stash/WIP
- [ ] `base_commit_sha` consistent
- [ ] judge_prep packaging sweep / static-check clean of .git authoring junk
- [ ] Network blocks still present (Case 01)

## Do not

- Delete tracked upstream files to silence packaging hard-caps without reviewer agreement.
- Put solution hunks in stash commits.
- Fold this into Case 01 “packaging hygiene.”

## Instances

- 2026-08 · JF040 c6889dd0 · stash WIP contains solution · fix unknown · next unknown
- 2026-08 · JF044 c6889dd0 · 22 tracked files deleted · fix unknown · next unknown
- 2026-08 · JF052 eb599683 · repo changed; restore HEAD + `.python-version` · **applied** · next **unknown**
- 2026-08 · JF022 826cb164 · refs/remotes/origin/HEAD null pointer · fix unknown · next unknown
