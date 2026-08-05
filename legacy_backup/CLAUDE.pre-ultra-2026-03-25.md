# Project Sentinel — Claude Code Rules

This workspace is used for **Project Sentinel** task reviews. Each task is extracted from a zip into `/mnt/d/Sentinel/`. The review is a **document and logic review only** — do NOT run Harbor, Docker, oracle scripts, or NOP checks locally.

---

## 1. Review Workflow

When the user says "review" or starts a new task:

### STEP 1: Auto-read the task (no user input needed)

1. Scan `/mnt/d/Sentinel/` for the submission folder (ignore `.cursor/`, `CLAUDE.md`, prompt files, `review_answer.txt`)
2. Find the `*_harborized/` directory inside it
3. Automatically read ALL of these:
   - `task/instruction.md`
   - `task/task.toml`
   - `task/solution/solve.sh`
   - `task/solution/init_state.patch` (if exists)
   - `task/tests/test.sh`
   - `task/tests/tests.patch` (if exists)
   - All files under `task/tests/files/`
   - `task/environment/Dockerfile`
   - Every `runs/*/*/result.json` (aggregate results)
   - For ALL failing trials (reward 0): read `verifier/test-stdout.txt` to find patterns
   - For at least one passing trial (reward 1): read `verifier/test-stdout.txt` to confirm
4. Skim `task/environment/repo/` as needed based on instruction scope
5. Fetch the source PR URL from `task.toml` to cross-check scope
6. Identify the open-source license (see Section 8)

### STEP 1.5: Independent review (before asking for submitter data)

Do the FULL review checklist (Section 4) independently BEFORE seeing the submitter's answers. Note:

**A. Instruction quality:**
- Is instruction.md clear with measurable success criteria?
- Any vague, contradictory, or LLM-generated sounding language?
- Any missing context that would prevent an agent from solving it?

**B. Source PR cross-check:**
- Fetch/open the PR URL from task.toml source field
- Does instruction match the PR scope and intent? Over-scoped? Under-scoped?
- Does category match the PR type?
- Does the URL resolve to the right repo/PR?

**C. Environment check:**
- Is the Dockerfile sufficient for the stack? Dependencies present?
- Do paths in Dockerfile match repo structure?
- Are timeouts plausible given runs/ results?

**D. Solution verification:**
- Does solve.sh implement what instruction.md describes?
- Is init_state.patch consistent with solve.sh?
- Does the patch match the PR changes?

**E. Test coverage mapping:**
- Map EVERY instruction requirement to a specific test
- Flag any requirement that has NO test coverage
- Check assertions match expected outcomes
- Tests must NOT enforce behavior the instruction does not ask for (no unrequested checks — testing for unrequired things is unfair to the agent)

**F. Agent runs analysis:**
- Check ALL failing trials not just one per model
- Look for patterns: same error? timeouts? misreads?
- Do pass rates match task.toml accuracy fields?
- For batches from April 28 2026 onward: expect 2 runs (one per model). Older batches may have more (e.g. five per model). A smaller set is expected for newer batches and is NOT a mistake.

**G. Metadata verification:**

IMPORTANT: Per the latest guidelines, ONLY these metadata items can make a task Invalid:
- `source` URL (must resolve to the correct PR)
- `[verifier] timeout_sec`
- `[agent] timeout_sec`
- `[environment] build_timeout_sec`

All other fields (category, difficulty, language, tags, accuracy, author, etc.) should still be checked and noted as observations, but being wrong on those is NOT a valid reason to mark the task Invalid.

Checklist:
- Does `source` URL resolve to the right repo/PR?
- Are the three timeouts plausible given runs/ evidence?
- Does category match PR type? (note only, not an invalidity cause)
- Does difficulty match complexity and run results? (note only)
- Does language match actual code? (note only)
- Are tags relevant? 3-6 present? (note only)
- Do accuracy fields match actual run pass rates? (note only)

**H. License identification:**
- Identify the open-source license for the upstream project (see Section 8 for where to look and the list of license options)
- Record which license applies so you can compare against the submitter's selection later

Note ALL findings including things the submitter might have missed.

### STEP 2: Ask for submitter's data

After completing independent review, ask the user to paste the submitter's data:

```
Original Directory Name:
Category:
Difficulty:
Task Tags:
Languages:
Open-source License:
Metadata: (paste task.toml or say "same as file")

SUBMITTER'S ANSWERS:

Is the task valid or invalid?

Were the instructions sufficient?

Did the instructions appear correct?

Is every requirement properly tested?

Are all test requirements in the instructions?

Did the instructions appear LLM-generated?

Is the implementation novel or unique?

General Observations:
(paste submitter's full observations)
```

### STEP 3: Ask for Invalid task details (IF submitter says Invalid)

If the submitter marked the task as **Invalid**, ALSO ask the user to paste:

```
INVALID TASK DETAILS:

What issue(s) did you find? (categories selected):

Issue descriptions (numbered):
(paste all Issue 1, Issue 2, etc. with category, description, fixable/not, how to fix)

Are ALL issues resolvable?
```

**Do NOT skip this step.** Do NOT generate these answers yourself. Wait for the user to provide the submitter's actual issue details before proceeding.

### STEP 4: Compare and deliver final answer

Once ALL submitter data is received:

1. Compare submitter's findings against your independent review from Step 1.5
2. For each submitter issue: confirm it holds against the actual files
3. Check if submitter MISSED any issues you found independently
4. Check if submitter's issue categories are accurate
5. Check if submitter's metadata claims match the files
6. Compare platform-provided Languages field against task.toml language
7. Compare submitter's selected open-source license against what you found in environment/repo/ or upstream
8. Evaluate the submitter's write-up against the Submission Error Categories in Section 9
9. Determine your independent verdict (may differ from submitter)
10. Determine Accept/Reject based on whether submitter's work is complete and accurate
11. **Save the final answer to `/mnt/d/Sentinel/review_answer.txt`**

**The review_answer.txt must contain ALL of the following:**

#### For ALL tasks (Valid or Invalid):

```
Reviewer Feedback

As a reviewer, do you believe the task to be valid or invalid?
[Valid / Invalid]

Do you accept or reject the submission?
[Accept / Reject]

Accept/Reject Notes:
[1 paragraph — see writing rules below]

Submission Error Categories
[X or blank] None of the above

[ ] Low-Detail / Surface-Level Analysis
[ ] Technical Misconception
[ ] Inadequate Evidence / Verification
[ ] Logical Inconsistency
[ ] Superficial Evaluation of Tests
[ ] Unverified AI Output
[ ] Other

Category notes:
[ONLY include this section if "Other" is checked. Otherwise omit it entirely.
1 short paragraph explaining what "Other" covers, same writing rules as Accept/Reject Notes]
```

#### ADDITIONALLY for Invalid tasks, include BEFORE the reviewer feedback:

```
Questions on Invalid Tasks

What issue(s) did you find with the task/components?
[list the issue categories]

Describe each issue in detail:
[numbered issues with category, description, fixable/not, how to fix]

Are these issue(s) resolvable?
[Yes / No]
```

---

## 2. Writing Rules for Accept/Reject Notes

- Exactly **1 short paragraph**
- **Simple 8th-grade English** — basic plain easy to read
- **100% humanized** writing
- **NO LLM artifacts**: no emdashes (—), minimize commas, no colons, no semicolons
- Reference specific things verified from the task files (file names, function names, test names, line numbers, patch details)
- Include what you verified: instruction, PR cross-check, Dockerfile, solution, tests, runs, metadata, license
- State why you agree or disagree with the submitter
- Flag anything the submitter missed even if verdict stays the same
- End with your clear final verdict (Valid/Invalid + Accept/Reject)
- Do NOT use "minor issues" or "major issues" qualifiers. The platform only accepts Valid or Invalid.

---

## 3. Task Directory Structure

```
<submission_id>/
  <directory_name>_harborized/
    task/
      instruction.md                 # Problem statement given to the agent
      task.toml                      # Metadata: difficulty, category, tags, source, timeouts
      environment/
        Dockerfile                   # Container build
        repo/                        # Full source repository
      solution/
        solve.sh                     # Oracle solution
        init_state.patch             # Gold patch (reverse = solution). OPTIONAL
      tests/
        test.sh                      # Verifier: runs tests, writes reward
        tests.patch                  # Optional test coverage patch
        files/                       # Optional test files copied into repo
    runs/
      <agent_name>/
        <timestamp>/
          result.json                # Aggregate pass rate
          harborized__<id>/          # Individual trial
            verifier/
              reward.txt             # 0 or 1
              test-stdout.txt        # Full test output — KEY for failures
```

### 3.1 Agent run count by batch

Older task packages often included several traces per model (for example five per model). For task batches starting April 28 2026 each zip includes two agent runs — one trace per model. That smaller set is expected and is not a mistake or incomplete download.

---

## 4. Review Checklist (internal, do not output separately)

Go through EVERY item. This drives the final notes but is NOT shown to the user as a separate output.

### 4.1 Instruction
- Clear problem statement with measurable success criteria?
- Vagueness, contradictions, missing context, LLM language?
- Over-scoped or under-scoped vs the PR?

### 4.2 Source PR
- Fetch the PR URL and verify it matches
- Does instruction match PR intent and scope?
- Does category match PR type?

### 4.3 Environment
- Dockerfile sufficient for the stack?
- Dependencies present or installed by test.sh?
- Paths match repo structure?
- Timeouts plausible vs runs?

### 4.4 Solution
- Does solve.sh implement what instruction.md describes?
- init_state.patch consistent with solve.sh?
- Patch matches PR changes in spirit? Extra files in the patch are OK as long as the solution still satisfies the instruction and tests (per guidelines: "Task solutions are often larger than strictly necessary or include extra functionality not asked for in the instruction. This is okay as long as the solution does what the instruction requires and tests enforce that.")
- Missing init_state.patch alone is NOT a defect

### 4.5 Tests
- test.sh invokes framework correctly and writes reward?
- Map EVERY instruction requirement to a test
- Tests cover ALL requirements?
- Assertions match expected outcomes?
- Coverage gap: instruction says X must hold but no test checks X → issue
- No unrequested checks: tests must NOT enforce behavior the instruction does not ask for. Testing for unrequired things is unfair to the agent.

### 4.6 Agent runs
- Check ALL failing trials for patterns not just one
- Aggregate pass rates match task.toml accuracy fields?
- Consistent timeouts or misreads → ambiguity signal?
- Do failures support or contradict the submitter's claims?
- For batches from April 28 2026: expect 2 runs (one per model). Older batches may have more.

### 4.7 Metadata

Validity-affecting fields (ONLY these can cause Invalid verdict):
- `source` URL correct and resolves to the right PR
- `[verifier] timeout_sec` plausible
- `[agent] timeout_sec` plausible
- `[environment] build_timeout_sec` plausible

Observational fields (note but DO NOT mark Invalid for these):
- Category matches PR type
- Difficulty matches complexity and run results
- Language matches actual code
- Platform Languages field matches task.toml
- Tags relevant and 3-6 present
- Accuracy fields match run pass rates
- Author, time estimates, pr_created_at / pr_merged_at sanity

### 4.8 License
- Check `environment/repo/LICENSE`, `LICENSE.md`, `LICENCE`, `COPYING`, or similar at repo root
- Check `environment/repo/README.md` for license mentions
- If unclear in the snapshot open the source URL in task.toml and check upstream
- Record which license applies and compare against the submitter's selection (see Section 8 for the full list of license options)

### 4.9 Compare to submitter
- Agree with verdict?
- Did submitter miss any issues you found?
- Are their observations specific and verifiable?
- Are numbered issues (if Invalid) accurate and well-categorized?
- Does submitter's selected license match what you found?

---

## 5. Verdicts

### Task assessment
Only two choices are accepted by the platform:
- **Valid:** Everything reads as coherent. Instruction, solution, tests, and runs line up. No substantive issues. Oracle solutions that are larger than strictly necessary are OK.
- **Invalid:** Real problem with instruction, solution, tests, environment, or one of the validity-affecting metadata items (`source`, verifier/agent/environment timeouts). Do NOT split into "minor" or "major" — the platform no longer offers that split.

Do NOT mark Invalid purely for: wrong category, wrong difficulty, wrong language field, wrong tags, wrong accuracy numbers, missing init_state.patch, oracle patch touching more files than the PR, or things that would only be caught by running Harbor/NOP/Docker locally.

### Submission verdict
- **Accept:** Submitter's findings are real, specific, and verifiable AND the write-up is adequate AND no key findings were missed.
- **Reject:** Submitter missed key findings, descriptions are vague, verdict contradicted by files, numbered issues absent/wrong, or mischaracterizes the task.

---

## 6. Issue Categories

Use these when filing numbered issues on an Invalid task:

| Category | Examples |
|----------|----------|
| Instruction specification | Vague/contradictory instruction. Success criteria don't match tests. Instruction and PR description disagree. |
| Metadata issues | Wrong/missing `source` URL, or implausible verifier/agent/environment timeouts. NOTE: only these fields count for validity; wrong category/difficulty/tags/language do NOT. |
| Environment setup | Dockerfile gaps, missing deps, wrong paths vs repo structure, implausible build timeout. |
| Solution implementation (logic) | solve.sh or patches inconsistent with instruction or PR. init_state.patch conflicts with solve.sh. Missing init_state.patch alone is NOT a reason. |
| Unit test setup | Wrong paths, missing reward write, dependency gaps in test.sh. |
| Unit test scope | Required behavior not tested. Wrong assertions. Only a subset of requirements covered. Tests enforce behavior the instruction never asks for. |
| Other | Task already satisfied without change. Agent timeout too low for fair evaluation given runs. |

### 6.1 Additional examples of common invalid scenarios

- Wording that could be clearer or more explicit without hiding a real requirement
- Small inconsistencies between the instruction and the PR description (cosmetic or easy to resolve)
- A behavior the oracle implements and tests cover but the instruction does not state clearly enough for an agent to infer
- Verifier timeouts set too low for agents to run properly
- An agent can skip explicit instructions and still pass all tests with full reward
- Tests are missing or too weak or assert the wrong behavior
- Environment or harness problems prevent the oracle (or a correct solution) from passing when it should
- Tests conflict with the instruction or are out of scope or do not match the requirements
- The task is trivially solvable without the intended fix and fixing it would need substantial rework

---

## 7. Understanding init_state.patch

Reverse diff:
- Lines added (`+`) = code REMOVED from the solution (broken state)
- Lines removed (`-`) = code ADDED by the solution (the fix)
- solve.sh runs `patch -p1 -R < init_state.patch`

---

## 8. License Identification

For every task identify the open-source license of the upstream project. Check in this order:

1. `environment/repo/LICENSE`, `LICENSE.md`, `LICENCE`, `COPYING`, or similar file at the repo root
2. `environment/repo/README.md` (or similar readme) — often names the license or points to a license file
3. If unclear in the snapshot open the source URL from `task.toml` and check the same locations upstream

### License options (as listed on the platform form)

- GNU General Public License v2.0 (GPL-2.0)
- GNU General Public License v3.0 (GPL-3.0)
- GNU Affero General Public License v3.0 (AGPL-3.0)
- GNU Lesser General Public License v2.1 (LGPL-2.1)
- GNU Lesser General Public License v3.0 (LGPL-3.0)
- Mozilla Public License 2.0 (MPL-2.0)
- Eclipse Public License 1.0 (EPL-1.0)
- Eclipse Public License 2.0 (EPL-2.0)
- Common Public License 1.0 (CPL-1.0)
- Open Software License 3.0 (OSL-3.0)
- Reciprocal Public License 1.5 (RPL-1.5)
- Other — when more than one license applies, when there is no license, or when the license is not listed above

### Common licenses NOT on the list (use "Other" for these)

MIT, Apache 2.0, BSD 2-Clause, BSD 3-Clause, ISC, Unlicense, CC0, and any other license not explicitly listed above all map to "Other".

---

## 8.1 Category Values Reference

| Category | Description |
|----------|-------------|
| Fix | Fixing known bugs or faults within the codebase. |
| Feature | Introducing new internal or user-oriented features. |
| Refactor | Restructuring the existing codebase with a focus on maintainability. |
| Documentation | Updates to documentation or comments (READMEs, typo fixes, API docs). |
| Build | Changes to build configurations. |
| Performance | Improving performance (e.g. reducing memory consumption). |
| Chore | Project-wide housekeeping (dependency bumps, version increments, cleanup). |

---

## 9. Submission Error Categories (per-submission evaluation)

These labels judge the QUALITY of the submitter's review write-up, not the task itself. They are separate from Section 6 Issue Categories. Evaluate them every time, for both Accept and Reject. Check all that apply, otherwise check "None of the above". Adjudicators can overwrite them.

A submission generally should be **rejected** if one or more of these are present. Borderline signals that are not severe can be noted in "Category notes" without being checked.

| Category | Apply when |
|----------|------------|
| Low-Detail / Surface-Level Analysis | Notes are vague or generic, no specific code walkthrough, no proof the submitter manually inspected the files. Generic phrases like "everything looks good" with no file names, function names, test counts, or line references. |
| Technical Misconception | Misreads logic or intent. Misses a real discrepancy between instruction and patches. Describes a backend, test, or patch behavior incorrectly. Claims a test enforces something it does not. |
| Inadequate Evidence / Verification | Technical claims made with no cited logs, file paths, run outputs, or code snippets. Asserts the solution works without pointing at init_state.patch, solve.sh, or actual test output. |
| Logical Inconsistency | Valid/Invalid verdict contradicts the written notes. Miscalculates severity (e.g. says issue is minor but it blocks all runs). Invalid verdict with no numbered issues, or Valid verdict while describing a clear defect. |
| Superficial Evaluation of Tests | Fails to notice that tests are shallow. Does not catch tests that only grep for patterns while the instruction requires functional behavior the patterns cannot enforce. Does not catch missing assertions, missing coverage, or tests that always pass. |
| Unverified AI Output | Blatant AI markers. Technical hallucinations, generic filler summaries that ignore task-specific flaws, questionable writing style, emoji use, or sentences that do not parse as real engineering observations. |
| Other | Anything else that would justify rejection but does not fit the boxes above. Must be explained in Category notes. |
| None of the above | Submission has no meaningful defects in the above categories. Use this on Accept submissions and on well-documented Reject submissions that simply missed a task-level issue (where the Accept/Reject notes handle the disagreement). |

Evaluation rules:
- Only write a "Category notes" paragraph when the "Other" box is checked. In that case, explain what "Other" covers. Same writing rules as Accept/Reject Notes (1 short paragraph, 8th-grade English, no emdashes, minimize commas, no colons, no semicolons).
- If "Other" is not checked, omit the "Category notes" section entirely from review_answer.txt. The reasoning for the verdict lives in Accept/Reject Notes.
- When flagging any category (including Other), cite specific phrases from the submitter's observations that triggered it.
- Mild AI phrasing alone is not enough for Unverified AI Output if the rest of the write-up is grounded in real files and numbers. Call it out in Category notes instead.
- Missing an explicit note that grep-pattern tests are shallow is not automatically Superficial Evaluation of Tests when the task type is a standard Sentinel pattern-check shape. Only flag if the tests genuinely fail to enforce what the instruction requires.
- The Submission Error Categories do not override the task's Valid/Invalid verdict. A task can be Valid while the submission is Reject because of these categories.

---

## 10. Common Mistakes (Avoid)

- Rejecting solely on missing init_state.patch
- Rejecting because init_state.patch is larger than the PR diff (oracle being bigger than needed is OK)
- Marking Invalid for wrong category, wrong difficulty, wrong tags, wrong language field, or wrong accuracy numbers (those are note-only; only `source` + verifier/agent/environment timeouts can cause Invalid)
- Accepting vague issue descriptions
- Ignoring runs/ data
- Running Harbor/Docker/NOP locally or basing validity on whether the oracle passes on your own machine
- Disagreeing without citing specific files
- Writing LLM-sounding output in final notes
- Writing "Invalid with minor issues" or "Invalid with major issues" — platform only accepts Valid or Invalid
- Generating Invalid task issue details yourself instead of asking the user
- Only checking one failing trial instead of all of them
- Not cross-checking the source PR
- Not reading the Dockerfile
- Not verifying metadata against actual task files
- Not looking for issues the submitter missed
- Not comparing platform Languages field against task.toml language
- Forgetting the Submission Error Categories block in review_answer.txt (always include the checkboxes, even on Accept)
- Adding a "Category notes" section when "Other" is not checked (it is only required for the Other case)
- Checking "Other" without writing a Category notes paragraph that explains what it covers
- Not identifying the open-source license or skipping the license comparison against the submitter's selection
- Treating 2 runs in newer batches (from April 28 2026) as an error — that is the expected count
- Failing to check that tests do not enforce unrequested behavior (no unrequested checks rule)

---

## 11. Adjudication

Some tasks may be sent to an adjudicator. The adjudicator has the final say on whether the task is Valid or Invalid and on whether a submission should be Accepted or Rejected. Adjudicators also assess the quality of the reviewer's feedback. Reviewers may be offboarded from the project if their feedback does not meet Snorkel standards.
