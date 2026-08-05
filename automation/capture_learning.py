#!/usr/bin/env python3
"""Post-task learning capture for Sentinel Submitter framework.

Derives candidate patterns from real task state only. Never emits placeholders
such as "(edit)". If nothing reusable is found, writes a short "no new pattern"
proposal and exits 0.

Never modifies work/ ZIPs, completed_tasks/, or policy rules. Never decides verdicts.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
PROPOSALS = ROOT / "knowledge" / "proposals"
FEEDBACK_DIR = ROOT / "knowledge" / "judge_feedback"

FORBIDDEN_PLACEHOLDERS = ("(edit)", "…", "...")


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
    text = re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "<task-id>",
        text,
        flags=re.I,
    )
    text = re.sub(r"https?://github\.com/\S+", "<source-url>", text)
    text = re.sub(r"\b[0-9a-f]{40}\b", "<commit-sha>", text)
    return text


def _feedback_for_task(task: str) -> Dict[str, Any]:
    direct = FEEDBACK_DIR / f"{task}.json"
    if direct.is_file():
        return load_json(direct)
    # also accept mirror
    mirror = ROOT / "task_outputs" / task / "judge_feedback.json"
    if mirror.is_file():
        return load_json(mirror)
    return {}


def derive_candidates(
    task: str,
    *,
    state: Dict[str, Any],
    session: Dict[str, Any],
    notes: str,
) -> Tuple[List[str], List[str], List[str]]:
    """Return (patterns, automation_ops, failure_entries) from real state only."""
    patterns: List[str] = []
    automation: List[str] = []
    failures: List[str] = []

    outputs = ROOT / "task_outputs" / task
    feedback = _feedback_for_task(task)
    rehearsal = load_json(outputs / "judge_rehearsal.json")
    prep = load_json(outputs / "judge_prep.json")
    preflight = load_json(outputs / "preflight_report.json")

    # --- judge_feedback: axes that moved + fixes ---
    if feedback:
        axes = (feedback.get("axes") or {}).get("adjudicated") or {}
        moved = [
            f"{k}={v}"
            for k, v in sorted(axes.items())
            if isinstance(v, (int, float))
        ]
        if moved:
            patterns.append(
                "Judge feedback recorded adjudicated axes: "
                + ", ".join(moved)
                + (
                    f" (verdict={feedback.get('verdict')}"
                    f", reason={feedback.get('verdict_reason')})"
                    if feedback.get("verdict")
                    else ""
                )
            )
        for fix in feedback.get("fixes_applied") or []:
            if not isinstance(fix, dict):
                continue
            change = (fix.get("change") or "").strip()
            if not change:
                continue
            axis = fix.get("axis_targeted") or "unspecified-axis"
            fpath = fix.get("file") or "unspecified-file"
            patterns.append(
                f"Fix that targeted {axis}: {redact(change)} (file={fpath})"
            )
        mh = feedback.get("must_haves_failed")
        if mh:
            failures.append(
                f"category: agent_judge_must_have\n"
                f"  symptom: must_haves_failed={mh}\n"
                f"  recovery: address cited must-haves before re-upload; "
                f"Difficulty stays blocked until Judge clears"
            )
        if feedback.get("difficulty_run") is False:
            automation.append(
                "When verdict is DISCUSS/REMOVE, record difficulty_run=false — "
                "do not invent Difficulty results (P-010)"
            )

    # --- rehearsal CONFIRMED that survived toward upload ---
    confirmed_o = list(rehearsal.get("confirmed_overreach") or [])
    confirmed_g = list(rehearsal.get("confirmed_gaps") or [])
    if not confirmed_o and prep:
        confirmed_o = list(prep.get("overreach_unexplained") or [])
    if not confirmed_g and prep:
        confirmed_g = list(prep.get("coverage_gaps_unexplained") or [])
    if confirmed_o:
        patterns.append(
            "Rehearsal/prep CONFIRMED overreach candidates at handoff: "
            + ", ".join(str(x) for x in confirmed_o[:20])
        )
    if confirmed_g:
        patterns.append(
            "Rehearsal/prep CONFIRMED coverage gaps at handoff: "
            + ", ".join(str(x) for x in confirmed_g[:20])
        )

    # --- accept-risk overrides ---
    if state.get("judge_prep_accept_risk"):
        reason = state.get("judge_prep_accept_risk_reason") or "reason not recorded"
        patterns.append(
            f"Static/judge_prep accept-risk used: {redact(str(reason))}"
        )
        automation.append(
            "Surface judge_prep_accept_risk_reason in Comments for Reviewer when packaging"
        )

    warnings = list(state.get("warnings") or [])
    for w in warnings:
        ws = str(w)
        if "accept-risk" in ws.lower():
            patterns.append(f"Preflight warning under accept-risk: {redact(ws)}")

    # --- validation evidence ---
    for key, label in (
        ("oracle_status", "Oracle"),
        ("nop_status", "NOP"),
        ("docker_build_status", "Docker"),
    ):
        st = state.get(key) or session.get(key)
        if st in ("passed", "confirmed_by_logs", "failed", "not_run"):
            reward = None
            if key == "oracle_status":
                reward = state.get("oracle_reward")
            elif key == "nop_status":
                reward = state.get("nop_reward")
            bit = f"{label} validation={st}"
            if reward is not None:
                bit += f" reward={reward}"
            automation.append(bit)

    # --- blocker walk residue ---
    blockers = list(state.get("blocking_issues") or [])
    if blockers:
        failures.append(
            "category: preflight_blocker\n"
            f"  symptom: lingering blockers at capture: {redact(json.dumps(blockers[:8]))}\n"
            "  recovery: clear SUBMITTER_BLOCKERS before package-fixable"
        )
    elif state.get("ready_to_package") is True:
        automation.append("Preflight ready_to_package=true at learning capture")

    # --- free-text notes only if non-empty and not placeholder ---
    notes_clean = (notes or "").strip()
    if notes_clean and notes_clean not in ("…", "...", "(edit)"):
        patterns.append(f"Operator notes: {redact(notes_clean)}")

    # Deduplicate while preserving order
    def uniq(items: List[str]) -> List[str]:
        seen = set()
        out = []
        for it in items:
            if it in seen:
                continue
            seen.add(it)
            out.append(it)
        return out

    return uniq(patterns), uniq(automation), uniq(failures)


def render_proposal(
    task: str,
    *,
    ts: str,
    branch: str,
    f2p: Any,
    patterns: List[str],
    automation: List[str],
    failures: List[str],
) -> str:
    if not patterns and not automation and not failures:
        return (
            f"# Learning proposal — no new pattern\n\n"
            f"- Generated: {ts} UTC\n"
            f"- Task ref: `{task}` (do not promote UUID into pattern titles)\n"
            f"- Branch recorded: {branch}\n"
            f"- Structural f2p count: {f2p}\n\n"
            f"## Result\n\n"
            f"no new pattern\n\n"
            f"No reusable candidates were derived from judge_feedback, "
            f"judge_prep/rehearsal CONFIRMED rows, accept-risk overrides, "
            f"or validation/blocker state.\n\n"
            f"---\n\n"
            f"**Promotion rule:** Human merges accepted items into "
            f"`knowledge/patterns/` or `knowledge/failures/`.\n"
            f"Never auto-edit `.cursor/rules/Review_Guidelines.mdc`.\n"
        )

    def numbered(items: List[str]) -> str:
        if not items:
            return "_none derived_\n"
        return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1)) + "\n"

    fail_block = "_none derived_\n"
    if failures:
        fail_block = "\n".join(f"- {f}" for f in failures) + "\n"

    return (
        f"# Learning proposal (pending human review)\n\n"
        f"- Generated: {ts} UTC\n"
        f"- Task ref: `{task}` (do not promote UUID into pattern titles)\n"
        f"- Branch recorded: {branch}\n"
        f"- Structural f2p count: {f2p}\n\n"
        f"## Candidate reusable patterns\n\n"
        f"Derived from task state only. Delete anything still task-specific before promoting.\n\n"
        f"{numbered(patterns)}\n"
        f"## Automation opportunities (deterministic only)\n\n"
        f"{numbered(automation)}\n"
        f"## Suggested failure catalog entries\n\n"
        f"{fail_block}\n"
        f"---\n\n"
        f"**Promotion rule:** Human merges accepted items into "
        f"`knowledge/patterns/` or `knowledge/failures/`.\n"
        f"Never auto-edit `.cursor/rules/Review_Guidelines.mdc`.\n"
    )


def assert_no_placeholders(text: str) -> None:
    for bad in FORBIDDEN_PLACEHOLDERS:
        # Allow ellipsis only inside redacted content? User said never "(edit)".
        # Ban "(edit)" hard. Ban standalone template ellipses we used to ship.
        if bad == "(edit)" and bad in text:
            raise RuntimeError(f"placeholder {bad!r} must not appear in proposal output")
    if re.search(r"(?m)^\s*\d+\.\s*\(edit\)", text):
        raise RuntimeError("numbered (edit) placeholder must not appear")
    if re.search(r"(?m)^\s*[-*]\s*(…|\.\.\.)\s*$", text):
        raise RuntimeError("bullet placeholder ellipsis must not appear")


def build_proposal_text(task: str, notes: str = "") -> Tuple[str, bool]:
    """Return (body, has_candidates)."""
    work = ROOT / "work" / task
    outputs = ROOT / "task_outputs" / task
    if not work.exists() and not outputs.exists():
        die(f"no work/ or task_outputs/ for {task}")

    state = load_json(outputs / "workflow_state.json")
    session = load_json(work / "session" / "session.json") if work.exists() else {}
    branch = state.get("duplicate_analysis") or session.get("duplicate_analysis") or "unknown"
    f2p = state.get("fail_to_pass_count")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    patterns, automation, failures = derive_candidates(
        task, state=state, session=session, notes=notes
    )
    body = render_proposal(
        task,
        ts=ts,
        branch=branch,
        f2p=f2p,
        patterns=patterns,
        automation=automation,
        failures=failures,
    )
    assert_no_placeholders(body)
    has = bool(patterns or automation or failures)
    return body, has


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Capture reusable learning proposal from real task state (no placeholders)"
    )
    p.add_argument("--task-name", required=True)
    p.add_argument("--notes", default="", help="Optional friction notes (redacted; no placeholders)")
    args = p.parse_args(argv)

    task = args.task_name
    body, has = build_proposal_text(task, notes=args.notes)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    PROPOSALS.mkdir(parents=True, exist_ok=True)
    out = PROPOSALS / f"{ts}__{task}__proposal.md"
    out.write_text(body, encoding="utf-8")
    if has:
        print(f"PROPOSAL WRITTEN: {out}")
        print("Review and promote manually. Archives untouched.")
    else:
        print(f"PROPOSAL WRITTEN (no new pattern): {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
