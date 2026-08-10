#!/usr/bin/env python3
"""Capture live Agent Judge result into knowledge/judge_feedback/ (schema v2).

Also mirrors to task_outputs/<task>/judge_feedback.json and appends a stats ledger row.
See docs/VALIDATION_STRATEGY.md and knowledge/judge_feedback/schema.json.

Usage:
  python3 automation/capture_judge_feedback.py --task-name TASK \\
    --verdict DISCUSS --verdict-reason weak_check \\
    --axes-json '{"prescriptiveness":2.5,"test_coverage":3.0}' \\
    --must-haves Q2,Q9,Q10 \\
    --citation 'quoted text||axis=test_faithfulness' \\
    --notes 'Difficulty not run'
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "automation"))

from lib.round_chain import (  # noqa: E402
    cites_from_feedback_record,
    classify_pair,
)

FEEDBACK_DIR = ROOT / "knowledge" / "judge_feedback"
HISTORY_DIR = FEEDBACK_DIR / "history"
OUTCOMES_JSONL = FEEDBACK_DIR / "round_outcomes.jsonl"
LEDGER = ROOT / "task_outputs" / "_judge_calibration_ledger.jsonl"
SCHEMA_VERSION = 2

AXIS_NAMES = (
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


def die(msg: str, code: int = 1) -> None:
    raise SystemExit(f"ERROR: {msg}")


def empty_adjudicated(partial: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    out = {k: None for k in AXIS_NAMES}
    if partial:
        for k, v in partial.items():
            if k in out:
                out[k] = v
    return out


def parse_citation(raw: str) -> Dict[str, Any]:
    """Parse 'quoted||file=path||line=1-3||axis=test_faithfulness' or plain quoted text."""
    parts = [p.strip() for p in raw.split("||") if p.strip()]
    cited: Dict[str, Any] = {
        "file": None,
        "line_range": None,
        "quoted_text": None,
        "axis": None,
    }
    if not parts:
        return cited
    cited["quoted_text"] = parts[0]
    for p in parts[1:]:
        if "=" not in p:
            continue
        key, val = p.split("=", 1)
        key, val = key.strip().lower(), val.strip()
        if key in ("file", "path"):
            cited["file"] = val
        elif key in ("line", "line_range", "lines"):
            cited["line_range"] = val
        elif key == "axis":
            cited["axis"] = val
    return cited


def prediction_ref_for(task_name: str) -> Optional[str]:
    rel = f"task_outputs/{task_name}/judge_prediction.json"
    if (ROOT / rel).is_file():
        return rel
    return None


def load_prediction(task_name: str) -> Dict[str, Any]:
    path = ROOT / "task_outputs" / task_name / "judge_prediction.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"error": "unparseable prediction"}


def build_record(
    task_name: str,
    *,
    verdict: Optional[str],
    verdict_reason: Optional[str],
    axes_partial: Dict[str, Any],
    per_judge: Optional[Dict[str, Any]],
    citations: List[Dict[str, Any]],
    must_haves_failed: Optional[List[str]],
    difficulty_run: Optional[bool],
    fixes_applied: List[Dict[str, Any]],
    next_round_result: Optional[Dict[str, Any]],
    source: str,
    notes: Optional[str],
) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "task_name": task_name,
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "axes": {
            "adjudicated": empty_adjudicated(axes_partial),
            "per_judge": per_judge,
        },
        "citations": citations,
        "must_haves_failed": must_haves_failed,
        "difficulty_run": difficulty_run,
        "fixes_applied": fixes_applied,
        "next_round_result": next_round_result,
        "prediction_ref": prediction_ref_for(task_name),
        "source": source,
        "notes": notes,
    }


def _safe_stamp(iso: str) -> str:
    return re.sub(r"[^0-9TZ]", "", iso or "unknown")[:20]


def _archive_and_chain_prior(task: str, new_record: Dict[str, Any]) -> Optional[Path]:
    """Move tip → history and set next_round_result via citation chaining."""
    safe = task.replace("/", "_")
    tip_path = FEEDBACK_DIR / f"{safe}.json"
    if not tip_path.is_file():
        return None
    prior = json.loads(tip_path.read_text(encoding="utf-8"))
    if prior.get("recorded_at") == new_record.get("recorded_at"):
        return None
    prior_cites = cites_from_feedback_record(prior)
    next_cites = cites_from_feedback_record(new_record)
    classified = classify_pair(prior_cites, next_cites)
    prior["next_round_result"] = {
        "following_recorded_at": new_record.get("recorded_at"),
        "following_verdict": new_record.get("verdict"),
        "source": "chained on capture_judge_feedback",
        **classified,
    }
    if not prior.get("fixes_applied"):
        print(
            "WARNING: prior tip had empty fixes_applied — record fixes at packaging "
            "via automation/record_revision_fixes.py so outcomes can be attributed."
        )
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    hist = HISTORY_DIR / f"{safe}__{_safe_stamp(prior.get('recorded_at') or '')}.json"
    hist.write_text(json.dumps(prior, indent=2) + "\n", encoding="utf-8")
    with OUTCOMES_JSONL.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                {
                    "task": task,
                    "from": prior.get("recorded_at"),
                    "to": new_record.get("recorded_at"),
                    "from_verdict": prior.get("verdict"),
                    "to_verdict": new_record.get("verdict"),
                    **classified["counts"],
                    "per_citation": classified["per_citation"],
                    "new_citations_in_next": classified["new_citations_in_next"],
                }
            )
            + "\n"
        )
    print(
        f"CHAINED prior→new: resolved={classified['counts']['resolved']} "
        f"not_resolved={classified['counts']['not_resolved']} "
        f"regressed={classified['counts']['regressed']} "
        f"(archived {hist.name})"
    )
    print("NEXT: match citations to knowledge/revision_library/ (ROUTER.md) and append Instances.")
    return hist


def write_feedback(record: Dict[str, Any]) -> Path:
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    task = record["task_name"]
    safe = task.replace("/", "_")
    path = FEEDBACK_DIR / f"{safe}.json"

    _archive_and_chain_prior(task, record)

    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    out_dir = ROOT / "task_outputs" / task
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "judge_feedback.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )

    pred = load_prediction(task) if record.get("prediction_ref") else {}
    cited_texts = [
        c.get("quoted_text") for c in (record.get("citations") or []) if c.get("quoted_text")
    ]
    ledger_row = {
        "task_name": task,
        "recorded_at": record["recorded_at"],
        "predicted_verdict": pred.get("predicted_verdict"),
        "actual_verdict": record.get("verdict"),
        "confirmed_overreach": pred.get("confirmed_overreach") or [],
        "cited_overreach": cited_texts,
        "confirmed_gaps": pred.get("confirmed_gaps") or [],
        "cited_gaps": [],
        "predicted_axes": pred.get("predicted_axes"),
        "actual_axes": (record.get("axes") or {}).get("adjudicated") or {},
        "feedback_path": str(path.relative_to(ROOT)),
        "verdict_reason": record.get("verdict_reason"),
        "source": record.get("source"),
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ledger_row) + "\n")
    return path


def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser(description="Capture Agent Judge feedback (schema v2)")
    p.add_argument("--task-name", required=True)
    p.add_argument("--verdict", required=True, choices=("OK", "DISCUSS", "REMOVE"))
    p.add_argument("--verdict-reason", default=None)
    p.add_argument("--axes-json", default="{}", help="Adjudicated axis scores JSON object")
    p.add_argument("--per-judge-json", default=None, help="Optional per-judge scores JSON")
    p.add_argument("--must-haves", default=None, help="Comma-separated must-have ids (Q2,Q9)")
    p.add_argument(
        "--citation",
        action="append",
        default=[],
        help="Repeatable. Format: quoted||file=path||line=1-2||axis=name",
    )
    p.add_argument(
        "--fix",
        action="append",
        default=[],
        help="Repeatable per citation. Format: change||file=path||axis=name||cite=quoted-or-id",
    )
    p.add_argument("--notes", default=None)
    p.add_argument(
        "--difficulty-run",
        action="store_true",
        help="Set only when Difficulty actually ran",
    )
    p.add_argument(
        "--difficulty-unknown",
        action="store_true",
        help="Leave difficulty_run null instead of false",
    )
    p.add_argument(
        "--source",
        default="live platform capture",
        help="Provenance string",
    )
    args = p.parse_args(argv)

    try:
        axes_partial = json.loads(args.axes_json)
        if not isinstance(axes_partial, dict):
            die("--axes-json must be a JSON object")
    except json.JSONDecodeError as e:
        die(f"bad --axes-json: {e}")

    per_judge = None
    if args.per_judge_json:
        try:
            per_judge = json.loads(args.per_judge_json)
        except json.JSONDecodeError as e:
            die(f"bad --per-judge-json: {e}")

    must_haves = None
    if args.must_haves is not None:
        must_haves = [x.strip() for x in args.must_haves.split(",") if x.strip()]

    citations = [parse_citation(c) for c in args.citation]
    fixes: List[Dict[str, Any]] = []
    for raw in args.fix:
        parts = [p.strip() for p in raw.split("||") if p.strip()]
        fix: Dict[str, Any] = {
            "file": None,
            "change": parts[0] if parts else None,
            "axis_targeted": None,
            "citation_ref": None,
            "source": "capture_judge_feedback --fix",
        }
        for pbit in parts[1:]:
            if "=" not in pbit:
                continue
            k, v = pbit.split("=", 1)
            k = k.strip().lower()
            if k in ("file", "path"):
                fix["file"] = v.strip()
            elif k == "axis":
                fix["axis_targeted"] = v.strip()
            elif k in ("cite", "citation", "citation_ref"):
                fix["citation_ref"] = v.strip()
        if not fix.get("citation_ref"):
            die(f"--fix must include cite=… (per citation). Got: {raw!r}")
        fixes.append(fix)

    if args.difficulty_unknown:
        diff: Optional[bool] = None
    else:
        diff = bool(args.difficulty_run)

    record = build_record(
        args.task_name,
        verdict=args.verdict,
        verdict_reason=args.verdict_reason,
        axes_partial=axes_partial,
        per_judge=per_judge,
        citations=citations,
        must_haves_failed=must_haves,
        difficulty_run=diff,
        fixes_applied=fixes,
        next_round_result=None,
        source=args.source,
        notes=args.notes,
    )
    path = write_feedback(record)
    print(f"JUDGE FEEDBACK WRITTEN: {path}")
    print(f"  mirror: task_outputs/{args.task_name}/judge_feedback.json")
    print(f"  prediction_ref: {record.get('prediction_ref')}")
    print(f"  verdict={record['verdict']} reason={record.get('verdict_reason')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
