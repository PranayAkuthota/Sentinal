# Sentinel Ultra Rule-System Final Audit

**Date:** 2026-07-22 (workspace local: 2026-07-23)  
**Workspace root for this rule system:** `/home/piyush/projects/terminal-bench/Rough`

---

## 1. Files and locations

### Active

| Path | Role |
|------|------|
| `Rough/CLAUDE.md` | Orchestration / automation controller |
| `Rough/AGENTS.md` | Plain-Markdown entry point |
| `Rough/.cursor/rules/Review_Guidelines.mdc` | Authoritative policy (`alwaysApply: true`) |
| `Rough/.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` | Quick reference (`alwaysApply: false`) |
| `Rough/.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` | Reviewer procedure (`alwaysApply: false`) |
| `Rough/document 1.txt` | Official Ultra Contributor Guidelines |
| `Rough/document 2.txt` | Official Tasking Guide |
| `Rough/document 3.txt` | Harbor Framework / Glossary / FAQ |

No duplicate active `.mdc` copies remain in the Rough root. No `(2)`-suffixed active files were present.

---

## 2. Backups

| Backup | Bytes | Status |
|--------|------:|--------|
| `legacy_backup/CLAUDE.pre-final-fix-2026-07-22.md` | 18067 | Non-empty; preserved |
| `legacy_backup/Review_Guidelines.pre-final-fix-2026-07-22.mdc` | 29608 | Non-empty; preserved |
| `legacy_backup/Sentinel_Expert_Contributor_Reference.pre-final-fix-2026-07-22.mdc` | 17018 | Non-empty; preserved |
| `legacy_backup/Sentinel_Reviewer_Step_by_Step.pre-final-fix-2026-07-22.mdc` | 19442 | Non-empty; preserved |

Older pre-ultra backups also retained (not overwritten):

- `CLAUDE.pre-ultra-2026-03-25.md`
- `Review_Guidelines.pre-ultra-2026-03-25.mdc`
- `Sentinel_Expert_Contributor_Reference.pre-ultra-2026-03-25.mdc`
- `Sentinel_Reviewer_Step_by_Step.pre-ultra-2026-03-25.mdc`

---

## 3. Cursor configuration

| Check | Result |
|-------|--------|
| Policy always applies | Yes — `Review_Guidelines.mdc` `alwaysApply: true` |
| Quick reference always applies | No — `alwaysApply: false` |
| Reviewer workflow always applies | No — `alwaysApply: false` |
| `AGENTS.md` exists | Yes |
| `CLAUDE.md` exists | Yes |
| Cross-file paths resolve | Yes — active refs use `.cursor/rules/...` |

---

## 4. Corrections completed

| Correction | Done |
|------------|------|
| Canonical filenames | Yes (already canonical; no `(2)` rename needed) |
| Correct directory placement | Yes — `.mdc` → `.cursor/rules/` |
| Safe precedence | Yes — Ultra docs + live form first |
| Context-aware role detection | Yes — no isolated-keyword mode selection |
| Safe multiple-root handling | Yes — no mtime-only selection |
| Operational f2p target ≥11 | Yes — all four active files |
| Conditional submitter templates A–C | Yes — Reference + CLAUDE |
| Conditional reviewer templates D–F | Yes — Reviewer workflow + CLAUDE |
| Internal audit vs platform-output separation | Yes |
| Legacy compatibility preserved | Yes |
| Duplicate content reduced | Partially — routed via consistency maps; full policy not reprinted in CLAUDE |
| Current Harbor structure aligned | Yes |

---

## 5. Cross-file consistency table

| Rule | Guidelines | Quick Reference | Reviewer Workflow | CLAUDE | Status |
| ---- | ---------- | --------------- | ----------------- | ------ | ------ |
| Submitter verdicts Valid as-is / Fixable / Not Fixable | Yes | Yes | Yes (assessment) | Yes | OK |
| Reviewer Accept / Needs Revision / Reject | Yes | Yes | Yes | Yes | OK |
| Reject = max revisions only | Yes | Yes | Yes | Yes | OK |
| f2p: ≥10 guideline; ≥11 safest; 11–20 preferred | Yes | Yes | Yes | Yes | OK |
| Current Harbor: golden.patch, problem_statement, config.json, grade.py | Yes | Yes | Yes | Yes | OK |
| Legacy init_state / solution.patch handling | Yes | Yes | Yes | Yes | OK |
| Local exec: Valid as-is required; Fixable recommended; Reviewer optional | Yes | Yes | Yes | Yes | OK |
| PR scope expand-only | Yes | Yes | Yes | Yes | OK |
| No tracked repo source edits; no p2p mutation | Yes | Yes | Yes | Yes | OK |
| Packaging flat zip; no runs/; problem_statement sync | Yes | Yes | Yes | Yes | OK |
| Quality Check coverage + faithfulness blocking | Yes | Yes | Yes | Yes | OK |
| Platform-output separation (audit vs form) | Referenced | Templates A–C | Templates D–F | Explicit | OK |

### Outdated-phrase scan (active files)

Occurrences of old verdict/Harbor-ban phrases appear **only** in labelled legacy mapping or “removed rules” lists — not as active defaults.

---

## 6. Remaining warnings

1. **Platform checkbox wording:** Official docs say “at least 10” f2p; live Valid as-is form may say “more than 10.” Operational rule uses ≥11 as safest submission target. If the live form later changes, follow the live form.
2. **Cursor rule loading:** `alwaysApply: false` files rely on Cursor description / agent request matching. If a session fails to load the quick-reference or reviewer procedure, open those files or `@`-mention them.
3. **Workspace scope:** This rule system lives under `Rough/` (isolated from the parent terminal-bench repo `AGENTS.md`). Opening only the parent repo without `Rough` as context may not load these rules.
4. **Document vs rule divergence risk:** Official `document *.txt` remain separate. If Snorkel publishes newer Ultra docs, re-sync is required.

---

## 7. Modification safety

Confirmed: during this operation, **no** Sentinel task package, `instruction.md`, task `task.toml`, Dockerfile, tests, solution, `environment/repo/`, `runs/`, or source repository was modified.

Only these were changed:

- `Rough/CLAUDE.md`
- `Rough/AGENTS.md` (created)
- `Rough/.cursor/rules/*.mdc` (moved + updated)
- `Rough/legacy_backup/*` (new pre-final-fix backups added)
- `Rough/sentinel_rule_system_final_audit.md` (this file)
