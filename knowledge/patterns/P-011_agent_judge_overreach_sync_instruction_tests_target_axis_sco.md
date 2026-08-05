# P-011: Agent Judge overreach: sync instruction↔tests; target axis scores ≥3.5 before Difficulty

**Status:** approved  
**Promoted:** 2026-08-04  
**Reusable:** yes

## Pattern

After the Aug 4 2026 eval-order change, **Agent Judge runs before Difficulty**. A failing Judge (including `discuss (overreach)`) returns immediately and Difficulty is **not** run.

Operational submitter bar for revisions: drive **every Agent Judge axis to ≥ 3.5** (policy already: do not ship a **3 with reservations** on blocking axes). Blocking axes remain **test_coverage** and **test_faithfulness**. Overreach is almost always a faithfulness failure.

## Overreach playbook (discuss / overreach)

For each graded assertion (and, with `allow_extra_failures: false`, every executed assert that can zero reward):

1. **Stated or reasonably implied** in `instruction.md`? Keep.
2. **Public/API contract** derivable from existing codebase symbols the instruction already points at? Keep; optionally name the public surface once (not a file walkthrough).
3. **Otherwise** → overreach. Fix by **one** of:
   - Soften/remove the assertion (or drop it from graded `fail_to_pass` / `pass_to_pass` while keeping true regressions ungated if policy allows), **or**
   - Add the missing **observable** requirement to the instruction (behavior/schema/errors — not “edit file X / function Y”).
4. Never “fix” overreach by dumping implementation spoilers (PR URLs, hidden test names, exact internal helpers) into the instruction.
5. Common overreach sources seen in Ultra revisions:
   - Graded `pass_to_pass` suites unrelated to the task contract (ungrade / keep as run-only regression).
   - Helper/unit tests for private names after the instruction was de-prescribed.
   - Exact strings, paths, CLI flags, thresholds asserted in tests but never stated.
   - Coverage chase that adds asserts for internals not in the instruction → faithfulness crash.

## Coverage chase trap

Fixing `coverage_gap` by adding tests **without** updating the instruction (or by naming only private helpers) often flips the next Judge run to **overreach**. Always move instruction ↔ tests ↔ oracle together.

## Difficulty

Do not invent Difficulty results when the platform says Judge blocked the screen. After Judge axes are ≥3.5 / pass, Difficulty uses **4 trials/model**; worse model must still be **≤50%** pass rate.

## When it applies

Every platform revision after Aug 4 2026 Agent Judge–first flow; any discuss/overreach or faithfulness/coverage score below 3.5

## What to do

Map every graded assertion to a stated/implied instruction contract; remove or ungrade overreaching asserts OR state the public contract; keep instruction↔tests↔oracle synced; re-upload Judge-only until axes ≥3.5; only then interpret Difficulty

## Do not promote into agent-facing instructions

Task UUIDs, golden patches, hidden tests, or PR spoilers.
