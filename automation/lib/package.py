"""Corrected-task ZIP packaging and verification."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import List, Tuple

EXCLUDE_FROM_CORRECTED_ZIP = {
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
    "workflow_state.json",
}

EXCLUDE_TOP_LEVEL_ONLY = {
    "session",
    "analysis",
    "original",
    "extracted_original",
}


def should_exclude_member(name: str) -> bool:
    parts = Path(name).parts
    if not parts:
        return True
    if parts[0] in EXCLUDE_TOP_LEVEL_ONLY:
        return True
    for part in parts:
        if part in EXCLUDE_FROM_CORRECTED_ZIP:
            return True
        if part.endswith((".pyc", ".orig", ".bak", ".swp", "~")):
            return True
        if part.endswith("~"):
            return True
    if "ground_truth" in name.lower():
        return True
    return False


def _zip_write_symlink(zf: zipfile.ZipFile, full: Path, rel: str) -> None:
    target = os.readlink(full)
    info = zipfile.ZipInfo(rel)
    info.create_system = 3
    info.external_attr = (0o120777 & 0xFFFF) << 16
    zf.writestr(info, target)


def package_flat_task_zip(task_root: Path, dest_zip: Path) -> List[str]:
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    partial = dest_zip.with_suffix(dest_zip.suffix + ".partial")
    if partial.exists():
        partial.unlink()
    if dest_zip.exists():
        dest_zip.unlink()
    written: List[str] = []
    with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(task_root, followlinks=False):
            rel_dir = Path(dirpath).relative_to(task_root)
            keep_dirs: List[str] = []
            for d in list(dirnames):
                full_d = Path(dirpath) / d
                rel_d = (rel_dir / d).as_posix() if str(rel_dir) != "." else d
                if should_exclude_member(rel_d):
                    continue
                if full_d.is_symlink():
                    _zip_write_symlink(zf, full_d, rel_d)
                    written.append(rel_d)
                    continue
                keep_dirs.append(d)
            dirnames[:] = keep_dirs
            for fn in filenames:
                full = Path(dirpath) / fn
                rel = full.relative_to(task_root).as_posix()
                if should_exclude_member(rel):
                    continue
                if full.is_symlink():
                    _zip_write_symlink(zf, full, rel)
                else:
                    zf.write(full, arcname=rel)
                written.append(rel)
    partial.replace(dest_zip)
    return written


def verify_corrected_zip(dest_zip: Path) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    required_top = {"instruction.md", "task.toml", "environment", "solution", "tests"}
    with zipfile.ZipFile(dest_zip, "r") as zf:
        names = zf.namelist()
        top = {n.split("/")[0] for n in names if n and not n.endswith("/")}
        top |= {n.split("/")[0] for n in names if n.endswith("/") and n.count("/") == 1}
        for n in names:
            if "/" in n:
                top.add(n.split("/")[0])
            elif n:
                top.add(n)
        missing = required_top - top
        if missing:
            errors.append(f"Missing top-level entries: {sorted(missing)}")
        if "task" in top and "instruction.md" not in top:
            errors.append("ZIP appears wrapped in outer task/")
        if any(n == "runs/" or n.startswith("runs/") for n in names):
            errors.append("ZIP contains runs/")
        for banned in ("workflow_state.json", "__pycache__/"):
            if any(banned in n for n in names):
                errors.append(f"ZIP contains banned path pattern: {banned}")
        for n in names:
            first = n.split("/", 1)[0]
            if first in {"session", "analysis", "original", "extracted_original"}:
                errors.append(f"ZIP contains banned top-level path: {first}/")
                break
    return (len(errors) == 0, errors)
