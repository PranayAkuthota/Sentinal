#!/usr/bin/env python3
"""Verify Execution-layer handoff readiness before advancing.

Does not assign verdicts. Does not mutate task packages.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent

# next checkpoint -> required prior handoff ids
REQUIRED_PRIORS: Dict[str, List[str]] = {
    "01": [],
    "02": ["01"],
    "03": ["01", "02"],
    "04": ["01", "02", "03"],
    "05": ["01", "02", "03", "04"],
    "06": ["01", "02", "03", "04", "05"],
    # Revision round: 06 already gated 01–05; requiring all six again is brittle for
    # legacy / pre-framework sessions. Escape: --resume-revision.
    "07": ["06"],
}


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def handoff_path(work: Path, nn: str) -> Path:
    return work / "session" / "execution" / f"{nn}__handoff.md"


def parse_status(text: str) -> Optional[str]:
    m = re.search(r"(?im)^\s*status\s*:\s*(complete|blocked|partial)\s*$", text)
    if m:
        return m.group(1).lower()
    m = re.search(r"(?im)^\s*-\s*status\s*:\s*(complete|blocked|partial)\s*$", text)
    if m:
        return m.group(1).lower()
    # loose fallback
    m = re.search(r"(?i)\bstatus\b\s*[:=]\s*(complete|blocked|partial)", text)
    return m.group(1).lower() if m else None


def check_handoff(path: Path) -> Tuple[bool, str]:
    if not path.is_file():
        return False, f"missing handoff: {path}"
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text.strip()) < 40:
        return False, f"handoff too thin: {path}"
    status = parse_status(text)
    if status == "blocked":
        return False, f"handoff blocked: {path}"
    if status is None:
        return False, f"handoff missing status field (complete|blocked|partial): {path}"
    if status == "partial":
        return False, f"handoff still partial: {path}"
    return True, f"ok {path.name} status={status}"


def main() -> int:
    p = argparse.ArgumentParser(description="Check Execution checkpoint readiness")
    p.add_argument("--task-name", required=True)
    p.add_argument(
        "--next",
        required=True,
        help="Next checkpoint id: 01..07",
    )
    p.add_argument(
        "--require-verdicts",
        action="store_true",
        help="Also require Public==Duplicate recorded (implied for --next 05/06/07)",
    )
    p.add_argument(
        "--resume-revision",
        metavar="REASON",
        default=None,
        help=(
            "For --next 07 only: allow missing 06 handoff when revising a task whose "
            "earlier handoffs predate the framework. Reason is recorded in the log; "
            "verdicts are still required."
        ),
    )
    p.add_argument(
        "--platform-zip",
        metavar="PATH",
        default=None,
        help=(
            "For --next 07: absolute path to the platform-downloaded corrected ZIP. "
            "When task_outputs/<task>/updated_zip_file/<task>__corrected.zip also exists, "
            "SHA-256 must match or the checkpoint FAILS (F-014 — stale mirror)."
        ),
    )
    args = p.parse_args()

    nn = args.next.strip()
    if nn not in REQUIRED_PRIORS:
        die(f"--next must be one of {list(REQUIRED_PRIORS)}")

    if args.resume_revision and nn != "07":
        die("--resume-revision is only valid with --next 07")
    if args.platform_zip and nn != "07":
        die("--platform-zip is only valid with --next 07")

    work = ROOT / "work" / args.task_name
    if not work.is_dir():
        die(f"missing work session: {work}")

    errors: List[str] = []
    notes: List[str] = []

    for prior in REQUIRED_PRIORS[nn]:
        ok, msg = check_handoff(handoff_path(work, prior))
        if (
            not ok
            and nn == "07"
            and prior == "06"
            and args.resume_revision
            and str(args.resume_revision).strip()
        ):
            notes.append(
                f"resume-revision waived missing/incomplete 06 handoff: "
                f"{str(args.resume_revision).strip()!r}"
            )
            continue
        (notes if ok else errors).append(msg)

    need_verdicts = args.require_verdicts or nn in ("05", "06", "07")
    if need_verdicts:
        session = load_json(work / "session" / "session.json")
        outputs = load_json(ROOT / "task_outputs" / args.task_name / "workflow_state.json")
        public = session.get("public_analysis") or outputs.get("public_analysis")
        duplicate = session.get("duplicate_analysis") or outputs.get("duplicate_analysis")
        internal = session.get("internal_validity") or outputs.get("internal_validity")
        if not public or not duplicate:
            errors.append("verdicts not recorded (need set-verdicts before 05/06/07)")
        elif str(public).strip() != str(duplicate).strip():
            errors.append(f"Public ({public}) != Duplicate ({duplicate})")
        else:
            notes.append(f"verdicts ok public=duplicate={public} internal={internal}")

    # F-014: never revise against a stale updated_zip_file mirror
    if nn == "07":
        mirror = (
            ROOT
            / "task_outputs"
            / args.task_name
            / "updated_zip_file"
            / f"{args.task_name}__corrected.zip"
        )
        platform = Path(args.platform_zip).expanduser() if args.platform_zip else None
        if mirror.is_file() and platform is None:
            errors.append(
                "F-014 FATAL: updated_zip_file mirror exists but --platform-zip was not "
                f"provided. Pass the platform-downloaded corrected ZIP and compare SHA-256 "
                f"(mirror={mirror}). Do NOT revise from the mirror alone."
            )
        elif mirror.is_file() and platform is not None:
            if not platform.is_file():
                errors.append(f"F-014 FATAL: --platform-zip not found: {platform}")
            else:
                import hashlib

                def _sha(p: Path) -> str:
                    h = hashlib.sha256()
                    h.update(p.read_bytes())
                    return h.hexdigest()

                m_digest = _sha(mirror)
                p_digest = _sha(platform)
                if m_digest != p_digest:
                    errors.append(
                        "F-014 FATAL: updated_zip_file mirror SHA-256 does not match "
                        f"platform zip.\n"
                        f"    mirror   = {mirror}\n"
                        f"    mirror_sha256   = {m_digest}\n"
                        f"    platform = {platform}\n"
                        f"    platform_sha256 = {p_digest}\n"
                        "    The mirror is STALE. Re-import the platform zip before any "
                        "revision edits — do not revise the wrong package."
                    )
                else:
                    notes.append(
                        f"platform zip SHA-256 matches updated_zip_file mirror ({m_digest[:16]}…)"
                    )
        elif platform is not None and platform.is_file():
            notes.append(f"platform zip provided (no updated_zip_file mirror): {platform}")

    print("CHECKPOINT READY")
    print(f"  task: {args.task_name}")
    print(f"  next: {nn}")
    for n in notes:
        print(f"  OK: {n}")
    if errors:
        print("  FAILED:")
        for e in errors:
            print(f"    - {e}")
        return 1
    print("  RESULT: ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
