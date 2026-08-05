# Learning proposal (pending human review)

- Generated: 20260802_053706 UTC
- Task ref: `004e50af-c9fc-4e84-b735-7f893aedb8cd_submission` (do not promote UUID into pattern titles)
- Branch recorded: Fixable
- Structural f2p count: 16

## Candidate reusable patterns

List only items likely to help **future** Sentinel tasks. Delete anything task-specific.

1. (edit) …
2. (edit) …

## Automation opportunities (deterministic only)

- …

## Suggested failure catalog entries

- category: …
  symptom: …
  recovery: …

## Agent notes (redacted)

_none_

## Workflow state warnings (structural)

```
[
  "grading.allow_extra_failures=true \u2014 only fail_to_pass/required_pass gate reward; ungraded tests in tests.patch can fail while reward stays 1.0 (expert coverage review required)"
]
```

## Extracted snippets (redacted, truncated)


## From findings_and_changes.md
# Findings and changes

## Original defects
1. Instruction over-prescriptive / claimed untested import-shadowing, typedef-import skip, NaN round-trip.
2. tests.patch leaked PR/JIRA ids; SkipTest on missing build tools.
3. network_mode / allowed_hosts in task.toml; verifier timeout 300s tight for cmake build.
4. Missing sibling grade.py; dirty git modes + reflog.

## Changes
See platform_answers Files Changed. golden.patch and f2p/p2p id lists unchanged (16/3).


## From submitter_audit.md
# Submitter audit — <task-id>_submission

## Verdict
- Public: Fixable
- Internal: Fixable
- Duplicate: Fixable

## Source
apache/thrift#3478 — Haxe codegen keyword escape, type-name disambiguation, bool/double/binary map-set helpers. Base SHA matches HEAD. golden.patch matches PR file set (+851/-89).

## Fixes applied (working_copy)
Instruction rewrite; problem_statement sync; task.toml network strip + verifier timeout 1800; tests.patch docstring/SkipTest; grade.py extract; git hygiene.

## Validation
Oracle 1.0 / NOP 0.0 / docker build passed. Packaged to work/task ready_to_submit/.


## From validation_summary.md
# Validation summary

| Check | Status | Reward | Evidence |
|-------|--------|--------|----------|
| docker_build | passed | — | session/validation_logs/docker_build.log |
| oracle | passed | 1.0 | session/validation_logs/oracle/reward.txt |
| nop | passed | 0.0 | session/validation_logs/nop/reward.txt |

validation_level: locally_validated  
preflight: ready_to_package=True  
ZIP: work/task ready_to_submit/<task-id>_submission__corrected.zip



---

**Promotion rule:** Human merges accepted items into `knowledge/patterns/` or `knowledge/failures/`.
Never auto-edit `.cursor/rules/Review_Guidelines.mdc`.
