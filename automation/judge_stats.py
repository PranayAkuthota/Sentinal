#!/usr/bin/env python3
"""Aggregate predicted vs actual Agent Judge calibration from the ledger.

See docs/VALIDATION_STRATEGY.md. Does not tune thresholds.

Usage:
  python3 automation/judge_stats.py
  python3 automation/judge_stats.py --ledger PATH
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

ROOT = Path(__file__).resolve().parent.parent
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
    """Loose match: id equality or mutual substring after normalize."""
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


def report(rows: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append(f"# Judge calibration stats ({len(rows)} joined rows)")
    lines.append("")
    if not rows:
        lines.append("No ledger rows yet. Upload with write_judge_prediction, then")
        lines.append("capture_judge_feedback after the platform returns.")
        return "\n".join(lines) + "\n"

    verdict_agree = sum(
        1 for r in rows if r.get("predicted_verdict") and r.get("predicted_verdict") == r.get("actual_verdict")
    )
    lines.append(f"Verdict agreement: {verdict_agree}/{len(rows)}")
    lines.append("")

    # Overreach P/R pooled
    all_conf: List[str] = []
    all_cit: List[str] = []
    per_task = []
    for r in rows:
        conf = list(r.get("confirmed_overreach") or [])
        cit = list(r.get("cited_overreach") or [])
        pr = precision_recall(conf, cit)
        per_task.append((r.get("task_name"), pr))
        all_conf.extend(conf)
        all_cit.extend(cit)
    pooled = precision_recall(all_conf, all_cit)
    lines.append("## Confirmed-overreach precision / recall")
    lines.append(
        f"Pooled: precision={_fmt(pooled['precision'])} recall={_fmt(pooled['recall'])} "
        f"(tp={pooled['tp']} fp={pooled['fp']} fn={pooled['fn']})"
    )
    for name, pr in per_task:
        lines.append(
            f"- {name}: P={_fmt(pr['precision'])} R={_fmt(pr['recall'])} "
            f"(confirmed={pr['tp']+pr['fp']} cited={pr['tp']+pr['fn']})"
        )
    lines.append("")

    gap_conf: List[str] = []
    gap_cit: List[str] = []
    for r in rows:
        gap_conf.extend(r.get("confirmed_gaps") or [])
        gap_cit.extend(r.get("cited_gaps") or [])
    gp = precision_recall(gap_conf, gap_cit)
    lines.append("## Confirmed-gap precision / recall")
    lines.append(
        f"Pooled: precision={_fmt(gp['precision'])} recall={_fmt(gp['recall'])}"
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
    lines.append("Do not tune thresholds from sparse n. Prefer prompt/map fixes when P or R is poor.")
    return "\n".join(lines) + "\n"


def _fmt(x: Optional[float]) -> str:
    if x is None:
        return "n/a"
    return f"{x:.2f}"


def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser(description="Judge prediction vs actual calibration stats")
    p.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = p.parse_args(argv)
    rows = load_ledger(args.ledger)
    text = report(rows)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
