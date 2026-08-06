# Reconciliation: `check_task.py` vs main pipeline

**Date:** 2026-08-05  
**Skill location (after move):** `.cursor/skills/sentinel-ultra-review/scripts/check_task.py`  
**Main:** `automation/sentinel_submitter.py` audit / preflight / helpers  

Legend: **Agree** · **Main weaker/missing** · **Disagree** · **Main stronger** · **Partial**

Adoption (approved): every Main-weaker/missing row → adopt `check_task` at its severity; G1 take stricter FIXABLE; preserve `analyze_tests_patch_health`; S2 adopt rename flagging for `tests/test.patch`; `tests/grade.py` is dialect-optional (not REQUIRED).

---

## S* — structure

| ID | check_task | Main equivalent | Status |
|----|------------|-----------------|--------|
| **S1** | Required Harbor artifacts missing | `required_files_report` / Fixable preflight | **Partial** → align REQUIRED to ten Harbor paths (no `grade.py`) |
| **S2** | Non-canonical names (`solution.patch` / `test.patch`) → FIXABLE for golden/tests | Legacy noted; Fixable requires `golden.patch` | **Partial** → adopt systematic rename flagging for `tests/test.patch` too |

## T* — task.toml / compose

| ID | check_task | Main equivalent | Status |
|----|------------|-----------------|--------|
| **T0** | TOML parse failure | Soft-fail line parser | **Main weaker** |
| **T1** | Missing `[environment]` resource keys | Partial warnings | **Main weaker** |
| **T2** | Resource values out of range | `metadata_limits_report` | **Agree** |
| **T3–T6** | Network blocks required | `validate_network_blocks` | **Agree** |
| **T7** | Missing `agent.timeout_sec` → ADVISORY | Silent if absent | **Main weaker** |
| **T8** | `agent.timeout_sec` > 7200 → FIXABLE | Same | **Agree** |
| **T9** | `verifier.timeout_sec` > 1800 → FIXABLE | Same | **Agree** |
| **T10** | Missing `[metadata].source` → FIXABLE | Not checked | **Main weaker** |
| **T11** | source not URL-like → ADVISORY | Not checked | **Main weaker** |
| **T12** | Missing category / difficulty_explanation → ADVISORY | Not checked | **Main weaker** |
| **T13** | compose `network_mode=none` → FIXABLE | Preflight compose scan | **Agree** |

## X* — instruction (mechanical)

| ID | check_task | Main | Status |
|----|------------|------|--------|
| **X1** | Over-prescriptive / verifier internals → FIXABLE | None | **Main weaker** |
| **X2** | LLM/template tells → ADVISORY | None | **Main weaker** |
| **X3** | Very short instruction → ADVISORY | None | **Main weaker** |

## L* — leakage

| ID | check_task | Main | Status |
|----|------------|------|--------|
| **L1** | Leakage in `instruction.md` → FIXABLE | None | **Main weaker** |
| **L2** | Leakage in `problem_statement.md` → FIXABLE | Sync only | **Main weaker** |
| **L3** | Solution material under `environment/repo` → FIXABLE | Narrow `artifact_scan` | **Partial / Main weaker** |

## P* — packaging / sync

| ID | check_task | Main | Status |
|----|------------|------|--------|
| **P1** | `problem_statement.md` ≠ `instruction.md` → FIXABLE | `check_instruction_sync` | **Agree** |
| **P2** | Stray artifacts → FIXABLE | `artifact_scan` | **Agree** |
| **P3** | `runs/` inside task root → ADVISORY | Not checked | **Main weaker** |

## V* — tests

| ID | check_task | Main | Status |
|----|------------|------|--------|
| **V0–V2** | config / empty f2p / f2p &lt; 10 | `validate_config` | **Agree** |
| **V3** | f2p &gt; 25 → ADVISORY | None | **Main weaker** |
| **V4** | Empty `pass_to_pass` → ADVISORY | Warning | **Agree** |
| **V5** | Patch touches non-test files → ADVISORY | None | **Main weaker** |
| **V6** | Patch deletes pre-existing test lines → FIXABLE | None | **Main weaker** |
| **V7** | f2p ids not in patch-added tests → FIXABLE | Partial blob search | **Partial** |
| **V8** | Few patch test defs when f2p empty → FIXABLE | Partial | **Partial** |
| **V9** | Auto-REMOVE patterns → FIXABLE | **None** | **Main weaker** (critical) |
| **V10** | Existence-only assertions → FIXABLE | None | **Main weaker** |
| **V11–V12** | Agent-controls-coverage / verifier-only constants → ADVISORY | None | **Main weaker** |
| **V13** | `test.sh` never writes reward → FIXABLE | Weak config warning | **Partial** |
| **V14** | CLI in instruction, suite never invokes → ADVISORY | None | **Main weaker** |
| *(main-only)* | Hunk / git-apply vs patch-only | `analyze_tests_patch_health` | **Main stronger** — **preserve** as PH1 |

## O* — oracle

| ID | check_task | Main | Status |
|----|------------|------|--------|
| **O1–O2** | Small / single-file oracle → ADVISORY | None | **Main weaker** |
| **O3–O4** | Tests-only golden / gaming → FIXABLE | None | **Main weaker** |
| **O5–O6** | shebang / +x on `solve.sh` → FIXABLE | Hygiene partial | **Partial** |

## D* — Dockerfile

| ID | check_task | Main | Status |
|----|------------|------|--------|
| **D1** | Unpinned / `:latest` | `:latest` only | **Partial** |
| **D2–D8** | Alpine/bash, tmux, asciinema, apt-update, COPY missing, model download, CRLF | Mostly none | **Main weaker** |

## G* — git

| ID | check_task | Main | Status |
|----|------------|------|--------|
| **G1** | `.git` missing → FIXABLE | Was warning + ok=True | **Disagree** → adopt FIXABLE |
| **G2–G3, G5–G10** | HEAD, remotes, filters, dirty, reflog, size, apply | Largely present | **Agree / Partial** |
| **G4** | Commits beyond HEAD | Unexpected-refs heuristic | **Partial** |

## Ruling: `tests/grade.py`

Official Harbor Framework REQUIRED layout does **not** include `grade.py`.  
Split: **REQUIRED** (ten paths) vs **DIALECT_OPTIONAL** (`grade.py`, `tests/files/`, compose).  
Missing `grade.py` is informational only when `test.sh` embeds a grader — never blocking.
