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
- `task_outputs/<task>/judge_rehearsal.md` + **`judge_rehearsal.json`** (from `Prompts/modules/judge_rehearsal.md`)
- Workflow state: `judge_prep_completed`, `judge_prep_passed`, blockers / accept-risk

## Validation
### Hard stop (map not built)
- PH1 / tests.patch does not apply
- V0 / config.json unparseable or missing
- `instruction.md` or `tests/tests.patch` missing

### Prep soft blockers (`prep_passed` false — map still built)
- Open static-check FIXABLE (unrelated packaging debt — banner in §0)
- Auto-REMOVE cites from static-check (silent_skip, fail_open, …; static overreach ids)
- UNDECIDED allow_extra rows
- Packaging hard-cap hits
- Invalidated decisions (fingerprint mismatch) — blocker **16h**

### Prep does **not** block on (FIX B)
- Lexical `no_graded_link` / `unlinked_lexically` — candidates only for rehearsal

### Rehearsal / preflight blockers
- Missing or unparseable `judge_rehearsal.json`
- `judge_prep_fingerprint` mismatch (stale rehearsal)
- Untagged prep candidates (rehearsal must triage every lexical row)
- **CONFIRMED_GAP** / **CONFIRMED_OVERREACH** (P-011 bucket c)
- **UNDECIDED** triage rows
- `--accept-risk "<reason>"` demotes the above (recorded; surfaced in reviewer comments)

## Failure
Missing static-check report; HARD STOP inputs; treating LOW CONFIDENCE maps as green;
treating lexical candidates as confirmed without P-011; filler f2p to chase coverage;
inventing Judge scores without reading `judge_prep.json`.

## Recovery
Fix hard-stop inputs; re-run `judge-prep`; complete two-pass rehearsal + triage JSON;
only then `preflight`. Discrimination for calibration uses **CONFIRMED** counts, not
lexical candidate piles.

## Automation
```bash
python3 automation/sentinel_submitter.py static-check --task-name TASK
python3 automation/sentinel_submitter.py judge-prep --task-name TASK
# then Cursor: Prompts/modules/judge_rehearsal.md → judge_rehearsal.md + .json
python3 automation/sentinel_submitter.py preflight --task-name TASK
# optional: --accept-risk "…"
```

## Backtest / control note

**Do not** calibrate against historical bounced packages. Forward validation only —
`docs/VALIDATION_STRATEGY.md` (`judge_prediction.json` → `capture_judge_feedback.py` →
`judge_stats.py`).
