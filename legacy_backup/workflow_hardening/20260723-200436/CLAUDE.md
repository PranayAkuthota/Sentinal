# Project Sentinel — Cursor Orchestration Controller

**Last updated:** July 23, 2026 (branch-aware submitter workflow)

This file is the **workflow router and automation controller**. It does not duplicate full policy from the `.mdc` files.

| Document | Authority |
|----------|-----------|
| `document 1.txt` / `document 2.txt` / `document 3.txt` | Official Ultra docs (July 22, 2026) |
| `.cursor/rules/Review_Guidelines.mdc` | Authoritative **policy** |
| `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` | Complete **branch-aware submitter platform workflow** |
| `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` | **Quick reference** / field mapping |
| `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` | **Reviewer procedure** |
| `CLAUDE.md` (this file) | **Orchestration / automation** |
| `AGENTS.md` | Plain-Markdown entry point routing here |
| `automation/sentinel_submitter.py` | File-management helpers only (no verdict decisions) |

Never confuse **submitter** and **reviewer** roles, verdicts, or output templates.

---

## Rule Precedence

Highest first:

1. Latest authoritative Sentinel Ultra documentation and **live platform fields**
2. Current user instruction, **only when** it does not conflict with authoritative project requirements
3. `.cursor/rules/Review_Guidelines.mdc`
4. Role-specific workflow (`.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` for submitters; `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` for reviewers)
5. `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc`
6. Clearly labelled legacy compatibility rules

Clarifications:

- A user may select the task, role, output, and workflow.
- A user instruction must **not** override official validity, safety, packaging, or evaluation requirements unless the user supplies newer authoritative documentation.
- The **live platform form** controls the exact fields that must be answered.
- When the live form conflicts with an old stored template, follow the live form.
- Never let a March 2026 rule override the July 22, 2026 Sentinel Ultra documentation.
- Submitter Mode is **branch-aware**: not permanently read-only, and not auto-modifying every task. Changes occur only when Duplicate Analysis is `Fixable`, and only inside `working_copy/`.

---

## Operating Modes

Do **not** select an operating mode from an isolated word such as Accept, Reject, Fixable, or Invalid. Determine the mode from the user’s explicit role, requested action, platform section, supplied files, and surrounding context. Keywords are supporting signals only.

### Submitter Mode

Activate when the user provides a Sentinel ZIP and platform information and says any equivalent of:

- I am working as a submitter. Start working.
- Start the Sentinel submitter workflow.
- Analyze this task and give me all submitter answers.
- Process this Sentinel submission.
- Audit this task and follow the correct platform branch.
- Submitter mode. Start working.
- Review and correct this Sentinel submission.

Also use when the user wants to:

- Inspect an original task
- Choose Valid as-is, Fixable, or Not Fixable
- Correct instructions, tests, oracle, Dockerfile, metadata, or packaging **when Duplicate Analysis is Fixable**
- Prepare a corrected upload or an unfixable evidence package
- Run local validation
- Fill the submission form / produce paste-ready platform answers

When Submitter Mode is clear, do **not** ask the user to paste a long workflow prompt. Follow `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc`.

### Reviewer Mode

Use when the user wants to:

- Review another submitter’s submission
- Verify corrections
- Choose Accept, Needs Revision, or Reject
- Read rebuttal comments
- Assign reviewer error categories
- Assign Submission Quality Score

Reviewer Mode remains independent and **read-only** with respect to authoring the task under review.

### Rule Maintenance Mode

Use only when updating these Sentinel rule files (`CLAUDE.md`, `AGENTS.md`, `.cursor/rules/*.mdc`, `automation/`).

### Read-Only Audit Mode

Use when the user explicitly asks for analysis without modification.

When mode remains genuinely unclear, ask only:

```text
Are you acting as the submitter or reviewer for this task?
```

Do not ask when context already establishes the role.

---

## Mandatory Role-Specific Rule Loading

Before performing a Sentinel task, open and read the rule files required for the selected operating mode.

### Submitter Mode

Read completely:

1. `.cursor/rules/Review_Guidelines.mdc`
2. `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc`
3. `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc`
4. Relevant sections of `document 1.txt`, `document 2.txt` and `document 3.txt` whenever a rule is unclear or disputed

Do not begin task modification or produce a submitter verdict until these files have been read. Modification is allowed only after the original-task audit and only when Duplicate Analysis is Fixable.

### Reviewer Mode

Read completely:

1. `.cursor/rules/Review_Guidelines.mdc`
2. `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc`
3. `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc`
4. Relevant sections of `document 1.txt`, `document 2.txt` and `document 3.txt` whenever a rule is unclear or disputed

Do not produce Accept, Needs Revision or Reject until the independent reviewer workflow has been completed.

### Rule Maintenance Mode

Read completely:

1. `CLAUDE.md`
2. `AGENTS.md`
3. All `.cursor/rules/*.mdc` files (including `Sentinel_Submitter_Platform_Workflow.mdc`)
4. All three authoritative `document *.txt` files

Do not update one rule file without checking cross-file consistency.

### Read-Only Audit Mode

Read the policy and any role-specific files needed to answer accurately. Do not modify task files.

---

## Workspace Layout (Branch-Aware)

```text
<workspace-root>/
├── incoming_tasks/
├── work/<task-name>/
│   ├── original/
│   ├── extracted_original/     # never mutate
│   ├── working_copy/           # Fixable edits only
│   ├── session/
│   └── analysis/
├── task_outputs/<task-name>/
│   ├── platform_answers.txt
│   ├── submitter_audit.md
│   ├── findings_and_changes.md
│   ├── validation_summary.md
│   ├── updated_zip_file/
│   └── invalid_evidence/
├── completed_tasks/
├── workspace_archive/
├── automation/sentinel_submitter.py
└── legacy_backup/
```

Never automatically select a task from `workspace_archive/`, `legacy_backup/`, previous `task_outputs/`, `completed_tasks/`, or old corrected ZIPs.

---

## Task Root Discovery

`/mnt/d/Sentinel/` is an **optional default example only**, not mandatory.

1. Start from the current workspace (this Sentinel folder / user-named path).
2. Prefer intake via `automation/sentinel_submitter.py intake`.
3. Ignore: `.cursor/`, `.git/` outside the task repo, `legacy_backup/`, `workspace_archive/`, `completed_tasks/`, `task_outputs/`, rule files, prompt files, previous generated reports.
4. Search for a directory containing `instruction.md`, `task.toml`, `environment/`, `solution/`, `tests/`.
5. Support packages where these files are inside `task/`.
6. Locate sibling `runs/` when available.
7. Do **not** require `_harborized` in the directory name.

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

1. Discover task root / run intake.
2. Detect role.
3. Detect task format.
4. Preserve original ZIP.
5. Read instruction.
6. Read task metadata.
7. Cross-check source PR, commit, or issue.
8. Inspect environment.
9. Inspect relevant repository files.
10. Inspect solution.
11. Inspect all test artifacts.
12. Build instruction-to-test map.
13. Build test-to-instruction map.
14. Count f2p tests using the official ≥10 / Fixable-if-<10 / live-form “more than 10” rules (preferred practical range 11–20).
15. Check regression coverage.
16. Check Quality Check failure patterns.
17. Inspect runs.
18. Check Git hygiene.
19. Check package hygiene.
20. Determine Public Main Analysis.
21. Determine Internal Validity separately (record reason).
22. Set Duplicate Analysis to match Public Main Analysis.
23. Select branch from Duplicate Analysis.
24. Perform branch actions (fix / evidence / confirm-only).
25. Validate per branch policy.
26. Produce chat answers + `task_outputs/` artifacts.

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

- `golden.patch` = current; `solution.patch` → rename when Fixable packaging requires it; `init_state.patch` = legacy.
- Missing optional legacy files ≠ automatic defects.
- Missing current required files = packaging issue.

---

## Fail-to-Pass Count (Operational)

- **Official guideline minimum:** at least **10** meaningful fail-to-pass tests.
- **Fixable test-count defect:** fewer than **10** fail-to-pass tests.
- **Exactly 10:** meets the documented guideline.
- **Live Valid-as-is confirmation “more than 10”:** true only if count ≥ **11**.
- When otherwise valid but exactly 10 and the live form requires more than 10: use **Fixable** branch and add at least one meaningful non-duplicate test in `working_copy/`.
- **Preferred practical range:** **11–20** meaningful fail-to-pass tests.
- Never add duplicate, shallow, or filler tests only to increase the count.

### Platform checkbox behavior

- If the task contains **9 or fewer** fail-to-pass tests: select **“Less than 10 fail-to-pass tests in the test suite.”**
- If the task contains **exactly 10:** do **not** select the “Less than 10” issue (that statement would be false).
- If the live form requires confirmation of **“More than 10 fail-to-pass tests in the test suite”:** select it only when the count is at least 11 (after Fixable corrections when applicable).

---

## Difficulty Handling (Routing)

Policy detail: `.cursor/rules/Review_Guidelines.mdc` → Difficulty Handling After Corrections.

In Submitter Mode, apply difficulty policy for assessment and reviewer comments. When Duplicate Analysis is Fixable, permitted instruction/test/oracle updates may be applied in `working_copy/` only. Never expand difficulty by inventing a different PR scope.

---

## Three Verdict Fields and Nine Combinations

| Field | Values |
|-------|--------|
| Public Main Analysis | Fixable / Invalid/Not Fixable / Valid as-is |
| Internal Validity | Invalid / Fixable / Valid-as-is |
| Duplicate Analysis | Fixable / Invalid/Not Fixable / Valid-as-is |

- Duplicate Analysis **must match** Public Main Analysis semantically.
- Internal Validity is recorded separately and may differ when evidence/platform context supports it.
- All nine Internal × Duplicate combinations are supported.
- **Branch selection uses Duplicate Analysis only.**

---

## Submitter Mode Summary (Branch-Aware)

1. Intake ZIP and platform information.
2. Preserve original ZIP.
3. Audit original task.
4. Determine Public Main Analysis.
5. Determine Internal Validity separately.
6. Make Duplicate Analysis match Public Main Analysis.
7. Select the branch using Duplicate Analysis.
8. Fix only in a separate working copy when Duplicate is Fixable.
9. Produce evidence package when Duplicate is Invalid/Not Fixable.
10. Make no task changes when Duplicate is Valid-as-is.
11. Answer all platform fields in chat.
12. Generate branch-specific outputs under `task_outputs/`.

Remove any notion that the whole workflow is permanently read-only.
Remove any notion that every task is automatically changed.

### Branch actions

| Duplicate Analysis | Action |
| ------------------ | ------ |
| Fixable | Audit → correct `working_copy/` → validate → flat corrected ZIP |
| Invalid/Not Fixable | Audit → diagnose → unfixable evidence ZIP → explain blocker |
| Valid-as-is | Audit → confirm seven requirements → no task modification → no new ZIP |

---

## Internal Audits vs Platform-Ready Answers

Never confuse detailed analysis with exact platform output.

**Submitter Mode:** deliver every paste-ready field answer **in the chat** and also save:

- `task_outputs/<task>/platform_answers.txt`
- `task_outputs/<task>/submitter_audit.md`
- `task_outputs/<task>/findings_and_changes.md`
- `task_outputs/<task>/validation_summary.md`
- Plus branch ZIP under `updated_zip_file/` or `invalid_evidence/` when applicable

| Kind | Where it goes | Contents |
|------|---------------|----------|
| Internal submitter audit | `submitter_audit.md` + chat summary | Full maps, oracle/env/git/packaging/PR/runs, evidence |
| Submitter findings/changes | `findings_and_changes.md` + chat | Issues and applied/not-applied changes |
| Platform submitter answers | **Chat** + `platform_answers.txt` | Live submitter form fields |
| Internal reviewer audit | `sentinel_reviewer_audit.md` when in Reviewer Mode | Independent findings |
| Platform reviewer answer | `review_answer.txt` when in Reviewer Mode | Live reviewer form fields |

Do **not** place generated analysis inside `environment/repo/` or inside the upload task package.

---

## Reviewer Mode Workflow

Procedure: **`.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc`**.

1. Independently inspect task first → `sentinel_reviewer_audit.md`.
2. Read submitter analysis (do not invent it).
3. Verify every claim; inspect corrected bundle when one was supplied.
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

- **A Valid as-is** — duplicate Task Analysis fields; validity confirmations including “More than 10” only when ≥11; validation evidence; difficulty; comments; tracked times.
- **B Fixable** — components/issue checkboxes; numbered issues with applied corrections in working copy; files changed; corrected ZIP path when ready; times.
- **C Not Fixable** — category/subcategory, detailed why-unfixable evidence, evidence ZIP path, difficulty/comments/times.

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

Inspect freely. Mutate only `working_copy/` and only on the Fixable branch.

Never:

- Edit tracked source in `environment/repo/`
- Place golden solution on agent paths
- Modify existing regression / p2p tests
- Delete history
- Use live internet inside task runtime
- Add unrelated source changes
- Silently change PR scope
- Overwrite the original ZIP
- Mutate `extracted_original/`

Git hygiene cleanup, when needed on Fixable, occurs only in `working_copy/`.

---

## Command Execution and Evidence

Distinguish: **Inspected** / **Inferred** / **Executed** / **Confirmed by supplied logs** / **Not verified**.

Default: document and logic analysis first. When a command may alter files, Git state, generated caches or build outputs:

- Do not run it against `extracted_original/`.
- Use `working_copy/` or a disposable copy.
- Preserve the original ZIP unchanged.

Do not claim Docker builds, oracle pass, or NOP fail unless verified by supplied logs or actual execution. Never fabricate validation results, issue evidence, test counts, or handling times.

---

## Platform Evaluation Follow-Up

When Static / Difficulty / Oracle / Quality reports are provided:

1. Read every cited defect.
2. Map to file and rule.
3. Decide if feedback is correct.
4. On Fixable branch, correct in `working_copy/` when permitted; otherwise update platform answers and evidence.
5. Do not dismiss borderline test scores (including “3 with reservations”).
6. Advise keeping Send to Reviewer unchecked while iterating — never claim a platform click you did not perform.
7. **Runtime note:** in-app platform checks have a **five-minute** runtime limit.

---

## Writing Rules (Active)

Plain evidence-based language; cite files/tests/logs; no generic praise; no hallucinated commands; no major/minor labels unless the live form asks; never mix role templates; never claim task edits that did not occur; never invent times.

---

## Cross-File Consistency Map

| Topic | Source of truth |
|-------|-----------------|
| Policy, principles, permissions, packaging, evals | `.cursor/rules/Review_Guidelines.mdc` |
| Branch-aware submitter ZIP → audit → branch → answers | `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` |
| Checklists, matrices, limits, Templates A–C, field mapping | `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` |
| Reviewer stages, outcomes, categories, Templates D–F | `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` |
| Mode routing, discovery, evidence, output files | `CLAUDE.md` |
| Intake / package / archive file ops | `automation/sentinel_submitter.py` |

Consistency requirements: Ultra submitter/reviewer verdicts; Harbor current artifacts; f2p operational rule; PR expand-only; no tracked-source edits; no p2p mutation; `golden.patch` canonical naming; Reject = max revisions; local-exec role split; legacy labelled only; internal audit ≠ platform answer; Duplicate controls branch; Public matches Duplicate; Internal Validity separately recordable; original ZIP always preserved.

---

## Active Rules Explicitly Removed

Not active defaults (legacy appendix only if useful):

- Permanently read-only Submitter Mode for all branches
- Automatically modifying every task
- “Review is document and logic only” as a ban on all execution (isolated disposable / working_copy validation remains allowed)
- Mandatory `/mnt/d/Sentinel/` or `*_harborized`
- `init_state.patch` as primary current patch
- Valid/Invalid as only submitter assessment
- Accept/Reject as only reviewer outcome
- Only four metadata fields matter
- Always paste all submitter information
- Always output old Submission Error Categories
- Treating exactly 10 f2p as automatically Fixable solely for the count (except live “more than 10” confirmation gap)
- Treating 11 as the official minimum instead of the preferred practical target
- Auto-select task root by modification time alone
- Mode selection from an isolated keyword
- Auto-select tasks from archives/backups/old outputs

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
