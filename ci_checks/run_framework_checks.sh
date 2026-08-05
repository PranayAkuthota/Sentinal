#!/usr/bin/env bash
# Sentinel framework CI — doctor + repo_tests. Never runs task verdicts.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== sentinel_doctor =="
python3 automation/sentinel_doctor.py

echo "== repo_tests =="
if python3 -c "import pytest" 2>/dev/null; then
  python3 -m pytest repo_tests/ -q
else
  python3 ci_checks/run_unittest_suite.py
fi

echo "== framework checks OK =="
