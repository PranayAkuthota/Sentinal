# Pattern index

| ID | Title | Status | Source |
|----|-------|--------|--------|
| P-001 | tests.patch must pass git apply (not patch-only) | approved | framework |
| P-002 | allow_extra_failures hides ungraded patch tests | approved | framework |
| P-003 | Fixable packaging: ensure Harbor network blocks (+ compose cleanup); ensure grade.py (superseded-and-corrected 2026-08-05; earlier strip guidance was wrong) | superseded-and-corrected | framework |
| P-004 | Exactly 10 f2p ≠ live “more than 10” (≥11) | approved | policy cross-ref |
| P-005 | Prefer absolute paths + --task-name with multi-session work/ | approved | framework |
| P-006 | Prefer trimming untested instruction claims over thin f2p filler | approved | promoted |
| P-007 | Compiler-build verifiers often need higher verifier.timeout_sec | approved | promoted |
| P-008 | Hard-fail missing build tools instead of SkipTest | approved | promoted |
| P-009 | Mode-only dirty trees are Fixable via reset not Invalid | approved | promoted |
| P-010 | Agent Judge before Difficulty; revise Judge first (4 trials/model, ≤50% bar) | approved | platform update 2026-08-04 |
| P-011 | Agent Judge overreach: sync instruction↔tests; target axis scores ≥3.5 before Difficulty | approved | platform update 2026-08-04 |
| P-012 | Faithfulness fixture-dump flips Q9/Q10 — state CONTRACT not fixture INSTANCE | approved | 0cf2e9a3 round1→2 live |
| P-013 | GPT is the binding judge on both test axes | approved | six-revision batch 2026-08-06 |

Add new rows via `python3 automation/promote_learning.py pattern …` after human review of `knowledge/proposals/`.
