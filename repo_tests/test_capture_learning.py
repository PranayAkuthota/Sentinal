"""capture_learning must never emit (edit) placeholders."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation"))

import capture_learning as cl  # noqa: E402


class CaptureLearningNoPlaceholderTests(unittest.TestCase):
    def test_empty_state_writes_no_new_pattern_without_edit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            task = "sample_task_for_learning"
            outputs = root / "task_outputs" / task
            outputs.mkdir(parents=True)
            (outputs / "workflow_state.json").write_text("{}\n", encoding="utf-8")

            with mock.patch.object(cl, "ROOT", root), mock.patch.object(
                cl, "PROPOSALS", root / "knowledge" / "proposals"
            ), mock.patch.object(cl, "FEEDBACK_DIR", root / "knowledge" / "judge_feedback"):
                body, has = cl.build_proposal_text(task, notes="")
                self.assertFalse(has)
                self.assertIn("no new pattern", body)
                self.assertNotIn("(edit)", body)
                cl.assert_no_placeholders(body)

    def test_feedback_axes_produce_real_candidates_without_edit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            task = "sample_with_feedback"
            outputs = root / "task_outputs" / task
            outputs.mkdir(parents=True)
            (outputs / "workflow_state.json").write_text(
                json.dumps(
                    {
                        "duplicate_analysis": "Fixable",
                        "fail_to_pass_count": 12,
                        "oracle_status": "passed",
                        "oracle_reward": 1.0,
                        "nop_status": "passed",
                        "nop_reward": 0.0,
                        "ready_to_package": True,
                        "judge_prep_accept_risk": True,
                        "judge_prep_accept_risk_reason": "V6 necessary PR test migration",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            fb_dir = root / "knowledge" / "judge_feedback"
            fb_dir.mkdir(parents=True)
            (fb_dir / f"{task}.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "task_name": task,
                        "verdict": "DISCUSS",
                        "verdict_reason": "weak_check",
                        "axes": {
                            "adjudicated": {"prescriptiveness": 2.5, "test_coverage": 3.0},
                            "per_judge": None,
                        },
                        "citations": [],
                        "must_haves_failed": ["Q2", "Q9"],
                        "difficulty_run": False,
                        "fixes_applied": [
                            {
                                "file": "instruction.md",
                                "change": "Removed file/macro recipe",
                                "axis_targeted": "prescriptiveness",
                            }
                        ],
                        "next_round_result": None,
                        "prediction_ref": None,
                        "source": "test",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (outputs / "judge_rehearsal.json").write_text(
                json.dumps({"confirmed_overreach": ["A22"], "confirmed_gaps": []}) + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(cl, "ROOT", root), mock.patch.object(
                cl, "PROPOSALS", root / "knowledge" / "proposals"
            ), mock.patch.object(cl, "FEEDBACK_DIR", fb_dir):
                body, has = cl.build_proposal_text(task, notes="real operator friction")
                self.assertTrue(has)
                self.assertNotIn("(edit)", body)
                self.assertIn("prescriptiveness=2.5", body)
                self.assertIn("Removed file/macro recipe", body)
                self.assertIn("A22", body)
                self.assertIn("accept-risk", body.lower())
                cl.assert_no_placeholders(body)


if __name__ == "__main__":
    unittest.main()
