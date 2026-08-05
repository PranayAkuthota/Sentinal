"""Minimal task.toml key=value parser (line-oriented)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def parse_task_toml_simple(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if not path.exists():
        return data
    section = ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("[") and s.endswith("]"):
            section = s[1:-1].strip()
            continue
        if "=" not in s:
            continue
        key, val = s.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        full = f"{section}.{key}" if section else key
        data[full] = val
        data[key] = val
    return data
