#!/usr/bin/env python3
"""Record per-citation fixes_applied on the current judge_feedback tip (packaging time).

Usage:
  python3 automation/record_revision_fixes.py --task-name TASK \\
    --fix 'TRIM ArcMutex claim||file=instruction.md||axis=test_coverage||cite=never verifies refactor' \\
    --fix 'delete pass_at_k||file=task.toml||axis=packaging||cite=irregular /3'

Replaces or merges into tip fixes_applied. Does not invent outcomes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
FEEDBACK = ROOT / "knowledge" / "judge_feedback"


def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def parse_fix(raw: str) -> Dict[str, Any]:
    parts = [p.strip() for p in raw.split("||") if p.strip()]
    fix: Dict[str, Any] = {
        "file": None,
        "change": parts[0] if parts else None,
        "axis_targeted": None,
        "citation_ref": None,
        "source": "packaging-time record",
    }
    for pbit in parts[1:]:
        if "=" not in pbit:
            continue
        k, v = pbit.split("=", 1)
        k, v = k.strip().lower(), v.strip()
        if k in ("file", "path"):
            fix["file"] = v
        elif k == "axis":
            fix["axis_targeted"] = v
        elif k in ("cite", "citation", "citation_ref"):
            fix["citation_ref"] = v
    if not fix.get("citation_ref"):
        die(f"each --fix must include cite=… (per-citation). Got: {raw!r}")
    if not fix.get("change"):
        die(f"empty change in --fix: {raw!r}")
    return fix


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--task-name", required=True)
    p.add_argument("--fix", action="append", default=[], required=False)
    p.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing fixes_applied instead of merging by citation_ref",
    )
    args = p.parse_args(argv)
    if not args.fix:
        die("pass at least one --fix …||cite=…")

    path = FEEDBACK / f"{args.task_name}.json"
    if not path.is_file():
        die(f"missing tip feedback {path} — capture Judge feedback before recording fixes")

    rec = json.loads(path.read_text(encoding="utf-8"))
    new_fixes = [parse_fix(x) for x in args.fix]
    if args.replace or not rec.get("fixes_applied"):
        rec["fixes_applied"] = new_fixes
    else:
        by_cite = {
            (f.get("citation_ref") or f.get("change")): f for f in rec["fixes_applied"]
        }
        for f in new_fixes:
            by_cite[f["citation_ref"]] = f
        rec["fixes_applied"] = list(by_cite.values())

    path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    mirror = ROOT / "task_outputs" / args.task_name / "judge_feedback.json"
    if mirror.parent.is_dir():
        mirror.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")

    print(f"FIXES RECORDED: {path} ({len(rec['fixes_applied'])} entries)")
    missing_cites = []
    tip_cites = [
        (c.get("quoted_text") or "") for c in (rec.get("citations") or []) if c.get("quoted_text")
    ]
    for f in rec["fixes_applied"]:
        ref = f.get("citation_ref") or ""
        if tip_cites and not any(ref[:40] in t or t[:40] in ref for t in tip_cites):
            missing_cites.append(ref)
    if missing_cites:
        print("WARNING: citation_ref not found in tip citations (substring):")
        for m in missing_cites:
            print(f"  - {m[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
