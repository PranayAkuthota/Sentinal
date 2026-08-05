#!/usr/bin/env python3
"""Apply the mechanical, guideline-authorised repairs to a Harbor task.

    python3 fix_common.py <task-root> [--apply] [--only a,b,c]

Default is a dry run. Nothing here touches tracked source files in environment/repo/,
pre-existing test logic, or PR scope — those repairs are yours to make by hand
(see reference/fix-playbooks.md).

Repairs:
  rename-golden    solution/solution.patch|init_state.patch -> solution/golden.patch
  rename-tests     tests/test.patch -> tests/tests.patch
  sync-statement   copy instruction.md -> environment/problem_statement.md (byte-exact)
  toml-network     set network_mode / allowed_hosts per block
  toml-limits      clamp cpus / memory_mb / storage_mb / gpus / timeouts into range
  compose-network  remove network_mode = "none" from docker_compose.yaml
  strip-artifacts  delete __pycache__, .DS_Store, .pytest_cache, .venv, node_modules, ...
  crlf             normalise CRLF -> LF in solve.sh / test.sh
  execbit          chmod +x solve.sh / test.sh
  shebang          report (never silently rewrite) a missing/incorrect shebang
"""
import argparse
import os
import re
import shutil
import stat
import sys

ACTIONS = []


def act(name, desc, fn):
    ACTIONS.append({"name": name, "desc": desc, "fn": fn})


def rel(root, p):
    return os.path.relpath(p, root)


# ------------------------------------------------------------------ repairs
def r_rename(root, apply_, plan):
    for src, dst in (("solution/solution.patch", "solution/golden.patch"),
                     ("solution/init_state.patch", "solution/golden.patch"),
                     ("tests/test.patch", "tests/tests.patch")):
        s, d = os.path.join(root, src), os.path.join(root, dst)
        if os.path.isfile(s) and not os.path.isfile(d):
            plan.append(("rename-golden" if "solution" in src else "rename-tests",
                         f"rename {src} -> {dst}"))
            if apply_:
                os.rename(s, d)
                # update references in scripts / config
                for ref in ("solution/solve.sh", "tests/test.sh", "tests/config.json"):
                    rp = os.path.join(root, ref)
                    if os.path.isfile(rp):
                        t = open(rp, encoding="utf-8", errors="replace").read()
                        n = t.replace(os.path.basename(src), os.path.basename(dst))
                        if n != t:
                            open(rp, "w", encoding="utf-8").write(n)
                            plan.append(("rename-golden",
                                         f"  updated reference in {ref}"))


def r_sync_statement(root, apply_, plan):
    i = os.path.join(root, "instruction.md")
    p = os.path.join(root, "environment", "problem_statement.md")
    if not os.path.isfile(i):
        return
    a = open(i, "rb").read()
    b = open(p, "rb").read() if os.path.isfile(p) else None
    if b != a:
        plan.append(("sync-statement",
                     "copy instruction.md -> environment/problem_statement.md "
                     f"({'differs' if b is not None else 'missing'})"))
        if apply_:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(a)


NET = {
    "environment": [('network_mode', '"public"')],
    "agent": [('network_mode', '"allowlist"'), ('allowed_hosts', '["api.portkey.ai"]')],
    "verifier": [('network_mode', '"no-network"')],
}
CLAMP = {
    "environment": {
        "cpus": lambda v: v if v in (2, 4) else (2 if v < 3 else 4),
        "memory_mb": lambda v: min(max(v, 2048), 16384),
        "storage_mb": lambda v: min(max(v, 5120), 10240),
        "gpus": lambda v: 0,
        "build_timeout_sec": lambda v: min(v, 1800),
    },
    "agent": {"timeout_sec": lambda v: min(v, 7200)},
    "verifier": {"timeout_sec": lambda v: min(v, 1800)},
}


COMPOSE_NETWORK_NONE_RE = re.compile(
    r"(?m)^\s*network_mode\s*[:=]\s*[\"']?none[\"']?\s*$\n?"
)

COMPOSE_CANDIDATES = (
    "docker_compose.yaml",
    "docker-compose.yaml",
    "environment/docker_compose.yaml",
    "environment/docker-compose.yaml",
)


def _sections(text):
    """-> [(name, start_idx, end_idx)] for top-level [name] tables."""
    out, marks = [], [(m.group(1), m.start(), m.end())
                      for m in re.finditer(r"(?m)^\[([A-Za-z_][\w.]*)\]\s*$", text)]
    for i, (name, s, e) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(text)
        out.append((name, e, end))
    return out


def _find_assignment(body, key):
    """Find key=value in section body; supports single-line and multiline arrays."""
    m = re.search(
        rf"(?ms)^(?P<indent>\s*){re.escape(key)}\s*=\s*\[.*?\]\s*$",
        body,
    )
    if m:
        return m
    return re.search(
        rf"(?m)^(?P<indent>\s*){re.escape(key)}\s*=\s*(?P<val>.+?)\s*$",
        body,
    )


def apply_network_blocks(text):
    """Ensure NET blocks/keys exist with canonical values. Returns (new_text, changes).

    Comment- and field-order preserving for existing lines; creates missing
    sections/keys. Idempotent when already correct.
    """
    changes = []
    for sec, kvs in NET.items():
        secs = [s for s in _sections(text) if s[0] == sec]
        if not secs:
            block_lines = [f"[{sec}]"] + [f"{k} = {want}" for k, want in kvs]
            addition = ("\n" if text and not text.endswith("\n") else "")
            addition += "\n".join(block_lines) + "\n"
            text = text + addition
            changes.append(f"[{sec}] section created with required network keys")
            continue
        _name, s, e = secs[0]
        body = text[s:e]
        for k, want in kvs:
            m = _find_assignment(body, k)
            if m:
                cur_raw = m.group(0)
                eq = cur_raw.split("=", 1)[1].strip()
                cur_norm = re.sub(r"\s+", "", eq)
                want_norm = re.sub(r"\s+", "", want)
                if cur_norm == want_norm:
                    continue
                changes.append(f"[{sec}] {k} = {eq} -> {want}")
                indent = m.group("indent") or ""
                body = body[: m.start()] + f"{indent}{k} = {want}\n" + body[m.end() :]
            else:
                changes.append(f"[{sec}] {k} = <missing> -> {want}")
                body = body.rstrip("\n") + f"\n{k} = {want}\n"
        text = text[:s] + body + text[e:]
    return text, changes


def network_blocks_ok(text):
    """True when text already has all NET keys at canonical values."""
    _, changes = apply_network_blocks(text)
    return len(changes) == 0


def r_toml(root, apply_, plan):
    p = os.path.join(root, "task.toml")
    if not os.path.isfile(p):
        return
    text = open(p, encoding="utf-8", errors="replace").read()
    orig = text

    new_text, net_changes = apply_network_blocks(text)
    for c in net_changes:
        plan.append(("toml-network", c))
    text = new_text if apply_ else text

    for sec, rules in CLAMP.items():
        secs = [s_ for s_ in _sections(text) if s_[0] == sec]
        if not secs:
            continue
        _name, s, e = secs[0]
        body = text[s:e]
        for k, fn in rules.items():
            m = re.search(rf"(?m)^\s*{k}\s*=\s*(-?\d+)\s*$", body)
            if not m:
                continue
            cur = int(m.group(1))
            new = fn(cur)
            if new != cur:
                plan.append(("toml-limits", f"[{sec}] {k} = {cur} -> {new} (published limit)"))
                if apply_:
                    body = body[:m.start()] + f"{k} = {new}" + body[m.end():]
        text = text[:s] + body + text[e:]

    if apply_ and text != orig:
        open(p, "w", encoding="utf-8").write(text)


def r_compose(root, apply_, plan):
    for cand in COMPOSE_CANDIDATES:
        p = os.path.join(root, cand)
        if not os.path.isfile(p):
            continue
        t = open(p, encoding="utf-8", errors="replace").read()
        n = COMPOSE_NETWORK_NONE_RE.sub("", t)
        if n != t:
            plan.append(("compose-network", f'remove network_mode = "none" from {cand}'))
            if apply_:
                open(p, "w", encoding="utf-8").write(n)


STRAY_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
              ".venv", "node_modules", ".idea", ".vscode"}
STRAY_FILES = {".DS_Store"}
STRAY_EXT = (".pyc", ".swp", ".orig", ".bak", "~")


def r_artifacts(root, apply_, plan):
    victims = []
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirpath.split(os.sep):
            dirnames[:] = []
            continue
        for d in list(dirnames):
            if d in STRAY_DIRS:
                victims.append(os.path.join(dirpath, d))
                dirnames.remove(d)
        for f in filenames:
            if f in STRAY_FILES or f.endswith(STRAY_EXT):
                victims.append(os.path.join(dirpath, f))
    for v in victims:
        plan.append(("strip-artifacts", f"delete {rel(root, v)}"))
        if apply_:
            shutil.rmtree(v, ignore_errors=True) if os.path.isdir(v) else os.remove(v)


SCRIPTS = ("solution/solve.sh", "tests/test.sh")


def r_crlf(root, apply_, plan):
    for s in SCRIPTS:
        p = os.path.join(root, s)
        if not os.path.isfile(p):
            continue
        b = open(p, "rb").read()
        if b"\r\n" in b:
            plan.append(("crlf", f"normalise CRLF -> LF in {s}"))
            if apply_:
                open(p, "wb").write(b.replace(b"\r\n", b"\n"))


def r_execbit(root, apply_, plan):
    for s in SCRIPTS:
        p = os.path.join(root, s)
        if os.path.isfile(p) and not os.access(p, os.X_OK):
            plan.append(("execbit", f"chmod +x {s}"))
            if apply_:
                m = os.stat(p).st_mode
                os.chmod(p, m | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def r_shebang(root, apply_, plan):
    for s in SCRIPTS:
        p = os.path.join(root, s)
        if not os.path.isfile(p):
            continue
        first = open(p, encoding="utf-8", errors="replace").readline()
        if not first.startswith("#!"):
            plan.append(("shebang",
                         f"REPORT ONLY: {s} has no shebang — add '#!/usr/bin/env bash' by hand "
                         "and confirm bash exists in the image (Alpine ships only ash)"))


REPAIRS = [
    ("rename", r_rename), ("sync-statement", r_sync_statement), ("toml", r_toml),
    ("compose-network", r_compose), ("strip-artifacts", r_artifacts),
    ("crlf", r_crlf), ("execbit", r_execbit), ("shebang", r_shebang),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--apply", action="store_true", help="actually make the changes")
    ap.add_argument("--dry-run", action="store_true", help="explicit no-op (the default)")
    ap.add_argument("--only", help="comma-separated repair names to run")
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    if not os.path.isfile(os.path.join(root, "task.toml")):
        sys.exit(f"error: {root} has no task.toml — point at the task root")
    apply_ = a.apply and not a.dry_run
    only = set(x.strip() for x in a.only.split(",")) if a.only else None

    plan = []
    for name, fn in REPAIRS:
        if only and name not in only:
            continue
        fn(root, apply_, plan)

    mode = "APPLIED" if apply_ else "DRY RUN (pass --apply to make these changes)"
    print(f"fix_common — {mode}")
    print(f"task root: {root}\n")
    if not plan:
        print("nothing to repair mechanically.")
    else:
        for kind, desc in plan:
            print(f"  [{kind}] {desc}")
    print()
    print("Not covered here — do these by hand per reference/fix-playbooks.md:")
    print("  F1 over-prescription   F2 LLM tone      F3 coverage gaps   F4 faithfulness")
    print("  F5 <10 f2p tests       F6 auto-REMOVE   F7 leakage         F8 oracle")
    print("  F9 git (use git_hygiene.sh --fix)       F10 tests.patch regeneration")
    print("  F11 Dockerfile installs                 F13 difficulty")
    print()
    print("After applying: re-run check_task.py AND redo the requirement<->assertion worksheet.")


if __name__ == "__main__":
    main()
