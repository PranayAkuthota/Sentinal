#!/usr/bin/env python3
"""Write judge_prediction.json from prep + rehearsal at upload time.

Usage:
  python3 automation/write_judge_prediction.py --task-name TASK
  python3 automation/write_judge_prediction.py --outputs-dir PATH
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import judge_prep as jp  # noqa: E402

AXES = (
    "realism",
    "clarity",
    "self_containedness",
    "prescriptiveness",
    "test_coverage",
    "test_faithfulness",
    "spec_faithfulness",
    "no_gaming",
    "robustness",
    "packaging",
)


def _load(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def build_prediction(outputs_dir: Path, task_name: str) -> Dict[str, Any]:
    prep_path = outputs_dir / "judge_prep.json"
    reh_path = outputs_dir / "judge_rehearsal.json"
    prep = _load(prep_path) or {}
    reh = _load(reh_path) or {}

    prep_fp = jp.file_sha256(prep_path) if prep_path.is_file() else None
    axes: Dict[str, Any] = {k: None for k in AXES}
    axes_source = "missing_rehearsal"
    if reh.get("predicted_axes"):
        for k in AXES:
            if k in reh["predicted_axes"]:
                axes[k] = reh["predicted_axes"][k]
        axes_source = "rehearsal.predicted_axes"
    elif reh.get("reconciled_axes"):
        for k in AXES:
            if k in reh["reconciled_axes"]:
                axes[k] = reh["reconciled_axes"][k]
        axes_source = "rehearsal.reconciled_axes"
    elif isinstance(reh.get("scores"), dict):
        # optional nested {axis: {final: n}}
        for k in AXES:
            cell = reh["scores"].get(k)
            if isinstance(cell, dict) and "final" in cell:
                axes[k] = cell["final"]
            elif isinstance(cell, (int, float)):
                axes[k] = cell
        if any(v is not None for v in axes.values()):
            axes_source = "rehearsal.scores"

    predicted_verdict = reh.get("platform_logic") or "UNSET"
    if predicted_verdict not in ("OK", "DISCUSS", "REMOVE", "UNSET"):
        predicted_verdict = str(predicted_verdict)

    return {
        "schema_version": 1,
        "task_name": task_name,
        "predicted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prep_fingerprint": prep_fp,
        "predicted_verdict": predicted_verdict,
        "predicted_axes": axes,
        "axes_source": axes_source,
        "confirmed_overreach": list(reh.get("confirmed_overreach") or []),
        "confirmed_gaps": list(reh.get("confirmed_gaps") or []),
        "packaging_hard_cap": bool((prep.get("packaging") or {}).get("hard_cap")),
        "operational_bar_3_5": reh.get("operational_bar_3_5"),
    }


def write_prediction(outputs_dir: Path, task_name: str) -> Path:
    outputs_dir.mkdir(parents=True, exist_ok=True)
    doc = build_prediction(outputs_dir, task_name)
    path = outputs_dir / "judge_prediction.json"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser(description="Write judge_prediction.json at upload time")
    p.add_argument("--task-name")
    p.add_argument("--outputs-dir", type=Path)
    args = p.parse_args(argv)

    if args.outputs_dir:
        out = args.outputs_dir
        name = args.task_name or out.name
    elif args.task_name:
        from sentinel_submitter import session_paths  # type: ignore

        out = session_paths(args.task_name)["outputs"]
        name = args.task_name
    else:
        print("ERROR: --task-name or --outputs-dir required", file=sys.stderr)
        return 2

    path = write_prediction(out, name)
    print(f"JUDGE PREDICTION WRITTEN: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
