# Proposal — Agent Judge overreach + ≥3.5 axis bar (promoted as P-011)

**Date:** 2026-08-04  
**Status:** promoted → `knowledge/patterns/P-011_…`  
**Trigger:** Platform marker `Blocked at the agentic judge…` with verdict `discuss (overreach)`; Difficulty not run after Agent Judge–first eval order.

## Decision

- Revisions must clear **Agent Judge first**, with operational bar **every axis ≥ 3.5**.
- Overreach → Tests→Instruction map; remove/ungrade **or** state observable public contract; never implementation spoilers.
- Coverage-only chases without instruction sync flip the next Judge to overreach.
- Difficulty (4 trials/model, ≤50% worse-model bar) only after Judge is green.

## Wired into

- `Review_Guidelines.mdc` (Quality Check + Platform Evaluations)
- `docs/SUBMITTER_BLOCKERS.md` (16b/c, 30d/e)
- Operational Patterns §8a/8b
- `Prompts/Submitter_Platform_Revision.md`, Execution 03/05
- `sentinel-submitter` skill, `templates/fixable_checklist.md`
- Strengthened `P-010`
