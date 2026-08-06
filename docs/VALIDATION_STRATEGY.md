# Judge validation strategy

**Last updated:** 2026-08-06

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
  --verdict DISCUSS --verdict-reason weak_check \
  --axes-json '{"prescriptiveness":2.5,"test_coverage":3.0}' \
  --must-haves Q2,Q9,Q10 \
  --citation 'quoted text||axis=test_faithfulness' \
  --notes '…'
```

Writes the canonical record to `knowledge/judge_feedback/<task>.json` (schema:
`knowledge/judge_feedback/schema.json`), mirrors `task_outputs/<task>/judge_feedback.json`,
and appends a join row to `task_outputs/_judge_calibration_ledger.jsonl`.
`prediction_ref` points at `task_outputs/<task>/judge_prediction.json` when present.

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

**Retrospective joins** (prediction `source: "retrospective backtest"` **or**
`"retrospective out-of-sample"`) are reported in a separate `judge_stats.py` section.
Precision is suppressed there: the live judge cites selectively, so an unmentioned flag
is not a false positive. Use recall on cited artifacts only.

### Out-of-sample recall — 0cf2e9a3 (2026-08-06)

First **out-of-sample** join (tools never tuned on this report), on the as-uploaded
corrected ZIP the Judge saw:

| Metric | Value |
|--------|------:|
| Semantic citation recall | **3/14 (0.21)** |
| Predicted verdict | REMOVE (matched actual) |
| Verdict driver | `silent_skip` V9 (`@pytest.mark.skipif`) — **not** the fail-open scans the Judge actually cited |

Group misses that matter for calibration:

- **Fail-open scans (0/5):** PSF `NATOM` / PDB `CRYST1` / four conf tests — V9 `fail_open`
  CLEAR. Detector only matches `except…pass/return` and `if not exists: return`, not
  `for … if/elif … else: pass` without a post-loop presence assert (~23× in that package).
  See `knowledge/failures/F-012_…`.
- **UA / NVT hidden values + comment-string parser:** hit only after body-read (assertion
  extractor keeps RHS-only `assert split_line[1] == '…'` / list-index compares).
- **`_get_*` order dump:** correctly **not** confirmed as faithfulness overreach (was
  stated in instruction); prep/rehearsal only flag **prescriptiveness**.
- Clarity / `VDWGeometricSigma` contradiction / `solve.sh` reverse-apply: miss without
  solution↔instruction cross-read.

**Do not quote eb599683’s retrospective 3/4 as the baseline.** That join was
**in-sample** (`source: "retrospective backtest"`) after the tools had already been
shaped around those citations. Prefer 0cf2e9a3’s 3/14 OOS recall when talking about
how well prep/rehearsal would have caught a novel bounce.

### Live join bias — 0cf2e9a3 round 2 (2026-08-06)

First **at-upload** prediction joined against a real platform verdict:

| Field | Predicted (`source: at_upload`) | Actual |
|-------|--------------------------------:|-------:|
| Verdict | **OK** | **DISCUSS** (`coverage_gap`) |
| `test_coverage` | 4.5 | **3.0** (Δ −1.5) |
| `test_faithfulness` | 4.5 | **3.0** (Δ −1.5; gpt scored **2**) |
| Other axes | all ≥ 4.0 | all ≥ 4.0 (MAE ~0 on clarity/self/prescriptiveness) |

Citation recall on this live join: **0/8** — rehearsal confirmed nothing that the panel
cited (defaults-subset gap, `bead_to_atom_name_dict`, UA letter pinning, Q9/Q10
fixture-shaped conf dump, mechanism/import/helper prose).

**Systematic optimism:** rehearsal axes sat at ≥ 4.0 and predicted OK while the live
panel left both blocking test axes at 3.0 (DISCUSS). Do **not** raise the ≥ 3.5 packaging
bar from this single join — record the bias and wait for more live joins before acting.

## Known limitation — strong-linked assertions (eb599683, in-sample)

In-sample retrospective recall on eb599683: **3/4** citations matched (CellMap, ValueError,
`.python-version` packaging). Useful as a regression check on already-known artifacts —
**not** as forward calibration. The unmatched class was **atypical path suffix vs decode** —
those asserts were status=`ok` (strong lexical link) and never entered P-011 triage.

Mitigation (not full triage of every linked row): `judge_prep` emits `linked_spot_check` —
a deterministic sample of `max(5, ceil(10%))` of status=`ok` faithfulness rows, with the
**seed recorded** for reproducibility. Rehearsal applies P-011 to the sample; confirmed
overreach → **`SAMPLE_HIT`** (signal to widen triage for that task). See
`Prompts/modules/judge_rehearsal.md`.
