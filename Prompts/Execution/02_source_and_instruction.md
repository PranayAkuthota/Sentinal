# 02 — Source & Instruction

**Canonical daily prompt · Stages S3–S4**  
**Chat mode:** fresh conversation preferred. Read prior handoff first.

## Purpose
Align task with source PR/commit/issue; expert-review instruction quality.  
**No verdict. No file edits. No packaging.**

## Gate (must pass)
```bash
python3 automation/checkpoint_ready.py --task-name TASK --next 02
```

## Required inputs
- `01__handoff.md` (`status: complete`)
- Source URL from metadata / `task.toml`
- `extracted_original/instruction.md` + `environment/problem_statement.md`
- Network for `gh`/GitHub API when available (else mark Not verified)

## Read first
- `workflows/stages/S3_source_alignment.md`, `S4_instruction_review.md`
- `Prompts/modules/source_alignment.md`, `instruction_review.md`
- `validation/checklists/semantic_review.md` (source + instruction bullets)
- `Review_Guidelines.mdc` — Source PR Scope + Instruction / Clarity (reference only)
- Patterns: P-006 (trim untested claims)

## Do
1. Fetch PR/commit/issue (title, files, base). Do not invent PR contents if offline.
2. Compare `base_commit_sha` vs shipped repo HEAD; map upstream fix ↔ `golden.patch` / `solution.patch`; tests ↔ `tests.patch` / f2p.
3. Scope check: preserved / naturally expandable / replaced. **Never plan to replace the PR with a different feature.**
4. Read instruction + problem_statement; note byte sync or Fixable sync debt.
5. Assess: clarity, solvability contracts, leakage (PR/SHA/hidden tests/spoilers), over-prescription, LLM tone, realism.
6. Number instruction issues with Fixable vs Invalid **lean signals** — proposed rewrites only. Each issue = short human paragraph (what + why + file cite).
7. List public contracts tests will likely enforce (schemas, flags, paths) so **03** can check coverage.
8. Write `02__handoff.md` (`status: complete|blocked|partial`).

## Do not
- Edit `working_copy/` or sync problem_statement yet
- Set the three verdict fields
- Touch `work/task ready_to_submit/`
- Add unrelated requirements to “save” a weak task

## Expected outputs
- Source one-liner + scope map
- Instruction issue list (or “none material”) + sync status
- `02__handoff.md`

## Done when
- Source reviewed or explicitly Not verified
- Base/HEAD + scope risk stated
- Issue list ready for **03/04**; no mutations

## Failure
| Symptom | Action |
|---------|--------|
| No network / gh | Continue from local patches; mark source Not verified |
| Missing instruction | `blocked` |
| Only solvable by replacing PR scope | Flag Invalid lean for **04**; do not set verdict here |

## Next
`checkpoint_ready.py --task-name TASK --next 03` → open **03**.
