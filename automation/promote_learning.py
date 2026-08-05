#!/usr/bin/env python3
"""Assist human promotion of learning proposals into patterns/failures.

Never edits Review_Guidelines.mdc, never rewrites archives or task ZIPs.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "knowledge" / "patterns"
FAILURES = ROOT / "knowledge" / "failures"
INDEX = PATTERNS / "INDEX.md"


def die(msg: str, code: int = 1) -> None:
    raise SystemExit(f"ERROR: {msg}")


def slug(title: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", title.strip().lower()).strip("_")
    return s[:60] or "pattern"


def ensure_index_row(pid: str, title: str, status: str = "approved") -> None:
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    if not INDEX.exists():
        INDEX.write_text(
            "# Pattern index\n\n| ID | Title | Status | Source |\n|----|-------|--------|--------|\n",
            encoding="utf-8",
        )
    text = INDEX.read_text(encoding="utf-8")
    if f"| {pid} |" in text:
        print(f"INDEX: {pid} already present")
        return
    with INDEX.open("a", encoding="utf-8") as f:
        f.write(f"| {pid} | {title} | {status} | promoted |\n")
    print(f"INDEX: added {pid}")


def cmd_pattern(args: argparse.Namespace) -> None:
    pid = args.id
    title = args.title
    body = f"""# {pid}: {title}

**Status:** approved  
**Promoted:** {datetime.now(timezone.utc).strftime("%Y-%m-%d")}  
**Reusable:** yes

## Pattern

{args.body or args.symptom or "(describe the reusable rule)"}

## When it applies

{args.when or "Recurring Sentinel Harbor submitter tasks."}

## What to do

{args.recovery or "(operator steps)"}

## Do not promote into agent-facing instructions

Task UUIDs, golden patches, hidden tests, or PR spoilers.
"""
    path = PATTERNS / f"{pid}_{slug(title)}.md"
    if path.exists() and not args.force:
        die(f"exists (use --force): {path}")
    path.write_text(body, encoding="utf-8")
    ensure_index_row(pid, title)
    print(f"PATTERN WRITTEN: {path}")


def cmd_failure(args: argparse.Namespace) -> None:
    record = {
        "id": args.id,
        "title": args.title,
        "category": args.category,
        "symptom": args.symptom,
        "root_cause_class": args.root_cause_class,
        "recovery": args.recovery,
        "reusable": True,
        "automation_opportunity": args.automation or "",
        "seen_count": args.seen_count,
        "notes": args.notes or "",
    }
    # validate required keys against schema enums lightly
    allowed = {
        "packaging",
        "tests_patch",
        "grading",
        "instruction",
        "oracle",
        "environment",
        "metadata",
        "validation",
        "workflow",
        "other",
    }
    if record["category"] not in allowed:
        die(f"category must be one of {sorted(allowed)}")
    path = FAILURES / f"{args.id}_{slug(args.title)}.json"
    if path.exists() and not args.force:
        die(f"exists (use --force): {path}")
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"FAILURE WRITTEN: {path}")


def main() -> None:
    p = argparse.ArgumentParser(description="Promote learning proposal items (human-driven)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("pattern", help="Write knowledge/patterns entry + INDEX row")
    pp.add_argument("--id", required=True, help="e.g. P-006")
    pp.add_argument("--title", required=True)
    pp.add_argument("--body", default="")
    pp.add_argument("--symptom", default="")
    pp.add_argument("--when", default="")
    pp.add_argument("--recovery", default="")
    pp.add_argument("--force", action="store_true")
    pp.set_defaults(func=cmd_pattern)

    # also allow --pattern flag style via alias
    pf = sub.add_parser("failure", help="Write knowledge/failures JSON record")
    pf.add_argument("--id", required=True, help="e.g. F-001")
    pf.add_argument("--title", required=True)
    pf.add_argument("--category", required=True)
    pf.add_argument("--symptom", required=True)
    pf.add_argument("--root-cause-class", dest="root_cause_class", required=True)
    pf.add_argument("--recovery", required=True)
    pf.add_argument("--automation", default="")
    pf.add_argument("--seen-count", dest="seen_count", type=int, default=2)
    pf.add_argument("--notes", default="")
    pf.add_argument("--force", action="store_true")
    pf.set_defaults(func=cmd_failure)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
