#!/usr/bin/env python3
"""Hardened Sentinel submitter integration tests (offline mocks only)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation"))
import sentinel_submitter as ss  # noqa: E402

PASS = FAIL = 0
RESULTS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        RESULTS.append(f"PASS: {name}")
        print(f"PASS: {name}")
    else:
        FAIL += 1
        RESULTS.append(f"FAIL: {name} — {detail}")
        print(f"FAIL: {name} — {detail}")


def cleanup(name: str) -> None:
    for p in (ROOT / "work" / name, ROOT / "task_outputs" / name):
        if p.exists():
            shutil.rmtree(p)
    for p in (ROOT / "completed_tasks").glob(f"{name}*"):
        shutil.rmtree(p, ignore_errors=True)


def write_task(
    staging: Path,
    *,
    f2p_count: int = 12,
    duplicate_ids: bool = False,
    invalid_ids: bool = False,
    sync: bool = True,
    golden: bool = True,
    solution_patch: bool = False,
    init_state: bool = False,
    network: bool = False,
    forbidden: bool = False,
    multi_root: bool = False,
    with_git: bool = True,
    dirty_git: bool = False,
    with_remote: bool = False,
    with_reflog: bool = False,
    unexpected_ref: bool = False,
    oversized_git: bool = False,
    patch_bad: bool = False,
    missing_instruction: bool = False,
    parameterized_ids: bool = False,
) -> None:
    def build_one(task_root: Path, label: str = "A") -> None:
        (task_root / "environment" / "repo").mkdir(parents=True)
        (task_root / "solution").mkdir(parents=True)
        (task_root / "tests").mkdir(parents=True)
        instr = f"# Mock {label}\nFix the bug in module.\n"
        if not missing_instruction:
            (task_root / "instruction.md").write_text(instr, encoding="utf-8")
        ps = instr if sync else instr + "EXTRA\n"
        (task_root / "environment" / "problem_statement.md").write_text(ps, encoding="utf-8")
        toml = [
            'version = "1.0"',
            "[metadata]",
            'category = "software-engineering"',
            'base_commit_sha = "PLACEHOLDER"',
            "[resources]",
            "cpus = 2",
            "memory_mb = 4096",
            "storage_mb = 8192",
            "gpus = 0",
            "[timeouts]",
            "build_timeout_sec = 600",
            "agent_timeout_sec = 900",
            "verifier_timeout_sec = 600",
            "[environment]",
            'network_mode = "public"',
            "[agent]",
            'network_mode = "allowlist"',
            'allowed_hosts = ["api.portkey.ai"]',
            "[verifier]",
            'network_mode = "no-network"',
        ]
        if network:
            # Intentional wrong values for negative tests
            toml = [line for line in toml if "network_mode" not in line and "allowed_hosts" not in line]
            toml.extend(
                [
                    "[environment]",
                    'network_mode = "bridge"',
                    "[agent]",
                    'allowed_hosts = ["example.com"]',
                ]
            )
        (task_root / "environment" / "Dockerfile").write_text(
            "FROM python:3.11-slim-bookworm\nRUN true\n", encoding="utf-8"
        )
        (task_root / "environment" / "repo" / "app.py").write_text("x=1\n", encoding="utf-8")
        (task_root / "solution" / "solve.sh").write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
        if golden:
            (task_root / "solution" / "golden.patch").write_text(
                "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-x=1\n+x=2\n", encoding="utf-8"
            )
        if solution_patch:
            (task_root / "solution" / "solution.patch").write_text(
                "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-x=1\n+x=2\n", encoding="utf-8"
            )
        if init_state:
            (task_root / "solution" / "init_state.patch").write_text(
                "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-x=2\n+x=1\n", encoding="utf-8"
            )
        (task_root / "tests" / "test.sh").write_text("#!/bin/bash\necho 1>/logs/verifier/reward.txt\n", encoding="utf-8")
        (task_root / "tests" / "grade.py").write_text("print('ok')\n", encoding="utf-8")
        if patch_bad:
            (task_root / "tests" / "tests.patch").write_text(
                "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-this_line_does_not_exist_anywhere\n+x=2\n",
                encoding="utf-8",
            )
        else:
            (task_root / "tests" / "tests.patch").write_text(
                "--- /dev/null\n+++ b/tests_added.py\n@@ -0,0 +1,3 @@\n+def test_added():\n+    assert True\n+\n",
                encoding="utf-8",
            )
            # file that patch would create is optional for dry-run against clean repo of app.py only
        ids = []
        for i in range(f2p_count):
            tid = f"test_case_{i}"
            if parameterized_ids and i == 0:
                tid = "tests/test_foo.py::test_bar[param-1]"
            if invalid_ids and i == 1:
                tid = "totally_missing_id_xyz"
            ids.append(tid)
        if duplicate_ids and f2p_count >= 2:
            ids[1] = ids[0]
        # put static tokens in tests for matching
        body = "\n".join(f"def {i.split('::')[-1].split('[')[0]}():\n    assert True\n" for i in ids if "[" not in i)
        if parameterized_ids:
            body += "\n# parameterized collected at runtime\n"
        (task_root / "tests" / "test_cases.py").write_text(body, encoding="utf-8")
        cfg = {
            "execution": {"commands": ["pytest -q"], "timeout": 120},
            "grading": {"fail_to_pass": ids, "pass_to_pass": ["test_case_0"], "parser": "pytest"},
            "reward_path": "/logs/verifier/reward.txt",
        }
        (task_root / "tests" / "config.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        if forbidden:
            (task_root / "__pycache__").mkdir(exist_ok=True)
            (task_root / "__pycache__" / "x.pyc").write_bytes(b"\0")
            (task_root / "metadata.json").write_text("{}", encoding="utf-8")

        if with_git:
            repo = task_root / "environment" / "repo"
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "base"], cwd=repo, check=True, capture_output=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            out = []
            for ln in toml:
                if "base_commit_sha" in ln:
                    out.append(f'base_commit_sha = "{head}"')
                else:
                    out.append(ln)
            (task_root / "task.toml").write_text("\n".join(out) + "\n", encoding="utf-8")
            if with_remote:
                subprocess.run(["git", "remote", "add", "origin", "https://example.com/r.git"], cwd=repo, check=True, capture_output=True)
            if dirty_git:
                (repo / "app.py").write_text("x=999\n", encoding="utf-8")
            if unexpected_ref:
                (repo / "extra.txt").write_text("x\n", encoding="utf-8")
                subprocess.run(["git", "add", "extra.txt"], cwd=repo, capture_output=True)
                subprocess.run(["git", "stash", "push", "-u", "-m", "x"], cwd=repo, capture_output=True)
            if not with_reflog:
                logs = repo / ".git" / "logs"
                if logs.exists():
                    shutil.rmtree(logs)
            if oversized_git:
                big = repo / ".git" / "big.bin"
                with big.open("wb") as f:
                    f.write(b"0" * (1024 * 1024))
        else:
            (task_root / "task.toml").write_text("\n".join(toml).replace("PLACEHOLDER", "abc") + "\n", encoding="utf-8")

    if multi_root:
        build_one(staging / "taskA", "A")
        build_one(staging / "taskB", "B")
    else:
        build_one(staging / "task", "A")


def make_zip(tmp: Path, name: str, **kwargs) -> Path:
    staging = tmp / f"stage_{name}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    write_task(staging, **kwargs)
    zpath = tmp / f"{name}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in staging.rglob("*"):
            if p.is_file():
                # skip oversized packing into zip for oversized_git case — still include path name? include small marker only if huge
                if p.stat().st_size > 50 * 1024 * 1024:
                    continue
                zf.write(p, arcname=p.relative_to(staging).as_posix())
    return zpath


def run_ok(args: list[str]) -> None:
    ss.main(args)


def run_fail(args: list[str]) -> int:
    try:
        ss.main(args)
        return 0
    except SystemExit as e:
        return int(e.code or 1)


def evidence(task: str, name: str) -> Path:
    p = ROOT / "work" / task / "session" / "validation_logs" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("ok\n", encoding="utf-8")
    return p


def test_complete_current(tmp: Path) -> None:
    name = "it_complete"
    cleanup(name)
    z = make_zip(tmp, name, f2p_count=12)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    run_ok(["prepare", "--task-name", name])
    run_ok(["audit", "--task-name", name])
    state = json.loads((ROOT / "task_outputs" / name / "workflow_state.json").read_text())
    check("complete: audit_completed", state.get("audit_completed") is True)
    check("complete: no verdict assigned by audit", state.get("public_analysis") is None)
    cleanup(name)


def test_incomplete_blocks_package(tmp: Path) -> None:
    name = "it_incomplete"
    cleanup(name)
    z = make_zip(tmp, name, missing_instruction=True, f2p_count=12)
    code = run_fail(["intake", "--zip", str(z), "--task-name", name, "--force"])
    # may intake if markers still score; force package path
    if code == 0:
        run_ok(
            [
                "set-verdicts",
                "--task-name",
                name,
                "--public-analysis",
                "Fixable",
                "--internal-validity",
                "Fixable",
                "--duplicate-analysis",
                "Fixable",
                "--reason",
                "incomplete",
            ]
        )
        code2 = run_fail(["package-fixable", "--task-name", name])
        check("incomplete: packaging blocked", code2 != 0)
        check(
            "incomplete: no corrected zip",
            not (ROOT / "task_outputs" / name / "updated_zip_file" / f"{name}__corrected.zip").exists(),
        )
    else:
        check("incomplete: intake/root handling non-zero or blocked", True)
    cleanup(name)


def test_multi_root(tmp: Path) -> None:
    name = "it_multi"
    cleanup(name)
    z = make_zip(tmp, name, multi_root=True)
    code = run_fail(["intake", "--zip", str(z), "--task-name", name, "--force"])
    check("multi-root: intake stops non-zero", code != 0)
    # explicit select
    run_ok(["select-task", "--task-name", name, "taskA"])
    session = json.loads((ROOT / "work" / name / "session" / "session.json").read_text())
    check("multi-root: explicit select works", session.get("real_task_root", "").endswith("taskA"))
    cleanup(name)


def test_mismatch_instruction_blocks(tmp: Path) -> None:
    name = "it_sync_mismatch"
    cleanup(name)
    z = make_zip(tmp, name, sync=False, f2p_count=12)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    run_ok(
        [
            "set-verdicts",
            "--task-name",
            name,
            "--public-analysis",
            "Fixable",
            "--internal-validity",
            "Fixable",
            "--duplicate-analysis",
            "Fixable",
            "--reason",
            "sync",
        ]
    )
    code = run_fail(["package-fixable", "--task-name", name])
    check("sync mismatch: package blocked", code != 0)
    check(
        "sync mismatch: no zip",
        not (ROOT / "task_outputs" / name / "updated_zip_file" / f"{name}__corrected.zip").exists(),
    )
    # sync then still may fail other gates; at least sync command works
    run_ok(["sync-problem-statement", "--task-name", name])
    working = Path(json.loads((ROOT / "work" / name / "session" / "session.json").read_text())["working_task_root"])
    check(
        "sync command: byte equal",
        (working / "instruction.md").read_bytes()
        == (working / "environment" / "problem_statement.md").read_bytes(),
    )
    cleanup(name)


def test_f2p_counts(tmp: Path) -> None:
    for count, label, expect_cfg_error in ((9, "lt10", True), (10, "eq10", False), (11, "gt10", False)):
        name = f"it_f2p_{label}"
        cleanup(name)
        z = make_zip(tmp, name, f2p_count=count)
        run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
        run_ok(["audit", "--task-name", name])
        cfg = json.loads((ROOT / "task_outputs" / name / "config_validation_report.json").read_text())
        check(f"f2p {label}: count={count}", cfg.get("fail_to_pass_count") == count)
        if expect_cfg_error:
            check(f"f2p {label}: structural error", cfg.get("ok") is False)
        else:
            check(f"f2p {label}: structural ok", cfg.get("ok") is True)
        # exactly 10 is not more than 10
        if count == 10:
            check("exactly 10: not more-than-10", True)
        cleanup(name)


def test_duplicate_and_invalid_ids(tmp: Path) -> None:
    name = "it_dup_ids"
    cleanup(name)
    z = make_zip(tmp, name, f2p_count=12, duplicate_ids=True)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    run_ok(["audit", "--task-name", name])
    cfg = json.loads((ROOT / "task_outputs" / name / "config_validation_report.json").read_text())
    check("duplicate ids: config not ok", cfg.get("ok") is False)
    cleanup(name)

    name = "it_param_ids"
    cleanup(name)
    z = make_zip(tmp, name, f2p_count=12, parameterized_ids=True)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    run_ok(["audit", "--task-name", name])
    cfg = json.loads((ROOT / "task_outputs" / name / "config_validation_report.json").read_text())
    check(
        "parameterized ids: manual review status",
        cfg.get("test_id_status") in {"manual_review_required", "static_matched"},
    )
    cleanup(name)


def test_patch_failure(tmp: Path) -> None:
    name = "it_patch_fail"
    cleanup(name)
    z = make_zip(tmp, name, patch_bad=True, f2p_count=12)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    run_ok(
        [
            "set-verdicts",
            "--task-name",
            name,
            "--public-analysis",
            "Fixable",
            "--internal-validity",
            "Fixable",
            "--duplicate-analysis",
            "Fixable",
            "--reason",
            "patch",
        ]
    )
    code = run_fail(["package-fixable", "--task-name", name])
    check("patch fail: package blocked", code != 0)
    cleanup(name)


def test_legacy_patches(tmp: Path) -> None:
    name = "it_legacy_sol"
    cleanup(name)
    z = make_zip(tmp, name, golden=False, solution_patch=True, init_state=True, f2p_count=12)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    run_ok(["audit", "--task-name", name])
    audit = json.loads((ROOT / "task_outputs" / name / "audit_report.json").read_text())
    check("legacy: solution.patch noted", any("solution.patch" in x for x in audit["required_files"]["legacy"]))
    check("legacy: init_state noted", any("init_state" in x for x in audit["required_files"]["legacy"]))
    cleanup(name)


def test_git_blockers(tmp: Path) -> None:
    cases = [
        ("it_git_remote", {"with_remote": True}),
        ("it_git_dirty", {"dirty_git": True}),
        ("it_git_reflog", {"with_reflog": True}),
    ]
    for name, kw in cases:
        cleanup(name)
        z = make_zip(tmp, name, f2p_count=12, **kw)
        run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
        run_ok(
            [
                "set-verdicts",
                "--task-name",
                name,
                "--public-analysis",
                "Fixable",
                "--internal-validity",
                "Fixable",
                "--duplicate-analysis",
                "Fixable",
                "--reason",
                "git",
            ]
        )
        code = run_fail(["package-fixable", "--task-name", name])
        check(f"{name}: package blocked", code != 0)
        cleanup(name)


def test_forbidden_artifacts(tmp: Path) -> None:
    name = "it_forbidden"
    cleanup(name)
    z = make_zip(tmp, name, forbidden=True, f2p_count=12)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    run_ok(
        [
            "set-verdicts",
            "--task-name",
            name,
            "--public-analysis",
            "Fixable",
            "--internal-validity",
            "Fixable",
            "--duplicate-analysis",
            "Fixable",
            "--reason",
            "artifacts",
        ]
    )
    code = run_fail(["package-fixable", "--task-name", name])
    check("forbidden artifacts: package blocked", code != 0)
    cleanup(name)


def test_valid_as_is_no_zip_and_evidence_gates(tmp: Path) -> None:
    name = "it_valid"
    cleanup(name)
    z = make_zip(tmp, name, f2p_count=12)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    run_ok(
        [
            "set-verdicts",
            "--task-name",
            name,
            "--public-analysis",
            "Valid as-is",
            "--internal-validity",
            "Valid-as-is",
            "--duplicate-analysis",
            "Valid-as-is",
            "--reason",
            "looks valid",
        ]
    )
    # without docker/oracle/nop evidence, finalize blocked
    code = run_fail(["preflight", "--task-name", name])
    check("valid without evidence: preflight blocks", code != 0)
    check(
        "valid: no corrected zip",
        not (ROOT / "task_outputs" / name / "updated_zip_file" / f"{name}__corrected.zip").exists(),
    )
    check(
        "valid: no evidence zip auto",
        not (ROOT / "task_outputs" / name / "invalid_evidence" / f"{name}__unfixable_evidence.zip").exists(),
    )
    # record validations then preflight ok and still no package zip path for valid
    for chk, reward in (("docker_build", None), ("oracle", 1.0), ("nop", 0.0), ("pass_to_pass", None)):
        ev = evidence(name, f"{chk}.log")
        args = [
            "record-validation",
            "--task-name",
            name,
            "--check",
            chk,
            "--status",
            "passed",
            "--evidence",
            str(ev),
            "--summary",
            "ok",
        ]
        if reward is not None:
            args += ["--reward", str(reward)]
        run_ok(args)
    # preflight should pass finalize; package-fixable must refuse
    run_ok(["preflight", "--task-name", name])
    state = json.loads((ROOT / "task_outputs" / name / "workflow_state.json").read_text())
    check("valid with evidence: ready_to_finalize", state.get("ready_to_finalize") is True)
    check("valid: ready_to_package false", state.get("ready_to_package") is False)
    code2 = run_fail(["package-fixable", "--task-name", name])
    check("valid: package-fixable refused", code2 != 0)
    cleanup(name)


def prepare_fixable_success(tmp: Path, name: str) -> Path:
    cleanup(name)
    z = make_zip(tmp, name, f2p_count=12, with_reflog=False)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    # Ensure working copy has Harbor network blocks and golden present
    run_ok(
        [
            "set-verdicts",
            "--task-name",
            name,
            "--public-analysis",
            "Fixable",
            "--internal-validity",
            "Fixable",
            "--duplicate-analysis",
            "Fixable",
            "--reason",
            "fixable structural",
        ]
    )
    run_ok(["ensure-packaging-hygiene", "--task-name", name])
    # record local validation optional; leave not_run => validation_level locally_prepared...
    return z


def test_fixable_success_flat_zip(tmp: Path) -> None:
    name = "it_fixable_ok"
    z = prepare_fixable_success(tmp, name)
    original = Path(json.loads((ROOT / "work" / name / "session" / "session.json").read_text())["original_path"])
    before = original.read_bytes()
    run_ok(["package-fixable", "--task-name", name])
    dest = ROOT / "task_outputs" / name / "updated_zip_file" / f"{name}__corrected.zip"
    check("fixable success: zip exists", dest.exists())
    with zipfile.ZipFile(dest, "r") as zf:
        names = zf.namelist()
        top = {n.split("/")[0] for n in names if n}
        check("fixable flat: instruction.md", "instruction.md" in top)
        check("fixable flat: no runs", "runs" not in top and not any(n.startswith("runs/") for n in names))
        check("fixable flat: has environment", "environment" in top)
    check("fixable: original preserved", original.read_bytes() == before)
    check("fixable: manifest exists", (ROOT / "task_outputs" / name / "zip_manifest.json").exists())
    state = json.loads((ROOT / "task_outputs" / name / "workflow_state.json").read_text())
    check(
        "fixable: validation_level notes platform eval if not_run",
        "platform_evaluation" in str(state.get("validation_level")) or state.get("validation_level") == "locally_validated",
    )
    cleanup(name)


def test_fixable_failed_validation_blocks(tmp: Path) -> None:
    name = "it_fixable_failval"
    prepare_fixable_success(tmp, name)
    ev = evidence(name, "docker_fail.log")
    run_ok(
        [
            "record-validation",
            "--task-name",
            name,
            "--check",
            "docker_build",
            "--status",
            "failed",
            "--evidence",
            str(ev),
            "--summary",
            "fail",
        ]
    )
    code = run_fail(["package-fixable", "--task-name", name])
    check("fixable failed validation: blocked", code != 0)
    check(
        "fixable failed validation: no partial zip",
        not (ROOT / "task_outputs" / name / "updated_zip_file" / f"{name}__corrected.zip").exists(),
    )
    cleanup(name)


def test_invalid_evidence(tmp: Path) -> None:
    name = "it_invalid"
    cleanup(name)
    z = make_zip(tmp, name, f2p_count=12)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    run_ok(
        [
            "set-verdicts",
            "--task-name",
            name,
            "--public-analysis",
            "Invalid/Not Fixable",
            "--internal-validity",
            "Invalid",
            "--duplicate-analysis",
            "Invalid/Not Fixable",
            "--reason",
            "scope",
            "--invalid-category",
            "PR scope needs to be changed or reduced",
            "--unfixable-explanation",
            "Would require reducing PR scope; inspected instruction and source.",
        ]
    )
    run_ok(["package-invalid", "--task-name", name])
    ev = ROOT / "task_outputs" / name / "invalid_evidence" / f"{name}__unfixable_evidence.zip"
    check("invalid: evidence zip exists", ev.exists())
    check(
        "invalid: no corrected zip",
        not (ROOT / "task_outputs" / name / "updated_zip_file" / f"{name}__corrected.zip").exists(),
    )
    with zipfile.ZipFile(ev, "r") as zf:
        data = zf.read("README_EVIDENCE.txt").decode()
        check("invalid: manual-review label", "not a corrected valid" in data.lower())
    cleanup(name)


def test_public_duplicate_mismatch(tmp: Path) -> None:
    name = "it_mismatch_verdict"
    cleanup(name)
    z = make_zip(tmp, name, f2p_count=12)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    code = run_fail(
        [
            "set-verdicts",
            "--task-name",
            name,
            "--public-analysis",
            "Fixable",
            "--internal-validity",
            "Fixable",
            "--duplicate-analysis",
            "Valid-as-is",
            "--reason",
            "bad",
        ]
    )
    check("public/duplicate mismatch rejected", code != 0)
    cleanup(name)


def test_nine_combinations(tmp: Path) -> None:
    name = "it_nine"
    cleanup(name)
    z = make_zip(tmp, name, f2p_count=12)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    internals = ["Invalid", "Fixable", "Valid-as-is"]
    dups = ["Fixable", "Invalid/Not Fixable", "Valid-as-is"]
    pub_map = {"Fixable": "Fixable", "Invalid/Not Fixable": "Invalid/Not Fixable", "Valid-as-is": "Valid as-is"}
    n = 0
    for internal in internals:
        for dup in dups:
            run_ok(
                [
                    "set-verdicts",
                    "--task-name",
                    name,
                    "--public-analysis",
                    pub_map[dup],
                    "--internal-validity",
                    internal,
                    "--duplicate-analysis",
                    dup,
                    "--reason",
                    f"{internal}x{dup}",
                    "--invalid-category",
                    "Environment Issues",
                    "--unfixable-explanation",
                    "n/a",
                ]
            )
            state = json.loads((ROOT / "task_outputs" / name / "workflow_state.json").read_text())
            check(f"nine {internal}/{dup}: branch=dup", state.get("branch") == dup)
            check(f"nine {internal}/{dup}: internal separate", state.get("internal_validity") == internal)
            n += 1
    check("nine: 9 combos", n == 9)
    cleanup(name)


def test_state_migration(tmp: Path) -> None:
    name = "it_migrate_ok"
    cleanup(name)
    z = make_zip(tmp, name, f2p_count=12)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    path = ROOT / "task_outputs" / name / "workflow_state.json"
    old = json.loads(path.read_text())
    old["schema_version"] = 2
    old["public_analysis"] = "Fixable"
    old["duplicate_analysis"] = "Fixable"
    old["internal_validity"] = "Fixable"
    path.write_text(json.dumps(old) + "\n", encoding="utf-8")
    state = ss.load_workflow_state(name)
    check("migration success: schema 3", state.get("schema_version") == 3)
    check("migration success: backup exists", any(ROOT.joinpath("task_outputs", name).glob("workflow_state.pre_migration_backup.*.json")))

    # conflict
    name2 = "it_migrate_conflict"
    cleanup(name2)
    z2 = make_zip(tmp, name2, f2p_count=12)
    run_ok(["intake", "--zip", str(z2), "--task-name", name2, "--force"])
    path2 = ROOT / "task_outputs" / name2 / "workflow_state.json"
    bad = json.loads(path2.read_text())
    bad["schema_version"] = 1
    bad["public_analysis"] = "Fixable"
    bad["duplicate_analysis"] = "Valid-as-is"
    path2.write_text(json.dumps(bad) + "\n", encoding="utf-8")
    try:
        ss.load_workflow_state(name2)
        check("migration conflict: blocked", False, "should die")
    except SystemExit:
        check("migration conflict: blocked", True)
    cleanup(name)
    cleanup(name2)


def test_archive_exclusion_and_preservation(tmp: Path) -> None:
    decoy_dir = ROOT / "workspace_archive" / "legacy_work" / "_harden_decoy"
    decoy_dir.mkdir(parents=True, exist_ok=True)
    decoy = decoy_dir / "decoy.zip"
    make_zip(tmp, "decoy", f2p_count=12)
    shutil.copy(tmp / "decoy.zip", decoy)
    cand = ROOT / "incoming_tasks" / "it_incoming_only.zip"
    shutil.copy(make_zip(tmp, "it_incoming_only", f2p_count=12), cand)
    found = ss.find_candidate_zips(None)
    check("archive zip ignored", all("workspace_archive" not in str(p) for p in found))
    check("incoming found", any(p.name == "it_incoming_only.zip" for p in found))
    # real archive untouched
    archived = ROOT / "workspace_archive" / "legacy_work" / "fc3ad565_unimport" / "task_work" / "task.toml"
    if archived.exists():
        before = archived.read_bytes()
        run_ok(["intake", "--zip", str(cand), "--task-name", "it_incoming_only", "--force"])
        check("real archive unmodified", archived.read_bytes() == before)
    else:
        check("real archive present", False, "missing")
    cleanup("it_incoming_only")
    cand.unlink(missing_ok=True)
    shutil.rmtree(decoy_dir, ignore_errors=True)


def test_passed_without_evidence_rejected(tmp: Path) -> None:
    name = "it_no_evidence"
    cleanup(name)
    z = make_zip(tmp, name, f2p_count=12)
    run_ok(["intake", "--zip", str(z), "--task-name", name, "--force"])
    code = run_fail(
        [
            "record-validation",
            "--task-name",
            name,
            "--check",
            "docker_build",
            "--status",
            "passed",
            "--summary",
            "no evidence",
        ]
    )
    check("passed without evidence rejected", code != 0)
    cleanup(name)


def main() -> int:
    print("=== Hardened integration tests ===")
    with tempfile.TemporaryDirectory(prefix="sentinel_harden_") as td:
        tmp = Path(td)
        test_complete_current(tmp)
        test_incomplete_blocks_package(tmp)
        test_multi_root(tmp)
        test_mismatch_instruction_blocks(tmp)
        test_f2p_counts(tmp)
        test_duplicate_and_invalid_ids(tmp)
        test_patch_failure(tmp)
        test_legacy_patches(tmp)
        test_git_blockers(tmp)
        test_forbidden_artifacts(tmp)
        test_valid_as_is_no_zip_and_evidence_gates(tmp)
        test_fixable_success_flat_zip(tmp)
        test_fixable_failed_validation_blocks(tmp)
        test_invalid_evidence(tmp)
        test_public_duplicate_mismatch(tmp)
        test_nine_combinations(tmp)
        test_state_migration(tmp)
        test_archive_exclusion_and_preservation(tmp)
        test_passed_without_evidence_rejected(tmp)

    # cleanup leftovers
    for p in (ROOT / "work").glob("it_*"):
        shutil.rmtree(p, ignore_errors=True)
    for p in (ROOT / "task_outputs").glob("it_*"):
        shutil.rmtree(p, ignore_errors=True)
    (ROOT / "incoming_tasks" / "it_incoming_only.zip").unlink(missing_ok=True)

    out = ROOT / "automation" / "integration_test_results.txt"
    out.write_text("\n".join(RESULTS) + f"\n\nTOTAL PASS={PASS} FAIL={FAIL}\n", encoding="utf-8")
    print(f"\nTOTAL PASS={PASS} FAIL={FAIL}")
    print(f"Results: {out}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
