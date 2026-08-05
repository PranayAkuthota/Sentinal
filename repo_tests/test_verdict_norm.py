"""Verdict normalization helpers must stay stable."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    lib = ROOT / "automation" / "lib" / "verdicts.py"
    path = lib if lib.is_file() else ROOT / "automation" / "sentinel_submitter.py"
    spec = importlib.util.spec_from_file_location("verdict_mod", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class VerdictNormTests(unittest.TestCase):
    def test_norm_analysis_aliases(self):
        m = _load()
        self.assertEqual(m.norm_analysis("Valid as-is"), "Valid-as-is")
        self.assertEqual(m.norm_analysis("Valid-as-is"), "Valid-as-is")
        self.assertEqual(m.norm_analysis("Fixable"), "Fixable")
        self.assertEqual(m.norm_analysis("Invalid/Not Fixable"), "Invalid/Not Fixable")
        self.assertEqual(m.norm_analysis("Invalid-Not Fixable"), "Invalid/Not Fixable")

    def test_public_matches_duplicate(self):
        m = _load()
        self.assertTrue(m.public_matches_duplicate("Valid as-is", "Valid-as-is"))
        self.assertTrue(m.public_matches_duplicate("Fixable", "Fixable"))
        self.assertFalse(m.public_matches_duplicate("Fixable", "Valid as-is"))


if __name__ == "__main__":
    unittest.main()
