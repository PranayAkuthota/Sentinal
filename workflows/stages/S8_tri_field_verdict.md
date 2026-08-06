# S8 — Tri-Field Verdict

## Purpose
Expert-only assignment of the three live platform fields: Public Main Analysis, Internal Validity, Duplicate Analysis. All three must share the same semantic branch (tri-field agreement).

## Inputs
- Complete S2–S7 findings
- Live platform label set (follow live form wording)
- Structural signals from audit (never sufficient alone)

## Outputs
- Recorded via `set-verdicts` with evidence-based reason
- Branch choice: Valid as-is / Fixable / Invalid/Not Fixable (map to live labels exactly)
- Handoff stating Public == Internal == Duplicate (same semantic branch)

## Validation
- Public, Internal, and Duplicate agree (`all_validity_fields_agree`)
- Internal reason matches the agreed label (no “internally invalid” prose when Internal is Fixable)
- Verdicts justified by concrete files/tests/logs — not vibes
- Scripts did **not** choose the fields
- Valid as-is only when no rewrite needed and local oracle/NOP will be required

## Failure
Tri-field disagreement (including Public/Duplicate=Fixable with Internal=Invalid); verdict before semantic review; automation-assigned labels; mixing submitter and reviewer outcome names.

## Recovery
Re-run `set-verdicts` with corrected expert judgement. Do not start S9 mutations until this stage is clean.

## Automation
`set-verdicts` records only. Never auto-suggest the three fields.
