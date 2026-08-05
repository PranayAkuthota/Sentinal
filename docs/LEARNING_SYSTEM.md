# Learning system

## Goal

Make the framework better after every completed Sentinel task without corrupting archives or automating judgement.

## Loop

```text
Complete S11 packaging/answers
    → S12 capture_learning.py
    → knowledge/proposals/*.md
    → human review
    → promote_learning.py pattern|failure  (or manual files)
    → knowledge/patterns or knowledge/failures
    → optionally update Operational Patterns / checklists (not Ultra policy unless docs change)
```

See also: `docs/FAILURE_CATALOG.md`.

## What may be learned

- Packaging traps
- Patch/apply hazards
- Grading config pitfalls
- Workflow friction (paths, Docker, multi-session)
- Checklist gaps

## What must not become permanent knowledge

- Task UUIDs as pattern titles
- Hidden test bodies / golden patches
- One-off fixture constants
- Spoilers that would leak into future agent-facing instructions

## Automation boundary

`capture_learning.py` only writes proposals. It never edits `Review_Guidelines.mdc`, never deletes `task_outputs`, never rewrites completed ZIPs.
