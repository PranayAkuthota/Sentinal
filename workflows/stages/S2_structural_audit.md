# S2 — Structural Harbor Audit

## Purpose
Deterministic structural scan of the Harbor package: required files, format dialect, patch health, metadata limits, git hygiene signals, ungraded tests.

## Inputs
- Prepared `work/<task>/` with resolved task root
- Prefer scanning `extracted_original` task root (or prepared copy used by audit)

## Outputs
- Audit report under `work/<task>/analysis/` and/or `task_outputs/<task>/`
- Recorded f2p/p2p counts, patch apply status, warnings (e.g. `allow_extra_failures`)

## Validation
- Required Harbor files inventory complete
- `tests.patch` checked with **git apply** (not only `patch(1)`)
- Metadata limits and network-field presence noted
- Instruction ↔ `problem_statement.md` sync noted

## Failure
Missing critical Harbor files; unreadable `task.toml`; patch cannot be analyzed.

## Recovery
If structure is unrecoverable for a corrected upload, route toward Invalid evidence later (expert). Most hygiene issues are Fixable after S8.

## Automation
`sentinel_submitter.py audit`. Never assigns Public/Internal/Duplicate.
