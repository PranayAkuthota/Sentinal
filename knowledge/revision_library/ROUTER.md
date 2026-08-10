# Revision router

Use this **first** when a platform or reviewer response arrives.
A stage that **did not run** is not evidence about the task.

## 0. Setup (pitfalls — not cases)

Before diagnosing the task, check process:

| Check | If failed → |
|-------|-------------|
| Platform ZIP SHA matches local mirror (when mirror exists) | `pitfalls/11_stale_platform_zip.md` |
| Docker oracle 1.0 + NOP 0.0 actually recorded (not invented) | `pitfalls/18_submit_without_docker_oracle_nop.md` |
| After bounce: rehearsal predicted OK but live DISCUSS on blocking axes | Note only — still route the **citations** via cases below; do not “fix optimism.” See `pitfalls/12_rehearsal_optimism.md` |

Never route a DISCUSS/REMOVE **to a pitfall as the defect to edit**.

## 1. Which stage blocked?

| Signal | Stage | Ran? | Next |
|--------|-------|------|------|
| `Blocked at agentic judge` / DISCUSS / REMOVE; Difficulty/Oracle “not run” | **Agentic Judge** | Judge yes; later stages no | §2 |
| Judge OK (or OK with notes) **and** free-text “Needs Revision” / reviewer list | **Manual Reviewer** | Judge (and often Difficulty) already passed | §3 |
| `Difficulty FAIL EASY` / `Requires at least MEDIUM` after Judge OK | **Difficulty** | Judge yes; Difficulty failed | → `cases/03_difficulty_fail_easy_after_judge_ok.md` |
| Quality / static alone (rare in our ledger) | Quality / local | — | map wording to cases |

If Difficulty or Oracle **did not run**, do not invent their results and do not treat silence as pass.

## 2. Agentic Judge → case

Read citations / must-haves. Pick by **root cause**, not by which axis title is loudest.

| If you see… | Case |
|-------------|------|
| Ungraded requirement / mock lets stub pass / weak sample of surfaces | `04_test_coverage_gap.md` |
| Undeclared kwargs, private DOM, literal API tokens tests demand | `05_test_faithfulness_overreach.md` ⚠↔06 |
| Q9/Q10, exact keys mirroring tests, how-to, path-as-navigation, suite-leak | `06_q9_q10_instruction_overprescription.md` ⚠↔05 |
| Golden / oracle behaviour disagrees with claim | `07_oracle_golden_mismatch.md` |
| `solve.sh` reverse-apply fallback | `08_non_idempotent_solve_sh.md` |
| Irregular `pass_at_k` / medium contradicts hard (Judge still failing) | `10_difficulty_metadata_lies.md` |
| Vague “well-formed” / schema under-specified | `16_clarity_self_contained.md` |
| Fail-open / `else: pass` scans / silent skip in tests | `13_…` / `14_…` |
| Operator looking for Difficulty while Judge blocked | `09_judge_first_misread.md` |

Coverage vs faithfulness: **opposite fixes — do not merge.**

## 3. Manual Reviewer → case

Diagnosis is free-text (no per-axis panel). Split notes into buckets:

| Note shape | Case |
|------------|------|
| Stash/WIP with solution; deleted tracked trees; `environment/repo` edited; broken `origin/HEAD` | `02_editing_boundary.md` |
| Network blocks gone; grade.py; Files Changed mismatch; missing `difficulty_explanation` / os | `01_manual_reviewer_packaging_harness.md` |
| Then same as Judge for coverage / faithfulness / Q9 / oracle / solve.sh | 04 / 05 / 06 / 07 / 08 |

## 4. After choosing a case

1. Diagnose (written finding) before edits.
2. Pick **one** fix direction per defect (see case file).
3. If touching instruction for faithfulness, re-check Case 06 — and the reverse.
4. Append a dated Instances row when the round closes (Part D).
