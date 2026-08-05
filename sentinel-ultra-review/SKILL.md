---
name: sentinel-ultra-review
description: Review a Sentinel Ultra / Harbor task zip as an Expert Contributor — decide Valid as-is vs Fixable vs Not Fixable, produce the evidence and submission-form text for that verdict, apply the allowed fixes, re-check until clean, and re-package. Use whenever a contributor uploads or points at a Sentinel task (a .zip, or a folder with task.toml + instruction.md + environment/ + solution/ + tests/), asks "is this task valid / fixable", asks to fix a task, or asks what to write in the submitter form.
---

# Sentinel Ultra — Expert Contributor task review

You are acting as the **Submitter EC**: you receive a task, decide its verdict, fix it if
fixable, re-verify, and hand back everything the submission form asks for.

Everything in this skill is derived from the five Sentinel Ultra docs (Guidelines,
Tasking Guide, Harbor Framework, Glossary, FAQ). **Do not invent rules.** Every finding
you report must cite a rule that exists in `reference/`. If a check is not covered by the
guidelines, say so and mark it advisory rather than making it a verdict driver.

## The three verdicts (memorize this — it is the whole job)

| Verdict | When it applies |
|---|---|
| **Valid as-is** | Instruction, tests, and oracle all align with each other and with the source PR. No rewrite or edits required. |
| **Fixable** | One or more issues from the **Fixable list** — and you can correct all of them yourself, without touching PR scope or repo source files. |
| **Not Fixable** | *Only* two causes: (a) the only way to make the task valid is to **reduce or replace the PR scope**, or (b) an **environment issue on the Not-Fixable list**. |

**Bias to Fixable.** Git problems are fixable. Missing tests are fixable. Bad instructions
are fixable. A too-easy task is fixable (expand PR scope). Infra/platform flakes are *never*
a defect at all. Reach for Not Fixable only when `reference/verdict-rubric.md` says you may.

## Workflow

Work these six phases in order. Do not skip to a verdict before phase 3.

### Phase 1 — Intake

```bash
python3 "$SKILL_DIR/scripts/intake.py" <task.zip | task-dir> --work <workdir>
```

Unpacks the zip (or copies the dir), locates the real task root (handles zips that wrap a
`task/` folder), reports the layout, flags naming variants (`solution.patch` →
`golden.patch`, `tests/test.patch` → `tests/tests.patch`), and prints an inventory.

Then **read, in this order**: `instruction.md` → `task.toml` (source URL) → the source PR →
`solution/golden.patch` → `tests/tests.patch` + `config.json` → `environment/Dockerfile` →
`runs/` if present. This ordering is the Tasking Guide's "Detailed Tasking Steps".

### Phase 2 — Mechanical checks

```bash
python3 "$SKILL_DIR/scripts/check_task.py" <task-root> --json findings.json --md report.md
```

Runs every check that can be decided from files alone: structure, `task.toml` limits and
`network_mode` blocks, `problem_statement.md` ↔ `instruction.md` identity, f2p count,
the six auto-REMOVE test patterns, leakage scans, over-prescription phrases, Dockerfile
rules, stray-artifact sweep, oracle size, and `tests.patch` sanity. Git hygiene:

```bash
bash "$SKILL_DIR/scripts/git_hygiene.sh" <task-root>        # the 9-line pre-submission checklist
```

Each finding carries a severity (`NOT_FIXABLE` / `FIXABLE` / `ADVISORY`), the form category
it maps to, evidence, the guideline citation, and the prescribed fix.

### Phase 3 — Judgement checks (no script can do these — you must read)

Load `reference/core-principles.md` and work the four principles by reading:

1. **Solvability** — solvable from the instruction alone; no arbitrary guesswork; every
   claim about files/APIs/behavior actually exists in the pinned repo.
2. **Clarity & No Leakage** — describes behavior not implementation; nothing exploitable.
3. **Verifiability** — build the bipartite map yourself: every instruction requirement →
   ≥1 enforcing assertion, and every assertion → something stated or reasonably implied.
   This is the only axis that *blocks* submission (`test_coverage`, `test_faithfulness`).
4. **Authenticity** — real engineering ask, one natural persona, ~100+ lines across 2+
   files, and the instruction asks for the *same change as the PR*.

`reference/checklists.md` has the literal worksheet for each. Fill the requirement↔assertion
table before you decide anything about tests — the platform's judge builds exactly that map.

### Phase 4 — Verdict

Apply `reference/verdict-rubric.md` decision tree. State the verdict, then list every
finding as evidence. Never assert a verdict you cannot ground in a cited rule. Write the
human-facing summary with `templates/review-report.md` — that's what the contributor reads.

### Phase 5 — Deliverables (this is what the contributor actually needs)

Produce the material for the verdict you reached, using `templates/`:

- **Valid as-is** → `templates/valid-as-is.md`. Requires confirming all 7 checkboxes **and**
  a local oracle + NOP run — Valid as-is tasks are *not* re-run by the platform's difficulty
  evals, so your local run is the only check on them.
- **Fixable** → `templates/fixable.md`. Numbered issue list in the required format, the
  Files Changed table, the PR-expansion note, all 8 confirmation checkboxes, difficulty
  write-up, reviewer comments. Then do phase 6.
- **Not Fixable** → `templates/not-fixable.md`. Category selection + a detailed,
  non-vague justification (vague ones get rejected).

Always also fill `templates/difficulty-and-timing.md` (needed on Valid and Fixable paths).

### Phase 6 — Fix loop (Fixable only)

1. Apply fixes from `reference/fix-playbooks.md`. Stay inside the editing rules:
   **editable** = instruction, tests, oracle, limited Dockerfile fixes, git metadata in
   `environment/repo`. **Never editable** = tracked source files in `environment/repo/`,
   pre-existing test files, PR scope (reduce/replace).
2. Mechanical autofixes:
   ```bash
   python3 "$SKILL_DIR/scripts/fix_common.py" <task-root> --apply
   ```
   (rename `solution.patch`, sync `problem_statement.md`, repair `network_mode` blocks and
   resource limits, strip `network_mode = "none"` from `docker_compose.yaml`, sweep stray
   artifacts, normalize CRLF/shebangs/exec bits, git cleanup.) Run with `--dry-run` first.
3. **Re-run phases 2 and 3 from scratch.** A task is only "fixed" when the full check
   passes again — not when the individual issue is patched.
4. Re-package:
   ```bash
   bash "$SKILL_DIR/scripts/package.sh" <task-root> <out.zip>
   ```
   Zips the **flat contents** of the task root (never the folder, never `runs/`), uses
   `zip -rX` so empty dir entries like `.git/refs/` survive, then verifies them in the
   archive.
5. Only mark **fixed** when: `check_task.py` reports no `FIXABLE`/`NOT_FIXABLE` finding,
   `git_hygiene.sh` is all-clean, the requirement↔assertion map is complete in both
   directions, f2p ≥ 10, and (recommended) a local oracle=1.0 / NOP=0.0 run succeeded.
   `reference/definition-of-fixed.md` is the gate — read it before you declare done.

## Hard rules that override everything else

- **Never edit tracked source files in `environment/repo/`.** Cleaning `.git` metadata and
  restoring the tree to the base commit is allowed and expected; editing code is not.
- **Never modify a pre-existing test file.** The harness byte-compares them against the
  base commit. Add new test functions or new files via `tests/tests.patch` only.
- **Never reduce or replace PR scope.** You may only *add* to it.
- **`problem_statement.md` must be a byte-exact copy of `instruction.md`** — re-copy after
  every instruction edit.
- **Infra/platform errors are not task defects.** `DaytonaRateLimitError`, sandbox auth
  errors, one-off `NonZeroAgentExitCode`, blank feedback — retry, never mark Not Fixable.
- **A Quality-Check score of exactly 3 on a test axis fails.** Aim comfortably above 3.

## Reference map

| File | Use it for |
|---|---|
| `reference/verdict-rubric.md` | The decision tree; the exact Fixable and Not-Fixable lists |
| `reference/core-principles.md` | The four principles, in full, with the guideline's examples |
| `reference/test-quality.md` | The blocking axes, six auto-REMOVE patterns, do/don't checklist |
| `reference/environment-and-git.md` | Fixable vs Not-Fixable env table; the 9 git checks + fixes |
| `reference/harbor-format.md` | Task layout, every `task.toml` field and its limit |
| `reference/fix-playbooks.md` | Step-by-step repair for each issue class |
| `reference/checklists.md` | Before-You-Upload, the reading worksheet, zip rules |
| `reference/definition-of-fixed.md` | The gate for declaring a task fixed |
| `reference/glossary.md` | Terminology (f2p, p2p, oracle, reward, pass@k …) |
| `reference/faq.md` | Edge cases: timeouts, curl bug, difficulty linter, scope vs complexity |

`SKILL_DIR` is this skill's directory. Scripts are dependency-free Python 3 / bash.
