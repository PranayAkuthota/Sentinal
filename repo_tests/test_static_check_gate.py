"""static-check gate: FIXABLE blocks packaging; ADVISORY warns; PH1 still blocks."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "automation"))

from automation import sentinel_submitter as ss  # noqa: E402


def _write_minimal_task(root: Path) -> None:
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "environment" / "repo").mkdir(parents=True, exist_ok=True)
    (root / "solution").mkdir(parents=True, exist_ok=True)
    # Healthy empty-ish patch (no hunks) — still a file for analyzer
    (root / "tests" / "tests.patch").write_text(
        "diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -0,0 +1,1 @@\n+ok\n",
        encoding="utf-8",
    )


def _fake_check_task(findings: list[dict]):
    """Replace subprocess.run so check_task 'writes' our findings JSON."""

    def _run(cmd, capture_output=True, text=True):  # noqa: ANN001
        # cmd: python check_task.py root --json OUT --md OUT
        json_out = Path(cmd[cmd.index("--json") + 1])
        md_out = Path(cmd[cmd.index("--md") + 1])
        payload = {"findings": findings, "verdict_hint": "TEST"}
        json_out.write_text(json.dumps(payload), encoding="utf-8")
        md_out.write_text("# mock\n", encoding="utf-8")
        # exit 1 if any FIXABLE/NOT_FIXABLE like real check_task
        code = (
            1
            if any(f.get("severity") in ("FIXABLE", "NOT_FIXABLE") for f in findings)
            else 0
        )
        return mock.Mock(returncode=code, stdout="mock", stderr="")

    return _run


def _preflight_gate_from_static(sc: dict) -> tuple[list[str], list[str], bool]:
    """Mirror preflight's static-check → blockers/warnings → ready_to_package signal."""
    blockers: list[str] = []
    warnings: list[str] = []
    for fid in sc["fixable_ids"]:
        blockers.append(f"static-check FIXABLE open: {fid}")
    for fid in sc["not_fixable_ids"]:
        blockers.append(f"static-check NOT_FIXABLE open: {fid}")
    for fid in sc["advisory_ids"]:
        warnings.append(f"static-check ADVISORY: {fid}")
    ready = len(blockers) == 0
    return blockers, warnings, ready


class StaticCheckGateTests(unittest.TestCase):
    def test_fixable_blocks_ready_to_package(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_minimal_task(root)
            findings = [
                {
                    "id": "T3",
                    "severity": "FIXABLE",
                    "category": "Environment",
                    "where": "task.toml",
                    "summary": "network_mode wrong",
                    "evidence": "",
                    "rule": "test",
                    "fix": "fix",
                }
            ]
            with mock.patch("automation.sentinel_submitter.subprocess.run", side_effect=_fake_check_task(findings)):
                # Also stub patch health as clean
                with mock.patch(
                    "automation.sentinel_submitter.analyze_tests_patch_health",
                    return_value={
                        "ok": True,
                        "hunk_mismatches": [],
                        "git_apply_check": True,
                        "patch_dry_run": True,
                        "errors": [],
                        "warnings": [],
                    },
                ):
                    sc = ss.run_static_check(
                        root, root / "out.json", root / "out.md"
                    )
            self.assertFalse(sc["ok"])
            self.assertIn("T3", sc["fixable_ids"])
            blockers, warnings, ready = _preflight_gate_from_static(sc)
            self.assertTrue(any("FIXABLE open: T3" in b for b in blockers))
            self.assertFalse(ready)
            self.assertEqual(warnings, [])

    def test_advisory_only_warns(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_minimal_task(root)
            findings = [
                {
                    "id": "T12",
                    "severity": "ADVISORY",
                    "category": "Environment",
                    "where": "task.toml",
                    "summary": "difficulty_explanation missing",
                    "evidence": "",
                    "rule": "test",
                    "fix": "fix",
                }
            ]
            with mock.patch("automation.sentinel_submitter.subprocess.run", side_effect=_fake_check_task(findings)):
                with mock.patch(
                    "automation.sentinel_submitter.analyze_tests_patch_health",
                    return_value={
                        "ok": True,
                        "hunk_mismatches": [],
                        "git_apply_check": True,
                        "patch_dry_run": True,
                        "errors": [],
                        "warnings": [],
                    },
                ):
                    sc = ss.run_static_check(
                        root, root / "out.json", root / "out.md"
                    )
            self.assertTrue(sc["ok"], sc)
            self.assertEqual(sc["fixable_ids"], [])
            self.assertIn("T12", sc["advisory_ids"])
            blockers, warnings, ready = _preflight_gate_from_static(sc)
            self.assertEqual(blockers, [])
            self.assertTrue(ready)
            self.assertTrue(any("ADVISORY: T12" in w for w in warnings))

    def test_ph1_from_patch_health_still_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_minimal_task(root)
            # check_task itself clean
            findings: list[dict] = []
            with mock.patch("automation.sentinel_submitter.subprocess.run", side_effect=_fake_check_task(findings)):
                with mock.patch(
                    "automation.sentinel_submitter.analyze_tests_patch_health",
                    return_value={
                        "ok": False,
                        "hunk_mismatches": [{"line": 1, "header_old": 1, "header_new": 1, "actual_old": 0, "actual_new": 0}],
                        "git_apply_check": False,
                        "patch_dry_run": True,
                        "errors": ["mismatch"],
                        "warnings": [],
                        "apply_detail": "hunk mismatch",
                    },
                ):
                    sc = ss.run_static_check(
                        root, root / "out.json", root / "out.md"
                    )
            self.assertIn("PH1", sc["fixable_ids"])
            self.assertFalse(sc["ok"])
            # Confirm analyzer still invoked (result attached)
            self.assertIn("tests_patch_health", sc)
            self.assertTrue(sc["tests_patch_health"]["hunk_mismatches"])
            blockers, warnings, ready = _preflight_gate_from_static(sc)
            self.assertTrue(any("FIXABLE open: PH1" in b for b in blockers))
            self.assertFalse(ready)

    def test_analyze_tests_patch_health_still_callable(self):
        """PH1 path depends on the main-pipeline analyzer remaining wired."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_minimal_task(root)
            # Corrupt hunk counts deliberately
            (root / "tests" / "tests.patch").write_text(
                "diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1,5 +1,5 @@\n+only one line\n",
                encoding="utf-8",
            )
            report = ss.analyze_tests_patch_health(root)
            self.assertTrue(report.get("hunk_mismatches"), report)


if __name__ == "__main__":
    unittest.main()
