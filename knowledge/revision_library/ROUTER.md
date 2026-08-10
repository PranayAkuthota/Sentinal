# Revision router

Use this **first** when a platform or reviewer response arrives.
A stage that **did not run** is not evidence about the task.

## 0. Setup (pitfalls — not cases)

| Check | If failed → |
|-------|-------------|
| Platform ZIP SHA matches local mirror (when mirror exists) | `pitfalls/11_stale_platform_zip.md` |
| Docker oracle 1.0 + NOP 0.0 actually recorded (not invented) | `pitfalls/18_submit_without_docker_oracle_nop.md` |
| Rehearsal OK but live DISCUSS on blocking axes | Note only — still fix **citations**. `pitfalls/12_rehearsal_optimism.md` |

Never route a DISCUSS/REMOVE **to a pitfall as the defect to edit**.

## 1. Which stage blocked?

| Signal | Stage | Next |
|--------|-------|------|
| **`Blocked at the agentic judge. Not run: difficulty screen…`** / `discuss (coverage_gap\|overreach)` / REMOVE + Difficulty not run | **Agentic Judge** (main block) | → **`cases/09_judge_first_misread.md` FIRST**, then §2 |
| Any Agent Judge axis **≤ 3.5** (esp. `test_coverage` / `test_faithfulness`) | Same | Case 09 gate: must reach **≥ 3.5** on all axes before re-upload |
| Judge OK + free-text Needs Revision | **Manual Reviewer** | §3 |
| `Difficulty FAIL EASY` **after** Judge OK | **Difficulty** | → `cases/03_difficulty_fail_easy_after_judge_ok.md` |

If Difficulty or Oracle **did not run**, that is **not** a pass and **not** an infra outage.

## 2. After Case 09 — map each Judge citation

| If you see… | Case |
|-------------|------|
| Ungraded / mock-pass / weak sample / `coverage_gap` | `04_test_coverage_gap.md` |
| Undeclared API / private access / literal tokens / overreach | `05_test_faithfulness_overreach.md` ⚠↔06 |
| Q9/Q10 / how-to / path / suite-leak | `06_q9_q10_instruction_overprescription.md` ⚠↔05 |
| Golden mismatch | `07_oracle_golden_mismatch.md` |
| `solve.sh` reverse-apply | `08_non_idempotent_solve_sh.md` |
| Irregular `pass_at_k` / medium≠hard | `10_difficulty_metadata_lies.md` |
| Fail-open / silent skip | `13_…` / `14_…` |
| Vague under-spec | `16_clarity_self_contained.md` |

Coverage vs faithfulness: **opposite fixes — do not merge.**  
Done only when **every** Judge axis is **≥ 3.5**.

## 3. Manual Reviewer → case

| Note shape | Case |
|------------|------|
| Stash/WIP solution; deleted tracked trees; `environment/repo` edited; bad `origin/HEAD` | `02_editing_boundary.md` |
| Network blocks / grade.py / Files Changed / difficulty_explanation | `01_manual_reviewer_packaging_harness.md` |
| Else same citation shapes as §2 | 04 / 05 / 06 / 07 / 08 |

## 4. After choosing a case

1. Diagnose before edits.
2. One fix direction per defect (see case Evidence tags).
3. Faithfulness ↔ Q9/Q10: cross-check Cases 05 and 06.
4. Append Instances when the round closes.
