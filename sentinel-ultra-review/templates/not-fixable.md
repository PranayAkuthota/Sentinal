# Submission material — INVALID / NOT FIXABLE

> **Before you use this template, re-read `reference/verdict-rubric.md`.** Not Fixable has
> exactly two causes. If your reason isn't one of them, the verdict is wrong.
>
> - Git problems → **Fixable.** Missing tests → **Fixable.** Bad instruction → **Fixable.**
>   Too easy → **Fixable** (expand scope). Agent timeout → raise `timeout_sec` to 7200 first.
>   Infra/platform error → **not a defect at all**; retry.

The platform asks the analysis question **twice** — **give the same answer both times.**

---

## Section 2 · Task Analysis

**What is your analysis of the Sentinel task you downloaded above?**
→ **Invalid/Not Fixable** — the task is invalid and/or unfixable, as it requires changes
outside of the instructions, tests, or oracle, or is invalid for other reasons.

### What issue did you find with the task/components? (check all that apply)

- [ ] PR scope needs to be changed or reduced
- [ ] Environment Issues

### If Environment Issues, what specific issues? (check all that apply)

- [ ] Image/Dependency Build Failures
- [ ] Oracle timeout
- [ ] External-network dependency at build/solve time
- [ ] Dirty git history that can't be recovered
      — *rare; most git issues are fixable, so only select this for genuinely unrecoverable
      corruption*

---

## Explain in more detail why this task is unfixable

> **Vague or incomplete descriptions may lead to the submission being rejected.** The reviewer
> will try to confirm every issue you list by reading the same files — so give them file paths,
> line numbers, commands, and exact error output.

### Issue format (one block per issue)

```
1) [Issue Category] — describe the specific issue with code examples where helpful
— Is this issue fixable or not fixable?
— If fixable, how? If not, why not?
```

### For a PR-scope Not Fixable, you must show all three

1. **What the source PR actually does.**
   Source: [`task.toml` `source` URL]. [Summarize the real upstream change.]

2. **Why the task cannot be made valid as it stands.**
   [The specific, concrete defect. E.g. "the instruction asks for X, the tests grade Y, and the
   oracle implements Z — no two of the three agree."]

3. **Why every allowed repair fails — this is the part reviewers check hardest.**
   - Rewriting the instruction: [why it doesn't resolve it]
   - Rewriting/adding tests: [why it doesn't resolve it]
   - Correcting the oracle: [why it doesn't resolve it]
   - **Expanding** PR scope: [why adding cannot help — adding is always allowed, so you must
     show the problem is that something must be *removed* or *swapped*]
   - Conclusion: the only remaining path is to **reduce or replace** the PR scope, which the
     guidelines prohibit → Not Fixable.

### For an environment Not Fixable, you must show all four

1. **The exact failure.** Paste the command and the full error:
   ```
   $ docker build environment/
   [paste real output]
   ```

2. **Which Not-Fixable category it falls under**, and why it's that category rather than the
   adjacent fixable one:
   - Image/dependency build failure → *"adding a missing dev package or flag is fixable; this
     is a tangled toolchain/version conflict because […]"*
   - Oracle timeout → *"I raised the timeout to […] and it still timed out at […]"*
   - External-network dependency → *"vendoring one small file is fixable; this pulls […] GB
     from […] at build/solve time"*

3. **The fixable repairs you actually attempted and their results.** Go through the Fixable
   environment table explicitly:
   ```
   bash/ash shebang mismatch        → [n/a | tried: … | result: …]
   missing frozen-requirements.txt  → [n/a | tried: … | result: …]
   tmux missing                     → [n/a | tried: … | result: …]
   asciinema missing                → [n/a | tried: … | result: …]
   unpinned base image              → [n/a | tried: … | result: …]
   resource limits too low          → [n/a | bumped to … | result: …]
   CRLF / shebang / exec bits       → [n/a | tried: … | result: …]
   stray artifacts / bad metadata   → [n/a | tried: … | result: …]
   removing `curl` from installs    → [n/a | tried: … | result: …]   (known Harbor bug)
   raised [agent] timeout_sec       → [n/a | raised to 7200 | result: …]
   ```

4. **That it is a genuine defect, not an infra flake.** Infra/platform errors never make a task
   unfixable. State the reproduction: *"failed identically on N of N attempts"* — a failure
   that appears on some runs and not others is an infra issue, not a task defect.
   If the error is `DaytonaRateLimitError`, `ApiRateLimitError`, a sandbox auth/connection
   error, a one-off `NonZeroAgentExitCode`, or blank feedback → **do not submit Not Fixable.**
   Retry later; flag on Slack with the UID if it persists.

### For unrecoverable git corruption (rare)

Show that each of the standard repairs was attempted and failed:

```
git rev-parse --verify HEAD                   → [output]
git rev-list --all --not HEAD                 → [output]
git remote                                    → [output]
git config --local --get-regexp '^filter\.'   → [output]
git status --porcelain                        → [output]
ls .git/logs                                  → [output]
du -sh .git                                   → [output]
git fsck                                      → [paste corruption evidence]
git gc --aggressive --prune=now               → [result]
git apply --check tests/tests.patch           → [output]
```

Then explain why the repo cannot be restored to a clean single-branch state at the base commit
without editing tracked source files.

---

## What I verified before reaching this verdict

[List what you did read/run, so the reviewer can retrace it: instruction, source PR
cross-check, environment scan, oracle read + run, test read, `runs/` logs. Cite concrete
observations from `runs/` where they support the verdict — e.g. systematic misinterpretation,
where the agent was timing out.]

---

## Comments for Reviewer

[Anything that would help the reviewer confirm the verdict: which repairs you ruled out and
why, where the evidence lives, any part where a second opinion is warranted.]

---

## Timing

- How long did it take you to review the initial task and determine its validity? → [N] minutes
- How long did it take you to complete this entire submission? → [N] minutes

> Note: the difficulty write-up and the senior-engineer time estimate are asked only for
> **Valid as-is** and **Fixable** tasks.
