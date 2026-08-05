#!/usr/bin/env python3
"""In-container f2p grader used by local_oracle_nop.py (mounted read-only)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def main() -> None:
    mode = os.environ.get("SENTINEL_VAL_MODE", "oracle")
    tests = json.loads(os.environ["SENTINEL_F2P_JSON"])
    Path("/logs/verifier").mkdir(parents=True, exist_ok=True)
    p = subprocess.run(
        ["python3", "-m", "pytest", "-q", "--tb=line", *tests],
        capture_output=True,
        text=True,
    )
    Path("/logs/verifier/test-stdout.txt").write_text(p.stdout or "", encoding="utf-8")
    err_path = Path("/logs/verifier/test-stderr.txt")
    prev = err_path.read_text(encoding="utf-8") if err_path.exists() else ""
    err_path.write_text(prev + (p.stderr or ""), encoding="utf-8")
    out = (p.stdout or "") + "\n" + (p.stderr or "")

    passed = 0
    for t in tests:
        short = t.split("::")[-1].split("[")[0]
        if re.search(rf"{re.escape(short)}\s+PASSED", out):
            passed += 1

    m = re.search(r"(\d+)\s+passed", out)
    summary_passed = int(m.group(1)) if m else -1
    has_failed = bool(re.search(r"\d+\s+failed", out)) or "FAILED" in out
    all_ok = (summary_passed == len(tests) and not has_failed) or (passed == len(tests) and not has_failed)

    if mode == "oracle":
        reward = 1.0 if all_ok else 0.0
    else:
        reward = 0.0 if not all_ok else 1.0

    Path("/logs/verifier/reward.txt").write_text(str(reward), encoding="utf-8")
    Path("/logs/verifier/report.json").write_text(
        json.dumps(
            {
                "mode": mode,
                "passed_detected": passed,
                "summary_passed": summary_passed,
                "total": len(tests),
                "returncode": p.returncode,
                "reward": reward,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    sys.stdout.write(out[-4000:])
    sys.stdout.write(f"\nREWARD {reward} passed_detected {passed}/{len(tests)} summary_passed={summary_passed}\n")


if __name__ == "__main__":
    main()
