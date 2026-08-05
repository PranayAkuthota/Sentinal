"""Execution prompts must only cite real sentinel_submitter subcommands / automation scripts."""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXEC = ROOT / "Prompts" / "Execution"
AUTOMATION = ROOT / "automation"


def _submitter_subcommands() -> set[str]:
    help_out = subprocess.check_output(
        [sys.executable, str(AUTOMATION / "sentinel_submitter.py"), "--help"],
        text=True,
    )
    m = re.search(r"\{([^}]+)\}", help_out)
    assert m, help_out
    return {x.strip() for x in m.group(1).split(",")}


def _automation_scripts() -> set[str]:
    return {p.name for p in AUTOMATION.glob("*.py")}


class ExecutionPromptCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.subcmds = _submitter_subcommands()
        cls.scripts = _automation_scripts()

    def test_execution_files_exist_01_through_07(self):
        for stem in (
            "01_boot_and_structural_audit",
            "02_source_and_instruction",
            "03_spec_alignment",
            "04_tri_field_verdict",
            "05_branch_fix_and_validate",
            "06_answers_package_and_learn",
            "07_platform_revision",
            "README",
        ):
            path = EXEC / f"{stem}.md"
            self.assertTrue(path.is_file(), f"missing {path}")

    def test_cited_submitter_subcommands_exist(self):
        pat = re.compile(r"sentinel_submitter\.py\s+([a-z0-9\-]+)")
        unknown: list[str] = []
        for path in sorted(EXEC.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for m in pat.finditer(text):
                sub = m.group(1)
                if sub not in self.subcmds:
                    unknown.append(f"{path.name}: `{sub}`")
        self.assertEqual(unknown, [], unknown)

    def test_cited_automation_scripts_exist(self):
        pat = re.compile(r"(?:python3\s+)?automation/([A-Za-z0-9_]+\.py)")
        unknown: list[str] = []
        for path in sorted(EXEC.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for m in pat.finditer(text):
                name = m.group(1)
                if name not in self.scripts:
                    unknown.append(f"{path.name}: automation/{name}")
        self.assertEqual(unknown, [], unknown)

    def test_checkpoint_ready_accepts_07(self):
        help_out = subprocess.check_output(
            [sys.executable, str(AUTOMATION / "checkpoint_ready.py"), "--help"],
            text=True,
        )
        self.assertIn("01..07", help_out)
        self.assertIn("resume-revision", help_out)


class CheckpointReady07Tests(unittest.TestCase):
    def test_required_priors_07_is_06_only(self):
        path = AUTOMATION / "checkpoint_ready.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        # load via importlib for live map
        import importlib.util

        spec = importlib.util.spec_from_file_location("checkpoint_ready", path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.REQUIRED_PRIORS["07"], ["06"])
        self.assertIn("07", mod.REQUIRED_PRIORS)


if __name__ == "__main__":
    unittest.main()
