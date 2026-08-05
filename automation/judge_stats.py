#!/usr/bin/env python3
"""Aggregate predicted vs actual Agent Judge calibration.

Reads knowledge/judge_feedback/*.json (schema v2) and joins prediction_ref when present.
Also accepts the legacy task_outputs/_judge_calibration_ledger.jsonl.

See docs/VALIDATION_STRATEGY.md. Does not tune thresholds.

Usage:
  python3 automation/judge_stats.py
  python3 automation/judge_stats.py --feedback-dir knowledge/judge_feedback
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FEEDBACK_DIR = ROOT / "knowledge" / "judge_feedback"
DEFAULT_LEDGER = ROOT / "task_outputs" / "_judge_calibration_ledger.jsonl"

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


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def load_feedback_rows(feedback_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not feedback_dir.is_dir():
        return rows
    for path in sorted(feedback_dir.glob("*.json")):
        if path.name == "schema.json":
            continue
        doc = _load_json(path)
        if not doc.get("task_name"):
            continue
        pred: Dict[str, Any] = {}
        pref = doc.get("prediction_ref")
        if pref:
            pred = _load_json(ROOT / pref)
        axes = (doc.get("axes") or {}).get("adjudicated") or {}
        cited = [
            c.get("quoted_text")
            for c in (doc.get("citations") or [])
            if isinstance(c, dict) and c.get("quoted_text")
        ]
        rows.append(
            {
                "task_name": doc.get("task_name"),
                "recorded_at": doc.get("recorded_at"),
                "predicted_verdict": pred.get("predicted_verdict"),
                "actual_verdict": doc.get("verdict"),
                "verdict_reason": doc.get("verdict_reason"),
                "confirmed_overreach": pred.get("confirmed_overreach") or [],
                "cited_overreach": cited,
                "confirmed_gaps": pred.get("confirmed_gaps") or [],
                "cited_gaps": [],
                "predicted_axes": pred.get("predicted_axes"),
                "actual_axes": axes,
                "source": doc.get("source"),
                "feedback_path": str(path.relative_to(ROOT)),
                "must_haves_failed": doc.get("must_haves_failed"),
                "difficulty_run": doc.get("difficulty_run"),
            }
        )
    return rows


def load_ledger(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _norm(s: str) -> str:
    return "".join(ch.lower() for ch in s if ch.isalnum() or ch in "._#")


def cite_match(confirmed: str, cited: str) -> bool:
    a, b = _norm(confirmed), _norm(cited)
    if not a or not b:
        return False
    if a == b:
        return True
    return a in b or b in a


def precision_recall(confirmed: List[str], cited: List[str]) -> Dict[str, Any]:
    conf = [str(x) for x in confirmed if x]
    cit = [str(x) for x in cited if x]
    if not conf and not cit:
        return {"precision": None, "recall": None, "tp": 0, "fp": 0, "fn": 0}
    tp_conf: Set[int] = set()
    tp_cit: Set[int] = set()
    for i, c in enumerate(conf):
        for j, t in enumerate(cit):
            if cite_match(c, t):
                tp_conf.add(i)
                tp_cit.add(j)
    tp = len(tp_conf)
    fp = len(conf) - tp
    fn = len(cit) - len(tp_cit)
    precision = (tp / len(conf)) if conf else None
    recall = (len(tp_cit) / len(cit)) if cit else None
    return {"precision": precision, "recall": recall, "tp": tp, "fp": fp, "fn": fn}


def _fmt(x: Optional[float]) -> str:
    if x is None:
        return "n/a"
    return f"{x:.2f}"


def report(rows: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append(f"# Judge calibration stats ({len(rows)} feedback records)")
    lines.append("")
    if not rows:
        lines.append("No feedback records yet. Capture with capture_judge_feedback.py")
        lines.append("or place schema-v2 JSON under knowledge/judge_feedback/.")
        return "\n".join(lines) + "\n"

    for r in rows:
        lines.append(
            f"- {r.get('task_name')}: verdict={r.get('actual_verdict')} "
            f"reason={r.get('verdict_reason')} source={r.get('source')} "
            f"pred={r.get('predicted_verdict')}"
        )
    lines.append("")

    paired = [r for r in rows if r.get("predicted_verdict") and r.get("actual_verdict")]
    if paired:
        agree = sum(1 for r in paired if r["predicted_verdict"] == r["actual_verdict"])
        lines.append(f"Verdict agreement (rows with prediction): {agree}/{len(paired)}")
    else:
        lines.append("Verdict agreement: n/a (no prediction_ref joins yet)")
    lines.append("")

    all_conf: List[str] = []
    all_cit: List[str] = []
    per_task = []
    for r in rows:
        conf = list(r.get("confirmed_overreach") or [])
        cit = list(r.get("cited_overreach") or [])
        pr = precision_recall(conf, cit)
        per_task.append((r.get("task_name"), pr, conf, cit))
        all_conf.extend(conf)
        all_cit.extend(cit)
    pooled = precision_recall(all_conf, all_cit)
    lines.append("## Confirmed-overreach precision / recall")
    lines.append(
        f"Pooled: precision={_fmt(pooled['precision'])} recall={_fmt(pooled['recall'])} "
        f"(tp={pooled['tp']} fp={pooled['fp']} fn={pooled['fn']})"
    )
    for name, pr, conf, cit in per_task:
        lines.append(
            f"- {name}: P={_fmt(pr['precision'])} R={_fmt(pr['recall'])} "
            f"(confirmed={len(conf)} cited={len(cit)})"
        )
    lines.append("")

    lines.append("## Per-axis |predicted − actual| (mean when both present)")
    abs_sums: Dict[str, float] = defaultdict(float)
    abs_n: Dict[str, int] = defaultdict(int)
    for r in rows:
        pred = r.get("predicted_axes") or {}
        act = r.get("actual_axes") or {}
        if not isinstance(pred, dict) or not isinstance(act, dict):
            continue
        for axis in AXES:
            pv, av = pred.get(axis), act.get(axis)
            if isinstance(pv, (int, float)) and isinstance(av, (int, float)):
                abs_sums[axis] += abs(float(pv) - float(av))
                abs_n[axis] += 1
    for axis in AXES:
        if abs_n[axis]:
            lines.append(f"- {axis}: MAE={abs_sums[axis]/abs_n[axis]:.2f} (n={abs_n[axis]})")
        else:
            lines.append(f"- {axis}: (no paired scores yet)")
    lines.append("")
    lines.append("Backfilled rows without predictions show cited counts only; P/R stays n/a until live joins.")
    return "\n".join(lines) + "\n"


def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser(description="Judge prediction vs actual calibration stats")
    p.add_argument("--feedback-dir", type=Path, default=DEFAULT_FEEDBACK_DIR)
    p.add_argument(
        "--ledger",
        type=Path,
        default=None,
        help="Optional legacy jsonl; used only when feedback-dir has no records",
    )
    args = p.parse_args(argv)
    rows = load_feedback_rows(args.feedback_dir)
    if not rows:
        ledger = args.ledger or DEFAULT_LEDGER
        rows = load_ledger(ledger)
    sys.stdout.write(report(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
