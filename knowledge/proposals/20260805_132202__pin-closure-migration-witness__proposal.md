# Learning proposal (pending human review)

- Generated: 20260805_132202 UTC
- Task ref: `pin-closure-migration-witness` (do not promote UUID into pattern titles)
- Branch recorded: Invalid/Not Fixable
- Structural f2p count: None

## Candidate reusable patterns

1. **Early authenticity stop on metadata↔ZIP mismatch.** If platform `source_pr_url` / Original Directory Name / languages / tags describe a different product than the ZIP `instruction.md` + `task.toml`, treat as authenticity / PR-scope Invalid lean before investing in Harbor Fixable packaging.
2. **Non-Harbor layout + claimed Harbor Ultra source → Invalid, not Fixable conversion.** Missing `environment/repo`, `golden.patch`, `tests.patch`, `config.json`, `grade.py`, `problem_statement.md` cannot be “fixed” by inventing an OSS repo for an unrelated synthetic payload.
3. **Invalid branch runtime honesty.** Do not invent oracle/NOP rewards. Cancelling a long Docker pull is acceptable when the authenticity blocker is already proven and the Harbor harness lacks `tests/config.json`.

## Automation opportunities (deterministic only)

- Intake/prepare warning when platform_input.txt `source_pr_url` host/path tokens do not appear in ZIP `task.toml` / instruction (flag only; no auto-verdict).
- `local_oracle_nop.py`: fail fast with clear message when `tests/config.json` missing instead of starting Docker build first.

## Suggested failure catalog entries

- category: authenticity / source mismatch  
  symptom: Platform paste cites PR A; ZIP content is unrelated language/stack with no matching source fields.  
  recovery: Mark Invalid/Not Fixable (PR scope needs to be changed or reduced); package evidence; do not build corrected ZIP.

- category: packaging dialect  
  symptom: TB-style pytest+solve.sh package presented under Ultra Harbor metadata.  
  recovery: Invalid unless a real Harbor Ultra package for the claimed PR is provided; do not retrofit synthetic desks into fake `environment/repo`.

## Agent notes (redacted)

Platform paste described a different OSS PR than the ZIP payload. Early authenticity stop; Invalid category PR scope. Harbor oracle/NOP needs config.json — do not invent rewards on Invalid when cancelling unrelated docker builds.

## Workflow state warnings (structural)

```
[]
```

---

**Promotion rule:** Human merges accepted items into `knowledge/patterns/` or `knowledge/failures/`.
Never auto-edit `.cursor/rules/Review_Guidelines.mdc`.
