#!/usr/bin/env python3
"""Sentinel branch-aware submitter — file-management helpers only.

This script never decides task verdicts and never modifies task logic.
It manages intake, session layout, packaging, and archive moves.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent

IGNORE_DIR_NAMES = {
    "legacy_backup",
    "workspace_archive",
    "completed_tasks",
    "task_outputs",
    "work",
    "automation",
    ".cursor",
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
}

EXCLUDE_ZIP_NAMES = {
    "__pycache__",
    ".pyc",
    ".DS_Store",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "node_modules",
    ".idea",
    ".vscode",
    "metadata.json",
    "runs",
}

TASK_MARKERS = (
    "instruction.md",
    "task.toml",
    "environment",
    "solution",
    "tests",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def ensure_workspace() -> None:
    for name in (
        "incoming_tasks",
        "work",
        "task_outputs",
        "completed_tasks",
        "workspace_archive",
        "automation",
    ):
        (WORKSPACE_ROOT / name).mkdir(parents=True, exist_ok=True)


def is_ignored_path(path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(WORKSPACE_ROOT.resolve())
    except ValueError:
        return True
    parts = set(rel.parts)
    return bool(parts & IGNORE_DIR_NAMES)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_task_name(name: str) -> str:
    base = Path(name).stem
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
    if not base:
        die("Could not derive a safe task name from ZIP")
    if ".." in base or "/" in base or "\\" in base:
        die(f"Rejected unsafe task name: {base}")
    return base


def find_candidate_zips(explicit: Optional[str]) -> List[Path]:
    if explicit:
        p = Path(explicit).expanduser()
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        else:
            p = p.resolve()
        if not str(p).startswith(str(WORKSPACE_ROOT.resolve())) and not p.exists():
            # Allow absolute paths that exist and are readable ZIPs outside ignore dirs
            pass
        if not p.exists() or not p.is_file():
            die(f"ZIP not found: {p}")
        if p.suffix.lower() != ".zip":
            die(f"Not a ZIP file: {p}")
        return [p]

    candidates: List[Path] = []
    search_roots = [WORKSPACE_ROOT / "incoming_tasks", WORKSPACE_ROOT]
    for root in search_roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("*.zip")):
            if path.name == "Sentinal.zip":
                continue
            if is_ignored_path(path):
                continue
            # Skip workspace self-archives at root named like Sentinal.zip already handled
            if path.parent.resolve() == WORKSPACE_ROOT.resolve() and path.stem.lower() in {
                "sentinal",
                "sentinel",
            }:
                continue
            candidates.append(path.resolve())

    # Deduplicate
    uniq: List[Path] = []
    seen = set()
    for c in candidates:
        key = str(c)
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    return uniq


def find_task_root(extracted: Path) -> Path:
    # Prefer direct markers at top, then task/, then first nested match
    def score(d: Path) -> int:
        return sum(1 for m in TASK_MARKERS if (d / m).exists())

    if score(extracted) >= 3:
        return extracted
    task_dir = extracted / "task"
    if task_dir.is_dir() and score(task_dir) >= 3:
        return task_dir

    best: Optional[Path] = None
    best_score = 0
    for dirpath, dirnames, _filenames in os.walk(extracted):
        # prune ignored
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIR_NAMES and d != "runs"]
        p = Path(dirpath)
        s = score(p)
        if s > best_score:
            best_score = s
            best = p
            if s >= 5:
                break
    if best is None or best_score < 3:
        die(f"Could not locate task root under {extracted}")
    return best


def detect_format(task_root: Path) -> str:
    current = any(
        (task_root / p).exists()
        for p in (
            "solution/golden.patch",
            "environment/problem_statement.md",
            "tests/config.json",
            "tests/grade.py",
        )
    )
    legacy = any(
        (task_root / p).exists()
        for p in (
            "solution/init_state.patch",
            "solution/solution.patch",
            "tests/files",
        )
    )
    if current and legacy:
        return "hybrid"
    if current:
        return "current"
    if legacy:
        return "legacy"
    return "unknown"


def detect_runs(extracted: Path, task_root: Path) -> Optional[str]:
    candidates = [
        extracted / "runs",
        task_root.parent / "runs",
        WORKSPACE_ROOT / "runs",
    ]
    for c in candidates:
        if c.is_dir():
            return str(c.resolve())
    return None


def session_paths(task_name: str) -> Dict[str, Path]:
    work = WORKSPACE_ROOT / "work" / task_name
    return {
        "work": work,
        "original": work / "original",
        "extracted_original": work / "extracted_original",
        "working_copy": work / "working_copy",
        "session": work / "session",
        "validation_logs": work / "session" / "validation_logs",
        "analysis": work / "analysis",
        "session_json": work / "session" / "session.json",
        "platform_input": work / "session" / "platform_input.txt",
        "outputs": WORKSPACE_ROOT / "task_outputs" / task_name,
        "updated_zip_dir": WORKSPACE_ROOT / "task_outputs" / task_name / "updated_zip_file",
        "invalid_evidence_dir": WORKSPACE_ROOT / "task_outputs" / task_name / "invalid_evidence",
    }


def load_session(task_name: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    if task_name:
        path = session_paths(task_name)["session_json"]
        if not path.exists():
            die(f"No session for task: {task_name}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return task_name, data

    work_root = WORKSPACE_ROOT / "work"
    sessions: List[Tuple[str, Path]] = []
    if work_root.exists():
        for child in sorted(work_root.iterdir()):
            sj = child / "session" / "session.json"
            if child.is_dir() and sj.exists():
                sessions.append((child.name, sj))
    if not sessions:
        die("No active work session found. Run intake first.")
    if len(sessions) > 1:
        names = ", ".join(n for n, _ in sessions)
        die(f"Multiple active sessions ({names}). Pass --task-name.")
    name, path = sessions[0]
    return name, json.loads(path.read_text(encoding="utf-8"))


def save_session(task_name: str, data: Dict[str, Any]) -> None:
    path = session_paths(task_name)["session_json"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def copytree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def should_exclude_member(name: str) -> bool:
    parts = Path(name).parts
    for part in parts:
        if part in EXCLUDE_ZIP_NAMES:
            return True
        if part.endswith(".pyc") or part.endswith(".orig") or part.endswith(".bak") or part.endswith(".swp"):
            return True
        if part == "runs":
            return True
    lower = name.lower()
    if "ground_truth" in lower:
        return True
    return False


def package_flat_task_zip(task_root: Path, dest_zip: Path) -> None:
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    if dest_zip.exists():
        dest_zip.unlink()
    with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(task_root):
            # Mutate dirnames in place to prune
            dirnames[:] = [
                d
                for d in dirnames
                if d not in EXCLUDE_ZIP_NAMES
                and d not in {"runs", "session", "analysis", "original", "extracted_original"}
            ]
            for fn in filenames:
                full = Path(dirpath) / fn
                rel = full.relative_to(task_root).as_posix()
                if should_exclude_member(rel):
                    continue
                # Never include outer task/ wrapper as an extra nesting: contents are already flat at task_root
                zf.write(full, arcname=rel)


def cmd_intake(args: argparse.Namespace) -> None:
    ensure_workspace()
    candidates = find_candidate_zips(args.zip)
    if not candidates:
        die("No candidate ZIP found in incoming_tasks/ or workspace root.")
    if len(candidates) > 1 and not args.zip:
        print("Multiple candidate ZIPs found. Specify one with --zip:")
        for c in candidates:
            print(f"  - {c}")
        raise SystemExit(2)

    src_zip = candidates[0]
    if src_zip.stat().st_size <= 0:
        die(f"ZIP is empty: {src_zip}")
    if not zipfile.is_zipfile(src_zip):
        die(f"Not a readable ZIP: {src_zip}")

    # Reject path traversal inside ZIP
    with zipfile.ZipFile(src_zip, "r") as zf:
        for info in zf.infolist():
            name = info.filename
            if name.startswith("/") or name.startswith("\\") or ".." in Path(name).parts:
                die(f"ZIP contains unsafe path: {name}")

    task_name = args.task_name or safe_task_name(src_zip.name)
    paths = session_paths(task_name)
    if paths["work"].exists() and not args.force:
        die(f"Work session already exists: {paths['work']} (use --force to replace)")

    if paths["work"].exists() and args.force:
        shutil.rmtree(paths["work"])

    for key in (
        "original",
        "extracted_original",
        "working_copy",
        "session",
        "validation_logs",
        "analysis",
        "outputs",
        "updated_zip_dir",
        "invalid_evidence_dir",
    ):
        paths[key].mkdir(parents=True, exist_ok=True)

    preserved = paths["original"] / src_zip.name
    shutil.copy2(src_zip, preserved)
    digest = sha256_file(preserved)

    # Extract untouched original
    with zipfile.ZipFile(preserved, "r") as zf:
        zf.extractall(paths["extracted_original"])

    task_root = find_task_root(paths["extracted_original"])
    # Working copy is a separate full copy of extracted_original
    copytree(paths["extracted_original"], paths["working_copy"])
    working_task_root = find_task_root(paths["working_copy"])
    fmt = detect_format(task_root)
    runs_path = detect_runs(paths["extracted_original"], task_root)

    if args.platform_input:
        pip = Path(args.platform_input)
        if pip.exists():
            shutil.copy2(pip, paths["platform_input"])
        else:
            paths["platform_input"].write_text(args.platform_input, encoding="utf-8")
    elif not paths["platform_input"].exists():
        paths["platform_input"].write_text("", encoding="utf-8")

    session = {
        "task_name": task_name,
        "original_zip_name": src_zip.name,
        "sha256": digest,
        "original_path": str(preserved.resolve()),
        "source_zip_path": str(src_zip.resolve()),
        "extracted_original_path": str(paths["extracted_original"].resolve()),
        "working_copy_path": str(paths["working_copy"].resolve()),
        "real_task_root": str(task_root.resolve()),
        "working_task_root": str(working_task_root.resolve()),
        "runs_path": runs_path,
        "format": fmt,
        "start_timestamp": utc_now(),
        "current_workflow_phase": "intake_complete",
        "public_analysis": None,
        "internal_validity": None,
        "duplicate_analysis": None,
        "branch": None,
        "timestamps": {
            "intake": utc_now(),
            "initial_audit_complete": None,
            "fix_start": None,
            "fix_complete": None,
            "validation_start": None,
            "validation_complete": None,
            "packaging": None,
            "final_response": None,
            "pauses": [],
            "user_adjustments": [],
        },
        "output_paths": {
            "task_outputs": str(paths["outputs"].resolve()),
            "platform_answers": str((paths["outputs"] / "platform_answers.txt").resolve()),
            "submitter_audit": str((paths["outputs"] / "submitter_audit.md").resolve()),
            "findings_and_changes": str((paths["outputs"] / "findings_and_changes.md").resolve()),
            "validation_summary": str((paths["outputs"] / "validation_summary.md").resolve()),
            "updated_zip_dir": str(paths["updated_zip_dir"].resolve()),
            "invalid_evidence_dir": str(paths["invalid_evidence_dir"].resolve()),
            "corrected_zip": None,
            "invalid_evidence_zip": None,
        },
        "notes": "Automation manages files only. Verdicts are set by the submitter workflow, not this script.",
    }
    save_session(task_name, session)

    print("INTAKE COMPLETE")
    print(f"  task_name:           {task_name}")
    print(f"  original_zip:        {preserved}")
    print(f"  sha256:              {digest}")
    print(f"  extracted_original:  {paths['extracted_original']}")
    print(f"  working_copy:        {paths['working_copy']}")
    print(f"  real_task_root:      {task_root}")
    print(f"  working_task_root:   {working_task_root}")
    print(f"  runs_path:           {runs_path or '(none)'}")
    print(f"  format:              {fmt}")
    print(f"  session:             {paths['session_json']}")
    print(f"  outputs:             {paths['outputs']}")


def cmd_status(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    paths = session_paths(task_name)
    print("SESSION STATUS")
    print(f"  task_name:          {task_name}")
    print(f"  format:             {session.get('format')}")
    print(f"  phase:              {session.get('current_workflow_phase')}")
    print(f"  public_analysis:    {session.get('public_analysis')}")
    print(f"  internal_validity:  {session.get('internal_validity')}")
    print(f"  duplicate_analysis: {session.get('duplicate_analysis')}")
    print(f"  branch:             {session.get('branch')}")
    print(f"  original_path:      {session.get('original_path')}")
    print(f"  extracted_original: {session.get('extracted_original_path')}")
    print(f"  working_copy:       {session.get('working_copy_path')}")
    print(f"  real_task_root:     {session.get('real_task_root')}")
    print(f"  runs_path:          {session.get('runs_path')}")
    outs = session.get("output_paths") or {}
    print(f"  corrected_zip:      {outs.get('corrected_zip')}")
    print(f"  invalid_evidence:   {outs.get('invalid_evidence_zip')}")
    print(f"  outputs_dir:        {paths['outputs']}")
    if paths["outputs"].exists():
        for p in sorted(paths["outputs"].rglob("*")):
            if p.is_file():
                print(f"    - {p.relative_to(paths['outputs'])}")


def update_verdicts_if_provided(session: Dict[str, Any], args: argparse.Namespace) -> None:
    if getattr(args, "public_analysis", None):
        session["public_analysis"] = args.public_analysis
    if getattr(args, "internal_validity", None):
        session["internal_validity"] = args.internal_validity
    if getattr(args, "duplicate_analysis", None):
        session["duplicate_analysis"] = args.duplicate_analysis
        session["branch"] = args.duplicate_analysis


def cmd_package_fixable(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    update_verdicts_if_provided(session, args)
    if session.get("duplicate_analysis") not in (None, "Fixable"):
        if session.get("duplicate_analysis") != "Fixable":
            die(
                "package-fixable requires Duplicate Analysis = Fixable "
                f"(got {session.get('duplicate_analysis')}). "
                "Set with --duplicate-analysis Fixable if recording now."
            )

    working_root = Path(session["working_task_root"])
    if not working_root.exists():
        die(f"Working task root missing: {working_root}")

    # Never package from extracted_original
    if Path(session["extracted_original_path"]) in working_root.parents or working_root == Path(
        session["extracted_original_path"]
    ):
        die("Refusing to package from extracted_original")

    paths = session_paths(task_name)
    dest = paths["updated_zip_dir"] / f"{task_name}__corrected.zip"
    # Safety: never overwrite original
    if Path(session["original_path"]).resolve() == dest.resolve():
        die("Refusing to overwrite original ZIP")

    package_flat_task_zip(working_root, dest)

    # Verify flat structure: no top-level runs/, and preferably no sole outer task/
    with zipfile.ZipFile(dest, "r") as zf:
        names = zf.namelist()
        if any(n == "runs/" or n.startswith("runs/") for n in names):
            die("Packaged ZIP unexpectedly contains runs/")
        top = {n.split("/")[0] for n in names if n}
        if top == {"task"}:
            die("Packaged ZIP still wrapped in outer task/ — flatten task root before packaging")

    session["duplicate_analysis"] = session.get("duplicate_analysis") or "Fixable"
    session["branch"] = "Fixable"
    if session.get("public_analysis") is None:
        session["public_analysis"] = "Fixable"
    session["current_workflow_phase"] = "packaged_fixable"
    session["timestamps"]["packaging"] = utc_now()
    session["output_paths"]["corrected_zip"] = str(dest.resolve())
    save_session(task_name, session)

    print("PACKAGE FIXABLE COMPLETE")
    print(f"  corrected_zip: {dest}")
    print(f"  original_preserved: {session['original_path']}")


def cmd_package_invalid(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    update_verdicts_if_provided(session, args)
    if session.get("duplicate_analysis") not in (None, "Invalid/Not Fixable"):
        if session.get("duplicate_analysis") != "Invalid/Not Fixable":
            die(
                "package-invalid requires Duplicate Analysis = Invalid/Not Fixable "
                f"(got {session.get('duplicate_analysis')})"
            )

    paths = session_paths(task_name)
    dest = paths["invalid_evidence_dir"] / f"{task_name}__unfixable_evidence.zip"
    staging = paths["work"] / "_invalid_evidence_staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    # Include working copy snapshot (safe latest attempt), validation logs, analysis, summary
    wc = Path(session["working_copy_path"])
    if wc.exists():
        copytree(wc, staging / "working_copy")
    logs = paths["validation_logs"]
    if logs.exists():
        copytree(logs, staging / "validation_logs")
    analysis = paths["analysis"]
    if analysis.exists():
        copytree(analysis, staging / "analysis")

    summary = staging / "evidence_summary.md"
    summary.write_text(
        "\n".join(
            [
                "# Unfixable Evidence Summary",
                "",
                f"- Task: `{task_name}`",
                f"- Original ZIP: `{session.get('original_path')}`",
                f"- SHA-256: `{session.get('sha256')}`",
                f"- Packaged at: `{utc_now()}`",
                "",
                "## Purpose",
                "",
                "This archive is a **manual-review evidence package**.",
                "It is **not** a corrected valid submission ZIP.",
                "",
                "## Reproduction",
                "",
                "1. Keep the original ZIP unchanged.",
                "2. Inspect `working_copy/` for any diagnostic attempt.",
                "3. Read `validation_logs/` and `analysis/` when present.",
                "4. Do not upload this archive as a valid corrected task.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    if args.summary_file:
        extra = Path(args.summary_file)
        if extra.exists():
            shutil.copy2(extra, staging / "unfixable_explanation.txt")

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for dirpath, _dirnames, filenames in os.walk(staging):
            for fn in filenames:
                full = Path(dirpath) / fn
                rel = full.relative_to(staging).as_posix()
                zf.write(full, arcname=rel)

    shutil.rmtree(staging)

    session["duplicate_analysis"] = session.get("duplicate_analysis") or "Invalid/Not Fixable"
    session["branch"] = "Invalid/Not Fixable"
    if session.get("public_analysis") is None:
        session["public_analysis"] = "Invalid/Not Fixable"
    session["current_workflow_phase"] = "packaged_invalid"
    session["timestamps"]["packaging"] = utc_now()
    session["output_paths"]["invalid_evidence_zip"] = str(dest.resolve())
    # Ensure no corrected ZIP claim
    session["output_paths"]["corrected_zip"] = None
    save_session(task_name, session)

    print("PACKAGE INVALID COMPLETE")
    print(f"  evidence_zip: {dest}")
    print(f"  original_preserved: {session['original_path']}")
    print("  note: This is NOT a corrected valid submission ZIP.")


def cmd_archive(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    paths = session_paths(task_name)
    dest_parent = WORKSPACE_ROOT / "completed_tasks"
    dest_parent.mkdir(parents=True, exist_ok=True)
    dest = dest_parent / task_name
    if dest.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        dest = dest_parent / f"{task_name}__{stamp}"
    shutil.move(str(paths["work"]), str(dest))
    session["current_workflow_phase"] = "archived"
    session["archived_path"] = str(dest.resolve())
    # Write a small pointer beside outputs
    pointer = paths["outputs"] / "archived_session_path.txt"
    paths["outputs"].mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(dest.resolve()) + "\n", encoding="utf-8")
    print("ARCHIVE COMPLETE")
    print(f"  moved_to: {dest}")


def cmd_set_verdicts(args: argparse.Namespace) -> None:
    """Optional helper to record verdicts without deciding them."""
    task_name, session = load_session(args.task_name)
    if not args.public_analysis or not args.internal_validity or not args.duplicate_analysis:
        die("Require --public-analysis, --internal-validity, and --duplicate-analysis")
    # Public must match Duplicate semantically (allow Valid as-is / Valid-as-is spelling)
    pub = args.public_analysis
    dup = args.duplicate_analysis

    def _norm_analysis(value: str) -> str:
        v = value.strip()
        mapping = {
            "Valid as-is": "Valid-as-is",
            "Valid-as-is": "Valid-as-is",
            "Fixable": "Fixable",
            "Invalid/Not Fixable": "Invalid/Not Fixable",
            "Invalid-Not Fixable": "Invalid/Not Fixable",
            "Invalid": "Invalid/Not Fixable",
        }
        return mapping.get(v, v)

    if _norm_analysis(pub) != _norm_analysis(dup):
        die(f"Public Main Analysis must match Duplicate Analysis (got {pub!r} vs {dup!r})")
    session["public_analysis"] = args.public_analysis
    session["internal_validity"] = args.internal_validity
    session["duplicate_analysis"] = args.duplicate_analysis
    session["branch"] = args.duplicate_analysis
    session["internal_validity_reason"] = args.reason or session.get("internal_validity_reason")
    session["current_workflow_phase"] = "verdicts_recorded"
    save_session(task_name, session)
    print("VERDICTS RECORDED")
    print(f"  public:   {session['public_analysis']}")
    print(f"  internal: {session['internal_validity']}")
    print(f"  duplicate:{session['duplicate_analysis']}")
    print(f"  branch:   {session['branch']}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Sentinel submitter file-management automation (no verdict decisions)."
    )
    sub = p.add_subparsers(dest="command", required=True)

    intake = sub.add_parser("intake", help="Intake a ZIP and create a work session")
    intake.add_argument("--zip", help="Explicit path to the task ZIP")
    intake.add_argument("--task-name", help="Override derived task name")
    intake.add_argument("--platform-input", help="Path or inline text for platform_input.txt")
    intake.add_argument("--force", action="store_true", help="Replace existing work session")
    intake.set_defaults(func=cmd_intake)

    status = sub.add_parser("status", help="Show current session status")
    status.add_argument("--task-name")
    status.set_defaults(func=cmd_status)

    pf = sub.add_parser("package-fixable", help="Package corrected working_copy as flat ZIP")
    pf.add_argument("--task-name")
    pf.add_argument("--duplicate-analysis", choices=["Fixable"])
    pf.add_argument("--public-analysis")
    pf.add_argument("--internal-validity")
    pf.set_defaults(func=cmd_package_fixable)

    pi = sub.add_parser("package-invalid", help="Package unfixable evidence ZIP")
    pi.add_argument("--task-name")
    pi.add_argument("--duplicate-analysis", choices=["Invalid/Not Fixable"])
    pi.add_argument("--public-analysis")
    pi.add_argument("--internal-validity")
    pi.add_argument("--summary-file", help="Optional unfixable explanation text file")
    pi.set_defaults(func=cmd_package_invalid)

    ar = sub.add_parser("archive", help="Move work session to completed_tasks/")
    ar.add_argument("--task-name")
    ar.set_defaults(func=cmd_archive)

    sv = sub.add_parser("set-verdicts", help="Record verdicts chosen by the workflow (not auto-decided)")
    sv.add_argument("--task-name")
    sv.add_argument("--public-analysis", required=True)
    sv.add_argument("--internal-validity", required=True)
    sv.add_argument("--duplicate-analysis", required=True)
    sv.add_argument("--reason", help="Reason for Internal Validity selection")
    sv.set_defaults(func=cmd_set_verdicts)

    return p


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
