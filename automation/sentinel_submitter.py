#!/usr/bin/env python3
"""Sentinel Ultra branch-aware submitter automation — safety gates only.

Never decides task verdicts. Never modifies task logic automatically.
Operates on working_copy only for mutations. Preserves original ZIP.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
SCHEMA_VERSION = 4  # workflow_state.json (v4: dialect_notes; grade.py not required)
AUDIT_SCHEMA_VERSION = 2  # audit_report.json (v2: network_blocks_ok / network_blocks_issues)

# Shared deterministic helpers (Phase 2 lib extract)
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from lib.verdicts import norm_analysis, public_matches_duplicate  # noqa: E402
from lib.paths import ensure_workspace, safe_task_name, sha256_file  # noqa: E402
from lib.toml_util import parse_task_toml_simple  # noqa: E402
from lib.sync import check_instruction_sync  # noqa: E402
from lib.package import (  # noqa: E402
    EXCLUDE_FROM_CORRECTED_ZIP as LIB_EXCLUDE_FROM_CORRECTED_ZIP,
    EXCLUDE_TOP_LEVEL_ONLY as LIB_EXCLUDE_TOP_LEVEL_ONLY,
    package_flat_task_zip,
    should_exclude_member,
    verify_corrected_zip,
)
from lib.hygiene import (  # noqa: E402
    ensure_network_blocks_in_task_toml,
    extract_grade_py_from_test_sh,
    strip_compose_network_none,
    validate_network_blocks,
)

# Keep module-level names aligned with lib (tests/docs may reference them)
EXCLUDE_FROM_CORRECTED_ZIP = LIB_EXCLUDE_FROM_CORRECTED_ZIP
EXCLUDE_TOP_LEVEL_ONLY = LIB_EXCLUDE_TOP_LEVEL_ONLY

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

TASK_MARKERS = (
    "instruction.md",
    "task.toml",
    "environment",
    "solution",
    "tests",
)

REQUIRED_CURRENT = [
    "instruction.md",
    "task.toml",
    "environment/Dockerfile",
    "environment/repo",
    "environment/problem_statement.md",
    "solution/solve.sh",
    "solution/golden.patch",
    "tests/test.sh",
    "tests/tests.patch",
    "tests/config.json",
]

# Present on some Harbor dialects / packages; never blocking by themselves.
DIALECT_OPTIONAL = [
    "tests/grade.py",
    "tests/files",
    "docker_compose.yaml",
    "docker-compose.yaml",
    "environment/docker_compose.yaml",
    "environment/docker-compose.yaml",
]

FORBIDDEN_ARTIFACT_GLOBS = [
    "**/__pycache__/**",
    "**/*.pyc",
    "**/.DS_Store",
    "**/.pytest_cache/**",
    "**/.mypy_cache/**",
    "**/.ruff_cache/**",
    "**/.venv/**",
    "**/node_modules/**",
    "**/.idea/**",
    "**/.vscode/**",
    "**/*.swp",
    "**/*~",
    "**/*.orig",
    "**/*.bak",
    "**/metadata.json",
    "**/ground_truth.*",
]

LEAKAGE_NAME_HINTS = (
    "expected_output",
    "golden_solution",
    "answer_key",
    "reference_answer",
)

PUBLIC_VALUES = {"Fixable", "Invalid/Not Fixable", "Valid as-is"}
INTERNAL_VALUES = {"Invalid", "Fixable", "Valid-as-is"}
DUPLICATE_VALUES = {"Fixable", "Invalid/Not Fixable", "Valid-as-is"}
VALIDATION_STATUSES = {"passed", "failed", "not_run", "confirmed_by_logs"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def is_ignored_path(path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(WORKSPACE_ROOT.resolve())
    except ValueError:
        return False
    return bool(set(rel.parts) & IGNORE_DIR_NAMES)


def session_paths(task_name: str) -> Dict[str, Path]:
    work = WORKSPACE_ROOT / "work" / task_name
    outputs = WORKSPACE_ROOT / "task_outputs" / task_name
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
        "outputs": outputs,
        "workflow_state": outputs / "workflow_state.json",
        "updated_zip_dir": outputs / "updated_zip_file",
        "invalid_evidence_dir": outputs / "invalid_evidence",
        "audit_json": outputs / "audit_report.json",
        "audit_md": outputs / "audit_report.md",
        "preflight_json": outputs / "preflight_report.json",
        "git_report": outputs / "git_hygiene_report.json",
        "artifact_report": outputs / "artifact_scan_report.json",
        "config_report": outputs / "config_validation_report.json",
        "zip_manifest": outputs / "zip_manifest.json",
    }


def empty_workflow_state() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "task_name": "",
        "source_zip": "",
        "source_sha256": "",
        "task_root": "",
        "working_task_root": "",
        "mode": "submitter",
        "public_analysis": None,
        "internal_validity": None,
        "internal_validity_reason": None,
        "duplicate_analysis": None,
        "branch": None,
        "invalid_category": None,
        "invalid_environment_subissue": None,
        "unfixable_explanation": None,
        "audit_completed": False,
        "required_files_checked": False,
        "missing_required_files": [],
        "dialect_notes": [],
        "static_check_completed": False,
        "static_check_passed": False,
        "static_check_fixable_ids": [],
        "static_check_advisory_ids": [],
        "static_check_not_fixable_ids": [],
        "judge_prep_completed": False,
        "judge_prep_passed": False,
        "judge_prep_blockers": [],
        "judge_prep_accept_risk": False,
        "judge_prep_accept_risk_reason": None,
        "instruction_problem_statement_match": False,
        "test_config_checked": False,
        "fail_to_pass_count": None,
        "test_ids_checked": False,
        "test_id_status": "not_run",
        "tests_patch_applies": False,
        "git_hygiene_checked": False,
        "git_hygiene_ok": False,
        "docker_build_status": "not_run",
        "oracle_status": "not_run",
        "oracle_reward": None,
        "nop_status": "not_run",
        "nop_reward": None,
        "pass_to_pass_status": "not_run",
        "artifact_scan_passed": False,
        "packaging_preflight_passed": False,
        "ready_to_finalize": False,
        "ready_to_package": False,
        "validation_level": "not_validated",
        "blocking_issues": [],
        "warnings": [],
        "format": None,
        "runs_path": None,
        "selected_task_root_explicit": False,
        "validation_evidence": {},
        "created_at": "",
        "last_updated": "",
    }


def load_session(task_name: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    if task_name:
        path = session_paths(task_name)["session_json"]
        if not path.exists():
            die(f"No session for task: {task_name}")
        return task_name, json.loads(path.read_text(encoding="utf-8"))
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
        die("Multiple active sessions: " + ", ".join(n for n, _ in sessions) + ". Pass --task-name.")
    name, path = sessions[0]
    return name, json.loads(path.read_text(encoding="utf-8"))


def save_session(task_name: str, data: Dict[str, Any]) -> None:
    path = session_paths(task_name)["session_json"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_workflow_state(task_name: str) -> Dict[str, Any]:
    path = session_paths(task_name)["workflow_state"]
    if not path.exists():
        state = empty_workflow_state()
        state["task_name"] = task_name
        state["created_at"] = utc_now()
        state["last_updated"] = utc_now()
        return state
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        migrated = migrate_workflow_state(task_name, data)
        return migrated
    return data


def migrate_workflow_state(task_name: str, old: Dict[str, Any]) -> Dict[str, Any]:
    paths = session_paths(task_name)
    backup = paths["outputs"] / f"workflow_state.pre_migration_backup.{utc_now().replace(':', '')}.json"
    paths["outputs"].mkdir(parents=True, exist_ok=True)
    backup.write_text(json.dumps(old, indent=2) + "\n", encoding="utf-8")

    # Detect contradictory verdict fields in old session-style blobs
    conflicts = []
    pub = old.get("public_analysis")
    dup = old.get("duplicate_analysis")
    if pub and dup and not public_matches_duplicate(str(pub), str(dup)):
        conflicts.append(f"public_analysis={pub!r} vs duplicate_analysis={dup!r}")
    if conflicts:
        die(
            "State migration blocked due to conflicting values: "
            + "; ".join(conflicts)
            + f". Backup at {backup}. Resolve manually."
        )

    state = empty_workflow_state()
    for key in state.keys():
        if key in old and old[key] is not None:
            state[key] = old[key]
    state["schema_version"] = SCHEMA_VERSION
    state["task_name"] = task_name
    state["created_at"] = old.get("created_at") or utc_now()
    state["last_updated"] = utc_now()
    save_workflow_state(task_name, state)
    print(f"Migrated workflow state; backup: {backup}")
    return state


def save_workflow_state(task_name: str, state: Dict[str, Any]) -> None:
    paths = session_paths(task_name)
    paths["outputs"].mkdir(parents=True, exist_ok=True)
    state["schema_version"] = SCHEMA_VERSION
    state["task_name"] = task_name
    state["last_updated"] = utc_now()
    if not state.get("created_at"):
        state["created_at"] = utc_now()
    paths["workflow_state"].write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def copytree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def score_task_root(d: Path) -> int:
    return sum(1 for m in TASK_MARKERS if (d / m).exists())


def find_all_task_roots(extracted: Path) -> List[Path]:
    roots: List[Path] = []
    for dirpath, dirnames, _ in os.walk(extracted):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIR_NAMES and d != "runs"]
        p = Path(dirpath)
        if score_task_root(p) >= 4:
            roots.append(p)
    # Prefer shallower unique roots (drop children of selected parents)
    roots = sorted(set(roots), key=lambda p: (len(p.parts), str(p)))
    filtered: List[Path] = []
    for r in roots:
        if any(str(r).startswith(str(parent) + os.sep) for parent in filtered):
            continue
        filtered.append(r)
    return filtered


def resolve_task_root(extracted: Path, explicit: Optional[Path] = None) -> Path:
    if explicit:
        exp = explicit if explicit.is_absolute() else (extracted / explicit)
        exp = exp.resolve()
        if not exp.exists() or score_task_root(exp) < 3:
            die(f"Explicit task root is not credible: {exp}")
        return exp
    roots = find_all_task_roots(extracted)
    if not roots:
        die(f"Could not locate task root under {extracted}")
    if len(roots) > 1:
        print("ERROR: Multiple credible task roots found. Explicit selection required.", file=sys.stderr)
        for r in roots:
            print(f"  - {r}", file=sys.stderr)
        print("Use: python automation/sentinel_submitter.py select-task <relative-or-absolute-path>", file=sys.stderr)
        raise SystemExit(2)
    return roots[0]


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
        for p in ("solution/init_state.patch", "solution/solution.patch", "tests/files")
    )
    if current and legacy:
        return "hybrid"
    if current:
        return "current"
    if legacy:
        return "legacy"
    return "unknown"


def detect_runs(extracted: Path, task_root: Path) -> Optional[str]:
    for c in (extracted / "runs", task_root.parent / "runs"):
        if c.is_dir():
            return str(c.resolve())
    return None


def find_candidate_zips(explicit: Optional[str]) -> List[Path]:
    if explicit:
        if ".." in Path(explicit).parts:
            die(f"Rejected path traversal in ZIP argument: {explicit}")
        raw = Path(explicit).expanduser()
        if raw.is_absolute():
            p = raw.resolve()
        else:
            # Prefer cwd, then workspace-relative
            cand = (Path.cwd() / raw).resolve()
            if cand.exists():
                p = cand
            else:
                p = (WORKSPACE_ROOT / raw).resolve()
        if not p.exists() or not p.is_file():
            die(f"ZIP not found: {p}")
        if p.suffix.lower() != ".zip":
            die(f"Not a ZIP file: {p}")
        # Reject ignored locations even for explicit paths
        try:
            rel = p.relative_to(WORKSPACE_ROOT.resolve())
            if bool(set(rel.parts) & IGNORE_DIR_NAMES):
                die(f"ZIP is inside an ignored location: {p}")
        except ValueError:
            # Absolute path outside workspace is allowed only when explicitly supplied
            pass
        return [p]

    candidates: List[Path] = []
    for root in (WORKSPACE_ROOT / "incoming_tasks", WORKSPACE_ROOT):
        if not root.exists():
            continue
        for path in sorted(root.glob("*.zip")):
            if path.stem.lower() in {"sentinal", "sentinel"}:
                continue
            if is_ignored_path(path):
                continue
            if path.parent.resolve() != root.resolve() and root == WORKSPACE_ROOT:
                continue
            candidates.append(path.resolve())
    uniq: List[Path] = []
    seen = set()
    for c in candidates:
        if str(c) not in seen:
            seen.add(str(c))
            uniq.append(c)
    return uniq


def validate_config(task_root: Path) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "ok": False,
        "errors": [],
        "warnings": [],
        "fail_to_pass_count": None,
        "duplicate_ids": [],
        "test_id_status": "not_run",
        "note": "The test count passes structural validation but semantic coverage and faithfulness still require expert review."
        if False
        else "",
    }
    cfg_path = task_root / "tests" / "config.json"
    if not cfg_path.exists():
        report["errors"].append("tests/config.json missing")
        return report
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        report["errors"].append(f"invalid JSON: {e}")
        return report

    # Flexible schema: support nested or flat keys used in Harbor tasks
    execution = cfg.get("execution") or {}
    grading = cfg.get("grading") or {}
    commands = execution.get("commands") or cfg.get("commands")
    if not commands:
        report["errors"].append("execution.commands missing")
    timeout = execution.get("timeout") or execution.get("timeout_sec") or cfg.get("timeout")
    if timeout is None:
        report["warnings"].append("execution timeout missing")
    else:
        try:
            if int(timeout) <= 0 or int(timeout) > 1800:
                report["warnings"].append(f"execution timeout unusual: {timeout}")
        except Exception:
            report["warnings"].append(f"execution timeout not numeric: {timeout}")

    f2p = grading.get("fail_to_pass") or cfg.get("fail_to_pass") or []
    p2p = grading.get("pass_to_pass") or cfg.get("pass_to_pass")
    if not isinstance(f2p, list):
        report["errors"].append("grading.fail_to_pass must be a list")
        f2p = []
    report["fail_to_pass_count"] = len(f2p)
    if len(f2p) < 10:
        report["errors"].append(f"fail_to_pass count {len(f2p)} < 10")
    dupes = sorted({x for x in f2p if f2p.count(x) > 1})
    report["duplicate_ids"] = dupes
    if dupes:
        report["errors"].append(f"duplicate fail_to_pass IDs: {dupes}")

    if p2p is None:
        report["warnings"].append("grading.pass_to_pass absent")

    parser = cfg.get("parser") or grading.get("parser") or execution.get("parser")
    if parser is None:
        report["warnings"].append("parser configuration missing")

    artifacts = cfg.get("artifacts") or {}
    reward = (
        cfg.get("reward_path")
        or grading.get("reward_path")
        or execution.get("reward_path")
        or cfg.get("reward")
        or artifacts.get("reward")
        or artifacts.get("reward_path")
    )
    if reward is None:
        # common Harbor default
        report["warnings"].append("reward artifact path not declared (often /logs/verifier/reward.txt)")

    allow_extra = grading.get("allow_extra_failures")
    if allow_extra is True:
        report["warnings"].append(
            "grading.allow_extra_failures=true — only fail_to_pass/required_pass gate reward; "
            "ungraded tests in tests.patch can fail while reward stays 1.0 (expert coverage review required)"
        )

    # Best-effort static ID matching
    unresolved = []
    tests_dir = task_root / "tests"
    blob = ""
    if tests_dir.exists():
        for p in tests_dir.rglob("*"):
            if p.is_file() and p.suffix in {".py", ".txt", ".md", ".patch", ".sh", ".json"}:
                try:
                    blob += p.read_text(encoding="utf-8", errors="ignore") + "\n"
                except Exception:
                    pass
    for tid in f2p:
        token = str(tid)
        # parameterized hints
        if "[" in token or "]" in token or "::" in token:
            if token not in blob and token.split("::")[-1] not in blob:
                unresolved.append(token)
        else:
            if token not in blob:
                unresolved.append(token)
    if unresolved:
        report["test_id_status"] = "manual_review_required"
        report["warnings"].append(
            "Unresolved or parameterized IDs require manual review (not declared missing solely from text search): "
            + ", ".join(unresolved[:20])
        )
    else:
        report["test_id_status"] = "static_matched"

    # Tests defined in tests.patch but not listed in fail_to_pass (coverage gap signal)
    patch_tests = discover_tests_patch_defs(task_root)
    f2p_names = {str(x).split("::")[-1].split("[")[0] for x in f2p}
    ungraded = sorted(n for n in patch_tests if n not in f2p_names)
    report["tests_patch_def_count"] = len(patch_tests)
    report["ungraded_tests_in_patch"] = ungraded
    if ungraded:
        report["warnings"].append(
            "tests.patch defines tests not present in fail_to_pass (manual coverage review): "
            + ", ".join(ungraded[:25])
        )

    report["ok"] = len(report["errors"]) == 0
    report["note"] = (
        "The test count passes structural validation but semantic coverage and faithfulness still require expert review."
        if report["ok"]
        else "Structural config validation failed; semantic review still required after fixes."
    )
    return report


def discover_tests_patch_defs(task_root: Path) -> List[str]:
    """Return test function names added in tests/tests.patch (+def test_...)."""
    patch = task_root / "tests" / "tests.patch"
    if not patch.exists():
        return []
    names: List[str] = []
    try:
        for line in patch.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("+def test_"):
                name = line[len("+def ") :].split("(")[0].strip()
                if name.startswith("test_") and name not in names:
                    names.append(name)
    except Exception:
        return []
    return names


def analyze_tests_patch_health(task_root: Path) -> Dict[str, Any]:
    """
    Structural health of tests.patch (does not prove semantic quality).
    Flags corrupt hunks and git-vs-patch apply discrepancies that break renames.
    """
    patch = task_root / "tests" / "tests.patch"
    report: Dict[str, Any] = {
        "ok": False,
        "errors": [],
        "warnings": [],
        "hunk_mismatches": [],
        "empty_context_lines": 0,
        "git_apply_check": None,
        "patch_dry_run": None,
    }
    if not patch.exists():
        report["errors"].append("tests/tests.patch missing")
        return report
    text = patch.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    i = 0
    empty_ctx = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("@@"):
            m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if not m:
                report["errors"].append(f"unparseable hunk header at line {i + 1}")
                i += 1
                continue
            old_n = int(m.group(2) or 1)
            new_n = int(m.group(4) or 1)
            old_c = new_c = 0
            j = i + 1
            while j < len(lines) and not lines[j].startswith("diff ") and not lines[j].startswith("@@"):
                l = lines[j]
                if l == "":
                    empty_ctx += 1
                    # treat as broken empty context for counting purposes
                    old_c += 1
                    new_c += 1
                elif l.startswith("-"):
                    old_c += 1
                elif l.startswith("+"):
                    new_c += 1
                elif l.startswith("\\"):
                    pass
                else:
                    old_c += 1
                    new_c += 1
                j += 1
            if old_c != old_n or new_c != new_n:
                report["hunk_mismatches"].append(
                    {"line": i + 1, "header_old": old_n, "header_new": new_n, "actual_old": old_c, "actual_new": new_c}
                )
            i = j
            continue
        i += 1
    report["empty_context_lines"] = empty_ctx
    if empty_ctx:
        report["warnings"].append(
            f"{empty_ctx} completely empty hunk line(s) found — unified diffs require a leading space on blank context lines; "
            "git apply often fails while GNU patch may succeed and mishandle renames"
        )
    if report["hunk_mismatches"]:
        report["errors"].append(
            f"{len(report['hunk_mismatches'])} hunk line-count mismatch(es) — regenerate tests.patch before packaging"
        )

    applies, detail, meta = check_tests_patch_applies_detailed(task_root)
    report["git_apply_check"] = meta.get("git")
    report["patch_dry_run"] = meta.get("patch")
    report["applies"] = applies
    report["apply_detail"] = detail
    if meta.get("git") is False and meta.get("patch") is True:
        report["warnings"].append(
            "git apply --check FAILED but patch --dry-run PASSED — treat as Fixable packaging defect; "
            "GNU patch often skips git renames (e.g. test/ → test/subdir/)"
        )
    if report["hunk_mismatches"] or (meta.get("git") is False and meta.get("patch") is True):
        # still may "apply" via patch fallback at runtime, but not healthy
        report["ok"] = False if report["hunk_mismatches"] else True
    else:
        report["ok"] = applies and not report["errors"]
    if report["errors"] and applies:
        report["ok"] = False
    elif applies and not report["errors"]:
        report["ok"] = True
    return report


def check_tests_patch_applies_detailed(task_root: Path) -> Tuple[bool, str, Dict[str, Any]]:
    patch = task_root / "tests" / "tests.patch"
    repo = task_root / "environment" / "repo"
    meta: Dict[str, Any] = {"git": None, "patch": None}
    if not patch.exists():
        return False, "tests/tests.patch missing", meta
    if not repo.exists():
        return False, "environment/repo missing", meta
    try:
        r = subprocess.run(
            ["git", "apply", "--check", str(patch)],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=60,
        )
        meta["git"] = r.returncode == 0
        if r.returncode == 0:
            return True, "git apply --check passed", meta
        r2 = subprocess.run(
            ["patch", "-p1", "--dry-run", "-i", str(patch)],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=60,
        )
        meta["patch"] = r2.returncode == 0
        if r2.returncode == 0:
            return True, (
                "patch --dry-run passed BUT git apply --check failed — "
                "rename-safe packaging requires regenerating tests.patch for git apply"
            ), meta
        return False, (r.stderr or r.stdout or r2.stderr or r2.stdout or "patch check failed")[:500], meta
    except FileNotFoundError:
        return False, "git/patch tools unavailable for apply check", meta
    except Exception as e:
        return False, f"patch check error: {e}", meta


def check_tests_patch_applies(task_root: Path) -> Tuple[bool, str]:
    ok, msg, _meta = check_tests_patch_applies_detailed(task_root)
    return ok, msg


def git_hygiene_report(task_root: Path, base_commit: Optional[str] = None) -> Dict[str, Any]:
    repo = task_root / "environment" / "repo"
    report: Dict[str, Any] = {
        "ok": False,
        "errors": [],
        "warnings": [],
        "checks": {},
    }
    gitdir = repo / ".git"
    if not repo.exists():
        report["errors"].append("environment/repo missing")
        return report
    if not gitdir.exists():
        report["errors"].append(
            ".git is missing — HEAD/base_commit_sha cannot be verified (FIXABLE git hygiene)"
        )
        report["checks"]["git_present"] = False
        report["ok"] = False
        return report
    report["checks"]["git_present"] = True

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=60,
        )

    head = git("rev-parse", "HEAD")
    report["checks"]["head_resolves"] = head.returncode == 0
    if head.returncode != 0:
        report["errors"].append("HEAD does not resolve")
    else:
        head_sha = head.stdout.strip()
        report["checks"]["head"] = head_sha
        if base_commit and base_commit not in ("", "null") and not head_sha.startswith(base_commit) and base_commit != head_sha:
            report["errors"].append(f"HEAD {head_sha} does not match base_commit_sha {base_commit}")

    remotes = git("remote", "-v")
    if remotes.returncode == 0 and remotes.stdout.strip():
        report["errors"].append("git remotes present")
        report["checks"]["remotes"] = remotes.stdout.strip().splitlines()
    else:
        report["checks"]["remotes"] = []

    status = git("status", "--porcelain")
    if status.returncode == 0 and status.stdout.strip():
        report["errors"].append("dirty working tree")
        report["checks"]["dirty"] = status.stdout.strip().splitlines()[:50]
    else:
        report["checks"]["dirty"] = []

    # reflog
    reflog = repo / ".git" / "logs" / "HEAD"
    if reflog.exists() and reflog.stat().st_size > 0:
        report["errors"].append("reflog leakage present (.git/logs/HEAD)")
        report["checks"]["reflog"] = True
    else:
        report["checks"]["reflog"] = False

    # filter drivers
    cfg = git("config", "--local", "--list")
    if cfg.returncode == 0 and "filter." in cfg.stdout:
        report["errors"].append("local filter drivers present")
        report["checks"]["filter_drivers"] = True
    else:
        report["checks"]["filter_drivers"] = False

    # unexpected refs beyond HEAD
    refs = git("for-each-ref", "--format=%(refname)")
    if refs.returncode == 0:
        ref_list = [r for r in refs.stdout.splitlines() if r.strip()]
        unexpected = [r for r in ref_list if r not in {"refs/heads/master", "refs/heads/main"} and not r.startswith("refs/heads/")]
        # allow a single local branch
        extras = [r for r in ref_list if r.startswith("refs/remotes/") or r.startswith("refs/original/") or "stash" in r]
        if extras:
            report["errors"].append(f"unexpected refs: {extras}")
        report["checks"]["refs"] = ref_list

    # size
    total = 0
    for p in gitdir.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    report["checks"]["git_size_bytes"] = total
    if total >= 100 * 1024 * 1024:
        report["errors"].append(f".git size {total} >= 100MB")

    applies, msg = check_tests_patch_applies(task_root)
    report["checks"]["tests_patch_applies"] = applies
    report["checks"]["tests_patch_message"] = msg
    if not applies:
        report["errors"].append(f"tests.patch apply check failed: {msg}")

    report["ok"] = len(report["errors"]) == 0
    return report


def artifact_scan(task_root: Path) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    forbidden_hit = False
    for dirpath, dirnames, filenames in os.walk(task_root):
        rel_dir = Path(dirpath).relative_to(task_root).as_posix()
        for d in list(dirnames):
            name = d
            path = f"{rel_dir}/{name}" if rel_dir != "." else name
            if name in {
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                ".venv",
                "node_modules",
                ".idea",
                ".vscode",
            }:
                findings.append({"path": path, "class": "forbidden"})
                forbidden_hit = True
        for fn in filenames:
            path = f"{rel_dir}/{fn}" if rel_dir != "." else fn
            lower = fn.lower()
            if (
                fn.endswith((".pyc", ".swp", ".orig", ".bak"))
                or fn.endswith("~")
                or fn in {".DS_Store", "metadata.json"}
                or lower.startswith("ground_truth")
            ):
                findings.append({"path": path, "class": "forbidden"})
                forbidden_hit = True
            elif any(h in lower for h in LEAKAGE_NAME_HINTS):
                findings.append({"path": path, "class": "manual_semantic_review_required"})
            elif path.endswith("solution/solution.patch") or path.endswith("solution/init_state.patch"):
                findings.append({"path": path, "class": "legacy_needs_review"})
    return {
        "passed": not forbidden_hit,
        "forbidden_found": forbidden_hit,
        "findings": findings,
    }


def metadata_limits_report(task_root: Path) -> Dict[str, Any]:
    toml = parse_task_toml_simple(task_root / "task.toml")
    errors: List[str] = []
    warnings: List[str] = []

    def as_int(key: str) -> Optional[int]:
        v = toml.get(key)
        if v is None:
            return None
        try:
            return int(float(str(v)))
        except Exception:
            return None

    cpus = as_int("cpus") or as_int("resources.cpus")
    if cpus not in (2, 4, None):
        errors.append(f"cpus must be 2 or 4 (got {cpus})")
    elif cpus is None:
        warnings.append("cpus not found in task.toml")

    mem = as_int("memory_mb") or as_int("resources.memory_mb")
    if mem is not None and not (2048 <= mem <= 16384):
        errors.append(f"memory_mb out of range: {mem}")
    storage = as_int("storage_mb") or as_int("resources.storage_mb")
    if storage is not None and not (5120 <= storage <= 10240):
        errors.append(f"storage_mb out of range: {storage}")
    gpus = as_int("gpus") or as_int("resources.gpus")
    if gpus not in (0, None):
        errors.append(f"gpus must be 0 (got {gpus})")

    timeout_specs = (
        ("build_timeout_sec", 1800, ("environment.build_timeout_sec", "build_timeout_sec")),
        ("agent_timeout_sec", 7200, ("agent.timeout_sec", "agent_timeout_sec")),
        ("verifier_timeout_sec", 1800, ("verifier.timeout_sec", "verifier_timeout_sec")),
    )
    for key, limit, aliases in timeout_specs:
        val = None
        for alias in aliases:
            val = as_int(alias)
            if val is not None:
                break
        if val is None:
            val = as_int(f"timeouts.{key}") or as_int(key.replace("_sec", ""))
        if val is not None and val > limit:
            errors.append(f"{key} {val} exceeds {limit}")

    net_ok, net_problems = validate_network_blocks(task_root)
    if not net_ok:
        for msg in net_problems:
            warnings.append(f"network block missing/wrong: {msg}")

    dockerfile = task_root / "environment" / "Dockerfile"
    if dockerfile.exists():
        text = dockerfile.read_text(encoding="utf-8", errors="replace")
        if re.search(r"FROM\s+\S+:latest\b", text, re.I):
            errors.append("Dockerfile uses :latest tag")
    else:
        errors.append("Dockerfile missing")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "network_blocks_ok": net_ok,
        "network_blocks_issues": list(net_problems),
        "base_commit_sha": toml.get("base_commit_sha") or toml.get("metadata.base_commit_sha"),
    }


def normalize_audit_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize metadata embedded in audit reports across schema eras.

    Old audits (pre AUDIT_SCHEMA_VERSION 2) may carry network_mode_present /
    allowed_hosts_present with present=bad semantics. Map those to the current
    network_blocks_ok / network_blocks_issues fields without rewriting files.
    """
    out = dict(meta or {})
    if "network_blocks_ok" in out and "network_blocks_issues" in out:
        return out
    # Legacy present=bad keys → invert for consumers
    if "network_mode_present" in out or "allowed_hosts_present" in out:
        issues: List[str] = []
        # Old reports treated presence as noteworthy; under current policy presence
        # of the fields is required — legacy flags alone cannot prove correctness.
        if out.get("network_mode_present") is False and out.get("allowed_hosts_present") is False:
            issues.append(
                "legacy audit: network_mode/allowed_hosts were absent "
                "(current policy requires Harbor three-block values)"
            )
        elif out.get("network_mode_present") or out.get("allowed_hosts_present"):
            issues.append(
                "legacy audit: network fields were present but values were not validated "
                "(re-run audit for network_blocks_ok)"
            )
        out.setdefault("network_blocks_ok", len(issues) == 0)
        out.setdefault("network_blocks_issues", issues)
    else:
        out.setdefault("network_blocks_ok", None)
        out.setdefault("network_blocks_issues", ["network block status unknown (pre-v2 audit)"])
    return out


def required_files_report(task_root: Path) -> Dict[str, Any]:
    missing = []
    legacy = []
    dialect_notes: List[str] = []
    for rel in REQUIRED_CURRENT:
        p = task_root / rel
        if not p.exists():
            # golden.patch may be represented by solution.patch (legacy)
            if rel == "solution/golden.patch" and (task_root / "solution/solution.patch").exists():
                legacy.append("solution/solution.patch present instead of golden.patch")
                continue
            if rel == "tests/tests.patch" and (task_root / "tests/test.patch").exists():
                legacy.append("tests/test.patch present instead of tests.patch")
                continue
            missing.append(rel)
    for rel in ("solution/solution.patch", "solution/init_state.patch", "tests/files"):
        if (task_root / rel).exists():
            legacy.append(rel)
    # Dialect optional: informational only — never blocking
    grade = task_root / "tests" / "grade.py"
    test_sh = task_root / "tests" / "test.sh"
    if not grade.exists() or grade.stat().st_size == 0:
        if test_sh.exists():
            ts = test_sh.read_text(encoding="utf-8", errors="replace")
            if "GRADE_PY_EOF" in ts or "/tmp/grade.py" in ts:
                dialect_notes.append(
                    "tests/grade.py absent while test.sh embeds a grader "
                    "(dialect optional — extract via ensure-packaging-hygiene if desired; not blocking)"
                )
    return {
        "missing": missing,
        "legacy": legacy,
        "ok": len(missing) == 0,
        "dialect_notes": dialect_notes,
    }


# ----------------------------- commands ---------------------------------


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
    if paths["outputs"].exists() and args.force:
        # preserve nothing misleading
        shutil.rmtree(paths["outputs"])

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
    with zipfile.ZipFile(preserved, "r") as zf:
        zf.extractall(paths["extracted_original"])
    copytree(paths["extracted_original"], paths["working_copy"])

    # Multiple roots: stop without selecting
    roots = find_all_task_roots(paths["extracted_original"])
    selected_root = None
    working_root = None
    multi = False
    if len(roots) == 1:
        selected_root = roots[0]
        working_root = find_all_task_roots(paths["working_copy"])[0]
    elif len(roots) == 0:
        die("No credible task root found after extract")
    else:
        multi = True
        print("INTAKE PARTIAL: multiple task roots — explicit select-task required")
        for r in roots:
            print(f"  - {r}")

    fmt = detect_format(selected_root) if selected_root else "unknown"
    runs_path = detect_runs(paths["extracted_original"], selected_root) if selected_root else None

    if args.platform_input:
        pip = Path(args.platform_input)
        if pip.exists():
            shutil.copy2(pip, paths["platform_input"])
        else:
            paths["platform_input"].write_text(str(args.platform_input), encoding="utf-8")
    else:
        paths["platform_input"].write_text("", encoding="utf-8")

    session = {
        "task_name": task_name,
        "original_zip_name": src_zip.name,
        "sha256": digest,
        "original_path": str(preserved.resolve()),
        "source_zip_path": str(src_zip.resolve()),
        "extracted_original_path": str(paths["extracted_original"].resolve()),
        "working_copy_path": str(paths["working_copy"].resolve()),
        "real_task_root": str(selected_root.resolve()) if selected_root else None,
        "working_task_root": str(working_root.resolve()) if working_root else None,
        "runs_path": runs_path,
        "format": fmt,
        "start_timestamp": utc_now(),
        "current_workflow_phase": "intake_partial_multi_root" if multi else "intake_complete",
        "public_analysis": None,
        "internal_validity": None,
        "internal_validity_reason": None,
        "duplicate_analysis": None,
        "branch": None,
        "timestamps": {"intake": utc_now()},
        "notes": "Automation manages files/gates only. Verdicts are set by submitter workflow.",
    }
    save_session(task_name, session)

    state = empty_workflow_state()
    state.update(
        {
            "task_name": task_name,
            "source_zip": str(preserved.resolve()),
            "source_sha256": digest,
            "task_root": session["real_task_root"],
            "working_task_root": session["working_task_root"],
            "format": fmt,
            "runs_path": runs_path,
            "created_at": utc_now(),
        }
    )
    if multi:
        state["blocking_issues"] = ["Multiple credible task roots — run select-task"]
        state["selected_task_root_explicit"] = False
    save_workflow_state(task_name, state)

    print("INTAKE COMPLETE" if not multi else "INTAKE NEEDS select-task")
    print(f"  task_name: {task_name}")
    print(f"  original_zip: {preserved}")
    print(f"  sha256: {digest}")
    print(f"  extracted_original: {paths['extracted_original']}")
    print(f"  working_copy: {paths['working_copy']}")
    print(f"  task_root: {session['real_task_root']}")
    print(f"  format: {fmt}")
    if multi:
        raise SystemExit(2)


def cmd_select_task(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    paths = session_paths(task_name)
    target = Path(args.path)
    # Interpret path relative to extracted_original if not absolute under it
    extracted = Path(session["extracted_original_path"])
    if not target.is_absolute():
        candidate = (extracted / target).resolve()
    else:
        candidate = target.resolve()
        try:
            candidate.relative_to(extracted.resolve())
        except ValueError:
            die("select-task path must be inside extracted_original")
    root = resolve_task_root(extracted, explicit=candidate)
    # Map to working copy equivalent
    rel = root.relative_to(extracted)
    working_root = (Path(session["working_copy_path"]) / rel).resolve()
    if score_task_root(working_root) < 3:
        die(f"Working copy root not credible: {working_root}")
    session["real_task_root"] = str(root)
    session["working_task_root"] = str(working_root)
    session["format"] = detect_format(root)
    session["runs_path"] = detect_runs(extracted, root)
    session["current_workflow_phase"] = "task_root_selected"
    save_session(task_name, session)
    state = load_workflow_state(task_name)
    state["task_root"] = session["real_task_root"]
    state["working_task_root"] = session["working_task_root"]
    state["format"] = session["format"]
    state["runs_path"] = session["runs_path"]
    state["selected_task_root_explicit"] = True
    state["blocking_issues"] = [b for b in state.get("blocking_issues", []) if "Multiple credible" not in b]
    save_workflow_state(task_name, state)
    print("TASK ROOT SELECTED")
    print(f"  task_root: {root}")
    print(f"  working_task_root: {working_root}")


def cmd_prepare(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    paths = session_paths(task_name)
    if not session.get("real_task_root"):
        die("No task root selected. Run select-task if multiple roots exist.")
    state = load_workflow_state(task_name)
    state["task_root"] = session["real_task_root"]
    state["working_task_root"] = session["working_task_root"]
    state["format"] = session.get("format")
    state["source_zip"] = session.get("original_path")
    state["source_sha256"] = session.get("sha256")
    # Non-destructive discovery reports
    root = Path(session["real_task_root"])
    req = required_files_report(root)
    (paths["analysis"] / "prepare_discovery.json").write_text(
        json.dumps({"required": req, "format": state["format"]}, indent=2) + "\n",
        encoding="utf-8",
    )
    (paths["outputs"] / "prepare_summary.md").write_text(
        f"# Prepare summary\n\nTask: {task_name}\nFormat: {state['format']}\n"
        f"Missing required: {req['missing']}\nLegacy: {req['legacy']}\n\n"
        "Prepare does not decide verdicts, modify logic, repair git, package, or mark validation passed.\n",
        encoding="utf-8",
    )
    session["current_workflow_phase"] = "prepared"
    save_session(task_name, session)
    save_workflow_state(task_name, state)
    print("PREPARE COMPLETE (no verdict, no packaging, no validation claims)")
    print(f"  missing_required: {req['missing']}")
    print(f"  legacy: {req['legacy']}")


def cmd_audit(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    if not session.get("real_task_root"):
        die("No task root selected.")
    # Audit ORIGINAL only
    root = Path(session["real_task_root"])
    paths = session_paths(task_name)
    req = required_files_report(root)
    sync_ok, sync_msg = check_instruction_sync(root)
    cfg = validate_config(root)
    meta = metadata_limits_report(root)
    gitrep = git_hygiene_report(root, base_commit=meta.get("base_commit_sha"))
    arts = artifact_scan(root)
    applies, applies_msg = check_tests_patch_applies(root)
    patch_health = analyze_tests_patch_health(root)

    report = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "task_name": task_name,
        "audited_root": str(root),
        "audited_copy": "extracted_original",
        "timestamp": utc_now(),
        "required_files": req,
        "instruction_sync": {"ok": sync_ok, "detail": sync_msg},
        "config": cfg,
        "metadata": meta,
        "network_blocks_ok": meta.get("network_blocks_ok"),
        "network_blocks_issues": meta.get("network_blocks_issues") or [],
        "git": gitrep,
        "artifacts": arts,
        "tests_patch": {"applies": applies, "detail": applies_msg, "health": patch_health},
        "runs_path": session.get("runs_path"),
        "format": session.get("format"),
        "maps_required_for_cursor": [
            "instruction-to-test coverage",
            "test-to-instruction faithfulness",
            "fail-to-pass count",
            "original-failure regression",
            "pass-to-pass protection",
            "oracle-to-instruction",
            "source PR scope",
            "environment findings",
            "git findings",
            "packaging findings",
            "metadata mismatches",
            "validation plan",
            "ungraded tests in tests.patch vs fail_to_pass",
            "tests.patch git-apply vs patch(1) rename safety",
        ],
        "verdict_assigned": False,
        "evidence_classes": ["Inspected", "Inferred", "Executed", "Confirmed by supplied logs", "Not verified"],
        "note": "Audit does not assign the final task verdict.",
    }
    paths["audit_json"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    ungraded = cfg.get("ungraded_tests_in_patch") or []
    net_ok = meta.get("network_blocks_ok")
    net_issues = meta.get("network_blocks_issues") or []
    paths["audit_md"].write_text(
        "# Submitter Audit (original task)\n\n"
        f"- Root: `{root}`\n"
        f"- Audit schema: {AUDIT_SCHEMA_VERSION}\n"
        f"- Missing required: {req['missing']}\n"
        f"- Legacy: {req['legacy']}\n"
        f"- Instruction sync: {sync_ok} ({sync_msg})\n"
        f"- f2p count (structural): {cfg.get('fail_to_pass_count')}\n"
        f"- Ungraded tests in tests.patch: {ungraded[:20]}\n"
        f"- Config ok: {cfg.get('ok')}\n"
        f"- Network blocks ok: {net_ok}\n"
        f"- Network blocks issues: {net_issues}\n"
        f"- Git ok: {gitrep.get('ok')}\n"
        f"- Artifact scan passed: {arts.get('passed')}\n"
        f"- tests.patch applies: {applies} ({applies_msg})\n"
        f"- tests.patch health ok: {patch_health.get('ok')}\n"
        f"- tests.patch health warnings: {patch_health.get('warnings')}\n\n"
        "Semantic maps must be completed by Cursor/expert. Audit assigns no verdict.\n",
        encoding="utf-8",
    )
    paths["git_report"].write_text(json.dumps(gitrep, indent=2) + "\n", encoding="utf-8")
    paths["artifact_report"].write_text(json.dumps(arts, indent=2) + "\n", encoding="utf-8")
    paths["config_report"].write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    state = load_workflow_state(task_name)
    state["audit_completed"] = True
    state["required_files_checked"] = True
    state["missing_required_files"] = req["missing"]
    state["dialect_notes"] = req.get("dialect_notes") or []
    state["instruction_problem_statement_match"] = sync_ok
    state["test_config_checked"] = True
    state["fail_to_pass_count"] = cfg.get("fail_to_pass_count")
    state["test_ids_checked"] = cfg.get("test_id_status") in {"static_matched", "manual_review_required"}
    state["test_id_status"] = cfg.get("test_id_status")
    state["tests_patch_applies"] = applies
    state["git_hygiene_checked"] = True
    state["git_hygiene_ok"] = bool(gitrep.get("ok"))
    state["artifact_scan_passed"] = bool(arts.get("passed"))
    # Do not mark validations passed from audit alone
    save_workflow_state(task_name, state)
    session["current_workflow_phase"] = "audited"
    save_session(task_name, session)
    print("AUDIT COMPLETE (no verdict assigned)")
    print(f"  report: {paths['audit_json']}")
    print(f"  f2p_count: {cfg.get('fail_to_pass_count')}")
    print(f"  sync: {sync_ok}")
    if cfg.get("ungraded_tests_in_patch"):
        print(f"  ungraded_in_tests_patch: {len(cfg.get('ungraded_tests_in_patch') or [])} (see audit report)")
    if patch_health.get("warnings") or patch_health.get("errors"):
        print(f"  tests_patch_health: ok={patch_health.get('ok')} warnings={len(patch_health.get('warnings') or [])}")
    print(cfg.get("note") or "")


ULTRA_REVIEW_SCRIPTS = (
    WORKSPACE_ROOT / ".cursor" / "skills" / "sentinel-ultra-review" / "scripts"
)
CHECK_TASK_PY = ULTRA_REVIEW_SCRIPTS / "check_task.py"


def resolve_static_check_root(session: Dict[str, Any], state: Dict[str, Any]) -> Path:
    """working_copy for Fixable; frozen original root for Valid as-is / otherwise."""
    branch = state.get("duplicate_analysis") or session.get("duplicate_analysis") or session.get("branch")
    if branch == "Fixable":
        root = Path(session.get("working_task_root") or "")
    else:
        root = Path(session.get("real_task_root") or session.get("working_task_root") or "")
    if not root.exists():
        die(f"static-check task root missing: {root}")
    return root


def run_static_check(task_root: Path, json_out: Path, md_out: Path) -> Dict[str, Any]:
    """Run check_task.py; preserve analyze_tests_patch_health as a combined-gate add-on."""
    if not CHECK_TASK_PY.is_file():
        die(f"check_task.py not found at {CHECK_TASK_PY}")
    json_out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(CHECK_TASK_PY),
        str(task_root),
        "--json",
        str(json_out),
        "--md",
        str(md_out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    data: Dict[str, Any] = {}
    if json_out.exists():
        try:
            data = json.loads(json_out.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            die(f"static-check wrote unreadable JSON: {e}")
    findings = data.get("findings") or []
    # Combined gate: preserve main's patch-health analyzer (check_task lacks it)
    patch_health = analyze_tests_patch_health(task_root)
    data["tests_patch_health"] = patch_health
    if patch_health.get("hunk_mismatches") or (
        patch_health.get("git_apply_check") is False and patch_health.get("patch_dry_run") is True
    ):
        findings.append(
            {
                "id": "PH1",
                "severity": "FIXABLE",
                "category": "Tests",
                "where": "tests/tests.patch",
                "summary": "tests.patch health failure (hunk mismatch and/or git-apply vs patch-only)",
                "evidence": patch_health.get("apply_detail") or str(patch_health.get("hunk_mismatches")),
                "rule": "Main pipeline analyze_tests_patch_health (preserved in merge)",
                "fix": "Regenerate tests.patch so git apply --check passes",
            }
        )
        data["findings"] = findings
        json_out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    fixable_ids = sorted({f["id"] for f in findings if f.get("severity") == "FIXABLE"})
    advisory_ids = sorted({f["id"] for f in findings if f.get("severity") == "ADVISORY"})
    not_fixable_ids = sorted({f["id"] for f in findings if f.get("severity") == "NOT_FIXABLE"})
    passed = len(fixable_ids) == 0 and len(not_fixable_ids) == 0
    return {
        "ok": passed,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "findings": findings,
        "fixable_ids": fixable_ids,
        "advisory_ids": advisory_ids,
        "not_fixable_ids": not_fixable_ids,
        "verdict_hint": data.get("verdict_hint"),
        "json_path": str(json_out),
        "md_path": str(md_out),
        "tests_patch_health": patch_health,
    }


def cmd_static_check(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    state = load_workflow_state(task_name)
    root = resolve_static_check_root(session, state)
    paths = session_paths(task_name)
    json_out = paths["outputs"] / "static_check_report.json"
    md_out = paths["outputs"] / "static_check_report.md"
    result = run_static_check(root, json_out, md_out)
    state["static_check_completed"] = True
    state["static_check_passed"] = bool(result["ok"])
    state["static_check_fixable_ids"] = result["fixable_ids"]
    state["static_check_advisory_ids"] = result["advisory_ids"]
    state["static_check_not_fixable_ids"] = result["not_fixable_ids"]
    req = required_files_report(root)
    state["dialect_notes"] = req.get("dialect_notes") or []
    save_workflow_state(task_name, state)
    print("STATIC CHECK COMPLETE")
    print(f"  root: {root}")
    print(f"  passed: {result['ok']}")
    print(f"  FIXABLE ids: {result['fixable_ids']}")
    print(f"  ADVISORY ids: {result['advisory_ids']}")
    print(f"  NOT_FIXABLE ids: {result['not_fixable_ids']}")
    print(f"  report: {json_out}")
    if result.get("stdout"):
        print(result["stdout"][-4000:])
    if not result["ok"]:
        raise SystemExit(1)


def cmd_set_verdicts(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    pub, internal, dup = args.public_analysis, args.internal_validity, args.duplicate_analysis
    if pub not in PUBLIC_VALUES:
        die(f"Invalid public_analysis: {pub}")
    if internal not in INTERNAL_VALUES:
        die(f"Invalid internal_validity: {internal}")
    if dup not in DUPLICATE_VALUES:
        die(f"Invalid duplicate_analysis: {dup}")
    if not public_matches_duplicate(pub, dup):
        die(f"Public Main Analysis must match Duplicate Analysis (got {pub!r} vs {dup!r})")
    if not args.reason or not str(args.reason).strip():
        die("Internal Validity requires --reason (evidence-based)")
    session["public_analysis"] = pub
    session["internal_validity"] = internal
    session["internal_validity_reason"] = args.reason
    session["duplicate_analysis"] = dup
    session["branch"] = dup
    session["current_workflow_phase"] = "verdicts_recorded"
    if args.invalid_category:
        session["invalid_category"] = args.invalid_category
    if args.environment_subissue:
        session["invalid_environment_subissue"] = args.environment_subissue
    if args.unfixable_explanation:
        session["unfixable_explanation"] = args.unfixable_explanation
    save_session(task_name, session)

    state = load_workflow_state(task_name)
    state["public_analysis"] = pub
    state["internal_validity"] = internal
    state["internal_validity_reason"] = args.reason
    state["duplicate_analysis"] = dup
    state["branch"] = dup
    # Do NOT infer validation from verdicts
    if args.invalid_category:
        state["invalid_category"] = args.invalid_category
    if args.environment_subissue:
        state["invalid_environment_subissue"] = args.environment_subissue
    if args.unfixable_explanation:
        state["unfixable_explanation"] = args.unfixable_explanation
    save_workflow_state(task_name, state)
    print("VERDICTS RECORDED")
    print(f"  public: {pub}")
    print(f"  internal: {internal}")
    print(f"  reason: {args.reason}")
    print(f"  duplicate: {dup}")
    print(f"  branch: {dup}")


def cmd_sync_problem_statement(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    state = load_workflow_state(task_name)
    if state.get("duplicate_analysis") != "Fixable" and session.get("duplicate_analysis") != "Fixable":
        die("sync-problem-statement allowed only when Duplicate Analysis is Fixable")
    working = Path(session["working_task_root"])
    src = working / "instruction.md"
    dst = working / "environment" / "problem_statement.md"
    if not src.exists():
        die(f"Missing {src}")
    if not dst.parent.exists():
        die(f"Missing environment directory under working copy")
    # Never touch extracted_original
    if str(working).startswith(str(session["extracted_original_path"])):
        die("Refusing to modify extracted_original")
    dst.write_bytes(src.read_bytes())
    ok = src.read_bytes() == dst.read_bytes()
    if not ok:
        die("Sync failed byte-equality recheck")
    state["instruction_problem_statement_match"] = True
    save_workflow_state(task_name, state)
    log = session_paths(task_name)["analysis"] / "sync_problem_statement.log"
    log.write_text(f"{utc_now()} synced instruction.md -> problem_statement.md\n", encoding="utf-8")
    print("SYNC COMPLETE (working_copy only)")
    print(f"  match: {ok}")


def cmd_ensure_packaging_hygiene(args: argparse.Namespace) -> None:
    """
    Safe Fixable packaging hygiene on working_copy only.
    Does not decide verdicts and does not edit instruction/tests/oracle logic.
    """
    task_name, session = load_session(args.task_name)
    state = load_workflow_state(task_name)
    branch = state.get("duplicate_analysis") or session.get("duplicate_analysis")
    if branch != "Fixable":
        die(f"ensure-packaging-hygiene only allowed when Duplicate Analysis is Fixable (got {branch})")
    working = Path(session.get("working_task_root") or "")
    if not working.exists():
        die("working_copy missing — run prepare first")
    extracted = Path(session.get("extracted_original_path") or session.get("extracted_path") or "")
    if extracted.exists() and working.resolve() == extracted.resolve():
        die("refusing to mutate extracted_original")
    if str(working).startswith(str(extracted)) and working.resolve() == extracted.resolve():
        die("refusing to mutate extracted_original")

    actions: List[str] = []
    wrote, msg = extract_grade_py_from_test_sh(working)
    actions.append(f"grade.py: {msg}")
    net_changed, nmsg = ensure_network_blocks_in_task_toml(working)
    actions.append(f"network blocks: {nmsg}")
    compose_changed, cmsg = strip_compose_network_none(working)
    actions.append(f"compose network: {cmsg}")

    solve = working / "solution" / "solve.sh"
    if solve.exists():
        mode = solve.stat().st_mode
        if not (mode & 0o111):
            solve.chmod(mode | 0o755)
            actions.append("solve.sh: set executable bit")
        else:
            actions.append("solve.sh: already executable")
    else:
        actions.append("solve.sh: missing")

    sol_legacy = working / "solution" / "solution.patch"
    golden = working / "solution" / "golden.patch"
    if sol_legacy.exists() and not golden.exists():
        sol_legacy.rename(golden)
        actions.append("renamed solution.patch → golden.patch")

    print("PACKAGING HYGIENE COMPLETE (working_copy only; no verdict)")
    for a in actions:
        print(f"  - {a}")
    print("Re-run preflight after expert semantic edits.")


def cmd_record_validation(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    state = load_workflow_state(task_name)
    check = args.check
    status = args.status
    if status not in VALIDATION_STATUSES:
        die(f"Invalid status: {status}")
    if status == "passed" and not args.evidence and not args.confirmed_by_logs:
        # require evidence path or explicit log confirmation flag mapped to confirmed_by_logs
        die("Refusing to mark passed without --evidence path (or use status confirmed_by_logs)")
    if status == "passed" and args.evidence:
        ev = Path(args.evidence)
        if not ev.exists():
            die(f"Evidence file not found: {ev}")

    reward = args.reward
    if reward is not None:
        try:
            reward = float(reward)
        except Exception:
            die("reward must be numeric")

    evidence_entry = {
        "check": check,
        "status": status,
        "command": args.command,
        "timestamp": utc_now(),
        "exit_code": args.exit_code,
        "evidence": args.evidence,
        "summary": args.summary,
        "reward": reward,
    }
    state.setdefault("validation_evidence", {})[check] = evidence_entry

    mapping = {
        "docker_build": ("docker_build_status", None),
        "oracle": ("oracle_status", "oracle_reward"),
        "nop": ("nop_status", "nop_reward"),
        "pass_to_pass": ("pass_to_pass_status", None),
        "tests_patch": (None, None),
        "git": (None, None),
        "packaging": (None, None),
    }
    if check not in mapping:
        die(f"Unknown check: {check}")
    status_key, reward_key = mapping[check]
    if status_key:
        state[status_key] = status
    if reward_key and reward is not None:
        state[reward_key] = reward
    if check == "tests_patch":
        state["tests_patch_applies"] = status in {"passed", "confirmed_by_logs"}
    if check == "git":
        state["git_hygiene_checked"] = True
        state["git_hygiene_ok"] = status in {"passed", "confirmed_by_logs"}

    save_workflow_state(task_name, state)
    print("VALIDATION RECORDED")
    print(json.dumps(evidence_entry, indent=2))


def run_judge_prep_for_task(task_name: str, task_root: Path, state: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke automation/judge_prep.py against task_root; update workflow state fields."""
    from judge_prep import run_judge_prep  # local import — keep submitter load light

    paths = session_paths(task_name)
    sc_json = paths["outputs"] / "static_check_report.json"
    accept = state.get("judge_prep_accept_risk_reason") if state.get("judge_prep_accept_risk") else None
    report = run_judge_prep(
        task_root,
        paths["outputs"],
        sc_json,
        task_name=task_name,
        accept_risk=accept,
    )
    state["judge_prep_completed"] = True
    state["judge_prep_passed"] = bool(report.get("prep_passed"))
    state["judge_prep_blockers"] = list(report.get("blockers") or [])
    return report


# Static-check ids that --accept-risk may demote (documented EC rationale required).
# V6: PR test migrations that necessarily delete obsolete assertions in pre-existing
# Jest suites while rewriting them for the new API. Relocating into brand-new files
# would rewrite the PR's test structure beyond natural scope. Other FIXABLE ids stay hard.
ACCEPT_RISK_STATIC_FIXABLE_IDS = frozenset({"V6"})


def apply_judge_prep_preflight_blockers(
    report: Dict[str, Any],
    blockers: List[str],
    warnings: List[str],
    accept_risk_reason: Optional[str],
) -> None:
    """Block on auto-REMOVE / UNDECIDED allow_extra / packaging / hard-stop / invalidated.

    Lexical coverage:/overreach: candidates from prep are NOT blockers (FIX B) — rehearsal
    confirms them. --accept-risk demotes remaining prep blockers to warnings.
    Also demotes judge_prep static_fixable:V6 when accept-risk is set (see ACCEPT_RISK_STATIC_FIXABLE_IDS).
    """
    if report.get("hard_stopped"):
        msg = "judge_prep HARD STOP: " + "; ".join(report.get("hard_stop_reasons") or ["unknown"])
        if accept_risk_reason:
            warnings.append(f"{msg} (accept-risk: {accept_risk_reason})")
        else:
            blockers.append(msg)
        return

    interesting = []
    for b in report.get("blockers") or []:
        if b.startswith("coverage:") or b.startswith("overreach:"):
            warnings.append(f"judge_prep lexical candidate (rehearsal owns confirmation): {b}")
            continue
        if (
            b.startswith("allow_extra:")
            or b.startswith("auto_remove:")
            or b.startswith("packaging:")
            or b.startswith("hard_stop:")
            or b == "decisions:invalidated"
            or (
                b.startswith("static_fixable:")
                and b.split(":", 1)[-1] in ACCEPT_RISK_STATIC_FIXABLE_IDS
            )
        ):
            interesting.append(b)
    for b in interesting:
        label = f"judge_prep: {b}"
        if accept_risk_reason:
            warnings.append(f"{label} (accept-risk: {accept_risk_reason})")
        else:
            blockers.append(label)


def apply_judge_rehearsal_preflight_blockers(
    outputs_dir: Path,
    blockers: List[str],
    warnings: List[str],
    accept_risk_reason: Optional[str],
) -> None:
    """Require fresh judge_rehearsal.json; block on CONFIRMED_* / UNDECIDED / stale fingerprint."""
    import judge_prep as jp  # type: ignore

    prep_path = outputs_dir / "judge_prep.json"
    reh_path = outputs_dir / "judge_rehearsal.json"
    if not prep_path.is_file():
        msg = "judge_rehearsal: missing judge_prep.json (run judge-prep first)"
        if accept_risk_reason:
            warnings.append(f"{msg} (accept-risk: {accept_risk_reason})")
        else:
            blockers.append(msg)
        return
    reh = jp.load_judge_rehearsal(reh_path)
    if reh is None:
        msg = (
            "judge_rehearsal: missing or unparseable judge_rehearsal.json "
            "(run Prompts/modules/judge_rehearsal.md)"
        )
        if accept_risk_reason:
            warnings.append(f"{msg} (accept-risk: {accept_risk_reason})")
        else:
            blockers.append(msg)
        return
    reh_blockers, _summary = jp.validate_judge_rehearsal(reh, prep_path)
    for b in reh_blockers:
        if accept_risk_reason:
            warnings.append(f"{b} (accept-risk: {accept_risk_reason})")
        else:
            blockers.append(b)


def run_preflight(
    task_name: str,
    session: Dict[str, Any],
    state: Dict[str, Any],
    accept_risk: Optional[str] = None,
) -> Dict[str, Any]:
    blockers: List[str] = []
    warnings: List[str] = []
    if accept_risk and str(accept_risk).strip():
        state["judge_prep_accept_risk"] = True
        state["judge_prep_accept_risk_reason"] = str(accept_risk).strip()
        state["judge_prep_accept_risk_at"] = utc_now()
    accept_risk_reason = (
        state.get("judge_prep_accept_risk_reason") if state.get("judge_prep_accept_risk") else None
    )
    if not session.get("working_task_root") or not session.get("real_task_root"):
        blockers.append("Task root not selected")
    pub = state.get("public_analysis") or session.get("public_analysis")
    internal = state.get("internal_validity") or session.get("internal_validity")
    dup = state.get("duplicate_analysis") or session.get("duplicate_analysis")
    reason = state.get("internal_validity_reason") or session.get("internal_validity_reason")
    if not pub or not internal or not dup:
        blockers.append("All three live verdict fields must be recorded")
    elif not public_matches_duplicate(str(pub), str(dup)):
        blockers.append(f"Public/Duplicate mismatch: {pub} vs {dup}")
    if not reason:
        blockers.append("Internal Validity reason missing")
    branch = dup
    if state.get("branch") and branch and state.get("branch") != branch:
        blockers.append("Stored branch does not match Duplicate Analysis")

    working = Path(session["working_task_root"]) if session.get("working_task_root") else None
    if working and working.exists():
        req = required_files_report(working)
        # For Fixable corrected packages, golden.patch required (solution.patch not enough)
        if branch == "Fixable":
            if not (working / "solution/golden.patch").exists():
                blockers.append("Corrected package requires solution/golden.patch")
            meta = metadata_limits_report(working)
            if not meta.get("ok"):
                blockers.extend(meta.get("errors") or [])
            warnings.extend(meta.get("warnings") or [])
            if meta.get("network_blocks_ok") is False:
                for issue in meta.get("network_blocks_issues") or ["Harbor network blocks missing/wrong"]:
                    blockers.append(f"network blocks: {issue}")
            # compose network_mode=none is a separate packaging defect
            for cand in (
                "docker_compose.yaml",
                "docker-compose.yaml",
                "environment/docker_compose.yaml",
                "environment/docker-compose.yaml",
            ):
                cp = working / cand
                if cp.is_file() and re.search(
                    r"(?m)^\s*network_mode\s*[:=]\s*[\"']?none[\"']?\s*$",
                    cp.read_text(encoding="utf-8", errors="replace"),
                ):
                    blockers.append(
                        f'{cand} still has network_mode="none" — run ensure-packaging-hygiene'
                    )
            sync_ok, sync_msg = check_instruction_sync(working)
            if not sync_ok:
                blockers.append(f"Instruction/problem_statement mismatch: {sync_msg}")
            cfg = validate_config(working)
            if not cfg.get("ok"):
                blockers.extend(cfg.get("errors") or [])
            warnings.extend(cfg.get("warnings") or [])
            state["fail_to_pass_count"] = cfg.get("fail_to_pass_count")
            state["test_id_status"] = cfg.get("test_id_status")
            applies, msg = check_tests_patch_applies(working)
            if not applies:
                blockers.append(f"tests.patch apply failed: {msg}")
            patch_health = analyze_tests_patch_health(working)
            if patch_health.get("hunk_mismatches"):
                blockers.append(
                    "tests.patch has corrupt/mismatched hunks — regenerate so git apply --check passes"
                )
            if patch_health.get("git_apply_check") is False and patch_health.get("patch_dry_run") is True:
                blockers.append(
                    "tests.patch fails git apply --check (patch-only success is unsafe for renames) — regenerate patch"
                )
            warnings.extend(patch_health.get("warnings") or [])
            gitrep = git_hygiene_report(working, base_commit=meta.get("base_commit_sha"))
            if not gitrep.get("ok"):
                blockers.extend(gitrep.get("errors") or [])
            arts = artifact_scan(working)
            if not arts.get("passed"):
                blockers.append("Forbidden artifacts present")
            if req["missing"]:
                # allow golden missing only if already handled
                blockers.append(f"Missing required files in working copy: {req['missing']}")
            warnings.extend(req.get("dialect_notes") or [])
            # Mechanical Ultra gate (check_task) — FIXABLE/NOT_FIXABLE block packaging
            sc_json = session_paths(task_name)["outputs"] / "static_check_report.json"
            sc_md = session_paths(task_name)["outputs"] / "static_check_report.md"
            sc = run_static_check(working, sc_json, sc_md)
            state["static_check_completed"] = True
            state["static_check_passed"] = bool(sc["ok"])
            state["static_check_fixable_ids"] = sc["fixable_ids"]
            state["static_check_advisory_ids"] = sc["advisory_ids"]
            state["static_check_not_fixable_ids"] = sc["not_fixable_ids"]
            state["dialect_notes"] = req.get("dialect_notes") or []
            for fid in sc["fixable_ids"]:
                msg = f"static-check FIXABLE open: {fid}"
                if accept_risk_reason and fid in ACCEPT_RISK_STATIC_FIXABLE_IDS:
                    warnings.append(f"{msg} (accept-risk: {accept_risk_reason})")
                else:
                    blockers.append(msg)
            for fid in sc["not_fixable_ids"]:
                blockers.append(f"static-check NOT_FIXABLE open: {fid}")
            for fid in sc["advisory_ids"]:
                warnings.append(f"static-check ADVISORY: {fid}")
            # S10.5 — judge_prep after static-check (map even if FIXABLE open)
            jp_report = run_judge_prep_for_task(task_name, working, state)
            apply_judge_prep_preflight_blockers(jp_report, blockers, warnings, accept_risk_reason)
            apply_judge_rehearsal_preflight_blockers(
                session_paths(task_name)["outputs"], blockers, warnings, accept_risk_reason
            )
            if accept_risk_reason:
                warnings.append(
                    f"judge_prep accept-risk recorded for reviewer comments: {accept_risk_reason}"
                )
        elif branch == "Valid-as-is":
            # validate against original root
            root = Path(session["real_task_root"])
            sync_ok, sync_msg = check_instruction_sync(root)
            if not sync_ok:
                blockers.append(f"Instruction sync failed on original: {sync_msg}")
            cfg = validate_config(root)
            f2p = cfg.get("fail_to_pass_count") or 0
            if f2p < 11:
                warnings.append(
                    f"Valid-as-is live confirmation 'more than 10' requires >=11 (structural count={f2p})"
                )
            sc_json = session_paths(task_name)["outputs"] / "static_check_report.json"
            sc_md = session_paths(task_name)["outputs"] / "static_check_report.md"
            sc = run_static_check(root, sc_json, sc_md)
            state["static_check_completed"] = True
            state["static_check_passed"] = bool(sc["ok"])
            state["static_check_fixable_ids"] = sc["fixable_ids"]
            state["static_check_advisory_ids"] = sc["advisory_ids"]
            state["static_check_not_fixable_ids"] = sc["not_fixable_ids"]
            for fid in sc["fixable_ids"]:
                msg = f"static-check FIXABLE open: {fid}"
                if accept_risk_reason and fid in ACCEPT_RISK_STATIC_FIXABLE_IDS:
                    warnings.append(f"{msg} (accept-risk: {accept_risk_reason})")
                else:
                    blockers.append(msg)
            for fid in sc["not_fixable_ids"]:
                blockers.append(f"static-check NOT_FIXABLE open: {fid}")
            for fid in sc["advisory_ids"]:
                warnings.append(f"static-check ADVISORY: {fid}")
            jp_report = run_judge_prep_for_task(task_name, root, state)
            apply_judge_prep_preflight_blockers(jp_report, blockers, warnings, accept_risk_reason)
            apply_judge_rehearsal_preflight_blockers(
                session_paths(task_name)["outputs"], blockers, warnings, accept_risk_reason
            )
            if accept_risk_reason:
                warnings.append(
                    f"judge_prep accept-risk recorded for reviewer comments: {accept_risk_reason}"
                )
            for key, label in (
                ("docker_build_status", "Docker"),
                ("oracle_status", "Oracle"),
                ("nop_status", "NOP"),
            ):
                st = state.get(key)
                if st == "failed":
                    blockers.append(f"{label} validation failed")
                elif st == "not_run":
                    blockers.append(f"{label} validation not_run (required for Valid-as-is when technically available)")
            if state.get("oracle_status") in {"passed", "confirmed_by_logs"} and state.get("oracle_reward") not in (1.0, 1, "1.0"):
                blockers.append("Oracle reward must be 1.0 for Valid-as-is")
            if state.get("nop_status") in {"passed", "confirmed_by_logs"} and state.get("nop_reward") not in (0.0, 0, "0.0"):
                blockers.append("NOP reward must be 0.0 for Valid-as-is")
            if state.get("pass_to_pass_status") == "failed":
                blockers.append("Pass-to-pass failed")
        elif branch == "Invalid/Not Fixable":
            if not (state.get("invalid_category") or session.get("invalid_category")):
                blockers.append("Invalid category required")
            if not (state.get("unfixable_explanation") or session.get("unfixable_explanation")):
                blockers.append("Unfixable explanation required")
    else:
        blockers.append("Working task root missing")

    ready_to_finalize = False
    ready_to_package = False
    validation_level = "not_validated"

    if branch == "Valid-as-is":
        ready_to_package = False
        ready_to_finalize = len(blockers) == 0
        validation_level = "locally_validated" if ready_to_finalize else "not_validated"
    elif branch == "Fixable":
        # structural blockers prevent packaging
        local_statuses = [state.get("docker_build_status"), state.get("oracle_status"), state.get("nop_status")]
        if any(s == "failed" for s in local_statuses):
            blockers.append("Required local check failed — correct before packaging")
        structural_ok = len(blockers) == 0
        if structural_ok:
            ready_to_package = True
            if any(s == "not_run" for s in local_statuses):
                validation_level = "locally_prepared_platform_evaluation_required"
            elif all(s in {"passed", "confirmed_by_logs"} for s in local_statuses):
                validation_level = "locally_validated"
            else:
                validation_level = "locally_prepared_platform_evaluation_required"
        ready_to_finalize = False
    elif branch == "Invalid/Not Fixable":
        ready_to_package = False
        ready_to_finalize = len(blockers) == 0
        validation_level = "evidence_only"

    result = {
        "task_name": task_name,
        "branch": branch,
        "blockers": blockers,
        "warnings": warnings,
        "ready_to_finalize": ready_to_finalize,
        "ready_to_package": ready_to_package,
        "validation_level": validation_level,
        "timestamp": utc_now(),
        "ok": len(blockers) == 0,
    }
    state["blocking_issues"] = blockers
    state["warnings"] = warnings
    state["ready_to_finalize"] = ready_to_finalize
    state["ready_to_package"] = ready_to_package
    state["validation_level"] = validation_level
    state["packaging_preflight_passed"] = bool(ready_to_package and branch == "Fixable")
    return result


def cmd_judge_prep(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    state = load_workflow_state(task_name)
    root = resolve_static_check_root(session, state)
    # Prefer existing static-check report; do not re-run check_task here (S10.5 assumes it ran).
    paths = session_paths(task_name)
    sc_json = paths["outputs"] / "static_check_report.json"
    if not sc_json.is_file():
        die("static_check_report.json missing — run static-check before judge-prep")
    report = run_judge_prep_for_task(task_name, root, state)
    save_workflow_state(task_name, state)
    print("JUDGE PREP COMPLETE")
    print(f"  root: {root}")
    print(f"  hard_stopped: {report.get('hard_stopped')}")
    print(f"  prep_passed: {report.get('prep_passed')}")
    print(f"  blockers: {report.get('blockers')}")
    print(f"  md: {paths['outputs'] / 'judge_prep.md'}")
    print(f"  decisions (human-owned): {paths['outputs'] / 'judge_prep_decisions.json'}")
    if report.get("hard_stopped") or not report.get("prep_passed"):
        raise SystemExit(1)


def cmd_preflight(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    state = load_workflow_state(task_name)
    accept = getattr(args, "accept_risk", None)
    result = run_preflight(task_name, session, state, accept_risk=accept)
    paths = session_paths(task_name)
    paths["preflight_json"].write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    save_workflow_state(task_name, state)
    print("PREFLIGHT")
    print(f"  branch: {result['branch']}")
    print(f"  ready_to_finalize: {result['ready_to_finalize']}")
    print(f"  ready_to_package: {result['ready_to_package']}")
    print(f"  validation_level: {result['validation_level']}")
    if state.get("judge_prep_accept_risk"):
        print(f"  judge_prep accept-risk: {state.get('judge_prep_accept_risk_reason')}")
    if result["blockers"]:
        print("  BLOCKERS:")
        for b in result["blockers"]:
            print(f"    - {b}")
    if result["warnings"]:
        print("  WARNINGS:")
        for w in result["warnings"]:
            print(f"    - {w}")
    if result["blockers"]:
        die("Packaging/finalization blocked by preflight.", code=2)


def cmd_package_fixable(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    state = load_workflow_state(task_name)
    pub = state.get("public_analysis") or session.get("public_analysis")
    dup = state.get("duplicate_analysis") or session.get("duplicate_analysis")
    internal = state.get("internal_validity") or session.get("internal_validity")
    if pub != "Fixable" or dup != "Fixable":
        die("package-fixable requires Public and Duplicate = Fixable")
    if not internal:
        die("Internal Validity must be recorded")

    # Always re-run preflight immediately before packaging
    result = run_preflight(task_name, session, state)
    paths = session_paths(task_name)
    paths["preflight_json"].write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    save_workflow_state(task_name, state)
    if not state.get("ready_to_package"):
        print("Packaging blocked. The task has not passed Sentinel preflight.", file=sys.stderr)
        for b in state.get("blocking_issues") or []:
            print(f"  - {b}", file=sys.stderr)
        raise SystemExit(2)

    working_root = Path(session["working_task_root"])
    dest = paths["updated_zip_dir"] / f"{task_name}__corrected.zip"
    if Path(session["original_path"]).resolve() == dest.resolve():
        die("Refusing to overwrite original ZIP")

    try:
        written = package_flat_task_zip(working_root, dest)
        ok, errors = verify_corrected_zip(dest)
        if not ok:
            dest.unlink(missing_ok=True)
            partial = dest.with_suffix(dest.suffix + ".partial")
            partial.unlink(missing_ok=True)
            print("Packaging blocked. The task has not passed Sentinel preflight.", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            raise SystemExit(2)
    except Exception:
        # ensure no misleading partial
        dest.unlink(missing_ok=True)
        partial = dest.with_suffix(dest.suffix + ".partial")
        partial.unlink(missing_ok=True)
        raise

    digest = sha256_file(dest)
    with zipfile.ZipFile(dest, "r") as zf:
        names = zf.namelist()
        top = sorted({n.split("/")[0] for n in names if n})
    # Delete-first refresh into the submitter drop folder (Finder Date Added stays honest).
    ready_dir = WORKSPACE_ROOT / "work" / "task ready_to_submit"
    ready_dir.mkdir(parents=True, exist_ok=True)
    ready_dest = ready_dir / dest.name
    ready_dest.unlink(missing_ok=True)
    # Also clear a double-dot typo variant if present from manual downloads.
    (ready_dir / f"{task_name}__corrected..zip").unlink(missing_ok=True)
    shutil.copy2(dest, ready_dest)
    manifest = {
        "zip_filename": dest.name,
        "sha256": digest,
        "file_count": len(written),
        "top_level_entries": top,
        "excluded_path_confirmation": sorted(EXCLUDE_FROM_CORRECTED_ZIP),
        "creation_timestamp": utc_now(),
        "validation_level": state.get("validation_level"),
        "original_zip_preserved": True,
        "original_sha256": session.get("sha256"),
        "ready_to_submit_zip": str(ready_dest),
    }
    paths["zip_manifest"].write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Forward-validation prediction (docs/VALIDATION_STRATEGY.md)
    try:
        from write_judge_prediction import write_prediction  # type: ignore

        pred_path = write_prediction(paths["outputs"], task_name)
        print(f"  judge_prediction: {pred_path}")
    except Exception as exc:  # noqa: BLE001 — packaging succeeded; prediction is best-effort
        print(f"  WARNING: judge_prediction not written: {exc}", file=sys.stderr)
    session["current_workflow_phase"] = "packaged_fixable"
    save_session(task_name, session)
    save_workflow_state(task_name, state)
    print("PACKAGE FIXABLE COMPLETE")
    print(f"  corrected_zip: {dest}")
    print(f"  ready_to_submit: {ready_dest}")
    print(f"  sha256: {digest}")
    print(f"  validation_level: {state.get('validation_level')}")
    print(f"  original_preserved: {session['original_path']}")


def cmd_package_invalid(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    state = load_workflow_state(task_name)
    pub = state.get("public_analysis") or session.get("public_analysis")
    dup = state.get("duplicate_analysis") or session.get("duplicate_analysis")
    if pub != "Invalid/Not Fixable" or dup != "Invalid/Not Fixable":
        die("package-invalid requires Public and Duplicate = Invalid/Not Fixable")
    if not (state.get("internal_validity") or session.get("internal_validity")):
        die("Internal Validity must be recorded")
    category = state.get("invalid_category") or session.get("invalid_category") or args.invalid_category
    explanation = (
        state.get("unfixable_explanation")
        or session.get("unfixable_explanation")
        or args.explanation
    )
    if not category:
        die("Invalid category required")
    if not explanation:
        die("Unfixable explanation required")

    paths = session_paths(task_name)
    dest = paths["invalid_evidence_dir"] / f"{task_name}__unfixable_evidence.zip"
    staging = paths["work"] / "_invalid_evidence_staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    wc = Path(session["working_copy_path"])
    if wc.exists():
        copytree(wc, staging / "working_copy")
    if paths["validation_logs"].exists():
        copytree(paths["validation_logs"], staging / "validation_logs")
    if paths["analysis"].exists():
        copytree(paths["analysis"], staging / "analysis")

    (staging / "README_EVIDENCE.txt").write_text(
        "Manual reviewer evidence — not a corrected valid task package.\n",
        encoding="utf-8",
    )
    (staging / "evidence_summary.md").write_text(
        "# Unfixable Evidence Summary\n\n"
        f"- Task: `{task_name}`\n"
        f"- Category: `{category}`\n"
        f"- Sub-issue: `{state.get('invalid_environment_subissue') or session.get('invalid_environment_subissue')}`\n"
        f"- Original ZIP: `{session.get('original_path')}`\n"
        f"- SHA-256: `{session.get('sha256')}`\n\n"
        "## Explanation\n\n"
        f"{explanation}\n\n"
        "This archive is **manual-review evidence**, not a corrected valid submission ZIP.\n",
        encoding="utf-8",
    )
    (staging / "unfixable_explanation.txt").write_text(explanation + "\n", encoding="utf-8")

    if dest.exists():
        dest.unlink()
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for dirpath, _, filenames in os.walk(staging):
            for fn in filenames:
                full = Path(dirpath) / fn
                zf.write(full, arcname=full.relative_to(staging).as_posix())
    shutil.rmtree(staging)

    # Ensure no corrected ZIP claim
    corrected = paths["updated_zip_dir"] / f"{task_name}__corrected.zip"
    if corrected.exists() and not args.keep_any_corrected:
        # do not delete user artifacts unexpectedly unless created same session — leave but warn
        print("WARNING: a corrected ZIP path exists but is not valid for Invalid branch", file=sys.stderr)

    session["current_workflow_phase"] = "packaged_invalid"
    save_session(task_name, session)
    state["invalid_category"] = category
    state["unfixable_explanation"] = explanation
    save_workflow_state(task_name, state)
    print("PACKAGE INVALID COMPLETE")
    print(f"  evidence_zip: {dest}")
    print("  label: Manual reviewer evidence — not a corrected valid task package.")
    print(f"  original_preserved: {session['original_path']}")


def cmd_status(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    state = load_workflow_state(task_name)
    paths = session_paths(task_name)
    print("SESSION STATUS")
    fields = [
        ("task", task_name),
        ("mode", state.get("mode")),
        ("original_zip", session.get("original_path")),
        ("original_sha256", session.get("sha256")),
        ("public_analysis", state.get("public_analysis") or session.get("public_analysis")),
        ("internal_validity", state.get("internal_validity") or session.get("internal_validity")),
        ("internal_validity_reason", state.get("internal_validity_reason") or session.get("internal_validity_reason")),
        ("duplicate_analysis", state.get("duplicate_analysis") or session.get("duplicate_analysis")),
        ("branch", state.get("branch") or session.get("branch")),
        ("audit_completed", state.get("audit_completed")),
        ("missing_files", state.get("missing_required_files")),
        ("instruction_sync", state.get("instruction_problem_statement_match")),
        ("fail_to_pass_count", state.get("fail_to_pass_count")),
        ("test_id_status", state.get("test_id_status")),
        ("tests_patch_applies", state.get("tests_patch_applies")),
        ("git_hygiene_ok", state.get("git_hygiene_ok")),
        ("docker_build_status", state.get("docker_build_status")),
        ("oracle_status", state.get("oracle_status")),
        ("oracle_reward", state.get("oracle_reward")),
        ("nop_status", state.get("nop_status")),
        ("nop_reward", state.get("nop_reward")),
        ("pass_to_pass_status", state.get("pass_to_pass_status")),
        ("artifact_scan_passed", state.get("artifact_scan_passed")),
        ("packaging_preflight_passed", state.get("packaging_preflight_passed")),
        ("ready_to_finalize", state.get("ready_to_finalize")),
        ("ready_to_package", state.get("ready_to_package")),
        ("validation_level", state.get("validation_level")),
        ("blocking_issues", state.get("blocking_issues")),
        ("warnings", state.get("warnings")),
        ("outputs", str(paths["outputs"])),
        ("workflow_state", str(paths["workflow_state"])),
    ]
    for k, v in fields:
        print(f"  {k}: {v}")


def cmd_archive(args: argparse.Namespace) -> None:
    task_name, session = load_session(args.task_name)
    paths = session_paths(task_name)
    dest_parent = WORKSPACE_ROOT / "completed_tasks"
    dest_parent.mkdir(parents=True, exist_ok=True)
    dest = dest_parent / task_name
    if dest.exists():
        dest = dest_parent / f"{task_name}__{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    shutil.move(str(paths["work"]), str(dest))
    paths["outputs"].mkdir(parents=True, exist_ok=True)
    (paths["outputs"] / "archived_session_path.txt").write_text(str(dest.resolve()) + "\n", encoding="utf-8")
    print("ARCHIVE COMPLETE")
    print(f"  moved_to: {dest}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Sentinel submitter automation (gates only; no auto-verdicts)")
    sub = p.add_subparsers(dest="command", required=True)

    def add_task(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--task-name")

    intake = sub.add_parser("intake")
    intake.add_argument("--zip")
    intake.add_argument("--task-name")
    intake.add_argument("--platform-input")
    intake.add_argument("--force", action="store_true")
    intake.set_defaults(func=cmd_intake)

    prep = sub.add_parser("prepare")
    add_task(prep)
    prep.set_defaults(func=cmd_prepare)

    sel = sub.add_parser("select-task")
    add_task(sel)
    sel.add_argument("path")
    sel.set_defaults(func=cmd_select_task)

    audit = sub.add_parser("audit")
    add_task(audit)
    audit.set_defaults(func=cmd_audit)

    sc = sub.add_parser(
        "static-check",
        help="Run sentinel-ultra-review check_task.py (+ patch-health) against working_copy or frozen root",
    )
    add_task(sc)
    sc.set_defaults(func=cmd_static_check)

    jp = sub.add_parser(
        "judge-prep",
        help="S10.5 deterministic Quality Check prep (bipartite map; cites static-check; never overwrites decisions)",
    )
    add_task(jp)
    jp.set_defaults(func=cmd_judge_prep)

    sv = sub.add_parser("set-verdicts")
    add_task(sv)
    sv.add_argument("--public-analysis", required=True)
    sv.add_argument("--internal-validity", required=True)
    sv.add_argument("--duplicate-analysis", required=True)
    sv.add_argument("--reason", required=True)
    sv.add_argument("--invalid-category")
    sv.add_argument("--environment-subissue")
    sv.add_argument("--unfixable-explanation")
    sv.set_defaults(func=cmd_set_verdicts)

    sync = sub.add_parser("sync-problem-statement")
    add_task(sync)
    sync.set_defaults(func=cmd_sync_problem_statement)

    hyg = sub.add_parser(
        "ensure-packaging-hygiene",
        help="Fixable working_copy only: extract grade.py, ensure Harbor network blocks, strip compose network_mode=none, chmod solve.sh",
    )
    add_task(hyg)
    hyg.set_defaults(func=cmd_ensure_packaging_hygiene)

    rv = sub.add_parser("record-validation")
    add_task(rv)
    rv.add_argument("--check", required=True, choices=["docker_build", "oracle", "nop", "pass_to_pass", "tests_patch", "git", "packaging"])
    rv.add_argument("--status", required=True, choices=sorted(VALIDATION_STATUSES))
    rv.add_argument("--evidence")
    rv.add_argument("--command")
    rv.add_argument("--exit-code", type=int)
    rv.add_argument("--summary")
    rv.add_argument("--reward")
    rv.add_argument("--confirmed-by-logs", action="store_true")
    rv.set_defaults(func=cmd_record_validation)

    pre = sub.add_parser("preflight")
    add_task(pre)
    pre.add_argument(
        "--accept-risk",
        metavar="REASON",
        help=(
            "Override judge_prep blockers (gaps/overreach/auto-REMOVE/UNDECIDED/invalidated) "
            "and demote static-check V6 (PR test-migration deletes); recorded for reviewer comments"
        ),
    )
    pre.set_defaults(func=cmd_preflight)

    pf = sub.add_parser("package-fixable")
    add_task(pf)
    pf.set_defaults(func=cmd_package_fixable)

    pi = sub.add_parser("package-invalid")
    add_task(pi)
    pi.add_argument("--invalid-category")
    pi.add_argument("--explanation")
    pi.add_argument("--keep-any-corrected", action="store_true")
    pi.set_defaults(func=cmd_package_invalid)

    st = sub.add_parser("status")
    add_task(st)
    st.set_defaults(func=cmd_status)

    ar = sub.add_parser("archive")
    add_task(ar)
    ar.set_defaults(func=cmd_archive)

    return p


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
