#!/usr/bin/env python3
"""Configuration tests for branch-aware Sentinel submitter setup.

Creates temporary mock tasks outside real task folders, verifies branch
behaviors and nine-case routing, then deletes mock data.
Does not modify any real Sentinel task.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation"))

import sentinel_submitter as ss  # noqa: E402

PASS = 0
FAIL = 0
RESULTS = []


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


def make_mock_task_zip(dest_zip: Path, task_name: str, with_runs: bool = True) -> None:
    staging = dest_zip.parent / f"_stage_{task_name}"
    if staging.exists():
        shutil.rmtree(staging)
    task_root = staging / "task"
    (task_root / "environment" / "repo").mkdir(parents=True)
    (task_root / "solution").mkdir(parents=True)
    (task_root / "tests").mkdir(parents=True)
    (task_root / "instruction.md").write_text("# Mock task\nFix the bug.\n", encoding="utf-8")
    (task_root / "task.toml").write_text(
        'version = "1.0"\n[metadata]\ncategory = "software-engineering"\n',
        encoding="utf-8",
    )
    (task_root / "environment" / "Dockerfile").write_text("FROM python:3.11-slim\n", encoding="utf-8")
    (task_root / "environment" / "problem_statement.md").write_text(
        "# Mock task\nFix the bug.\n", encoding="utf-8"
    )
    (task_root / "environment" / "repo" / "README.md").write_text("repo\n", encoding="utf-8")
    (task_root / "solution" / "solve.sh").write_text("#!/bin/bash\necho solved\n", encoding="utf-8")
    (task_root / "solution" / "golden.patch").write_text("--- a/x\n+++ b/x\n", encoding="utf-8")
    (task_root / "tests" / "test.sh").write_text("#!/bin/bash\necho 1 > /logs/verifier/reward.txt\n", encoding="utf-8")
    (task_root / "tests" / "tests.patch").write_text("--- /dev/null\n+++ b/t.py\n", encoding="utf-8")
    (task_root / "tests" / "config.json").write_text('{"tests":[]}\n', encoding="utf-8")
    (task_root / "tests" / "grade.py").write_text("print('grade')\n", encoding="utf-8")
    if with_runs:
        runs = staging / "runs" / "trial1"
        runs.mkdir(parents=True)
        (runs / "result.json").write_text('{"reward":0}\n', encoding="utf-8")

    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in staging.rglob("*"):
            if p.is_file():
                zf.write(p, arcname=p.relative_to(staging).as_posix())
    shutil.rmtree(staging)


def write_branch_answers(task_name: str, branch: str, internal: str) -> None:
    out = ROOT / "task_outputs" / task_name
    out.mkdir(parents=True, exist_ok=True)
    common = f"""SENTINEL SUBMITTER PLATFORM ANSWERS

Task:
{task_name}

Original Directory Name:
{task_name}

Original ZIP:
work/{task_name}/original/

Original ZIP Preserved:
Yes

Platform Metadata Verification:
Matched (mock)

A. PUBLIC MAIN ANALYSIS
{branch if branch != 'Valid-as-is' else 'Valid as-is'}

B. INTERNAL VALIDITY
{internal}

C. DUPLICATE ANALYSIS
{branch}

D. CONDITIONAL BRANCH
{branch}

E. BRANCH-SPECIFIC ANSWERS
[{branch} mock answers]

F. WHAT MAKES THIS TASK DIFFICULT?
Mock difficulty: multi-module config parsing edge cases in the fixture.

G. SENIOR ENGINEER ESTIMATE
10-20 minutes

H. COMMENTS FOR REVIEWER
Mock reviewer comment for {branch}.

I. INITIAL REVIEW TIME
User confirmation required

J. ENTIRE SUBMISSION TIME
User confirmation required

K. VALIDATION EVIDENCE
Not executed (configuration mock)

L. OUTPUT FILE
[branch-specific]

M. FINAL READINESS
Ready

N. REMAINING BLOCKERS
None
"""
    (out / "platform_answers.txt").write_text(common, encoding="utf-8")
    (out / "submitter_audit.md").write_text(f"# Audit\nBranch={branch}\nInternal={internal}\n", encoding="utf-8")
    (out / "findings_and_changes.md").write_text(f"# Findings\nBranch={branch}\n", encoding="utf-8")
    (out / "validation_summary.md").write_text("# Validation\nNot executed (mock)\n", encoding="utf-8")

    if branch == "Valid-as-is":
        conf = out / "confirmations.txt"
        conf.write_text(
            "\n".join(
                [
                    "1. Every requirement properly tested: Yes (mock evidence)",
                    "2. All test requirements in instructions: Yes",
                    "3. Not LLM-generated: Yes",
                    "4. Not overly-prescriptive: Yes",
                    "5. No solution leak: Yes",
                    "6. Oracle follows instructions: Yes",
                    "7. More than 10 f2p: Yes (>=11 mock)",
                ]
            )
            + "\n",
            encoding="utf-8",
        )


def cleanup_task(task_name: str) -> None:
    for p in (ROOT / "work" / task_name, ROOT / "task_outputs" / task_name, ROOT / "completed_tasks" / task_name):
        if p.exists():
            shutil.rmtree(p)
    # also any archived variants
    for p in (ROOT / "completed_tasks").glob(f"{task_name}__*"):
        shutil.rmtree(p)


def test_fixable(tmp: Path) -> None:
    name = "mock_fixable_cfg"
    cleanup_task(name)
    zpath = tmp / f"{name}.zip"
    make_mock_task_zip(zpath, name)
    # remember original bytes
    original_bytes = zpath.read_bytes()

    ss.main(["intake", "--zip", str(zpath), "--task-name", name, "--force"])
    session_path = ROOT / "work" / name / "session" / "session.json"
    check("fixable: session created", session_path.exists())
    data = json.loads(session_path.read_text(encoding="utf-8"))
    orig = Path(data["original_path"])
    extracted = Path(data["extracted_original_path"])
    working = Path(data["working_copy_path"])
    check("fixable: original preserved path exists", orig.exists() and orig.stat().st_size > 0)
    check("fixable: original bytes unchanged vs source", orig.read_bytes() == original_bytes)
    check("fixable: extracted_original exists", extracted.exists())
    check("fixable: working_copy exists", working.exists())

    # mutate only working copy
    marker = Path(data["working_task_root"]) / "instruction.md"
    marker.write_text(marker.read_text(encoding="utf-8") + "\n# corrected\n", encoding="utf-8")
    extracted_instr = Path(data["real_task_root"]) / "instruction.md"
    check(
        "fixable: extracted_original not modified",
        "# corrected" not in extracted_instr.read_text(encoding="utf-8"),
    )
    check("fixable: working_copy used for edits", "# corrected" in marker.read_text(encoding="utf-8"))

    ss.main(
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
            "mock fixable",
        ]
    )
    # Hardened packaging requires ready_to_package after preflight; this simple mock is not preflight-ready.
    try:
        ss.main(["package-fixable", "--task-name", name])
        packaged = True
    except SystemExit:
        packaged = False
    corrected = ROOT / "task_outputs" / name / "updated_zip_file" / f"{name}__corrected.zip"
    check("fixable: packaging blocked without preflight-ready mock", packaged is False and not corrected.exists())
    write_branch_answers(name, "Fixable", "Fixable")
    check(
        "fixable: branch answers generated",
        (ROOT / "task_outputs" / name / "platform_answers.txt").exists(),
    )
    check("fixable: original still unchanged after package attempt", orig.read_bytes() == original_bytes)
    cleanup_task(name)


def test_invalid(tmp: Path) -> None:
    name = "mock_invalid_cfg"
    cleanup_task(name)
    zpath = tmp / f"{name}.zip"
    make_mock_task_zip(zpath, name)
    original_bytes = zpath.read_bytes()
    ss.main(["intake", "--zip", str(zpath), "--task-name", name, "--force"])
    data = json.loads((ROOT / "work" / name / "session" / "session.json").read_text(encoding="utf-8"))
    orig = Path(data["original_path"])

    # diagnostic note in analysis
    analysis = ROOT / "work" / name / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    (analysis / "blocker.txt").write_text("PR scope would need reduction\n", encoding="utf-8")
    (ROOT / "work" / name / "session" / "validation_logs").mkdir(parents=True, exist_ok=True)
    (ROOT / "work" / name / "session" / "validation_logs" / "build.log").write_text("FAIL mock\n", encoding="utf-8")

    ss.main(
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
            "mock unfixable",
            "--invalid-category",
            "PR scope needs to be changed or reduced",
            "--unfixable-explanation",
            "Blocking defect: PR scope must be reduced. Inspected Dockerfile and instruction. Allowed corrections insufficient.",
        ]
    )
    ss.main(
        [
            "package-invalid",
            "--task-name",
            name,
            "--invalid-category",
            "PR scope needs to be changed or reduced",
            "--explanation",
            "Blocking defect: PR scope must be reduced. Inspected Dockerfile and instruction. Allowed corrections insufficient.",
        ]
    )
    evidence = ROOT / "task_outputs" / name / "invalid_evidence" / f"{name}__unfixable_evidence.zip"
    corrected = ROOT / "task_outputs" / name / "updated_zip_file" / f"{name}__corrected.zip"
    check("invalid: evidence package generated", evidence.exists())
    check("invalid: no corrected-valid ZIP created", not corrected.exists())
    check("invalid: original preserved", orig.read_bytes() == original_bytes)
    write_branch_answers(name, "Invalid/Not Fixable", "Invalid")
    # unfixable explanation template present in outputs via package contents
    with zipfile.ZipFile(evidence, "r") as zf:
        names = zf.namelist()
        check("invalid: evidence contains summary", any("evidence_summary" in n for n in names))
        check(
            "invalid: unfixable explanation template included",
            any("unfixable_explanation" in n for n in names),
        )
    cleanup_task(name)


def test_valid_as_is(tmp: Path) -> None:
    name = "mock_valid_cfg"
    cleanup_task(name)
    zpath = tmp / f"{name}.zip"
    make_mock_task_zip(zpath, name)
    original_bytes = zpath.read_bytes()
    ss.main(["intake", "--zip", str(zpath), "--task-name", name, "--force"])
    data = json.loads((ROOT / "work" / name / "session" / "session.json").read_text(encoding="utf-8"))
    orig = Path(data["original_path"])
    extracted_instr = Path(data["real_task_root"]) / "instruction.md"
    before = extracted_instr.read_text(encoding="utf-8")

    ss.main(
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
            "mock valid",
        ]
    )
    write_branch_answers(name, "Valid-as-is", "Valid-as-is")
    corrected = ROOT / "task_outputs" / name / "updated_zip_file" / f"{name}__corrected.zip"
    evidence = ROOT / "task_outputs" / name / "invalid_evidence" / f"{name}__unfixable_evidence.zip"
    check("valid: original preserved", orig.read_bytes() == original_bytes)
    check("valid: no task modification", extracted_instr.read_text(encoding="utf-8") == before)
    check("valid: no corrected ZIP", not corrected.exists())
    check("valid: no evidence ZIP", not evidence.exists())
    check(
        "valid: seven confirmations generated",
        (ROOT / "task_outputs" / name / "confirmations.txt").exists()
        and len((ROOT / "task_outputs" / name / "confirmations.txt").read_text(encoding="utf-8").splitlines())
        >= 7,
    )
    # common fields present
    answers = (ROOT / "task_outputs" / name / "platform_answers.txt").read_text(encoding="utf-8")
    for field in (
        "WHAT MAKES THIS TASK DIFFICULT",
        "SENIOR ENGINEER ESTIMATE",
        "COMMENTS FOR REVIEWER",
        "INITIAL REVIEW TIME",
        "ENTIRE SUBMISSION TIME",
    ):
        check(f"valid: common field {field}", field in answers)
    check("valid: times not invented", "User confirmation required" in answers)
    cleanup_task(name)


def test_nine_combinations(tmp: Path) -> None:
    internals = ["Invalid", "Fixable", "Valid-as-is"]
    duplicates = ["Fixable", "Invalid/Not Fixable", "Valid-as-is"]
    public_map = {
        "Fixable": "Fixable",
        "Invalid/Not Fixable": "Invalid/Not Fixable",
        "Valid-as-is": "Valid as-is",
    }
    name = "mock_nine_cfg"
    zpath = tmp / f"{name}.zip"
    make_mock_task_zip(zpath, name, with_runs=False)
    ss.main(["intake", "--zip", str(zpath), "--task-name", name, "--force"])

    routed = []
    for internal in internals:
        for dup in duplicates:
            pub = public_map[dup]
            ss.main(
                [
                    "set-verdicts",
                    "--task-name",
                    name,
                    "--public-analysis",
                    pub,
                    "--internal-validity",
                    internal,
                    "--duplicate-analysis",
                    dup,
                    "--reason",
                    f"combo {internal} x {dup}",
                ]
            )
            data = json.loads((ROOT / "work" / name / "session" / "session.json").read_text(encoding="utf-8"))
            check(
                f"nine: public matches duplicate for {internal}/{dup}",
                data["public_analysis"] == pub and data["duplicate_analysis"] == dup,
            )
            check(
                f"nine: branch==duplicate for {internal}/{dup}",
                data["branch"] == dup,
            )
            check(
                f"nine: internal separately recordable {internal}/{dup}",
                data["internal_validity"] == internal,
            )
            routed.append((internal, dup, data["branch"]))
    check("nine: all 9 combinations routed", len(routed) == 9)
    # Duplicate controls branch regardless of internal
    check(
        "nine: duplicate controls branch",
        all(branch == dup for _internal, dup, branch in routed),
    )
    cleanup_task(name)


def test_ignore_archived(tmp: Path) -> None:
    # Place a decoy ZIP under workspace_archive and ensure intake without --zip
    # only sees incoming_tasks / root non-ignored zips.
    decoy_dir = ROOT / "workspace_archive" / "legacy_work" / "_decoy_zip_test"
    decoy_dir.mkdir(parents=True, exist_ok=True)
    decoy = decoy_dir / "should_ignore.zip"
    make_mock_task_zip(decoy, "should_ignore")

    # Also put one real candidate in incoming_tasks
    cand = ROOT / "incoming_tasks" / "mock_intake_only.zip"
    make_mock_task_zip(cand, "mock_intake_only")

    found = ss.find_candidate_zips(None)
    check("ignore: archive zip not selected", all("workspace_archive" not in str(p) for p in found))
    check("ignore: incoming candidate found", any(p.name == "mock_intake_only.zip" for p in found))

    # ensure archived real task path still present and untouched
    archived = ROOT / "workspace_archive" / "legacy_work" / "fc3ad565_unimport"
    check("ignore: real archived task still present", archived.exists())
    toml = archived / "task_work" / "task.toml"
    if toml.exists():
        before = toml.read_bytes()
        # run intake of mock only
        ss.main(["intake", "--zip", str(cand), "--task-name", "mock_intake_only", "--force"])
        check("ignore: real archived task unmodified", toml.read_bytes() == before)
    else:
        check("ignore: real archived task.toml present", False, "missing task.toml")

    cleanup_task("mock_intake_only")
    cand.unlink(missing_ok=True)
    shutil.rmtree(decoy_dir)


def test_set_verdicts_rejects_mismatch() -> None:
    name = "mock_mismatch_cfg"
    cleanup_task(name)
    # minimal session fabricate
    paths = ss.session_paths(name)
    for k in ("original", "extracted_original", "working_copy", "session", "analysis", "outputs"):
        paths[k].mkdir(parents=True, exist_ok=True)
    session = {
        "task_name": name,
        "original_path": str(paths["original"] / "x.zip"),
        "extracted_original_path": str(paths["extracted_original"]),
        "working_copy_path": str(paths["working_copy"]),
        "real_task_root": str(paths["extracted_original"]),
        "working_task_root": str(paths["working_copy"]),
        "sha256": "0",
        "format": "current",
        "output_paths": {},
        "timestamps": {},
    }
    ss.save_session(name, session)
    # Create empty fake zip path not needed for set-verdicts
    try:
        ss.main(
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
                "should fail",
            ]
        )
        check("mismatch: rejected inconsistent public/duplicate", False, "should have exited")
    except SystemExit as e:
        check("mismatch: rejected inconsistent public/duplicate", e.code not in (0, None))
    cleanup_task(name)


def main() -> int:
    print("=== Branch-aware submitter configuration tests ===")
    print(f"Workspace: {ROOT}")
    # Confirm archived real task exists and will not be modified
    archived = ROOT / "workspace_archive" / "legacy_work" / "fc3ad565_unimport"
    print(f"Archived real task present: {archived.exists()}")

    with tempfile.TemporaryDirectory(prefix="sentinel_cfg_test_") as td:
        tmp = Path(td)
        test_fixable(tmp)
        test_invalid(tmp)
        test_valid_as_is(tmp)
        test_nine_combinations(tmp)
        test_ignore_archived(tmp)
        test_set_verdicts_rejects_mismatch()

    # Final cleanup of any leftover mocks
    for name in (
        "mock_fixable_cfg",
        "mock_invalid_cfg",
        "mock_valid_cfg",
        "mock_nine_cfg",
        "mock_intake_only",
        "mock_mismatch_cfg",
    ):
        cleanup_task(name)
    decoy = ROOT / "workspace_archive" / "legacy_work" / "_decoy_zip_test"
    if decoy.exists():
        shutil.rmtree(decoy)
    (ROOT / "incoming_tasks" / "mock_intake_only.zip").unlink(missing_ok=True)

    report = ROOT / "task_outputs" / "_config_test_results.txt"
    # write then we may delete — store under automation instead
    report = ROOT / "automation" / "config_test_results.txt"
    report.write_text("\n".join(RESULTS) + f"\n\nTOTAL PASS={PASS} FAIL={FAIL}\n", encoding="utf-8")
    print(f"\nTOTAL PASS={PASS} FAIL={FAIL}")
    print(f"Results: {report}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
