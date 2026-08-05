# Glossary

Source: Sentinel Ultra Glossary.

## Roles & workflow

| Term | Meaning |
|---|---|
| **EC (Expert Contributor)** | You — the person reviewing, fixing, and validating tasks. |
| **Submitter** | The EC who reviews a task, decides its verdict, and fixes it if needed. |
| **Reviewer** | A second EC who independently verifies the submitter's work. |
| **Adjudicator** | A final reviewer who resolves disagreements between submitter and reviewer. |
| **Source PR / commit / issue** | The real upstream change a task is derived from and anchored to. **Every task comes from a real source — there are no net-new tasks.** |
| **PR scope** | What the task is fundamentally about. You may expand it to add difficulty, but never reduce or replace it. |

**Task lifecycle:** Authoring → **Submission** (an EC reviews, decides validity, fixes) →
**Review** (a second EC independently verifies) → **Adjudication** (resolves disagreements) →
**Delivery**.

## Task anatomy

| Term | Meaning |
|---|---|
| **Harbor** | The framework/format every task is built in. |
| **Task** | A single software-engineering problem in Harbor format: instruction, environment, solution, tests. |
| **`instruction.md`** | The problem statement the agent receives — what to do and how success is measured. |
| **`problem_statement.md`** | A restatement of the instruction placed inside the environment. Must be an exact copy. |
| **`task.toml`** | Task metadata: pinned image URI, resource budget, timeouts, source, difficulty fields. |
| **Environment** | The container the task runs in — the Dockerfile plus `repo/` (the cloned base repository). |
| **`runs/`** | Logs of past agent attempts, delivered alongside the task as reference. Never included in your re-upload. |

## Solution (oracle)

| Term | Meaning |
|---|---|
| **Oracle** (a.k.a. golden solution, reference solution) | The known-correct solution that proves the task is solvable. |
| **`solve.sh`** | Script that applies the golden patch to bring the repo to the solved state. |
| **`golden.patch`** (a.k.a. gold patch; formerly `init_state.patch`) | The self-contained patch containing all of the solution's changes. **If a task ships `solution.patch`, rename it to `golden.patch`** — that was a short-lived draft name. |

## Tests & grading

| Term | Meaning |
|---|---|
| **Fail-to-pass (f2p) tests** | Tests that fail on the unsolved repo and pass after the fix — the core behavioral checks. **At least 10 required.** They live in `tests.patch`. |
| **Pass-to-pass (p2p) tests** | Tests that must pass both before and after the fix; a regression guard. |
| **`tests.patch`** | The patch containing the fail-to-pass tests. |
| **`config.json`** | Declares how the suite runs and which test ids are f2p vs p2p. |
| **`test.sh`** | Runs the suite and writes the reward. |
| **Verifier** | The component that runs the tests and computes the reward. Runs airgapped. |
| **Reward** | The pass/fail signal: **1.0 only if every fail-to-pass test passes and no pass-to-pass test regresses.** |

## Quality & difficulty

| Term | Meaning |
|---|---|
| **Agent** | The model or coding agent attempting the task. |
| **Reward hacking** | Passing the tests without doing the intended engineering work (editing the tests, hardcoding outputs). **Preventing this is a central goal.** |
| **Difficulty bar / pass@k** | Rate threshold a task must clear — worse model **≤50%** pass rate. As of Aug 4 2026: **4 trials per model** (was 8). Older Medium ≤4/8 / Hard ≤2/8 examples are the prior 8-trial schedule. Difficulty runs only after Agent Judge passes. |
| **Outcome-based test** | A test that checks observable behavior by running code, not by inspecting diffs, file names, or source keywords. |

## What Sentinel Ultra is

Snorkel AI's initiative to build a high-quality dataset of Harbor-format software-engineering
tasks, drawn from real open-source pull requests, commits, and issues — used to train and
evaluate frontier coding agents and models on realistic engineering work.

> Because of that purpose, **the thing that matters most is that every task is correct,
> complete, and impossible to game** — no errors, no gaps in coverage, and no way for an agent
> to pass without doing the real engineering work. Difficulty matters too, but the platform's
> evals help confirm a task clears the difficulty bar; **your focus is on the errors and gaps
> that automated checks can't catch.**
