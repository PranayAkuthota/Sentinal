#!/usr/bin/env python3
"""Capture live Agent Judge result and join to judge_prediction.json.

Called after the platform returns (Execution 06 / post-upload). See
docs/VALIDATION_STRATEGY.md.

Usage:
  python3 automation/capture_judge_feedback.py --task-name TASK \\
    --verdict DISCUSS \\
    --axes-json '{"test_coverage":3.0,"test_faithfulness":2.5,"prescriptiveness":2.5}' \\
    --cited-overreach 'CellMap.out_shape;count >= 4' \\
    --cited-gaps '' \\
    --notes 'Blocked at agentic judge; Difficulty not run'
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "task_outputs" / "_judge_calibration_ledger.jsonl"


def die(msg: str, code: int = 1) -> None:
    raise SystemExit(f"ERROR: {msg}")


def _split_cites(raw: str) -> List[str]:
    if not raw or not str(raw).strip():
        return []
    parts = []
    for chunk in str(raw).replace("\n", ";").split(";"):
        c = chunk.strip()
        if c:
            parts.append(c)
    return parts


def capture(
    outputs_dir: Path,
    task_name: str,
    *,
    verdict: str,
    axes: Dict[str, Any],
    cited_overreach: List[str],
    cited_gaps: List[str],
    notes: str,
    difficulty_ran: bool,
) -> Dict[str, Any]:
    pred_path = outputs_dir / "judge_prediction.json"
    prediction = {}
    if pred_path.is_file():
        try:
            prediction = json.loads(pred_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prediction = {"error": "unparseable prediction"}
    else:
        prediction = {"warning": "missing judge_prediction.json"}

    feedback = {
        "schema_version": 1,
        "task_name": task_name,
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actual_verdict": verdict,
        "actual_axes": axes,
        "cited_overreach": cited_overreach,
        "cited_gaps": cited_gaps,
        "difficulty_ran": difficulty_ran,
        "notes": notes,
        "prediction": {
            "predicted_verdict": prediction.get("predicted_verdict"),
            "confirmed_overreach": prediction.get("confirmed_overreach") or [],
            "confirmed_gaps": prediction.get("confirmed_gaps") or [],
            "predicted_axes": prediction.get("predicted_axes"),
            "prep_fingerprint": prediction.get("prep_fingerprint"),
            "predicted_at": prediction.get("predicted_at"),
        },
    }

    outputs_dir.mkdir(parents=True, exist_ok=True)
    out_path = outputs_dir / "judge_feedback.json"
    out_path.write_text(json.dumps(feedback, indent=2) + "\n", encoding="utf-8")

    ledger_row = {
        "task_name": task_name,
        "recorded_at": feedback["recorded_at"],
        "predicted_verdict": feedback["prediction"]["predicted_verdict"],
        "actual_verdict": verdict,
        "confirmed_overreach": feedback["prediction"]["confirmed_overreach"],
        "cited_overreach": cited_overreach,
        "confirmed_gaps": feedback["prediction"]["confirmed_gaps"],
        "cited_gaps": cited_gaps,
        "predicted_axes": feedback["prediction"]["predicted_axes"],
        "actual_axes": axes,
        "feedback_path": str(out_path),
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ledger_row) + "\n")

    return feedback


def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser(description="Capture live Judge feedback joined to prediction")
    p.add_argument("--task-name", required=True)
    p.add_argument("--verdict", required=True, choices=("OK", "DISCUSS", "REMOVE"))
    p.add_argument("--axes-json", default="{}", help="JSON object of axis → score")
    p.add_argument("--cited-overreach", default="", help="Semicolon-separated judge citations")
    p.add_argument("--cited-gaps", default="", help="Semicolon-separated coverage citations")
    p.add_argument("--notes", default="")
    p.add_argument(
        "--difficulty-ran",
        action="store_true",
        help="Set if Difficulty screen actually ran (usually false when Judge blocks)",
    )
    p.add_argument("--outputs-dir", type=Path)
    args = p.parse_args(argv)

    try:
        axes = json.loads(args.axes_json)
        if not isinstance(axes, dict):
            die("--axes-json must be a JSON object")
    except json.JSONDecodeError as e:
        die(f"bad --axes-json: {e}")

    if args.outputs_dir:
        out = args.outputs_dir
    else:
        out = ROOT / "task_outputs" / args.task_name

    fb = capture(
        out,
        args.task_name,
        verdict=args.verdict,
        axes=axes,
        cited_overreach=_split_cites(args.cited_overreach),
        cited_gaps=_split_cites(args.cited_gaps),
        notes=args.notes,
        difficulty_ran=bool(args.difficulty_ran),
    )
    print(f"JUDGE FEEDBACK WRITTEN: {out / 'judge_feedback.json'}")
    print(f"  ledger: {LEDGER}")
    print(f"  predicted={fb['prediction'].get('predicted_verdict')} actual={fb['actual_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
