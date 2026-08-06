#!/usr/bin/env python3
"""Aggregate predicted vs actual Agent Judge calibration.

Reads knowledge/judge_feedback/*.json (schema v2) and joins prediction_ref when present.

Retrospective joins (prediction.source == \"retrospective backtest\") are reported
SEPARATELY from live at-upload joins. Precision is suppressed for retrospective rows:
the live judge cites selectively, so an unmentioned flag is not a false positive.

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
from typing import Any, Dict, List, Optional, Set, Tuple

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

RETROSPECTIVE_SOURCES = frozenset({"retrospective backtest", "retrospective out-of-sample"})


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _norm(s: str) -> str:
    return "".join(ch.lower() for ch in s if ch.isalnum() or ch in "._#")


def prediction_is_retrospective(pred: Dict[str, Any]) -> bool:
    return str(pred.get("source") or "") in RETROSPECTIVE_SOURCES


def expand_confirmed_artifacts(pred: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten confirmed overreach/gaps/packaging into matchable artifact records."""
    rows: List[Dict[str, Any]] = []
    for item in pred.get("confirmed_overreach_detail") or []:
        if isinstance(item, dict):
            arts = [str(a) for a in (item.get("artifacts") or []) if a]
            rows.append(
                {
                    "kind": "overreach",
                    "id": item.get("id"),
                    "artifacts": arts,
                    "text": item.get("assertion_text") or item.get("id") or "",
                }
            )
    for aid in pred.get("confirmed_overreach") or []:
        if any(r.get("id") == aid for r in rows):
            continue
        rows.append({"kind": "overreach", "id": aid, "artifacts": [str(aid)], "text": str(aid)})

    for item in pred.get("confirmed_gap_detail") or []:
        if isinstance(item, dict):
            arts = [str(a) for a in (item.get("artifacts") or []) if a]
            rows.append(
                {
                    "kind": "gap",
                    "id": item.get("id"),
                    "artifacts": arts,
                    "text": item.get("text") or item.get("id") or "",
                }
            )
    for gid in pred.get("confirmed_gaps") or []:
        if any(r.get("id") == gid for r in rows):
            continue
        rows.append({"kind": "gap", "id": gid, "artifacts": [str(gid)], "text": str(gid)})

    if pred.get("packaging_hard_cap"):
        arts = [str(a) for a in (pred.get("packaging_artifacts") or []) if a]
        if not arts:
            arts = [".python-version", "python-version", "packaging"]
        rows.append(
            {
                "kind": "packaging",
                "id": "packaging_hard_cap",
                "artifacts": arts,
                "text": "packaging hard-cap",
            }
        )
    return rows


def artifact_match(confirmed: Dict[str, Any], citation: Dict[str, Any]) -> bool:
    """Match on cited artifact (file/symbol/assertion), not exact wording."""
    cited_bits = []
    for key in ("quoted_text", "file", "axis"):
        v = citation.get(key)
        if v:
            cited_bits.append(str(v))
    cited_blob = _norm(" ".join(cited_bits))
    if not cited_blob:
        return False

    candidates = list(confirmed.get("artifacts") or [])
    if confirmed.get("id"):
        candidates.append(str(confirmed["id"]))
    if confirmed.get("text"):
        candidates.append(str(confirmed["text"]))

    for c in candidates:
        cn = _norm(c)
        if not cn:
            continue
        if cn == cited_blob or cn in cited_blob or cited_blob in cn:
            return True
        # token-ish: CellMap vs cell_map.out_shape
        if len(cn) >= 4 and cn in cited_blob:
            return True
    return False


def match_citations(
    confirmed_rows: List[Dict[str, Any]], citations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    matched: List[Dict[str, Any]] = []
    unmatched: List[Dict[str, Any]] = []
    used_conf: Set[int] = set()
    for cit in citations:
        hit_idx = None
        for i, conf in enumerate(confirmed_rows):
            if i in used_conf:
                continue
            if artifact_match(conf, cit):
                hit_idx = i
                break
        if hit_idx is None:
            unmatched.append(cit)
        else:
            used_conf.add(hit_idx)
            matched.append(
                {
                    "citation": cit.get("quoted_text") or cit.get("file"),
                    "axis": cit.get("axis"),
                    "matched_to": confirmed_rows[hit_idx].get("id"),
                    "kind": confirmed_rows[hit_idx].get("kind"),
                }
            )
    n_cit = len(citations)
    recall = (len(matched) / n_cit) if n_cit else None
    return {
        "matched": matched,
        "unmatched": unmatched,
        "recall": recall,
        "n_cited": n_cit,
        "n_matched": len(matched),
        "n_confirmed": len(confirmed_rows),
    }


def load_feedback_rows(feedback_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not feedback_dir.is_dir():
        return rows
    for path in sorted(feedback_dir.glob("*.json")):
        if path.name in {"schema.json"} or path.parent.name == "predictions":
            continue
        if path.parent != feedback_dir:
            continue
        doc = _load_json(path)
        if not doc.get("task_name"):
            continue
        pred: Dict[str, Any] = {}
        pref = doc.get("prediction_ref")
        if pref:
            pred = _load_json(ROOT / pref)
        axes = (doc.get("axes") or {}).get("adjudicated") or {}
        citations = [c for c in (doc.get("citations") or []) if isinstance(c, dict)]
        cited_texts = [c.get("quoted_text") for c in citations if c.get("quoted_text")]
        retrospective = prediction_is_retrospective(pred) if pred else False
        conf_rows = expand_confirmed_artifacts(pred) if pred else []
        match = match_citations(conf_rows, citations) if pred else None
        rows.append(
            {
                "task_name": doc.get("task_name"),
                "recorded_at": doc.get("recorded_at"),
                "predicted_verdict": pred.get("predicted_verdict"),
                "actual_verdict": doc.get("verdict"),
                "verdict_reason": doc.get("verdict_reason"),
                "confirmed_overreach": pred.get("confirmed_overreach") or [],
                "cited_overreach": cited_texts,
                "citations": citations,
                "confirmed_gaps": pred.get("confirmed_gaps") or [],
                "predicted_axes": pred.get("predicted_axes"),
                "actual_axes": axes,
                "source": doc.get("source"),
                "prediction_source": pred.get("source"),
                "retrospective": retrospective,
                "has_prediction": bool(pred.get("predicted_verdict") or pred.get("confirmed_overreach") is not None and pref),
                "prediction_ref": pref,
                "feedback_path": str(path.relative_to(ROOT)),
                "must_haves_failed": doc.get("must_haves_failed"),
                "difficulty_run": doc.get("difficulty_run"),
                "packaging_hard_cap": pred.get("packaging_hard_cap"),
                "match": match,
                "confirmed_artifact_rows": conf_rows,
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


def _fmt(x: Optional[float]) -> str:
    if x is None:
        return "n/a"
    return f"{x:.2f}"


def _section_recall(rows: List[Dict[str, Any]], *, show_precision: bool) -> List[str]:
    lines: List[str] = []
    if not rows:
        lines.append("(no rows)")
        return lines

    for r in rows:
        lines.append(
            f"- {r.get('task_name')}: verdict={r.get('actual_verdict')} "
            f"reason={r.get('verdict_reason')} pred={r.get('predicted_verdict')} "
            f"pred_source={r.get('prediction_source')}"
        )
        m = r.get("match")
        if not m:
            lines.append("  (no prediction join or no match detail)")
            continue
        if m["n_cited"] == 0:
            lines.append("  citations: none recorded on feedback — recall n/a")
        else:
            lines.append(
                f"  recall: {m['n_matched']}/{m['n_cited']} ({_fmt(m['recall'])}) "
                f"[confirmed artifacts available: {m['n_confirmed']}]"
            )
            if show_precision:
                # live only — not computed for retrospective in caller
                pass
            if m["matched"]:
                lines.append("  matched:")
                for hit in m["matched"]:
                    lines.append(
                        f"    ✓ {hit.get('citation')!r} → {hit.get('kind')}:{hit.get('matched_to')}"
                    )
            if m["unmatched"]:
                lines.append("  unmatched:")
                for miss in m["unmatched"]:
                    lines.append(
                        f"    ✗ {miss.get('quoted_text')!r} (axis={miss.get('axis')})"
                    )
    return lines


def report(rows: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append(f"# Judge calibration stats ({len(rows)} feedback records)")
    lines.append("")
    if not rows:
        lines.append("No feedback records yet.")
        return "\n".join(lines) + "\n"

    retro = [r for r in rows if r.get("retrospective")]
    live = [r for r in rows if r.get("prediction_ref") and not r.get("retrospective")]
    orphan = [r for r in rows if not r.get("prediction_ref")]

    lines.append("## Retrospective joins")
    lines.append(
        "Precision suppressed: the judge cites selectively, so a flag it did not mention "
        "is not a false positive."
    )
    lines.extend(_section_recall(retro, show_precision=False))
    lines.append("")

    lines.append("## Live joins (at-upload predictions)")
    if not live:
        lines.append("(none yet)")
    else:
        # live: report recall + precision
        for r in live:
            m = r.get("match") or {}
            conf = list(r.get("confirmed_overreach") or [])
            cit = list(r.get("cited_overreach") or [])
            # precision only on overreach id list vs cited texts (legacy); prefer artifact recall above
            from_ids_matched = 0
            if cit and conf:
                for c in cit:
                    if any(_norm(str(x)) in _norm(str(c)) or _norm(str(c)) in _norm(str(x)) for x in conf):
                        from_ids_matched += 1
            prec = None
            if conf:
                # count confirmed that matched some citation via artifact matcher
                matched_ids = {h.get("matched_to") for h in (m.get("matched") or [])}
                prec = len([c for c in conf if c in matched_ids]) / len(conf) if conf else None
            lines.append(
                f"- {r.get('task_name')}: recall={_fmt(m.get('recall'))} "
                f"precision={_fmt(prec)} (live)"
            )
        lines.extend(_section_recall(live, show_precision=True))
    lines.append("")

    if orphan:
        lines.append("## Feedback without prediction_ref")
        for r in orphan:
            lines.append(
                f"- {r.get('task_name')}: verdict={r.get('actual_verdict')} "
                f"source={r.get('source')}"
            )
        lines.append("")

    lines.append("## Per-axis |predicted − actual| (live joins only)")
    abs_sums: Dict[str, float] = defaultdict(float)
    abs_n: Dict[str, int] = defaultdict(int)
    for r in live:
        pred = r.get("predicted_axes") or {}
        act = r.get("actual_axes") or {}
        if not isinstance(pred, dict) or not isinstance(act, dict):
            continue
        for axis in AXES:
            pv, av = pred.get(axis), act.get(axis)
            if isinstance(pv, (int, float)) and isinstance(av, (int, float)):
                abs_sums[axis] += abs(float(pv) - float(av))
                abs_n[axis] += 1
    any_axis = False
    for axis in AXES:
        if abs_n[axis]:
            any_axis = True
            lines.append(f"- {axis}: MAE={abs_sums[axis]/abs_n[axis]:.2f} (n={abs_n[axis]})")
    if not any_axis:
        lines.append("(no live paired axis scores yet)")
    lines.append("")
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
