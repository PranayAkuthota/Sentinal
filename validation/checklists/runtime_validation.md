# Runtime validation checklist

Evidence classes: Inspected / Inferred / Executed / Confirmed by logs / Not verified.  
Never invent Executed results.

## Before run
- [ ] Docker available (or explicitly mark `not_run`)
- [ ] Correct task root (`working_copy/` for Fixable)
- [ ] Hygiene already applied on Fixable (Harbor network blocks ensured, compose `network_mode="none"` stripped if present, grade.py)

## Commands
- [ ] `python3 automation/local_oracle_nop.py --task-name TASK --mode both`
- [ ] Logs under `work/<TASK>/session/validation_logs/`
- [ ] `record-validation` for docker_build / oracle / nop with paths + rewards

## Expectations
- [ ] Valid-as-is: oracle reward `1.0`, NOP `0.0` (Executed required)
- [ ] Fixable: strongly recommended same evidence before upload
- [ ] Invalid: do not claim passing corrected oracle

## After run
- [ ] Failures diagnosed (tests vs env vs oracle)
- [ ] Timeouts within policy caps; bumped only with justification
- [ ] No fabricated `reward.txt`
