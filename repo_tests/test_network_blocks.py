"""Harbor network-block hygiene and agent.timeout_sec limits (29 Jul 2026)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation"))

from lib.hygiene import (  # noqa: E402
    ensure_network_blocks_in_task_toml,
    strip_compose_network_none,
    validate_network_blocks,
)
from lib.toml_util import parse_task_toml_simple  # noqa: E402

# Import metadata_limits_report from the submitter module
sys.path.insert(0, str(ROOT))
from automation.sentinel_submitter import metadata_limits_report  # noqa: E402


CORRECT_TOML = """\
schema_version = "1.3"

# keep this comment
[environment]
os = "linux"
cpus = 2
network_mode = "public"

[agent]
timeout_sec = 1800
network_mode = "allowlist"
allowed_hosts = ["api.portkey.ai"]

[verifier]
timeout_sec = 300
network_mode = "no-network"
"""


class NetworkBlocksTests(unittest.TestCase):
    def test_missing_block_created(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "task.toml").write_text(
                'schema_version = "1.3"\n[environment]\ncpus = 2\n',
                encoding="utf-8",
            )
            changed, msg = ensure_network_blocks_in_task_toml(root)
            self.assertTrue(changed, msg)
            text = (root / "task.toml").read_text(encoding="utf-8")
            self.assertIn("[agent]", text)
            self.assertIn("[verifier]", text)
            self.assertIn('network_mode = "public"', text)
            self.assertIn('network_mode = "allowlist"', text)
            self.assertIn('allowed_hosts = ["api.portkey.ai"]', text)
            self.assertIn('network_mode = "no-network"', text)
            ok, problems = validate_network_blocks(root)
            self.assertTrue(ok, problems)

    def test_wrong_value_corrected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "task.toml").write_text(
                "[environment]\n"
                'network_mode = "bridge"\n'
                "[agent]\n"
                'network_mode = "public"\n'
                'allowed_hosts = ["evil.example"]\n'
                "[verifier]\n"
                'network_mode = "public"\n',
                encoding="utf-8",
            )
            changed, msg = ensure_network_blocks_in_task_toml(root)
            self.assertTrue(changed, msg)
            text = (root / "task.toml").read_text(encoding="utf-8")
            self.assertIn('network_mode = "public"', text)
            self.assertIn('network_mode = "allowlist"', text)
            self.assertIn('allowed_hosts = ["api.portkey.ai"]', text)
            self.assertIn('network_mode = "no-network"', text)
            self.assertNotIn("bridge", text)
            self.assertNotIn("evil.example", text)

    def test_already_correct_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "task.toml").write_text(CORRECT_TOML, encoding="utf-8")
            before = (root / "task.toml").read_text(encoding="utf-8")
            changed, msg = ensure_network_blocks_in_task_toml(root)
            self.assertFalse(changed, msg)
            after = (root / "task.toml").read_text(encoding="utf-8")
            self.assertEqual(before, after)
            changed2, _ = ensure_network_blocks_in_task_toml(root)
            self.assertFalse(changed2)
            self.assertEqual(before, (root / "task.toml").read_text(encoding="utf-8"))

    def test_comment_preservation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "task.toml").write_text(
                "# top comment stays\n"
                "[environment]\n"
                "# env note\n"
                "cpus = 2\n"
                'network_mode = "bridge"\n',
                encoding="utf-8",
            )
            ensure_network_blocks_in_task_toml(root)
            text = (root / "task.toml").read_text(encoding="utf-8")
            self.assertIn("# top comment stays", text)
            self.assertIn("# env note", text)
            self.assertIn("cpus = 2", text)

    def test_strip_compose_network_none(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = root / "environment"
            env.mkdir()
            compose = env / "docker_compose.yaml"
            compose.write_text(
                "services:\n"
                "  main:\n"
                '    network_mode: "none"\n'
                "    image: foo\n",
                encoding="utf-8",
            )
            changed, msg = strip_compose_network_none(root)
            self.assertTrue(changed, msg)
            text = compose.read_text(encoding="utf-8")
            self.assertNotIn("none", text)
            self.assertIn("image: foo", text)
            changed2, _ = strip_compose_network_none(root)
            self.assertFalse(changed2)

    def test_agent_timeout_7200_accepted_7201_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "environment").mkdir()
            (root / "environment" / "Dockerfile").write_text(
                "FROM python:3.11-slim-bookworm\n", encoding="utf-8"
            )
            (root / "task.toml").write_text(
                CORRECT_TOML.replace("timeout_sec = 1800", "timeout_sec = 7200", 1),
                encoding="utf-8",
            )
            report = metadata_limits_report(root)
            self.assertTrue(report["ok"], report.get("errors"))
            errs = " ".join(report.get("errors") or [])
            self.assertNotIn("agent_timeout_sec", errs)

            (root / "task.toml").write_text(
                CORRECT_TOML.replace("timeout_sec = 1800", "timeout_sec = 7201", 1),
                encoding="utf-8",
            )
            report2 = metadata_limits_report(root)
            self.assertFalse(report2["ok"])
            self.assertTrue(
                any("agent_timeout_sec" in e and "7201" in e and "7200" in e for e in report2["errors"]),
                report2["errors"],
            )

    def test_parse_still_sees_section_keys(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "task.toml").write_text(CORRECT_TOML, encoding="utf-8")
            data = parse_task_toml_simple(root / "task.toml")
            self.assertEqual(data.get("agent.network_mode"), "allowlist")
            self.assertEqual(data.get("environment.network_mode"), "public")

    def test_metadata_warns_on_missing_not_on_present(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "environment").mkdir()
            (root / "environment" / "Dockerfile").write_text(
                "FROM python:3.11-slim-bookworm\n", encoding="utf-8"
            )
            (root / "task.toml").write_text(CORRECT_TOML, encoding="utf-8")
            good = metadata_limits_report(root)
            self.assertTrue(good["network_blocks_ok"])
            self.assertEqual(good["network_blocks_issues"], [])
            self.assertFalse(
                any("present" in w and "network" in w for w in good.get("warnings") or [])
            )

            (root / "task.toml").write_text('schema_version = "1.3"\ncpus = 2\n', encoding="utf-8")
            bad = metadata_limits_report(root)
            self.assertFalse(bad["network_blocks_ok"])
            self.assertTrue(bad["network_blocks_issues"])
            self.assertTrue(
                any("network block missing/wrong" in w for w in bad.get("warnings") or [])
            )

    def test_normalize_legacy_audit_metadata(self):
        from automation.sentinel_submitter import normalize_audit_metadata

        legacy_absent = normalize_audit_metadata(
            {"network_mode_present": False, "allowed_hosts_present": False}
        )
        self.assertFalse(legacy_absent["network_blocks_ok"])
        self.assertTrue(any("absent" in i for i in legacy_absent["network_blocks_issues"]))

        modern = normalize_audit_metadata(
            {"network_blocks_ok": True, "network_blocks_issues": []}
        )
        self.assertTrue(modern["network_blocks_ok"])
        self.assertEqual(modern["network_blocks_issues"], [])


if __name__ == "__main__":
    unittest.main()
