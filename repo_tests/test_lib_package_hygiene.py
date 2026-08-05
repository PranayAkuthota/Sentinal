"""Lib package + hygiene helpers."""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation"))

from lib.hygiene import ensure_network_blocks_in_task_toml  # noqa: E402
from lib.package import package_flat_task_zip, verify_corrected_zip  # noqa: E402
from lib.sync import check_instruction_sync  # noqa: E402


class LibPackageHygieneTests(unittest.TestCase):
    def test_instruction_sync(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "environment").mkdir()
            (root / "instruction.md").write_text("hello\n", encoding="utf-8")
            (root / "environment" / "problem_statement.md").write_text("hello\n", encoding="utf-8")
            ok, msg = check_instruction_sync(root)
            self.assertTrue(ok, msg)
            (root / "environment" / "problem_statement.md").write_text("other\n", encoding="utf-8")
            ok, msg = check_instruction_sync(root)
            self.assertFalse(ok)

    def test_ensure_network_blocks_creates_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "task.toml").write_text('schema_version = "1.3"\ncpus = 2\n', encoding="utf-8")
            changed, msg = ensure_network_blocks_in_task_toml(root)
            self.assertTrue(changed, msg)
            text = (root / "task.toml").read_text(encoding="utf-8")
            self.assertIn('network_mode = "public"', text)
            self.assertIn('allowed_hosts = ["api.portkey.ai"]', text)
            self.assertIn('network_mode = "no-network"', text)

    def test_package_and_verify(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "taskroot"
            for name in ("environment", "solution", "tests"):
                (root / name).mkdir(parents=True)
            (root / "instruction.md").write_text("i\n", encoding="utf-8")
            (root / "task.toml").write_text("x=1\n", encoding="utf-8")
            (root / "environment" / "Dockerfile").write_text("FROM x\n", encoding="utf-8")
            (root / "solution" / "solve.sh").write_text("#!/bin/bash\n", encoding="utf-8")
            (root / "tests" / "test.sh").write_text("#!/bin/bash\n", encoding="utf-8")
            (root / "runs").mkdir()
            (root / "runs" / "x.txt").write_text("nope\n", encoding="utf-8")
            dest = base / "out.zip"
            written = package_flat_task_zip(root, dest)
            self.assertIn("instruction.md", written)
            self.assertFalse(any(w.startswith("runs") for w in written))
            ok, errors = verify_corrected_zip(dest)
            self.assertTrue(ok, errors)
            with zipfile.ZipFile(dest) as zf:
                names = zf.namelist()
                self.assertIn("instruction.md", names)
                self.assertFalse(any(n.startswith("runs/") for n in names))

    def test_empty_git_refs_survive_packaging(self):
        """zip -rX keeps empty .git/refs/heads; Python zipfile must match."""
        import subprocess

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "taskroot"
            for name in ("environment/repo/.git/refs/heads", "solution", "tests"):
                (root / name).mkdir(parents=True)
            (root / "instruction.md").write_text("i\n", encoding="utf-8")
            (root / "task.toml").write_text("x=1\n", encoding="utf-8")
            (root / "environment" / "Dockerfile").write_text("FROM x\n", encoding="utf-8")
            (root / "environment" / "repo" / ".git" / "HEAD").write_text(
                "ref: refs/heads/main\n", encoding="utf-8"
            )
            (root / "solution" / "solve.sh").write_text("#!/bin/bash\n", encoding="utf-8")
            (root / "tests" / "test.sh").write_text("#!/bin/bash\n", encoding="utf-8")
            # empty dirs: refs/ and refs/heads/ (no files inside heads)
            dest = base / "out.zip"
            package_flat_task_zip(root, dest)
            ok, errors = verify_corrected_zip(dest)
            self.assertTrue(ok, errors)
            listing = subprocess.check_output(["unzip", "-l", str(dest)], text=True)
            self.assertIn("refs/", listing)
            with zipfile.ZipFile(dest) as zf:
                names = zf.namelist()
                self.assertTrue(
                    any("refs/" in n for n in names),
                    f"refs/ missing from {names}",
                )
                self.assertTrue(
                    any(n.rstrip("/").endswith("refs/heads") or "refs/heads/" in n for n in names),
                    f"refs/heads missing from {names}",
                )


if __name__ == "__main__":
    unittest.main()
