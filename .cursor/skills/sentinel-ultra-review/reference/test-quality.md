# Test quality — the only axis that blocks submission

Source: Tasking Guide § "Quality Check — the agentic rubric-panel judge"; Guidelines §
"3 Verifiability".

## How the judge works

When you run evals, an automated rubric panel reviews your task the way a human reviewer
would. **Two independent LLM judges** (Claude Opus and GPT-5.5) each read your instruction,
tests, oracle solution, and task directory, and score the task against **four rubrics
(10 axes total, each 1–5)**. Where the two judges disagree by ≥ 2 points on an axis, a
**third blinded adjudicator** settles it. The Quality Check summary gives a per-axis report
with justifications citing specific files and lines — **read them; they tell you exactly what
to fix.**

This is a **blocking eval.** A failing verdict sends the task to `NEEDS_REVISION`, just like
a failing difficulty or oracle check.

### The 10 axes

| Rubric | Axes | What it reads |
|---|---|---|
| Instruction quality | realism, clarity, self-containedness, prescriptiveness | `instruction.md` + environment only |
| **Test quality** | **`test_coverage`, `test_faithfulness`** | instruction + every test file |
| Oracle quality | spec faithfulness, no gaming, robustness/reproducibility | instruction + `solution/` |
| Packaging | packaging | directory listing + `task.toml` + `Dockerfile` |

### What actually blocks

The pass/fail verdict is driven by **`test_coverage` and `test_faithfulness` only**. The other
eight axes are scored and shown in the report (fix them — reviewers see them too), but they
don't flip the verdict on their own.

| Verdict | Condition |
|---|---|
| **REMOVE** (fails → NEEDS_REVISION) | Adjudicated score on either test axis ≤ 2.0, **or** either judge scored an axis ≤ 2 *and* the failure matches an "essential" pattern below. |
| **DISCUSS** (fails → NEEDS_REVISION) | Any single judge scored either test axis ≤ 2, **or** the adjudicated score on either axis ≤ 3.0. |
| **OK** (passes) | Both test axes land **above 3.0** with no judge at ≤ 2. |

> **Practical bar: a task sitting right at 3 does NOT pass.** Aim comfortably above 3 on
> both axes. Don't ship borderline — fix it.

## The two questions the judge asks

Both axes are two sides of the same question: *is the verifier a fair grader of the contract
written in the instruction?*

- **Coverage (Instruction → Tests):** every requirement stated in the instruction has a real,
  enforcing assertion. **A broken or stub solution must fail at least one test.** Gaps here
  mean *false positives* — an agent gets reward 1.0 without doing the work.
- **Faithfulness (Tests → Instruction):** every assertion maps back to something stated or
  reasonably implied in the instruction. Hidden requirements mean *false negatives* — a
  competent engineer who follows the instruction exactly still fails.

---

## The six patterns that trigger an automatic REMOVE

These are treated as **customer-essential defects**. If a judge scores a test axis ≤ 2 and
cites one of these, the task is removed outright — no "discuss" middle ground.

| Pattern | What it looks like in a task |
|---|---|
| **Silent skip** | `@pytest.mark.skip`, `skipif`, catching `ImportError` and setting the module to `None`, or any construct that lets substantive tests silently not run. **If a dependency is missing, the test must fail, not skip.** |
| **No CLI/entry-point invocation** | The instruction asks for a CLI, service, or script, but `test.sh` only runs pytest against library internals and never actually invokes the thing being built. |
| **Pre-created artifact passes** | Tests assert a file exists (`path.exists()`, `is_file()`) without checking its contents, so `touch`-ing the right filename passes. **Every existence check must be paired with a content/behavior assertion.** |
| **Agent controls coverage** | Tests iterate over whatever the agent's own output reports (e.g. loop over entries in the agent's JSON and validate each) — the agent can shrink its output to shrink the test surface. **Enumerate expected items from the instruction/environment, never from agent output.** |
| **Fail-open** | `if not output.exists(): return`, `try: ... except Exception: pass`, assertions gated behind preconditions that may not hold. **A missing or malformed artifact must fail the suite, never pass it.** |
| **Overreach** | Tests enforce names, formats, thresholds, paths, or conventions the instruction never states (the arbitrary naming problem — now machine-checked). |

---

## Test-writing checklist

### Do

- **Map every imperative, named output field, named edge case, and named threshold in the
  instruction to at least one assertion.** The judge literally builds this bipartite mapping —
  build it yourself first.
- **Test observable behavior at the instruction's stated strictness.** If the instruction says
  "all rows", don't assert "at least one row". If it names a threshold, assert the threshold,
  not just `isinstance(score, float)`.
- **Include the regression test** that reproduces the original failure (fails pre-patch,
  passes post-patch). Already required; the judge checks for it.
- **Keep tests deterministic:** fixed seeds, no order dependence, no wall-clock or network
  dependence.
- **Commit fixtures and mock data into the verifier image** so the agent can't tamper with them.
- If the instruction requires a specific output format/schema, **state it in the instruction** —
  that makes your format assertions *faithful* instead of hidden.

### Don't

- ❌ Assert on **source code text** (substring/keyword scans like `"deque" in source`). The
  judge flags source-pattern checks as unfaithful, and they're trivially gamed anyway.
- ❌ Embed **verifier-only constants** (`EXPECTED_COUNT = 47`) the agent can't derive from the
  instruction and environment.
- ❌ Compare against **hidden golden files** the instruction never foreshadows.
- ❌ Compute the expected value **from the agent's own output** (circular checks).
- ❌ Require exact **error strings, JSON key orderings, whitespace styles, tolerances, or file
  paths** unless the instruction (or an existing codebase/framework convention) fixes them.
- ❌ Wrap test bodies in **broad try/except** — ever.

---

## The advisory axes still matter

They appear in the Quality Check report and in what your reviewer reads.

- **Instruction axes** — the judge rewards instructions that read like a real ticket
  (*realism*), fully specify success (*clarity*), reference only artifacts that exist in the
  repo (*self-containedness*), and state requirements, not procedure (*prescriptiveness*).
  Detailed output schemas and conventions are fine and score well; ordered how-to steps, file
  localization hints ("the bug is in `helpers/queue.py`"), and pre-answered edge cases score
  badly.
- **Oracle axes** — the oracle must implement every instruction requirement with the correct
  logic (*spec faithfulness*); must genuinely do the work — no hardcoded answers, no fabricated
  tool output, no reading test-side ground truth, no fixture-specific shortcuts like treating
  `df['Date'].max()` as "today" (*no gaming*); and must be reproducible — seed randomness, no
  live network calls, timeouts on subprocesses (*robustness*).
  > **Litmus test the judge applies:** *"if the inputs were reshuffled within the spec, would
  > this oracle still produce the right answer?"*
- **Packaging** — a **single** stray developer artifact that ships into the container
  (`__pycache__/`, `.DS_Store`, `.venv/`, `.pytest_cache/`, `.idea/`, `.vscode/`, editor swap
  files, `.ruff_cache/`, `node_modules/`) **hard-caps this axis at 1**, as does any solution
  leakage into agent-readable paths.

---

## If the Quality Check fails

1. Download the report and read the per-axis justifications — they cite the exact files, line
   ranges, and quoted instruction text behind each score.
2. Fix the cited defect. **For coverage gaps, add or strengthen assertions; for faithfulness
   defects, either move the requirement into the instruction or relax the assertion.**
3. Keep instruction, tests, and oracle in lockstep, re-upload, and re-run with **Send to
   reviewer unchecked** until the check passes.

---

## Reference: `config.json` and `test.sh`

`config.json` tells the harness how to run the suite and which test ids decide the reward.
`fail_to_pass` is the required, non-empty list; `pass_to_pass` is the regression guard.

```json
{
  "execution": {
    "commands": ["python -m pytest -q tests/test_resume.py"],
    "timeout_sec": 1800
  },
  "grading": {
    "fail_to_pass": [
      "tests/test_resume.py::test_partial_file_preserved",
      "tests/test_resume.py::test_range_request_on_retry"
    ],
    "pass_to_pass": [
      "tests/test_resume.py::test_basic_download"
    ],
    "parser": { "framework": "pytest", "result_source": "stdout_stderr" }
  },
  "artifacts": { "reward": "/logs/verifier/reward.txt" }
}
```

`test.sh` applies the tests, runs the suite, and writes the reward to the path Harbor reads.
**The exit code should match the reward it writes.**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Add the fail-to-pass tests to the repo
git apply /tests/tests.patch

# Run the suite; write 1.0 only if it passes, else 0.0
cd /workspace/repo
if python -m pytest -q tests/test_resume.py; then
  echo "1.0" > /logs/verifier/reward.txt
else
  echo "0.0" > /logs/verifier/reward.txt
  exit 1
fi
```

**Reward** (Glossary): 1.0 only if **every** fail-to-pass test passes and **no** pass-to-pass
test regresses.
