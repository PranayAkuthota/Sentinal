#!/usr/bin/env python3
"""Intake a Sentinel Ultra / Harbor task: unpack, locate the task root, inventory it.

Usage:
    python3 intake.py <task.zip | task-dir> [--work <workdir>] [--json out.json]

Handles the common packaging shapes:
  * zip whose entries are the flat task contents (the required shape)
  * zip that wraps a `task/` folder (and possibly `runs/`)
  * zip that wraps `<task-id>/task/` + `<task-id>/runs/`
  * a plain directory already on disk
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile

MARKERS = ("task.toml", "instruction.md")


def find_task_root(base):
    """Return the directory that directly contains task.toml + instruction.md."""
    candidates = []
    for dirpath, dirnames, filenames in os.walk(base):
        # never descend into the repo checkout or runs logs
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
        if all(m in filenames for m in MARKERS):
            depth = os.path.relpath(dirpath, base).count(os.sep)
            candidates.append((depth, dirpath))
        # don't walk into environment/repo -- huge and irrelevant
        if os.path.basename(dirpath) == "environment" and "repo" in dirnames:
            dirnames.remove("repo")
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][1]


def find_runs(base, task_root):
    """runs/ sits alongside task/ at the top level."""
    for cand in (os.path.join(os.path.dirname(task_root), "runs"),
                 os.path.join(base, "runs")):
        if os.path.isdir(cand):
            return cand
    return None


def du(path):
    try:
        out = subprocess.run(["du", "-sk", path], capture_output=True, text=True, timeout=120)
        return int(out.stdout.split()[0]) * 1024
    except Exception:
        return -1


def human(n):
    if n < 0:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024.0
    return f"{n:.1f}TB"


EXPECTED = [
    ("instruction.md", "file"),
    ("task.toml", "file"),
    ("environment/Dockerfile", "file"),
    ("environment/problem_statement.md", "file"),
    ("environment/repo", "dir"),
    ("solution/solve.sh", "file"),
    ("solution/golden.patch", "file"),
    ("tests/test.sh", "file"),
    ("tests/tests.patch", "file"),
    ("tests/config.json", "file"),
]

# Known variant names -> canonical name (see reference/harbor-format.md)
VARIANTS = {
    "solution/solution.patch": "solution/golden.patch",
    "solution/init_state.patch": "solution/golden.patch",
    "tests/test.patch": "tests/tests.patch",
    "environment/config.json": "tests/config.json",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="task .zip or task directory")
    ap.add_argument("--work", help="workdir to unpack into (default: alongside the zip)")
    ap.add_argument("--json", help="write the inventory as JSON")
    ap.add_argument("--force", action="store_true", help="overwrite an existing workdir")
    a = ap.parse_args()

    target = os.path.abspath(a.target)
    if not os.path.exists(target):
        sys.exit(f"error: no such path: {target}")

    if os.path.isfile(target) and target.lower().endswith(".zip"):
        work = os.path.abspath(a.work or os.path.splitext(target)[0] + "_unpacked")
        if os.path.exists(work):
            if a.force:
                shutil.rmtree(work)
            else:
                sys.exit(f"error: {work} already exists (use --force to overwrite)")
        os.makedirs(work)
        with zipfile.ZipFile(target) as z:
            z.extractall(work)
        base = work
        src_kind = "zip"
    elif os.path.isdir(target):
        if a.work:
            work = os.path.abspath(a.work)
            if os.path.exists(work):
                if a.force:
                    shutil.rmtree(work)
                else:
                    sys.exit(f"error: {work} already exists (use --force to overwrite)")
            shutil.copytree(target, work, symlinks=True)
            base = work
        else:
            base = target
        src_kind = "dir"
    else:
        sys.exit("error: target must be a .zip file or a directory")

    root = find_task_root(base)
    if root is None:
        sys.exit(f"error: could not find a task root (a dir containing {' + '.join(MARKERS)}) "
                 f"under {base}")

    runs = find_runs(base, root)
    rel_root = os.path.relpath(root, base)

    inv = {
        "source": target,
        "source_kind": src_kind,
        "base": base,
        "task_root": root,
        "task_root_rel": rel_root,
        "runs_dir": runs,
        "wrapped": rel_root != ".",
        "present": {},
        "missing": [],
        "variants": [],
        "notes": [],
    }

    for rel, kind in EXPECTED:
        p = os.path.join(root, rel)
        ok = os.path.isdir(p) if kind == "dir" else os.path.isfile(p)
        inv["present"][rel] = ok
        if not ok:
            inv["missing"].append(rel)

    for variant, canonical in VARIANTS.items():
        if os.path.exists(os.path.join(root, variant)):
            inv["variants"].append({"found": variant, "rename_to": canonical})
            if canonical in inv["missing"]:
                inv["missing"].remove(canonical)

    repo = os.path.join(root, "environment", "repo")
    if os.path.isdir(repo):
        inv["repo_size_bytes"] = du(repo)
        gd = os.path.join(repo, ".git")
        inv["git_present"] = os.path.exists(gd)
        inv["git_size_bytes"] = du(gd) if os.path.exists(gd) else 0
    else:
        inv["git_present"] = False

    if inv["wrapped"]:
        inv["notes"].append(
            "Bundle wraps the task in a subdirectory. Your re-upload zip must contain the "
            "FLAT contents of the task root (see checklists.md D).")
    if runs:
        inv["notes"].append(
            "runs/ present -- review it for timeouts/misinterpretation, but NEVER include it "
            "in the re-upload zip.")
    if not inv.get("git_present"):
        inv["notes"].append(
            "environment/repo/.git is missing -- usually a zip tool that dropped dotfiles. "
            "The agent needs a real repo. See environment-and-git.md.")

    # ---- report ----
    print(f"Task root : {root}")
    print(f"Layout    : {'WRAPPED in ' + rel_root if inv['wrapped'] else 'flat (correct)'}")
    print(f"runs/     : {runs or 'not present'}")
    if os.path.isdir(repo):
        print(f"repo size : {human(inv['repo_size_bytes'])}   "
              f".git: {human(inv.get('git_size_bytes', 0))}"
              f"{'  ** > 100MB **' if inv.get('git_size_bytes', 0) > 100 * 1024 ** 2 else ''}")
    print()
    print("Expected files:")
    for rel, _ in EXPECTED:
        print(f"  {'OK ' if inv['present'][rel] else 'MISSING'}  {rel}")
    if inv["variants"]:
        print()
        print("Naming variants found (rename before submitting):")
        for v in inv["variants"]:
            print(f"  {v['found']}  ->  {v['rename_to']}")
    if inv["missing"]:
        print()
        print("MISSING (after accounting for variants):")
        for m in inv["missing"]:
            print(f"  - {m}")
    if inv["notes"]:
        print()
        for n in inv["notes"]:
            print(f"NOTE: {n}")

    print()
    print("Next: read in this order -> instruction.md, task.toml (source PR), the PR itself,")
    print("      solution/golden.patch, tests/tests.patch + config.json, environment/Dockerfile,")
    print("      runs/. Then:  python3 check_task.py " + root)

    if a.json:
        with open(a.json, "w") as f:
            json.dump(inv, f, indent=2)
        print(f"\nwrote {a.json}")


if __name__ == "__main__":
    main()
