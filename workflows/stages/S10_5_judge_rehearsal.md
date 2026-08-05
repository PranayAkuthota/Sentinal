# S10.5 — Judge rehearsal (local Quality Check simulation)

## Purpose
Build the deterministic bipartite instruction↔assertion map and packaging hard-cap
sweep **before** packaging, then run a single-model two-pass rehearsal of the platform
Agent Judge so we do not upload tasks the judge will bounce.

## Inputs
- Task root (Fixable → `working_copy/`; Valid-as-is → frozen original root)
- `task_outputs/<task>/static_check_report.json` (must exist; run `static-check` first)
- Optional human file `task_outputs/<task>/judge_prep_decisions.json` (never overwritten)

## Outputs
- `task_outputs/<task>/judge_prep.md` + `judge_prep.json`
- `task_outputs/<task>/judge_rehearsal.md` (from `Prompts/modules/judge_rehearsal.md`)
- Workflow state: `judge_prep_completed`, `judge_prep_passed`, blockers / accept-risk

## Validation
### Hard stop (map not built)
- PH1 / tests.patch does not apply
- V0 / config.json unparseable or missing
- `instruction.md` or `tests/tests.patch` missing

### Soft (map still built; prep_passed false)
- Open static-check FIXABLE (unrelated packaging debt — banner in §0)
- Unexplained coverage gaps / graded overreach / UNDECIDED allow_extra rows
- Auto-REMOVE cites from static-check
- Packaging hard-cap hits (ZIP junk not tracked at base)
- Invalidated decisions (fingerprint mismatch) — blocker **16h**

### Preflight
Refuses `ready_to_package` on unexplained GAP / OVERREACH / UNDECIDED / auto-REMOVE /
invalidated decisions unless `--accept-risk "<reason>"` (recorded in workflow_state;
surfaced in reviewer comments). Distinct from per-item `judge_prep_decisions.json`.

## Failure
Missing static-check report; HARD STOP inputs; treating LOW CONFIDENCE maps as green;
filler f2p to chase coverage; inventing Judge scores without reading `judge_prep.json`.

## Recovery
Fix hard-stop inputs; explain or edit gaps/overreach via decisions file (with fingerprint);
re-run `judge-prep`; complete two-pass rehearsal; only then `preflight`.

## Automation
```bash
python3 automation/sentinel_submitter.py static-check --task-name TASK
python3 automation/sentinel_submitter.py judge-prep --task-name TASK
# then Cursor: Prompts/modules/judge_rehearsal.md → judge_rehearsal.md
python3 automation/sentinel_submitter.py preflight --task-name TASK
# optional: --accept-risk "…"
```

## Backtest / control note

No Valid-as-is package exists in current local history. Discrimination backtests used weak
Fixable `working_copy` controls. Re-run Case-3 control against the first genuine
Valid-as-is intake before treating gap-pile comparisons as calibration evidence.
