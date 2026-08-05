# Execution handoff

Use `work/<task>/session/execution/NN__handoff.md` where `NN` is `01`…`06`.

```text
task_name:
checkpoint_id: 01 | 02 | 03 | 04 | 05 | 06
status: complete | blocked | partial
timestamp_utc:

## Findings
- (human EC paragraphs / short notes — anything that may paste into Snorkel later must not sound LLM-generated)

## Artifacts
-

## Evidence classes used
- Inspected / Inferred / Executed / Confirmed by supplied logs / Not verified

## Open questions
-

## Stale flags
- (what must be re-run if later stages change)

## Next checkpoint
-

## Packaging note (when relevant)
- Fixable upload ZIP (step 06 only): `work/task ready_to_submit/<task>__corrected.zip`

## Voice
- Narrative findings destined for Snorkel = normal human paragraphs (workflow §13)
```
