# Knowledge plane

Permanent, **reusable** operational knowledge for the Sentinel Submitter framework.

| Path | Purpose |
|------|---------|
| `patterns/` | Merged reusable patterns (human-approved) |
| `failures/` | Anonymized failure modes + recovery |
| `proposals/` | Auto/agent proposals after each task (pending review) |

## Rules

- Never store full task solutions, golden patches, or hidden test bodies.
- Never modify `work/`, `task_outputs/`, or `completed_tasks/` from learning scripts.
- Promote `proposals/` → `patterns/` or `failures/` only after human review.
- Assist stubs: `python3 automation/promote_learning.py pattern|failure …`
- Prefer patterns that appeared in ≥2 tasks before promoting to Operational Patterns.
- Never auto-edit `Review_Guidelines.mdc` from learning scripts.
- See `docs/LEARNING_SYSTEM.md` and `docs/FAILURE_CATALOG.md`.
