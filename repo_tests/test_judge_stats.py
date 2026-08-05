"""judge_stats retrospective vs live recall; precision suppressed for retrospective."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation"))

import judge_stats as js  # noqa: E402


class JudgeStatsRetrospectiveTests(unittest.TestCase):
    def test_eb599_style_artifact_recall_and_precision_note(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fb_dir = root / "knowledge" / "judge_feedback"
            pred_dir = fb_dir / "predictions"
            pred_dir.mkdir(parents=True)
            task = "eb_sample"
            pred = {
                "source": "retrospective backtest",
                "predicted_verdict": "REMOVE",
                "confirmed_overreach": ["A6"],
                "confirmed_overreach_detail": [
                    {"id": "A6", "artifacts": ["CellMap", "out_shape"], "assertion_text": "cell_map.out_shape"}
                ],
                "confirmed_gaps": ["R19"],
                "confirmed_gap_detail": [
                    {"id": "R19", "artifacts": ["ValueError"], "text": "ValueError"}
                ],
                "packaging_hard_cap": True,
                "packaging_artifacts": [".python-version"],
            }
            (pred_dir / f"{task}.json").write_text(json.dumps(pred), encoding="utf-8")
            fb = {
                "schema_version": 2,
                "task_name": task,
                "verdict": "REMOVE",
                "verdict_reason": "overreach",
                "axes": {"adjudicated": {}, "per_judge": None},
                "citations": [
                    {"file": None, "line_range": None, "quoted_text": "CellMap public attrs", "axis": "test_faithfulness"},
                    {"file": None, "line_range": None, "quoted_text": "atypical path suffix vs decode", "axis": "test_faithfulness"},
                    {"file": None, "line_range": None, "quoted_text": "ValueError match", "axis": "test_faithfulness"},
                    {"file": None, "line_range": None, "quoted_text": ".python-version hard-cap", "axis": "packaging"},
                ],
                "must_haves_failed": None,
                "difficulty_run": None,
                "fixes_applied": [],
                "next_round_result": None,
                "prediction_ref": f"knowledge/judge_feedback/predictions/{task}.json",
                "source": "backfilled from task_outputs",
            }
            (fb_dir / f"{task}.json").write_text(json.dumps(fb), encoding="utf-8")

            # Point ROOT at temp tree
            old = js.ROOT
            try:
                js.ROOT = root
                rows = js.load_feedback_rows(fb_dir)
                self.assertEqual(len(rows), 1)
                self.assertTrue(rows[0]["retrospective"])
                m = rows[0]["match"]
                self.assertEqual(m["n_matched"], 3)
                self.assertEqual(m["n_cited"], 4)
                text = js.report(rows)
                self.assertIn("Precision suppressed", text)
                self.assertIn("Retrospective joins", text)
                self.assertIn("unmatched", text.lower())
                self.assertIn("path suffix", text)
            finally:
                js.ROOT = old


if __name__ == "__main__":
    unittest.main()
