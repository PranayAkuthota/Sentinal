# The four core principles

Source: Sentinel Ultra Guidelines § "The four core principles".

Apply these to every task — together they determine the verdict. Two of them —
Clarity & No Leakage and Verifiability — are two sides of the same goal: **making a task
impossible to reward-hack**, so an agent has to do the real engineering work to pass.

| # | Principle | What to check |
|---|---|---|
| 1 | Solvability | A competent engineer can solve it from the instruction alone, within limits. |
| 2 | Clarity & No Leakage | Describes the problem and behavior — not the implementation — and reveals nothing exploitable. |
| 3 | Verifiability | A sound, comprehensive, outcome-based test suite that can't be gamed. |
| 4 | Authenticity | A realistic, substantial engineering task that reads like real communication and matches the PR. |

---

## 1 — Solvability

A task is valid only if a competent engineer can solve it from the instruction alone —
within the task's time and resource limits, and **without guessing arbitrary implementation
choices**.

- **No arbitrary guesswork.** Every choice the tests require is stated or reasonably implied.
- **No unsupported claims.** The instruction must only reference behaviors, APIs, files, or
  repo structure that **actually exist in the pinned repository**. If it describes something
  that isn't there, the task isn't solvable as written.

**How to check:** for every noun the instruction names — a file, a class, a function, a
config key, an endpoint — grep `environment/repo/` at the base commit and confirm it exists.
A single fabricated reference breaks solvability.

---

## 2 — Clarity & No Leakage

The instruction should give an engineer enough to solve the task **without telling them how
to implement it** and **without revealing the answer**. Two failure modes: over-prescription
and leakage. Together they are how most reward-hacking sneaks in.

### Signs an instruction is overly prescriptive

- Says "Where to look:" followed by a list of the relevant files.
- Names the exact hidden test, fixture, mock endpoint, cassette, or harness file used to
  grade the task.
- Explains how the verifier proves success instead of describing user- or API-visible behavior.
- Identifies exact internal functions, branches, comprehensions, or callbacks to edit when a
  behavioral description would do.
- Provides root-cause analysis that removes the need to inspect the code.
- Says "the tests reference this name" or "this file validates the fix."
- Copies exact assertion strings, state paths, or fixture values from tests — unless they're
  a genuine public/API contract.

### Rewrite examples (Guidelines § "Instructions — editable")

| ❌ Overly prescriptive | ✅ Preferred |
|---|---|
| "The test `test_download_packages_resume_on_mirror_switch` uses `/yum/partial` and `/yum/range_only` to verify resume behavior." | "When a resumed download fails after writing a valid partial file, retrying against another mirror should preserve the partial data and request only the remaining bytes." |
| "Fix the `range()` call inside the list comprehension that creates `schemas.SlotBase`." | "Generated slots must never extend past the schedule's availability end time." |
| "The hook should expose `handleScrollContainerWheel` because the tests reference this name." | "The hook should expose a stable wheel handler for the scroll container." |

### Document required output formats — this is NOT leakage

If the task requires a specific output format, schema, or API response shape, **state that
format in the instruction** (or in a clearly referenced file in the environment). Describing
the expected shape is *necessary* and is not leakage — leaving it to guesswork is what
breaks solvability. Detailed output schemas and conventions score *well* on the judge's
clarity axis.

### No leakage — what to check

- **PR leakage:** PR URLs, titles, numbers, or commit SHAs in the instruction that let an
  agent scrape the fix.
- **Environment spoilers:** commit messages, comments, or docs in the base repo / Docker
  setup that describe the exact change.
- **Test-modification gaming:** loose test constraints that can be satisfied by editing the
  test files instead of the implementation.

**Balancing context is the crux of this work:** a task needs enough context to be solvable,
but not so much that it becomes instructional.

---

## 3 — Verifiability

Tests are the ground truth for a task. They must comprehensively and fairly verify the
required behavior, and be impossible to game. See `test-quality.md` for the full treatment —
this is the only axis that *blocks* submission.

### Test ↔ instruction alignment — check BOTH directions

| Direction | Requirement |
|---|---|
| Instruction → Tests | Every required behavior is tested. |
| Tests → Instruction | Every assertion maps to something stated or reasonably implied. |
| No hidden checks | Tests don't grade behavior the instruction never asked for. |

Tests likely need a rewrite when they: enforce undescribed behavior, require non-derivable
names/paths/formats, over-constrain implementation, depend on verifier internals or hidden
fixtures, can be passed by editing the tests, or miss / partially cover major requirements.

### At least 10 fail-to-pass tests

Every task must ship with **at least 10 fail-to-pass tests** — the single most important
guard against reward hacking and the main way to ensure sufficient behavioral coverage. If
the task arrives with fewer than 10, mark it **Fixable** and add tests during your rewrite to
reach at least 10 — **ideally 10–20**. Added tests must cover requirements stated or
reasonably implied in the instruction (**never undescribed behavior**).

### Outcome-based tests

Tests must verify observable behavior by **running code and checking results** — invoking the
corrected API, querying a service, inspecting runtime output. They must **not** grade by patch
structure, diff format, line numbers, file names, or source-code keyword matching, and must
not be satisfiable by hardcoding or special-casing expected values.

### Regression test required

The suite must include at least one test that **directly reproduces the failure described in
the issue** — it fails on the pre-patch repo and passes after the fix.

### Deterministic and fast

Deterministic inputs, seeds, and assertions. No flaky or order-dependent behavior. Must
finish within the configured timeout. Scope long suites to the relevant subset.

### Independent of the oracle

Tests must not import or call the golden solution, compare against files created only by the
solution, or otherwise depend on solution-side artifacts. Any fixtures or mock data must be
**committed into the verifier image** so the agent cannot tamper with them.

### The arbitrary naming problem

A common alignment failure: tests expect a specific name the instruction never gave — a
function/method/class name, exact error string, output format (JSON keys, log format), new
module/file name, or CLI flag / config key.

A name is **derivable** (and therefore acceptable) only if it:

1. already exists in the base codebase being modified (e.g. an existing `parse_date()`), **or**
2. follows a standard language/framework convention (e.g. Python `str`, standard REST
   resource names), **or**
3. is explicitly stated in the instruction.

> Example — Invalid but Fixable: instruction says "Add a feature to validate emails," but the
> test asserts `validate_email_address(email) == True`. The instruction never specified that
> name → add it in your rewrite.

**To catch it:** list the names/formats the instruction explicitly specifies → scan the tests
for expected names → flag any that aren't derivable.

---

## 4 — Authenticity

A valid task looks like real engineering work and reads like real engineering communication.

### Substantial and agentic

Must require genuine code exploration, multi-step reasoning, and real changes — not a
one-line edit or a zero-shot generation. **Rule of thumb: the underlying fix is roughly 100+
lines across two or more files.** A task solvable by a trivial edit, or a contrived puzzle
with no real-world analogue, is not authentic.

### Reads like a real engineering ask

A good instruction matches **one** natural persona:

- **Casual/Slack-like** — direct, assumes domain knowledge.
- **Structured ticket** — Summary / Steps to Reproduce / Expected Behavior.
- **Technical memo** — professional refactor/logic context.
- **Prose/email** — a peer or tech lead explaining context and impact.
- **Acceptance criteria** — bulleted "when X, the system should Y."

**Red flags:** robotic phrasing ("The system shall…", "It is required that…"), tone that
mismatches the persona, structure identical across many tasks, or writing that reads like
code documentation rather than a task assignment.

### PR ↔ instruction alignment

The instruction must ask for the **same change as the PR** (bug X → describes bug X;
feature Y → requests feature Y). If you expanded scope, it should still be the original PR
**plus** your additions — not a different task.

---

## Task difficulty (Guidelines § "PR Scope and Task Difficulty")

Sentinel tasks train and evaluate frontier coding agents, so they have to be genuinely hard —
an easy task gives no useful signal. **By the time a task reaches you it has already passed
our difficulty checks**, so you don't need to judge difficulty from scratch. (That's also why
difficulty evals don't re-run on tasks you mark Valid as-is.)

But clearing the bar doesn't mean the task is free of other issues — and **fixing those issues
can pull difficulty back below the benchmark.** When that happens, the platform's evals send
the task back to you to raise it again.

### Troubleshooting difficulty, in order

1. **Check for over-prescriptive instructions first.** Often an instruction hands the agent
   context it should have discovered itself — the files to touch, the root cause, or a
   step-by-step approach. Remove anything the agent could reasonably find by exploring the
   codebase (those are also leakage), and describe the behavior you expect instead of the how.
2. **If trimming isn't enough, expand the PR scope.** When the source PR simply isn't complex
   enough, add to its scope (see PR scope rules in `verdict-rubric.md`).
3. **Keep any added difficulty real.** Good difficulty comes from the problem itself — complex
   debugging, root-cause analysis, a substantial feature, hard domain/security work. It must
   **not** come from vague or underspecified requirements, or from stapling unrelated changes
   together; those make a task confusing, not difficult, and a reviewer will flag them.

Difficulty bar (Glossary): worse-performing model must have a pass rate of **50% or lower**.
As of August 4, 2026 Difficulty runs **4 trials per model** (was 8). Older Medium ≤4/8 /
Hard ≤2/8 examples match that rate bar under the prior 8-trial schedule. Agent Judge runs
before Difficulty; Difficulty is not run while Judge fails.

---

## What you can edit, and what you can't

| Component | Rule |
|---|---|
| ✅ `instruction.md` | Editable. Rewrite over-prescriptive instructions to mirror real-world engineering tasks — expected behavior, constraints, observable outcomes, while still requiring standard codebase investigation. |
| ✅ Tests (`tests.patch`, `test.sh`, `config.json`) | Editable. Map 1:1 with instruction requirements; ≥10 f2p; keep flexible enough for multiple valid implementations; no arbitrary names/strings/paths/formats; validate observable behavior. |
| ✅ Solution / oracle (`solve.sh`, `golden.patch`) | Editable **in two cases only**: (1) to correct an oracle that does not implement the instruction, or (2) to expand PR scope to increase difficulty. |
| ⚠️ Environment (`Dockerfile`, `problem_statement.md`) | **Limited** fixes only — see `environment-and-git.md`. |
| ✅ Git metadata in `environment/repo/.git` | Fixable — see `environment-and-git.md`. |
| ❌ Tracked source files in `environment/repo/` | **Never edit.** The task is anchored to the real base repository; changing its code breaks that grounding and is not allowed. |
| ❌ Pre-existing / p2p test files | **Never modify.** The harness byte-compares them to the base commit. Add new functions or new files through `tests/tests.patch` instead. |
| ❌ PR scope | Never reduce or replace. Adding is allowed. |

### When you edit the oracle

- **Match the canonical fix.** The solution should correspond to the actual fix from the
  source PR — not an alternative you invented. Only diverge if the upstream fix is genuinely
  unavailable or unsuitable, and **document why**.
- **No unnecessary changes.** Only what's needed to resolve the task. No unrelated refactors,
  style cleanups, or drive-by edits.
- The expanded oracle must still resemble the source PR (anchor preserved, with additions).
- **Update instruction and tests in lockstep** so the trio stays internally consistent, and
  the instruction reads as one realistic ask, not a tacked-on list.
- If you expanded scope, **re-run the difficulty eval** to confirm the task clears the bar.
- If a fix would require reducing or replacing the PR's behavior → **Not Fixable**.

> Note (Harbor Framework): task solutions may be **larger** than strictly necessary or include
> extra functionality not asked for in the instruction. **That is okay** as long as the
> solution does what the instruction requires and the tests enforce that. The point of the
> oracle is to show the task is solvable.
