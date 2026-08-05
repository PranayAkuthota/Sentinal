# Project Sentinel — Cursor Orchestration Controller

**Last updated:** July 22, 2026 (Sentinel Ultra)

This file is the **workflow router and automation controller** for Project Sentinel in Cursor. It decides which rules and workflows apply. It does **not** duplicate every policy detail from the `.mdc` files.

| File | Authority |
|------|-----------|
| `Review_Guidelines.mdc` | Authoritative **policy** |
| `Sentinel_Expert_Contributor_Reference.mdc` | **Quick reference** |
| `Sentinel_Reviewer_Step_by_Step.mdc` | **Reviewer procedure** |
| `CLAUDE.md` (this file) | **Orchestration / automation** |

Never confuse **submitter** and **reviewer** roles, verdicts, or output templates.

---

## Rule Precedence

When rules conflict, follow the higher-priority source:

1. Current user instruction
2. Current Sentinel Ultra documentation (July 22, 2026)
3. `Review_Guidelines.mdc`
4. Role-specific workflow file (`Sentinel_Reviewer_Step_by_Step.mdc` for reviewers; submitter steps in this file + Guidelines)
5. `Sentinel_Expert_Contributor_Reference.mdc`
6. Legacy compatibility rules

**Never** allow a March 2026 legacy rule to override a July 22, 2026 Sentinel Ultra rule.

---

## Operating Modes

### Submitter Mode

Activate when the user says any of:

- submission / submitter
- fix this task / correct the bundle / prepare upload
- Valid as-is / Fixable / Not Fixable
- run eval preparation
- update instruction, tests, or oracle

### Reviewer Mode

Activate when the user says any of:

- review submission / reviewer
- Accept / Needs Revision / Reject
- verify submitter / rebuttal / quality score

### Rule Maintenance Mode

Activate when the user asks to update the four Sentinel rule files (`Review_Guidelines.mdc`, `Sentinel_Expert_Contributor_Reference.mdc`, `Sentinel_Reviewer_Step_by_Step.mdc`, `CLAUDE.md`).

### Read-Only Audit Mode

Activate when the user asks only for analysis and explicitly asks **not** to modify files.

If mode is still unclear after inspecting the request and available platform data, ask **one** concise question:

`Are you acting as the submitter or reviewer for this task?`

Do **not** ask when the answer is already clear.

---

## Task Root Discovery

Do **not** require tasks to live only at `/mnt/d/Sentinel/`. That path is an **optional default example** only.

Automation must:

1. Start from the current workspace.
2. Ignore:
   - `.cursor/`
   - `.git/` outside the task repository
   - `legacy_backup/`
   - Rule files (`.mdc`, this `CLAUDE.md`)
   - Prompt files
   - Previous generated reports (`sentinel_*.md`, `sentinel_*.txt`, `review_answer.txt`)
3. Search for a directory containing:
   - `instruction.md`
   - `task.toml`
   - `environment/`
   - `solution/`
   - `tests/`
4. Also support packages where these files are inside `task/`.
5. Locate a sibling `runs/` folder when available.
6. Do **not** require `_harborized` in the directory name.
7. If multiple possible task roots exist, list them and select the one most recently provided or explicitly named by the user.
8. **Never** modify a task until the intended root is unambiguous.

---

## Task Format Detection

### Current Sentinel Ultra signals

- `solution/golden.patch`
- `environment/problem_statement.md`
- `tests/config.json`
- `tests/grade.py`
- Current `task.toml` schema and resource structure
- Current Valid as-is / Fixable / Not Fixable form

### Legacy signals

- `solution/init_state.patch`
- Reverse-patch solve process
- `tests/files/`
- Old Valid or Invalid form
- Old Accept or Reject-only review form
- Missing current packaging files

### Hybrid task

When current and legacy artifacts are mixed:

- Use **current rules** as default.
- Read legacy artifacts for context.
- Do **not** assume absence of an old optional artifact is a defect.
- Identify files that must be renamed or added for current upload.
- Explain the compatibility decision in the report.

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
13. Count f2p tests.
14. Check regression coverage.
15. Check Quality Check failure patterns.
16. Inspect runs.
17. Check Git hygiene.
18. Check package hygiene.
19. Decide assessment.
20. Perform role-allowed corrections or produce review findings.
21. Validate.
22. Produce platform-ready answer.

---

## Auto-Read File List

Read when present:

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

Rules:

- `golden.patch` is **current**.
- `solution.patch` should be flagged for **rename** to `golden.patch`.
- `init_state.patch` is **legacy**.
- Missing optional legacy files are **not** automatic defects.
- Missing current required files must be evaluated as a **current packaging issue**.

Also skim `environment/repo/` as needed for scope, and identify license when the platform asks.

---

## Submitter Mode Workflow

Policy details: `Review_Guidelines.mdc`. Checklists: `Sentinel_Expert_Contributor_Reference.mdc`.

### Step 1: Independent task assessment

Inspect everything **before changing anything**.

Prepare:

- Requirements list
- Instruction issues
- Test coverage map
- Test faithfulness map
- Oracle issues
- Environment issues
- Git issues
- Packaging issues
- PR-scope comparison
- f2p count
- Current likely verdict

### Step 2: Choose assessment

Use only:

- **Valid as-is**
- **Fixable**
- **Not Fixable**

### Step 3: Valid as-is behavior

Do **not** rewrite the task.

Required actions:

- Confirm at least **10** f2p tests.
- Confirm instruction and tests align (both directions).
- Confirm oracle alignment.
- Confirm no leakage.
- Confirm PR relevance.
- Run or provide evidence of offline Docker build.
- Run oracle validation.
- Run NOP validation.
- Confirm reward `1.0` for oracle.
- Confirm reward `0.0` for NOP.
- Confirm p2p behavior.
- Prepare platform answers.

Do **not** claim a command passed unless it was actually executed or a supplied log proves it.

### Step 4: Fixable behavior

Allowed files may be corrected according to `Review_Guidelines.mdc`.

Before editing:

- Create a task-specific backup or Git checkpoint **outside** the tracked task repo.
- Record original file hashes or diffs.
- Do **not** edit tracked source files in `environment/repo/`.
- Do **not** modify pre-existing regression / p2p tests.

Correct as needed:

- Instruction
- Problem statement (exact copy of final instruction)
- New tests via `tests.patch`
- Test runner (`test.sh`)
- Test config (`config.json`)
- Grading (`grade.py`)
- Oracle (`solve.sh`, `golden.patch`)
- Limited Dockerfile issues
- Metadata
- Git metadata
- Packaging

Keep instruction, tests, and oracle synchronized. Expand PR scope only when allowed; never reduce or replace it.

After editing:

- Confirm `instruction.md` equals `problem_statement.md`.
- Confirm `tests.patch` applies.
- Confirm at least 10 f2p tests.
- Run available validation.
- Prepare changed-files list.
- Explain every change and reason.
- Explain PR expansion or write `NA`.
- Prepare corrected flat ZIP (contents of `task/` only; no `runs/`; no outer `task/` wrapper).

### Step 5: Not Fixable behavior

Do **not** rewrite the task into a different problem.

Provide:

- Exact Not Fixable category
- Specific evidence
- Why allowed corrections are insufficient
- Why fixing it would require prohibited PR-scope change or disallowed environment repair

---

## Reviewer Mode Workflow

Detailed procedure: **`Sentinel_Reviewer_Step_by_Step.mdc`**. Follow that file’s stages.

Cursor must:

1. Independently inspect the task first.
2. Then read submitter analysis.
3. Verify every claim.
4. Inspect the corrected bundle.
5. Review comments and rebuttal.
6. Choose **Accept**, **Needs Revision**, or **Reject**.
7. Use **Reject only after maximum revisions**.
8. Assign current error categories.
9. Assign Submission Quality Score (1–5).
10. Produce evidence-based notes.

Reviewer local execution is **optional**.

Do **not** ask the user to paste submitter data when it already exists in files, platform exports, screenshots, or prior messages.

When submitter data is absent:

- Complete the independent task audit first.
- Clearly list the missing submitter fields.
- Ask only for the missing material needed for the final comparison.
- Do **not** invent submitter answers.

---

## Automated Test Mapping

For every task, generate an internal table:

```text
Requirement ID
Instruction text
Expected observable behavior
Test file
Test ID
Assertion
Coverage status
Faithfulness status
Risk
```

Required checks:

- Every requirement mapped
- Every assertion justified
- At least 10 f2p tests
- Original-failure regression test
- CLI invocation where required
- Deterministic behavior
- No silent skip
- No fail-open
- No existence-only pass
- No agent-controlled coverage
- No hidden format requirement
- No source text matching
- No broad exception swallowing
- No verifier-only constants
- No circular expected values
- No hidden golden comparison

The internal mapping may be detailed. The final platform note should remain concise.

---

## Environment and Repository Safety

Cursor may inspect all relevant files.

In Submitter Mode it may run validation commands and make **allowed** fixes.

It must **never**:

- Directly edit tracked source files in `environment/repo/`
- Add the golden solution to agent paths
- Modify existing regression tests
- Delete source history without first determining the correct base
- Use live internet inside task runtime
- Add unrelated source changes
- Silently change PR scope

Git cleanup is allowed only for:

- Removing remotes
- Removing stray refs
- Removing filter drivers
- Cleaning reflog
- Garbage collection
- Restoring clean working tree
- Aligning base commit metadata to shipped HEAD
- Reducing `.git` size
- Regenerating `tests.patch` against the correct base

Record every Git operation.

---

## Command Execution and Evidence

- Do not state “Docker builds” unless it was run successfully or supported by supplied logs.
- Do not state “oracle passes” unless verified.
- Do not state “NOP fails correctly” unless verified.
- Distinguish: **Inspected** / **Inferred** / **Executed** / **Confirmed by supplied logs**.
- Preserve command output needed to support findings.
- Stop destructive commands when paths are uncertain.
- Prefer read-only inspection before edits.
- Do not run external network commands inside the task container.
- Source PR browsing may be done outside the task runtime when tools are available.

---

## Platform Evaluation Follow-Up

When the user provides Static / Difficulty / Oracle / Quality Check reports, Cursor must:

1. Read every cited defect.
2. Map it to the exact file and rule.
3. Decide whether the feedback is correct.
4. Correct the task when appropriate (Submitter Mode).
5. Do **not** dismiss a borderline test score (including “3 with reservations”).
6. Keep Send to Reviewer unchecked during iteration (advise the user; do not claim a platform click).
7. Update the changed-files log.
8. Reassess PR scope after each expansion.
9. Prepare a concise response for the reviewer.

Cursor cannot actually click platform buttons unless the environment provides that control. **Never** claim a platform action was performed when it was not.

---

## Standardized Output Files

Create these only when performing an actual task (not during rule-file maintenance):

### Submitter Mode

- `sentinel_submitter_audit.md`
- `sentinel_changes.md`
- `sentinel_platform_answers.txt`
- Corrected task ZIP when requested and technically possible

### Reviewer Mode

- `sentinel_reviewer_audit.md`
- `review_answer.txt`

### Read-Only Audit Mode

- `sentinel_audit.md`

Do **not** place these files inside `environment/repo/`.

Do **not** include generated reports inside the final task ZIP.

---

## Current Reviewer Output Template

Default for Sentinel Ultra (`review_answer.txt`):

```text
Reviewer Verdict
[Accept / Needs Revision / Reject]

Independent Task Assessment
[Assessment]

Error Categories
[Categories or None]

Reviewer Note
[Evidence-based note]

PR Scope Assessment
[Result]

Instruction and Test Alignment
[Result]

Oracle Assessment
[Result]

Environment and Packaging Assessment
[Result]

Rebuttal Acknowledgement
[Result]

Submission Quality Score
[1–5]

Review Time
[Minutes]
```

Use old Valid/Invalid and Submission Error Categories output only in **Legacy Mode** or when the user explicitly requests the old form.

---

## Current Submitter Output Template

```text
Task Analysis
[Valid as-is / Fixable / Not Fixable]

Issues Found
[Numbered issues with evidence]

Fixability
[Explanation]

Files Changed
[Path, change, reason]

PR Scope Changes
[Explanation or NA]

Validation
[Commands run and results]

Difficulty Explanation
[Specific technical explanation]

Comments for Reviewer
[Important context]

Initial Review Time
[Minutes]

Rewrite Time
[Minutes when applicable]

Total Submission Time
[Minutes]
```

Do **not** fabricate time values. Ask the user or use values explicitly provided.

---

## Writing Rules (Active)

- Plain and natural language
- Specific evidence (files, tests, functions, logs, paths)
- No generic “everything looks good”
- Distinguish inspected vs executed validation
- Do not hallucinate command results
- Do not overstate certainty
- Do not use major/minor issue labels unless the live platform asks for them
- Keep final platform notes concise; keep internal audits detailed
- Never mix submitter and reviewer templates

---

## Cross-File Consistency Map

Do not duplicate full contents of the other files. Route instead:

| Topic | Source of truth |
|-------|-----------------|
| Policy, principles, edit permissions, packaging, evals | `Review_Guidelines.mdc` |
| Checklists, matrices, quick limits, Do Not Confuse | `Sentinel_Expert_Contributor_Reference.mdc` |
| Reviewer stages, outcomes, error categories, quality score, rebuttal | `Sentinel_Reviewer_Step_by_Step.mdc` |
| Mode routing, discovery, automation, evidence rules, output files | `CLAUDE.md` (this file) |

### Consistency requirements (all four files)

- Submitter verdicts: **Valid as-is / Fixable / Not Fixable**
- Reviewer verdicts: **Accept / Needs Revision / Reject** (Reject = max revisions only)
- Current Harbor: `golden.patch`, `problem_statement.md`, `config.json`, `grade.py`
- Legacy terms labelled as compatibility only
- Local execution: submitter Valid as-is **required**; Fixable recommended; reviewer **optional**
- f2p: at least **10** (ideally 10–20)
- PR scope: expand allowed; reduce/replace forbidden
- Never edit tracked repo source; never modify existing regression tests
- `init_state.patch` is **not** current canonical format
- Old platform output is **not** the current default

---

## Active Rules Explicitly Removed

These must **not** appear as active defaults (legacy appendix only if useful):

- “Review is document and logic only”
- “Do not run Harbor, Docker, oracle or NOP”
- Mandatory `/mnt/d/Sentinel/`
- Mandatory `*_harborized`
- `init_state.patch` as the primary current patch
- Valid or Invalid as the only task assessment
- Accept or Reject as the only reviewer outcome
- Only four metadata fields can matter
- Always ask the user to paste all submitter information
- Always output the old Submission Error Categories
- Save only one old-format `review_answer.txt`
- Treat two runs as a universal current package rule

---

## Legacy Sentinel Compatibility

**Not current default.** Use only when the task or platform explicitly requires it. Current policy always wins on conflict.

### Reverse `init_state.patch`

Older packages often used a reverse patch: `solve.sh` ran `patch -p1 -R < init_state.patch`.

- `+` lines in `init_state.patch` = removed from solution (broken state)
- `-` lines = added by solution (the fix)

Missing `init_state.patch` alone is not a defect. Current uploads use forward `golden.patch`.

### Historical run-count note

Older packages often had several trials per model. Newer batches (e.g. from April 28 2026) may have fewer (often two — one per model). Smaller newer sets are expected, not automatically defective.

Always inspect all failing trials where practical and at least one passing trial when available.

### Old license identification

Check `LICENSE` / README / upstream via `source`. Platform list often includes GPL/LGPL/AGPL/MPL/EPL/CPL/OSL/RPL variants plus Other. MIT/Apache/BSD/ISC/Unlicense/CC0 commonly map to Other when not listed.

### Old category reference

Fix · Feature · Refactor · Documentation · Build · Performance · Chore (plus Ultra free-form labels when present).

### Old submission-quality categories (legacy forms)

Low-Detail / Surface-Level Analysis · Technical Misconception · Inadequate Evidence / Verification · Logical Inconsistency · Superficial Evaluation of Tests · Unverified AI Output · Other · None of the above

### Old Valid/Invalid + Accept/Reject output (legacy only)

```text
Reviewer Feedback

As a reviewer, do you believe the task to be valid or invalid?
[Valid / Invalid]

Do you accept or reject the submission?
[Accept / Reject]

Accept/Reject Notes:
[1 short evidence-based paragraph]

Submission Error Categories
[as shown on the old form]
```

### Simple legacy writing reminders

- 8th-grade plain English when the old form expects it
- Cite real files and tests
- Do not invent Invalid-issue details for the submitter
- Translate old Valid/Invalid answers into Ultra terms before deciding current reviewer outcomes
