"""Instruction ↔ problem_statement sync check."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple


def check_instruction_sync(task_root: Path) -> Tuple[bool, str]:
    a = task_root / "instruction.md"
    b = task_root / "environment" / "problem_statement.md"
    if not a.exists() or not b.exists():
        return False, "missing instruction.md or environment/problem_statement.md"
    if a.read_bytes() == b.read_bytes():
        return True, "byte-identical"
    la = a.read_text(encoding="utf-8", errors="replace").splitlines()
    lb = b.read_text(encoding="utf-8", errors="replace").splitlines()
    return False, f"byte mismatch (instruction lines={len(la)}, problem_statement lines={len(lb)})"
