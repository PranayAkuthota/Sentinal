#!/usr/bin/env python3
"""Post-task learning capture for Sentinel Submitter framework.

Writes a proposal under knowledge/proposals/ only.
Never modifies work/, task_outputs/ ZIPs, completed_tasks/, or policy rules.
Never decides verdicts.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
PROPOSALS = ROOT / "knowledge" / "proposals"


def die(msg: str, code: int = 1) -> None:
    raise SystemExit(f"ERROR: {msg}")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def redact(text: str) -> str:
    """Strip common task-specific spoilers from free text."""
    text = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "<task-id>", text, flags=re.I)
    text = re.sub(r"https?://github\.com/\S+", "<source-url>", text)
    text = re.sub(r"\b[0-9a-f]{40}\b", "<commit-sha>", text)
    return text


def main() -> None:
    p = argparse.ArgumentParser(description="Capture reusable learning proposal (no archive mutation)")
    p.add_argument("--task-name", required=True)
    p.add_argument("--notes", default="", help="Optional friction notes (will be redacted)")
    args = p.parse_args()

    task = args.task_name
    work = ROOT / "work" / task
    outputs = ROOT / "task_outputs" / task
    if not work.exists() and not outputs.exists():
        die(f"no work/ or task_outputs/ for {task}")

    state = load_json(outputs / "workflow_state.json")
    session = load_json(work / "session" / "session.json") if work.exists() else {}
    findings = ""
    for name in ("findings_and_changes.md", "submitter_audit.md", "validation_summary.md"):
        fp = outputs / name
        if fp.exists():
            findings += f"\n## From {name}\n"
            # keep short; redact
            body = fp.read_text(encoding="utf-8", errors="replace")
            findings += redact(body[:4000])
            findings += "\n"

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    PROPOSALS.mkdir(parents=True, exist_ok=True)
    out = PROPOSALS / f"{ts}__{task}__proposal.md"

    branch = state.get("duplicate_analysis") or session.get("duplicate_analysis") or "unknown"
    f2p = state.get("fail_to_pass_count")
    warnings = state.get("warnings") or []

    body = f"""# Learning proposal (pending human review)

- Generated: {ts} UTC
- Task ref: `{task}` (do not promote UUID into pattern titles)
- Branch recorded: {branch}
- Structural f2p count: {f2p}

## Candidate reusable patterns

List only items likely to help **future** Sentinel tasks. Delete anything task-specific.

1. (edit) …
2. (edit) …

## Automation opportunities (deterministic only)

- …

## Suggested failure catalog entries

- category: …
  symptom: …
  recovery: …

## Agent notes (redacted)

{redact(args.notes) or "_none_"}

## Workflow state warnings (structural)

```
{json.dumps(warnings, indent=2)[:2000]}
```

## Extracted snippets (redacted, truncated)

{findings or "_no reports found_"}

---

**Promotion rule:** Human merges accepted items into `knowledge/patterns/` or `knowledge/failures/`.
Never auto-edit `.cursor/rules/Review_Guidelines.mdc`.
"""
    out.write_text(body, encoding="utf-8")
    print(f"PROPOSAL WRITTEN: {out}")
    print("Review and promote manually. Archives untouched.")


if __name__ == "__main__":
    main()
