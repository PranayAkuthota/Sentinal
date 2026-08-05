# S0 — Framework Boot

## Purpose
Load the correct role, authority stack, and path conventions before any task work. Confirm the workspace is the Sentinel framework root (not a nested task package).

## Inputs
- User role intent (submitter / reviewer / framework)
- Optional task ZIP path or existing `--task-name`
- Live platform field labels when provided

## Outputs
- Confirmed mode and entry prompt (`Prompts/Execution/01_…` or reviewer skill)
- Absolute-path + `python3` discipline acknowledged
- Optional doctor smoke if framework health is in doubt

## Validation
- Policy authority is `Review_Guidelines.mdc` + official Ultra docs
- Not reading `legacy_backup/`, `workspace_archive/`, or old `task_outputs` ZIPs as “the” task
- Multiple `work/*` sessions ⇒ `--task-name` required going forward

## Failure
Wrong role loaded; treating archives as active task; inventing commands not in `docs/COMMANDS.md`.

## Recovery
Stop, re-read `AGENTS.md` / `CLAUDE.md`, reopen the correct skill/prompt. Run `python3 automation/sentinel_doctor.py` if layout looks broken.

## Automation
`sentinel_doctor.py` (optional). No verdicts. No package mutations.
