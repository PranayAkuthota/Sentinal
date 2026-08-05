"""checkpoint_ready prior map and status parsing."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "automation" / "checkpoint_ready.py"
    spec = importlib.util.spec_from_file_location("checkpoint_ready", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CheckpointReadyTests(unittest.TestCase):
    def test_required_priors_chain(self):
        m = _load()
        self.assertEqual(m.REQUIRED_PRIORS["01"], [])
        self.assertEqual(m.REQUIRED_PRIORS["04"], ["01", "02", "03"])
        self.assertIn("04", m.REQUIRED_PRIORS["05"])
        self.assertIn("05", m.REQUIRED_PRIORS["06"])

    def test_parse_status(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "01__handoff.md"
            p.write_text(
                "# 01 handoff\n\ntask_name: sample\nstatus: complete\n\n"
                "key findings:\n- intake ok\n\nnext_checkpoint: 02\n",
                encoding="utf-8",
            )
            ok, msg = m.check_handoff(p)
            self.assertTrue(ok, msg)
            p.write_text(
                "# 01 handoff\n\ntask_name: sample\nstatus: blocked\n\n"
                "key findings:\n- zip corrupt\n\nnext_checkpoint: 01\n",
                encoding="utf-8",
            )
            ok, msg = m.check_handoff(p)
            self.assertFalse(ok)
            self.assertIn("blocked", msg)


if __name__ == "__main__":
    unittest.main()
