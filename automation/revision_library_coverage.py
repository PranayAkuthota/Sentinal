#!/usr/bin/env python3
"""Fail loudly if a recorded revision-library instance is not covered by a case/pitfall.

Reads knowledge/revision_library/INSTANCE_INDEX.json and greps cases/ + pitfalls/
Instances sections for each id.

Exit 1 on orphans. Exit 2 if index missing.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "knowledge" / "revision_library"
INDEX = LIB / "INSTANCE_INDEX.json"


def main() -> int:
    if not INDEX.is_file():
        print(f"ERROR: missing {INDEX}", file=sys.stderr)
        return 2
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    instances = data.get("instances") or []
    corpus = ""
    for p in sorted((LIB / "cases").glob("*.md")) + sorted((LIB / "pitfalls").glob("*.md")):
        corpus += p.read_text(encoding="utf-8") + "\n"

    orphans = []
    misfiled = []
    for inst in instances:
        iid = inst["id"]
        expected = inst.get("case") or inst.get("pitfall")
        if iid not in corpus and not re.search(rf"\b{re.escape(iid)}\b", corpus):
            orphans.append(inst)
            continue
        if expected:
            # ensure expected file mentions id
            kind = "cases" if inst.get("case") else "pitfalls"
            name = inst.get("case") or inst.get("pitfall")
            path = LIB / kind / name
            if path.is_file() and iid not in path.read_text(encoding="utf-8"):
                misfiled.append(inst)

    print(f"revision_library coverage: {len(instances)} indexed instances")
    if orphans:
        print(f"ORPHANS ({len(orphans)}) — no case/pitfall mentions id:")
        for o in orphans:
            print(f"  {o['id']}  expected={o.get('case') or o.get('pitfall')}  {o.get('note','')}")
        return 1
    if misfiled:
        print(f"MISFILED ({len(misfiled)}) — id not in expected file:")
        for o in misfiled:
            print(f"  {o['id']} → {o.get('case') or o.get('pitfall')}")
        return 1
    print("OK — every indexed instance appears in the library")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
