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
import math
import os
import random
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
JUDGE_REHEARSAL_SCHEMA = 1
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
    "node_modules", ".idea", ".vscode", ".gradle",
}
JUNK_FILE_EXACT = {".DS_Store", "metadata.json", ".python-version"}
JUNK_FILE_SUFFIXES = (".pyc", ".swp", ".orig", ".rej", ".bak")
JUNK_FILE_ENDSWITH = ("~",)
ALLOW_DOTFILES = {".gitignore", ".dockerignore", ".gitattributes", ".gitkeep", ".env"}
ALLOW_DOTDIRS = {".github", ".git"}
# Nested cache path markers (segment sequences), not bare `build/` (too broad upstream).
JUNK_PATH_MARKERS = (
    "/.gradle/",
    "/build/reports/",
    "/build/tmp/",
)
_GIT_AUTHORING_BRANCH = re.compile(
    r"(?i)\b(framework/|sentinel|submission|fixable|task[_-]?ready|corrected|revision)\b"
)

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


def _identifier_parts(toks: Set[str]) -> Set[str]:
    """Snake/dot fragments of identifier tokens (cell_map → cell, map)."""
    parts: Set[str] = set()
    for t in toks:
        if "_" not in t and "." not in t and "/" not in t:
            continue
        for p in re.split(r"[_\./]+", t):
            if len(p) >= 3:
                parts.add(p)
    return parts


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


def _list_from_src(src: Any, key: str) -> Optional[List[str]]:
    if not isinstance(src, dict):
        return None
    # case-insensitive key match
    for k, v in src.items():
        if str(k).lower() != key.lower():
            continue
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return [str(x) for x in v]
        return []
    return None


def extract_grade_lists(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Read fail_to_pass / pass_to_pass / required_pass from nested grading or top-level.

    Prefer nested ``grading.*`` when both shapes exist; warn on disagreement.
    Also resolve ``allow_extra_failures`` the same way.
    """
    grading = cfg.get("grading") if isinstance(cfg.get("grading"), dict) else {}
    warnings: List[str] = []
    out: Dict[str, Any] = {"warnings": warnings}

    for key in ("fail_to_pass", "pass_to_pass", "required_pass"):
        nested = _list_from_src(grading, key)
        top = _list_from_src(cfg, key)
        if nested is not None and top is not None:
            if nested != top:
                warnings.append(
                    f"grading.{key} and top-level {key} disagree "
                    f"(nested={len(nested)} top={len(top)}); preferring nested"
                )
            chosen, source = nested, "grading"
        elif nested is not None:
            chosen, source = nested, "grading"
        elif top is not None:
            chosen, source = top, "top-level"
        else:
            chosen, source = [], "missing"
        out[key] = set(chosen)
        out[f"{key}_source"] = source

    ae_nested = grading.get("allow_extra_failures") if grading else None
    ae_top = cfg.get("allow_extra_failures")
    if ae_nested is not None and ae_top is not None and bool(ae_nested) != bool(ae_top):
        warnings.append(
            "grading.allow_extra_failures and top-level disagree; preferring nested"
        )
    if ae_nested is not None:
        out["allow_extra_failures"] = bool(ae_nested)
    elif ae_top is not None:
        out["allow_extra_failures"] = bool(ae_top)
    else:
        out["allow_extra_failures"] = False
    return out


def _grade_sets(cfg: Dict[str, Any]) -> Tuple[Set[str], Set[str], Set[str], Dict[str, Any]]:
    meta = extract_grade_lists(cfg)
    return meta["fail_to_pass"], meta["pass_to_pass"], meta["required_pass"], meta


def resolve_grade(test_id: Optional[str], f2p: Set[str], p2p: Set[str], req: Set[str]) -> str:
    if not test_id or test_id == "UNKNOWN":
        return "UNRESOLVED"
    pools = f2p | p2p | req
    if test_id in pools:
        return "GRADED"
    # Pytest node ids: path::Class::test_name or path::test_name
    exact_suffix = [cid for cid in pools if cid.endswith("::" + test_id) or cid.endswith("." + test_id)]
    if len(exact_suffix) == 1:
        return "GRADED"
    if len(exact_suffix) > 1:
        return "UNRESOLVED"
    # Unique containment of the function name as a node-id segment
    contains = [cid for cid in pools if f"::{test_id}" in cid or cid == test_id]
    if len(contains) == 1:
        return "GRADED"
    if len(contains) > 1:
        return "UNRESOLVED"
    return "UNGRADED"


ASSERT_LINE = re.compile(
    r"(?i)^\+?\s*(?:assert\b|self\.assert|expect\(|should\.|pytest\.raises|"
    r"unittest\.assert|\.to\(|\.toEqual\(|\.toBe\()"
)


def extract_assertions(patch_text: str, cfg: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    f2p, p2p, req, grade_meta = _grade_sets(cfg)
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
            test_id = current_test or "UNKNOWN"
            grade = resolve_grade(test_id, f2p, p2p, req)
            assertions.append(
                {
                    "id": f"A{aid}",
                    "file": current_file,
                    "line": i,
                    "loc": f"tests.patch:{i}",
                    "test_id": test_id,
                    "assertion_text": text,
                    "grade": grade,
                    "tokens": sorted(tokens_from(text)),
                    "fingerprint": fingerprint(text),
                }
            )
    return assertions, grade_meta


def link_status(req_toks: Set[str], as_toks: Set[str]) -> str:
    """Lexical R↔A overlap class.

    ``linked`` — strong behavioural overlap (≥2 effective strong tokens). Only this
    bypasses rehearsal triage.
    ``weak_link`` — single identifier hit, fragment noise, or weak-only overlap. Same
    uncertainty as the old single-token UNRESOLVED; must not paint the row green.
    ``none`` — no shared tokens.

    Fragments of snake_case/dotted identifiers (e.g. ``shape`` from ``out_shape``,
    ``map`` from ``cell_map``) do not count toward strong overlap — that is what made
    Case 2 A6 falsely green against R11.
    """
    if not req_toks or not as_toks:
        return "none"
    inter = req_toks & as_toks
    if not inter:
        return "none"
    frag_noise = _identifier_parts(req_toks) | _identifier_parts(as_toks)
    effective_strong: Set[str] = set()
    for t in strong_tokens(inter):
        if "_" in t or "." in t or "/" in t:
            effective_strong.add(t)
            continue
        if t in frag_noise:
            continue
        effective_strong.add(t)
    if len(effective_strong) >= 2:
        return "linked"
    if effective_strong or inter:
        return "weak_link"
    return "none"


# Lexical statuses only — semantic overreach/gap confirmation is judge_rehearsal (P-011).
STATUS_UNLINKED_LEXICALLY = "unlinked_lexically"
STATUS_WEAK_LINK = "weak_link"
STATUS_NO_GRADED_LINK = "no_graded_link"
# Faithfulness rows that must be P-011-triaged (not confident green).
FAITHFULNESS_TRIAGE_STATUSES = frozenset({STATUS_UNLINKED_LEXICALLY, STATUS_WEAK_LINK})
COVERAGE_TRIAGE_STATUSES = frozenset({STATUS_NO_GRADED_LINK, STATUS_WEAK_LINK})


def sample_linked_spot_check(
    faithfulness: List[Dict[str, Any]],
    *,
    seed: str,
) -> Dict[str, Any]:
    """Deterministic spot-check of status=ok (strong-linked) faithfulness rows.

    Sample size = max(5, ceil(10% of linked population)), capped at population.
    Seed is recorded so a re-run selects the same assertion ids.
    """
    linked_ids = sorted(
        r["assertion_id"] for r in faithfulness if r.get("status") == "ok"
    )
    n = len(linked_ids)
    if n == 0:
        return {
            "seed": seed,
            "population": 0,
            "sample_size": 0,
            "sample_rule": "max(5, ceil(0.10 * population))",
            "assertion_ids": [],
            "note": "no status=ok linked rows to sample",
        }
    k = min(n, max(5, int(math.ceil(n * 0.10))))
    rng = random.Random(int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16], 16))
    shuffled = list(linked_ids)
    rng.shuffle(shuffled)
    sample_ids = sorted(shuffled[:k])
    return {
        "seed": seed,
        "population": n,
        "sample_size": k,
        "sample_rule": "max(5, ceil(0.10 * population))",
        "assertion_ids": sample_ids,
        "note": (
            "Rehearsal applies P-011 to these strong-linked rows. "
            "CONFIRMED overreach in the sample → SAMPLE_HIT (matcher may be over-confident; "
            "consider widening triage for this task)."
        ),
    }


def _faithfulness_severity(grade: str, status: str) -> Optional[str]:
    """Severity for triage-bound faithfulness rows. Grade gates severity, not eligibility.

    GRADED → high (can zero reward). UNGRADED → medium (judge still scores the whole suite).
    """
    if status not in FAITHFULNESS_TRIAGE_STATUSES:
        return None
    if grade == "GRADED":
        return "high"
    return "medium"


def build_bipartite(
    reqs: List[Dict[str, Any]], asserts: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    coverage: List[Dict[str, Any]] = []
    faithfulness: List[Dict[str, Any]] = []
    weak_cov = 0
    weak_faith = 0

    # Coverage: only strong ``linked`` GRADED asserts close a gap.
    for r in reqs:
        rt = set(r["tokens"])
        linked: List[str] = []
        weak_as: List[str] = []
        for a in asserts:
            if a["grade"] != "GRADED":
                continue
            st = link_status(rt, set(a["tokens"]))
            if st == "linked":
                linked.append(a["id"])
            elif st == "weak_link":
                weak_as.append(a["id"])
        if linked:
            status = "ok"
        elif weak_as:
            status = STATUS_WEAK_LINK
            weak_cov += 1
        else:
            status = STATUS_NO_GRADED_LINK
        coverage.append(
            {
                "requirement_id": r["id"],
                "assertion_ids": linked,
                "weak_assertion_ids": weak_as,
                "unresolved_assertion_ids": weak_as,  # back-compat alias
                "status": status,
                "fingerprint": r["fingerprint"],
            }
        )

    # Faithfulness: EVERY assertion. Only strong linked bypasses triage.
    for a in asserts:
        at = set(a["tokens"])
        linked_r: List[str] = []
        weak_r: List[str] = []
        for r in reqs:
            st = link_status(set(r["tokens"]), at)
            if st == "linked":
                linked_r.append(r["id"])
            elif st == "weak_link":
                weak_r.append(r["id"])
        if linked_r:
            status = "ok"
        elif weak_r:
            status = STATUS_WEAK_LINK
            weak_faith += 1
        else:
            status = STATUS_UNLINKED_LEXICALLY
        faithfulness.append(
            {
                "assertion_id": a["id"],
                "requirement_ids": linked_r,
                "weak_requirement_ids": weak_r,
                "unresolved_requirement_ids": weak_r,  # back-compat alias
                "grade": a["grade"],
                "status": status,
                "severity": _faithfulness_severity(a["grade"], status),
                "fingerprint": a["fingerprint"],
            }
        )

    n_req = max(len(reqs), 1)
    n_assert = max(len(asserts), 1)
    stats = {
        "weak_link_coverage_rows": weak_cov,
        "weak_link_faithfulness_rows": weak_faith,
        "unresolved_coverage_rows": weak_cov,  # back-compat
        "unresolved_faithfulness_rows": weak_faith,
        "unresolved_coverage_ratio": weak_cov / n_req,
        "unresolved_faithfulness_ratio": weak_faith / n_assert,
        "low_confidence": (
            (weak_cov / n_req) > UNRESOLVED_WARN_RATIO
            or (weak_faith / n_assert) > UNRESOLVED_WARN_RATIO
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
    norm = "/" + rel.replace("\\", "/").strip("/") + "/"
    if any(marker in norm for marker in JUNK_PATH_MARKERS):
        return True
    # prior-run artifact dirs under the shipped repo
    if is_dir and name == "outputs" and "environment/repo" in rel.replace("\\", "/"):
        return True
    return False


def inspect_git_authoring_leakage(task_root: Path) -> List[Dict[str, Any]]:
    """Agent-readable task-authoring history inside environment/repo/.git."""
    git_dir = task_root / "environment" / "repo" / ".git"
    if not git_dir.is_dir():
        return []
    hits: List[Dict[str, Any]] = []

    def add_hit(rel: str, note: str) -> None:
        hits.append(
            {
                "path": rel,
                "class": "git_authoring_leak",
                "tracked": False,  # .git internals are not tree paths in ls-files
                "remediation": (
                    "tracked=false — delete/clear from the shipped .git; keep HEAD == "
                    "base_commit_sha"
                ),
                "note": note,
            }
        )

    cem = git_dir / "COMMIT_EDITMSG"
    if cem.is_file():
        text = cem.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            add_hit(
                "environment/repo/.git/COMMIT_EDITMSG",
                f"COMMIT_EDITMSG has task-authoring text: {text[:120]!r}",
            )
    logs = git_dir / "logs"
    if logs.is_dir():
        for p in logs.rglob("*"):
            if p.is_file() and p.stat().st_size > 0:
                add_hit(
                    p.relative_to(task_root).as_posix(),
                    "non-empty .git/logs entry (authoring history)",
                )
                break
    packed = git_dir / "packed-refs"
    if packed.is_file():
        body = packed.read_text(encoding="utf-8", errors="replace")
        if _GIT_AUTHORING_BRANCH.search(body):
            add_hit(
                "environment/repo/.git/packed-refs",
                "packed-refs names task-authoring branches",
            )
    heads = git_dir / "refs" / "heads"
    if heads.is_dir():
        for p in heads.rglob("*"):
            if not p.is_file():
                continue
            branch = p.relative_to(heads).as_posix()
            if _GIT_AUTHORING_BRANCH.search(branch):
                add_hit(
                    f"environment/repo/.git/refs/heads/{branch}",
                    f"authoring branch ref: {branch}",
                )
    return hits


# Optional suppressions for junk-named paths that are genuinely upstream source.
# Default is empty — any entry MUST carry a human justification string.
# Format: { "environment/repo/some/path": "why this is real project source, not junk" }
UPSTREAM_JUNK_NAME_SUPPRESSIONS: Dict[str, str] = {}


def packaging_sweep(task_root: Path) -> Dict[str, Any]:
    """Flag every junk-list hit. Never suppress on tracked-ness.

    Annotate tracked=true|false:
      tracked=false → delete from the bundle
      tracked=true  → remove from shipped tree AND realign base_commit_sha (git hygiene)

    Both severities hard-cap the packaging axis at 1.
    Narrow optional suppressions only via UPSTREAM_JUNK_NAME_SUPPRESSIONS with justification.
    """
    repo = task_root / "environment" / "repo"
    tracked = git_tracked_at_head(repo)
    hits: List[Dict[str, Any]] = []
    suppressed: List[Dict[str, str]] = []

    def annotate(path: str, klass: str = "stray_artifact") -> Dict[str, Any]:
        under_repo = path.startswith("environment/repo/")
        rel_in_repo = path[len("environment/repo/") :] if under_repo else ""
        is_tracked = bool(under_repo and rel_in_repo in tracked)
        if is_tracked:
            remediation = (
                "tracked=true — remove from the shipped tree AND realign "
                "base_commit_sha to the new HEAD (fixable git hygiene; heavier fix)"
            )
        else:
            remediation = "tracked=false — delete from the bundle"
        return {
            "path": path,
            "class": klass,
            "tracked": is_tracked,
            "remediation": remediation,
        }

    for dirpath, dirnames, filenames in os.walk(task_root):
        # Skip .git contents here; inspect_git_authoring_leakage covers them.
        dirnames[:] = [d for d in dirnames if d != ".git"]
        rel_dir = Path(dirpath).relative_to(task_root).as_posix()
        for d in list(dirnames):
            path = f"{rel_dir}/{d}" if rel_dir != "." else d
            if not is_junk_path(path, d, True):
                continue
            if path in UPSTREAM_JUNK_NAME_SUPPRESSIONS:
                suppressed.append(
                    {"path": path, "justification": UPSTREAM_JUNK_NAME_SUPPRESSIONS[path]}
                )
                continue
            hits.append(annotate(path))
        for fn in filenames:
            path = f"{rel_dir}/{fn}" if rel_dir != "." else fn
            if not is_junk_path(path, fn, False):
                continue
            if path in UPSTREAM_JUNK_NAME_SUPPRESSIONS:
                suppressed.append(
                    {"path": path, "justification": UPSTREAM_JUNK_NAME_SUPPRESSIONS[path]}
                )
                continue
            hits.append(annotate(path))

    hits.extend(inspect_git_authoring_leakage(task_root))

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
        "suppressed_with_justification": suppressed,
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


# ---------------------------------------------------------------- Q9/Q10 + private internals


_ASSERT_NOISE = frozenset({
    "self", "true", "false", "none", "null", "assert", "assertequal", "asserttrue",
    "assertfalse", "assertin", "assertis", "assertisnone", "assertisnotnone",
    "assertalmostequal", "assertraises", "assertraisesregex", "pytest", "raises",
    "result", "actual", "expected", "output", "value", "values", "data", "obj",
    "item", "items", "kwargs", "args", "exc", "err", "error", "msg", "message",
    "match", "regex", "pattern", "test", "tests", "mock", "magicmock", "call",
    "return", "returns", "isinstance", "issubclass", "hasattr", "getattr", "len",
    "str", "int", "float", "bool", "list", "dict", "set", "tuple", "bytes",
    "path", "pathlib", "open", "print", "range", "type", "object", "super",
})

_ERROR_MSG_LITERAL = re.compile(
    r"(?is)(?:error\s+message|exception\s+message|(?:raised?\s+)?(?:value)?error|"
    r"message\s+(?:must|should|shall))\s+"
    r".{0,120}?\b(?:must|should|shall)\s+contain\b.{0,80}?"
    r"[`'\"]([^`'\"]{2,})[`'\"]"
    r"(?:.{0,60}?\band\b.{0,40}?[`'\"]([^`'\"]{2,})[`'\"])?"
)

_ERROR_MSG_LITERAL_ALT = re.compile(
    r"(?is)\b(?:must|should|shall)\s+contain\s+(?:the\s+)?(?:words?|substrings?)\s+"
    r"[`'\"]([^`'\"]{2,})[`'\"]\s+and\s+[`'\"]([^`'\"]{2,})[`'\"]"
)

_PATH_IMPERATIVE = re.compile(
    r"(?i)\b(update|modify|edit|add\s+to|look\s+in|start\s+by|change|implement\s+in|"
    r"place\s+(?:it\s+)?(?:in|under)|put\s+(?:it\s+)?(?:in|under))\b"
)

_FS_PATH = re.compile(
    r"(?ix)(?:^|[^\w./])("
    r"(?:src|lib|tests?|docs?|include|scripts?|app|packages?|environment|"
    r"resources?|assets?)/[\w./\-]+"
    r"|[\w./\-]+\.(?:py|ts|tsx|js|jsx|cpp|cc|cxx|h|hpp|java|kt|go|rs|md|toml|"
    r"yml|yaml|cmake|txt|json|css|scss|xml)"
    r")\b"
)


def scan_q9_q10_instruction(instruction: str) -> Dict[str, Any]:
    """Q10 error-message literals → blocking. Q9 path-as-navigation → candidates only."""
    blocking: List[Dict[str, Any]] = []
    path_candidates: List[Dict[str, Any]] = []

    for rx in (_ERROR_MSG_LITERAL, _ERROR_MSG_LITERAL_ALT):
        for m in rx.finditer(instruction or ""):
            words = [w for w in m.groups() if w]
            if not words:
                continue
            blocking.append(
                {
                    "kind": "error_message_literal",
                    "words": words,
                    "snippet": " ".join(m.group(0).split())[:160],
                    "rule": "Q10 — instruction must not require error messages to contain "
                    "specific literal words (leaks test match= logic)",
                }
            )

    lines = (instruction or "").splitlines()
    for i, line in enumerate(lines, 1):
        if not _PATH_IMPERATIVE.search(line):
            continue
        for pm in _FS_PATH.finditer(line):
            path = pm.group(1)
            # Module/import paths without a filesystem root or extension were already
            # excluded by _FS_PATH; still skip dotted-only API if somehow matched.
            if "/" not in path and "." not in path.split("/")[-1]:
                continue
            path_candidates.append(
                {
                    "kind": "path_as_navigation",
                    "path": path,
                    "line": i,
                    "snippet": line.strip()[:160],
                    "rule": "Q9 candidate — filesystem path near imperative "
                    "(update/modify/edit/add to/look in/start by); module import "
                    "paths naming public API are not flagged",
                }
            )
    return {"blocking": blocking, "path_candidates": path_candidates}


def scan_private_internals(
    asserts: List[Dict[str, Any]], instruction: str
) -> List[Dict[str, Any]]:
    """Graded assertion identifiers absent from instruction.md — faithfulness candidates."""
    instr_lower = (instruction or "").lower()
    instr_toks = tokens_from(instruction or "")
    cands: List[Dict[str, Any]] = []

    def declared(name: str) -> bool:
        n = name.lower()
        if n in instr_toks or n in instr_lower:
            return True
        # allow instruction to name without exact case
        return name in (instruction or "")

    for a in asserts:
        if a.get("grade") != "GRADED":
            continue
        text = a.get("assertion_text") or ""
        # subscript into private-ish members
        for key in re.findall(r"\[\s*['\"]([^'\"]+)['\"]\s*\]", text):
            if declared(key):
                continue
            cands.append(
                {
                    "assertion_id": a["id"],
                    "test_id": a.get("test_id"),
                    "identifier": key,
                    "kind": "private_subscript",
                    "severity": "higher",
                    "note": f"subscript {key!r} not declared in instruction.md",
                }
            )
        for name in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", text):
            if name.lower() in _ASSERT_NOISE:
                continue
            if len(name) < 3:
                continue
            if declared(name):
                continue
            # Prefer API-ish names: CapWords, snake_case, underscore-private
            if not (name.startswith("_") or "_" in name or name[:1].isupper()):
                continue
            sev = "higher" if name.startswith("_") else "normal"
            cands.append(
                {
                    "assertion_id": a["id"],
                    "test_id": a.get("test_id"),
                    "identifier": name,
                    "kind": "undeclared_identifier",
                    "severity": sev,
                    "note": f"{name!r} not declared in instruction.md",
                }
            )
    # de-dupe
    seen = set()
    out = []
    for c in cands:
        key = (c["assertion_id"], c["identifier"], c["kind"])
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def grading_config_from_static(findings: List[Dict[str, Any]], grade_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Dedicated report section for V15/V16 (+ allow_extra mirror)."""
    v15 = [f for f in findings if f.get("id") == "V15"]
    v16 = [f for f in findings if f.get("id") == "V16"]
    return {
        "allow_extra_failures": bool(grade_meta.get("allow_extra_failures")),
        "v15_hits": [
            {"summary": f.get("summary"), "evidence": f.get("evidence"), "fix": f.get("fix")}
            for f in v15
        ],
        "v16_hits": [
            {"summary": f.get("summary"), "evidence": f.get("evidence"), "fix": f.get("fix")}
            for f in v16
        ],
        "ok": not v15 and not v16,
    }


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


def allow_extra_rows(
    cfg: Dict[str, Any], asserts: List[Dict[str, Any]], grade_meta: Optional[Dict[str, Any]] = None
) -> Tuple[bool, List[Dict[str, Any]]]:
    if grade_meta is not None:
        enabled = bool(grade_meta.get("allow_extra_failures"))
    else:
        enabled = bool(extract_grade_lists(cfg).get("allow_extra_failures"))
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
    gm = report.get("grade_meta") or {}
    if gm:
        L.append(
            f"Grade lists: fail_to_pass×{gm.get('fail_to_pass_count')} "
            f"(source={gm.get('fail_to_pass_source')})"
        )
        for w in gm.get("warnings") or []:
            L.append(f"> grading warning: {w}")
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
    L.append("| R | strong-linked GRADED A | weak A | status | decision |")
    L.append("|---|------------------------|--------|--------|----------|")
    for row in report["coverage"]:
        dec = report["decision_join"].get(f"coverage:{row['requirement_id']}", {})
        st = row["status"]
        if st == STATUS_NO_GRADED_LINK and dec.get("status") == "explained":
            st = "no_graded_link (explained)"
        elif st == STATUS_WEAK_LINK and dec.get("status") == "explained":
            st = "weak_link (explained)"
        aids = ", ".join(row["assertion_ids"]) or "—"
        weaks = ", ".join(row.get("weak_assertion_ids") or []) or "—"
        L.append(
            f"| {row['requirement_id']} | {aids} | {weaks} | {st} | {dec.get('status', '—')} |"
        )
    L.append("")
    L.append("### FAITHFULNESS (Assertion → Requirement)")
    L.append("| A | grade | severity | strong R | weak R | status | decision |")
    L.append("|---|-------|----------|----------|--------|--------|----------|")
    for row in report["faithfulness"]:
        dec = report["decision_join"].get(f"overreach:{row['assertion_id']}", {})
        st = row["status"]
        if st in FAITHFULNESS_TRIAGE_STATUSES and dec.get("status") == "explained":
            st = f"{row['status']} (explained)"
        rids = ", ".join(row["requirement_ids"]) or "—"
        wrids = ", ".join(row.get("weak_requirement_ids") or []) or "—"
        sev = row.get("severity") or "—"
        L.append(
            f"| {row['assertion_id']} | {row['grade']} | {sev} | {rids} | {wrids} | {st} | {dec.get('status', '—')} |"
        )
    L.append("")
    L.append(
        "> Lexical statuses (`no_graded_link` / `unlinked_lexically` / `weak_link`) are **candidate "
        "generators**, not confirmed defects. A single identifier token (e.g. `cell_map`) is "
        "`weak_link`, not green. `judge_rehearsal` applies P-011 triage; only CONFIRMED rows block preflight."
    )
    L.append("")

    L.append("## 2. Auto-REMOVE patterns (cite static-check; no re-detect)")
    L.append("| pattern | status | static_ids | notes |")
    L.append("|---------|--------|------------|-------|")
    for name, row in report["auto_remove"].items():
        L.append(
            f"| {name} | {row['status']} | {', '.join(row['static_ids']) or '—'} | {row.get('notes','')} |"
        )
    # bipartite lexical candidates (not confirmed overreach)
    oc = report.get("faithfulness_triage_candidates") or report.get("unlinked_lexically_candidates") or []
    if oc:
        L.append("")
        L.append(f"Faithfulness triage candidates (unlinked + weak_link): {', '.join(oc)}")
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
        f"{len(pk['hits'])} hit(s); tracked annotated, not suppressed |"
    )
    L.append(f"| problem_statement ≡ instruction | {'OK' if pk['instruction_sync_ok'] else 'FAIL'} | {pk['instruction_sync_detail']} |")
    L.append(
        f"| solution leakage on agent paths | {'HIT' if pk['leakage'] else 'OK'} | "
        f"{', '.join(pk['leakage'][:5]) or '—'} |"
    )
    if pk["hits"]:
        L.append("")
        L.append("Hits:")
        for h in pk["hits"][:40]:
            note = h.get("note") or h.get("class") or ""
            L.append(
                f"- `{h['path']}` (tracked={h.get('tracked')}; class={h.get('class')}) — "
                f"{h.get('remediation') or note}"
            )
    if pk.get("suppressed_with_justification"):
        L.append("")
        L.append("Suppressed (justified upstream source):")
        for h in pk["suppressed_with_justification"]:
            L.append(f"- `{h['path']}` — {h.get('justification')}")
    L.append("")

    L.append("## 4b. Grading configuration (V15 / V16)")
    gc = report.get("grading_config") or {}
    L.append(
        f"allow_extra_failures: **{gc.get('allow_extra_failures')}** — "
        f"{'OK' if gc.get('ok', True) else 'FIXABLE'}"
    )
    L.append("")
    L.append("| id | status | summary | evidence |")
    L.append("|----|--------|---------|----------|")
    if gc.get("v15_hits"):
        for h in gc["v15_hits"]:
            L.append(
                f"| V15 | HIT | {(h.get('summary') or '')[:70]} | {(h.get('evidence') or '')[:50]} |"
            )
    else:
        L.append("| V15 | CLEAR | allow_extra_failures is not true | — |")
    if gc.get("v16_hits"):
        for h in gc["v16_hits"]:
            L.append(
                f"| V16 | HIT | {(h.get('summary') or '')[:70]} | {(h.get('evidence') or '')[:50]} |"
            )
    else:
        L.append(
            "| V16 | CLEAR | no unrelated suite paths gating reward (or allow_extra true→V15) | — |"
        )
    L.append("")
    L.append(
        "Correct configuration: `allow_extra_failures=false` with the execution command "
        "scoped to the task's own tests (paths introduced by `tests.patch`)."
    )
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

    L.append("## 5b. Q9/Q10 instruction guards")
    q9 = report.get("q9_q10") or {}
    blocking = q9.get("blocking") or []
    path_cands = q9.get("path_candidates") or []
    L.append(
        f"Q10 error-message literals: **{'BLOCKING (' + str(len(blocking)) + ')' if blocking else 'CLEAR'}**"
    )
    for h in blocking[:10]:
        L.append(f"- words={h.get('words')}: {(h.get('snippet') or '')[:120]}")
    L.append(
        f"Q9 path-as-navigation candidates: **{len(path_cands)}** "
        "(rehearsal / P-011 triage — not prep blockers)"
    )
    for h in path_cands[:10]:
        L.append(f"- L{h.get('line')}: `{h.get('path')}` — {(h.get('snippet') or '')[:100]}")
    L.append("")

    L.append("## 5c. Private-internals candidates")
    pi = report.get("private_internals_candidates") or []
    L.append(
        f"{len(pi)} candidate(s) — graded assertion identifiers absent from instruction.md "
        "(rehearsal confirms via P-011; underscore / private subscript = higher severity)"
    )
    L.append("| assertion | id | kind | severity | note |")
    L.append("|-----------|----|------|----------|------|")
    for c in pi[:25]:
        L.append(
            f"| {c.get('assertion_id')} | `{c.get('identifier')}` | {c.get('kind')} | "
            f"{c.get('severity')} | {(c.get('note') or '')[:60]} |"
        )
    if not pi:
        L.append("| — | — | — | — | none |")
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
    spot = report.get("linked_spot_check") or {}
    if spot:
        L.append("## 6b. Linked-row spot check (strong `ok` sample)")
        L.append(
            f"seed=`{spot.get('seed')}` population={spot.get('population')} "
            f"sample_size={spot.get('sample_size')} rule=`{spot.get('sample_rule')}`"
        )
        L.append(f"assertion_ids: {', '.join(spot.get('assertion_ids') or []) or '—'}")
        L.append(f"> {spot.get('note') or ''}")
        L.append("")
    L.append("## 7. Handoff to judge_rehearsal")
    L.append(
        "Run `Prompts/modules/judge_rehearsal.md`: triage every `no_graded_link`, "
        "`unlinked_lexically`, and `weak_link` row with P-011 (stated / public API / neither), "
        "score Pass A (coverage-hostile) and Pass B (faithfulness-hostile), reconcile, flag "
        "axes differing by ≥2 for human review. Write `judge_rehearsal.md` **and** "
        "`judge_rehearsal.json` (fingerprint = sha256 of `judge_prep.json`). Only "
        "CONFIRMED_GAP / CONFIRMED_OVERREACH block preflight — not lexical candidates. "
        "A single shared identifier (e.g. `cell_map`) is `weak_link`, not green."
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
        base_report["inputs_hash"] = prep_inputs_hash(task_root)
        write_json(json_path, base_report)
        md_path.write_text(render_md(base_report), encoding="utf-8")
        # never overwrite decisions file
        if not decisions_path.is_file():
            write_json(decisions_path, {"schema_version": DECISIONS_SCHEMA, "decisions": []})
        return base_report

    instruction = instr_path.read_text(encoding="utf-8", errors="replace")
    patch_text = patch_path.read_text(encoding="utf-8", errors="replace")
    reqs = extract_requirements(instruction)
    asserts, grade_meta = extract_assertions(patch_text, cfg)
    coverage, faithfulness, map_stats = build_bipartite(reqs, asserts)
    auto_remove = cite_auto_remove(findings)
    # Lexical unlinked + weak_link for rehearsal — do NOT promote to auto_remove HIT.
    faithfulness_triage_candidates = [
        row["assertion_id"]
        for row in faithfulness
        if row["status"] in FAITHFULNESS_TRIAGE_STATUSES
    ]
    unlinked_lexically_candidates = [
        row["assertion_id"]
        for row in faithfulness
        if row["status"] == STATUS_UNLINKED_LEXICALLY
    ]
    weak_link_candidates = [
        row["assertion_id"]
        for row in faithfulness
        if row["status"] == STATUS_WEAK_LINK
    ]
    no_graded_link_candidates = [
        row["requirement_id"]
        for row in coverage
        if row["status"] in COVERAGE_TRIAGE_STATUSES
    ]

    packaging = packaging_sweep(task_root)
    dont = dont_list_scan(patch_text, findings)
    ae_enabled, ae_rows = allow_extra_rows(cfg, asserts, grade_meta)
    q9q10 = scan_q9_q10_instruction(instruction)
    private_internals = scan_private_internals(asserts, instruction)
    grading_config = grading_config_from_static(
        findings, {"allow_extra_failures": ae_enabled, **grade_meta}
    )

    reqs_by_id = {r["id"]: r for r in reqs}
    asserts_by_id = {a["id"]: a for a in asserts}
    decisions_doc = load_decisions(decisions_path)
    by_ref, invalidated = join_decisions(
        decisions_doc, coverage, faithfulness, ae_rows, reqs_by_id, asserts_by_id
    )

    blockers: List[str] = []
    # auto-REMOVE hits from static-check cites only (bipartite overreach is rehearsal work)
    for pattern, row in auto_remove.items():
        if pattern == "overreach":
            # Static-check overreach cite still counts as auto-REMOVE HIT
            if row["status"] == "HIT" and row.get("static_ids"):
                blockers.append(f"auto_remove:{pattern}:{','.join(row['static_ids'])}")
            continue
        if row["status"] == "HIT":
            blockers.append(f"auto_remove:{pattern}:{','.join(row['static_ids'])}")

    # Lexical candidates are informational — prep does NOT block on them (FIX B).
    # Still record unexplained lists for rehearsal handoff / decisions join display.
    unexplained_gaps = []
    for row in coverage:
        if row["status"] not in COVERAGE_TRIAGE_STATUSES:
            continue
        ref = f"coverage:{row['requirement_id']}"
        dec = by_ref.get(ref)
        if dec and dec.get("status") == "explained":
            continue
        unexplained_gaps.append(row["requirement_id"])

    unexplained_overreach = []
    for row in faithfulness:
        if row["status"] not in FAITHFULNESS_TRIAGE_STATUSES:
            continue
        ref = f"overreach:{row['assertion_id']}"
        dec = by_ref.get(ref)
        if dec and dec.get("status") == "explained":
            continue
        unexplained_overreach.append(row["assertion_id"])

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

    # Q10 error-message literal words — blocking (platform must-have / leakage)
    for i, hit in enumerate(q9q10.get("blocking") or [], 1):
        blockers.append(f"q10:error_message_literal:{i}")

    if invalidated:
        blockers.append("decisions:invalidated")

    # Open FIXABLE does not hard-stop but keeps prep_passed false
    if fixable_ids or not_fixable_ids:
        for fid in fixable_ids:
            blockers.append(f"static_fixable:{fid}")
        for fid in not_fixable_ids:
            blockers.append(f"static_not_fixable:{fid}")

    prep_passed = len(blockers) == 0

    spot_seed = hashlib.sha256(
        f"{task_name or task_root.name}|{len(asserts)}|{len(reqs)}|{len(faithfulness_triage_candidates)}".encode()
    ).hexdigest()[:16]
    linked_spot_check = sample_linked_spot_check(faithfulness, seed=spot_seed)

    report = {
        **base_report,
        "requirements": reqs,
        "assertions": asserts,
        "coverage": coverage,
        "faithfulness": faithfulness,
        "map_stats": map_stats,
        "grade_meta": {
            "fail_to_pass_source": grade_meta.get("fail_to_pass_source"),
            "pass_to_pass_source": grade_meta.get("pass_to_pass_source"),
            "required_pass_source": grade_meta.get("required_pass_source"),
            "fail_to_pass_count": len(grade_meta.get("fail_to_pass") or []),
            "warnings": grade_meta.get("warnings") or [],
            "allow_extra_failures": ae_enabled,
        },
        "grading_config": grading_config,
        "auto_remove": auto_remove,
        "faithfulness_triage_candidates": faithfulness_triage_candidates,
        "unlinked_lexically_candidates": unlinked_lexically_candidates,
        "weak_link_candidates": weak_link_candidates,
        "no_graded_link_candidates": no_graded_link_candidates,
        "linked_spot_check": linked_spot_check,
        # Back-compat aliases for older readers
        "overreach_unexplained": unexplained_overreach,
        "coverage_gaps_unexplained": unexplained_gaps,
        "dont_list": dont,
        "packaging": packaging,
        "allow_extra_failures": {"enabled": ae_enabled, "rows": ae_rows},
        "q9_q10": q9q10,
        "private_internals_candidates": private_internals,
        "decision_join": by_ref,
        "invalidated_decisions": invalidated,
        "prep_passed": prep_passed,
        "blockers": blockers,
        "candidate_note": (
            "no_graded_link / unlinked_lexically / weak_link / private_internals / "
            "q9 path-as-navigation are lexical candidates only; "
            "judge_rehearsal confirms via P-011 before preflight blocks. "
            "Q10 error-message literal words ARE prep blockers. "
            "linked_spot_check samples status=ok rows for SAMPLE_HIT detection."
        ),
        "inputs_hash": prep_inputs_hash(task_root),
    }

    write_json(json_path, report)
    md_path.write_text(render_md(report), encoding="utf-8")
    if not decisions_path.is_file():
        write_json(decisions_path, {"schema_version": DECISIONS_SCHEMA, "decisions": []})
    return report


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# Exact preflight message when task inputs diverge from the stored judge_prep.json.
PREP_INPUTS_CHANGED_MSG = (
    "prep inputs changed since rehearsal; re-run judge-prep then rehearsal"
)

# Paths hashed as named inputs (also covered by the tree walk; listed for clarity).
_PREP_NAMED_INPUTS = (
    "instruction.md",
    "tests/tests.patch",
    "tests/config.json",
)

_PREP_HASH_SKIP_PARTS = frozenset(
    {
        "__pycache__",
        ".pyc",
        ".DS_Store",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".venv",
        "node_modules",
        ".idea",
        ".vscode",
        "runs",
    }
)


def _prep_hash_skip(rel: str) -> bool:
    parts = Path(rel).parts
    for part in parts:
        if part in _PREP_HASH_SKIP_PARTS:
            return True
        if part.endswith((".pyc", ".orig", ".bak", ".swp", "~")):
            return True
    return False


def prep_inputs_hash(task_root: Path) -> str:
    """Deterministic hash of named prep inputs + task-tree file inventory.

    Used by preflight to detect drift without rewriting judge_prep.json.
    """
    h = hashlib.sha256()
    root = task_root.resolve()
    for rel in _PREP_NAMED_INPUTS:
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        p = root / rel
        if p.is_file():
            h.update(p.read_bytes())
        else:
            h.update(b"__MISSING__")
        h.update(b"\0")

    # Full tree: every file (content digest) and every empty directory marker.
    entries: List[str] = []
    if root.is_dir():
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            rel_dir = Path(dirpath).relative_to(root)
            keep: List[str] = []
            for d in sorted(dirnames):
                rel_d = (rel_dir / d).as_posix() if str(rel_dir) != "." else d
                if _prep_hash_skip(rel_d):
                    continue
                keep.append(d)
                full_d = Path(dirpath) / d
                try:
                    if full_d.is_dir() and not any(full_d.iterdir()):
                        entries.append(f"DIR:{rel_d}")
                except OSError:
                    entries.append(f"DIR:{rel_d}")
            dirnames[:] = keep
            for fn in sorted(filenames):
                full = Path(dirpath) / fn
                rel = full.relative_to(root).as_posix()
                if _prep_hash_skip(rel):
                    continue
                if full.is_symlink() or not full.is_file():
                    continue
                digest = hashlib.sha256(full.read_bytes()).hexdigest()
                entries.append(f"FILE:{rel}:{digest}")
    for e in sorted(entries):
        h.update(e.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def load_judge_prep_for_preflight(
    task_root: Path,
    judge_prep_path: Path,
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Read existing judge_prep.json for preflight — never regenerate.

    Returns (report, blockers). On success report is non-None and blockers empty
    for the inputs-hash check (callers still apply prep/rehearsal blockers).
    """
    if not judge_prep_path.is_file():
        return None, ["judge_prep.json missing (run judge-prep first)"]
    try:
        report = load_json(judge_prep_path)
    except (json.JSONDecodeError, OSError) as exc:
        return None, [f"judge_prep.json unreadable: {exc}"]
    stored = report.get("inputs_hash")
    if not stored:
        return None, [PREP_INPUTS_CHANGED_MSG]
    current = prep_inputs_hash(task_root)
    if stored != current:
        return None, [PREP_INPUTS_CHANGED_MSG]
    return report, []


def validate_judge_rehearsal(
    rehearsal: Dict[str, Any],
    judge_prep_path: Path,
    *,
    require_all_candidates: bool = True,
    prep_report: Optional[Dict[str, Any]] = None,
) -> Tuple[List[str], Dict[str, Any]]:
    """Return (blockers, summary). Empty blockers ⇒ rehearsal is preflight-ready."""
    blockers: List[str] = []
    if not judge_prep_path.is_file():
        return ["judge_rehearsal: judge_prep.json missing"], {}

    expected_fp = file_sha256(judge_prep_path)
    got_fp = str(rehearsal.get("judge_prep_fingerprint") or "")
    if not got_fp:
        blockers.append("judge_rehearsal: missing judge_prep_fingerprint")
    elif got_fp != expected_fp:
        blockers.append(
            f"judge_rehearsal: fingerprint mismatch (stale vs {judge_prep_path.name})"
        )

    triage = rehearsal.get("triage") or {}
    cov_rows = list(triage.get("coverage") or [])
    faith_rows = list(triage.get("faithfulness") or [])

    if prep_report is None and judge_prep_path.is_file():
        try:
            prep_report = load_json(judge_prep_path)
        except (json.JSONDecodeError, OSError):
            prep_report = None

    if require_all_candidates and prep_report and not prep_report.get("hard_stopped"):
        need_cov = {
            r["requirement_id"]
            for r in (prep_report.get("coverage") or [])
            if r.get("status") in COVERAGE_TRIAGE_STATUSES
        }
        need_faith = {
            r["assertion_id"]
            for r in (prep_report.get("faithfulness") or [])
            if r.get("status") in FAITHFULNESS_TRIAGE_STATUSES
        }
        got_cov = {r.get("requirement_id") for r in cov_rows}
        got_faith = {r.get("assertion_id") for r in faith_rows}
        missing_c = sorted(need_cov - got_cov)
        missing_f = sorted(need_faith - got_faith)
        if missing_c:
            blockers.append(f"judge_rehearsal: untagged coverage candidates: {','.join(missing_c)}")
        if missing_f:
            blockers.append(
                f"judge_rehearsal: untagged faithfulness candidates: {','.join(missing_f)}"
            )

    confirmed_gaps: List[str] = []
    confirmed_overreach: List[str] = []
    for row in cov_rows:
        v = row.get("verdict")
        rid = row.get("requirement_id")
        if v == "CONFIRMED_GAP":
            confirmed_gaps.append(str(rid))
            blockers.append(f"rehearsal:CONFIRMED_GAP:{rid}")
        elif v == "UNDECIDED":
            blockers.append(f"rehearsal:UNDECIDED_GAP:{rid}")
        elif v not in ("NOT_A_GAP", "CONFIRMED_GAP", "UNDECIDED"):
            blockers.append(f"rehearsal:bad_coverage_verdict:{rid}:{v}")

    for row in faith_rows:
        v = row.get("verdict")
        aid = row.get("assertion_id")
        if v == "CONFIRMED_OVERREACH":
            confirmed_overreach.append(str(aid))
            blockers.append(f"rehearsal:CONFIRMED_OVERREACH:{aid}")
        elif v == "UNDECIDED":
            blockers.append(f"rehearsal:UNDECIDED_OVERREACH:{aid}")
        elif v not in ("NOT_OVERREACH", "CONFIRMED_OVERREACH", "UNDECIDED"):
            blockers.append(f"rehearsal:bad_faith_verdict:{aid}:{v}")

    # Linked-row spot check (strong ok sample) — SAMPLE_HIT is a signal, not a packaging block
    # Canonical shape (Prompts/modules/judge_rehearsal.md): linked_spot_check.triage[]
    warnings: List[str] = []
    sample_hits: List[str] = []
    prep_spot = (prep_report or {}).get("linked_spot_check") or {}
    reh_spot = rehearsal.get("linked_spot_check") or {}
    need_sample = set(prep_spot.get("assertion_ids") or reh_spot.get("assertion_ids") or [])
    sample_rows = list(reh_spot.get("triage") or [])
    if not isinstance(sample_rows, list):
        sample_rows = []
    got_sample = {r.get("assertion_id") for r in sample_rows if isinstance(r, dict)}
    if require_all_candidates and need_sample:
        missing_s = sorted(need_sample - got_sample)
        if missing_s:
            blockers.append(
                f"judge_rehearsal: untagged linked_spot_check sample: {','.join(missing_s)}"
            )
        if reh_spot.get("seed") and prep_spot.get("seed") and reh_spot.get("seed") != prep_spot.get("seed"):
            blockers.append("judge_rehearsal: linked_spot_check seed mismatch vs judge_prep")
    for row in sample_rows:
        if not isinstance(row, dict):
            continue
        v = row.get("verdict")
        aid = row.get("assertion_id")
        if v == "SAMPLE_HIT" or (v == "CONFIRMED_OVERREACH" and aid in need_sample):
            sample_hits.append(str(aid))
            warnings.append(
                f"SAMPLE_HIT:{aid} — strong-linked row looks like overreach; "
                "consider widening triage for this task"
            )
        elif v == "UNDECIDED":
            blockers.append(f"rehearsal:UNDECIDED_SAMPLE:{aid}")
        elif v not in ("NOT_OVERREACH", "SAMPLE_HIT", "CONFIRMED_OVERREACH", "UNDECIDED", None):
            blockers.append(f"rehearsal:bad_sample_verdict:{aid}:{v}")

    summary = {
        "judge_prep_fingerprint_ok": got_fp == expected_fp and bool(got_fp),
        "confirmed_gaps": confirmed_gaps,
        "confirmed_overreach": confirmed_overreach,
        "sample_hits": sample_hits,
        "warnings": warnings,
        "n_coverage_triaged": len(cov_rows),
        "n_faithfulness_triaged": len(faith_rows),
        "n_sample_triaged": len(sample_rows),
        "platform_logic": rehearsal.get("platform_logic"),
        "operational_bar_3_5": rehearsal.get("operational_bar_3_5"),
    }
    return blockers, summary


def load_judge_rehearsal(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        return load_json(path)
    except (json.JSONDecodeError, OSError):
        return None


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
