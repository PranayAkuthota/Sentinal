# Checklists — reading worksheet, Before You Upload, zipping

---

## A. Detailed Tasking Steps (the reading order)

Source: Tasking Guide § "Detailed Tasking Steps". Follow it for every task.

1. **Read the instruction** — start with `instruction.md`. Note requirements, expected
   behavior, success criteria. It should describe the problem and contract, not prescribe
   implementation or expose verifier internals.
2. **Cross-check the source PR and check `task.toml`** — confirm the task reflects the
   intended change and does not introduce unrelated scope (if expanding scope, confirm it's a
   natural extension). Confirm `task.toml` fields meet the requirements: resource/timeout
   values within limits, `gpus = 0`, `network_mode` set in each block.
3. **Scan the environment** — read `environment/Dockerfile`, skim `environment/repo/` to judge
   whether setup and codebase context look plausible for the instruction. Build locally
   (`docker build environment/`) to confirm it builds cleanly and reproducibly.
4. **Review the solution artifacts** — read `solution/solve.sh` and `solution/golden.patch`.
   Check they implement the instruction, and that the change is **substantive (~100+ lines
   spanning 2+ files)**. Run the oracle locally and confirm reward 1.0.
5. **Review the tests** — read `tests/test.sh`, `tests.patch`, `config.json`. Check f2p
   coverage and assertions map to the instruction's requirements; confirm your edits don't
   break any p2p test. **Count the f2p tests: at least 10 (ideally 10–20).** Fewer → Fixable.
6. **Review agent runs** — open `runs/` for evidence of timeouts, systematic misinterpretation,
   or instability. **Cite concrete observations** when they support your verdict or a
   timeout/metadata tweak.
7. **Run evals before submitting** — if the task is too easy after your rewrite, consider
   whether expanding PR scope is appropriate.
8. **Compile findings and submit** via the platform.
9. **Zip the task correctly** before re-uploading (§ C below).

> "Your goal is a thorough, exhaustive review of the task's logic and content. If you miss key
> findings or your submission lacks detail, the task may be sent back for revision."

---

## B. The requirement ↔ assertion worksheet

Do this by hand before judging tests. The Quality-Check judge builds exactly this bipartite
map; building it yourself is the only reliable way to predict the score.

**Step 1 — enumerate the instruction's contract.** One row per imperative, named output field,
named edge case, and named threshold.

| # | Requirement (quote the instruction) | Strictness stated |
|---|---|---|
| R1 | | |
| R2 | | |

**Step 2 — map forward (coverage).** Every R must hit ≥1 enforcing assertion.

| Req | Test id(s) that enforce it | Enforcing? (would a stub solution fail it?) |
|---|---|---|
| R1 | | |

Any R with no test, or only a weak/`isinstance` check → **coverage gap → Fixable**
(form category: "Every requirement in the instructions is not properly tested").

**Step 3 — map backward (faithfulness).** Every assertion must trace to an R.

| Test id | Asserts | Traces to | Derivable? |
|---|---|---|---|
| | | R? / **nothing** | base-codebase / language convention / stated in instruction / **none** |

Any assertion tracing to "nothing", or any expected name that is not derivable by one of the
three routes → **faithfulness defect → Fixable** (form category: "All test requirements are
not properly specified in the instructions").

**Step 4 — the two repairs.** For a coverage gap, *add or strengthen assertions*. For a
faithfulness defect, *either move the requirement into the instruction or relax the assertion*.

**Step 5 — count.** f2p entries in `config.json` `grading.fail_to_pass` — must be ≥ 10.
Confirm each id actually exists in `tests.patch` and actually fails pre-patch.

---

## C. Before You Upload

Source: Tasking Guide § "Before You Upload". These are the failures that produce
"0/8 valid trials — infra/harness failure" difficulty bounces and packaging-axis failures.
**They reproduce identically on every run — resubmitting an unchanged zip will always fail the
same way. Verify locally first.**

- [ ] **`tests.patch` applies cleanly to the base commit.** (See `environment-and-git.md` for
      the verify + regenerate procedure.)
- [ ] **No pre-existing (regression / p2p) test file modified.** They must be byte-identical to
      the base commit. Add new functions or new files only.
- [ ] **Dockerfile builds locally and reproducibly.** `docker build environment/`. Network is
      allowed at build time; the run-time sandbox is restricted and the verifier is airgapped.
      `apt-get update` before installs; distro-correct packages; pinned base image; test deps
      baked into the image.
- [ ] **Git-history hygiene on `environment/repo`** — all nine checks pass.
- [ ] **No stray artifacts or leakage in the bundle** — run the `find` sweep; delete
      everything it finds. Confirm no solution material is readable from agent paths.
- [ ] **`environment/problem_statement.md` is an exact copy of `instruction.md`** — re-copy
      after any instruction edit.
- [ ] **`solution/solution.patch` renamed to `golden.patch`** if present.
- [ ] **`task.toml` sanity** — resource and timeout values within published limits; `gpus = 0`;
      `network_mode` set in each block; `network_mode = "none"` removed from
      `docker_compose.yaml`; `category`, `difficulty_explanation`, and `source` accurate.
- [ ] **Full local dry run** — required for Valid as-is, recommended for Fixable:
      ```bash
      docker build -t task-env environment/   # env builds (network allowed at build time)
      # oracle run: apply golden.patch via solution/solve.sh, then run tests -> reward 1.0
      # NOP run:    run tests on the unsolved repo                           -> reward 0.0
      ```
      Valid as-is tasks are **not** re-run by the platform's difficulty evals — your local run
      is the only check on them.

---

## D. How to zip the task

The archive must contain the **flat contents of `task/`** — not the `task/` folder itself, and
not `runs/`.

```bash
cd task
zip -rX ../<your_task>.zip . -x '*.DS_Store' '__MACOSX/*'
```

- `cd task` — run from inside `task/` so the archive holds its contents at the top level (it
  unpacks directly to `instruction.md`, `task.toml`, `environment/`, `solution/`, `tests/`).
- `zip -rX` — `-r` recurses; `-X` strips extra macOS attributes (resource forks, UID/GID).
- `../<your_task>.zip` — write one level up, outside `task/`, so it isn't included in itself.
- `.` — everything in the current directory.
- `-x '*.DS_Store' '__MACOSX/*'` — exclude macOS junk.

**Why not GUI compress or `zip -rD`:** GUI "Compress" adds `__MACOSX/` and `.DS_Store` entries
and can omit empty directories. **`-D` tells zip not to create directory entries**, so empty
directories such as `.git/refs/` (common after `git gc`) are dropped — the repo then unpacks
without them and git operations fail on the platform, **even though the uncompressed copy
works locally.** `-rX` (no `-D`) preserves those directory entries.

**Verify before uploading** — the empty git directories should still be listed:

```bash
unzip -l <your_task>.zip | grep 'refs/'
```

---

## E. Run Evals (platform, after upload)

Source: Tasking Guide § "Section 3 · Run Evals" + August 4, 2026 Agent Judge–first update.

- **Static Checks** — click *Check feedback* for instant structure and Dockerfile validation.
  **These must pass for the task to be eligible for submission.**
- Summaries after the bundle runs (order matters):
  - **Quality Check (Agent Judge)** — agentic rubric-panel judge; **runs first** and **can block** Difficulty + submission.
  - **Oracle Check** — golden solution against the verifiers.
  - **Difficulty Check** — agent simulation stats; **not run** until Agent Judge passes.
    Marker when blocked: `Blocked at the agentic judge. Not run: difficulty screen (cheap single-arm rollout).`
    After Judge passes: **4 trials per model** (was 8); worse model still must be **≤50%** pass rate.
- *Download difficulty check results* for full logs **when Difficulty ran**. Run checks as many times as needed.
- *Send to Reviewer* — only check once difficulty and quality checks are passing. If
  checks are failing when checked, the task **will always result in revision**; if sending
  intentionally, leave detailed comments explaining why.
- **In-app checks have a 5-minute runtime limit.** If your task needs longer agent runs,
  iterate with the box **unchecked** first.

**When checks fail:** if blocked at Agent Judge, fix Judge citations first (Difficulty was not
run) → revise → re-upload unchecked → repeat until Judge + Difficulty clean → then check
Send to Reviewer.

---

## F. What the Reviewer will do to your submission

Source: Tasking Guide § "Step-by-Step Reviewer Form Questions". Anticipate these; they're what
your submission must survive.

A second EC repeats your document and logic review. They are **not** required to run Harbor,
the oracle, NOP, or Docker builds — but may.

- **On Valid as-is** — they repeat your workflow, sanity-check coherence between instruction /
  solution / tests / PR, verify `task.toml` metadata, and confirm PR comparability.
- **On Not Fixable** — they confirm each issue you listed holds when they read the same files,
  check your issue list matches what they see, and confirm the reason matches a defined
  Not-Fixable category.
- **On Fixable** — they confirm you correctly identified the issues, that your rewrites
  resolve them **without introducing new inconsistencies, hidden requirements, or leakage**,
  that instruction↔test alignment and solvability hold, that any oracle expansion **only adds**
  to the original PR, that the upload contains the full corrected bundle, and they review
  `runs/` where relevant.

They must read your **Comments for Reviewer** field and acknowledge whether it changed their
decision — so write it.

**Reviewer error-category tags** (what they'll label you with if they send it back): Instruction
Styling · Instruction Prescriptiveness · Test ↔ Instruction Misalignment · Test Coverage Issues ·
Exposing Hints/Answers · Oracle Solution Issues · PR Scope Violation · Test Build Issues ·
Time-Based Tests · Task Difficulty · Metadata Issues · Uses Internet · Agent Timeout ·
Wrong Coding Language · Test Dependency Location · Pinning Issues · Environment · PR Relevancy ·
Other.

**Submission Quality Score** you're graded on:

| Score | Description | Action |
|---|---|---|
| 1 | Deviated from the source content (wrong PR, substituted repo code), or low-effort/sloppy/spam | NEEDS REVISION |
| 2 | Source intact but noticeable gaps — untested requirements, instruction/test misalignment, bundle mismatches | NEEDS REVISION |
| 3 | Correct and complete; remaining issues too minor to send back | ACCEPT |
| 4 | All components thorough and accurate, no significant issues | ACCEPT |
| 5 | Every component precise, well-reasoned, clearly written — reference quality | ACCEPT |
