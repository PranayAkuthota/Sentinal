#!/usr/bin/env python3
"""Local Docker oracle / NOP validation helper for Harbor-format Sentinel tasks.

Does NOT decide verdicts. Does NOT package ZIPs.
Writes evidence under work/<task>/session/validation_logs/{oracle,nop}/.

  python3 automation/local_oracle_nop.py --task-name <task> --mode both
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
GRADE_HELPER = SCRIPT_DIR / "docker_grade_f2p.py"


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_f2p(task_root: Path) -> List[str]:
    cfg = json.loads((task_root / "tests" / "config.json").read_text(encoding="utf-8"))
    grading = cfg.get("grading") or {}
    f2p = grading.get("fail_to_pass") or cfg.get("fail_to_pass") or []
    if not isinstance(f2p, list) or not f2p:
        die("no fail_to_pass tests in tests/config.json")
    return [str(x) for x in f2p]


def docker_build(task_root: Path, image: str, log_path: Path) -> None:
    env_dir = task_root / "environment"
    if not (env_dir / "Dockerfile").exists():
        die(f"missing Dockerfile under {env_dir}")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        p = subprocess.run(
            ["docker", "build", "-t", image, "."],
            cwd=str(env_dir),
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    if p.returncode != 0:
        die(f"docker build failed — see {log_path}")
    print(f"BUILD OK → {image}")


def run_mode(*, task_root: Path, image: str, mode: str, out_dir: Path, f2p: List[str]) -> float:
    assert mode in {"oracle", "nop"}
    if not GRADE_HELPER.exists():
        die(f"missing helper {GRADE_HELPER}")
    out_dir.mkdir(parents=True, exist_ok=True)
    inner = f"""
set -uo pipefail
cd /app
mkdir -p /logs/verifier
: > /logs/verifier/test-stderr.txt
if [ {mode!r} = oracle ]; then
  bash /solution/solve.sh
fi
if ! git apply /tests/tests.patch 2>>/logs/verifier/test-stderr.txt; then
  if ! git apply --3way /tests/tests.patch 2>>/logs/verifier/test-stderr.txt; then
    patch -p1 --forward < /tests/tests.patch >>/logs/verifier/test-stderr.txt 2>&1 || true
  fi
fi
export SENTINEL_VAL_MODE={mode}
export SENTINEL_F2P_JSON={json.dumps(json.dumps(f2p))}
python3 /sentinel_helpers/docker_grade_f2p.py
"""
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{task_root / 'solution'}:/solution:ro",
        "-v",
        f"{task_root / 'tests'}:/tests:ro",
        "-v",
        f"{SCRIPT_DIR}:/sentinel_helpers:ro",
        "-v",
        f"{out_dir}:/logs/verifier",
        image,
        "bash",
        "-lc",
        inner,
    ]
    run_log = out_dir.parent / f"{mode}_run.log"
    with run_log.open("w", encoding="utf-8") as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    reward_path = out_dir / "reward.txt"
    if not reward_path.exists():
        die(f"{mode}: reward.txt missing — see {run_log}")
    reward = float(reward_path.read_text(encoding="utf-8").strip())
    print(f"{mode.upper()} reward={reward} (log: {run_log})")
    return reward


def resolve_task_root(args: argparse.Namespace) -> Tuple[Path, Path]:
    if args.task_root:
        root = Path(args.task_root).resolve()
        logs = root.parent / "session" / "validation_logs"
        if root.name == "working_copy":
            logs = root.parent / "session" / "validation_logs"
        return root, logs
    if not args.task_name:
        die("provide --task-name or --task-root")
    work = WORKSPACE_ROOT / "work" / args.task_name
    wc = work / "working_copy"
    if wc.exists():
        return wc.resolve(), work / "session" / "validation_logs"
    eo = work / "extracted_original"
    if eo.exists():
        return eo.resolve(), work / "session" / "validation_logs"
    die(f"no working_copy or extracted_original under {work}")


def main(argv: Optional[list] = None) -> None:
    p = argparse.ArgumentParser(description="Local Harbor oracle/NOP Docker validation (no auto-verdicts)")
    p.add_argument("--task-name")
    p.add_argument("--task-root")
    p.add_argument("--mode", choices=["oracle", "nop", "both", "build-only"], default="both")
    p.add_argument("--image", default=None)
    p.add_argument("--skip-build", action="store_true")
    args = p.parse_args(argv)

    task_root, logs = resolve_task_root(args)
    if not (task_root / "instruction.md").exists():
        die(f"not a task root: {task_root}")
    image = args.image or f"sentinel-local-{(args.task_name or task_root.parent.name).lower().replace('_', '-')[:48]}"

    d = subprocess.run(["docker", "info"], capture_output=True, text=True)
    if d.returncode != 0:
        die("Docker daemon not available. Start Docker Desktop / engine, then retry.")

    logs.mkdir(parents=True, exist_ok=True)
    if not args.skip_build:
        docker_build(task_root, image, logs / "docker_build.log")
    if args.mode == "build-only":
        return

    f2p = load_f2p(task_root)
    print(f"f2p count: {len(f2p)}")
    print(f"task_root: {task_root}")
    print(f"logs: {logs}")

    if args.mode in {"oracle", "both"}:
        r = run_mode(task_root=task_root, image=image, mode="oracle", out_dir=logs / "oracle", f2p=f2p)
        if r != 1.0:
            print("ORACLE DID NOT REACH 1.0 — do not claim ready packaging without fix", file=sys.stderr)
    if args.mode in {"nop", "both"}:
        r = run_mode(task_root=task_root, image=image, mode="nop", out_dir=logs / "nop", f2p=f2p)
        if r != 0.0:
            print("NOP DID NOT STAY 0.0 — suite may be vacuous or pre-solved", file=sys.stderr)

    tn = args.task_name or "TASK"
    print("DONE — record evidence with:")
    print(
        f"  python3 automation/sentinel_submitter.py record-validation --task-name {tn} "
        f"--check docker_build --status passed --evidence {logs / 'docker_build.log'}"
    )
    print(
        f"  python3 automation/sentinel_submitter.py record-validation --task-name {tn} "
        f"--check oracle --status passed --evidence {logs / 'oracle' / 'reward.txt'} --reward 1.0"
    )
    print(
        f"  python3 automation/sentinel_submitter.py record-validation --task-name {tn} "
        f"--check nop --status passed --evidence {logs / 'nop' / 'reward.txt'} --reward 0.0"
    )


if __name__ == "__main__":
    main()
