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
- `01__handoff.md`, `02__handoff.md`
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
2. Map instruction → graded assertions (coverage gaps). Prefer promoting real patch tests into f2p over filler.
3. Map graded assertions → stated/implied requirements (faithfulness / overreach). On platform revisions, treat any assert that fails this map as a **must-fix** before re-upload (P-011); target Agent Judge axes ≥3.5.
4. Account for `allow_extra_failures` + ungraded `+def test_*` (P-002).
5. State meaningful f2p count: guideline ≥10; live “More than 10” only if ≥11 (P-004).
6. Propose Fixable test/config actions as **notes only**.

### B. Oracle (S6)
7. Naming: `golden.patch` vs legacy `solution.patch`.
8. Disposable apply check if needed — never mutate `extracted_original/`.
9. Faithfulness vs instruction; gaming (fixture hardcoding, hidden goldens, network oracle).
10. Do **not** run full oracle reward here.

### C. Environment & metadata (S7)
11. Dockerfile offline realism; Fixable vs Not Fixable env class.
12. Resources/timeouts/gpus; note Harbor `network_mode` / `allowed_hosts` (ensure correct blocks later on Fixable in **05**; do not strip).
13. Git hygiene summary; whether env alone forces Invalid.
14. Compiler-build suites: flag low `verifier.timeout_sec` (P-007).

15. Write one `03__handoff.md` with sections A/B/C in human EC prose (files, tests, counts).
16. Do not run preflight/package or write `work/task ready_to_submit/`.

## Do not
- Edit `working_copy/`
- Invent grading results
- Claim apply-safe when git-apply failed
- Set Public/Internal/Duplicate

## Expected outputs
- Coverage + faithfulness summaries
- Oracle OK / Fixable / Invalid lean
- Env/metadata + git signals
- `03__handoff.md`

## Done when
- Both maps exist (even if brief); f2p adequacy stated
- Oracle + env recommendations ready for **04**
- No mutations; no ZIP

## Failure
| Symptom | Action |
|---------|--------|
| Corrupt tests.patch / missing config | Document; do not invent grading |
| Unrecoverable env | Document for Invalid at **04** |
| git-apply fails | Fixable lean if regenerable; else blocker for **04** |

## Next
`checkpoint_ready.py --task-name TASK --next 04` → open **04**.
