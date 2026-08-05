# 03 — Spec Alignment (Tests, Oracle, Env)

**Canonical daily prompt · Stages S5–S7**  
**Chat mode:** one analysis pass covering verifier + oracle (static) + env/metadata.

## Purpose
Build coverage ↔ faithfulness picture; static oracle review; env/metadata/git class.  
**No verdict. No content mutations. No packaging. No oracle reward run** (runtime = **05**).

## Gate (must pass)
```bash
python3 automation/checkpoint_ready.py --task-name TASK --next 03
```

## Required inputs
- `01__handoff.md`, `02__handoff.md` (including **02** PRELIMINARY REQUIREMENT LIST)
- `tests/config.json`, `tests/tests.patch`, instruction
- `solution/solve.sh`, `golden.patch` or legacy `solution.patch`
- `task.toml`, `environment/Dockerfile`, audit git notes

## Read first
- `workflows/stages/S5_verifier_alignment.md`, `S6_oracle_faithfulness.md`, `S7_environment_metadata.md`
- `Prompts/modules/verifier_alignment.md`, `oracle_review.md`
- `validation/checklists/semantic_review.md`, `structural_preflight.md`
- Operational Patterns: grading / tests.patch / hygiene
- Patterns: P-001, P-002, P-004 (10 vs more-than-10), P-007 (verifier timeout), P-008 (no SkipTest soft-pass), P-011 (overreach / faithfulness ≥3.5 on revisions)

## Do

### A. Verifier (S5)
1. Reuse **01** structural facts; re-audit only if stale.
2. **Diagnostic `judge-prep`** (not a gate — map even when unrelated FIXABLEs are open):

```bash
python3 automation/sentinel_submitter.py judge-prep --task-name TASK
# → task_outputs/<TASK>/judge_prep.{md,json}
```

   Read `judge_prep.md`. Report: coverage gaps; `unlinked_lexically` and `weak_link` candidates;
   UNRESOLVED count; whether the LOW CONFIDENCE flag is set. Cross-check against **02**’s human
   requirement list — any requirement the human found that the extractor missed is a matcher
   problem worth noting. At this stage these are **CANDIDATES**, not confirmed defects; P-011
   triage happens in the rehearsal at **05**. Do **not** treat `prep_passed=false` as a verdict.
   If judge-prep **hard-stops** (PH1 / V0 / missing config), that is itself a strong Fixable
   lean for **04** — record it and continue with the rest of **03**.
3. Account for `allow_extra_failures` + ungraded `+def test_*` (P-002).
4. State meaningful f2p count: guideline ≥10; live “More than 10” only if ≥11 (P-004).
5. Propose Fixable test/config actions as **notes only**.

### B. Oracle (S6)
6. Naming: `golden.patch` vs legacy `solution.patch`.
7. Disposable apply check if needed — never mutate `extracted_original/`.
8. Faithfulness vs instruction; gaming (fixture hardcoding, hidden goldens, network oracle).
9. Do **not** run full oracle reward here.

### C. Environment & metadata (S7)
10. Dockerfile offline realism; Fixable vs Not Fixable env class.
11. Resources/timeouts/gpus; note Harbor `network_mode` / `allowed_hosts` (ensure correct blocks later on Fixable in **05**; do not strip).
12. Git hygiene summary; whether env alone forces Invalid.
13. Compiler-build suites: flag low `verifier.timeout_sec` (P-007).

14. Write one `03__handoff.md` with sections A/B/C in human EC prose (files, tests, counts).
15. Do not run preflight/package or write `work/task ready_to_submit/`.

## Do not
- Edit `working_copy/`
- Invent grading results
- Claim apply-safe when git-apply failed
- Set Public/Internal/Duplicate
- Treat judge-prep candidates as confirmed overreach/gaps (that is **05** rehearsal)

## Expected outputs
- `task_outputs/<TASK>/judge_prep.md` (+ `.json`)
- Gap / candidate counts; LOW CONFIDENCE yes/no; hard-stop yes/no
- Coverage + faithfulness summaries (from prep + human cross-check)
- Oracle OK / Fixable / Invalid lean
- Env/metadata + git signals
- `03__handoff.md`

## Done when
- Diagnostic judge-prep run (or hard-stop recorded); f2p adequacy stated
- Oracle + env recommendations ready for **04**
- No mutations; no ZIP

## Failure
| Symptom | Action |
|---------|--------|
| Corrupt tests.patch / missing config | Document; do not invent grading |
| judge-prep hard-stop | Record Fixable lean for **04**; finish B/C |
| Unrecoverable env | Document for Invalid at **04** |
| git-apply fails | Fixable lean if regenerable; else blocker for **04** |

## Next
`checkpoint_ready.py --task-name TASK --next 04` → open **04**.
