# Pitfall 11 · Stale platform ZIP mirror

**Status:** PROVISIONAL (n=1 in our history)

**Not a task defect.** Do not route DISCUSS/REMOVE here.
Check **before** revision edits when a local mirror exists.

## Recognise it

F-014: revision work ran against `task_outputs/<task>/updated_zip_file/<task>__corrected.zip`
while the Agent Judge scored a different platform-downloaded `*__corrected.zip`.
Example: 965e30ce mirror `allow_extra_failures=true` vs platform `false` + unrelated suites.

## Read first

- `knowledge/failures/F-014_stale_updated_zip_mirror_vs_platform_download.json`
- `Prompts/Execution/07_platform_revision.md`
- `automation/checkpoint_ready.py` `--platform-zip`

## Diagnose before editing

1. Locate platform download ZIP and local mirror.
2. Compare SHA-256.
3. If mismatch or mirror-only: stop task edits.

## Fix — pick ONE direction per defect

Re-import / refresh working_copy from the **platform** ZIP. Pass `--platform-zip` so
checkpoint fails loud on SHA mismatch. Never calibrate detectors on the stale mirror alone.

## Verify before repackaging

- [ ] SHA match (or mirror deleted and platform zip is source of truth)
- [ ] working_copy matches platform bytes for task.toml / tests config

## Do not

- “Fix” Judge citations against the wrong package.
- Route feedback to this pitfall as the defect.

## Instances

- 2026-08-06 · FC014 F-014 · 965e30ce mirror ≠ platform · SHA gate / re-import · next unknown
