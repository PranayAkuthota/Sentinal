# S8 — Tri-Field Verdict

## Purpose
Expert-only assignment of the three live platform fields: Public Main Analysis, Internal Validity, Duplicate Analysis. Public must match Duplicate.

## Inputs
- Complete S2–S7 findings
- Live platform label set (follow live form wording)
- Structural signals from audit (never sufficient alone)

## Outputs
- Recorded via `set-verdicts` with evidence-based reason
- Branch choice: Valid as-is / Fixable / Invalid/Not Fixable (map to live labels exactly)
- Handoff stating Public == Duplicate

## Validation
- Public Main Analysis matches Duplicate Analysis
- Verdicts justified by concrete files/tests/logs — not vibes
- Scripts did **not** choose the fields
- Valid as-is only when no rewrite needed and local oracle/NOP will be required

## Failure
Public ≠ Duplicate; verdict before semantic review; automation-assigned labels; mixing submitter and reviewer outcome names.

## Recovery
Re-run `set-verdicts` with corrected expert judgement. Do not start S9 mutations until this stage is clean.

## Automation
`set-verdicts` records only. Never auto-suggest the three fields.
