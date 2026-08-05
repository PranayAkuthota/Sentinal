# Project Sentinel — Cursor Orchestration Controller

**Last updated:** July 23, 2026 (strict read-only submitter workflow)

This file is the **workflow router and automation controller**. It does not duplicate full policy from the `.mdc` files.

| Document | Authority |
|----------|-----------|
| `document 1.txt` / `document 2.txt` / `document 3.txt` | Official Ultra docs (July 22, 2026) |
| `.cursor/rules/Review_Guidelines.mdc` | Authoritative **policy** |
| `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` | Complete **read-only submitter platform-answer workflow** |
| `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` | **Quick reference** / field mapping |
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
4. Role-specific workflow (`.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` for submitters; `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` for reviewers)
5. `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc`
6. Clearly labelled legacy compatibility rules

Clarifications:

- A user may select the task, role, output, and workflow.
- A user instruction must **not** override official validity, safety, packaging, or evaluation requirements unless the user supplies newer authoritative documentation.
- The **live platform form** controls the exact fields that must be answered.
- When the live form conflicts with an old stored template, follow the live form.
- Never let a March 2026 rule override the July 22, 2026 Sentinel Ultra documentation.
- In this Cursor workspace, Submitter Mode is **strict read-only**. Official policy still defines what “Fixable” would allow on the platform; Cursor must not apply those changes to the supplied task.

---

## Operating Modes

Do **not** select an operating mode from an isolated word such as Accept, Reject, Fixable, or Invalid. Determine the mode from the user’s explicit role, requested action, platform section, supplied files, and surrounding context. Keywords are supporting signals only.

### Submitter Mode

Activate when the user provides a Sentinel ZIP and platform information and says any equivalent of:

- I am working as a submitter. Start working.
- Analyze this Sentinel task and answer the submitter fields.
- Perform a read-only Sentinel submitter audit.
- Use the supplied ZIP to prepare the platform answers.
- Submitter mode. Start working.
- Start this task as a submitter.
- I am the submitter. Begin the task.

Also use when the user wants to:

- Inspect an original task in read-only mode
- Choose Valid as-is, Fixable, or Not Fixable for the **original** task
- Verify platform metadata against the package
- Fill the submission form / produce paste-ready platform answers

Do **not** interpret “submitter” as permission to modify the task.

Do **not** activate from correction-implying phrases as a license to edit. If the user asks only for platform answers, stay read-only.

When Submitter Mode is clear, do **not** ask the user to paste a long workflow prompt. Follow `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc`.

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

## Strict Read-Only Submitter Analysis

When the user provides a Sentinel task ZIP for platform-answer analysis:

- Treat the complete supplied task as read-only.
- Do not modify any file inside the extracted task.
- Do not rewrite `instruction.md`.
- Do not change `environment/problem_statement.md`.
- Do not edit `task.toml`.
- Do not remove `network_mode` or `allowed_hosts`.
- Do not edit the Dockerfile.
- Do not alter Git metadata.
- Do not edit or regenerate `tests.patch`.
- Do not modify existing tests.
- Do not add fail-to-pass tests.
- Do not modify `test.sh`, `config.json` or `grade.py`.
- Do not modify `solve.sh`, `golden.patch`, `solution.patch` or `init_state.patch`.
- Do not change anything under `environment/repo/`.
- Do not clean packaging artifacts.
- Do not rename solution artifacts.
- Do not create a corrected task ZIP.
- Do not overwrite the original ZIP.
- Do not apply suggested fixes automatically.

If a problem is found:

1. Record the problem.
2. Explain why it matters.
3. Classify the task as Fixable or Invalid/Not Fixable as appropriate.
4. Produce the required platform answers.
5. Leave the task unchanged.

The word **“Fixable”** is an assessment, not permission to fix the supplied task.

---

## Mandatory Role-Specific Rule Loading

Before performing a Sentinel task, open and read the rule files required for the selected operating mode.

### Submitter Mode

Read completely:

1. `.cursor/rules/Review_Guidelines.mdc`
2. `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc`
3. `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc`
4. Relevant sections of `document 1.txt`, `document 2.txt` and `document 3.txt` whenever a rule is unclear or disputed

Do not produce a submitter verdict until these files have been read. Do not begin task modification — Submitter Mode must leave the supplied task unchanged.

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
4. Do **not** modify any candidate.
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

Use current rules as default; read legacy artifacts for context; do not treat missing optional legacy artifacts as defects; report renames/adds needed for current upload as findings only; explain the decision in the audit.

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
13. Count f2p tests using the official ≥10 / Fixable-if-<10 / live-form “more than 10” rules (preferred practical range 11–20).
14. Check regression coverage.
15. Check Quality Check failure patterns.
16. Inspect runs.
17. Check Git hygiene.
18. Check package hygiene.
19. Decide assessment of the **original** task.
20. Record read-only findings (do not edit the task in Submitter Mode).
21. Record validation evidence (inspected / supplied logs / unexecuted).
22. Produce internal audit + platform-ready answers.

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

- `golden.patch` = current; report `solution.patch` naming when applicable (do not rename); `init_state.patch` = legacy.
- Missing optional legacy files ≠ automatic defects.
- Missing current required files = packaging issue (report only).

---

## Fail-to-Pass Count (Operational)

- **Official guideline minimum:** at least **10** meaningful fail-to-pass tests.
- Plain wording: At least 10 meaningful fail-to-pass tests.
- **Fixable test-count defect:** fewer than **10** fail-to-pass tests.
- **Exactly 10:** meets the documented guideline. Do **not** classify a task as Fixable solely because it has exactly 10 unless the live platform or an automated platform check explicitly requires more than 10.
- **Safest live-form submission target:** when the live platform requires confirmation of **“more than 10,”** that confirmation is true only if the original task already has at least 11. Never claim “More than 10” when the task contains exactly 10. Do **not** add tests in Submitter Mode.
- **Preferred practical range:** **11–20** meaningful fail-to-pass tests.
- Plain wording: 11–20 meaningful fail-to-pass tests.
- Never add duplicate, shallow, or filler tests only to increase the count.

### Platform checkbox behavior

- If the task contains **9 or fewer** fail-to-pass tests: select **“Less than 10 fail-to-pass tests in the test suite.”**
- If the task contains **exactly 10:** do **not** select the “Less than 10” issue (that statement would be false).
- If the live form requires confirmation of **“More than 10 fail-to-pass tests in the test suite”:** select it only when the original task already has at least 11. Do **not** add tests.

---

## Difficulty Handling (Routing)

Policy detail: `.cursor/rules/Review_Guidelines.mdc` → Difficulty Handling After Corrections.

In Submitter Mode, use difficulty policy only for assessment and reviewer comments. Do **not** rewrite the instruction, expand PR scope, or update tests/oracle in the supplied task. Report theoretical difficulty-related corrections as findings when relevant.

---

## Internal Audits vs Platform-Ready Answers

Never confuse detailed analysis with exact platform output.

**Submitter Mode (Cursor):** deliver every paste-ready field answer **in the chat only**. Do **not** create submitter output files on disk (`sentinel_platform_answers.txt`, `sentinel_submitter_audit.md`, `sentinel_findings.md`, `sentinel_submitter_session.json`, `sentinel_audit.md`, `sentinel_changes.md`).

| Kind | Where it goes | Contents |
|------|---------------|----------|
| Internal submitter audit | Keep internal / summarize in chat as needed | Full maps, oracle/env/git/packaging/PR/runs, evidence |
| Submitter findings | Chat (Task Findings section) | Issues only (no claim that changes occurred) |
| Platform submitter answers | **Chat paste-ready block** | **Only** fields needed by the live submitter form |
| Internal reviewer audit | `sentinel_reviewer_audit.md` when in Reviewer Mode | Independent findings, submitter comparison, detailed categories, rebuttal analysis |
| Platform reviewer answer | `review_answer.txt` when in Reviewer Mode | **Only** fields needed by the live reviewer form |

Do **not** create `sentinel_changes.md` as though task changes occurred.

Do **not** place generated analysis inside `environment/repo/` or inside any task package.

Do **not** create a corrected task ZIP.

---

## Submitter Mode Workflow

**Complete procedure:** `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc`.

Policy: `.cursor/rules/Review_Guidelines.mdc`. Checklists / quick field mapping: `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc`.

Normal submitter inputs: one Sentinel ZIP + platform-information block (Original Directory Name, Category, Difficulty, Task Tags, Languages, Metadata) + start-as-submitter instruction. Verify platform metadata against the task; do not assume it is correct.

### Submitter Mode summary

1. Locate and inspect ZIP
2. Verify platform metadata
3. Complete read-only audit
4. Choose assessment
5. Generate platform answers
6. Do not modify task
7. Do not create corrected ZIP

### Routing summary (details in Submitter Platform Workflow)

1. Track real timestamps internally (draft times only; confirm in chat before final answers). Do not write a session file.
2. Locate ZIP → find task root → detect Current / Legacy / Hybrid / Unknown.
3. Complete read-only audit and instruction↔test maps. Do not edit the task.
4. Choose internal assessment of the original task: **Valid as-is** | **Fixable** | **Not Fixable**.
5. Map to live form exactly:

| Internal | Main analysis | Validity required | Duplicate analysis |
|----------|---------------|-------------------|--------------------|
| Valid as-is | Valid as-is | Valid-as-is | Valid-as-is |
| Fixable | Fixable | Fixable | Fixable |
| Not Fixable | Invalid/Not Fixable | Invalid | Invalid/Not Fixable |

6. Handle Valid as-is / Fixable / Not Fixable as analysis-only paths (Templates A/B/C remain in the Expert Reference; Fixable fields describe theoretical corrections only).
7. Put the full paste-ready platform answers block **in the chat**. Do not create separate output files.

---

## Reviewer Mode Workflow

Procedure: **`.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc`**.

1. Independently inspect task first → `sentinel_reviewer_audit.md`.
2. Read submitter analysis (do not invent it).
3. Verify every claim; inspect corrected bundle when one was supplied by the platform submitter (separate from this Cursor read-only submitter workflow).
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

- **A Valid as-is** — duplicate Task Analysis fields; validity confirmations; select “More than 10 fail-to-pass tests in the test suite” only when true for the original task; validation evidence from inspection/logs; difficulty; comments; user-provided times.
- **B Fixable** — components/issue checkboxes including exact **“Less than 10 fail-to-pass tests in the test suite”** only when count < 10; numbered issues with theoretical fixes; Files Changed = None; no corrected-task claims; times.
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

Keep mapping in the internal audit; keep platform notes concise. Maps must not trigger task edits.

---

## Environment and Repository Safety

Inspect freely. Submitter Mode must **not** modify the supplied task.

Never:

- Edit tracked source in `environment/repo/`
- Place golden solution on agent paths
- Modify existing regression / p2p tests
- Delete history
- Use live internet inside task runtime
- Add unrelated source changes
- Silently change PR scope
- Remove `network_mode` / `allowed_hosts` from the supplied task
- Rename patches, clean packaging, or regenerate patches in the supplied task
- Create a corrected ZIP

Git hygiene findings are report-only in Submitter Mode. Do not perform Git cleanup against the original task.

---

## Command Execution and Evidence

Distinguish: **Inspected** / **Inferred** / **Executed** / **Confirmed by supplied logs**.

Default Submitter Mode: document and logic analysis. Do not run commands that change the original task.

When a command may alter files, Git state, generated caches or build outputs:

- Do not run it against the original extracted task.
- Mark the corresponding validation as not executed.

If the user later explicitly requests execution, use a disposable copy and preserve the original unchanged.

Do not claim Docker builds, oracle pass, or NOP fail unless verified by supplied logs or an isolated disposable copy. Source PR browsing may occur outside the task runtime.

---

## Platform Evaluation Follow-Up

When Static / Difficulty / Oracle / Quality reports are provided:

1. Read every cited defect.
2. Map to file and rule.
3. Decide if feedback is correct.
4. Record findings and update platform answers as needed.
5. Do **not** modify the supplied task automatically.
6. Do not dismiss borderline test scores (including “3 with reservations”).
7. Advise keeping Send to Reviewer unchecked while iterating — never claim a platform click you did not perform.
8. **Runtime note:** in-app platform checks have a **five-minute** runtime limit. If full agent evaluation needs longer, iterate with Send to Reviewer unchecked and use supplied logs or isolated disposable validation. Do not claim a platform run completed if the platform stopped because of its runtime limit.
9. Prepare concise reviewer-facing notes based on the original task.

---

## Writing Rules (Active)

Plain evidence-based language; cite files/tests/logs; no generic praise; no hallucinated commands; no major/minor labels unless the live form asks; never mix role templates; never claim task edits that did not occur.

---

## Cross-File Consistency Map

| Topic | Source of truth |
|-------|-----------------|
| Policy, principles, permissions, packaging, evals | `.cursor/rules/Review_Guidelines.mdc` |
| Complete read-only submitter ZIP → form-answer workflow | `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` |
| Checklists, matrices, limits, Templates A–C, field mapping | `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` |
| Reviewer stages, outcomes, categories, Templates D–F | `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` |
| Mode routing, discovery, evidence, output files | `CLAUDE.md` |

Consistency requirements: Ultra submitter/reviewer verdicts; Harbor current artifacts; f2p operational rule; PR expand-only (theoretical for submitter analysis); no tracked-source edits; no p2p mutation; `golden.patch` canonical naming (report-only); Reject = max revisions; local-exec role split; legacy labelled only; internal audit ≠ platform answer; exact live-form verdict mapping (Invalid vs Not Fixable labels); Cursor Submitter Mode never modifies the supplied task.

---

## Active Rules Explicitly Removed

Not active defaults (legacy appendix only if useful):

- “Review is document and logic only” as a ban on all execution (isolated disposable copies remain allowed when explicitly requested)
- Mandatory `/mnt/d/Sentinel/` or `*_harborized`
- `init_state.patch` as primary current patch
- Valid/Invalid as only submitter assessment
- Accept/Reject as only reviewer outcome
- Only four metadata fields matter
- Always paste all submitter information
- Always output old Submission Error Categories
- Treating exactly 10 f2p as automatically Fixable
- Treating 11 as the official minimum instead of the preferred practical target
- Auto-select task root by modification time alone
- Mode selection from an isolated keyword
- Submitter Mode may edit the supplied task / produce a corrected ZIP
- Fixable assessment means apply corrections in-workspace
- `sentinel_changes.md` as evidence that task files were changed

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
