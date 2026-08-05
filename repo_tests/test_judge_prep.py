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
        # Weak-only lexical links set low_confidence; that is advisory, not a prep failure.


class JudgePrepLinkStatusTests(unittest.TestCase):
    def test_single_strong_identifier_is_weak_link(self):
        """cell_map alone must not paint green (Case 2 A6 bug)."""
        self.assertEqual(jp.link_status({"cell_map", "downsample"}, {"cell_map", "out_shape"}), "weak_link")
        self.assertEqual(jp.link_status({"cell_map"}, {"cell_map"}), "weak_link")
        # Fragment noise (shape from out_shape, map from cell_map) must not create "linked"
        req = jp.tokens_from(
            "`downsample(..., cell_map=None)` returns RGBA of the output shape, collapsing each cell."
        )
        asrt = jp.tokens_from("assert cell_map.out_shape == (len(lines_y) - 1, len(lines_x) - 1)")
        self.assertEqual(jp.link_status(req, asrt), "weak_link")

    def test_two_strong_tokens_linked(self):
        self.assertEqual(
            jp.link_status({"cell_map", "downsample", "opaque"}, {"cell_map", "downsample"}),
            "linked",
        )

    def test_no_overlap_none(self):
        self.assertEqual(jp.link_status({"alpha"}, {"beta"}), "none")

    def test_linked_spot_check_deterministic(self):
        faith = [{"assertion_id": f"A{i}", "status": "ok"} for i in range(1, 21)]
        faith.append({"assertion_id": "A99", "status": "unlinked_lexically"})
        s1 = jp.sample_linked_spot_check(faith, seed="abc123")
        s2 = jp.sample_linked_spot_check(faith, seed="abc123")
        self.assertEqual(s1["assertion_ids"], s2["assertion_ids"])
        self.assertEqual(s1["sample_size"], max(5, int(__import__("math").ceil(20 * 0.10))))
        self.assertEqual(s1["population"], 20)
        self.assertNotIn("A99", s1["assertion_ids"])
        s3 = jp.sample_linked_spot_check(faith, seed="other")
        # different seed usually different order/set; at least seed recorded
        self.assertEqual(s3["seed"], "other")


class JudgePrepGapOverreachTests(unittest.TestCase):
    def test_lexical_candidates_do_not_block_prep(self):
        """FIX B: prep emits candidates; does not block on coverage:/overreach:."""
        r = run_fixture("gap_overreach")
        self.assertFalse(r["hard_stopped"])
        self.assertTrue(r.get("no_graded_link_candidates") or r.get("coverage_gaps_unexplained"))
        self.assertTrue(
            r.get("faithfulness_triage_candidates")
            or r.get("unlinked_lexically_candidates")
            or r.get("overreach_unexplained")
        )
        self.assertFalse(any(b.startswith("coverage:") for b in r["blockers"]), r["blockers"])
        self.assertFalse(any(b.startswith("overreach:") for b in r["blockers"]), r["blockers"])
        faith = [
            f
            for f in r["faithfulness"]
            if f["status"] in ("unlinked_lexically", "weak_link")
        ]
        self.assertTrue(faith)
        cov = [c for c in r["coverage"] if c["status"] in ("no_graded_link", "weak_link")]
        self.assertTrue(cov)

    def test_explained_decisions_still_join(self):
        r0 = run_fixture("gap_overreach")
        gap_ids = r0.get("coverage_gaps_unexplained") or r0.get("no_graded_link_candidates") or []
        self.assertTrue(gap_ids)
        rid = gap_ids[0]
        req = next(x for x in r0["requirements"] if x["id"] == rid)
        over = r0.get("overreach_unexplained") or r0.get("unlinked_lexically_candidates") or []
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
        self.assertNotIn(rid, r1.get("coverage_gaps_unexplained") or [])

    def test_stale_fingerprint_invalidates(self):
        r0 = run_fixture("gap_overreach")
        rid = (r0.get("coverage_gaps_unexplained") or r0.get("no_graded_link_candidates") or ["R1"])[0]
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


class JudgePrepRehearsalValidateTests(unittest.TestCase):
    def test_validate_blocks_confirmed_and_stale(self):
        r = run_fixture("gap_overreach")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            prep_path = out / "judge_prep.json"
            prep_path.write_text(json.dumps(r), encoding="utf-8")
            fp = jp.file_sha256(prep_path)
            cand_a = (r.get("faithfulness_triage_candidates") or r.get("unlinked_lexically_candidates") or ["A1"])[0]
            cand_r = (r.get("no_graded_link_candidates") or ["R1"])[0]
            reh = {
                "schema_version": 1,
                "judge_prep_fingerprint": fp,
                "triage": {
                    "coverage": [
                        {
                            "requirement_id": cand_r,
                            "prep_status": "no_graded_link",
                            "verdict": "CONFIRMED_GAP",
                            "rationale": "untested",
                        }
                    ],
                    "faithfulness": [
                        {
                            "assertion_id": cand_a,
                            "prep_status": "unlinked_lexically",
                            "verdict": "NOT_OVERREACH",
                            "bucket": "a",
                            "rationale": "implied",
                        }
                    ],
                },
            }
            # incomplete triage of all candidates → blockers for missing + confirmed gap
            blockers, summary = jp.validate_judge_rehearsal(reh, prep_path, prep_report=r)
            self.assertTrue(any("CONFIRMED_GAP" in b for b in blockers), blockers)
            self.assertIn(cand_r, summary["confirmed_gaps"])

            # full NOT_A_GAP / NOT_OVERREACH clears confirmation blockers (may still warn missing none)
            faith_rows = []
            for aid in r.get("faithfulness_triage_candidates") or r.get("unlinked_lexically_candidates") or []:
                row = next(x for x in r["faithfulness"] if x["assertion_id"] == aid)
                faith_rows.append(
                    {
                        "assertion_id": aid,
                        "prep_status": row["status"],
                        "verdict": "NOT_OVERREACH",
                        "bucket": "b",
                        "rationale": "public API",
                    }
                )
            cov_rows = []
            for rid in r.get("no_graded_link_candidates") or []:
                crow = next(x for x in r["coverage"] if x["requirement_id"] == rid)
                cov_rows.append(
                    {
                        "requirement_id": rid,
                        "prep_status": crow["status"],
                        "verdict": "NOT_A_GAP",
                        "rationale": "wording only",
                    }
                )
            reh2 = {
                "schema_version": 1,
                "judge_prep_fingerprint": fp,
                "triage": {"coverage": cov_rows, "faithfulness": faith_rows},
                "linked_spot_check": {
                    "seed": (r.get("linked_spot_check") or {}).get("seed"),
                    "assertion_ids": (r.get("linked_spot_check") or {}).get("assertion_ids") or [],
                    "triage": [
                        {
                            "assertion_id": aid,
                            "prep_status": "ok",
                            "verdict": "NOT_OVERREACH",
                            "bucket": "a",
                            "rationale": "sample clear",
                        }
                        for aid in ((r.get("linked_spot_check") or {}).get("assertion_ids") or [])
                    ],
                },
            }
            blockers2, summary2 = jp.validate_judge_rehearsal(reh2, prep_path, prep_report=r)
            self.assertEqual(blockers2, [], blockers2)

            # SAMPLE_HIT is a warning signal, not a packaging blocker
            if (r.get("linked_spot_check") or {}).get("assertion_ids"):
                aid0 = r["linked_spot_check"]["assertion_ids"][0]
                reh_hit = json.loads(json.dumps(reh2))
                reh_hit["linked_spot_check"]["triage"][0]["verdict"] = "SAMPLE_HIT"
                blockers_hit, summary_hit = jp.validate_judge_rehearsal(
                    reh_hit, prep_path, prep_report=r
                )
                self.assertEqual(blockers_hit, [], blockers_hit)
                self.assertIn(aid0, summary_hit.get("sample_hits") or [])

            reh_stale = {**reh2, "judge_prep_fingerprint": "0" * 64}
            blockers3, _ = jp.validate_judge_rehearsal(reh_stale, prep_path, prep_report=r)
            self.assertTrue(any("fingerprint mismatch" in b for b in blockers3), blockers3)


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

    def test_ungraded_asserts_participate_in_faithfulness_with_medium_severity(self):
        """FIX A: judge scores EVERY test file; grade gates severity, not eligibility."""
        r = run_fixture("allow_extra")
        ungraded = [f for f in r["faithfulness"] if f["grade"] == "UNGRADED"]
        self.assertTrue(ungraded, "expected UNGRADED faithfulness rows")
        self.assertFalse(
            any(f["status"].startswith("n/a_") for f in r["faithfulness"]),
            "UNGRADED must not be skipped as n/a_*",
        )
        unlinked = [f for f in ungraded if f["status"] in ("unlinked_lexically", "weak_link")]
        self.assertTrue(unlinked, ungraded)
        for f in unlinked:
            self.assertEqual(f["severity"], "medium", f)
        for f in r["faithfulness"]:
            if f["status"] in ("unlinked_lexically", "weak_link") and f["grade"] == "GRADED":
                self.assertEqual(f["severity"], "high", f)
            if f["status"] == "ok":
                self.assertIsNone(f.get("severity"))


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


class JudgePrepPreflightInputsHashTests(unittest.TestCase):
    """prep → rehearsal → preflight hash gate (never silently regenerate)."""

    def _write_clear_rehearsal(self, prep: dict, prep_path: Path, reh_path: Path) -> None:
        import hashlib

        fp = hashlib.sha256(prep_path.read_bytes()).hexdigest()
        cov_rows = [
            {
                "requirement_id": r["requirement_id"],
                "prep_status": r["status"],
                "verdict": "NOT_A_GAP",
                "bucket": "a",
                "rationale": "clear",
            }
            for r in prep.get("coverage") or []
            if r.get("status") in jp.COVERAGE_TRIAGE_STATUSES
        ]
        faith_rows = [
            {
                "assertion_id": r["assertion_id"],
                "prep_status": r["status"],
                "verdict": "NOT_OVERREACH",
                "bucket": "a",
                "rationale": "clear",
            }
            for r in prep.get("faithfulness") or []
            if r.get("status") in jp.FAITHFULNESS_TRIAGE_STATUSES
        ]
        spot = prep.get("linked_spot_check") or {}
        reh = {
            "schema_version": 1,
            "judge_prep_fingerprint": fp,
            "triage": {"coverage": cov_rows, "faithfulness": faith_rows},
            "linked_spot_check": {
                "seed": spot.get("seed"),
                "assertion_ids": list(spot.get("assertion_ids") or []),
                "triage": [
                    {
                        "assertion_id": aid,
                        "prep_status": "ok",
                        "bucket": "a",
                        "verdict": "NOT_OVERREACH",
                        "rationale": "sample clear",
                    }
                    for aid in (spot.get("assertion_ids") or [])
                ],
                "sample_hits": [],
            },
            "platform_logic": "OK",
            "operational_bar_3_5": "PASS",
        }
        reh_path.write_text(json.dumps(reh, indent=2) + "\n", encoding="utf-8")

    def test_prep_rehearsal_preflight_stable_then_edit_fails(self):
        src = FIX / "clean"
        task_src = src / "task"
        sc = src / "static_check_report.json"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            task = root / "task"
            out = root / "outputs"
            out.mkdir()
            # copy fixture task so we can edit it
            import shutil

            shutil.copytree(task_src, task)
            prep = jp.run_judge_prep(task, out, sc, task_name="clean_chain")
            prep_path = out / "judge_prep.json"
            self.assertTrue(prep_path.is_file())
            self.assertTrue(prep.get("inputs_hash"))
            self.assertEqual(prep["inputs_hash"], jp.prep_inputs_hash(task))

            reh_path = out / "judge_rehearsal.json"
            self._write_clear_rehearsal(prep, prep_path, reh_path)

            # Stable: load for preflight + rehearsal validate both clean
            loaded, hash_blockers = jp.load_judge_prep_for_preflight(task, prep_path)
            self.assertEqual(hash_blockers, [], hash_blockers)
            self.assertIsNotNone(loaded)
            reh = json.loads(reh_path.read_text(encoding="utf-8"))
            reh_blockers, _ = jp.validate_judge_rehearsal(reh, prep_path, prep_report=loaded)
            self.assertEqual(reh_blockers, [], reh_blockers)
            # File bytes unchanged (no regenerate)
            before = prep_path.read_bytes()
            loaded2, _ = jp.load_judge_prep_for_preflight(task, prep_path)
            self.assertEqual(prep_path.read_bytes(), before)
            self.assertEqual(loaded2.get("inputs_hash"), prep["inputs_hash"])

            # Edit a test file between rehearsal and preflight → specific message
            patch = task / "tests" / "tests.patch"
            patch.write_text(patch.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
            loaded3, hash_blockers3 = jp.load_judge_prep_for_preflight(task, prep_path)
            self.assertIsNone(loaded3)
            self.assertEqual(hash_blockers3, [jp.PREP_INPUTS_CHANGED_MSG], hash_blockers3)


class JudgeRehearsalModuleExampleTests(unittest.TestCase):
    """Validator must accept the exact JSON shape documented in judge_rehearsal.md."""

    def test_module_documented_example_shape_validates(self):
        """linked_spot_check.triage is canonical — not triage.linked_spot_check."""
        src = FIX / "clean"
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            prep = jp.run_judge_prep(
                src / "task", out, src / "static_check_report.json", task_name="example_shape"
            )
            prep_path = out / "judge_prep.json"
            import hashlib

            fp = hashlib.sha256(prep_path.read_bytes()).hexdigest()
            spot = prep.get("linked_spot_check") or {}
            # Minimal instance of the module's documented example (same keys / nesting)
            example = {
                "schema_version": 1,
                "judge_prep_fingerprint": fp,
                "triage": {
                    "coverage": [
                        {
                            "requirement_id": r["requirement_id"],
                            "prep_status": r["status"],
                            "bucket": "a",
                            "verdict": "NOT_A_GAP",
                            "rationale": "...",
                        }
                        for r in prep.get("coverage") or []
                        if r.get("status") in jp.COVERAGE_TRIAGE_STATUSES
                    ],
                    "faithfulness": [
                        {
                            "assertion_id": r["assertion_id"],
                            "prep_status": r["status"],
                            "grade": r.get("grade") or "GRADED",
                            "severity": r.get("severity") or "high",
                            "bucket": "a",
                            "verdict": "NOT_OVERREACH",
                            "rationale": "...",
                        }
                        for r in prep.get("faithfulness") or []
                        if r.get("status") in jp.FAITHFULNESS_TRIAGE_STATUSES
                    ],
                },
                "confirmed_gaps": [],
                "confirmed_overreach": [],
                "linked_spot_check": {
                    "seed": spot.get("seed"),
                    "assertion_ids": list(spot.get("assertion_ids") or []),
                    "triage": [
                        {
                            "assertion_id": aid,
                            "prep_status": "ok",
                            "bucket": "a",
                            "verdict": "NOT_OVERREACH",
                            "rationale": "...",
                        }
                        for aid in (spot.get("assertion_ids") or [])
                    ],
                    "sample_hits": [],
                },
                "platform_logic": "OK",
                "operational_bar_3_5": "PASS",
            }
            blockers, summary = jp.validate_judge_rehearsal(
                example, prep_path, prep_report=prep
            )
            self.assertEqual(blockers, [], blockers)
            self.assertEqual(
                summary.get("n_sample_triaged"),
                len(spot.get("assertion_ids") or []),
            )
            # Wrong legacy nesting must NOT satisfy the sample gate when samples exist
            if spot.get("assertion_ids"):
                wrong = json.loads(json.dumps(example))
                wrong["triage"]["linked_spot_check"] = wrong["linked_spot_check"].pop("triage")
                blockers_wrong, _ = jp.validate_judge_rehearsal(
                    wrong, prep_path, prep_report=prep
                )
                self.assertTrue(
                    any("untagged linked_spot_check sample" in b for b in blockers_wrong),
                    blockers_wrong,
                )


if __name__ == "__main__":
    unittest.main()
