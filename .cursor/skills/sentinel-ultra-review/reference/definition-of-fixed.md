# Definition of Fixed — the gate before you say a task is done

Do **not** report a task as fixed until every line below is satisfied. Each line cites the
guideline that requires it. If a line cannot be satisfied, the task is not fixed — either keep
fixing, or reconsider the verdict.

## Gate 1 — Mechanical (scripts must be clean)

- [ ] `check_task.py` reports **zero** `NOT_FIXABLE` and **zero** `FIXABLE` findings.
- [ ] `git_hygiene.sh` — all nine checks clean:
      HEAD resolves · HEAD == `base_commit_sha` · `git rev-list --all --not HEAD` empty ·
      no remotes · no `filter.*` · clean tree · no `.git/logs` · `.git` < 100 MB ·
      `git apply --check tests/tests.patch` succeeds.
- [ ] Stray-artifact sweep returns nothing.
- [ ] `environment/problem_statement.md` is **byte-identical** to `instruction.md`.
- [ ] `solution/golden.patch` exists (no `solution.patch`).
- [ ] `task.toml`: `cpus` ∈ {2,4} · `memory_mb` 2048–16384 · `storage_mb` 5120–10240 ·
      `gpus = 0` · `build_timeout_sec` ≤ 1800 · `[agent] timeout_sec` ≤ 7200 ·
      `[verifier] timeout_sec` ≤ 1800 · `network_mode` correct in all three blocks ·
      `allowed_hosts = ["api.portkey.ai"]` · accurate `category`, `difficulty_explanation`,
      `source`.
- [ ] `docker_compose.yaml` has no `network_mode = "none"` (if the file exists).

## Gate 2 — Tests (the blocking axes)

- [ ] `config.json` `grading.fail_to_pass` has **≥ 10** entries (ideally 10–20).
- [ ] Every listed f2p id **exists in `tests.patch`** and genuinely fails pre-patch.
- [ ] `pass_to_pass` present as a regression guard; **no pre-existing test file was modified**
      (byte-identical to base commit).
- [ ] At least one test **directly reproduces the failure described in the issue** (fails
      pre-patch, passes post-patch).
- [ ] Worksheet **Step 2 (coverage)** complete: every instruction requirement maps to ≥ 1
      *enforcing* assertion. A stub/broken solution fails at least one test per requirement.
- [ ] Worksheet **Step 3 (faithfulness)** complete: every assertion traces to something stated
      or reasonably implied; every expected name is derivable (exists in base codebase /
      standard convention / stated in instruction).
- [ ] **None** of the six auto-REMOVE patterns present: silent skip · no CLI/entry-point
      invocation · pre-created artifact passes · agent controls coverage · fail-open · overreach.
- [ ] Tests are outcome-based (run code, check results) — no patch-structure, diff, line-number,
      file-name, or source-keyword grading; not satisfiable by hardcoding.
- [ ] Deterministic: fixed seeds, no order dependence, no wall-clock, no network. Finishes
      within the configured timeout.
- [ ] Independent of the oracle: no import/call of the golden solution, no comparison against
      solution-created files; fixtures committed into the verifier image.

## Gate 3 — Instruction

- [ ] Not overly prescriptive — no "Where to look", no named hidden tests/fixtures, no verifier
      internals, no named internal functions to edit, no root-cause hand-holding, no copied
      assertion strings (unless a genuine public/API contract).
- [ ] Any required output format / schema / API shape **is stated** in the instruction (or a
      clearly referenced environment file).
- [ ] Reads like one natural persona; no robotic "The system shall…" phrasing; not templated.
- [ ] Every file, API, and behavior it references **actually exists** in the pinned repo.
- [ ] No PR URL, title, number, or commit SHA. No environment spoilers.

## Gate 4 — Oracle

- [ ] Implements every instruction requirement, with the correct logic.
- [ ] Corresponds to the canonical fix from the source PR (or divergence is documented).
- [ ] No unnecessary changes — no unrelated refactors or drive-by edits.
- [ ] No gaming: no hardcoded answers, fabricated tool output, test-side ground-truth reads, or
      fixture-specific shortcuts. Passes the reshuffle litmus test.
- [ ] Reproducible: seeded randomness, no live network, subprocess timeouts.
- [ ] Substantive: roughly **100+ lines across 2+ files**.

## Gate 5 — PR anchor

- [ ] The task still asks for the **same change as the source PR**.
- [ ] If scope was expanded, it is the **original PR plus additions** — nothing reduced,
      nothing replaced.
- [ ] Instruction, tests, and oracle were updated **in lockstep**, and the instruction reads as
      one realistic ask rather than a tacked-on list.

## Gate 6 — Runtime proof

- [ ] `docker build environment/` succeeds.
- [ ] **Oracle run → reward 1.0.**
- [ ] **NOP run → reward 0.0** (f2p fail, p2p pass).

Required for **Valid as-is** (the platform does not re-run those). Strongly recommended for
**Fixable** — the platform runs it on submission, but a local run saves an eval round-trip.

## Gate 7 — Bundle

- [ ] Zipped with `cd <task-root> && zip -rX ../<name>.zip . -x '*.DS_Store' '__MACOSX/*'`.
- [ ] Contains the **flat contents** of the task root — unpacks directly to `instruction.md`,
      `task.toml`, `environment/`, `solution/`, `tests/`.
- [ ] **No `runs/`**, no wrapping `task/` folder.
- [ ] `unzip -l <name>.zip | grep 'refs/'` shows the empty git directory entries survived.

## Gate 8 — Submission material

- [ ] Every issue documented in the required format:
      `1) [Issue Category] — description with code examples` / `— fixable or not?` /
      `— if fixable, how? if not, why not?`
- [ ] Files Changed list: **path · what changed · why**, for every file.
- [ ] PR-expansion note (or literally `"NA"` if the PR wasn't modified).
- [ ] All 8 Fixable confirmation checkboxes can be truthfully ticked.
- [ ] Difficulty write-up, senior-engineer time estimate, and the three timing fields.
- [ ] Comments for Reviewer written — assumptions, edge cases considered, reasons a file was
      left alone, anything warranting reviewer judgement. **The reviewer is required to read
      this field and acknowledge it.**

---

## Declaring the verdict

Only after **all applicable gates pass** may you say:

> **FIXED** — task now satisfies the Sentinel Ultra bar. Verdict: Fixable. Issues found: N,
> all corrected. Re-checked clean: mechanical ✓, git ✓, coverage map ✓, faithfulness map ✓,
> f2p = M ≥ 10, oracle 1.0 / NOP 0.0 ✓, bundle ✓.

If a gate fails, say exactly which one and what remains. **Never round up.** A task at the
threshold is a task that gets sent back — the Quality Check treats an axis score of exactly 3
as a failure.
