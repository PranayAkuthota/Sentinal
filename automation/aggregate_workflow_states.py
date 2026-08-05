#!/usr/bin/env python3
"""Optional cross-task aggregation of task_outputs/*/workflow_state.json.

Read-only. Never assigns verdicts. Never mutates ZIPs.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent


def load_states() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    base = ROOT / "task_outputs"
    if not base.is_dir():
        return out
    for path in sorted(base.glob("*/workflow_state.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        data["_task"] = path.parent.name
        out.append(data)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Aggregate workflow_state.json across tasks")
    p.add_argument("--json", action="store_true", help="Emit JSON summary")
    args = p.parse_args()
    states = load_states()
    dup = Counter(str(s.get("duplicate_analysis") or "unknown") for s in states)
    pub = Counter(str(s.get("public_analysis") or "unknown") for s in states)
    warnings = Counter()
    for s in states:
        for w in s.get("warnings") or []:
            warnings[str(w)[:120]] += 1
    summary = {
        "task_count": len(states),
        "duplicate_analysis": dict(dup),
        "public_analysis": dict(pub),
        "top_warnings": warnings.most_common(20),
        "tasks": [s.get("_task") for s in states],
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print("WORKFLOW STATE AGGREGATE")
        print(f"  tasks: {summary['task_count']}")
        print(f"  duplicate_analysis: {summary['duplicate_analysis']}")
        print(f"  public_analysis: {summary['public_analysis']}")
        print("  top_warnings:")
        for w, c in summary["top_warnings"][:10]:
            print(f"    [{c}] {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
