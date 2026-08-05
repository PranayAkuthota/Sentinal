"""Doctor should import and report a numeric score."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DoctorTests(unittest.TestCase):
    def test_doctor_runs(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "automation" / "sentinel_doctor.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertIn("health_score:", proc.stdout)
        self.assertIn(proc.returncode, (0, 1))


if __name__ == "__main__":
    unittest.main()
