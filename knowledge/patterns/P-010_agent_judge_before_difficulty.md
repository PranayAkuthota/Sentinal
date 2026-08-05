# P-010: Agent Judge runs before Difficulty (revise Judge first)

**Status:** approved  
**Promoted:** 2026-08-04  
**Reusable:** yes  
**Source:** Official Sentinel Ultra platform update (August 4, 2026)

## Pattern

Platform eval order is **Agent Judge (Quality Check) → Difficulty**. A failing Judge blocks Difficulty entirely. Difficulty trial count is **4 per model** (was 8); pass bar unchanged (worse model ≤50% pass rate).

## When it applies

Every platform revision / re-upload after Fixable packaging. Especially when feedback says:

`Blocked at the agentic judge. Not run: difficulty screen (cheap single-arm rollout).`

## What to do

1. Treat Agent Judge / Quality Check citations as the **only** actionable eval until they all pass.
2. Fix blocking axes first: **test_coverage** and **test_faithfulness** (also clear other Judge findings reviewers will see).
3. **Operational score bar:** revise until **every Agent Judge axis is ≥ 3.5**. Do not re-upload for Difficulty while any axis is below 3.5 or still “3 with reservations.” Overreach / `discuss (overreach)` → follow **P-011**.
4. Keep instruction ↔ tests ↔ oracle synchronized; do not add filler f2p. Coverage chase without instruction sync often flips the next run to overreach.
5. Re-upload with Send to Reviewer unchecked; iterate Judge until green (≥3.5 on all axes).
6. Only after Judge passes, interpret Difficulty (4 trials/model, ≤50% on worse model). Timeout gates and easy-task signals still apply then.
7. Do **not** assume Difficulty ran, invent difficulty stats, or delay Judge fixes waiting for difficulty logs that were never produced.

## Do not promote into agent-facing instructions

Task UUIDs, golden patches, hidden tests, or PR spoilers.
