# Judge validation strategy

**Last updated:** 2026-08-05

## Stop measuring discrimination against history

Every package under `task_outputs/` (and the historical `work/*` trees used in early
S10.5 backtests) was either:

1. **Bounced** by the live Agent Judge, or
2. **Corrected** by the pre-2026-08-05 pipeline, which had **no** judge triage.

None is a known-accepted / Valid-as-is negative sample. There is currently **no**
Valid-as-is package in local history.

In particular, `ctrl_965`'s own recorded defect is that the instruction copies fixture
constants and file paths — which is exactly what rehearsal CONFIRMED on it. Its three
confirmed overreach rows are most likely **true positives**, not evidence that semantic
triage lacks discriminating power.

**Conclusion:** discrimination cannot be measured retrospectively against these packages.
Further tuning of link heuristics, triage prompts, or thresholds against this corpus
would be fitting to noise. Do not run “control vs bounced” tables as calibration evidence.

Re-open retrospective discrimination only if we later obtain a **genuinely Valid-as-is /
platform-accepted** task with an intact upload tree.

## Forward validation (the only honest calibration)

Before each real upload, write a prediction. After the platform returns, record the
actual Judge result and join it. Aggregate over time — three or four real tasks beat any
amount of retro-fitting.

### 1. Prediction at upload time

Written by packaging / explicit `write_judge_prediction.py`:

`task_outputs/<task>/judge_prediction.json`

```json
{
  "schema_version": 1,
  "task_name": "<task>",
  "predicted_at": "<iso8601>",
  "prep_fingerprint": "<sha256 of judge_prep.json>",
  "predicted_verdict": "OK|DISCUSS|REMOVE",
  "predicted_axes": {
    "realism": 0.0,
    "clarity": 0.0,
    "self_containedness": 0.0,
    "prescriptiveness": 0.0,
    "test_coverage": 0.0,
    "test_faithfulness": 0.0,
    "spec_faithfulness": 0.0,
    "no_gaming": 0.0,
    "robustness": 0.0,
    "packaging": 0.0
  },
  "confirmed_overreach": ["A…"],
  "confirmed_gaps": ["R…"],
  "packaging_hard_cap": false,
  "operational_bar_3_5": "PASS|REFUSE_PACKAGE"
}
```

Axes come from `judge_rehearsal.json` when present (reconciled scores); otherwise omit
or leave nulls and set `axes_source: "missing_rehearsal"`.

### 2. Actual result after platform returns

```bash
python3 automation/capture_judge_feedback.py --task-name TASK \
  --verdict OK|DISCUSS|REMOVE \
  --axes-json '{"test_coverage":3.0,...}' \
  --cited-overreach 'CellMap.out_shape;exact threshold' \
  --cited-gaps '…' \
  --notes '…'
```

Writes `task_outputs/<task>/judge_feedback.json` and appends a join row to
`task_outputs/_judge_calibration_ledger.jsonl`.

### 3. Aggregate stats

```bash
python3 automation/judge_stats.py
```

Reports over the ledger:

- Per-axis predicted vs actual delta (mean absolute error when both present)
- Confirmed-overreach **precision** — fraction of our confirmed A# / notes that the
  judge also cited (substring / id match when available)
- Confirmed-overreach **recall** — fraction of judge citations we had confirmed
- Verdict agreement (predicted vs actual OK/DISCUSS/REMOVE)

Calibrate prompts and map rules from these rates only — never from historical backtests.
