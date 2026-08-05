#!/usr/bin/env python3
"""Deterministic Quality Check prep — bipartite map, cite static-check, packaging sweep.

Does NOT re-implement check_task.py detectors. Reads static_check_report.json and cites
finding IDs. Human decisions live in judge_prep_decisions.json (never overwritten).

Usage:
  python3 automation/judge_prep.py --task-name TASK
  python3 automation/judge_prep.py --task-root PATH --outputs-dir PATH \\
      --static-check-json PATH

Exit: 0 always writes reports; exit 1 when HARD STOP or prep_passed is false
(unless --allow-fail-exit is unset — default exit 1 when not prep_passed).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
JUDGE_PREP_SCHEMA = 1
DECISIONS_SCHEMA = 1
UNRESOLVED_WARN_RATIO = 0.20

STOPWORDS = {
    "must", "shall", "should", "require", "requires", "required", "ensure", "ensures",
    "return", "returns", "emit", "emits", "reject", "raise", "fail", "fails", "when",
    "with", "from", "that", "this", "these", "those", "into", "onto", "have", "has",
    "been", "being", "will", "would", "could", "also", "only", "each", "every",
    "file", "files", "test", "tests", "true", "false", "none", "null", "data",
    "value", "values", "output", "input", "error", "errors", "case", "cases",
}

JUNK_DIR_NAMES = {
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv",
    "node_modules", ".idea", ".vscode",
}
JUNK_FILE_EXACT = {".DS_Store", "metadata.json", ".python-version"}
JUNK_FILE_SUFFIXES = (".pyc", ".swp", ".orig", ".rej", ".bak")
JUNK_FILE_ENDSWITH = ("~",)
ALLOW_DOTFILES = {".gitignore", ".dockerignore", ".gitattributes", ".gitkeep", ".env"}
ALLOW_DOTDIRS = {".github", ".git"}

# Pattern name → static-check id prefixes / exact ids to cite
AUTO_REMOVE_CITES = {
    "silent_skip": {"ids": {"V9"}, "summary_needles": ("silent skip", "importerror")},
    "no_entry_point": {"ids": {"V13", "V14"}, "summary_needles": ("cli", "entry-point", "entry point")},
    "precreated_artifact": {"ids": {"V10"}, "summary_needles": ("path exists", "pre-created", "touch")},
    "agent_controls_cover": {"ids": {"V11"}, "summary_needles": ("agent controls coverage",)},
    "fail_open": {"ids": {"V9"}, "summary_needles": ("fail-open", "fail open", "early return")},
    "overreach": {"ids": set(), "summary_needles": ("source-text", "source text")},  # bipartite primary
}

HARD_STOP_IDS = {"PH1", "V0"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fingerprint(text: str) -> str:
    norm = re.sub(r"\s+", " ", (text or "").strip().lower())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def tokens_from(text: str) -> Set[str]:
    out: Set[str] = set()

    def add_word(w: str) -> None:
        w = w.lower().strip()
        if len(w) < 2 or w in STOPWORDS:
            return
        out.add(w)
        # snake_case / dotted parts help link exit_code ↔ "exit code"
        for part in re.split(r"[_\./\-]+", w):
            if len(part) >= 3 and part not in STOPWORDS:
                out.add(part)

    for m in re.finditer(r"`([^`]+)`", text):
        add_word(m.group(1).strip())
    for m in re.finditer(r'["\']([A-Za-z0-9_./\-]{3,})["\']', text):
        add_word(m.group(1))
    for m in re.finditer(r"\b([A-Za-z][A-Za-z0-9_]{3,})\b", text):
        add_word(m.group(1))
    return out


def strong_tokens(toks: Set[str]) -> Set[str]:
    return {t for t in toks if len(t) >= 5 or "_" in t or "." in t or "/" in t}


# ---------------------------------------------------------------- requirement extraction


def extract_requirements(instruction: str) -> List[Dict[str, Any]]:
    lines = instruction.splitlines()
    reqs: List[Dict[str, Any]] = []
    rid = 0

    schema_pat = re.compile(
        r"(?i)\b(schema|json\s*schema|output\s+format|response\s+format|"
        r"wire\s+format|must\s+(?:emit|return|produce|serialize)|"
        r"fields?\s*:|properties\s*:)\b"
    )
    threshold_pat = re.compile(
        r"(?i)\b(at\s+least|at\s+most|no\s+more\s+than|within|threshold|"
        r"timeout|>=|<=|±|\b\d+(?:\.\d+)?\s*(?:ms|s|sec|seconds|%|percent))\b"
    )
    edge_pat = re.compile(
        r"(?i)\b(edge\s+case|when\s+missing|if\s+(?:absent|empty|invalid|null)|"
        r"must\s+(?:reject|raise|fail)|error\s+condition|on\s+failure)\b"
    )
    imperative_pat = re.compile(
        r"(?i)\b(must|shall|should|require[ds]?|ensure|implement|support|"
        r"return|emit|reject|raise|fail\s+when|do\s+not|never)\b"
    )
    field_pat = re.compile(
        r"(?i)\b(field|key|flag|option|argument|cli|path|header|property)\b|"
        r"`[A-Za-z0-9_./\-]+`|\"[A-Za-z0-9_./\-]{2,}\""
    )

    for i, line in enumerate(lines, 1):
        raw = line.strip()
        if not raw or raw.startswith("#") or raw.startswith("```"):
            continue
        # bullet / numbered / prose
        body = re.sub(r"^[-*]\s+", "", raw)
        body = re.sub(r"^\d+[.)]\s+", "", body)
        if len(body) < 12:
            continue
        kind = None
        if schema_pat.search(body):
            kind = "stated_schema"
        elif threshold_pat.search(body) and (imperative_pat.search(body) or field_pat.search(body)):
            kind = "threshold"
        elif edge_pat.search(body):
            kind = "edge_case"
        elif field_pat.search(body) and imperative_pat.search(body):
            kind = "named_field"
        elif imperative_pat.search(body):
            kind = "imperative"
        else:
            continue
        rid += 1
        conf = "high" if kind in ("stated_schema", "threshold") or "`" in body else "medium"
        if len(body) > 220:
            conf = "low" if conf != "high" else "medium"
        reqs.append(
            {
                "id": f"R{rid}",
                "kind": kind,
                "text": body,
                "line": i,
                "loc": f"instruction.md:{i}",
                "confidence": conf,
                "tokens": sorted(tokens_from(body)),
                "fingerprint": fingerprint(body),
            }
        )
    return reqs


# ---------------------------------------------------------------- assertion extraction


def _grade_sets(cfg: Dict[str, Any]) -> Tuple[Set[str], Set[str], Set[str]]:
    def as_set(key: str) -> Set[str]:
        v = cfg.get(key) or []
        if not isinstance(v, list):
            return set()
        return {str(x) for x in v}

    return as_set("fail_to_pass"), as_set("pass_to_pass"), as_set("required_pass")


def resolve_grade(test_id: Optional[str], f2p: Set[str], p2p: Set[str], req: Set[str]) -> str:
    if not test_id:
        return "UNRESOLVED"
    if test_id in f2p or test_id in p2p or test_id in req:
        return "GRADED"
    # partial: config id ends with function name
    short = test_id.split(".")[-1]
    for pool in (f2p, p2p, req):
        for cid in pool:
            if cid == short or cid.endswith("." + short) or short in cid:
                return "UNRESOLVED"  # ambiguous partial — do not treat as GRADED
    return "UNGRADED"


ASSERT_LINE = re.compile(
    r"(?i)^\+?\s*(?:assert\b|self\.assert|expect\(|should\.|pytest\.raises|"
    r"unittest\.assert|\.to\(|\.toEqual\(|\.toBe\()"
)


def extract_assertions(patch_text: str, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    f2p, p2p, req = _grade_sets(cfg)
    lines = patch_text.splitlines()
    assertions: List[Dict[str, Any]] = []
    aid = 0
    current_file = "tests.patch"
    current_test: Optional[str] = None
    # track new-file path from diff headers
    for i, line in enumerate(lines, 1):
        if line.startswith("+++ b/") or line.startswith("+++ "):
            path = line.split(None, 1)[-1]
            if path.startswith("b/"):
                path = path[2:]
            current_file = path
            continue
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:]
            mfn = re.match(r"\s*(?:async\s+)?def\s+(test_\w+)\s*\(", content)
            if mfn:
                current_test = mfn.group(1)
                continue
            mit = re.match(r"\s*(?:it|test)\s*\(\s*['\"]([^'\"]+)", content)
            if mit:
                current_test = mit.group(1)
                continue
            if not ASSERT_LINE.search(content):
                continue
            text = content.strip()
            if len(text) < 6:
                continue
            aid += 1
            # Prefer dotted id if we know file
            test_id = None
            if current_test:
                mod = current_file.replace("/", ".").removesuffix(".py").removesuffix(".ts")
                if mod.startswith("tests.") or mod.startswith("test"):
                    test_id = f"{mod}::{current_test}" if "::" not in current_test else current_test
                    # also keep short form for matching
                test_id = current_test
            grade = resolve_grade(test_id, f2p, p2p, req)
            # Also try matching full path-ish ids in config
            if grade == "UNGRADED" and test_id:
                for pool in (f2p, p2p, req):
                    if any(test_id in c or c.endswith(test_id) for c in pool):
                        grade = "GRADED"
                        break
            assertions.append(
                {
                    "id": f"A{aid}",
                    "file": current_file,
                    "line": i,
                    "loc": f"tests.patch:{i}",
                    "test_id": test_id or "UNKNOWN",
                    "assertion_text": text,
                    "grade": grade,
                    "tokens": sorted(tokens_from(text)),
                    "fingerprint": fingerprint(text),
                }
            )
    return assertions


def link_status(req_toks: Set[str], as_toks: Set[str]) -> str:
    if not req_toks or not as_toks:
        return "none"
    inter = req_toks & as_toks
    if not inter:
        return "none"
    strong = strong_tokens(inter)
    if strong:
        return "linked"
    if len(inter) >= 2:
        return "linked"
    if len(inter) == 1:
        return "UNRESOLVED"
    return "none"


def build_bipartite(
    reqs: List[Dict[str, Any]], asserts: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    coverage: List[Dict[str, Any]] = []
    faithfulness: List[Dict[str, Any]] = []
    unresolved_cov = 0
    unresolved_faith = 0

    for r in reqs:
        rt = set(r["tokens"])
        linked: List[str] = []
        unresolved_as: List[str] = []
        for a in asserts:
            if a["grade"] != "GRADED":
                continue
            st = link_status(rt, set(a["tokens"]))
            if st == "linked":
                linked.append(a["id"])
            elif st == "UNRESOLVED":
                unresolved_as.append(a["id"])
        if linked:
            status = "ok"
        elif unresolved_as:
            status = "unresolved"
            unresolved_cov += 1
        else:
            status = "gap"
        coverage.append(
            {
                "requirement_id": r["id"],
                "assertion_ids": linked,
                "unresolved_assertion_ids": unresolved_as,
                "status": status,
                "fingerprint": r["fingerprint"],
            }
        )

    for a in asserts:
        at = set(a["tokens"])
        linked_r: List[str] = []
        unresolved_r: List[str] = []
        for r in reqs:
            st = link_status(set(r["tokens"]), at)
            if st == "linked":
                linked_r.append(r["id"])
            elif st == "UNRESOLVED":
                unresolved_r.append(r["id"])
        if a["grade"] != "GRADED":
            status = "n/a_ungraded" if a["grade"] == "UNGRADED" else "n/a_unresolved_grade"
        elif linked_r:
            status = "ok"
        elif unresolved_r:
            status = "unresolved"
            unresolved_faith += 1
        else:
            status = "overreach_candidate"
        faithfulness.append(
            {
                "assertion_id": a["id"],
                "requirement_ids": linked_r,
                "unresolved_requirement_ids": unresolved_r,
                "grade": a["grade"],
                "status": status,
                "fingerprint": a["fingerprint"],
            }
        )

    n_req = max(len(reqs), 1)
    n_graded = max(sum(1 for a in asserts if a["grade"] == "GRADED"), 1)
    stats = {
        "unresolved_coverage_rows": unresolved_cov,
        "unresolved_faithfulness_rows": unresolved_faith,
        "unresolved_coverage_ratio": unresolved_cov / n_req,
        "unresolved_faithfulness_ratio": unresolved_faith / n_graded,
        "low_confidence": (
            (unresolved_cov / n_req) > UNRESOLVED_WARN_RATIO
            or (unresolved_faith / n_graded) > UNRESOLVED_WARN_RATIO
        ),
    }
    return coverage, faithfulness, stats


# ---------------------------------------------------------------- static-check cite


def cite_auto_remove(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for pattern, spec in AUTO_REMOVE_CITES.items():
        hits = []
        for f in findings:
            fid = str(f.get("id") or "")
            summary = (f.get("summary") or "").lower()
            if fid in spec["ids"]:
                if pattern in ("silent_skip", "fail_open"):
                    if any(n in summary for n in spec["summary_needles"]):
                        hits.append(fid)
                elif pattern == "overreach":
                    if any(n in summary for n in spec["summary_needles"]):
                        hits.append(fid)
                else:
                    hits.append(fid)
            elif any(n in summary for n in spec["summary_needles"]) and fid.startswith("V"):
                hits.append(fid)
        hits = sorted(set(hits))
        if hits:
            out[pattern] = {"status": "HIT", "static_ids": hits, "notes": "cited from static_check_report"}
        else:
            out[pattern] = {
                "status": "CLEAR",
                "static_ids": [],
                "notes": "no matching static-check finding",
            }
    return out


def hard_stop_reasons(
    task_root: Path,
    findings: List[Dict[str, Any]],
    instruction_ok: bool,
    patch_ok: bool,
    cfg_ok: bool,
) -> List[str]:
    reasons = []
    if not instruction_ok:
        reasons.append("instruction.md missing")
    if not patch_ok:
        reasons.append("tests/tests.patch missing")
    if not cfg_ok:
        reasons.append("tests/config.json missing or unparseable (V0-class)")
    for f in findings:
        fid = str(f.get("id") or "")
        sev = f.get("severity")
        if fid == "PH1" or (fid == "V0"):
            reasons.append(f"HARD STOP finding {fid}: {f.get('summary')}")
        if fid == "PH1" or (sev in ("FIXABLE", "NOT_FIXABLE") and fid in HARD_STOP_IDS):
            if f"HARD STOP finding {fid}" not in " ".join(reasons):
                reasons.append(f"HARD STOP finding {fid}: {f.get('summary')}")
    # Also treat tests.patch apply failure messages in findings
    for f in findings:
        if f.get("id") == "PH1":
            if not any("PH1" in r for r in reasons):
                reasons.append(f"HARD STOP PH1: {f.get('summary')}")
    return reasons


# ---------------------------------------------------------------- packaging sweep


def git_tracked_at_head(repo: Path) -> Set[str]:
    if not (repo / ".git").exists():
        return set()
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "ls-files"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return set()
        return {ln.strip() for ln in proc.stdout.splitlines() if ln.strip()}
    except Exception:
        return set()


def is_junk_path(rel: str, name: str, is_dir: bool) -> bool:
    if name in ALLOW_DOTFILES or name in ALLOW_DOTDIRS:
        return False
    if is_dir and name in JUNK_DIR_NAMES:
        return True
    if not is_dir:
        if name in JUNK_FILE_EXACT:
            return True
        if name.endswith(JUNK_FILE_SUFFIXES) or name.endswith(JUNK_FILE_ENDSWITH):
            return True
        if name.startswith("ground_truth"):
            return True
    # path segments
    parts = Path(rel).parts
    if any(p in JUNK_DIR_NAMES for p in parts):
        return True
    return False


def packaging_sweep(task_root: Path) -> Dict[str, Any]:
    repo = task_root / "environment" / "repo"
    tracked = git_tracked_at_head(repo)
    hits: List[Dict[str, str]] = []
    for dirpath, dirnames, filenames in os.walk(task_root):
        # never descend into .git
        dirnames[:] = [d for d in dirnames if d != ".git"]
        rel_dir = Path(dirpath).relative_to(task_root).as_posix()
        for d in list(dirnames):
            path = f"{rel_dir}/{d}" if rel_dir != "." else d
            if not is_junk_path(path, d, True):
                continue
            # suppress if under environment/repo and tracked? dirs usually not in ls-files
            under_repo = path == "environment/repo" or path.startswith("environment/repo/")
            if under_repo:
                # directory junk inside repo — always flag (caches are not tracked)
                hits.append({"path": path, "class": "stray_artifact"})
            else:
                hits.append({"path": path, "class": "stray_artifact"})
        for fn in filenames:
            path = f"{rel_dir}/{fn}" if rel_dir != "." else fn
            if not is_junk_path(path, fn, False):
                continue
            under_repo = path.startswith("environment/repo/")
            if under_repo:
                rel_in_repo = path[len("environment/repo/") :]
                if rel_in_repo in tracked:
                    # tracked at HEAD — upstream project; suppress
                    continue
            hits.append({"path": path, "class": "stray_artifact"})

    instr = task_root / "instruction.md"
    ps = task_root / "environment" / "problem_statement.md"
    sync_ok = False
    sync_detail = "missing file(s)"
    if instr.is_file() and ps.is_file():
        sync_ok = instr.read_bytes() == ps.read_bytes()
        sync_detail = "byte-identical" if sync_ok else "MISMATCH"

    leakage = []
    for dirpath, _, filenames in os.walk(task_root):
        if ".git" in Path(dirpath).parts:
            continue
        rel_dir = Path(dirpath).relative_to(task_root).as_posix()
        for fn in filenames:
            path = f"{rel_dir}/{fn}" if rel_dir != "." else fn
            lower = fn.lower()
            if lower.startswith("ground_truth") or "expected_output" in lower or "golden_solution" in lower:
                if not path.startswith("solution/"):
                    leakage.append(path)

    hard_cap = bool(hits)
    return {
        "hard_cap": hard_cap,
        "hits": hits,
        "instruction_sync_ok": sync_ok,
        "instruction_sync_detail": sync_detail,
        "leakage": leakage,
        "tracked_repo_files": len(tracked),
    }


# ---------------------------------------------------------------- don't-list (prep-native only)


def dont_list_scan(patch_text: str, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []
    # cite existing
    for f in findings:
        summary = (f.get("summary") or "").lower()
        fid = f.get("id")
        if "source-text" in summary or "source text" in summary or "keyword/substring" in summary:
            flags.append({"flag": "source_text", "source": f"cite {fid}", "loc": f.get("where"), "note": f.get("summary")})
        if "golden.patch" in summary or "ground_truth" in summary or "solution-side" in summary:
            flags.append({"flag": "hidden_golden", "source": f"cite {fid}", "loc": f.get("where"), "note": f.get("summary")})
    # native: magic constants in added lines
    for i, line in enumerate(patch_text.splitlines(), 1):
        if not line.startswith("+") or line.startswith("+++"):
            continue
        content = line[1:]
        if re.search(r"\bEXPECTED_[A-Z0-9_]+\s*=\s*\d+", content):
            flags.append(
                {
                    "flag": "magic_constant",
                    "source": "judge_prep",
                    "loc": f"tests.patch:{i}",
                    "note": content.strip()[:120],
                }
            )
        if re.search(r"except\s+Exception\s*:\s*pass", content):
            flags.append(
                {
                    "flag": "broad_try_except",
                    "source": "judge_prep",
                    "loc": f"tests.patch:{i}",
                    "note": "prefer cite V9 fail-open when present; flagged here if not",
                }
            )
    return flags


# ---------------------------------------------------------------- decisions join


def load_decisions(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {"schema_version": DECISIONS_SCHEMA, "decisions": []}
    try:
        data = load_json(path)
    except json.JSONDecodeError:
        return {"schema_version": DECISIONS_SCHEMA, "decisions": [], "error": "unparseable"}
    data.setdefault("decisions", [])
    return data


def join_decisions(
    decisions_doc: Dict[str, Any],
    coverage: List[Dict[str, Any]],
    faithfulness: List[Dict[str, Any]],
    allow_rows: List[Dict[str, Any]],
    reqs_by_id: Dict[str, Dict[str, Any]],
    asserts_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (by_ref map of active decisions, invalidated list)."""
    by_ref: Dict[str, Dict[str, Any]] = {}
    invalidated: List[Dict[str, Any]] = []
    for d in decisions_doc.get("decisions") or []:
        ref = d.get("ref")
        if not ref:
            continue
        fp = d.get("fingerprint")
        current_fp = None
        if ref.startswith("coverage:"):
            rid = ref.split(":", 1)[1]
            current_fp = (reqs_by_id.get(rid) or {}).get("fingerprint")
        elif ref.startswith("overreach:"):
            aid = ref.split(":", 1)[1]
            current_fp = (asserts_by_id.get(aid) or {}).get("fingerprint")
        elif ref.startswith("allow_extra:"):
            # fingerprint optional; if present compare to joined assertion texts
            tid = ref.split(":", 1)[1]
            texts = [a["assertion_text"] for a in asserts_by_id.values() if a.get("test_id") == tid]
            current_fp = fingerprint("|".join(sorted(texts))) if texts else None
            if fp and current_fp and fp != current_fp:
                invalidated.append({**d, "invalid_reason": "fingerprint mismatch after edit"})
                continue
            by_ref[ref] = d
            continue
        else:
            by_ref[ref] = d
            continue
        if fp and current_fp and fp != current_fp:
            invalidated.append({**d, "invalid_reason": "fingerprint mismatch after edit"})
            continue
        if fp and current_fp is None:
            invalidated.append({**d, "invalid_reason": "ref no longer present"})
            continue
        by_ref[ref] = d
    return by_ref, invalidated


# ---------------------------------------------------------------- allow_extra


def allow_extra_rows(cfg: Dict[str, Any], asserts: List[Dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]]]:
    enabled = bool(cfg.get("allow_extra_failures"))
    by_tid: Dict[str, List[Dict[str, Any]]] = {}
    for a in asserts:
        if a["grade"] != "UNGRADED":
            continue
        by_tid.setdefault(a["test_id"], []).append(a)
    rows = []
    for tid, alist in sorted(by_tid.items()):
        rows.append(
            {
                "test_id": tid,
                "assertion_ids": [a["id"] for a in alist],
                "assertion_count": len(alist),
                "decision": "UNDECIDED",
                "fingerprint": fingerprint("|".join(sorted(a["assertion_text"] for a in alist))),
            }
        )
    return enabled, rows


# ---------------------------------------------------------------- markdown


def render_md(report: Dict[str, Any]) -> str:
    L: List[str] = []
    L.append(f"# Judge prep — {report['task_name']}")
    L.append(f"Generated: {report['generated_at']}")
    L.append(f"Task root: `{report['task_root']}`")
    sc = report["static_check"]
    if report.get("hard_stopped"):
        L.append(f"Static-check / inputs: **HARD STOP** — {', '.join(report['hard_stop_reasons'])}")
    else:
        fix = sc.get("fixable_ids") or []
        adv = sc.get("advisory_ids") or []
        L.append(
            f"Static-check: map built"
            + (f"; open FIXABLE (packaging still blocked): {', '.join(fix)}" if fix else " (no FIXABLE)")
            + (f"; ADVISORY: {', '.join(adv)}" if adv else "")
        )
    L.append("")
    if report.get("hard_stopped"):
        L.append("## 0. HARD STOP")
        L.append("")
        for r in report["hard_stop_reasons"]:
            L.append(f"- {r}")
        L.append("")
        L.append("Map not built. Fix the hard-stop inputs, then re-run judge_prep.")
        L.append("")
        return "\n".join(L)

    L.append("## 0. Static-check gate")
    L.append("")
    if sc.get("fixable_ids"):
        L.append("> **BANNER:** Open FIXABLE findings block packaging, but the bipartite map below was still built.")
        L.append("")
    L.append("| id | severity | summary |")
    L.append("|----|----------|---------|")
    for f in sc.get("findings") or []:
        L.append(f"| {f.get('id')} | {f.get('severity')} | {(f.get('summary') or '')[:80]} |")
    if not sc.get("findings"):
        L.append("| — | — | (no findings in report) |")
    L.append("")

    if report["map_stats"].get("low_confidence"):
        L.append(
            f"> **LOW CONFIDENCE MAP:** unresolved links exceed {int(UNRESOLVED_WARN_RATIO*100)}% "
            f"in coverage and/or faithfulness "
            f"(cov={report['map_stats']['unresolved_coverage_ratio']:.0%}, "
            f"faith={report['map_stats']['unresolved_faithfulness_ratio']:.0%}). "
            "A human must read this map; do not trust it as green."
        )
        L.append("")

    L.append("## 1. Bipartite map")
    L.append("")
    L.append("### Requirements (R*)")
    L.append("| ID | kind | loc | text (truncated) | confidence |")
    L.append("|----|------|-----|-----------------|------------|")
    for r in report["requirements"]:
        trunc = r["text"] if len(r["text"]) <= 80 else r["text"][:77] + "..."
        trunc = trunc.replace("|", "\\|")
        L.append(f"| {r['id']} | {r['kind']} | {r['loc']} | {trunc} | {r['confidence']} |")
    L.append("")
    L.append("### Assertions (A*)")
    L.append("| ID | grade | test_id | loc | assertion (truncated) |")
    L.append("|----|-------|---------|-----|----------------------|")
    for a in report["assertions"]:
        trunc = a["assertion_text"] if len(a["assertion_text"]) <= 70 else a["assertion_text"][:67] + "..."
        trunc = trunc.replace("|", "\\|")
        L.append(f"| {a['id']} | {a['grade']} | {a['test_id']} | {a['loc']} | {trunc} |")
    L.append("")
    L.append("### COVERAGE (Requirement → Assertions)")
    L.append("| R | linked GRADED A | status | decision |")
    L.append("|---|-----------------|--------|----------|")
    for row in report["coverage"]:
        dec = report["decision_join"].get(f"coverage:{row['requirement_id']}", {})
        st = row["status"]
        if st == "gap" and dec.get("status") == "explained":
            st = "gap (explained)"
        aids = ", ".join(row["assertion_ids"]) or "—"
        L.append(
            f"| {row['requirement_id']} | {aids} | {st} | {dec.get('status', '—')} |"
        )
    L.append("")
    L.append("### FAITHFULNESS (Assertion → Requirement)")
    L.append("| A | grade | linked R | status | decision |")
    L.append("|---|-------|----------|--------|----------|")
    for row in report["faithfulness"]:
        dec = report["decision_join"].get(f"overreach:{row['assertion_id']}", {})
        st = row["status"]
        if st == "overreach_candidate" and dec.get("status") == "explained":
            st = "overreach (explained)"
        rids = ", ".join(row["requirement_ids"]) or "—"
        L.append(
            f"| {row['assertion_id']} | {row['grade']} | {rids} | {st} | {dec.get('status', '—')} |"
        )
    L.append("")

    L.append("## 2. Auto-REMOVE patterns (cite static-check; no re-detect)")
    L.append("| pattern | status | static_ids | notes |")
    L.append("|---------|--------|------------|-------|")
    for name, row in report["auto_remove"].items():
        L.append(
            f"| {name} | {row['status']} | {', '.join(row['static_ids']) or '—'} | {row.get('notes','')} |"
        )
    # bipartite overreach overlay
    oc = report.get("overreach_unexplained") or []
    if oc:
        L.append("")
        L.append(f"Bipartite graded overreach candidates (unexplained): {', '.join(oc)}")
    L.append("")

    L.append("## 3. Don’t-list flags")
    L.append("| flag | source | loc | note |")
    L.append("|------|--------|-----|------|")
    for d in report.get("dont_list") or []:
        L.append(f"| {d['flag']} | {d['source']} | {d.get('loc')} | {(d.get('note') or '')[:80]} |")
    if not report.get("dont_list"):
        L.append("| — | — | — | none |")
    L.append("")

    L.append("## 4. Packaging hard-cap (judge packaging axis)")
    pk = report["packaging"]
    L.append("| check | result | detail |")
    L.append("|-------|--------|--------|")
    L.append(
        f"| stray artifacts | {'HIT → cap packaging at 1' if pk['hard_cap'] else 'OK'} | "
        f"{len(pk['hits'])} hit(s); tracked-in-git suppressed |"
    )
    L.append(f"| problem_statement ≡ instruction | {'OK' if pk['instruction_sync_ok'] else 'FAIL'} | {pk['instruction_sync_detail']} |")
    L.append(
        f"| solution leakage on agent paths | {'HIT' if pk['leakage'] else 'OK'} | "
        f"{', '.join(pk['leakage'][:5]) or '—'} |"
    )
    if pk["hits"]:
        L.append("")
        L.append("Hits:")
        for h in pk["hits"][:30]:
            L.append(f"- `{h['path']}` ({h['class']})")
    L.append("")

    L.append("## 5. allow_extra_failures decision list")
    ae = report["allow_extra_failures"]
    L.append(f"config.allow_extra_failures: **{ae['enabled']}**")
    L.append("")
    if not ae["enabled"]:
        L.append("Flag false/absent — ungraded extras still listed for awareness; reward-gating asserts must stay faithful.")
        L.append("")
    L.append("| test_id | #asserts | decision | rationale |")
    L.append("|---------|----------|----------|-----------|")
    for row in ae["rows"]:
        ref = f"allow_extra:{row['test_id']}"
        dec = report["decision_join"].get(ref, {})
        decision = dec.get("status") or row["decision"]
        L.append(
            f"| {row['test_id']} | {row['assertion_count']} | {decision} | {dec.get('reason', '—')} |"
        )
    if not ae["rows"]:
        L.append("| — | 0 | — | no ungraded tests |")
    L.append("")

    L.append("## 6. Prep verdict (deterministic)")
    L.append(f"passed: **{str(report['prep_passed']).lower()}**")
    L.append(f"blockers: {report['blockers'] or '[]'}")
    if report.get("invalidated_decisions"):
        L.append("")
        L.append("**INVALIDATED decisions** (fingerprint mismatch or missing ref) — re-decide:")
        for d in report["invalidated_decisions"]:
            L.append(f"- `{d.get('ref')}`: {d.get('invalid_reason')} (was: {d.get('status')})")
    L.append("")
    L.append(f"accept_risk (workflow_state): {report.get('accept_risk') or 'unset'}")
    L.append("")
    L.append("## 7. Handoff to judge_rehearsal")
    L.append(
        "Read `judge_prep.json`. Run **two** adversarial scoring passes (coverage stub vs "
        "faithfulness instruction-only), reconcile, flag axes differing by ≥2 for human review. "
        "Apply REMOVE/DISCUSS/OK on test axes; refuse package if any axis < 3.5. No filler f2p."
    )
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- main run


def run_judge_prep(
    task_root: Path,
    outputs_dir: Path,
    static_check_json: Path,
    task_name: str = "",
    accept_risk: Optional[str] = None,
) -> Dict[str, Any]:
    outputs_dir.mkdir(parents=True, exist_ok=True)
    decisions_path = outputs_dir / "judge_prep_decisions.json"
    md_path = outputs_dir / "judge_prep.md"
    json_path = outputs_dir / "judge_prep.json"

    findings: List[Dict[str, Any]] = []
    fixable_ids: List[str] = []
    advisory_ids: List[str] = []
    not_fixable_ids: List[str] = []
    sc_ok = False
    if static_check_json.is_file():
        sc = load_json(static_check_json)
        findings = sc.get("findings") or []
        fixable_ids = sorted({f["id"] for f in findings if f.get("severity") == "FIXABLE"})
        # also from top-level if present
        fixable_ids = sorted(set(fixable_ids) | set(sc.get("fixable_ids") or []))
        advisory_ids = sorted(set(sc.get("advisory_ids") or []) | {f["id"] for f in findings if f.get("severity") == "ADVISORY"})
        not_fixable_ids = sorted(set(sc.get("not_fixable_ids") or []) | {f["id"] for f in findings if f.get("severity") == "NOT_FIXABLE"})
        sc_ok = True
    else:
        # missing report is not hard-stop for map if files exist — but warn via fixable-like banner
        fixable_ids = ["MISSING_STATIC_CHECK_REPORT"]

    instr_path = task_root / "instruction.md"
    patch_path = task_root / "tests" / "tests.patch"
    cfg_path = task_root / "tests" / "config.json"
    instruction_ok = instr_path.is_file()
    patch_ok = patch_path.is_file()
    cfg: Dict[str, Any] = {}
    cfg_ok = False
    if cfg_path.is_file():
        try:
            cfg = load_json(cfg_path)
            cfg_ok = True
        except json.JSONDecodeError:
            cfg_ok = False

    # Inject synthetic V0 if config bad
    if cfg_path.is_file() and not cfg_ok:
        findings = list(findings) + [{
            "id": "V0", "severity": "FIXABLE", "summary": "config.json unparseable",
        }]
        fixable_ids = sorted(set(fixable_ids) | {"V0"})

    stop_reasons = hard_stop_reasons(task_root, findings, instruction_ok, patch_ok, cfg_ok or not cfg_path.exists())
    # config missing entirely — treat as hard stop (cannot grade)
    if not cfg_path.is_file():
        stop_reasons.append("tests/config.json missing — graded vs ungraded cannot be determined")
        stop_reasons = list(dict.fromkeys(stop_reasons))

    base_report: Dict[str, Any] = {
        "schema_version": JUDGE_PREP_SCHEMA,
        "task_name": task_name or task_root.name,
        "generated_at": utc_now(),
        "task_root": str(task_root.resolve()),
        "static_check": {
            "ok": sc_ok and not fixable_ids and not not_fixable_ids,
            "report_path": str(static_check_json),
            "fixable_ids": fixable_ids,
            "advisory_ids": advisory_ids,
            "not_fixable_ids": not_fixable_ids,
            "findings": [
                {"id": f.get("id"), "severity": f.get("severity"), "summary": f.get("summary")}
                for f in findings
            ],
        },
        "accept_risk": accept_risk,
        "hard_stopped": False,
        "hard_stop_reasons": [],
        "prep_passed": False,
        "blockers": [],
    }

    if stop_reasons:
        base_report["hard_stopped"] = True
        base_report["hard_stop_reasons"] = stop_reasons
        base_report["blockers"] = [f"hard_stop:{r}" for r in stop_reasons]
        base_report["requirements"] = []
        base_report["assertions"] = []
        base_report["coverage"] = []
        base_report["faithfulness"] = []
        base_report["map_stats"] = {}
        base_report["auto_remove"] = {}
        base_report["dont_list"] = []
        base_report["packaging"] = {}
        base_report["allow_extra_failures"] = {"enabled": False, "rows": []}
        base_report["decision_join"] = {}
        base_report["invalidated_decisions"] = []
        write_json(json_path, base_report)
        md_path.write_text(render_md(base_report), encoding="utf-8")
        # never overwrite decisions file
        if not decisions_path.is_file():
            write_json(decisions_path, {"schema_version": DECISIONS_SCHEMA, "decisions": []})
        return base_report

    instruction = instr_path.read_text(encoding="utf-8", errors="replace")
    patch_text = patch_path.read_text(encoding="utf-8", errors="replace")
    reqs = extract_requirements(instruction)
    asserts = extract_assertions(patch_text, cfg)
    coverage, faithfulness, map_stats = build_bipartite(reqs, asserts)
    auto_remove = cite_auto_remove(findings)
    # bipartite overreach feeds pattern status
    overreach_ids = [
        row["assertion_id"]
        for row in faithfulness
        if row["status"] == "overreach_candidate"
    ]
    if overreach_ids:
        auto_remove["overreach"] = {
            "status": "HIT",
            "static_ids": auto_remove["overreach"].get("static_ids") or [],
            "notes": f"bipartite graded candidates: {', '.join(overreach_ids)}",
        }

    packaging = packaging_sweep(task_root)
    dont = dont_list_scan(patch_text, findings)
    ae_enabled, ae_rows = allow_extra_rows(cfg, asserts)

    reqs_by_id = {r["id"]: r for r in reqs}
    asserts_by_id = {a["id"]: a for a in asserts}
    decisions_doc = load_decisions(decisions_path)
    by_ref, invalidated = join_decisions(
        decisions_doc, coverage, faithfulness, ae_rows, reqs_by_id, asserts_by_id
    )

    blockers: List[str] = []
    # auto-REMOVE hits from static cite (except overreach handled via bipartite decisions)
    for pattern, row in auto_remove.items():
        if pattern == "overreach":
            continue
        if row["status"] == "HIT":
            blockers.append(f"auto_remove:{pattern}:{','.join(row['static_ids'])}")

    unexplained_gaps = []
    for row in coverage:
        if row["status"] != "gap":
            continue
        ref = f"coverage:{row['requirement_id']}"
        dec = by_ref.get(ref)
        if dec and dec.get("status") == "explained":
            continue
        unexplained_gaps.append(row["requirement_id"])
        blockers.append(ref)

    unexplained_overreach = []
    for row in faithfulness:
        if row["status"] != "overreach_candidate":
            continue
        ref = f"overreach:{row['assertion_id']}"
        dec = by_ref.get(ref)
        if dec and dec.get("status") == "explained":
            continue
        unexplained_overreach.append(row["assertion_id"])
        blockers.append(ref)

    if ae_enabled:
        for row in ae_rows:
            ref = f"allow_extra:{row['test_id']}"
            dec = by_ref.get(ref)
            status = (dec or {}).get("status") or "UNDECIDED"
            row["decision"] = status
            if status not in ("PROMOTE_F2P", "DELETE"):
                blockers.append(ref)

    if packaging.get("hard_cap"):
        blockers.append("packaging:hard_cap")
    if not packaging.get("instruction_sync_ok"):
        blockers.append("packaging:instruction_sync")
    if packaging.get("leakage"):
        blockers.append("packaging:leakage")

    if invalidated:
        blockers.append("decisions:invalidated")

    # Open FIXABLE does not hard-stop but keeps prep_passed false
    if fixable_ids or not_fixable_ids:
        for fid in fixable_ids:
            blockers.append(f"static_fixable:{fid}")
        for fid in not_fixable_ids:
            blockers.append(f"static_not_fixable:{fid}")

    prep_passed = len(blockers) == 0

    report = {
        **base_report,
        "requirements": reqs,
        "assertions": asserts,
        "coverage": coverage,
        "faithfulness": faithfulness,
        "map_stats": map_stats,
        "auto_remove": auto_remove,
        "overreach_unexplained": unexplained_overreach,
        "coverage_gaps_unexplained": unexplained_gaps,
        "dont_list": dont,
        "packaging": packaging,
        "allow_extra_failures": {"enabled": ae_enabled, "rows": ae_rows},
        "decision_join": by_ref,
        "invalidated_decisions": invalidated,
        "prep_passed": prep_passed,
        "blockers": blockers,
    }

    write_json(json_path, report)
    md_path.write_text(render_md(report), encoding="utf-8")
    if not decisions_path.is_file():
        write_json(decisions_path, {"schema_version": DECISIONS_SCHEMA, "decisions": []})
    return report


def resolve_from_session(task_name: str) -> Tuple[Path, Path, Path, Optional[str]]:
    sys.path.insert(0, str(SCRIPT_DIR))
    from sentinel_submitter import (  # type: ignore
        load_session,
        load_workflow_state,
        resolve_static_check_root,
        session_paths,
    )

    name, session = load_session(task_name)
    state = load_workflow_state(name)
    root = resolve_static_check_root(session, state)
    paths = session_paths(name)
    sc_json = paths["outputs"] / "static_check_report.json"
    accept = state.get("judge_prep_accept_risk_reason") if state.get("judge_prep_accept_risk") else None
    return root, paths["outputs"], sc_json, accept


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Sentinel Ultra judge_prep (deterministic)")
    p.add_argument("--task-name")
    p.add_argument("--task-root", type=Path)
    p.add_argument("--outputs-dir", type=Path)
    p.add_argument("--static-check-json", type=Path)
    p.add_argument("--allow-fail-exit", action="store_true", default=True)
    args = p.parse_args(argv)

    accept = None
    if args.task_root:
        if not args.outputs_dir or not args.static_check_json:
            print("ERROR: --task-root requires --outputs-dir and --static-check-json", file=sys.stderr)
            return 2
        task_root = args.task_root
        outputs_dir = args.outputs_dir
        sc_json = args.static_check_json
        task_name = args.task_name or task_root.name
    elif args.task_name:
        task_root, outputs_dir, sc_json, accept = resolve_from_session(args.task_name)
        task_name = args.task_name
    else:
        print("ERROR: provide --task-name or --task-root", file=sys.stderr)
        return 2

    report = run_judge_prep(task_root, outputs_dir, sc_json, task_name=task_name, accept_risk=accept)
    print("JUDGE PREP COMPLETE")
    print(f"  root: {task_root}")
    print(f"  hard_stopped: {report.get('hard_stopped')}")
    print(f"  prep_passed: {report.get('prep_passed')}")
    print(f"  blockers: {len(report.get('blockers') or [])}")
    print(f"  report: {outputs_dir / 'judge_prep.md'}")
    if report.get("hard_stopped") or not report.get("prep_passed"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
