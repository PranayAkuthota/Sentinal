# Submission material — VALID AS-IS

Fill every field. Delete the bracketed guidance as you go. The platform asks the analysis
question **twice** and both are required — **give the same answer both times.**

---

## Section 2 · Task Analysis

**What is your analysis of the Sentinel task you downloaded above?**
→ **Valid as-is** — the task is valid without changes.

### Required confirmations (you must check EVERY item)

- [ ] Every requirement in the instructions is properly tested
- [ ] All test requirements are properly specified in the instructions
- [ ] The instructions do not sound like an LLM generated them
- [ ] The instructions are not overly-prescriptive
- [ ] The task does not leak solution information
- [ ] The oracle implements the solution following the instructions
- [ ] Contains more than 10 fail-to-pass tests in the test suite

> You may only tick these if you verified each one by reading. Below is the evidence that
> backs each tick — write it, because the reviewer repeats your review and will flag anything
> you asserted without support.

---

## Evidence (write this out — it is what makes the submission accepted)

**1. Coverage — every instruction requirement is tested.**

| # | Requirement (quoted from instruction.md) | Enforcing test id(s) |
|---|---|---|
| R1 | [quote] | [`tests/…::test_…`] |
| R2 | | |

[Confirm: a stub implementation would fail at least one test per requirement.]

**2. Faithfulness — every assertion traces back to the instruction.**

| Test id | Asserts | Traces to | Name derivable via |
|---|---|---|---|
| | | R# | base codebase / language convention / stated in instruction |

[State explicitly: no assertion grades behavior the instruction never asked for; no expected
name, string, path, or format is non-derivable.]

**3. Instruction reads as a real engineering ask.**
Persona: [Casual/Slack-like · Structured ticket · Technical memo · Prose/email · Acceptance
criteria]. [One or two sentences on why it reads authentic and consistent — no robotic
phrasing, no template scaffolding.]

**4. Not overly prescriptive.**
[Confirm absent: "Where to look" file lists, named hidden tests/fixtures/harness files,
verifier-internals explanations, named internal functions to edit, root-cause hand-holding,
copied assertion strings. Note any output format the instruction states — that's required,
not leakage.]

**5. No leakage.**
[Confirm: no PR URL/title/number/commit SHA in instruction.md or problem_statement.md; no
environment spoilers in commit messages/comments/docs; no test-gaming shortcut;
`git rev-list --all --not HEAD` empty; no solution material on agent-readable paths.]

**6. Oracle implements the instruction.**
`solution/golden.patch`: [N] lines across [M] files. [How it maps to the instruction's
requirements, and that it corresponds to the canonical fix from the source PR.]

**7. Fail-to-pass count.**
`config.json` `grading.fail_to_pass` = **[N] tests** (≥ 10). Regression test that reproduces
the original failure: [`test id`]. `pass_to_pass` = [M] tests.

**8. Metadata and packaging.**
[`task.toml`: cpus/memory/storage/gpus/timeouts within limits; `network_mode` correct in all
three blocks; `source` URL matches the PR the task derives from; `category` and
`difficulty_explanation` accurate. Bundle: no stray artifacts; `problem_statement.md` identical
to `instruction.md`; `golden.patch` correctly named.]

---

## Required local runs

**Valid as-is tasks are NOT re-run by the platform's difficulty evals — your local run is the
only check on them.** Do not submit this verdict without them.

```
docker build environment/     → [SUCCESS / paste failure]
Oracle run (solve.sh + tests) → reward [1.0]
NOP run   (tests, unsolved)   → reward [0.0]   (all f2p fail, all p2p pass)
```

---

## What makes this task difficult?

[Describe what makes the task technically challenging — edge cases, implementation
dependencies, requirements that may be overlooked on first reading, complexity in the test
setup. Good difficulty = the problem itself: complex debugging, root-cause analysis, a
substantial feature, hard domain/security work. Be specific; this is read by the reviewer.]

---

## Comments for Reviewer

[Flag anything that helps the reviewer understand the task and your decisions: assumptions you
made, edge cases you considered, reasons you didn't change a file, parts of the task that may
warrant reviewer judgement or a second opinion. The reviewer is required to read this field and
acknowledge whether it changed their decision — so use it.]

---

## Timing

- How much time would a senior engineer familiar with the codebase take to solve this?
  → [ <10 min · 10–20 min · 20–40 min · 40+ min ]
- How long did it take you to review the initial task and determine its validity? → [N] minutes
- How long did it take you to complete this entire submission? → [N] minutes
