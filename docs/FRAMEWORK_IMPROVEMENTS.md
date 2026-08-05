# Sentinel Framework Improvements (July 30, 2026)

Based on completing one full submitter task (`gs-quant` PR #16 style Harbor package).  
**No completed task artifacts were modified.**

---

## 1. Improvement plan

| Gap observed on first task | Framework change |
|----------------------------|------------------|
| Manual Docker oracle/NOP scripting | `automation/local_oracle_nop.py` + `docker_grade_f2p.py` |
| `grade.py` missing though embedded in `test.sh` | `ensure-packaging-hygiene` extracts it |
| `network_mode`/`allowed_hosts` easy to get wrong | Same hygiene command ensures Harbor blocks; preflight blocks missing/wrong values |
| `tests.patch` “applies” via GNU patch but fails `git apply` / breaks renames | Health analyzer + Fixable preflight blocker |
| Ungraded tests under `allow_extra_failures` | Audit warning listing `+def test_*` not in `fail_to_pass` |
| Single ambiguous `Command_Prompt.md` | Split into First Pass vs Platform Revision prompts |
| Repeated platform answer / report structure | `templates/` |
| Knowledge only in chat memory | `Sentinel_Submitter_Operational_Patterns.mdc` + this doc |
| cwd/`python`/`--task-name` friction | Documented in CLAUDE/AGENTS/Operational Patterns |

---

## 2. Modified files

| File | Change |
|------|--------|
| `automation/sentinel_submitter.py` | Patch health, ungraded-test warnings, reward path via `artifacts`, `ensure-packaging-hygiene`, stricter Fixable preflight on git-apply |
| `automation/README.md` | Document new commands/helpers |
| `CLAUDE.md` | Routing to prompts/patterns; absolute paths; extended automation flow |
| `AGENTS.md` | Entry points for patterns, prompts, local validate, hygiene |
| `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` | Pointers to patterns/helpers; git-apply requirement |
| `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` | Recurring traps section |
| `Prompts/Command_Prompt.md` | Router only (no duplicated revision essay) |

---

## 3. Newly created files

| File | Purpose |
|------|---------|
| `.cursor/rules/Sentinel_Submitter_Operational_Patterns.mdc` | Reusable traps (agent-requestable) |
| `Prompts/Submitter_First_Pass.md` | New-task submitter prompt |
| `Prompts/Submitter_Platform_Revision.md` | Post-eval revision prompt |
| `templates/platform_answers_fixable.txt` | Platform answers skeleton |
| `templates/submitter_audit.md` | Audit skeleton |
| `templates/findings_and_changes.md` | Findings skeleton |
| `templates/validation_summary.md` | Validation skeleton |
| `templates/fixable_checklist.md` | Structural Fixable checklist |
| `automation/local_oracle_nop.py` | Local Docker oracle/NOP |
| `automation/docker_grade_f2p.py` | In-container f2p reward helper |
| `docs/FRAMEWORK_IMPROVEMENTS.md` | This document |

---

## 4. Explanation + expected benefit (per change)

1. **Patch health / git-apply gate** — Prevents shipping rename-broken `tests.patch` that looked green under `patch(1)`.  
2. **Ungraded-test warning** — Surfaces coverage holes when `allow_extra_failures` hides failing tests.  
3. **ensure-packaging-hygiene** — Removes repetitive mechanical edits that blocked preflight.  
4. **local_oracle_nop** — Standardizes Executed evidence; reduces ad-hoc Docker one-liners and shebang/`+x` mistakes.  
5. **Split prompts** — Stops mixing first-pass and revision instructions; reduces missed steps.  
6. **Operational Patterns + templates** — Captures reusable knowledge without bloating `alwaysApply` policy.  
7. **CLAUDE/AGENTS updates** — Consistency for path/`python3`/`--task-name` discipline.

---

## 5. Automation added

- `ensure-packaging-hygiene` (verdict-gated to Fixable; `working_copy` only)  
- `local_oracle_nop.py` / `docker_grade_f2p.py`  
- Stronger audit/preflight structural signals (still **no auto-verdicts**)

**Not automated (requires human judgement):** Public/Internal/Duplicate verdicts, instruction rewrite quality, semantic coverage/faithfulness, Not Fixable scope calls, difficulty expansion design.

---

## 6. Remaining weaknesses

- Local validator grades listed f2p only (does not replace full Harbor `test.sh` embedding nuances).  
- `ensure_network_blocks_in_task_toml` reuses `fix_common.apply_network_blocks` (line-oriented; creates missing sections).  
- No automated PR fetcher (curl/`gh` still manual).  
- No reviewer-mode templates yet.  
- Multi-session UX still requires explicit `--task-name` (by design).  
- Does not auto-regenerate corrupt `tests.patch` (expert must rebuild).  
- Platform UI field labels can drift; live form still wins.

---

## 7. Recommendations after N tasks

### After 5 tasks
- Collect top 5 recurring Fixable issue checkboxes; extend Operational Patterns only if ≥2 occurrences.  
- If `local_oracle_nop` mismatches platform Oracle Check twice, align helper with real `test.sh` invocation.  
- Add a tiny `prompts` smoke checklist in `templates/`.

### After 10 tasks
- Consider a read-only `audit --json-summary` dashboard across `task_outputs/*/workflow_state.json` (counts of issue types).  
- If grade extraction is always needed for a batch format, keep hygiene command; if platform starts shipping `grade.py`, narrow the helper.  
- Add reviewer answer template once reviewer assignments are in regular use.

### After 25 tasks
- Evaluate whether a curated “known Harbor packing dialects” table (embedded grader vs sibling `grade.py`, init_state vs golden) belongs in Expert Reference.  
- Only then consider semi-automated instruction lint (over-prescription heuristics) — never auto-rewrite.  
- Re-audit automation blockers against live platform form changes.

---

## 8. Compatibility

- Policy precedence unchanged (`Review_Guidelines.mdc` still sole `alwaysApply`).  
- Existing intake → package flow preserved; new steps are optional helpers except stricter git-apply preflight for Fixable.  
- Completed / archived task outputs intentionally untouched.
