# Pre-hardening inspection (July 23, 2026)

## Active rule conflicts
1. Expert Reference: network_mode/allowed_hosts "do not remove" vs Review_Guidelines "Remove" for Fixable corrected packages.
2. Expert Reference: "do not add tests in Cursor Submitter Mode" vs Fixable working_copy may add tests via tests.patch.
3. Expert Reference packaging: "do not rename solution.patch" vs Review_Guidelines rename to golden.patch on Fixable.
4. Expert Reference still contains full duplicated platform templates (should be short checklist only).

## Duplicated rules
- Full Templates A/B/C in Expert Reference duplicate Submitter Workflow.
- f2p count rules repeated across CLAUDE, Workflow, Expert Reference, Review_Guidelines.

## Unsupported legacy behavior
- Old permanently read-only submitter audits remain as historical markdown only (OK if not active).
- Automation auto-picks best-scoring task root instead of stopping on multiples.

## Missing automation checks
- No prepare/audit/select-task/sync-problem-statement/record-validation/preflight.
- No workflow_state.json schema v3.
- package-fixable does not require ready_to_package or full preflight.
- No instruction byte-equality gate, config/f2p structural validation gate, git hygiene gate, artifact scan gate.
- No ZIP post-verify + manifest.
- Absolute path rejection incomplete for intake.

## Unsafe packaging paths
- package-fixable can create ZIP without structural/preflight gates.
- Multiple roots silently select highest marker score.

## Tests preserving incorrect behavior
- config_test_branch_aware.py packages Fixable without ready_to_package/preflight (will need update).

## Documentation mismatches
- automation/README.md documents only intake/status/package/archive.
- Expert Reference still oversized with full templates.
