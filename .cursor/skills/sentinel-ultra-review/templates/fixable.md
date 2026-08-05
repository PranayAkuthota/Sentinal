# Submission material — FIXABLE

Fill every field. The platform asks the analysis question **twice** — **give the same answer
both times.**

---

## Section 2 · Task Analysis

**What is your analysis of the Sentinel task you downloaded above?**
→ **Fixable** — the task has issues in the instructions, tests, and/or oracle, but I corrected
all issues.

### Where did the task have issues? (check all that apply)

- [ ] Instructions
- [ ] Tests
- [ ] Oracle Solution
- [ ] Environment / Dockerfile

### What issues did you find? (check all that apply)

- [ ] Every requirement in the instructions is not properly tested
- [ ] All test requirements are not properly specified in the instructions
- [ ] The instructions appear LLM generated
- [ ] The instructions are overly-prescriptive
- [ ] The task leaks solution information
- [ ] The oracle does not implement the solution following the instructions
- [ ] Less than 10 fail-to-pass tests in the test suite

---

## Describe each issue in detail

**Use exactly this format** (one numbered block per issue category selected above). Include
code examples where helpful — vague descriptions get sent back.

```
1) [Issue Category] — describe the specific issue with code examples where helpful
— Is this issue fixable or not fixable?
— If fixable, how? If not, why not?
2) [Issue Category 2]...
```

### Worked shape to follow

> **1) [Tests — coverage] — `tests/tests.patch` never enforces the retry-budget requirement.**
> The instruction states *"a request must not be retried more than three times"*, but the only
> retry assertion is `assert result.ok`, which passes for any retry count. A stub that retries
> forever still passes the suite.
> — **Fixable.**
> — **How:** added `test_retry_budget_exhausted` and `test_retry_budget_boundary` to
> `tests/tests.patch` asserting the transport records exactly 3 attempts and raises
> `RetryBudgetExceeded` on the 4th; registered both ids in `config.json` `grading.fail_to_pass`.
> Verified a stub implementation now fails both.

> **2) [Instructions — overly prescriptive] — instruction names the grading fixture.**
> `instruction.md:14` reads *"the test `test_resume_on_mirror_switch` uses `/yum/partial` and
> `/yum/range_only` to verify resume behavior"*, which exposes verifier internals and removes
> the need to explore the code.
> — **Fixable.**
> — **How:** rewrote to describe behavior only: *"When a resumed download fails after writing a
> valid partial file, retrying against another mirror should preserve the partial data and
> request only the remaining bytes."* Re-copied the instruction into
> `environment/problem_statement.md`.

*(Repeat for every issue. Every issue you list must be one that a reviewer can confirm by
reading the same files.)*

---

## Files Changed

List **every** file you changed.

| File path | What changed | Why |
|---|---|---|
| `instruction.md` | | |
| `environment/problem_statement.md` | Re-copied to match `instruction.md` byte-for-byte | Guidelines require the two be identical |
| `tests/tests.patch` | | |
| `tests/config.json` | | |
| `solution/golden.patch` | | |
| `environment/Dockerfile` | | |
| `task.toml` | | |

---

## PR expansion

**If you added to the PR in any way, explain how. If you did not modify the PR in any way,
write "NA".**

→ [`NA` **or** describe the addition and why it is an addition rather than a change: what the
original PR does, what you added on top, and how the task still clearly maps back to the source
PR. Remember: you may not change or reduce PR scope, only expand it.]

---

## Required confirmations for the corrected task (you must select ALL)

- [ ] Every requirement in the instructions is properly tested
- [ ] All test requirements are properly specified in the instructions
- [ ] The instructions do not sound like an LLM generated them
- [ ] The instructions are not overly-prescriptive
- [ ] The task does not leak solution information
- [ ] The oracle implements the solution following the instructions
- [ ] The PR was not modified in any way beyond what is allowed by the guidelines
- [ ] More than 10 fail-to-pass tests in the test suite

---

## Post-fix verification (proof the task is now clean)

**Mechanical**

```
check_task.py       → 0 NOT_FIXABLE, 0 FIXABLE findings
git_hygiene.sh      → 9/9 clean
stray-artifact sweep→ empty
problem_statement.md == instruction.md → identical
```

**Tests**

- `fail_to_pass` count: **[N]** (≥ 10, ideally 10–20)
- Regression test reproducing the original failure: [`test id`]
- Coverage map complete: every requirement → ≥1 enforcing assertion ✓
- Faithfulness map complete: every assertion → stated/implied requirement ✓
- None of the six auto-REMOVE patterns present ✓
- No pre-existing test file modified ✓
- `git apply --check tests/tests.patch` at base commit → clean ✓

**Runtime** *(recommended for Fixable — saves an eval round-trip)*

```
docker build environment/     → [SUCCESS]
Oracle run                    → reward [1.0]
NOP run                       → reward [0.0]
```

**Bundle**

```
cd <task-root> && zip -rX ../<task>.zip . -x '*.DS_Store' '__MACOSX/*'
unzip -l <task>.zip | grep 'refs/'   → [entries present]
```
Unpacks directly to `instruction.md`, `task.toml`, `environment/`, `solution/`, `tests/`.
No `runs/`, no wrapping `task/` folder.

---

## Re-upload

Re-upload the entire corrected task as a **single zip**, submitted as `<all-task-content>`.
Do **not** include `runs/` or the `task/` directory itself.

After upload, run evals and iterate immediately — keep re-running and fixing until the checks
pass and the task is error-free, **then** come back and fill in the rest of the form. Run with
*Send to reviewer* **unchecked** until Difficulty, Oracle, and Quality checks are all passing.

---

## What makes this task difficult?

[Describe what makes the task technically challenging — edge cases, implementation
dependencies, requirements that may be overlooked on first reading, complexity in the test
setup. Good difficulty comes from the problem itself, not from vagueness or stapled-on
unrelated changes.]

---

## Comments for Reviewer

[Assumptions you made, edge cases you considered, reasons you didn't change a file, parts that
may warrant reviewer judgement. If you diverged from the canonical upstream fix in the oracle,
document why here. The reviewer must read and acknowledge this field.]

---

## Timing

- How long did it take you to complete the **initial task rewrite only**? → [N] minutes
- How much time would a senior engineer familiar with the codebase take to solve this?
  → [ <10 min · 10–20 min · 20–40 min · 40+ min ]
- How long did it take you to review the initial task and determine its validity? → [N] minutes
- How long did it take you to complete this **entire submission**? → [N] minutes
  *(if the task is sent back for revision, adjust to include the additional time)*
