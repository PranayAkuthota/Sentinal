# S12 — Learning Capture

## Purpose
Capture reusable framework improvements after the task without corrupting archives or Ultra policy.

## Inputs
- Completed S11 artifacts / workflow_state
- Agent friction notes (redacted)

## Outputs
- `knowledge/proposals/<timestamp>__<task>__proposal.md`
- Optional human promotion via `promote_learning.py` into patterns/failures

## Validation
- Proposal contains reusable items only (no golden patches, hidden tests, UUID titles)
- Archives and `Review_Guidelines.mdc` untouched by learning scripts

## Failure
Promoting spoilers; auto-editing policy; rewriting historical ZIPs.

## Recovery
Delete or redact the bad proposal; re-capture with cleaner notes.

## Automation
`capture_learning.py` (proposals only). `promote_learning.py` assists stubs after human choice — never auto-merges policy.
