# Sentinel Ultra Rule-System Final Audit

**Date:** 2026-07-22 (workspace local: 2026-07-23)  
**Workspace root for this rule system:** `/home/piyush/projects/terminal-bench/Rough`  
**Last correction pass:** final f2p / checkbox / loading / difficulty / packaging / platform-runtime fix

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

No duplicate active `.mdc` copies in the Rough root.

---

## 2. Backups

### Before this final f2p correction (new)

| Backup | Bytes | Status |
|--------|------:|--------|
| `legacy_backup/CLAUDE.before-final-f2p-fix.md` | 15901 | Non-empty |
| `legacy_backup/Review_Guidelines.before-final-f2p-fix.mdc` | 31114 | Non-empty |
| `legacy_backup/Sentinel_Expert_Contributor_Reference.before-final-f2p-fix.mdc` | 21006 | Non-empty |
| `legacy_backup/Sentinel_Reviewer_Step_by_Step.before-final-f2p-fix.mdc` | 21073 | Non-empty |
| `legacy_backup/sentinel_rule_system_final_audit.before-final-f2p-fix.md` | 5741 | Non-empty |

Older backups retained (not overwritten): `*.pre-final-fix-2026-07-22.*`, `*.pre-ultra-2026-03-25.*`.

---

## 3. Cursor configuration

| Check | Result |
|-------|--------|
| Policy always applies | Yes — `Review_Guidelines.mdc` `alwaysApply: true` |
| Quick reference always applies | No — `alwaysApply: false` |
| Reviewer workflow always applies | No — `alwaysApply: false` |
| `AGENTS.md` exists | Yes |
| `CLAUDE.md` exists | Yes |
| Cross-file paths resolve | Yes — `.cursor/rules/...` |
| Role-specific files explicitly loaded by `CLAUDE.md` | Yes — **Mandatory Role-Specific Rule Loading** |

---

## 4. Corrections completed (this pass)

| Correction | Done |
|------------|------|
| Official minimum = at least 10 meaningful f2p | Yes |
| Fixable test-count = fewer than 10 only | Yes |
| Exactly 10 meets guideline; not automatically Fixable | Yes |
| Live-form “more than 10” handling | Yes |
| Preferred practical range 11–20; no filler | Yes |
| Exact checkbox: “Less than 10 fail-to-pass tests in the test suite” | Yes |
| Exact confirmation: “More than 10 fail-to-pass tests in the test suite” | Yes |
| Mandatory role-specific rule loading | Yes |
| Difficulty Handling After Corrections | Yes |
| Expanded packaging sweep (`metadata.json`, `ground_truth.*`, `*.orig`, `*.bak`, `*.swp`, `*~`) | Yes |
| Five-minute platform runtime note | Yes |
| Legacy compatibility preserved | Yes |

---

## 5. f2p test-count rule (authoritative summary)

f2p test-count rule:

- Fewer than 10 is a Fixable test-count defect.
- Exactly 10 meets the documented guideline.
- When the live platform requires “more than 10,” add at least one meaningful test before selecting that confirmation.
- The preferred practical target is 11–20 meaningful fail-to-pass tests.
- Filler tests are prohibited.

Status: Consistent across all active rule files.

---

## 6. Cross-file consistency table (final validation)

| Check | CLAUDE | Guidelines | Quick Reference | Reviewer Workflow | Status |
| --------------------------------------- | ------ | ---------- | --------------- | ------------------ | ------ |
| Official minimum is at least 10 | Yes | Yes | Yes | Yes | Pass |
| Fewer than 10 is Fixable | Yes | Yes | Yes | Yes | Pass |
| Exactly 10 is not automatically Fixable | Yes | Yes | Yes | Yes | Pass |
| More than 10 live-form handling | Yes | Yes | Yes | Yes | Pass |
| Preferred range is 11–20 | Yes | Yes | Yes | Yes | Pass |
| Exact checkbox wording | Yes | Yes | Yes | Yes | Pass |
| Role-specific rule loading | Yes | Referenced | Referenced | Referenced | Pass |
| Difficulty handling | Routed | Yes | Yes | Reviewer check | Pass |
| Expanded packaging sweep | Yes | Yes | Yes | Yes | Pass |
| Five-minute platform note | Yes | Yes | Yes | Relevant reference | Pass |
| Legacy compatibility preserved | Yes | Yes | Yes | Yes | Pass |
| No task files modified | Yes | Yes | Yes | Yes | Pass |

### Forbidden-phrase scan

Active files contain **none** of:

- Fewer than the safest required f2p target
- Below the operational target
- Exactly 10 is automatically Fixable
- 11 is the official minimum
- Less than the preferred f2p count

### Required-phrase scan

Present in appropriate files:

- Less than 10 fail-to-pass tests in the test suite
- More than 10 fail-to-pass tests in the test suite
- At least 10 meaningful fail-to-pass tests
- 11–20 meaningful fail-to-pass tests
- Mandatory Role-Specific Rule Loading
- Difficulty Handling After Corrections
- five-minute / metadata.json / ground_truth.*

---

## 7. Remaining warnings

1. Live platform form wording may still change; always follow the live form when it conflicts with a stored template.
2. `alwaysApply: false` rules still depend on Cursor matching / explicit `@` / Mandatory Role-Specific Rule Loading in `CLAUDE.md`.
3. This rule system lives under `Rough/`; opening only the parent terminal-bench repo may not load it.

---

## 8. Modification safety

Confirmed: during this correction pass, **no** Sentinel task package, `instruction.md`, task `task.toml`, Dockerfile, tests, solution, `environment/repo/`, `runs/`, or source repository was modified.

Only these were changed:

- `Rough/CLAUDE.md`
- `Rough/AGENTS.md`
- `Rough/.cursor/rules/Review_Guidelines.mdc`
- `Rough/.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc`
- `Rough/.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc`
- `Rough/sentinel_rule_system_final_audit.md`
- `Rough/legacy_backup/*before-final-f2p-fix*`
