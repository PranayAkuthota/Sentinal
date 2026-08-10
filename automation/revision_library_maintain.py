#!/usr/bin/env python3
"""Revision-library maintenance: promote provisional cases; flag contradiction edits.

Promote:
  python3 automation/revision_library_maintain.py promote --case 15 \\
    --instance-a FC003 --instance-b JF021 --date 2026-08-10

Contradiction (never silent overwrite):
  python3 automation/revision_library_maintain.py contradict --case 06 \\
    --old-guidance '…' --new-guidance '…' --reason '…'
  → appends knowledge/revision_library/CONTRADICTIONS_PENDING.md and exits 1
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "knowledge" / "revision_library"
CASES = LIB / "cases"
PENDING = LIB / "CONTRADICTIONS_PENDING.md"


def die(msg: str, code: int = 1) -> None:
    raise SystemExit(f"ERROR: {msg}")


def find_case(num: str) -> Path:
    matches = list(CASES.glob(f"{int(num):02d}_*.md")) + list(
        (LIB / "pitfalls").glob(f"{int(num):02d}_*.md")
    )
    if not matches:
        die(f"no case/pitfall file for number {num}")
    return matches[0]


def cmd_promote(args: argparse.Namespace) -> int:
    path = find_case(args.case)
    text = path.read_text(encoding="utf-8")
    if "PROVISIONAL" not in text and "PROVISIONAL-THIN" not in text:
        print(f"{path.name}: already not provisional")
        return 0
    if args.instance_a == args.instance_b:
        die("need two independent instance ids")
    new_status = (
        f"**Status:** CONFIRMED (promoted {args.date}; "
        f"instances {args.instance_a}, {args.instance_b})"
    )
    text2, n = re.subn(
        r"\*\*Status:\*\*\s*PROVISIONAL[^\n]*",
        new_status,
        text,
        count=1,
    )
    if n == 0:
        text2, n = re.subn(
            r"\*\*Status:\*\*\s*PROVISIONAL-THIN[^\n]*",
            new_status,
            text,
            count=1,
        )
    if n == 0:
        die("could not find Status line to promote")
    # Append promotion note under Instances
    note = (
        f"\n- {args.date} · PROMOTED to CONFIRMED · "
        f"{args.instance_a} + {args.instance_b} · {args.note or ''}\n"
    )
    if "## Instances" in text2:
        text2 = text2.rstrip() + note
    path.write_text(text2, encoding="utf-8")
    print(f"PROMOTED: {path}")
    return 0


def cmd_contradict(args: argparse.Namespace) -> int:
    path = find_case(args.case)
    PENDING.parent.mkdir(parents=True, exist_ok=True)
    block = (
        f"\n## Pending · Case {args.case} · {args.date}\n\n"
        f"File: `{path.relative_to(ROOT)}`\n\n"
        f"**Existing guidance:**\n\n> {args.old_guidance}\n\n"
        f"**Proposed guidance:**\n\n> {args.new_guidance}\n\n"
        f"**Reason / new instance:** {args.reason}\n\n"
        f"**Decision:** _awaiting human_\n"
    )
    with PENDING.open("a", encoding="utf-8") as fh:
        if not PENDING.exists() or PENDING.stat().st_size == 0:
            fh.write(
                "# Contradictions pending human decision\n\n"
                "Do **not** silently overwrite case Fix sections.\n"
            )
        fh.write(block)
    print(f"CONTRADICTION FLAGGED (not applied): {PENDING}")
    print("Resolve manually, then delete or check off the pending block.")
    return 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("promote", help="PROVISIONAL → CONFIRMED with two instances")
    pr.add_argument("--case", required=True)
    pr.add_argument("--instance-a", required=True)
    pr.add_argument("--instance-b", required=True)
    pr.add_argument("--date", default=str(date.today()))
    pr.add_argument("--note", default="")
    pr.set_defaults(func=cmd_promote)

    co = sub.add_parser("contradict", help="Flag conflicting guidance; do not overwrite")
    co.add_argument("--case", required=True)
    co.add_argument("--old-guidance", required=True)
    co.add_argument("--new-guidance", required=True)
    co.add_argument("--reason", required=True)
    co.add_argument("--date", default=str(date.today()))
    co.set_defaults(func=cmd_contradict)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
