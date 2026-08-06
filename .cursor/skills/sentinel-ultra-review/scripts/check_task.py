#!/usr/bin/env python3
"""Mechanical Sentinel Ultra checks over a Harbor task directory.

Every check below is traceable to a rule in ../reference/. Nothing here is invented.

Usage:
    python3 check_task.py <task-root> [--json out.json] [--md report.md] [--no-git]

Exit codes:  0 = no FIXABLE/NOT_FIXABLE findings   1 = findings   2 = usage/IO error

Severities
  NOT_FIXABLE  forces the Not-Fixable verdict (PR scope, or a listed environment issue)
  FIXABLE      must be corrected before submission; drives the Fixable verdict
  ADVISORY     scored by the judge / read by the reviewer, but doesn't flip the verdict
  INFO         context only
"""
import argparse
import json
import os
import re
import subprocess
import sys

# ---------------------------------------------------------------- toml loading
try:
    import tomllib  # py311+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


def load_toml(path):
    raw = open(path, "rb").read()
    if tomllib:
        try:
            return tomllib.loads(raw.decode("utf-8", "replace")), None
        except Exception as e:
            return None, f"could not parse task.toml: {e}"
    # minimal fallback parser: sections + scalar/list assignments
    data, section = {}, None
    for line in raw.decode("utf-8", "replace").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.match(r"^\[([^\]]+)\]$", line)
        if m:
            section = m.group(1)
            data.setdefault(section, {})
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s*=\s*(.+)$", line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if v.startswith("[") and v.endswith("]"):
            val = [x.strip().strip('"\'') for x in v[1:-1].split(",") if x.strip()]
        elif v.lower() in ("true", "false"):
            val = v.lower() == "true"
        elif re.fullmatch(r"-?\d+", v):
            val = int(v)
        else:
            val = v.strip('"\'')
        (data.setdefault(section, {}) if section else data)[k] = val
    return data, None


# ---------------------------------------------------------------- findings
FINDINGS = []


def add(fid, severity, category, where, summary, evidence, rule, fix):
    FINDINGS.append({
        "id": fid, "severity": severity, "category": category, "where": where,
        "summary": summary, "evidence": evidence, "rule": rule, "fix": fix,
    })


def read(path, binary=False):
    try:
        if binary:
            return open(path, "rb").read()
        return open(path, "r", encoding="utf-8", errors="replace").read()
    except Exception:
        return None


def lineno(text, idx):
    return text.count("\n", 0, idx) + 1


def find_all(text, pattern, flags=re.I):
    return [(m.start(), m.group(0)) for m in re.finditer(pattern, text, flags)]


# ---------------------------------------------------------------- 1. structure
REQUIRED = {
    "instruction.md": "file",
    "task.toml": "file",
    "environment/Dockerfile": "file",
    "environment/problem_statement.md": "file",
    "environment/repo": "dir",
    "solution/solve.sh": "file",
    "solution/golden.patch": "file",
    "tests/test.sh": "file",
    "tests/tests.patch": "file",
    "tests/config.json": "file",
}
VARIANTS = {
    "solution/golden.patch": ["solution/solution.patch", "solution/init_state.patch"],
    "tests/tests.patch": ["tests/test.patch"],
    "tests/config.json": ["environment/config.json", "config.json"],
}


def resolve(root, rel):
    """Return the actual path for a required artifact, honouring known variants."""
    p = os.path.join(root, rel)
    if os.path.exists(p):
        return p, None
    for alt in VARIANTS.get(rel, []):
        ap = os.path.join(root, alt)
        if os.path.exists(ap):
            return ap, alt
    return None, None


def check_structure(root):
    paths = {}
    for rel, kind in REQUIRED.items():
        p, variant = resolve(root, rel)
        ok = p is not None and (os.path.isdir(p) if kind == "dir" else os.path.isfile(p))
        paths[rel] = p if ok else None
        if not ok:
            add("S1", "FIXABLE", "Environment", rel,
                f"Required Harbor artifact missing: {rel}",
                "not found in the bundle (and no known variant name present)",
                "Harbor Framework - Task Structure",
                "Restore the file. If the whole component is absent the bundle is incomplete - "
                "re-download and re-unpack before reviewing.")
        elif variant:
            sev = "FIXABLE" if rel in ("solution/golden.patch", "tests/tests.patch") else "ADVISORY"
            rule = ("Harbor Framework - 'If the solution/ folder contains solution.patch "
                    "instead of golden.patch, rename it to golden.patch'"
                    if "golden" in rel else
                    "Harbor Framework - Task Structure (canonical Harbor layout)")
            add("S2", sev, "Environment", variant,
                f"Non-canonical filename: {variant}",
                f"found {variant}, Harbor expects {rel}", rule,
                f"Rename {variant} -> {rel} and update any reference in test.sh / solve.sh / "
                "config.json. Record the rename in Files Changed.")
    return paths


# ---------------------------------------------------------------- 2. task.toml
LIMITS = {
    "cpus": ("in", [2, 4]),
    "memory_mb": ("range", (2048, 16384)),
    "storage_mb": ("range", (5120, 10240)),
    "gpus": ("eq", 0),
    "build_timeout_sec": ("max", 1800),
}


def check_task_toml(root, paths):
    p = paths.get("task.toml")
    if not p:
        return {}
    data, err = load_toml(p)
    if err or data is None:
        add("T0", "FIXABLE", "Environment", "task.toml", "task.toml does not parse", err or "",
            "Harbor Framework - Task Metadata", "Fix the TOML syntax.")
        return {}

    env = data.get("environment", {}) or {}
    agent = data.get("agent", {}) or {}
    ver = data.get("verifier", {}) or {}
    meta = data.get("metadata", {}) or {}

    for key, (kind, bound) in LIMITS.items():
        if key not in env:
            add("T1", "FIXABLE", "Environment", "task.toml [environment]",
                f"[environment].{key} is not set", "missing",
                "Harbor Framework - [environment] resources",
                f"Set {key} within the published limit.")
            continue
        v = env[key]
        bad = ((kind == "in" and v not in bound) or
               (kind == "range" and not (bound[0] <= v <= bound[1])) or
               (kind == "eq" and v != bound) or
               (kind == "max" and v > bound))
        if bad:
            if kind == "in":
                want = f"one of {bound}"
            elif kind == "range":
                want = f"{bound[0]}..{bound[1]}"
            elif kind == "eq":
                want = f"== {bound}"
            else:
                want = f"<= {bound}"
            add("T2", "FIXABLE", "Environment", "task.toml [environment]",
                f"[environment].{key} = {v} is outside the allowed limit ({want})",
                f"{key} = {v}", "Harbor Framework - [environment] resources",
                f"Set {key} to {want}.")

    if env.get("network_mode") != "public":
        add("T3", "FIXABLE", "Environment", "task.toml [environment]",
            "[environment].network_mode must be \"public\"",
            f"network_mode = {env.get('network_mode')!r}",
            "Harbor Framework / FAQ - network_mode is set per block",
            'Set network_mode = "public". Do not strip the field.')
    if agent.get("network_mode") != "allowlist":
        add("T4", "FIXABLE", "Environment", "task.toml [agent]",
            "[agent].network_mode must be \"allowlist\"",
            f"network_mode = {agent.get('network_mode')!r}",
            "Harbor Framework / FAQ", 'Set network_mode = "allowlist".')
    hosts = agent.get("allowed_hosts")
    if hosts != ["api.portkey.ai"]:
        add("T5", "FIXABLE", "Environment", "task.toml [agent]",
            "[agent].allowed_hosts must be [\"api.portkey.ai\"]",
            f"allowed_hosts = {hosts!r}", "Harbor Framework / FAQ",
            'Set allowed_hosts = ["api.portkey.ai"].')
    if ver.get("network_mode") != "no-network":
        add("T6", "FIXABLE", "Environment", "task.toml [verifier]",
            "[verifier].network_mode must be \"no-network\"",
            f"network_mode = {ver.get('network_mode')!r}",
            "Harbor Framework / FAQ - the verifier runs airgapped",
            'Set network_mode = "no-network".')

    at = agent.get("timeout_sec")
    if at is None:
        add("T7", "ADVISORY", "Environment", "task.toml [agent]",
            "[agent].timeout_sec not set", "missing", "Harbor Framework - [agent]",
            "Set it; max 7200. Set generously rather than tight - a low ceiling fails tasks "
            "that would otherwise pass.")
    elif at > 7200:
        add("T8", "FIXABLE", "Environment", "task.toml [agent]",
            f"[agent].timeout_sec = {at} exceeds the maximum 7200", f"timeout_sec = {at}",
            "Harbor Framework - [agent]", "Lower to <= 7200.")
    vt = ver.get("timeout_sec")
    if vt is not None and vt > 1800:
        add("T9", "FIXABLE", "Environment", "task.toml [verifier]",
            f"[verifier].timeout_sec = {vt} exceeds the maximum 1800", f"timeout_sec = {vt}",
            "Harbor Framework - [verifier]", "Lower to <= 1800.")

    src = meta.get("source")
    if not src:
        add("T10", "FIXABLE", "Environment", "task.toml [metadata]",
            "[metadata].source is missing - the task has no PR anchor",
            "source not set", "Harbor Framework - [metadata]; Guidelines - PR scope rules",
            "Set source to the URL of the PR/commit/issue the task derives from. The judge's "
            "packaging axis cross-checks metadata against task content.")
    elif not re.match(r"^https?://", str(src)):
        add("T11", "ADVISORY", "Environment", "task.toml [metadata]",
            "[metadata].source does not look like a URL", f"source = {src!r}",
            "Harbor Framework - [metadata]", "Use the full PR/commit/issue URL.")
    for k in ("category", "difficulty_explanation"):
        if not meta.get(k):
            add("T12", "ADVISORY", "Environment", "task.toml [metadata]",
                f"[metadata].{k} is missing", "not set", "Harbor Framework - [metadata]",
                f"Set {k} accurately - the packaging axis cross-checks it against content.")

    # docker_compose.yaml must not carry network_mode = "none"
    for cand in ("docker_compose.yaml", "docker-compose.yaml",
                 "environment/docker_compose.yaml", "environment/docker-compose.yaml"):
        dc = os.path.join(root, cand)
        if os.path.isfile(dc):
            txt = read(dc) or ""
            if re.search(r'network_mode\s*[:=]\s*["\']?none', txt, re.I):
                add("T13", "FIXABLE", "Environment", cand,
                    'docker_compose.yaml still sets network_mode = "none"',
                    "found network_mode none", "FAQ - Which network_mode should my task.toml use?",
                    "Remove the network_mode = \"none\" line entirely.")
    return {"env": env, "agent": agent, "verifier": ver, "metadata": meta}


# ---------------------------------------------------------------- 3. instruction
PRESCRIPTIVE = [
    (r"where to look", "'Where to look:' file list"),
    (r"the tests? (?:reference|expect|use|check for) this name", "'the tests reference this name'"),
    (r"this file validates", "'this file validates the fix'"),
    (r"\bthe (?:hidden )?tests? (?:file )?(?:is|are) (?:named|called)", "names the hidden test"),
    (r"\b(?:test_[a-z0-9_]{6,}|tests?/[\w/]+\.py)\b", "names a specific test id/file"),
    (r"\bfixture (?:file )?(?:named|called|at)\b", "names a grading fixture"),
    (r"\bcassette\b", "names a cassette (verifier internal)"),
    (r"\bthe verifier\b", "explains verifier internals"),
    (r"\broot cause (?:is|analysis)\b", "hands over root-cause analysis"),
    (r"\bthe bug is in\b", "file localization hint"),
    (r"\bmodify the .{0,40}function\b", "names the exact function to edit"),
    (r"\bstep \d\b.{0,60}\bstep \d\b", "ordered how-to steps"),
]
LLM_TELLS = [
    (r"\bthe system shall\b", "robotic 'The system shall'"),
    (r"\bit is required that\b", "robotic 'It is required that'"),
    (r"\bthis task requires you to\b", "template scaffolding"),
    (r"\byour task is to\b", "template scaffolding"),
    (r"\bin conclusion\b", "essay filler"),
    (r"\b(?:delve|leverage|utilize|robust and scalable)\b", "LLM register"),
    (r"^#+\s*(?:overview|requirements|deliverables|acceptance criteria)\s*$", "generated section triad"),
    (r"\bcomprehensive(?:ly)?\b.{0,30}\bsolution\b", "LLM register"),
]
LEAK = [
    (r"https?://\S*github\.com/\S+/(?:pull|pulls)/\d+", "PR URL"),
    (r"https?://\S*github\.com/\S+/commit/[0-9a-f]{7,40}", "commit URL"),
    (r"https?://\S*(?:gitlab|bitbucket)\.\S+/(?:merge_requests|pull-requests)/\d+", "MR/PR URL"),
    (r"\bPR\s*#?\d{2,6}\b", "PR number"),
    (r"\b(?:pull request|merge request)\s*#?\d{2,6}\b", "PR number"),
    (r"\b[0-9a-f]{40}\b", "40-char commit SHA"),
    (r"\bgolden\.patch\b|\bgold(?:en)? patch\b", "reference to the golden patch"),
    (r"\bground_truth\b", "reference to ground truth"),
    (r"\bfixes\s+#\d+\b", "upstream issue reference"),
]


def check_instruction(root, paths):
    p = paths.get("instruction.md")
    if not p:
        return None
    txt = read(p) or ""

    for pat, label in PRESCRIPTIVE:
        for idx, hit in find_all(txt, pat):
            add("X1", "FIXABLE", "Instructions", f"instruction.md:{lineno(txt, idx)}",
                f"Overly prescriptive / exposes verifier internals - {label}",
                repr(hit[:120]),
                "Guidelines 2 Clarity & No Leakage - 'Signs an instruction is overly prescriptive'",
                "Rewrite to describe user- or API-visible behavior instead of implementation. "
                "See fix-playbooks.md F1.")
    for pat, label in LLM_TELLS:
        for idx, hit in find_all(txt, pat, re.I | re.M):
            add("X2", "ADVISORY", "Instructions", f"instruction.md:{lineno(txt, idx)}",
                f"Reads as templated/AI-generated - {label}", repr(hit[:120]),
                "Guidelines 4 Authenticity - 'Reads like a real engineering ask'",
                "Pick one persona (Slack / ticket / memo / email / acceptance criteria) and "
                "rewrite in it. See fix-playbooks.md F2.")
    for pat, label in LEAK:
        for idx, hit in find_all(txt, pat):
            add("L1", "FIXABLE", "Instructions", f"instruction.md:{lineno(txt, idx)}",
                f"Solution leakage - {label} in the instruction", repr(hit[:120]),
                "Guidelines 2 - No leakage: 'PR URLs, titles, numbers, or commit SHAs'",
                "Remove it. The PR URL belongs in task.toml [metadata].source only. "
                "See fix-playbooks.md F7.")

    words = len(re.findall(r"\w+", txt))
    if words < 80:
        add("X3", "ADVISORY", "Instructions", "instruction.md",
            f"Instruction is very short ({words} words)", f"{words} words",
            "Guidelines 1 Solvability - solvable from the instruction alone",
            "Confirm every requirement the tests grade is actually stated. Short instructions "
            "are the usual cause of faithfulness defects.")

    # problem_statement.md must be byte-identical
    ps = paths.get("environment/problem_statement.md")
    if ps:
        a, b = read(p, binary=True), read(ps, binary=True)
        if a is not None and b is not None and a != b:
            add("P1", "FIXABLE", "Environment", "environment/problem_statement.md",
                "problem_statement.md is not an exact copy of instruction.md",
                f"instruction.md {len(a)} bytes vs problem_statement.md {len(b)} bytes",
                "Guidelines - Environment: 'problem_statement.md must be an exact copy of "
                "instruction.md'",
                "cp instruction.md environment/problem_statement.md  (re-copy after EVERY "
                "instruction edit)")
        if b is not None:
            pst = b.decode("utf-8", "replace")
            for pat, label in LEAK:
                for idx, hit in find_all(pst, pat):
                    add("L2", "FIXABLE", "Environment",
                        f"environment/problem_statement.md:{lineno(pst, idx)}",
                        f"Solution leakage - {label} inside the environment", repr(hit[:120]),
                        "Guidelines 2 - No leakage: environment spoilers",
                        "Remove it, then re-sync with instruction.md.")
    return txt


# ---------------------------------------------------------------- 4. tests
def parse_patch(text):
    """-> {target_path: {'added': [lines], 'removed': [lines], 'new_file': bool}}"""
    files, cur = {}, None
    for line in (text or "").splitlines():
        m = re.match(r"^\+\+\+ (?:b/)?(.+)$", line)
        if m:
            path = m.group(1).strip()
            if path != "/dev/null":
                cur = files.setdefault(path, {"added": [], "removed": [], "new_file": False})
            continue
        if line.startswith("diff --git"):
            cur = None
            continue
        if line.startswith("new file mode"):
            # applies to the next +++ header; stash on a pending flag
            files.setdefault("__pending_new__", {"added": [], "removed": [], "new_file": True})
            continue
        if cur is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            cur["added"].append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            cur["removed"].append(line[1:])
    files.pop("__pending_new__", None)
    # second pass for new-file detection (header order: diff --git / new file mode / --- / +++)
    blocks = re.split(r"(?m)^diff --git ", text or "")
    for b in blocks[1:]:
        m = re.search(r"^\+\+\+ (?:b/)?(.+)$", b, re.M)
        if m and m.group(1).strip() in files:
            files[m.group(1).strip()]["new_file"] = bool(re.search(r"^new file mode", b, re.M))
    return files


AUTO_REMOVE = [
    ("silent-skip", r"@pytest\.mark\.skip(?:if)?|unittest\.skip|pytest\.skip\(|\.skip\b",
     "Silent skip",
     "Guidelines/Tasking Guide - auto-REMOVE pattern 'Silent skip'",
     "Delete the skip. If a dependency is missing the test must FAIL, not skip. Bake the "
     "dependency into the verifier image."),
    ("silent-skip-import", r"except\s+ImportError\s*:",
     "Silent skip via ImportError guard",
     "auto-REMOVE 'Silent skip' - catching ImportError and setting the module to None",
     "Remove the guard and install the dependency in the image."),
    ("fail-open", r"except\s+(?:Exception|BaseException)?\s*(?:as\s+\w+\s*)?:\s*(?:pass|return)\b",
     "Fail-open (broad except that swallows failure)",
     "auto-REMOVE 'Fail-open'; checklist: 'Don't wrap test bodies in broad try/except - ever'",
     "Let the exception propagate. A missing or malformed artifact must fail the suite."),
    ("fail-open-guard", r"if\s+not\s+[\w.\[\]'\"()]*\.exists\(\)\s*:\s*return",
     "Fail-open (early return when the artifact is absent)",
     "auto-REMOVE 'Fail-open'",
     "Assert the artifact exists AND assert its contents; never return early."),
    # source-scan handled by emit_source_text_ratio_findings (ratio-aware V9 extension)
    ("wallclock", r"\b(?:datetime\.(?:now|utcnow|today)|time\.time|date\.today)\s*\(",
     "Wall-clock dependence (non-deterministic test)",
     "Guidelines - 'Deterministic and fast'; reviewer tag 'Time-Based Tests'",
     "Freeze or inject the clock. Wall-clock values embedded in expectations make the task "
     "fail on a future run."),
    ("unseeded-random", r"\b(?:random\.(?:random|randint|choice|shuffle|sample)|np\.random\.(?!seed))",
     "Randomness in tests",
     "Guidelines - 'Tests must use deterministic inputs, seeds, and assertions'",
     "Seed it explicitly, or replace with fixed inputs."),
    ("network", r"\b(?:requests\.(?:get|post|put)|urllib\.request\.urlopen|httpx\.(?:get|post)|"
                r"socket\.create_connection)\s*\(",
     "Network access from a test (the verifier is airgapped)",
     "Harbor Framework - the verifier runs fully airgapped",
     "Bake fixtures/mock data into the verifier image; never reach the network at test time."),
    ("oracle-dep", r"\bgolden\.patch\b|\bgolden_patch\b|\bground_truth\b|solution/",
     "Test depends on solution-side artifacts",
     "Guidelines - 'Independent of the oracle'",
     "Tests must not import/call the golden solution or compare against files created only by "
     "the solution."),
]


# ---------------------------------------------------------------- grading config (V15 / V16)


def resolve_allow_extra_failures(cfg):
    """Prefer nested grading.allow_extra_failures; default False when absent."""
    grading = cfg.get("grading") if isinstance(cfg.get("grading"), dict) else {}
    if grading.get("allow_extra_failures") is not None:
        return bool(grading.get("allow_extra_failures"))
    if cfg.get("allow_extra_failures") is not None:
        return bool(cfg.get("allow_extra_failures"))
    return False


def collect_execution_command_text(cfg, test_sh_text=""):
    chunks = []
    for src in (cfg.get("execution") if isinstance(cfg.get("execution"), dict) else {},
                cfg.get("grading") if isinstance(cfg.get("grading"), dict) else {},
                cfg if isinstance(cfg, dict) else {}):
        for key in ("commands", "command"):
            v = src.get(key)
            if isinstance(v, str) and v.strip():
                chunks.append(v)
            elif isinstance(v, list):
                chunks.extend(str(x) for x in v if str(x).strip())
    if test_sh_text:
        chunks.append(test_sh_text)
    return "\n".join(chunks)


_TEST_PATH_REF = re.compile(
    r"(?ix)(?:^|[\s\"'=])("
    r"(?:[\w.\-]+/)*(?:test_[\w./\-]+|tests?/[\w./\-]+|[\w.\-]+_test\.py|"
    r"[\w.\-]+\.test\.[a-z]+|Test[\w]+\.java)"
    r"(?:::[^\s\"']+)?"
    r")"
)

# Shell / harness noise that looks vaguely path-like but is not a suite selector.
_TEST_REF_NOISE_BASENAMES = frozenset({
    "config.json", "tests.patch", "test.sh", "grade.py", "TEST_DESIGN.md",
    "metadata.json", "problem_statement.md", "instruction.md",
})
_TEST_REF_CODE_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs", ".kt")


def _is_plausible_test_suite_ref(ref: str) -> bool:
    """True only for real test files / pytest|jest node ids — not shell vars or config paths."""
    if not ref:
        return False
    r = ref.strip().strip("\"'")
    if not r or "${" in r or r.startswith("$"):
        return False
    bare = r.split("::")[0].split("/")[-1]
    if re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", bare):
        return False
    if bare in _TEST_REF_NOISE_BASENAMES:
        return False
    path_part = r.split("::")[0].lstrip("./")
    base = os.path.basename(path_part)
    if base in _TEST_REF_NOISE_BASENAMES:
        return False
    lower = base.lower()
    if lower.endswith((".json", ".patch", ".md", ".toml", ".yml", ".yaml", ".txt", ".sh")):
        return False
    if "::" in r:
        return True
    if re.search(r"(^|/)(tests?/|test_)|_test\.[a-z]+$|\.test\.[a-z]+$", path_part):
        return True
    if any(path_part.endswith(ext) for ext in _TEST_REF_CODE_EXTS):
        return True
    return False


def extract_test_path_refs(command_blob):
    """Suite selectors from execution commands / test.sh (not bare `pytest`).

    Only keeps refs that resolve to real test files or pytest/jest node ids.
    Ignores shell variables, config.json, tests.patch, and harness noise.
    """
    refs = []
    for m in _TEST_PATH_REF.finditer(command_blob or ""):
        ref = m.group(1).strip().strip("\"'")
        if _is_plausible_test_suite_ref(ref) and ref not in refs:
            refs.append(ref)
    for m in re.finditer(r"(?i)(?:-s|--start-directory|--pyargs)\s+(\S+)", command_blob or ""):
        ref = m.group(1).strip().strip("\"'")
        if _is_plausible_test_suite_ref(ref) and ref not in refs:
            refs.append(ref)
    return refs


def unrelated_suite_paths(path_refs, patch_files):
    """Refs that are not the patch's own tests (nor a parent/child of those paths)."""
    patch_norm = {p.lstrip("./") for p in patch_files}
    unrelated = []
    for ref in path_refs:
        r = ref.lstrip("./").split("::")[0]
        covered = False
        for pf in patch_norm:
            if pf == r or pf.startswith(r.rstrip("/") + "/") or r.startswith(pf.rstrip("/") + "/"):
                covered = True
                break
            if os.path.basename(pf) == os.path.basename(r) or (
                os.path.splitext(os.path.basename(pf))[0] == os.path.splitext(os.path.basename(r))[0]
            ):
                covered = True
                break
        if not covered:
            unrelated.append(ref)
    return unrelated


def emit_grading_config_findings(cfg, cfg_where, patch_files, test_sh_text=""):
    """V15: allow_extra_failures=true. V16: false + unrelated suite paths gate reward."""
    allow_extra = resolve_allow_extra_failures(cfg)
    if allow_extra:
        add("V15", "FIXABLE", "Tests", cfg_where,
            "allow_extra_failures=true — ungraded tests can fail without losing reward "
            "(coverage gap risk)",
            "allow_extra_failures=true",
            "Grading config — reward must be gated by the full scoped suite; "
            "allow_extra_failures=true hides requirements in ungraded tests",
            "Set allow_extra_failures=false and scope the execution command to the "
            "task's own tests (paths introduced by tests.patch).")
        return
    # Prefer execution.commands from config; fall back to filtered test.sh refs
    exec_blob = collect_execution_command_text(cfg, test_sh_text="")
    refs = extract_test_path_refs(exec_blob)
    if not refs and test_sh_text:
        refs = extract_test_path_refs(test_sh_text)
    unrelated = unrelated_suite_paths(refs, patch_files)
    if unrelated:
        add("V16", "FIXABLE", "Tests", cfg_where,
            "allow_extra_failures=false but execution command references test paths "
            "not in tests.patch — unrelated suites gate the reward (faithfulness / "
            "hidden-requirement risk)",
            "unrelated=" + ", ".join(unrelated[:8])
            + (f" (+{len(unrelated) - 8} more)" if len(unrelated) > 8 else "")
            + f"; patch_files={len(patch_files)}",
            "Grading config — with allow_extra_failures=false the verifier enforces "
            "every test the command runs; legacy/unrelated suites become hidden reqs",
            "Scope execution.commands / test.sh to only the tests introduced by "
            "tests.patch (remove unrelated suite paths).")


# ---------------------------------------------------------------- source-text ratio (V9 extension)


_SOURCE_TEXT_LINE = re.compile(
    r"(?ix)"
    r"(?:read_text\s*\(|\.read\s*\(|open\s*\([^)]*\)\s*\.read\s*\()"
    r".{0,120}(?:\bin\b|find\s*\(|search\s*\(|match\s*\(|findall\s*\(|assertIn|assertRegex)"
    r"|assert(?:In|Regex)?\s*\(\s*[\'\"][^\'\"]+[\'\"]\s*,\s*"
    r"(?:src|source|content|code|text|body|cmake|cmakelists|\w+_src|\w+_text)\b"
    r"|assert\s+[\'\"][^\'\"]+[\'\"]\s+in\s+"
    r"(?:src|source|content|code|text|body|cmake|cmakelists|\w+_src|\w+_text)\b"
    r"|re\.(?:search|match|findall|fullmatch)\s*\([^)]*"
    r"(?:src|source|content|code|text|body|read_text|\.read\()"
    r"|(?:src|source|content|code|text|body)\s*=\s*(?:.*\.(?:read_text|read)\s*\()"
)

_BEHAVIOURAL_LINE = re.compile(
    r"(?ix)"
    r"(?:subprocess\.|pytest\.raises|assertRaises(?:Regex)?|assertWarns|"
    r"self\.assert(?:equal|true|false|is|count|almost|list|dict|set|tuple)|"
    r"assert\s+(?![\'\"][^\'\"]+[\'\"]\s+in\s+(?:src|source|content|code|text)\b)"
    r"(?:\w+\s*\(|not\s+\w|\w+\.\w+)|"
    r"(?:\.call\s*\(|\.invoke\s*\(|\.run\s*\(|\.execute\s*\(|\.main\s*\())"
)

_ASSERTISH_LINE = re.compile(
    r"(?ix)^\s*(?:assert\b|self\.assert|pytest\.raises|assertRaises|expect\(|should\.)"
)

# Assignment from reading repo / source-file text (taint source).
_FILE_READ_ASSIGN = re.compile(
    r"(?ix)^\s*"
    r"([A-Za-z_][\w]*)\s*=\s*"
    r"(?:"
    r"Path\s*\([^)]*\)\s*\.\s*(?:read_text|read_bytes|open)\s*\("
    r"|open\s*\([^)]*\)\s*\.\s*(?:read|readlines)\s*\("
    r"|(?:[\w.]+)\.(?:read_text|read_bytes|readlines)\s*\("
    r"|[A-Za-z_][\w]*\s*\.\s*read\s*\(\s*\)"
    r")"
)

_FILE_READ_ASSIGN_ALT = re.compile(
    r"(?ix)^\s*"
    r"([A-Za-z_][\w]*)\s*=\s*"
    r"(?:"
    r"open\s*\(\s*[\'\"][^\'\"]+[\'\"][^)]*\)\s*\.\s*(?:read|readlines)\s*\("
    r"|Path\s*\(\s*[\'\"][^\'\"]+[\'\"]\s*\)\s*\.\s*read_text\s*\("
    r")"
)

_FILE_READ_WITH = re.compile(
    r"(?ix)\bopen\s*\([^)]*\)\s+as\s+([A-Za-z_][\w]*)"
)
_FILE_READ_FROM_HANDLE = re.compile(
    r"(?ix)^\s*([A-Za-z_][\w]*)\s*=\s*([A-Za-z_][\w]*)\s*\.\s*(?:read|readlines)\s*\("
)
_ASSIGN_ANY = re.compile(r"(?ix)^\s*([A-Za-z_][\w]*)\s*=\s*(.+)$")
_HELPER_CALL_ASSIGN = re.compile(
    r"(?ix)^\s*([A-Za-z_][\w]*)\s*=\s*([A-Za-z_][\w]*)\s*\("
)

# Common local wrappers (d41a2c3a: `text = read("CMakeLists.txt")`).
_DEFAULT_FILE_READ_HELPERS = frozenset({
    "read", "read_file", "read_text", "read_source", "load_text", "load_source",
    "load_file", "slurp", "get_source", "get_text", "file_text", "repo_read",
})


def _iter_added_test_bodies(all_added):
    # Close only at the next test_* def so nested helpers stay inside the body.
    for m in re.finditer(r"(?m)^\s*(?:async\s+)?def\s+(test_\w+)\s*\([^)]*\)\s*:", all_added):
        start = m.end()
        nxt = re.search(r"(?m)^\s*(?:async\s+)?def\s+test_\w+\s*\(", all_added[start:])
        body = all_added[start:start + (nxt.start() if nxt else len(all_added))]
        yield m.group(1), body


def _file_read_helper_names(all_added: str) -> set:
    """Names of helpers that open/read repo files (module-level or nested)."""
    names = set(_DEFAULT_FILE_READ_HELPERS)
    for m in re.finditer(r"(?m)^\s*(?:async\s+)?def\s+([A-Za-z_][\w]*)\s*\([^)]*\)\s*:", all_added):
        name = m.group(1)
        if name.startswith("test_"):
            continue
        start = m.end()
        nxt = re.search(r"(?m)^\s*(?:async\s+)?def\s+", all_added[start:])
        body = all_added[start:start + (nxt.start() if nxt else min(2500, len(all_added) - start))]
        body = "\n".join(body.splitlines()[:50])
        if re.search(
            r"(?ix)\bopen\s*\(|\.read_text\s*\(|\.readlines\s*\(|\.read_bytes\s*\("
            r"|\.read\s*\(\s*\)",
            body,
        ):
            names.add(name)
    return names


def _tainted_file_text_vars(body: str, helpers: set | None = None) -> set:
    """Vars assigned from open/Path.read_text/readlines/helpers; propagate via RHS use."""
    helpers = set(helpers or _DEFAULT_FILE_READ_HELPERS)
    tainted: set = set()
    handles: set = set()
    for line in body.splitlines():
        if line.startswith("+"):
            line = line[1:]
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = _FILE_READ_ASSIGN.search(line) or _FILE_READ_ASSIGN_ALT.search(line)
        if m:
            tainted.add(m.group(1))
            continue
        m = _FILE_READ_WITH.search(line)
        if m:
            handles.add(m.group(1))
            continue
        m = _FILE_READ_FROM_HANDLE.search(line)
        if m and m.group(2) in handles:
            tainted.add(m.group(1))
            continue
        m = _HELPER_CALL_ASSIGN.match(line)
        if m and m.group(2) in helpers:
            tainted.add(m.group(1))
            continue
        # Propagate: any assignment whose RHS mentions a tainted var / handle read.
        m = _ASSIGN_ANY.match(line)
        if m:
            lhs, rhs = m.group(1), m.group(2)
            if _line_uses_tainted(rhs, tainted) or _line_uses_tainted(rhs, handles):
                tainted.add(lhs)
    return tainted


def _line_uses_tainted(line: str, tainted: set) -> bool:
    if not tainted:
        return False
    for name in tainted:
        if re.search(rf"(?<![\w.]){re.escape(name)}(?![\w])", line):
            return True
    return False


def classify_assertion_line(line, tainted=None):
    """Return 'source', 'behavioural', or None.

    Taint rule: if the line is an assertion that references a variable assigned from
    reading repo/source file text (open/read_text/readlines/helpers like read(path)),
    it is source-text even when the match uses re.search / assertEqual / etc.
    Those are not execution of the code under test.
    """
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    tainted = tainted or set()
    is_assert = bool(_ASSERTISH_LINE.search(s) or _SOURCE_TEXT_LINE.search(s))
    if not is_assert:
        return None
    if _line_uses_tainted(s, tainted):
        return "source"
    if _SOURCE_TEXT_LINE.search(s):
        return "source"
    if _BEHAVIOURAL_LINE.search(s) or _ASSERTISH_LINE.search(s):
        return "behavioural"
    return None


def analyze_source_text_ratios(all_added, f2p_ids=None):
    """Per-test source-text vs behavioural assertion counts and ratios."""
    f2p_ids = f2p_ids or []
    helpers = _file_read_helper_names(all_added)
    rows = []
    for name, body in _iter_added_test_bodies(all_added):
        tainted = _tainted_file_text_vars(body, helpers)
        source_n = behav_n = 0
        for line in body.splitlines():
            if line.startswith("+"):
                line = line[1:]
            kind = classify_assertion_line(line, tainted)
            if kind == "source":
                source_n += 1
            elif kind == "behavioural":
                behav_n += 1
        total = source_n + behav_n
        ratio = (source_n / total) if total else 0.0
        graded = (not f2p_ids) or any(name in str(t) for t in f2p_ids)
        rows.append({
            "test": name,
            "source": source_n,
            "behavioural": behav_n,
            "ratio": ratio,
            "graded": graded,
            "tainted_vars": sorted(tainted),
        })
    return rows



def emit_source_text_ratio_findings(tp_where, all_added, f2p_ids=None):
    """Extend V9 source-scan: per-test + suite-level FIXABLE; ADVISORY mixed; always report."""
    rows = analyze_source_text_ratios(all_added, f2p_ids)
    if not rows:
        return rows
    graded_rows = [r for r in rows if r["graded"]]
    suite_src = sum(r["source"] for r in graded_rows)
    suite_beh = sum(r["behavioural"] for r in graded_rows)
    suite_total = suite_src + suite_beh
    suite_ratio = (suite_src / suite_total) if suite_total else 0.0
    ratio_table = (
        f"suite_graded={suite_src}/{suite_total} (ratio={suite_ratio:.2f}); "
        + "; ".join(
            f"{r['test']}={r['source']}/{r['source'] + r['behavioural']} "
            f"(ratio={r['ratio']:.2f})"
            for r in rows
        )
    )
    pure = [r for r in graded_rows if r["source"] >= 1 and r["behavioural"] == 0]
    mixed_high = [
        r for r in graded_rows
        if r["behavioural"] >= 1 and r["ratio"] >= 0.5
    ]
    suite_fixable = suite_total > 0 and suite_ratio >= 0.5 and suite_src >= 1
    fixable_emitted = False
    if pure:
        add("V9", "FIXABLE", "Tests", tp_where,
            f"{len(pure)} graded test(s) use only source-text assertions "
            "(zero behavioural) — stub can pass; trivially gamed",
            ratio_table,
            "Guidelines - outcome-based tests; checklist: \"Don't assert on source code text\" "
            "(V9 source-scan ratio extension)",
            "Replace source-substring/regex checks with assertions that execute the code "
            "under test and check observable behaviour.")
        fixable_emitted = True
    if suite_fixable and not pure:
        add("V9", "FIXABLE", "Tests", tp_where,
            f"Graded suite source-text assertion ratio {suite_ratio:.2f} >= 0.5 "
            f"({suite_src}/{suite_total}) — verifier is predominantly source-scanning",
            ratio_table,
            "Guidelines - outcome-based tests; checklist: \"Don't assert on source code text\" "
            "(V9 suite-level source-scan ratio)",
            "Convert the suite toward behavioural assertions that execute the code under "
            "test; a source-restructuring contract still needs runnable checks, not regex-only.")
        fixable_emitted = True
    if mixed_high and not suite_fixable:
        add("V9", "ADVISORY", "Tests", tp_where,
            f"{len(mixed_high)} graded test(s) have source-text assertion ratio >= 0.5 "
            "(judgment call — may be defensible for source-restructuring contracts)",
            ratio_table,
            "Guidelines - prefer behavioural assertions; source-heavy suites risk "
            "faithfulness complaints",
            "Review whether each source check is required by an instruction-stated "
            "source contract; otherwise convert to behavioural asserts.")
    if not fixable_emitted and not mixed_high:
        add("V9", "INFO", "Tests", tp_where,
            "Source-text assertion ratios (no FIXABLE/ADVISORY threshold hit)",
            ratio_table,
            "Guidelines - outcome-based tests; checklist: \"Don't assert on source code text\"",
            "No action required unless ratios climb toward source-only tests.")
    return rows


def check_tests(root, paths, instruction_text):
    cfg_p = paths.get("tests/config.json")
    f2p, p2p = [], []
    cfg = {}
    if cfg_p:
        try:
            cfg = json.loads(read(cfg_p) or "{}")
        except Exception as e:
            cfg = {}
            add("V0", "FIXABLE", "Tests", os.path.relpath(cfg_p, root),
                "config.json does not parse", str(e),
                "Guidelines - Example config.json", "Fix the JSON.")
        def pick(key):
            """config.json ships as grading.fail_to_pass, fail_to_pass, or FAIL_TO_PASS."""
            for src in (cfg.get("grading") or {}, cfg):
                if not isinstance(src, dict):
                    continue
                for k, v in src.items():
                    if k.lower() == key and v:
                        return [v] if isinstance(v, str) else list(v)
            return []

        f2p, p2p = pick("fail_to_pass"), pick("pass_to_pass")

        if len(f2p) == 0:
            add("V1", "FIXABLE", "Tests", os.path.relpath(cfg_p, root),
                "fail_to_pass is empty or missing", f"fail_to_pass = {f2p!r}",
                "Glossary - 'fail_to_pass is the required, non-empty list'",
                "Populate it with the ids of the tests that fail pre-fix and pass post-fix.")
        elif len(f2p) < 10:
            add("V2", "FIXABLE", "Tests", os.path.relpath(cfg_p, root),
                f"Only {len(f2p)} fail-to-pass tests - at least 10 are required",
                f"fail_to_pass has {len(f2p)} entries",
                "Guidelines 3 Verifiability - 'At least 10 fail-to-pass tests'",
                f"Add {10 - len(f2p)}+ tests (target 10-20) covering requirements stated or "
                "reasonably implied in the instruction - never undescribed behavior. "
                "See fix-playbooks.md F5.")
        elif len(f2p) > 25:
            add("V3", "ADVISORY", "Tests", os.path.relpath(cfg_p, root),
                f"{len(f2p)} fail-to-pass tests - guidance suggests 10-20",
                f"fail_to_pass has {len(f2p)} entries",
                "Guidelines - 'ideally 10-20'",
                "Not a defect; just confirm the suite still finishes inside the verifier timeout.")
        if not p2p:
            add("V4", "ADVISORY", "Tests", os.path.relpath(cfg_p, root),
                "pass_to_pass is empty - no regression guard declared", "pass_to_pass = []",
                "Glossary - 'pass_to_pass is the regression guard'",
                "Declare the pre-existing tests that must keep passing.")

    # ---- tests.patch ----
    tp_p = paths.get("tests/tests.patch")
    patch_txt = read(tp_p) if tp_p else None
    added_test_fns = []
    if patch_txt:
        files = parse_patch(patch_txt)
        test_files = {k: v for k, v in files.items()
                      if re.search(r"(^|/)(tests?|spec)/|(^|/)test_[^/]*$|_test\.[a-z]+$|"
                                   r"\.test\.[a-z]+$|Test[A-Z]\w*\.java$", k)}
        non_test = [k for k in files if k not in test_files]
        if non_test:
            add("V5", "ADVISORY", "Tests", os.path.relpath(tp_p, root),
                "tests.patch touches non-test files",
                ", ".join(non_test[:6]) + (" ..." if len(non_test) > 6 else ""),
                "Tasking Guide - common trap: 'the patch touches a non-test file "
                "(e.g. CMakeLists.txt) that has since changed'",
                "Acceptable only for build wiring the new tests genuinely need. Confirm it "
                "still applies at base_commit_sha and carries no implementation of the fix.")

        for path_, info in files.items():
            if info["removed"] and not info["new_file"]:
                add("V6", "FIXABLE", "Tests", f"{os.path.relpath(tp_p, root)} -> {path_}",
                    "tests.patch DELETES lines from a pre-existing test file",
                    f"{len(info['removed'])} removed line(s) in {path_}",
                    "Tasking Guide - 'Never modify pre-existing (regression / pass-to-pass) "
                    "test files ... the harness checks they are byte-identical to the base commit'",
                    "Revert that file to its base_commit_sha content and add your coverage as "
                    "NEW test functions or NEW files instead.")

        added_lines = [l for f in files.values() for l in f["added"]]
        all_added = "\n".join(added_lines)
        added_test_fns = re.findall(r"^\s*(?:async\s+)?def\s+(test_\w+)", all_added, re.M)
        added_test_fns += re.findall(r"^\s*(?:it|test)\s*\(\s*['\"]([^'\"]+)", all_added, re.M)
        added_test_fns += re.findall(r"@Test\s*\n\s*public\s+void\s+(\w+)", all_added)
        if f2p and added_test_fns:
            names = set(added_test_fns)
            missing = [t for t in f2p
                       if not any(n in str(t) for n in names)]
            if missing:
                add("V7", "FIXABLE", "Tests", os.path.relpath(cfg_p or "tests/config.json", root),
                    f"{len(missing)} fail_to_pass id(s) do not correspond to any test added by "
                    "tests.patch",
                    "; ".join(str(m) for m in missing[:5]) + (" ..." if len(missing) > 5 else ""),
                    "Tasking Guide - the f2p tests are injected by applying tests.patch; ids "
                    "that don't exist fail every trial",
                    "Either add the missing tests to tests.patch or correct the ids in "
                    "config.json. Verify with a NOP run: every f2p id must actually FAIL "
                    "pre-patch.")
        if len(added_test_fns) < 10 and not f2p:
            add("V8", "FIXABLE", "Tests", os.path.relpath(tp_p, root),
                f"tests.patch adds only {len(added_test_fns)} test function(s) - at least 10 "
                "fail-to-pass tests are required",
                f"{len(added_test_fns)} test definitions found",
                "Guidelines 3 Verifiability", "See fix-playbooks.md F5.")

        # match against the joined added text so multi-line constructs
        # (`except Exception:\n    pass`) are caught too
        for key, pat, label, rule, fix in AUTO_REMOVE:
            hits = [m.group(0) for m in re.finditer(pat, all_added, re.M | re.S)]
            if hits:
                add("V9", "FIXABLE", "Tests", os.path.relpath(tp_p, root),
                    f"{label} in added test code",
                    "  |  ".join(" ".join(h.split())[:110] for h in hits[:3]),
                    rule, fix)

        # V9 source-scan (ratio-aware extension — replaces binary source-scan AUTO_REMOVE)
        emit_source_text_ratio_findings(os.path.relpath(tp_p, root), all_added, f2p)

        # pre-created artifact: exists() with no content/behavior assertion in the SAME test
        CONTENT = (r"read_text|read_bytes|json\.load|\.read\(\)|loads\(|"
                   r"len\s*\(.*\)\s*[=><]|==|!=|\bin\b|assert_called|>\s*0")
        bad_fns = []
        for m in re.finditer(r"(?m)^\s*(?:async\s+)?def\s+(test_\w+)\s*\([^)]*\)\s*:", all_added):
            start = m.end()
            nxt = re.search(r"(?m)^\s*(?:async\s+)?def\s+\w+\s*\(", all_added[start:])
            body = all_added[start:start + (nxt.start() if nxt else len(all_added))]
            if re.search(r"\.(?:exists|is_file|isfile|is_dir)\s*\(\)", body) and \
               not re.search(CONTENT, body):
                bad_fns.append(m.group(1))
        if bad_fns:
            add("V10", "FIXABLE", "Tests", os.path.relpath(tp_p, root),
                f"{len(bad_fns)} test(s) assert only that a path exists, with no content or "
                "behavior assertion - `touch`-ing the right filename would pass",
                ", ".join(bad_fns[:5]),
                "auto-REMOVE pattern 'Pre-created artifact passes'",
                "Pair EVERY existence check with an assertion on the artifact's contents or "
                "behavior.")

        # agent controls coverage
        for l in added_lines:
            if re.search(r"for\s+\w+\s+in\s+(?:json\.load|.*output.*|.*result.*)\b.*:", l) and \
               re.search(r"output|result|report", l, re.I):
                add("V11", "ADVISORY", "Tests", os.path.relpath(tp_p, root),
                    "Possible 'agent controls coverage' - test surface derived from produced "
                    "output rather than enumerated from the instruction",
                    l.strip()[:140],
                    "auto-REMOVE pattern 'Agent controls coverage'",
                    "Enumerate expected items from the instruction/environment, never from the "
                    "agent's own output.")
                break

        # verifier-only constants
        for l in added_lines:
            m = re.search(r"^\s*(?:EXPECTED|GOLDEN|REFERENCE)_\w*\s*=\s*(\d+|\[|\{|['\"])", l)
            if m:
                add("V12", "ADVISORY", "Tests", os.path.relpath(tp_p, root),
                    "Verifier-only constant the agent cannot derive from the instruction",
                    l.strip()[:140],
                    "Test-writing checklist: \"Don't embed verifier-only constants "
                    "(EXPECTED_COUNT = 47)\"",
                    "Either state the value in the instruction, or derive it from the "
                    "environment.")
                break

    # ---- test.sh ----
    ts_p = paths.get("tests/test.sh")
    ts = ""
    if ts_p:
        ts = read(ts_p) or ""
        if "reward" not in ts:
            add("V13", "FIXABLE", "Tests", "tests/test.sh",
                "test.sh never writes a reward", "no 'reward' reference found",
                "Harbor Framework - test.sh runs the suite and writes the reward to "
                "/logs/verifier/reward.txt",
                "Write 1.0 on success and 0.0 on failure, and make the exit code match.")
        if instruction_text and re.search(
                r"\b(CLI|command[- ]line|entry[- ]point|executable|daemon|service|endpoint|"
                r"subcommand|`[a-z][\w-]{2,}\s+\w+`)\b", instruction_text, re.I):
            if re.search(r"pytest|unittest|jest|go test|mvn|gradle", ts) and not re.search(
                    r"subprocess|\./|\bpython\s+-m\s+(?!pytest)|curl\s|http", ts + "\n".join(
                        l for f in parse_patch(patch_txt or "").values() for l in f["added"])):
                add("V14", "ADVISORY", "Tests", "tests/test.sh",
                    "Instruction describes a CLI/service/entry point, but the suite appears to "
                    "only exercise library internals",
                    "no entry-point invocation found in test.sh or the added tests",
                    "auto-REMOVE pattern 'No CLI/entry-point invocation'",
                    "Actually invoke the thing being built (subprocess the entry point / hit "
                    "the endpoint), not just its internals.")

    # ---- grading configuration (V15 / V16) ----
    if cfg_p and cfg:
        patch_files = list(parse_patch(patch_txt or "").keys()) if patch_txt else []
        emit_grading_config_findings(
            cfg, os.path.relpath(cfg_p, root), patch_files, test_sh_text=ts
        )
    return {"f2p": f2p, "p2p": p2p, "added_tests": added_test_fns}


# ---------------------------------------------------------------- 5. oracle
def check_oracle(root, paths):
    gp = paths.get("solution/golden.patch")
    stats = {}
    if gp:
        txt = read(gp) or ""
        files = parse_patch(txt)
        changed = [f for f in files if not re.search(r"(^|/)(tests?|spec)/", f)]
        added = sum(len(v["added"]) for v in files.values())
        removed = sum(len(v["removed"]) for v in files.values())
        stats = {"files": len(files), "code_files": len(changed),
                 "added": added, "removed": removed}
        if added + removed < 100:
            add("O1", "ADVISORY", "Oracle Solution", "solution/golden.patch",
                f"Oracle is small ({added} added / {removed} removed lines across "
                f"{len(files)} file(s)) - authenticity rule of thumb is ~100+ lines across 2+ files",
                f"+{added}/-{removed} in {len(files)} files",
                "Guidelines 4 Authenticity - 'the underlying fix is roughly 100+ lines across "
                "two or more files'",
                "If the task really is a trivial edit it is not authentic -> expand the PR "
                "scope (adding only). See fix-playbooks.md F13.")
        if len(files) < 2:
            add("O2", "ADVISORY", "Oracle Solution", "solution/golden.patch",
                f"Oracle touches only {len(files)} file(s)", f"{list(files)[:3]}",
                "Guidelines 4 Authenticity - 'across two or more files'",
                "Same as above - confirm the task is substantial and agentic.")
        if not changed and files:
            add("O3", "FIXABLE", "Oracle Solution", "solution/golden.patch",
                "golden.patch modifies only test files - it does not implement the fix",
                f"{list(files)[:4]}",
                "Guidelines - the oracle must implement the instruction",
                "The oracle must change implementation code. See fix-playbooks.md F8.")
        for pat, label in (
            (r"^\+.*\breturn\s+(?:\[|\{|['\"]).{0,80}#\s*(?:hardcode|expected)", "hardcoded answer"),
            (r"^\+.*\.max\(\)\s*(?:#.*today|as\s+today)", "fixture-specific shortcut"),
            (r"^\+.*\b(?:requests|urllib|httpx)\.", "live network call in the oracle"),
        ):
            for idx, hit in find_all(txt, pat, re.I | re.M):
                add("O4", "FIXABLE", "Oracle Solution", f"solution/golden.patch:{lineno(txt, idx)}",
                    f"Oracle gaming / robustness risk - {label}", repr(hit.strip()[:120]),
                    "Quality Check oracle axes - 'no gaming', 'robustness'",
                    "Litmus test: if the inputs were reshuffled within the spec, would this "
                    "oracle still produce the right answer? See fix-playbooks.md F8.")

    sh = paths.get("solution/solve.sh")
    if sh:
        txt = read(sh) or ""
        if not txt.startswith("#!"):
            add("O5", "FIXABLE", "Environment", "solution/solve.sh",
                "solve.sh has no shebang", "first line is not #!",
                "Guidelines - fixable env issue: 'Bad shell/shebang ... Script fails to exec'",
                "Add #!/usr/bin/env bash (and ensure bash exists in the image).")
        if not os.access(sh, os.X_OK):
            add("O6", "FIXABLE", "Environment", "solution/solve.sh",
                "solve.sh is not executable", "mode lacks +x",
                "Guidelines - fixable env issue: 'non-executable scripts'", "chmod +x solve.sh")
    return stats


# ---------------------------------------------------------------- 6. dockerfile
def check_dockerfile(root, paths):
    p = paths.get("environment/Dockerfile")
    if not p:
        return
    txt = read(p) or ""
    froms = re.findall(r"^\s*FROM\s+(\S+)", txt, re.M | re.I)
    for f in froms:
        if f.lower().endswith(":latest") or (":" not in f and "@" not in f):
            add("D1", "FIXABLE", "Environment", "environment/Dockerfile",
                f"Base image is not pinned to a concrete tag: {f}", f"FROM {f}",
                "Guidelines - fixable env issue 'Unpinned base image (FROM ...:latest)'",
                "Pin to a concrete tag or digest.")
    alpine = any("alpine" in f.lower() for f in froms) or "apk add" in txt
    if alpine:
        scripts = [paths.get("solution/solve.sh"), paths.get("tests/test.sh")]
        needs_bash = any((read(s) or "").startswith("#!/usr/bin/env bash") or
                         (read(s) or "").startswith("#!/bin/bash") for s in scripts if s)
        if needs_bash and not re.search(r"apk add[^\n]*\bbash\b", txt):
            add("D2", "FIXABLE", "Environment", "environment/Dockerfile",
                "Alpine image but bash is never installed, while solve.sh/test.sh use a bash "
                "shebang (Alpine ships only ash)",
                "no 'apk add ... bash' found",
                "Guidelines - fixable env issue 'Alpine image missing bash' (saw 55x)",
                "RUN apk add --no-cache bash")
    if not re.search(r"\btmux\b", txt):
        add("D3", "FIXABLE", "Environment", "environment/Dockerfile",
            "tmux is not installed - Harbor drives the agent/verifier inside a tmux pane",
            "no tmux install found",
            "Guidelines - fixable env issue 'tmux not installed in the task image'",
            "RUN apt-get update && apt-get install -y tmux   (or: apk add --no-cache tmux)")
    if not re.search(r"\basciinema\b", txt):
        add("D4", "ADVISORY", "Environment", "environment/Dockerfile",
            "asciinema is not installed - Harbor records the terminal session with it",
            "no asciinema install found",
            "Guidelines - fixable env issue 'asciinema not installed'",
            "RUN apt-get install -y asciinema  /  pip install asciinema  /  apk add asciinema")
    if re.search(r"apt-get\s+install", txt) and not re.search(r"apt-get\s+update", txt):
        add("D5", "FIXABLE", "Environment", "environment/Dockerfile",
            "apt-get install without a preceding apt-get update - non-reproducible build",
            "no 'apt-get update' found",
            "Tasking Guide - 'run apt-get update before installs'",
            "RUN apt-get update && apt-get install -y ...")
    for m in re.finditer(r"^\s*COPY\s+([^\s]+)\s", txt, re.M | re.I):
        src = m.group(1).strip()
        if any(ch in src for ch in "*?[$"):
            continue
        if not os.path.exists(os.path.join(root, "environment", src)) and \
           not os.path.exists(os.path.join(root, src)):
            sev = "FIXABLE"
            fix = ("Generate the file." if "frozen-requirements" in src
                   else "Add the file to environment/, or drop the COPY.")
            add("D6", sev, "Environment", "environment/Dockerfile",
                f"Dockerfile COPYs a path that is not in the bundle: {src}",
                f"COPY {src}",
                "Guidelines - fixable env issue 'Missing environment/frozen-requirements.txt "
                "(Dockerfile COPYs it but it's absent, saw 683x)'", fix)
    if re.search(r"^\s*(?:RUN\s+)?.*\b(?:curl|wget)\b.*\b(?:https?://)", txt, re.M) and \
       re.search(r"huggingface|\.bin\b|\.safetensors\b|models?/", txt, re.I):
        add("D7", "NOT_FIXABLE", "Environment", "environment/Dockerfile",
            "Large external model/artifact download at build time",
            "curl/wget of a model artifact",
            "Guidelines - Not Fixable env issue 'External-network dependency at build/solve "
            "time' (a multi-GB model pull or live external service is not fixable)",
            "Vendoring ONE SMALL file is fixable; a multi-GB pull is not. Confirm the size "
            "before choosing the verdict.")
    for s in (paths.get("solution/solve.sh"), paths.get("tests/test.sh")):
        if s and (read(s, binary=True) or b"").find(b"\r\n") != -1:
            add("D8", "FIXABLE", "Environment", os.path.relpath(s, root),
                "Script has CRLF line endings - it will fail to exec in the container",
                "found \\r\\n",
                "Guidelines - fixable env issue 'CRLF line endings'",
                "Normalize to LF:  sed -i 's/\\r$//' <file>")


# ---------------------------------------------------------------- 7. packaging
STRAY = ["__pycache__", ".DS_Store", ".pytest_cache", ".mypy_cache", ".ruff_cache",
         ".venv", "node_modules", ".idea", ".vscode", ".gradle"]
STRAY_EXT = [".pyc", ".swp", ".orig", ".bak"]
# Directory path suffixes that are build/run caches (not mere names — avoid flagging
# legitimate upstream `build/` source trees unless reports/artifacts nest under them).
STRAY_PATH_MARKERS = (
    "/.gradle/",
    "/build/reports/",
    "/build/tmp/",
    "/outputs/",
)


_GIT_AUTHORING_BRANCH = re.compile(
    r"(?i)\b(framework/|sentinel|submission|fixable|task[_-]?ready|corrected|revision)\b"
)


def inspect_git_authoring_leakage(root):
    """Flag agent-readable task-authoring history inside environment/repo/.git."""
    repo_git = os.path.join(root, "environment", "repo", ".git")
    if not os.path.isdir(repo_git):
        return []
    hits = []
    cem = os.path.join(repo_git, "COMMIT_EDITMSG")
    if os.path.isfile(cem):
        text = (read(cem) or "").strip()
        if text:
            hits.append(("environment/repo/.git/COMMIT_EDITMSG",
                         f"COMMIT_EDITMSG has task-authoring text: {text[:120]!r}"))
    logs = os.path.join(repo_git, "logs")
    if os.path.isdir(logs):
        # any non-empty log is agent-readable history
        for dirpath, _, filenames in os.walk(logs):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                if os.path.getsize(fp) > 0:
                    rel = os.path.relpath(fp, root)
                    hits.append((rel, "non-empty .git/logs entry (authoring history)"))
                    break
            if hits and hits[-1][0].startswith("environment/repo/.git/logs"):
                break
    for name in ("packed-refs",):
        pr = os.path.join(repo_git, name)
        if not os.path.isfile(pr):
            continue
        body = read(pr) or ""
        if _GIT_AUTHORING_BRANCH.search(body):
            hits.append((f"environment/repo/.git/{name}",
                         "packed-refs names task-authoring branches"))
    heads = os.path.join(repo_git, "refs", "heads")
    if os.path.isdir(heads):
        for dirpath, _, filenames in os.walk(heads):
            for fn in filenames:
                branch = os.path.relpath(os.path.join(dirpath, fn), heads)
                if _GIT_AUTHORING_BRANCH.search(branch):
                    hits.append((f"environment/repo/.git/refs/heads/{branch}",
                                 f"authoring branch ref: {branch}"))
    return hits


def check_packaging(root):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        # Skip .git contents in the generic stray walk; handled by inspect_git_authoring_leakage
        if os.sep + ".git" in os.sep + rel or rel.startswith(".git") or rel.endswith(os.sep + ".git") or rel == ".git":
            dirnames[:] = []
            continue
        for d in list(dirnames):
            if d in STRAY:
                found.append(os.path.join(rel, d) if rel != "." else d)
                dirnames.remove(d)
        for f in filenames:
            if f in STRAY or any(f.endswith(e) for e in STRAY_EXT) or f.endswith("~"):
                found.append(os.path.join(rel, f) if rel != "." else f)
        # path-marker caches (build/reports, outputs, .gradle nested)
        norm = "/" + rel.replace("\\", "/").strip(".") + "/"
        if rel == ".":
            norm = "/"
        for marker in STRAY_PATH_MARKERS:
            if marker in norm:
                found.append(rel if rel != "." else marker.strip("/"))
                break
        # environment/repo/outputs as a directory name
        if os.path.basename(dirpath) == "outputs" and "environment" in Path_parts_safe(rel):
            found.append(rel if rel != "." else "outputs")
    if found:
        add("P2", "FIXABLE", "Environment", "bundle",
            f"{len(found)} stray developer artifact(s) in the bundle - a SINGLE one hard-caps "
            "the packaging axis at 1",
            ", ".join(sorted(set(found))[:8]) + (" ..." if len(found) > 8 else ""),
            "Tasking Guide - 'No stray artifacts or leakage in the bundle'",
            "Delete every one of them before zipping. Intentional dotfiles (.gitignore, "
            ".dockerignore, .gitattributes, .gitkeep, .github/, .env) are fine. "
            "For tracked paths: delete and realign base_commit_sha.")

    git_hits = inspect_git_authoring_leakage(root)
    if git_hits:
        add("P4", "FIXABLE", "Environment", "environment/repo/.git",
            f"{len(git_hits)} .git authoring-leakage hit(s) — agent-readable packaging history",
            " | ".join(f"{p}: {note}" for p, note in git_hits[:4])
            + (" ..." if len(git_hits) > 4 else ""),
            "Packaging — do not ship task-authoring COMMIT_EDITMSG / logs / branch refs",
            "Clear COMMIT_EDITMSG and authoring logs/refs from the shipped .git; keep HEAD "
            "== base_commit_sha. Untracked → delete; tracked metadata → delete and realign.")

    if os.path.isdir(os.path.join(root, "runs")):
        add("P3", "ADVISORY", "Environment", "runs/",
            "runs/ is inside the task root", "runs/ present",
            "Tasking Guide - 'zip only the contents of the task/ folder - not the folder "
            "itself, and not runs/'",
            "Review runs/ for timeouts and misinterpretation, but exclude it from the zip.")

    # solution material readable from agent paths
    repo = os.path.join(root, "environment", "repo")
    if os.path.isdir(repo):
        leaks = []
        for dirpath, dirnames, filenames in os.walk(repo):
            if ".git" in dirnames:
                dirnames.remove(".git")
            for f in filenames:
                if re.search(r"golden|ground_truth|solution\.patch|expected_output", f, re.I):
                    leaks.append(os.path.relpath(os.path.join(dirpath, f), root))
        if leaks:
            add("L3", "FIXABLE", "Instructions", "environment/repo",
                "Solution material is readable from an agent path",
                ", ".join(leaks[:5]),
                "Tasking Guide - 'Confirm no solution material (golden patch content, expected "
                "outputs, ground_truth.* files) is readable from agent paths'",
                "Remove it. Any such leakage also hard-caps the packaging axis at 1.")


def Path_parts_safe(rel):
    return rel.replace("\\", "/").split("/")


# ---------------------------------------------------------------- 8. git
def git(repo, *args, timeout=120):
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                           timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return 127, "", str(e)


def check_git(root, toml_data):
    repo = os.path.join(root, "environment", "repo")
    if not os.path.isdir(repo):
        return
    if not os.path.exists(os.path.join(repo, ".git")):
        add("G1", "FIXABLE", "Environment", "environment/repo/.git",
            ".git is missing - there is no repo for the agent to work in",
            ".git not found",
            "Guidelines - Git: '.git missing ... usually a zip tool that dropped dotfiles'",
            "Make sure environment/repo/ is a real repo and .git/ is in the zip. Re-zip with "
            "zip -rX (never -D, never a GUI compress tool).")
        return
    if subprocess.run(["which", "git"], capture_output=True).returncode != 0:
        add("G0", "ADVISORY", "Environment", "environment/repo",
            "git not available - git hygiene not checked", "", "", "Run git_hygiene.sh manually.")
        return

    rc, head, _ = git(repo, "rev-parse", "--verify", "HEAD")
    if rc != 0:
        add("G2", "FIXABLE", "Environment", "environment/repo",
            "HEAD does not resolve", "git rev-parse --verify HEAD failed",
            "Guidelines - Git: 'A detached, empty, or corrupt HEAD can't be checked out'",
            "Ensure the repo has at least one commit and HEAD points at it.")
        return

    declared = None
    for section in (toml_data.get("metadata", {}), toml_data.get("environment", {}), {}):
        for k in ("base_commit_sha", "base_commit"):
            if section.get(k):
                declared = str(section[k])
                break
        if declared:
            break
    if declared is None:
        raw = read(os.path.join(root, "task.toml")) or ""
        m = re.search(r'base_commit(?:_sha)?\s*=\s*["\']([0-9a-fA-F]{7,40})', raw)
        declared = m.group(1) if m else None
    if declared and not head.startswith(declared[:len(head)][:40]) and \
       not declared.startswith(head[:len(declared)]):
        add("G3", "FIXABLE", "Environment", "task.toml / environment/repo",
            "HEAD does not match the declared base commit",
            f"HEAD = {head}   declared = {declared}",
            "Guidelines - Git: 'the shipped repo (HEAD) is the source of truth' -> realign the "
            "declared commit to HEAD",
            f"Preferred: set base_commit_sha = \"{head}\" in task.toml. "
            "(Only checkout the declared sha if HEAD is genuinely wrong.)")

    rc, out, _ = git(repo, "rev-list", "--all", "--not", "HEAD")
    if out:
        n = len(out.splitlines())
        add("G4", "FIXABLE", "Environment", "environment/repo",
            f"{n} commit(s) exist beyond HEAD - these can carry the fix history and leak the "
            "answer",
            f"git rev-list --all --not HEAD -> {n} commits",
            "Guidelines - Git: 'Any ref past HEAD can carry the fix history and leak the "
            "answer, making the difficulty signal worthless'",
            "Delete the extra branches/tags so `git rev-list --all --not HEAD` is empty; ship a "
            "single branch at the base commit with no stray tags.")

    rc, out, _ = git(repo, "remote")
    if out:
        add("G5", "FIXABLE", "Environment", "environment/repo",
            "Remote(s) configured - an escape hatch to external history; tasks must be "
            "self-contained and offline",
            out.replace("\n", ", "),
            "Guidelines - Git: 'Remote configured'",
            "git remote remove <name> for each remote.")

    rc, out, _ = git(repo, "config", "--local", "--get-regexp", r"^filter\.")
    if out:
        add("G6", "FIXABLE", "Environment", "environment/repo/.git/config",
            "filter.* drivers configured - arbitrary commands git can run (security risk, "
            "non-reproducible)",
            out.splitlines()[0][:120],
            "Guidelines - Git: 'Filter drivers (filter.*)'",
            "Remove every filter.* section from .git/config.")

    rc, out, _ = git(repo, "status", "--porcelain")
    if out:
        n = len(out.splitlines())
        add("G7", "FIXABLE", "Environment", "environment/repo",
            f"Dirty working tree ({n} entr{'y' if n == 1 else 'ies'}) - non-reproducible start, "
            "and an uncommitted solution leaks the answer",
            out.splitlines()[0][:120] + (" ..." if n > 1 else ""),
            "Guidelines - Git: 'Dirty working tree'",
            "Commit or discard until `git status --porcelain` prints nothing.")

    logs = os.path.join(repo, ".git", "logs")
    if os.path.exists(logs):
        add("G8", "FIXABLE", "Environment", "environment/repo/.git/logs",
            "Reflog present - records rewound commits (like the solution) and bloats the repo",
            ".git/logs exists",
            "Guidelines - Git: 'Reflog present (.git/logs)'",
            "git reflog expire --expire=now --all && git gc --prune=now, then remove .git/logs")

    try:
        sz = int(subprocess.run(["du", "-sk", os.path.join(repo, ".git")],
                                capture_output=True, text=True, timeout=180).stdout.split()[0])
        if sz * 1024 > 100 * 1024 ** 2:
            add("G9", "FIXABLE", "Environment", "environment/repo/.git",
                f".git is {sz/1024:.0f} MB - over the 100 MB limit",
                f"{sz/1024:.0f} MB",
                "Guidelines - Git: '.git over 100 MB'",
                "git gc --aggressive --prune=now; if still large, strip big blobs or ship a "
                "fresh single-commit base history (then reset base_commit_sha in task.toml).")
    except Exception:
        pass

    for rel in ("tests/tests.patch", "tests/test.patch"):
        tp = os.path.join(root, rel)
        if os.path.isfile(tp):
            rc, out, err = git(repo, "apply", "--check", os.path.abspath(tp))
            if rc != 0:
                add("G10", "FIXABLE", "Tests", rel,
                    "tests.patch does not apply to the shipped repo - the most common infra "
                    "failure; every trial fails before any evidence is collected",
                    (err or out).splitlines()[0][:160] if (err or out) else f"exit {rc}",
                    "Tasking Guide - 'tests.patch must apply cleanly to the base commit'",
                    "Fix HEAD == base commit first, then regenerate the patch against the "
                    "shipped repo state. See fix-playbooks.md F10.")
            break


# ---------------------------------------------------------------- report
SEV_ORDER = {"NOT_FIXABLE": 0, "FIXABLE": 1, "ADVISORY": 2, "INFO": 3}


def verdict_hint():
    sev = {f["severity"] for f in FINDINGS}
    if "NOT_FIXABLE" in sev:
        return ("NOT FIXABLE (candidate)",
                "A finding maps to a Not-Fixable environment category. Confirm against "
                "reference/verdict-rubric.md - and first rule out every fixable repair, "
                "including bumping timeouts and vendoring small files.")
    if "FIXABLE" in sev:
        return ("FIXABLE",
                "Mechanical defects found. Fix them, then re-run this check AND redo the "
                "requirement<->assertion worksheet before declaring the task fixed.")
    return ("VALID AS-IS (mechanically)",
            "No mechanical defect found. This is NOT a verdict yet - you still owe the four "
            "judgement checks (solvability, clarity/leakage, the coverage+faithfulness maps, "
            "authenticity/PR alignment) and a local oracle + NOP run.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--json")
    ap.add_argument("--md")
    ap.add_argument("--no-git", action="store_true")
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    if not os.path.isdir(root):
        sys.exit(2)
    if not os.path.isfile(os.path.join(root, "task.toml")):
        print(f"error: {root} has no task.toml - point at the task root "
              f"(run intake.py first)", file=sys.stderr)
        sys.exit(2)

    paths = check_structure(root)
    toml_data = check_task_toml(root, paths)
    instruction = check_instruction(root, paths)
    tstats = check_tests(root, paths, instruction)
    ostats = check_oracle(root, paths)
    check_dockerfile(root, paths)
    check_packaging(root)
    if not a.no_git:
        check_git(root, toml_data if isinstance(toml_data, dict) else {})

    FINDINGS.sort(key=lambda f: (SEV_ORDER[f["severity"]], f["id"]))
    v, why = verdict_hint()

    counts = {}
    for f in FINDINGS:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1

    print("=" * 78)
    print(f"Sentinel Ultra mechanical check - {os.path.basename(root)}")
    print("=" * 78)
    print(f"fail_to_pass: {len(tstats.get('f2p', []))}   pass_to_pass: "
          f"{len(tstats.get('p2p', []))}   tests added by patch: "
          f"{len(tstats.get('added_tests', []))}")
    if ostats:
        print(f"oracle: +{ostats.get('added',0)}/-{ostats.get('removed',0)} lines across "
              f"{ostats.get('files',0)} file(s)")
    print(f"findings: " + ("  ".join(f"{k}={v_}" for k, v_ in counts.items()) or "none"))
    print()
    for f in FINDINGS:
        print(f"[{f['severity']:<11}] {f['id']:<4} {f['category']:<18} {f['where']}")
        print(f"    {f['summary']}")
        if f["evidence"]:
            print(f"    evidence: {f['evidence']}")
        if f["rule"]:
            print(f"    rule    : {f['rule']}")
        if f["fix"]:
            print(f"    fix     : {f['fix']}")
        print()
    print("-" * 78)
    print(f"Mechanical verdict hint: {v}")
    print(why)
    print("-" * 78)
    print("Still required by hand: reference/checklists.md B (requirement<->assertion "
          "worksheet), the four principles, and the source-PR cross-check.")

    if a.json:
        with open(a.json, "w") as fh:
            json.dump({"root": root, "verdict_hint": v, "counts": counts,
                       "tests": tstats, "oracle": ostats, "findings": FINDINGS}, fh, indent=2)
    if a.md:
        with open(a.md, "w") as fh:
            fh.write(f"# Mechanical check - `{os.path.basename(root)}`\n\n")
            fh.write(f"**Verdict hint:** {v}\n\n{why}\n\n")
            fh.write(f"- fail_to_pass: **{len(tstats.get('f2p', []))}** "
                     f"(>= 10 required)\n- pass_to_pass: {len(tstats.get('p2p', []))}\n")
            if ostats:
                fh.write(f"- oracle: +{ostats.get('added',0)}/-{ostats.get('removed',0)} "
                         f"across {ostats.get('files',0)} file(s)\n")
            fh.write("\n| # | Severity | Category | Where | Finding | Rule | Fix |\n")
            fh.write("|---|---|---|---|---|---|---|\n")
            for i, f in enumerate(FINDINGS, 1):
                cell = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
                fh.write(f"| {i} | {f['severity']} | {f['category']} | `{cell(f['where'])}` | "
                         f"{cell(f['summary'])} | {cell(f['rule'])} | {cell(f['fix'])} |\n")

    sys.exit(1 if counts.get("FIXABLE") or counts.get("NOT_FIXABLE") else 0)


if __name__ == "__main__":
    main()
