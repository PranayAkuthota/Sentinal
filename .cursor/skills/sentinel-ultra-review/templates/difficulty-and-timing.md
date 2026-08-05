# Difficulty write-up and timing fields

Asked for **Valid as-is** and **Fixable** tasks (not for Not Fixable).

---

## What makes this task difficult?

> "Describe what makes the task technically challenging — edge cases, implementation
> dependencies, requirements that may be overlooked on first reading, or complexity in the
> test setup."

Write 3–6 sentences covering whichever of these actually apply. Be concrete and cite the task.

- **The core reasoning demand** — what has to be understood before anything can be written
  (a subtle invariant, an interaction between two subsystems, a protocol/spec detail).
- **Discovery cost** — what the agent must find on its own because the instruction
  deliberately doesn't say it (which module owns the behavior, where state is threaded).
- **Edge cases the requirements imply but don't spell out** — boundaries, empty/degenerate
  inputs, concurrency, ordering, encoding.
- **Implementation dependencies** — changes that must land in more than one place to be
  coherent; the ~100+ lines across 2+ files.
- **Requirements easy to miss on first reading** — the ones a fast reader drops and then fails
  a test on.
- **Test-setup complexity** — fixtures, service doubles, timing/determinism constraints.

### Good vs bad difficulty (the reviewer applies this)

✅ **Good** — complex debugging, root-cause analysis, a substantial feature, hard domain or
security work. Difficulty that comes from **the problem itself**.

❌ **Bad** — vague or underspecified requirements; unrelated changes stapled together. Those
make a task *confusing*, not *difficult*, and a reviewer will flag them.

If you raised difficulty during a rewrite, say **how**: trimmed over-prescription (preferred
first move), or expanded PR scope (state what you added and that it builds on the PR).

### Context on the difficulty bar

- By the time a task reaches you it has **already passed the difficulty checks** — you don't
  judge difficulty from scratch.
- But **fixing other issues can pull difficulty back below the benchmark**; when that happens
  the platform's evals send it back to you to raise it again.
- Benchmark: worse-performing model must have a pass rate of **50% or lower**. Difficulty
  now runs **4 trials per model** (was 8 as of Aug 4 2026). Older Medium ≤4/8 / Hard ≤2/8
  examples are the same rate bar under the prior 8-trial schedule.
- Agent Judge (Quality Check) runs **before** Difficulty; Difficulty is skipped while Judge fails.
- Difficulty evals do **not** re-run on tasks marked Valid as-is.

---

## Timing fields

| Field | Applies to | Your answer |
|---|---|---|
| How long did it take you to complete the **initial task rewrite only**? (minutes) | Fixable | |
| How much time would a **senior engineer familiar with the codebase** take to solve this? | Valid as-is, Fixable | `<10 min` / `10–20 min` / `20–40 min` / `40+ min` |
| How long did it take you to **review the initial task and determine its validity**? (minutes) | all paths | |
| How long did it take you to complete **this entire submission**? (minutes) | all paths | |

> If the task is sent back for revision, **adjust the total-submission number** to include the
> additional time.

Sanity check on the senior-engineer estimate: an authentic task is roughly 100+ lines across
2+ files and requires genuine exploration — an answer of `<10 minutes` is in tension with the
authenticity bar. If you genuinely believe it's under 10 minutes, that is itself evidence the
task is too easy → see `fix-playbooks.md` F13.
