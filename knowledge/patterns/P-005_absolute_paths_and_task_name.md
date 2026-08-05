# P-005: Absolute paths + --task-name

**Status:** approved  
**Reusable:** yes

## Pattern

Prefer absolute paths and `python3`. When multiple `work/*` sessions exist, always pass `--task-name`.

## What to do

Never rely on cwd after `/tmp` disposable work; re-enter the framework root before automation commands.
