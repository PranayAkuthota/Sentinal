# Project Sentinel — Cursor Orchestration Controller

**Last updated:** July 22, 2026 (Sentinel Ultra final fix)

This file is the **workflow router and automation controller**. It does not duplicate full policy from the `.mdc` files.

| Document | Authority |
|----------|-----------|
| `document 1.txt` / `document 2.txt` / `document 3.txt` | Official Ultra docs (July 22, 2026) |
| `.cursor/rules/Review_Guidelines.mdc` | Authoritative **policy** |
| `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` | **Quick reference** |
| `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` | **Reviewer procedure** |
| `CLAUDE.md` (this file) | **Orchestration / automation** |
| `AGENTS.md` | Plain-Markdown entry point routing here |

Never confuse **submitter** and **reviewer** roles, verdicts, or output templates.

---

## Rule Precedence

Highest first:

1. Latest authoritative Sentinel Ultra documentation and **live platform fields**
2. Current user instruction, **only when** it does not conflict with authoritative project requirements
3. `.cursor/rules/Review_Guidelines.mdc`
4. Role-specific workflow (`.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` for reviewers; submitter steps below + Guidelines)
5. `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc`
6. Clearly labelled legacy compatibility rules

Clarifications:

- A user may select the task, role, output, and workflow.
- A user instruction must **not** override official validity, safety, packaging, or evaluation requirements unless the user supplies newer authoritative documentation.
- The **live platform form** controls the exact fields that must be answered.
- When the live form conflicts with an old stored template, follow the live form.
- Never let a March 2026 rule override the July 22, 2026 Sentinel Ultra documentation.

---

## Operating Modes

Do **not** select an operating mode from an isolated word such as Accept, Reject, Fixable, or Invalid. Determine the mode from the user’s explicit role, requested action, platform section, supplied files, and surrounding context. Keywords are supporting signals only.

### Submitter Mode

Use when the user wants to:

- Inspect an original task
- Choose Valid as-is, Fixable, or Not Fixable
- Correct instructions, tests, oracle, Dockerfile, metadata, or packaging
- Prepare a corrected upload
- Run local validation
- Fill the submission form

### Reviewer Mode

Use when the user wants to:

- Review another submitter’s submission
- Verify corrections
- Choose Accept, Needs Revision, or Reject
- Read rebuttal comments
- Assign reviewer error categories
- Assign Submission Quality Score

### Rule Maintenance Mode

Use only when updating these Sentinel rule files (`CLAUDE.md`, `AGENTS.md`, `.cursor/rules/*.mdc`).

### Read-Only Audit Mode

Use when the user explicitly asks for analysis without modification.

When mode remains genuinely unclear, ask only:

```text
Are you acting as the submitter or reviewer for this task?
```

Do not ask when context already establishes the role.

---

## Task Root Discovery

`/mnt/d/Sentinel/` is an **optional default example only**, not mandatory.

1. Start from the current workspace (this Sentinel folder / user-named path).
2. Ignore: `.cursor/`, `.git/` outside the task repo, `legacy_backup/`, rule files, prompt files, previous generated reports (`sentinel_*.md`, `sentinel_*.txt`, `review_answer.txt`, `sentinel_rule_system_final_audit.md`).
3. Search for a directory containing `instruction.md`, `task.toml`, `environment/`, `solution/`, `tests/`.
4. Support packages where these files are inside `task/`.
5. Locate sibling `runs/` when available.
6. Do **not** require `_harborized` in the directory name.

### Multiple task roots

If multiple possible task roots are found:

1. Prefer the root explicitly named by the user.
2. Otherwise list all credible candidates.
3. Do **not** use modification time alone as proof of the intended task.
4. Do **not** modify any candidate until one task root is clearly selected.
5. Read-only comparison is allowed before selection when needed to identify candidates.

---

## Task Format Detection

### Current Sentinel Ultra signals

- `solution/golden.patch`
- `environment/problem_statement.md`
- `tests/config.json`
- `tests/grade.py`
- Current `task.toml` schema / resources
- Valid as-is / Fixable / Not Fixable form

### Legacy signals

- `solution/init_state.patch`
- Reverse-patch solve process
- `tests/files/`
- Old Valid/Invalid form
- Old Accept/Reject-only review form
- Missing current packaging files

### Hybrid

Use current rules as default; read legacy artifacts for context; do not treat missing optional legacy artifacts as defects; identify renames/adds needed for current upload; explain the decision in the audit.

---

## Universal Inspection Order

1. Discover task root.
2. Detect role.
3. Detect task format.
4. Read instruction.
5. Read task metadata.
6. Cross-check source PR, commit, or issue.
7. Inspect environment.
8. Inspect relevant repository files.
9. Inspect solution.
10. Inspect all test artifacts.
11. Build instruction-to-test map.
12. Build test-to-instruction map.
13. Count f2p tests (guideline ≥10; safest ≥11; preferred 11–20).
14. Check regression coverage.
15. Check Quality Check failure patterns.
16. Inspect runs.
17. Check Git hygiene.
18. Check package hygiene.
19. Decide assessment.
20. Perform role-allowed corrections or produce review findings.
21. Validate.
22. Produce internal audit + platform-ready answer.

---

## Auto-Read File List

```text
instruction.md
task.toml
environment/Dockerfile
environment/problem_statement.md
environment/repo/
solution/solve.sh
solution/golden.patch
solution/solution.patch
solution/init_state.patch
tests/test.sh
tests/tests.patch
tests/config.json
tests/grade.py
tests/files/
runs/**/result.json
runs/**/reward.txt
runs/**/test-stdout.txt
```

- `golden.patch` = current; `solution.patch` → rename; `init_state.patch` = legacy.
- Missing optional legacy files ≠ automatic defects.
- Missing current required files = packaging issue.

---

## Fail-to-Pass Count (Operational)

- Official guideline minimum: **at least 10** fail-to-pass tests.
- Because the current platform form may use **“more than 10,”** prepare **at least 11** meaningful fail-to-pass tests for submission whenever possible.
- Preferred operational target: **11–20**.
- Do **not** create filler tests merely to increase the count.

---

## Internal Audits vs Platform-Ready Answers

Never confuse detailed analysis with exact platform output.

| Kind | File | Contents |
|------|------|----------|
| Internal submitter audit | `sentinel_submitter_audit.md` | Full maps, oracle/env/git/packaging/PR/runs, command evidence |
| Internal reviewer audit | `sentinel_reviewer_audit.md` | Independent findings, submitter comparison, detailed categories, rebuttal analysis |
| Platform submitter answer | `sentinel_platform_answers.txt` | **Only** fields needed by the live submitter form |
| Platform reviewer answer | `review_answer.txt` | **Only** fields needed by the live reviewer form |
| Read-only audit | `sentinel_audit.md` | Analysis only |

Do **not** place these inside `environment/repo/` or inside the corrected task ZIP.

---

## Submitter Mode Workflow

Policy: `.cursor/rules/Review_Guidelines.mdc`. Checklists/templates: `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc`.

### Step 1 — Independent assessment (no edits yet)

Prepare requirements list, instruction issues, coverage/faithfulness maps, oracle/env/git/packaging issues, PR-scope comparison, f2p count, likely verdict → write to `sentinel_submitter_audit.md`.

### Step 2 — Choose assessment

Only: **Valid as-is** | **Fixable** | **Not Fixable**.

### Step 3 — Valid as-is

Do not rewrite. Confirm alignment, no leakage, PR relevance, f2p operational count, offline Docker build, oracle `1.0`, NOP `0.0`, p2p behavior. Use **Template A** for `sentinel_platform_answers.txt`. Never claim a command passed without execution or supplied logs.

### Step 4 — Fixable

Before edits: backup/checkpoint outside tracked task repo; record hashes/diffs. Never edit tracked `environment/repo/` sources; never modify pre-existing p2p tests.

May correct: instruction, `problem_statement.md`, new tests via `tests.patch`, `test.sh`, `config.json`, `grade.py`, `solve.sh`, `golden.patch`, limited Dockerfile, metadata, Git metadata, packaging.

Keep instruction/tests/oracle synchronized. After edits: match problem statement; `tests.patch` applies; ≥11 meaningful f2p when feasible; validate; changed-files log; PR expansion or `NA`; flat ZIP. Use **Template B**.

### Step 5 — Not Fixable

Do not rewrite into a different problem. Provide category, evidence, why allowed fixes fail, why prohibited scope/env work would be required. Use **Template C**.

---

## Reviewer Mode Workflow

Procedure: **`.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc`**.

1. Independently inspect task first → `sentinel_reviewer_audit.md`.
2. Read submitter analysis (do not invent it).
3. Verify every claim; inspect corrected bundle.
4. Review comments/rebuttal.
5. Choose **Accept** / **Needs Revision** / **Reject**.
6. Reject **only** after maximum revisions.
7. Assign error categories + Submission Quality Score.
8. Emit platform answer with Template **D** / **E** / **F** into `review_answer.txt`.

Reviewer local execution is **optional**.

Do not ask the user to paste submitter data when it already exists in files, exports, screenshots, or prior messages. If absent: finish independent audit, list missing fields, ask only for what is needed.

---

## Conditional Submitter Templates (Platform)

Full text also in `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` (Templates A/B/C). Live form wins. Summary:

- **A Valid as-is** — duplicate Task Analysis fields, validity confirmations including safest “more than 10” f2p wording, local validation evidence, difficulty, comments, time fields (user-provided).
- **B Fixable** — components/issue checkboxes, numbered issues, files changed, PR scope, corrected confirmations (≥11 f2p when feasible), validation, times.
- **C Not Fixable** — category/subcategory, detailed why-unfixable evidence, optional difficulty/comments/times.

---

## Conditional Reviewer Templates (Platform)

Full text in `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` (Templates D/E/F). Live form wins. Summary:

- **D Accept** — required confirmations, concise note, rebuttal acknowledgement, score 3–5, time.
- **E Needs Revision** — current error categories, numbered required revisions, rebuttal acknowledgement, score normally 1–2, time.
- **F Reject** — maximum-revision status, remaining categories/defects, note, rebuttal acknowledgement, score 1–2, time.

---

## Automated Test Mapping

Internal table fields:

```text
Requirement ID | Instruction text | Expected observable behavior
Test file | Test ID | Assertion | Coverage | Faithfulness | Risk
```

Required checks: every requirement mapped; every assertion justified; f2p operational count; original-failure regression; CLI when required; deterministic; no silent skip / fail-open / existence-only / agent-controlled coverage / hidden formats / source-text matching / broad except / verifier-only constants / circular expecteds / hidden goldens.

Keep mapping in the internal audit; keep platform notes concise.

---

## Environment and Repository Safety

Inspect freely. Submitter Mode may run validation and allowed fixes.

Never:

- Edit tracked source in `environment/repo/`
- Place golden solution on agent paths
- Modify existing regression / p2p tests
- Delete history without determining correct base
- Use live internet inside task runtime
- Add unrelated source changes
- Silently change PR scope (expand only when allowed)

Git cleanup allowed for: remotes, stray refs, filter drivers, reflog, gc, clean tree, align `base_commit_sha` to HEAD, reduce `.git` size, regenerate `tests.patch`. Record every Git operation.

---

## Command Execution and Evidence

Distinguish: **Inspected** / **Inferred** / **Executed** / **Confirmed by supplied logs**.

Do not claim Docker builds, oracle pass, or NOP fail unless verified. Prefer read-only inspection before edits. No external network inside the task container. Source PR browsing may occur outside the task runtime.

---

## Platform Evaluation Follow-Up

When Static / Difficulty / Oracle / Quality reports are provided:

1. Read every cited defect.
2. Map to file and rule.
3. Decide if feedback is correct.
4. Correct when appropriate (Submitter Mode).
5. Do not dismiss borderline test scores (including “3 with reservations”).
6. Advise keeping Send to Reviewer unchecked while iterating — never claim a platform click you did not perform.
7. Update changed-files log; reassess PR scope after expansions.
8. Prepare concise reviewer-facing notes.

---

## Writing Rules (Active)

Plain evidence-based language; cite files/tests/logs; no generic praise; no hallucinated commands; no major/minor labels unless the live form asks; never mix role templates.

---

## Cross-File Consistency Map

| Topic | Source of truth |
|-------|-----------------|
| Policy, principles, permissions, packaging, evals | `.cursor/rules/Review_Guidelines.mdc` |
| Checklists, matrices, limits, Templates A–C | `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` |
| Reviewer stages, outcomes, categories, Templates D–F | `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` |
| Mode routing, discovery, evidence, output files | `CLAUDE.md` |

Consistency requirements: Ultra submitter/reviewer verdicts; Harbor current artifacts; f2p operational rule; PR expand-only; no tracked-source edits; no p2p mutation; `golden.patch` canonical; Reject = max revisions; local-exec role split; legacy labelled only; internal audit ≠ platform answer.

---

## Active Rules Explicitly Removed

Not active defaults (legacy appendix only if useful):

- “Review is document and logic only”
- “Do not run Harbor, Docker, oracle or NOP”
- Mandatory `/mnt/d/Sentinel/` or `*_harborized`
- `init_state.patch` as primary current patch
- Valid/Invalid as only submitter assessment
- Accept/Reject as only reviewer outcome
- Only four metadata fields matter
- Always paste all submitter information
- Always output old Submission Error Categories
- “Exactly 10 f2p is always sufficient” without the ≥11 safest target
- Auto-select task root by modification time alone
- Mode selection from an isolated keyword

---

## Legacy Sentinel Compatibility

**Not current default.** Use only when the task or platform explicitly requires it. Current Ultra docs and live forms always win.

Preserve: reverse `init_state.patch` explanation; older license mapping; older category list; historical run-count differences; old submission-quality categories; all-failing-run inspection; at least one passing-run confirmation; missing `init_state.patch` alone is not a defect; extra non-conflicting oracle functionality alone is not automatically a defect.

### Reverse `init_state.patch`

Older packages: `solve.sh` often ran `patch -p1 -R < init_state.patch`. `+` = removed from solution; `-` = added by fix. Current uploads use forward `golden.patch`.

### Historical run counts

Older packages: several trials per model. Newer batches (e.g. from April 28 2026): often fewer (two — one per model). Smaller newer sets are expected.

### Old license / category / quality labels

See `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` Legacy Platform Compatibility and `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` Legacy Reviewer Form Compatibility.

### Old Valid/Invalid + Accept/Reject output

Legacy only — see reviewer workflow legacy section. Never combine with Ultra form unless the user explicitly asks for both.
