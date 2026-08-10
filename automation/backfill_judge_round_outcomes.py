#!/usr/bin/env python3
"""Backfill next_round_result by chaining calibration-ledger rounds per task.

Writes:
  knowledge/judge_feedback/history/<task>__<recorded_at>.json  (round stubs + outcomes)
  knowledge/revision_library/OUTCOMES.md

Also patches tip knowledge/judge_feedback/<task>.json when a 07 handoff records fixes
(source: reconstructed from handoff) and when the tip is not the last ledger round
(rare — usually tip IS last and keeps next_round_result null).

Does not invent oracle/NOP numbers.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "automation"))

from lib.round_chain import (  # noqa: E402
    cites_from_feedback_record,
    cites_from_ledger_row,
    classify_pair,
)

LEDGER = ROOT / "task_outputs" / "_judge_calibration_ledger.jsonl"
HISTORY = ROOT / "knowledge" / "judge_feedback" / "history"
FEEDBACK = ROOT / "knowledge" / "judge_feedback"
OUTCOMES = ROOT / "knowledge" / "revision_library" / "OUTCOMES.md"

# Map tip task → reconstructed fixes from 07 handoffs (Part A evidence).
HANDOFF_FIXES: Dict[str, List[Dict[str, Any]]] = {
    "1e6ecbbd-2a02-4323-b280-934a874c27a9_submission": [
        {
            "file": "instruction.md",
            "change": "TRIM: removed ArcMutex / mutex-replacement claim; requirements "
            "match graded with_context suite only (JF014)",
            "axis_targeted": "test_coverage",
            "citation_ref": "never verifies refactor away from Arc Mutex",
            "source": "reconstructed from handoff",
        },
        {
            "file": "task.toml",
            "change": "Removed irregular pass_at_k_* /3 fields; kept difficulty=medium (JF015)",
            "axis_targeted": "packaging",
            "citation_ref": "irregular /3 baseline denominators",
            "source": "reconstructed from handoff",
        },
    ],
    "eb599683-21e8-49a0-badd-207636178abc_submission": [
        {
            "file": "environment/repo/.python-version",
            "change": "Restored tracked .python-version / original HEAD 4645096… (JF052)",
            "axis_targeted": "packaging",
            "citation_ref": "environment/repo was changed at tracked source level",
            "source": "reconstructed from handoff",
        },
        {
            "file": "solution/solve.sh",
            "change": "Forward-only apply; remove reverse-apply success fallback (JF053)",
            "axis_targeted": "oracle_robustness",
            "citation_ref": "solve.sh reverse applies golden.patch",
            "source": "reconstructed from handoff",
        },
        {
            "file": "task.toml",
            "change": "difficulty/model_difficulty=hard + difficulty_explanation; os=linux (JF059)",
            "axis_targeted": "packaging",
            "citation_ref": "task.toml missing os=linux and difficulty_explanation",
            "source": "reconstructed from handoff",
        },
    ],
}


def load_ledger() -> Dict[str, List[Dict[str, Any]]]:
    by: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if not LEDGER.is_file():
        return by
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        by[row["task_name"]].append(row)
    for t in by:
        by[t].sort(key=lambda r: r.get("recorded_at") or "")
    return by


def safe_stamp(iso: str) -> str:
    return re.sub(r"[^0-9TZ]", "", iso or "unknown")[:20]


def stub_from_ledger(row: Dict[str, Any]) -> Dict[str, Any]:
    cites = cites_from_ledger_row(row)
    return {
        "schema_version": 2,
        "task_name": row["task_name"],
        "recorded_at": row["recorded_at"],
        "verdict": row.get("actual_verdict"),
        "verdict_reason": row.get("verdict_reason"),
        "axes": {
            "adjudicated": row.get("actual_axes") or {},
            "per_judge": None,
        },
        "citations": [
            {"file": None, "line_range": None, "quoted_text": c, "axis": None} for c in cites
        ],
        "must_haves_failed": None,
        "difficulty_run": None,
        "fixes_applied": [],
        "next_round_result": None,
        "prediction_ref": None,
        "source": "reconstructed from calibration ledger",
        "notes": "Round stub for outcome chaining; citations from ledger cited_* fields.",
    }


def main() -> int:
    by = load_ledger()
    HISTORY.mkdir(parents=True, exist_ok=True)
    all_outcomes: List[Dict[str, Any]] = []
    pairs = 0

    for task, rounds in sorted(by.items()):
        if len(rounds) < 2:
            # Still write tip handoff fixes if any
            tip_path = FEEDBACK / f"{task}.json"
            if tip_path.is_file() and task in HANDOFF_FIXES:
                tip = json.loads(tip_path.read_text(encoding="utf-8"))
                if not tip.get("fixes_applied"):
                    tip["fixes_applied"] = HANDOFF_FIXES[task]
                    tip_path.write_text(json.dumps(tip, indent=2) + "\n", encoding="utf-8")
            continue

        for i, row in enumerate(rounds):
            stub = stub_from_ledger(row)
            # Prefer tip file citations when timestamps match tip
            tip_path = FEEDBACK / f"{task}.json"
            if tip_path.is_file() and i == len(rounds) - 1:
                tip = json.loads(tip_path.read_text(encoding="utf-8"))
                if cites_from_feedback_record(tip):
                    stub["citations"] = tip["citations"]
                    stub["verdict"] = tip.get("verdict")
                    stub["verdict_reason"] = tip.get("verdict_reason")
                    stub["axes"] = tip.get("axes") or stub["axes"]
                    stub["source"] = tip.get("source") or stub["source"]
                    stub["notes"] = tip.get("notes")
                    stub["must_haves_failed"] = tip.get("must_haves_failed")
                    stub["difficulty_run"] = tip.get("difficulty_run")
                    if tip.get("fixes_applied"):
                        stub["fixes_applied"] = tip["fixes_applied"]
                    elif task in HANDOFF_FIXES:
                        stub["fixes_applied"] = HANDOFF_FIXES[task]

            if i < len(rounds) - 1:
                nxt = rounds[i + 1]
                prior_cites = [c["quoted_text"] for c in stub["citations"] if c.get("quoted_text")]
                next_cites = cites_from_ledger_row(nxt)
                # If next is tip, use tip citations
                if tip_path.is_file() and i + 1 == len(rounds) - 1:
                    tip = json.loads(tip_path.read_text(encoding="utf-8"))
                    tc = cites_from_feedback_record(tip)
                    if tc:
                        next_cites = tc
                classified = classify_pair(prior_cites, next_cites)
                stub["next_round_result"] = {
                    "following_recorded_at": nxt.get("recorded_at"),
                    "following_verdict": nxt.get("actual_verdict"),
                    "source": "chained from calibration ledger",
                    **classified,
                }
                pairs += 1
                all_outcomes.append(
                    {
                        "task": task,
                        "from": row.get("recorded_at"),
                        "to": nxt.get("recorded_at"),
                        "from_verdict": row.get("actual_verdict"),
                        "to_verdict": nxt.get("actual_verdict"),
                        **classified["counts"],
                        "per_citation": classified["per_citation"],
                        "new_citations_in_next": classified["new_citations_in_next"],
                    }
                )

            hist = HISTORY / f"{task}__{safe_stamp(row.get('recorded_at') or '')}.json"
            hist.write_text(json.dumps(stub, indent=2) + "\n", encoding="utf-8")

            # Mirror next_round_result onto tip only when tip equals this round and has a follower
            # (should not happen for last). For penultimate, also write outcome summary file.
            if i == len(rounds) - 1 and tip_path.is_file() and task in HANDOFF_FIXES:
                tip = json.loads(tip_path.read_text(encoding="utf-8"))
                if not tip.get("fixes_applied"):
                    tip["fixes_applied"] = HANDOFF_FIXES[task]
                    tip_path.write_text(json.dumps(tip, indent=2) + "\n", encoding="utf-8")

    # Persist machine-readable chain outcomes
    out_json = FEEDBACK / "round_outcomes.jsonl"
    with out_json.open("w", encoding="utf-8") as fh:
        for o in all_outcomes:
            # trim per_citation for ledger size? keep full — needed for case updates
            fh.write(json.dumps(o) + "\n")

    write_outcomes_md(all_outcomes, pairs)
    print(f"BACKFILL: {pairs} consecutive pairs across {sum(1 for t,r in by.items() if len(r)>=2)} tasks")
    print(f"  history dir: {HISTORY}")
    print(f"  outcomes: {OUTCOMES}")
    print(f"  jsonl: {out_json}")
    return 0


def write_outcomes_md(outcomes: List[Dict[str, Any]], pairs: int) -> None:
    resolved = sum(o["resolved"] for o in outcomes)
    not_res = sum(o["not_resolved"] for o in outcomes)
    regressed = sum(o["regressed"] for o in outcomes)
    lines = [
        "# Round-chain outcomes (backfill)",
        "",
        "Built by chaining `task_outputs/_judge_calibration_ledger.jsonl` rounds per task.",
        "Judge **citations** only — verdict can improve while a defect persists, or worsen",
        "while one citation resolved.",
        "",
        f"- Consecutive pairs chained: **{pairs}**",
        f"- Citation outcomes: **resolved={resolved}**, **not_resolved={not_res}**, "
        f"**regressed={regressed}**",
        "",
        "## Honesty",
        "",
        "These outcomes are **observed** from consecutive captured rounds. They still do not",
        "prove which edit caused a resolution unless `fixes_applied` was recorded for that",
        "round. Handoff-reconstructed fixes exist only for 1e6ecbbd (JF014/015) and",
        "eb599683 (JF052/053/059) — and those tip rounds have **no following response yet**.",
        "",
        "## Per pair",
        "",
        "| task | from → to | verdicts | resolved | not_resolved | regressed | new |",
        "|------|-----------|----------|----------|--------------|-----------|-----|",
    ]
    for o in outcomes:
        lines.append(
            f"| {o['task'][:8]} | `{o['from']}` → `{o['to']}` | "
            f"{o['from_verdict']}→{o['to_verdict']} | {o['resolved']} | {o['not_resolved']} | "
            f"{o['regressed']} | {o['new_in_next']} |"
        )

    lines.extend(
        [
            "",
            "## Evidenced working (resolved citations with clear family)",
            "",
            "Examples where a prior citation did not recur (not proof of a specific patch):",
            "",
        ]
    )
    # Highlight a few known families
    for o in outcomes:
        for pc in o["per_citation"]:
            if pc["outcome"] != "resolved":
                continue
            qt = pc["quoted_text"]
            if any(
                k in qt.lower()
                for k in (
                    "fail-open",
                    "allow_extra_failures",
                    "reverse-apply",
                    "git apply -r",
                    "source substring",
                    "gradle",
                )
            ):
                lines.append(
                    f"- **resolved** `{o['task'][:8]}` `{o['from']}`: {qt[:120]}"
                )

    lines.extend(["", "## Evidenced failing / oscillating", ""])
    for o in outcomes:
        for pc in o["per_citation"]:
            if pc["outcome"] == "not_resolved":
                lines.append(
                    f"- **not_resolved** `{o['task'][:8]}` {o['from']}→{o['to']}: "
                    f"{pc['quoted_text'][:100]}"
                )
            elif pc["outcome"] == "regressed":
                lines.append(
                    f"- **regressed** `{o['task'][:8]}` {o['from']}→{o['to']}: "
                    f"{pc['quoted_text'][:80]} ⇒ {pc.get('regression_appeared_as','')[:80]}"
                )

    lines.extend(
        [
            "",
            "## Case library mapping (rough)",
            "",
            "| Case family | Signal in chain |",
            "|-------------|-----------------|",
            "| 03 Difficulty FAIL EASY | FAIL EASY / 100% (4/4) recurring not_resolved |",
            "| 05↔06 oscillation | regressed rows + Q9/Q10 new after unstated→stated |",
            "| 08 solve.sh reverse | reverse-apply resolved when absent next round |",
            "| 13 fail-open | fail-open scan resolved 0cf2e9a3 round1→2 |",
            "| 02 editing-boundary | new stash/repo-edit cites after prior OK |",
            "",
        ]
    )
    OUTCOMES.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
