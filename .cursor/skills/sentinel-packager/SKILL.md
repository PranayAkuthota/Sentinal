---
name: sentinel-packager
description: >-
  Deterministic Sentinel packaging hygiene and ZIP build for Fixable Harbor tasks.
  Use when preparing corrected ZIPs, ensuring Harbor network blocks in task.toml,
  stripping docker_compose network_mode=none, extracting grade.py, or running
  preflight/package-fixable.
---

# Sentinel Packager Skill

## Preconditions — stop if any fail

1. Duplicate Analysis is **Fixable** (and Public matches Duplicate).
2. `work/<TASK>/working_copy/` exists and is the edit surface.
3. Execution **04** / S8 complete — no packaging before verdicts.
4. Content edits for this revision are finished (or only hygiene remains).

## Sequence (stop on first failure)

```bash
python3 automation/sentinel_submitter.py ensure-packaging-hygiene --task-name TASK
# if instruction changed:
python3 automation/sentinel_submitter.py sync-problem-statement --task-name TASK
python3 automation/local_oracle_nop.py --task-name TASK --mode both
python3 automation/sentinel_submitter.py record-validation --task-name TASK \
  --check oracle --status passed --evidence … --reward 1.0
# similarly for nop / docker_build with real evidence
python3 automation/sentinel_submitter.py preflight --task-name TASK
# only if ready_to_package:
python3 automation/sentinel_submitter.py package-fixable --task-name TASK
```

Walk `docs/SUBMITTER_BLOCKERS.md` before claiming upload-ready.

## Outputs

- Upload: `work/task ready_to_submit/<TASK>__corrected.zip` (delete-first)
- Mirror: `task_outputs/<TASK>/updated_zip_file/<TASK>__corrected.zip`

## Hard rules

1. Do not invent validation results.  
2. Do not decide verdicts.  
3. Do not package Valid-as-is or Invalid as a corrected valid ZIP.  
4. Do not include `runs/` or reports inside the ZIP.  
5. Do **not** strip `network_mode` / `allowed_hosts` from `task.toml` — ensure the Harbor three-block contract instead.
