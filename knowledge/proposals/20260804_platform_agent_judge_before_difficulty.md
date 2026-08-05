# Proposal — Platform feed: Agent Judge before Difficulty

**Date:** 2026-08-04  
**Source:** Official Sentinel Ultra Discord/announcement (user-fed)  
**Status:** promoted immediately (authoritative platform update)

## Summary

Agent Judge (Quality Check) now runs before Difficulty. Failing Judge skips Difficulty. Difficulty uses 4 trials/model; ≤50% worse-model bar unchanged.

## Promoted artifacts

- Pattern: `knowledge/patterns/P-010_agent_judge_before_difficulty.md`
- Failure: `knowledge/failures/F-010_waited_for_difficulty_while_agent_judge_blocked_the_screen.json`
- Policy: `.cursor/rules/Review_Guidelines.mdc` → Platform Evaluations
- Ops: `Sentinel_Submitter_Operational_Patterns.mdc` §8a
- Revision: `Prompts/Submitter_Platform_Revision.md`
- Docs: `document 2.txt`, `document 3.txt`, blockers, ultra-review refs, EC quick reference

## Operator takeaway for revisions

If you see `Blocked at the agentic judge. Not run: difficulty screen…`, fix Judge axes only and re-upload. Do not wait for Difficulty logs.
