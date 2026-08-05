# Verdict rubric — Valid as-is / Fixable / Not Fixable

Source: Sentinel Ultra Guidelines § "Task verdicts"; Tasking Guide § "Section 2 · Task
Analysis"; FAQ § "How do I decide between Valid as-is, Fixable, and Not Fixable?".

The platform's wording for the three options:

- **Fixable** — the task has issues in the instructions, tests, and/or oracle, but you can
  correct all issues.
- **Invalid/Not Fixable** — the task is invalid and/or unfixable, as it requires changes
  outside of the instructions, tests, or oracle, or is invalid for other reasons.
- **Valid as-is** — the task is valid without changes.

---

## Decision tree

Run it top to bottom. **First match wins.**

```
1. Is the ONLY way to make this task valid to reduce or replace the PR scope?
      YES → NOT FIXABLE  (reason: "PR scope needs to be changed or reduced")
      NO  ↓

2. Does the task have an environment issue on the NOT-FIXABLE env list below?
   (and it is a genuine defect, not an infra/platform flake)
      YES → NOT FIXABLE  (reason: "Environment Issues" + the specific sub-category)
      NO  ↓

3. Does the task have ANY issue on the FIXABLE list below?
      YES → FIXABLE  (fix all of them, re-verify, re-zip)
      NO  ↓

4. Can you confirm all seven Valid-as-is statements AND did a local
   oracle run give reward 1.0 and a local NOP run give reward 0.0?
      YES → VALID AS-IS
      NO  → you have not finished reviewing. Go back to phase 3.
```

**Step 1 is the trap.** Before answering YES, ask: *could I instead ADD to the scope?*
Adding is always allowed. A task is only scope-Not-Fixable when the instruction/tests/oracle
cannot be made coherent without *removing* or *swapping* what the PR does.

---

## The FIXABLE list (verbatim from Guidelines § Task verdicts)

A task is Fixable if it has one or more of:

1. Instructions are overly prescriptive or expose verifier internals
2. Instruction reads as templated/AI-generated
3. Tests miss requirements stated in the instruction
4. Tests grade behavior that is not in the instruction, or rely on arbitrary names
5. Fewer than 10 fail-to-pass tests — add tests to reach at least 10 (ideally 10–20)
6. Task leaks solution information (PR URL in instruction, environment spoilers,
   test-gaming shortcuts)
7. Oracle does not implement the solution following the instructions
8. Overall task is too easy — but you can raise difficulty by adding to the PR scope
9. A specific, listed Dockerfile issue (see `environment-and-git.md` → Fixable table)
10. A git-hygiene issue in the shipped repo — leaked fix history, a remote, a HEAD/base-commit
    mismatch, reflog, an oversized `.git`

## The NOT-FIXABLE list (verbatim from Guidelines § Task verdicts)

Either of:

- **PR scope needs to be changed or reduced** — the only way to make the task valid is to
  reduce or replace the PR scope entirely.
- **Environment Issues** — the environment has issues ECs aren't allowed to fix.

The platform's Not-Fixable sub-checkboxes (Tasking Guide § "If Invalid/Not Fixable"):

- [ ] PR scope needs to be changed or reduced
- [ ] Environment Issues
  - [ ] Image/Dependency Build Failures
  - [ ] Oracle timeout
  - [ ] External-network dependency at build/solve time
  - [ ] Dirty git history that can't be recovered — *rare; most git issues are fixable, so
        only select this for genuinely unrecoverable corruption*

Nothing else is Not Fixable. If you want to select Not Fixable for a reason not on this
list, you are wrong — re-read the Fixable list.

### Not-Fixable environment issues, and when each is defensible

| Issue | When it's defensible |
|---|---|
| Image/dependency build failures | apt/pip/npm/cargo install errors, missing system libs, compiler flags. Adding a missing dev package or a flag is *fixable*; a tangled toolchain/version conflict is not. |
| Oracle timeout | `harbor run` timed out after n seconds. **Try bumping the timeout first.** |
| External-network dependency at build/solve time | curl/wget/HF/model pulls against a restricted or flaky sandbox. Vendoring one small file is *fixable*; a multi-GB model pull or a live external service is not. |

---

## Things that are NEVER Not Fixable

- **Any git problem** except genuinely unrecoverable corruption. Leaked fix history, a
  remote, a HEAD/base-commit mismatch, a reflog, an oversized `.git` — all fixable inside
  `environment/repo/`, then re-zip. (FAQ: "Git problems are fixable.")
- **Infra / platform errors.** `DaytonaRateLimitError`, `ApiRateLimitError`, sandbox
  auth/connection errors, a one-off `NonZeroAgentExitCode`, blank feedback or
  "No evaluation information available". The tell is *inconsistency* — same task passes on
  one run, errors on another. Retry later; never mark Not Fixable; don't burn a revision
  slot resubmitting blindly. (FAQ)
- **Agent timeout** — raise `[agent] timeout_sec` up to 7200 first. Only if it genuinely
  cannot finish at 7200 *and* the only fix would be reducing PR scope does it become
  Not Fixable.
- **Too easy** — expand PR scope instead.
- **Fewer than 10 f2p tests** — write more.

---

## Valid as-is: the seven statements you must be able to confirm

You must check **every** item (Tasking Guide § "If Valid as-is"):

- [ ] Every requirement in the instructions is properly tested
- [ ] All test requirements are properly specified in the instructions
- [ ] The instructions do not sound like an LLM generated them
- [ ] The instructions are not overly-prescriptive
- [ ] The task does not leak solution information
- [ ] The oracle implements the solution following the instructions
- [ ] Contains more than 10 fail-to-pass tests in the test suite

Plus: **run the oracle and NOP tests locally before submitting.** Valid as-is tasks are
*not* re-run by the platform's difficulty evals — your local run is the only check on them.

```bash
docker build -t task-env environment/          # network allowed at build time
# oracle run: solution/solve.sh applies golden.patch, then tests  -> reward 1.0
# NOP run:    tests on the unsolved repo                          -> reward 0.0
```

## Fixable: the eight statements your corrected task must satisfy

After the rewrite you must be able to confirm all of (Tasking Guide § "If Fixable"):

- [ ] Every requirement in the instructions is properly tested
- [ ] All test requirements are properly specified in the instructions
- [ ] The instructions do not sound like an LLM generated them
- [ ] The instructions are not overly-prescriptive
- [ ] The task does not leak solution information
- [ ] The oracle implements the solution following the instructions
- [ ] The PR was not modified in any way beyond what is allowed by the guidelines
- [ ] More than 10 fail-to-pass tests in the test suite

---

## PR scope rules (the anchor for step 1)

The source PR anchors what the task is about. `task.toml`'s `source` field is that anchor.

**You may:**
- ✅ Add to the scope of the PR to make the task harder.
  - PR adds a `/health` endpoint → you extend it to also handle auto-restart on failure.
  - PR fixes one edge case in a date parser → you extend it to three more edge cases.

**You may not:**
- ❌ Reduce the scope of the PR to make it more concise.
- ❌ Replace the PR with a different feature or task type entirely.
  - PR is a bug fix → you can't rewrite it as a feature add.
  - PR refactors module X → you can't rewrite it as a refactor of module Y.

FAQ rule of thumb: if the task still clearly maps back to the original PR — just bigger or
more thorough — that's adding complexity. If it no longer resembles the PR, or does *less*
than the PR, you've changed the scope → Not Fixable.

Worked example (FAQ): source PR adds CSV export to a reports page.
- ✅ Adding complexity: let the user pick which columns to export; handle empty results,
  commas/quotes inside cell values, very large exports.
- ❌ Changing scope: PDF export instead of CSV; something unrelated; export only the
  current page instead of the full dataset.

Why it matters: the task is anchored to a real PR via `task.toml`. If the task no longer
resembles the PR, the link is misleading and the dataset loses its grounding in real-world
engineering work.
