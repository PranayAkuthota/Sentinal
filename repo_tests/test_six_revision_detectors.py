"""Six-revision-batch detectors: V15/V16, V9 source-ratio, Q9/Q10, private internals, packaging."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation"))

import judge_prep as jp  # noqa: E402

CHECK_TASK = ROOT / ".cursor" / "skills" / "sentinel-ultra-review" / "scripts" / "check_task.py"


def _load_check_task():
    spec = importlib.util.spec_from_file_location("check_task_mod", CHECK_TASK)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class V15V16GradingConfigTests(unittest.TestCase):
    def setUp(self):
        self.ct = _load_check_task()
        self.ct.FINDINGS.clear()

    def test_allow_extra_true_emits_v15(self):
        self.ct.emit_grading_config_findings(
            {"grading": {"allow_extra_failures": True, "fail_to_pass": ["t1"]}},
            "tests/config.json",
            patch_files=["tests/test_task.py"],
            test_sh_text="pytest tests/test_task.py",
        )
        ids = [f["id"] for f in self.ct.FINDINGS]
        self.assertIn("V15", ids)
        self.assertNotIn("V16", ids)
        self.assertTrue(all(f["severity"] == "FIXABLE" for f in self.ct.FINDINGS if f["id"] == "V15"))

    def test_allow_extra_false_unrelated_suite_emits_v16(self):
        self.ct.emit_grading_config_findings(
            {
                "grading": {"allow_extra_failures": False},
                "execution": {
                    "commands": [
                        "python -m pytest -q tests/test_index.py tests/test_time.py tests/test_timeseries.py"
                    ]
                },
            },
            "tests/config.json",
            patch_files=["tests/test_new_feature.py"],
            test_sh_text="",
        )
        ids = [f["id"] for f in self.ct.FINDINGS]
        self.assertIn("V16", ids)
        self.assertNotIn("V15", ids)
        ev = next(f["evidence"] for f in self.ct.FINDINGS if f["id"] == "V16")
        self.assertIn("test_index", ev)

    def test_allow_extra_false_scoped_command_clear(self):
        self.ct.emit_grading_config_findings(
            {
                "grading": {"allow_extra_failures": False},
                "execution": {"commands": ["python -m pytest -q tests/test_new_feature.py"]},
            },
            "tests/config.json",
            patch_files=["tests/test_new_feature.py"],
        )
        self.assertEqual(self.ct.FINDINGS, [])


class V9SourceTextRatioTests(unittest.TestCase):
    def setUp(self):
        self.ct = _load_check_task()
        self.ct.FINDINGS.clear()

    def test_source_only_graded_is_fixable(self):
        body = """
def test_cmake_mentions_simd():
    src = Path("CMakeLists.txt").read_text()
    assert "SIMD" in src
    assert re.search(r"AVX2", src)
"""
        self.ct.emit_source_text_ratio_findings("tests/tests.patch", body, ["test_cmake_mentions_simd"])
        v9 = [f for f in self.ct.FINDINGS if f["id"] == "V9"]
        self.assertTrue(any(f["severity"] == "FIXABLE" for f in v9), v9)
        self.assertTrue(any("ratio=" in (f.get("evidence") or "") for f in v9))

    def test_mixed_high_ratio_is_advisory_not_fixable(self):
        body = """
def test_mixed():
    src = Path("foo.py").read_text()
    assert "toHex" in src
    assert re.search(r"ternary", src)
    assert convert(1) == "1"
"""
        self.ct.emit_source_text_ratio_findings("tests/tests.patch", body, ["test_mixed"])
        v9 = [f for f in self.ct.FINDINGS if f["id"] == "V9"]
        self.assertTrue(any(f["severity"] == "ADVISORY" for f in v9), v9)
        self.assertFalse(any(f["severity"] == "FIXABLE" for f in v9), v9)

    def test_behavioural_only_reports_info_ratio(self):
        body = """
def test_ok():
    assert run_pipeline() == 1
    with pytest.raises(ValueError):
        run_pipeline(bad=True)
"""
        self.ct.emit_source_text_ratio_findings("tests/tests.patch", body, ["test_ok"])
        v9 = [f for f in self.ct.FINDINGS if f["id"] == "V9"]
        self.assertTrue(any(f["severity"] == "INFO" for f in v9), v9)
        self.assertTrue(any("ratio=" in (f.get("evidence") or "") for f in v9))


class Q9Q10InstructionGuardTests(unittest.TestCase):
    def test_error_message_literal_blocks(self):
        text = (
            "On failure the error message must contain the words 'unsupported' and 'format'."
        )
        r = jp.scan_q9_q10_instruction(text)
        self.assertTrue(r["blocking"], r)
        self.assertTrue(any("unsupported" in (h.get("words") or []) for h in r["blocking"]))

    def test_path_near_imperative_is_candidate(self):
        text = "Update styles under src/style/ to match the tray theme."
        r = jp.scan_q9_q10_instruction(text)
        self.assertFalse(r["blocking"])
        self.assertTrue(any(c.get("path", "").startswith("src/style") for c in r["path_candidates"]), r)

    def test_module_import_path_not_flagged_as_navigation(self):
        text = (
            "Call `mbuild.utils.conversion.base10_to_base16_alph_num` to convert ids. "
            "The function must return a hex-like string."
        )
        r = jp.scan_q9_q10_instruction(text)
        self.assertEqual(r["path_candidates"], [])


class PrivateInternalsCandidateTests(unittest.TestCase):
    def test_undeclared_and_subscript_flagged(self):
        instr = "The exporter must write a video summary with width and height."
        asserts = [
            {
                "id": "A1",
                "test_id": "test_video",
                "grade": "GRADED",
                "assertion_text": "assert video_io.VideoInfo(path).width == 64",
            },
            {
                "id": "A2",
                "test_id": "test_tray",
                "grade": "GRADED",
                "assertion_text": "assert manager['contextTray']['containerEl'] is not None",
            },
        ]
        cands = jp.scan_private_internals(asserts, instr)
        ids = {c["identifier"] for c in cands}
        self.assertIn("VideoInfo", ids)
        self.assertIn("contextTray", ids)
        self.assertTrue(any(c["kind"] == "private_subscript" for c in cands))
        higher = [c for c in cands if c["severity"] == "higher"]
        self.assertTrue(higher)

    def test_declared_name_not_flagged(self):
        instr = "Construct a `VideoInfo` from the path and read `.width`."
        asserts = [
            {
                "id": "A1",
                "test_id": "test_video",
                "grade": "GRADED",
                "assertion_text": "assert VideoInfo(path).width == 64",
            }
        ]
        cands = jp.scan_private_internals(asserts, instr)
        self.assertFalse(any(c["identifier"] == "VideoInfo" for c in cands), cands)


class PackagingGitAndCacheTests(unittest.TestCase):
    def test_commit_editmsg_and_gradle_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "environment" / "repo"
            git = repo / ".git"
            git.mkdir(parents=True)
            (git / "COMMIT_EDITMSG").write_text(
                "Remove .python-version from task packaging tree\n", encoding="utf-8"
            )
            (repo / "lib" / "kotlin" / ".gradle").mkdir(parents=True)
            (repo / "lib" / "kotlin" / "build" / "reports").mkdir(parents=True)
            (repo / "outputs").mkdir(parents=True)
            (root / "instruction.md").write_text("must work\n", encoding="utf-8")
            (root / "environment" / "problem_statement.md").write_text("must work\n", encoding="utf-8")

            sweep = jp.packaging_sweep(root)
            paths = [h["path"] for h in sweep["hits"]]
            self.assertTrue(sweep["hard_cap"])
            self.assertTrue(any("COMMIT_EDITMSG" in p for p in paths), paths)
            self.assertTrue(any(".gradle" in p for p in paths), paths)
            self.assertTrue(any("build/reports" in p or p.endswith("reports") for p in paths), paths)
            self.assertTrue(any(p.endswith("outputs") or "/outputs" in p for p in paths), paths)

    def test_check_task_p4_git_leak(self):
        ct = _load_check_task()
        ct.FINDINGS.clear()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            git = root / "environment" / "repo" / ".git"
            git.mkdir(parents=True)
            (git / "COMMIT_EDITMSG").write_text("task packaging cleanup\n", encoding="utf-8")
            hits = ct.inspect_git_authoring_leakage(str(root))
            self.assertTrue(hits)
            ct.check_packaging(str(root))
            ids = [f["id"] for f in ct.FINDINGS]
            self.assertIn("P4", ids)


class JudgePrepGradingConfigSectionTests(unittest.TestCase):
    def test_grading_config_section_in_md_and_q10_blocks(self):
        fix = ROOT / "repo_tests" / "fixtures" / "judge_prep" / "clean"
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            task = Path(td) / "task"
            # copy-minimal: symlink-like by writing key files
            import shutil

            shutil.copytree(fix / "task", task)
            instr = task / "instruction.md"
            instr.write_text(
                instr.read_text(encoding="utf-8")
                + "\nThe error message must contain the words 'unsupported' and 'format'.\n",
                encoding="utf-8",
            )
            (task / "environment" / "problem_statement.md").write_text(
                instr.read_text(encoding="utf-8"), encoding="utf-8"
            )
            sc = {
                "findings": [
                    {
                        "id": "V15",
                        "severity": "FIXABLE",
                        "summary": "allow_extra_failures=true",
                        "evidence": "allow_extra_failures=true",
                        "fix": "set false",
                    }
                ],
                "fixable_ids": ["V15"],
                "advisory_ids": [],
                "not_fixable_ids": [],
                "ok": False,
            }
            sc_path = out / "static_check_report.json"
            sc_path.write_text(json.dumps(sc), encoding="utf-8")
            r = jp.run_judge_prep(task, out, sc_path, task_name="q10_v15")
            self.assertFalse(r["prep_passed"])
            self.assertTrue(any(b.startswith("q10:error_message_literal") for b in r["blockers"]), r["blockers"])
            self.assertTrue(any(b == "static_fixable:V15" for b in r["blockers"]))
            md = (out / "judge_prep.md").read_text(encoding="utf-8")
            self.assertIn("## 4b. Grading configuration (V15 / V16)", md)
            self.assertIn("## 5b. Q9/Q10 instruction guards", md)
            self.assertIn("V15", md)


if __name__ == "__main__":
    unittest.main()
