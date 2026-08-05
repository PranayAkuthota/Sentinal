# Fix playbooks

One playbook per issue class. Each states the guideline rule it serves, the repair, and the
**re-check** that proves it's fixed. Never apply a repair that steps outside the editing rules
in `core-principles.md` § "What you can edit".

**Golden rule of the fix loop:** after any repair, re-run the *whole* check — mechanical
(`check_task.py`, `git_hygiene.sh`) **and** judgement (the requirement↔assertion worksheet).
An individually-patched issue is not a fixed task.

---

## F1 — Instructions are overly prescriptive / expose verifier internals

**Rule:** Guidelines § "Clarity & No Leakage"; judge axis *prescriptiveness*.

**Repair.** Rewrite each offending sentence to describe **observable behavior** instead of
implementation. Delete outright:

- "Where to look:" + file lists, and any file-localization hint.
- Named hidden tests, fixtures, mock endpoints, cassettes, harness files.
- Explanations of how the verifier proves success.
- Named internal functions/branches/comprehensions/callbacks to edit.
- Root-cause analysis that removes the need to inspect the code.
- "the tests reference this name" / "this file validates the fix".
- Exact assertion strings, state paths, or fixture values copied from tests — **unless** they
  are a genuine public/API contract.
- Ordered how-to steps and pre-answered edge cases.

**Keep** (these are required, not leakage): the required output format/schema/API response
shape, stated thresholds, and the acceptance criteria.

**Watch the side effect.** Removing prescription *raises* difficulty (good) but you must not
also remove information the agent cannot rediscover — that breaks solvability. The line:
delete anything the agent could reasonably find by exploring the codebase; keep anything it
could not.

**Re-check.** Re-read as a competent engineer with no repo knowledge: can you tell *what* is
required (yes) without being told *how* (yes)? Then re-run the worksheet — trimming often
orphans assertions that relied on the deleted text.

**Also do:** copy the new `instruction.md` over `environment/problem_statement.md`.

---

## F2 — Instruction reads as templated / AI-generated

**Rule:** Guidelines § "4 Authenticity"; judge axis *realism*; reviewer tag "Instruction Styling".

**Repair.** Pick **one** persona and commit to it: Casual/Slack-like · Structured ticket ·
Technical memo · Prose/email · Acceptance criteria. Then strip the tells:

- Robotic phrasing — "The system shall…", "It is required that…", "This task requires you to…".
- Boilerplate scaffolding headers that no human ticket carries.
- Uniform bullet symmetry and exhaustive enumeration of the obvious.
- Documentation voice instead of task-assignment voice.
- Emoji-headed sections, "Overview / Requirements / Deliverables" triads on a bug report.

Write what the actual reporter would have written: the symptom, when it happens, what should
happen instead, and the constraints that matter.

**Re-check.** Read it aloud. If it sounds like a spec generator rather than a colleague, it
still fails. Confirm the persona is consistent start to finish (mixed tone is itself a red flag).

---

## F3 — Tests miss requirements stated in the instruction (coverage gap)

**Rule:** Guidelines § Test↔instruction alignment (Instruction → Tests); judge axis
*test_coverage*; **blocking**.

**Repair.** From worksheet Step 2, for each uncovered requirement add a test that:

- **runs code and checks results** (outcome-based) — never patch structure, diff format, line
  numbers, file names, or source-keyword matching;
- asserts at the **instruction's stated strictness** — "all rows" means all rows, not "at
  least one"; a named threshold means asserting the threshold, not `isinstance(x, float)`;
- **would fail against a stub solution.** If a `pass`-body implementation still passes your
  test, the test isn't enforcing.

Add them as **new test functions or new test files** in `tests/tests.patch`. Register the new
ids in `config.json` `grading.fail_to_pass`. Never edit a pre-existing test file.

**Re-check.** Mentally (or actually) run the suite against a stubbed implementation — at least
one test must fail per requirement. Then confirm `tests.patch` still applies at base and the
oracle still reaches 1.0.

---

## F4 — Tests grade undescribed behavior / rely on arbitrary names (faithfulness defect)

**Rule:** Guidelines § "The arbitrary naming problem"; judge axis *test_faithfulness*;
**blocking**. Auto-REMOVE pattern: **Overreach**.

**Repair — choose per assertion:**

- **Move it into the instruction** — when the requirement is legitimate and belongs in the
  contract (output schema, JSON keys, a CLI flag, an error taxonomy). Stating a format in the
  instruction is *not* leakage; it's what makes the assertion faithful.
- **Relax the assertion** — when the constraint is incidental. Drop exact error strings, key
  ordering, whitespace, tolerances, and file paths that the instruction (or an existing
  codebase/framework convention) does not fix.

A name is acceptable **only** if it (1) already exists in the base codebase, (2) follows a
standard language/framework convention, or (3) is explicitly stated in the instruction.

**Re-check.** Re-derive every expected name via one of those three routes; anything left over
is still a defect. Keep tests flexible enough to allow multiple valid implementations.

---

## F5 — Fewer than 10 fail-to-pass tests

**Rule:** Guidelines § "At least 10 fail-to-pass tests". Target **10–20**.

**Repair.** Add tests covering requirements **stated or reasonably implied** in the
instruction — *never* undescribed behavior (that just converts a coverage gap into a
faithfulness defect). Productive sources of legitimate additional tests:

- each named edge case in the instruction, separately;
- each named error/failure mode, separately;
- boundary values of any stated threshold;
- the interaction between two stated requirements;
- the **regression test** reproducing the original failure, if it isn't already there.

Count from `config.json` `grading.fail_to_pass`, and verify each listed id actually exists in
`tests.patch` and actually fails pre-patch.

**Re-check.** ≥10 ids, each genuinely f2p (NOP run must give 0.0 with those failing), oracle
run 1.0, no p2p regression.

---

## F6 — The six auto-REMOVE test patterns

**Rule:** Tasking Guide § "Patterns that trigger an automatic REMOVE".

| Pattern | Repair |
|---|---|
| **Silent skip** | Delete `@pytest.mark.skip`/`skipif` and `ImportError → module = None` guards. If a dependency is missing the test must **fail**. Bake the dependency into the verifier image instead. |
| **No CLI/entry-point invocation** | If the instruction asks for a CLI/service/script, `test.sh` must actually invoke it (subprocess the entry point, hit the endpoint) — not only unit-test library internals. |
| **Pre-created artifact passes** | Pair **every** `exists()`/`is_file()` check with a content/behavior assertion on that artifact. |
| **Agent controls coverage** | Enumerate expected items from the instruction/environment. Never iterate over the agent's own output as the test surface. |
| **Fail-open** | Remove `if not X.exists(): return`, `try/except: pass`, and precondition-gated assertions. A missing/malformed artifact must **fail** the suite. |
| **Overreach** | See F4. |

**Re-check.** Grep the test sources for `skip`, `except`, `exists(`, `return` at test top-level,
and confirm none reintroduce the pattern. `check_task.py` flags all six.

---

## F7 — Task leaks solution information

**Rule:** Guidelines § "No leakage".

**Repair by leak type:**

- **PR leakage** — remove PR URLs, titles, numbers, commit SHAs from `instruction.md` and
  `problem_statement.md`. (`task.toml`'s `source` field **should** hold the PR URL — that's
  metadata, not agent-visible.)
- **Environment spoilers** — commit messages, comments, or docs in the base repo / Docker setup
  that describe the exact change. You **may not** edit tracked repo source; if the spoiler is
  in git *metadata* (a commit message past HEAD, a stray branch/tag carrying fix history),
  remove the refs (see F9). If the spoiler is in a Dockerfile comment or a task-level doc,
  delete it.
- **Test-modification gaming** — tighten loose constraints so passing requires implementing the
  behavior, not editing the test.
- **Solution material on agent-readable paths** — golden patch content, expected outputs,
  `ground_truth.*` files. Confirm none is readable from agent paths in the built image; any
  such leakage hard-caps the packaging axis at 1.

**Re-check.** Grep instruction + problem_statement + environment for `github.com/*/pull/`,
`/commit/`, 7–40-hex SHAs, `golden`, `ground_truth`, and the PR title words. Run
`git rev-list --all --not HEAD` (must be empty).

---

## F8 — Oracle does not implement the solution following the instructions

**Rule:** Guidelines § "Solution & oracle — editable in two cases"; judge axes *spec
faithfulness* / *no gaming* / *robustness*.

You may edit `solve.sh` / `golden.patch` in **exactly two cases**: (1) the oracle doesn't
implement the instruction, (2) you're expanding PR scope for difficulty.

**Repair.**

- **Match the canonical fix** from the source PR — not an alternative you invented. Only
  diverge if the upstream fix is genuinely unavailable or unsuitable, and **document why** in
  your submission.
- **No unnecessary changes** — no unrelated refactors, style cleanups, drive-by edits.
- Remove gaming: hardcoded answers, fabricated tool output, reading test-side ground truth,
  fixture-specific shortcuts (e.g. treating `df['Date'].max()` as "today").
- Make it reproducible: seed randomness, no live network calls, timeouts on subprocesses.
- **Update instruction and tests in lockstep.** The instruction must still read as one
  realistic ask, not a tacked-on list.

**Litmus test the judge applies:** *if the inputs were reshuffled within the spec, would this
oracle still produce the right answer?*

**Re-check.** Oracle run → reward 1.0; NOP run → 0.0. Confirm the patch is still ~100+ lines
across 2+ files and still resembles the source PR.

> An oracle that is *larger* than necessary, or includes extra functionality not asked for, is
> **fine** — as long as it does what the instruction requires and the tests enforce that.

---

## F9 — Git hygiene

**Rule:** Guidelines § "Git — fixable in the repo". Do all work **inside `environment/repo`**,
then re-zip. **Never edit tracked source files.**

```bash
cd environment/repo

# HEAD ≠ declared base commit — the shipped repo (HEAD) WINS.
#   Preferred: edit task.toml so base_commit_sha == $(git rev-parse HEAD)
#   (Alternative, only if HEAD is genuinely wrong: git checkout <base_commit_sha>)

# Commits/branches/tags beyond HEAD (these leak the fix history)
git rev-list --all --not HEAD                    # must be empty
git branch  | grep -v '^\*' | xargs -r git branch -D
git tag     | xargs -r git tag -d

# Remotes
git remote | xargs -r -n1 git remote remove

# Filter drivers (arbitrary commands git may run)
git config --local --get-regexp '^filter\.' | cut -d' ' -f1 \
  | sed 's/\.[^.]*$//' | sort -u | xargs -r -n1 git config --local --remove-section

# Dirty tree
git status --porcelain                           # must print nothing
#   -> git checkout -- . && git clean -fd   (discard), or commit if legitimately part of base

# Reflog
git reflog expire --expire=now --all && git gc --prune=now
rm -rf .git/logs

# Oversized .git
du -sh .git                                      # must be < 100 MB
git gc --aggressive --prune=now
#   still large -> strip big blobs, or ship a fresh single-commit base history
#   (then reset base_commit_sha in task.toml)
```

**`.git` missing entirely:** the zip tool dropped dotfiles. Make sure `environment/repo/` is a
real repo and `.git/` is in the archive — and re-zip with `zip -rX` (never `-D`, never GUI).

**Re-check.** `scripts/git_hygiene.sh` — all nine lines clean.

---

## F10 — `tests.patch` won't apply

**Rule:** Tasking Guide § "Before You Upload" (the most common infra failure).

**Repair.** Fix HEAD == base commit **first**, then regenerate against the shipped repo state:

1. At `base_commit_sha`, confirm the target test files are in their **original** state — they
   must **not** already contain the new f2p tests; the patch is what adds them.
2. Apply your f2p test additions by hand.
3. `git add -A && git diff --cached -- <test paths> > ../../tests/tests.patch`
4. `git checkout .` to restore the repo to base.
5. `git apply --check ../../tests/tests.patch` → must succeed silently.
6. Run the oracle + tests end to end.

**Traps:** the repo copy already includes your new tests (patch re-adds → conflict); the patch
touches a non-test file (e.g. `CMakeLists.txt`) that has since changed.

---

## F11 — Dockerfile / environment (limited fixes only)

**Rule:** Guidelines § "Fixable environment issues". Anything not on that table → **Not Fixable**.

```dockerfile
# Alpine missing bash
RUN apk add --no-cache bash
# tmux — Harbor drives agent/verifier inside a tmux pane
RUN apt-get update && apt-get install -y tmux      # or: apk add --no-cache tmux
# asciinema — Harbor records the session
RUN apt-get update && apt-get install -y asciinema # or: pip install asciinema
# Pin the base image
FROM python:3.11.9-slim-bookworm                   # never :latest
```

Also: generate a missing `environment/frozen-requirements.txt` that the Dockerfile `COPY`s;
normalize CRLF → LF; `chmod +x` on `solve.sh` / `test.sh`; fix shebangs; bump undersized
`cpus`/`memory_mb`/`storage_mb` within limits; delete stray pipeline artifacts (`metadata.json`
in root, wrong language fields).

**Bake test dependencies into the image** — the verifier is airgapped, so anything fetched at
test time fails.

**Known bug:** persistent nonzero exit-code agent errors → try removing `curl` from the
package installs and rebuild.

**Re-check.** `docker build environment/` succeeds from a clean cache.

---

## F12 — `task.toml` metadata

**Rule:** Harbor Framework § Task Metadata; judge *packaging* axis cross-checks metadata
against actual content.

Set: `cpus` ∈ {2,4}; `memory_mb` 2048–16384; `storage_mb` 5120–10240; `gpus = 0`;
`build_timeout_sec` ≤ 1800; `[agent] timeout_sec` ≤ 7200; `[verifier] timeout_sec` ≤ 1800;
`network_mode` = `public` / `allowlist` (+ `allowed_hosts = ["api.portkey.ai"]`) / `no-network`
per block. Remove `network_mode = "none"` from `docker_compose.yaml`. Make `category`,
`difficulty_explanation`, and `source` accurate.

> **Don't hand-edit the difficulty/pass-rate fields to satisfy a reviewer.** The linter rejects
> tasks it reads as "easy" outright, so those two goals pull in opposite directions. If you hit
> that conflict, flag it to the team on Slack with the UID and the two disagreeing values —
> it's a tooling gap, not something to fix by editing the task. (FAQ)

---

## F13 — Task is too easy

**Rule:** Guidelines § "Troubleshooting task difficulty". In this order:

1. **Trim over-prescription first** (F1) — it's the usual cause and costs nothing.
2. **If that's not enough, expand the PR scope** — add to what the PR already does.
3. **Keep the added difficulty real** — complex debugging, root-cause analysis, a substantial
   feature, hard domain/security work. **Not** vagueness, underspecification, or stapling
   unrelated changes together; reviewers flag those as confusing, not difficult.
4. Update instruction, tests, and oracle **in lockstep**; re-run the difficulty eval.

If the only way to make it work is reducing or replacing PR scope → **Not Fixable**.

---

## F14 — Packaging hygiene

**Rule:** Tasking Guide § "No stray artifacts or leakage"; judge *packaging* axis (**a single
stray artifact hard-caps it at 1**).

Delete everything the sweep finds: `__pycache__/`, `*.pyc`, `.DS_Store`, `.pytest_cache`,
`.mypy_cache`, `.ruff_cache`, `.venv`, `node_modules`, `.idea`, `.vscode`, `*.swp`, `*~`,
`*.orig`, `*.bak`. Keep intentional dotfiles (`.gitignore`, `.dockerignore`, `.gitattributes`,
`.gitkeep`, `.github/`, `.env` when warranted).

Rename `solution/solution.patch` → `golden.patch`. Sync `problem_statement.md` to
`instruction.md`. Then zip per `checklists.md` § D and verify `refs/` survived.
