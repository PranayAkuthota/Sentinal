#!/usr/bin/env python3
"""Build retrospective judge_prediction.json from /tmp backtest trees + P-011 triage.

Marked source: \"retrospective backtest\" — never treat as at-upload predictions.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation"))
import judge_prep as jp  # noqa: E402

PRED_DIR = ROOT / "knowledge" / "judge_feedback" / "predictions"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Semantic CONFIRMED sets from the fixed prep map (P-011), not raw weak_link piles.
# Artifacts are for citation matching (file/symbol/assertion), not exact wording.
CASES = {
    "d41a2c3a-d176-41fe-a1b4-930ed2a85152_submission": {
        "prep_out": Path("/tmp/jp_backtest2/out_case1_fresh"),
        "predicted_verdict": "DISCUSS",
        "predicted_axes": {
            "prescriptiveness": 2.3,
            "test_coverage": 3.3,
            "test_faithfulness": 2.8,
        },
        "confirmed_overreach": [
            {
                "id": "A22",
                "artifacts": ["count", "ENABLE_GNUABI", "guards", "weak_check"],
                "assertion_text": "assert count >= 4",
            },
            {
                "id": "A24",
                "artifacts": ["count", "ENABLE_GNUABI", "guards", "weak_check"],
                "assertion_text": "assert count >= 3",
            },
            {
                "id": "A37",
                "artifacts": ["printf", "__attribute__", "mkmasked_gnuabi", "weak_alias"],
                "assertion_text": "printf EXPORT CONST __attribute__",
            },
        ],
        "confirmed_gaps": [],
        "packaging_hard_cap": False,
        "operational_bar_3_5": "REFUSE_PACKAGE",
        "notes": "Retrospective from /tmp/jp_backtest2/out_case1_fresh + P-011 triage (weak_check floors).",
    },
    "eb599683-21e8-49a0-badd-207636178abc_submission": {
        "prep_out": Path("/tmp/jp_backtest2/out_case2_fresh"),
        "predicted_verdict": "REMOVE",
        "predicted_axes": {
            "test_faithfulness": 2.0,
            "packaging": 1.0,
        },
        "confirmed_overreach": [
            {
                "id": "A6",
                "artifacts": ["CellMap", "cell_map", "out_shape"],
                "assertion_text": "assert cell_map.out_shape == (len(lines_y) - 1, len(lines_x) - 1)",
            },
            {
                "id": "A14",
                "artifacts": ["tolerance", "nearest.max"],
                "assertion_text": "assert nearest.max() <= tolerance",
            },
            {
                "id": "A28",
                "artifacts": ["len(decoded)", "frame count"],
                "assertion_text": "assert len(decoded) == 4",
            },
            {
                "id": "A41",
                "artifacts": ["tolerance", "np.abs"],
                "assertion_text": "assert np.abs(...).max() <= 8",
            },
        ],
        "confirmed_gaps": [
            {
                "id": "R19",
                "artifacts": ["ValueError", "Unsupported output format"],
                "text": "Unsupported output format raises ValueError matching Unsupported output format",
            },
            {
                "id": "R16",
                "artifacts": ["dependencies", "third-party"],
                "text": "must not add third-party dependencies",
            },
        ],
        "packaging_hard_cap": True,
        "packaging_artifacts": [".python-version", "python-version", "base_commit_sha"],
        "operational_bar_3_5": "REFUSE_PACKAGE",
        "notes": (
            "Retrospective from /tmp/jp_backtest2/out_case2_fresh. A6 CellMap is weak_link "
            "(FIX) and CONFIRMED overreach. Packaging hard-cap on .python-version."
        ),
    },
}


def build_prediction(task: str, spec: dict) -> dict:
    prep_path = spec["prep_out"] / "judge_prep.json"
    if not prep_path.is_file():
        raise SystemExit(f"missing {prep_path} — regenerate backtest prep first")
    prep_fp = jp.file_sha256(prep_path)
    prep = json.loads(prep_path.read_text())
    pack = bool((prep.get("packaging") or {}).get("hard_cap"))
    if "packaging_hard_cap" in spec:
        pack = bool(spec["packaging_hard_cap"])

    axes = {k: None for k in (
        "realism", "clarity", "self_containedness", "prescriptiveness",
        "test_coverage", "test_faithfulness", "spec_faithfulness",
        "no_gaming", "robustness", "packaging",
    )}
    for k, v in (spec.get("predicted_axes") or {}).items():
        axes[k] = v

    conf_o = spec["confirmed_overreach"]
    conf_g = spec["confirmed_gaps"]
    return {
        "schema_version": 1,
        "task_name": task,
        "predicted_at": NOW,
        "prep_fingerprint": prep_fp,
        "predicted_verdict": spec["predicted_verdict"],
        "predicted_axes": axes,
        "axes_source": "retrospective_rehearsal",
        "confirmed_overreach": [x["id"] for x in conf_o],
        "confirmed_overreach_detail": conf_o,
        "confirmed_gaps": [x["id"] for x in conf_g],
        "confirmed_gap_detail": conf_g,
        "packaging_hard_cap": pack,
        "packaging_artifacts": list(spec.get("packaging_artifacts") or []),
        "operational_bar_3_5": spec.get("operational_bar_3_5"),
        "source": "retrospective backtest",
        "notes": spec.get("notes"),
    }


def main() -> None:
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    for task, spec in CASES.items():
        pred = build_prediction(task, spec)
        path = PRED_DIR / f"{task}.json"
        path.write_text(json.dumps(pred, indent=2) + "\n", encoding="utf-8")
        # local mirror (gitignored task_outputs)
        mirror_dir = ROOT / "task_outputs" / task
        if mirror_dir.is_dir():
            (mirror_dir / "judge_prediction.json").write_text(
                json.dumps(pred, indent=2) + "\n", encoding="utf-8"
            )
        print(f"WROTE {path}")
        print(f"  confirmed_overreach={pred['confirmed_overreach']} pack={pred['packaging_hard_cap']}")


if __name__ == "__main__":
    main()
