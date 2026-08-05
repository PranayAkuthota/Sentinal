---
name: sentinel-reviewer
description: >-
  Independent Sentinel Ultra reviewer workflow. Read-only on the submission;
  no corrected ZIP. Use when the user acts as reviewer.
---

# Sentinel Reviewer Skill

## Preconditions — stop if any fail

1. User is in **reviewer** mode (not submitter packaging).
2. Submission materials + submitter answers available.
3. Do **not** use Execution **05/06** packaging path to “fix” the task for the submitter.

## Procedure

1. Follow `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc`.
2. Independently verify instruction, tests, oracle, env, source, metadata, runs, and corrected bundle if any.
3. Read Comments for Reviewer / rebuttal before finishing; acknowledge impact.
4. Outcomes only: **Accept** / **Needs Revision** / **Reject** (+ Submission Quality Score 1–5).
5. Reject only after max revision cycles exhausted.
6. Optional local checks only in disposable copies — never mutate the submission under review.

## Outputs

- Copy structure from `templates/reviewer_answer.txt`.
- Write reviewer answer artifact (e.g. `review_answer.txt` in the review workspace).
- No corrected task ZIP from the reviewer role.
- Optional read-only aggregate (framework ops only): `python3 automation/aggregate_workflow_states.py`

## Hard rules

1. Do not mix submitter verdict labels (Valid as-is / Fixable / Invalid) as reviewer outcomes.  
2. Do not rubber-stamp the submitter’s conclusion.  
3. Cite concrete files, tests, logs, and paths.  
