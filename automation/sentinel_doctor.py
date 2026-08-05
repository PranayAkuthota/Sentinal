#!/usr/bin/env python3
"""Framework health check for the Sentinel Submitter repository.

Scores depth and tooling — not layout presence alone.
Never assigns task verdicts. Never mutates task packages.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "incoming_tasks",
    "work",
    "task_outputs",
    "completed_tasks",
    "automation",
    "automation/lib",
    "docs",
    "docs/history",
    "workflows/stages",
    "Prompts/modules",
    "Prompts/Execution",
    "templates",
    "validation/checklists",
    "knowledge/patterns",
    "knowledge/failures",
    "knowledge/proposals",
    "repo_tests",
    "ci_checks",
    ".cursor/rules",
    ".cursor/skills",
]

REQUIRED_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "docs/ARCHITECTURE.md",
    "docs/WORKFLOW.md",
    "docs/COMMANDS.md",
    "docs/EXECUTION_LAYER.md",
    "docs/SUBMITTER_BLOCKERS.md",
    "docs/FAILURE_CATALOG.md",
    "docs/FRAMEWORK_REDESIGN_AUDIT.md",
    "docs/LEARNING_SYSTEM.md",
    ".cursor/rules/Review_Guidelines.mdc",
    "automation/sentinel_submitter.py",
    "automation/local_oracle_nop.py",
    "automation/capture_learning.py",
    "automation/checkpoint_ready.py",
    "automation/promote_learning.py",
    "automation/sentinel_doctor.py",
]

STAGE_MIN_BYTES = 800
MODULE_MIN_BYTES = 400
SKILL_MIN_BYTES = 900
EXEC_PROMPT_MIN_BYTES = 1500


def try_import(rel: str) -> str | None:
    path = ROOT / rel
    try:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        assert spec and spec.loader
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return None
    except Exception as e:
        return f"import failed {rel}: {e}"


def min_depth(paths: list[Path], min_bytes: int, label: str) -> list[str]:
    warns = []
    for p in paths:
        if p.stat().st_size < min_bytes:
            warns.append(f"thin {label}: {p.relative_to(ROOT)} ({p.stat().st_size}<{min_bytes}B)")
    return warns


def main() -> int:
    errors: list[str] = []
    warns: list[str] = []
    score_parts: dict[str, int] = {}

    # Layout (20)
    missing = 0
    for d in REQUIRED_DIRS:
        if not (ROOT / d).is_dir():
            errors.append(f"missing dir: {d}")
            missing += 1
    for f in REQUIRED_FILES:
        if not (ROOT / f).is_file():
            errors.append(f"missing file: {f}")
            missing += 1
    score_parts["layout"] = max(0, 20 - 2 * missing)

    # Imports (15)
    import_errs = 0
    for mod in (
        "automation/sentinel_submitter.py",
        "automation/local_oracle_nop.py",
        "automation/capture_learning.py",
        "automation/checkpoint_ready.py",
        "automation/promote_learning.py",
    ):
        err = try_import(mod)
        if err:
            errors.append(err)
            import_errs += 1
    score_parts["imports"] = max(0, 15 - 3 * import_errs)

    # Stage depth (15)
    stages = sorted((ROOT / "workflows/stages").glob("S*.md"))
    if len(stages) < 13:
        errors.append(f"expected ≥13 stage files, found {len(stages)}")
    thin_stages = min_depth(stages, STAGE_MIN_BYTES, "stage")
    warns.extend(thin_stages)
    stage_score = 15
    if len(stages) < 13:
        stage_score -= 8
    stage_score -= min(10, len(thin_stages))
    score_parts["stages"] = max(0, stage_score)

    # Module depth (10)
    modules = sorted((ROOT / "Prompts/modules").glob("*.md"))
    thin_mods = min_depth(modules, MODULE_MIN_BYTES, "module")
    warns.extend(thin_mods)
    score_parts["modules"] = max(0, 10 - len(thin_mods))

    # Skills depth (10)
    skills = sorted((ROOT / ".cursor/skills").glob("sentinel-*/SKILL.md"))
    thin_skills = min_depth(skills, SKILL_MIN_BYTES, "skill")
    warns.extend(thin_skills)
    if len(skills) < 3:
        errors.append(f"expected ≥3 sentinel skills, found {len(skills)}")
    score_parts["skills"] = max(0, 10 - 2 * len(thin_skills) - (3 if len(skills) < 3 else 0))

    # Execution prompts (5)
    execs = sorted((ROOT / "Prompts/Execution").glob("0*.md"))
    thin_exec = min_depth(execs, EXEC_PROMPT_MIN_BYTES, "execution prompt")
    warns.extend(thin_exec)
    score_parts["execution"] = max(0, 5 - len(thin_exec))

    # Learning closed loop (15)
    patterns = list((ROOT / "knowledge/patterns").glob("P-*.md"))
    failures = list((ROOT / "knowledge/failures").glob("F-*.json"))
    index = ROOT / "knowledge/patterns/INDEX.md"
    learn = 15
    if not index.is_file():
        errors.append("missing knowledge/patterns/INDEX.md")
        learn -= 5
    if len(patterns) < 5:
        warns.append(f"few pattern files: {len(patterns)}")
        learn -= 3
    if len(failures) < 1:
        warns.append("no failure catalog JSON records")
        learn -= 4
    if not (ROOT / "automation/promote_learning.py").is_file():
        learn -= 3
    score_parts["learning"] = max(0, learn)

    # Tests / CI (10)
    tests = list((ROOT / "repo_tests").glob("test_*.py"))
    ci = ROOT / "ci_checks" / "run_framework_checks.sh"
    test_score = 0
    if tests:
        test_score += min(7, 2 * len(tests))
    else:
        warns.append("no repo_tests/test_*.py")
    if ci.is_file():
        test_score += 3
    else:
        warns.append("missing ci_checks/run_framework_checks.sh")
    score_parts["tests_ci"] = min(10, test_score)

    # Lib modularization (optional progress) — up to 5 bonus toward maintainability bucket
    lib_py = [p for p in (ROOT / "automation/lib").glob("*.py") if p.name != "__init__.py"]
    if not lib_py:
        warns.append("automation/lib has no modules yet (Phase 2)")
        score_parts["lib"] = 0
    else:
        score_parts["lib"] = min(5, len(lib_py))

    total = sum(score_parts.values())
    # normalize: max = 20+15+15+10+10+5+15+10+5 = 105 → cap 100
    total = min(100, total)

    print("SENTINEL DOCTOR")
    print(f"  root: {ROOT}")
    print("  score_parts:")
    for k, v in score_parts.items():
        print(f"    {k}: {v}")
    if errors:
        print("  FAILED:")
        for e in errors:
            print(f"    - {e}")
    else:
        print("  OK: critical layout/imports present")
    if warns:
        print("  WARNINGS:")
        for w in warns:
            print(f"    - {w}")
    print(f"  health_score: {total}/100")
    print("  note: score reflects framework depth; 100 requires lib modules + tests + CI")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
