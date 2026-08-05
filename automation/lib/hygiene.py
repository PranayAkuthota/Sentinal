"""Fixable packaging hygiene helpers (working_copy only)."""

from __future__ import annotations

import importlib.util
import sys
import tomllib
from pathlib import Path
from typing import List, Tuple


def _load_fix_common():
    """Load fix_common.py from the sentinel-ultra-review skill (single NET / compose source)."""
    scripts = (
        Path(__file__).resolve().parents[2]
        / ".cursor"
        / "skills"
        / "sentinel-ultra-review"
        / "scripts"
    )
    path = scripts / "fix_common.py"
    if not path.is_file():
        raise FileNotFoundError(f"fix_common.py not found at {path}")
    spec = importlib.util.spec_from_file_location("sentinel_fix_common", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load fix_common from {path}")
    mod = importlib.util.module_from_spec(spec)
    # Avoid polluting if already loaded under another name
    sys.modules.setdefault("sentinel_fix_common", mod)
    spec.loader.exec_module(mod)
    return mod


def extract_grade_py_from_test_sh(task_root: Path) -> Tuple[bool, str]:
    grade = task_root / "tests" / "grade.py"
    if grade.exists() and grade.stat().st_size > 0:
        return False, "tests/grade.py already present"
    test_sh = task_root / "tests" / "test.sh"
    if not test_sh.exists():
        return False, "tests/test.sh missing"
    text = test_sh.read_text(encoding="utf-8", errors="replace")
    end = "GRADE_PY_EOF\n"
    marker = 'cat > /tmp/grade.py <<\'GRADE_PY_EOF\'\n'
    if marker not in text:
        marker = 'cat > /tmp/grade.py <<"GRADE_PY_EOF"\n'
        if marker not in text:
            marker = 'cat > /tmp/grade.py <<\"GRADE_PY_EOF\"\n'
            if marker not in text:
                return False, "no embedded GRADE_PY_EOF block in test.sh"
    start = text.index(marker) + len(marker)
    if end not in text[start:]:
        return False, "GRADE_PY_EOF terminator missing"
    end_idx = text.index(end, start)
    body = text[start:end_idx]
    if "def " not in body and "reward" not in body.lower():
        return False, "embedded block does not look like grade.py"
    grade.write_text(body + ("\n" if not body.endswith("\n") else ""), encoding="utf-8")
    return True, f"extracted tests/grade.py ({len(body.splitlines())} lines)"


def ensure_network_blocks_in_task_toml(task_root: Path) -> Tuple[bool, str]:
    """Ensure Harbor network_mode / allowed_hosts per [environment]/[agent]/[verifier].

    Reuses fix_common.apply_network_blocks (NET dict). Idempotent; line-oriented
    write that preserves comments and field order; creates missing sections/keys.
    Validates result with tomllib.
    """
    path = task_root / "task.toml"
    if not path.exists():
        return False, "task.toml missing"
    fc = _load_fix_common()
    original = path.read_text(encoding="utf-8")
    new_text, changes = fc.apply_network_blocks(original)
    if not changes:
        # Still validate parseability
        try:
            tomllib.loads(original)
        except tomllib.TOMLDecodeError as exc:
            return False, f"task.toml already correct for network but invalid TOML: {exc}"
        return False, "network blocks already correct"
    try:
        tomllib.loads(new_text)
    except tomllib.TOMLDecodeError as exc:
        return False, f"refusing to write invalid TOML after network ensure: {exc}"
    path.write_text(new_text, encoding="utf-8")
    return True, "; ".join(changes)


def strip_compose_network_none(task_root: Path) -> Tuple[bool, str]:
    """Remove network_mode = \"none\" from docker_compose.yaml variants (fix_common)."""
    fc = _load_fix_common()
    plan: List[tuple] = []
    fc.r_compose(str(task_root), True, plan)
    if not plan:
        return False, "no docker_compose network_mode=none found"
    msgs = [p[1] for p in plan]
    return True, "; ".join(msgs)


def validate_network_blocks(task_root: Path) -> Tuple[bool, List[str]]:
    """Check network blocks without mutating. Returns (ok, problem messages)."""
    path = task_root / "task.toml"
    if not path.exists():
        return False, ["task.toml missing"]
    fc = _load_fix_common()
    text = path.read_text(encoding="utf-8")
    _, changes = fc.apply_network_blocks(text)
    if changes:
        return False, changes
    return True, []
