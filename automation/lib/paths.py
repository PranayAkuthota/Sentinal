"""Workspace path helpers."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parent
AUTOMATION_DIR = LIB_DIR.parent
WORKSPACE_ROOT = AUTOMATION_DIR.parent


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_task_name(name: str) -> str:
    base = Path(name).stem
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
    if not base or ".." in base or "/" in base or "\\" in base:
        die(f"Rejected unsafe task name: {name}")
    return base
