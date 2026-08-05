"""judge_prep: bipartite map, cite-only auto-REMOVE, packaging git-suppress, decisions."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation"))

import judge_prep as jp  # noqa: E402

FIX = ROOT / "repo_tests" / "fixtures" / "judge_prep"


def run_fixture(name: str, decisions: dict | None = None) -> dict:
    src = FIX / name
    task = src / "task"
    sc = src / "static_check_report.json"
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        if decisions is not None:
            (out / "judge_prep_decisions.json").write_text(
                json.dumps(decisions, indent=2) + "\n", encoding="utf-8"
            )
        return jp.run_judge_prep(task, out, sc, task_name=name)


class JudgePrepHardStopTests(unittest.TestCase):
    def test_ph1_hard_stops_without_map(self):
        r = run_fixture("hard_stop_ph1")
        self.assertTrue(r["hard_stopped"])
        self.assertFalse(r["requirements"])
        self.assertTrue(any("PH1" in x for x in r["hard_stop_reasons"]))

    def test_v0_unparseable_config_hard_stops(self):
        r = run_fixture("hard_stop_v0")
        self.assertTrue(r["hard_stopped"])
        self.assertTrue(
            any("V0" in x or "unparseable" in x.lower() or "config" in x.lower() for x in r["hard_stop_reasons"])
        )


class JudgePrepCleanTests(unittest.TestCase):
    def test_clean_task_prep_passed(self):
        r = run_fixture("clean")
        self.assertFalse(r["hard_stopped"], r.get("hard_stop_reasons"))
        self.assertTrue(r["requirements"], "should extract requirements")
        self.assertTrue(r["assertions"], "should extract assertions")
        self.assertTrue(r["prep_passed"], r.get("blockers"))
        self.assertFalse(r["map_stats"].get("low_confidence"))


class JudgePrepGapOverreachTests(unittest.TestCase):
    def test_unexplained_gap_and_overreach_block(self):
        r = run_fixture("gap_overreach")
        self.assertFalse(r["hard_stopped"])
        self.assertFalse(r["prep_passed"])
        self.assertTrue(any(b.startswith("coverage:") for b in r["blockers"]), r["blockers"])
        self.assertTrue(any(b.startswith("overreach:") for b in r["blockers"]), r["blockers"])

    def test_explained_gap_clears_with_fingerprint(self):
        # First run to learn R ids / fingerprints
        r0 = run_fixture("gap_overreach")
        gap_ids = r0.get("coverage_gaps_unexplained") or []
        self.assertTrue(gap_ids)
        rid = gap_ids[0]
        req = next(x for x in r0["requirements"] if x["id"] == rid)
        over = r0.get("overreach_unexplained") or []
        decisions = {
            "schema_version": 1,
            "decisions": [
                {
                    "ref": f"coverage:{rid}",
                    "status": "explained",
                    "reason": "covered by manual oracle check out of band",
                    "decided_at": "2026-08-05T00:00:00+00:00",
                    "fingerprint": req["fingerprint"],
                }
            ],
        }
        for aid in over:
            a = next(x for x in r0["assertions"] if x["id"] == aid)
            decisions["decisions"].append(
                {
                    "ref": f"overreach:{aid}",
                    "status": "explained",
                    "reason": "public API implied by health contract",
                    "decided_at": "2026-08-05T00:00:00+00:00",
                    "fingerprint": a["fingerprint"],
                }
            )
        r1 = run_fixture("gap_overreach", decisions=decisions)
        self.assertFalse(any(b == f"coverage:{rid}" for b in r1["blockers"]), r1["blockers"])
        self.assertFalse(any(b.startswith("overreach:") for b in r1["blockers"]), r1["blockers"])

    def test_stale_fingerprint_invalidates(self):
        r0 = run_fixture("gap_overreach")
        rid = (r0.get("coverage_gaps_unexplained") or ["R1"])[0]
        decisions = {
            "schema_version": 1,
            "decisions": [
                {
                    "ref": f"coverage:{rid}",
                    "status": "explained",
                    "reason": "stale",
                    "decided_at": "2026-08-05T00:00:00+00:00",
                    "fingerprint": "deadbeefdeadbeef",
                }
            ],
        }
        r1 = run_fixture("gap_overreach", decisions=decisions)
        self.assertTrue(r1["invalidated_decisions"])
        self.assertIn("decisions:invalidated", r1["blockers"])


class JudgePrepAllowExtraTests(unittest.TestCase):
    def test_undecided_blocks(self):
        r = run_fixture("allow_extra")
        self.assertTrue(r["allow_extra_failures"]["enabled"])
        self.assertTrue(any(b.startswith("allow_extra:") for b in r["blockers"]), r["blockers"])
        self.assertFalse(r["prep_passed"])

    def test_promote_decision_clears(self):
        r0 = run_fixture("allow_extra")
        row = r0["allow_extra_failures"]["rows"][0]
        decisions = {
            "schema_version": 1,
            "decisions": [
                {
                    "ref": f"allow_extra:{row['test_id']}",
                    "status": "DELETE",
                    "reason": "helper not part of contract",
                    "decided_at": "2026-08-05T00:00:00+00:00",
                    "fingerprint": row["fingerprint"],
                }
            ],
        }
        r1 = run_fixture("allow_extra", decisions=decisions)
        self.assertFalse(any(b.startswith("allow_extra:") for b in r1["blockers"]), r1["blockers"])


class JudgePrepPackagingTests(unittest.TestCase):
    def test_untracked_junk_hard_caps_tracked_annotated_not_suppressed(self):
        src = FIX / "packaging_junk"
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            # Pretend environment/repo/.python-version is tracked — must STILL flag,
            # with tracked=true remediation (realign base_commit_sha).
            real = jp.git_tracked_at_head

            def fake_tracked(repo: Path):
                return {".python-version", "README.md"}

            jp.git_tracked_at_head = fake_tracked  # type: ignore
            try:
                r = jp.run_judge_prep(
                    src / "task", out, src / "static_check_report.json", task_name="packaging_junk"
                )
            finally:
                jp.git_tracked_at_head = real  # type: ignore
        hits = r["packaging"]["hits"]
        paths = [h["path"] for h in hits]
        by_path = {h["path"]: h for h in hits}
        self.assertTrue(r["packaging"]["hard_cap"])
        self.assertTrue(any(p.endswith(".DS_Store") or p == ".DS_Store" for p in paths), paths)
        self.assertTrue(
            any(p.endswith("tests/.python-version") or p == "tests/.python-version" for p in paths),
            paths,
        )
        # tracked upstream junk MUST still be flagged
        self.assertIn("environment/repo/.python-version", by_path)
        self.assertTrue(by_path["environment/repo/.python-version"]["tracked"])
        self.assertIn("realign", by_path["environment/repo/.python-version"]["remediation"])
        # untracked tests/.python-version
        tpy = next(h for h in hits if h["path"].endswith("tests/.python-version") or h["path"] == "tests/.python-version")
        self.assertFalse(tpy["tracked"])
        self.assertIn("delete", tpy["remediation"].lower())
        self.assertTrue(any("__pycache__" in p for p in paths), paths)


class JudgePrepGradingShapeTests(unittest.TestCase):
    def test_nested_grading_marks_assertions_graded(self):
        r = run_fixture("grading_nested")
        grades = {a["grade"] for a in r["assertions"]}
        self.assertIn("GRADED", grades, r.get("grade_meta"))
        self.assertEqual(r["grade_meta"]["fail_to_pass_source"], "grading")
        self.assertEqual(r["grade_meta"]["fail_to_pass_count"], 4)
        # Should not falsely gap every requirement once graded
        self.assertLess(len(r.get("coverage_gaps_unexplained") or []), 4, r.get("coverage"))

    def test_toplevel_grading_marks_assertions_graded(self):
        r = run_fixture("grading_toplevel")
        grades = {a["grade"] for a in r["assertions"]}
        self.assertIn("GRADED", grades, r.get("grade_meta"))
        self.assertEqual(r["grade_meta"]["fail_to_pass_source"], "top-level")

    def test_disagree_prefers_nested_and_warns(self):
        r = run_fixture("grading_disagree")
        self.assertEqual(r["grade_meta"]["fail_to_pass_source"], "grading")
        self.assertEqual(r["grade_meta"]["fail_to_pass_count"], 4)
        self.assertTrue(any("disagree" in w for w in r["grade_meta"]["warnings"]))


class JudgePrepPatternCiteTests(unittest.TestCase):
    """Six patterns: HIT cites static id; CLEAR/negative do not false-positive."""

    def test_silent_skip_hit_and_negative(self):
        hit = run_fixture("pattern_silent_skip_hit")
        self.assertEqual(hit["auto_remove"]["silent_skip"]["status"], "HIT")
        self.assertIn("V9", hit["auto_remove"]["silent_skip"]["static_ids"])
        neg = run_fixture("pattern_silent_skip_negative")
        self.assertEqual(neg["auto_remove"]["silent_skip"]["status"], "CLEAR")

    def test_fail_open_hit(self):
        r = run_fixture("pattern_fail_open_hit")
        self.assertEqual(r["auto_remove"]["fail_open"]["status"], "HIT")

    def test_precreated_hit(self):
        r = run_fixture("pattern_precreated_artifact_hit")
        self.assertEqual(r["auto_remove"]["precreated_artifact"]["status"], "HIT")
        self.assertIn("V10", r["auto_remove"]["precreated_artifact"]["static_ids"])

    def test_agent_controls_hit(self):
        r = run_fixture("pattern_agent_controls_cover_hit")
        self.assertEqual(r["auto_remove"]["agent_controls_cover"]["status"], "HIT")

    def test_no_entry_point_hit(self):
        r = run_fixture("pattern_no_entry_point_hit")
        self.assertEqual(r["auto_remove"]["no_entry_point"]["status"], "HIT")

    def test_all_clear(self):
        r = run_fixture("static_patterns_clear")
        for name in ("silent_skip", "fail_open", "precreated_artifact", "agent_controls_cover", "no_entry_point"):
            self.assertEqual(r["auto_remove"]["name" if False else name]["status"], "CLEAR", name)

    def test_fixable_unrelated_still_builds_map(self):
        """D2-like FIXABLE must NOT hard-stop; map still built; prep_passed false."""
        src = FIX / "clean"
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            sc = {
                "findings": [
                    {
                        "id": "D2",
                        "severity": "FIXABLE",
                        "summary": "Alpine image but bash is never installed",
                    }
                ],
                "fixable_ids": ["D2"],
                "advisory_ids": [],
                "not_fixable_ids": [],
            }
            sc_path = out / "static_check_report.json"
            sc_path.write_text(json.dumps(sc), encoding="utf-8")
            r = jp.run_judge_prep(src / "task", out, sc_path, task_name="d2_map")
        self.assertFalse(r["hard_stopped"])
        self.assertTrue(r["requirements"])
        self.assertFalse(r["prep_passed"])
        self.assertIn("static_fixable:D2", r["blockers"])


class JudgePrepSchemaKindTests(unittest.TestCase):
    def test_stated_schema_kind_extracted(self):
        r = run_fixture("clean")
        kinds = {x["kind"] for x in r["requirements"]}
        self.assertIn("stated_schema", kinds)


if __name__ == "__main__":
    unittest.main()
