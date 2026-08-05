# Semantic review checklist (expert only)

Scripts must not auto-pass these items.

## Source (S3)
- [ ] Source URL resolves to correct PR/commit/issue
- [ ] Task remains recognizably based on that source
- [ ] Scope not replaced; expansion (if any) is natural

## Instruction (S4)
- [ ] Observable outcomes clear; required schemas stated
- [ ] No leakage (PR/SHA/hidden tests/spoilers/verifier internals)
- [ ] Not over-prescriptive implementation walkthrough
- [ ] Human engineering voice (not robotic LLM template)
- [ ] Solvable from instruction + pinned repo

## Verifier (S5)
- [ ] Instruction → tests coverage map complete for critical behaviors
- [ ] Tests → instruction faithfulness (no arbitrary overreach)
- [ ] Meaningful f2p (not filler); ≥10; ≥11 if claiming more than 10
- [ ] At least one test reproduces the original failure class
- [ ] Deterministic; no silent skip / fail-open / agent-controlled coverage

## Oracle (S6)
- [ ] Satisfies instruction without gaming
- [ ] No fixture-only hardcoding strategy; no hidden golden reads
- [ ] Aligned with tests after any scope expansion

## Verdict (S8)
- [ ] Public == Duplicate
- [ ] Evidence-based reason recorded
- [ ] Valid-as-is / Fixable / Invalid chosen for the right reasons
