# Sentinel Workflow Hardening Audit

**Date:** July 23, 2026  
**Workspace:** `/home/piyush/projects/terminal-bench/Sentinal`  
**Policy date:** July 22, 2026 (Sentinel Ultra)

---

## 1. Files changed

| Path | Change |
|------|--------|
| `automation/sentinel_submitter.py` | Full harden: prepare/audit/select-task/set-verdicts/sync/record-validation/preflight/package gates, workflow_state schema v3 |
| `automation/README.md` | Simple workflow + safety statements |
| `automation/integration_test_hardening.py` | New offline integration suite |
| `automation/integration_test_results.txt` | Latest results |
| `automation/config_test_branch_aware.py` | Aligned to hardened API (reason required; packaging blocked without preflight) |
| `CLAUDE.md` | Routing/safety; hierarchy principle; no policy redefinition |
| `AGENTS.md` | Concise entry; submitter/reviewer examples |
| `.cursor/rules/Review_Guidelines.mdc` | Hierarchy principle; Fixable network_mode/golden.patch/tests.patch cross-ref |
| `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` | Rewritten short checklist (15 sections) |
| `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` | Hierarchy + automation gate commands |
| `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` | Hierarchy + read-only reminder only |
| `sentinel_workflow_hardening_audit.md` | This report |

Official `document 1/2/3.txt` unchanged.

---

## 2. Backups created

`legacy_backup/workflow_hardening/20260723-200436/`

Includes non-empty copies of CLAUDE.md, AGENTS.md, all active `.mdc` rules, automation script/README/tests, plus `INSPECTION_NOTES.md`.

---

## 3. Git branch status

**Sentinal workspace root is not a Git repository** (no `Sentinal/.git`).

Parent `terminal-bench` is a Git repo and lists `Sentinal/` as untracked.

**Branch creation skipped** per instructions (do not initialize Git automatically). File backups used instead.

---

## 4. Rule contradictions removed

Active conflicts corrected:

- Expert Reference no longer says Cursor cannot add Fixable tests / cannot remove `network_mode` / cannot rename `solution.patch`.
- Quick reference no longer duplicates full platform templates or permanently read-only submitter language.
- Supporting files now defer to `Review_Guidelines.mdc`.
- Packaging no longer allowed without preflight/`ready_to_package`.

---

## 5. Quick-reference simplification

`Sentinel_Expert_Contributor_Reference.mdc` reduced to scannable sections 1–15 only (hierarchy, three fields, nine-case, branch table, reviewer table, Harbor structure, checklists, validation-by-role, packaging, common fields, legacy summary, master refs).

---

## 6. Workflow-state changes

Canonical state: `task_outputs/<task>/workflow_state.json` schema_version **3**.

Includes public/internal/duplicate/branch, audit flags, validation statuses, ready_to_finalize/ready_to_package, validation_level, blockers/warnings.

Migration from older schema backed up; Public/Duplicate conflicts block migration.

---

## 7. Audit changes

`audit` inspects **extracted_original** only, writes `audit_report.json` + `.md`, config/git/artifact reports. Does **not** assign verdicts.

---

## 8. Preflight changes

`preflight` enforces structural/branch gates, separates `ready_to_finalize` vs `ready_to_package`, sets validation_level including `locally_prepared_platform_evaluation_required` when Fixable locals are `not_run`.

---

## 9. Packaging protections

- `package-fixable` requires Fixable Public+Duplicate, recorded Internal, `ready_to_package`, immediate preflight, ZIP verify, manifest; atomic write; no partial ZIP on failure.
- `package-invalid` requires Invalid fields + explanation; labels evidence as manual-review; no corrected-valid ZIP.
- Valid-as-is never packages a task ZIP.

---

## 10. Multiple-root handling

If >1 credible root: intake exits non-zero, lists candidates, requires `select-task`. No alphabetical/mtime selection. No ZIP created from ambiguous roots.

---

## 11. Test and config validation

Parses `tests/config.json` structurally: commands, timeout, f2p/p2p, parser, reward path, duplicates, count≥10, best-effort ID matching with manual-review for parameterized IDs. Always notes semantic review still required.

---

## 12. Git-hygiene checks

Non-destructive: HEAD, base commit, remotes, dirty tree, reflog, filter drivers, unexpected refs, `.git` size, `tests.patch` apply check. No auto-repair.

---

## 13. Artifact scan

Forbidden caches/editor junk/`metadata.json`/`ground_truth.*` block packaging; leakage-name hints → manual semantic review; legacy patches → needs review.

---

## 14. Three-field behavior preserved

Public / Internal / Duplicate retained with live wording. Public must match Duplicate. Internal separate with required reason.

---

## 15. Nine-case behavior preserved

All nine Internal×Duplicate combinations tested and supported. Duplicate controls branch.

---

## 16. Common fields preserved

Difficulty, senior estimate, reviewer comments, initial/entire times required in workflow docs; times never invented.

---

## 17. Reviewer workflow status

Remains independent and read-only. Minor hierarchy/read-only cross-ref only. Still writes `review_answer.txt`.

---

## 18. Integration tests added

`automation/integration_test_hardening.py` covers multi-root, sync mismatch, f2p 9/10/11, duplicate IDs, parameterized IDs, patch failure, legacy patches, git remotes/dirty/reflog, forbidden artifacts, Valid-as-is evidence gates, Fixable flat ZIP, failed validation, Invalid evidence, Public/Duplicate mismatch, nine combos, state migration success/conflict, archive exclusion, original preservation, passed-without-evidence rejection.

---

## 19. Full test results

| Suite | Result |
|-------|--------|
| `python3 -m py_compile automation/*.py` | OK |
| `python3 automation/integration_test_hardening.py` | **TOTAL PASS=70 FAIL=0** |
| `python3 automation/config_test_branch_aware.py` | **TOTAL PASS=60 FAIL=0** |

---

## 20. Static-search results

Active docs/rules searched for: never-add-tests-in-Cursor, always-preserve-network_mode-without-Fixable-correction, permanently/strict read-only submitter packaging bans, unsupported verdict simplification.

Remaining “not permanently read-only” phrases are intentional affirmations.

`alwaysApply: true` only on `Review_Guidelines.mdc`.

---

## 21. Remaining limitations

1. Automation cannot prove semantic coverage/faithfulness.
2. Docker/oracle/NOP still require real evidence from Cursor/human via `record-validation`.
3. Git repair is not automated (explicit Fixable path reserved for humans/Cursor).
4. Live platform form may still change; live form wins.
5. Sentinal folder is not its own Git repo; hardening used file backups only.

---

## 22. Exact commands for the next real task

```bash
cd /home/piyush/projects/terminal-bench/Sentinal
python automation/sentinel_submitter.py intake --zip incoming_tasks/<task>.zip
python automation/sentinel_submitter.py prepare
python automation/sentinel_submitter.py audit
# If multiple roots:
# python automation/sentinel_submitter.py select-task <path>
python automation/sentinel_submitter.py set-verdicts \
  --public-analysis <...> --internal-validity <...> --duplicate-analysis <...> --reason "<evidence>"
# Fixable edits only in work/<task>/working_copy/
python automation/sentinel_submitter.py sync-problem-statement   # if needed
python automation/sentinel_submitter.py record-validation --check docker_build --status passed --evidence <log>
python automation/sentinel_submitter.py record-validation --check oracle --status passed --evidence <log> --reward 1.0
python automation/sentinel_submitter.py record-validation --check nop --status passed --evidence <log> --reward 0.0
python automation/sentinel_submitter.py preflight
python automation/sentinel_submitter.py package-fixable   # or package-invalid
python automation/sentinel_submitter.py status
```

---

## 23. Confirmation: no real Sentinel task modified

- No edits under `workspace_archive/legacy_work/fc3ad565_unimport/`.
- No real task ZIP packaged or overwritten.
- All tests used temporary mock ZIPs only; mocks deleted afterward.
- Official documents unchanged.
