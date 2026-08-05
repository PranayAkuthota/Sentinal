# Sentinel Submitter Platform-Workflow Setup Audit

**Date:** 2026-07-23  
**Workspace:** `/home/piyush/projects/terminal-bench/Sentinal`  
**Scope:** One-time rule-system alignment for submitter ZIP + platform-metadata → paste-ready form answers  
**Mode used:** Rule Maintenance Mode  

---

## 1. Files created

| Path | Role |
|------|------|
| `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` | Complete submitter platform-answer workflow (`alwaysApply: false`) |
| `sentinel_submitter_platform_workflow_audit.md` | This setup audit |

---

## 2. Files modified

| Path | Change summary |
|------|----------------|
| `CLAUDE.md` | Submitter activation phrases; mandatory load order includes new rule; submitter workflow routes to new rule; cross-file map updated |
| `AGENTS.md` | Entry-point lists new rule; submitter start instructions |
| `.cursor/rules/Review_Guidelines.mdc` | Short cross-refs to submitter workflow; precedence role-specific entry updated; live-form label note under Submitter |
| `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` | File-role table; exact verdict mapping; submitter ZIP checklist; Templates A/B/C aligned to Validity required + Invalid/Not Fixable |
| `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` | Cross-file reference only (document role table lists submitter workflow as not used in Reviewer Mode) |

---

## 3. Backup paths (non-empty; not overwritten)

| Backup | Bytes |
|--------|------:|
| `legacy_backup/CLAUDE.before-submitter-platform-workflow.md` | 19741 |
| `legacy_backup/AGENTS.before-submitter-platform-workflow.md` | 770 |
| `legacy_backup/Review_Guidelines.before-submitter-platform-workflow.mdc` | 33603 |
| `legacy_backup/Sentinel_Expert_Contributor_Reference.before-submitter-platform-workflow.mdc` | 22991 |
| `legacy_backup/Sentinel_Reviewer_Step_by_Step.before-submitter-platform-workflow.mdc` | 22007 |

---

## 4. New rule path

`.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc`

Frontmatter:

```yaml
---
description: Apply when the user provides a Sentinel task ZIP and platform metadata and asks to work as the submitter or produce submitter form answers
alwaysApply: false
---
```

---

## 5. Submitter activation phrases

- I am working as a submitter. Start working.
- Submitter mode. Start working.
- Start this task as a submitter.
- I am the submitter. Begin the task.
- Review and correct this Sentinel submission.

Do **not** activate from an isolated word such as “Fixable” or “Valid.”

When Submitter Mode is clear, do not ask for a long workflow paste.

---

## 6. ZIP handling behavior

- Auto-identify a single readable ZIP
- Inspect archive; locate task root (`instruction.md`, `task.toml`, `environment/`, `solution/`, `tests/`) at archive root, under `task/`, or one wrapper
- Locate `runs/` when available
- Do not require `_harborized`
- If multiple ZIPs: list candidates and ask which to use
- Do not guess by modification time alone
- Do not execute files from an unverified archive

---

## 7. Metadata verification behavior

Platform block (Original Directory Name, Category, Difficulty, Task Tags, Languages, Metadata) is **context to verify**, not assumed truth.

Compare against `task.toml`, repo languages, source PR/commit/issue, instruction, oracle, tests, runs, Ultra requirements.

Report mismatches. Do not invalidate solely for observational field drift unless validity-affecting under current rules.

---

## 8. Exact verdict mapping

| Internal assessment | Main analysis field | Validity required | Duplicate analysis |
| ------------------- | ------------------- | ----------------- | ------------------ |
| Valid as-is | Valid as-is | Valid-as-is | Valid-as-is |
| Fixable | Fixable | Fixable | Fixable |
| Not Fixable | Invalid/Not Fixable | Invalid | Invalid/Not Fixable |

---

## 9. Conditional form support

- **A Valid as-is:** confirmations, f2p count truthfulness, local oracle/NOP evidence
- **B Fixable:** components, issue checkboxes (including exact “Less than 10…” only when ≤9), detailed issues, files changed, PR scope, corrected confirmations (“More than 10…” only when ≥11)
- **C Not Fixable:** category, environment subcategory, evidence why permitted fixes fail

---

## 10. Time-tracking behavior

- Create `sentinel_submitter_session.json` outside the task package at start
- Record real timestamps and phases
- Draft elapsed minutes only; confirm with user before final answers
- Never invent times; use “User confirmation required” when unreliable

---

## 11. Output files (per submitter task; outside package)

| File | Purpose |
|------|---------|
| `sentinel_submitter_audit.md` | Detailed analysis |
| `sentinel_changes.md` | Changed files and reasons |
| `sentinel_platform_answers.txt` | Paste-ready platform answers |
| `sentinel_submitter_session.json` | Session times / phases |

Never under `environment/repo/`; never inside corrected upload ZIP.

---

## 12. Responsibility split

| File | Responsibility |
|------|----------------|
| `Review_Guidelines.mdc` | Authoritative project policy |
| `Sentinel_Submitter_Platform_Workflow.mdc` | Complete submitter platform-answer workflow |
| `Sentinel_Expert_Contributor_Reference.mdc` | Quick field mapping and checklist |
| `CLAUDE.md` | Mode activation and workflow routing |
| `AGENTS.md` | Concise entry-point instructions |
| `Sentinel_Reviewer_Step_by_Step.mdc` | Reviewer procedure |

---

## 13. Configuration-test results

Read-only configuration test after edits:

| Check | Result |
|-------|--------|
| New submitter rule exists with correct frontmatter | Pass |
| Submitter mode loads new rule (CLAUDE.md + AGENTS.md) | Pass |
| Submitter load order: Guidelines → Submitter Workflow → Expert Reference | Pass |
| ZIP identification / multi-ZIP ask behavior | Pass |
| Platform metadata treated as verifiable context | Pass |
| Exact verdict mapping rows | Pass |
| Exactly 10 f2p not labelled &lt;10; More than 10 only if ≥11 | Pass |
| Times not invented | Pass |
| Output files outside task package | Pass |
| Reviewer mode still routed to reviewer workflow | Pass |
| Conditional form paths A/B/C | Pass |
| Activation phrases + isolated-word guard | Pass |
| Five backups non-empty | Pass |
| No real Sentinel task package files present/modified | Pass |

**Overall:** Pass (13/13 after recheck; initial script miss on bold markdown for “modification time” was a test-string issue, not missing content).

---

## 14. Remaining limitations

- No live Sentinel task ZIP was present to exercise an end-to-end submitter run during setup.
- Docker/oracle/NOP execution paths are documented for real tasks; they were not executed in this setup pass (correct — no task package).
- Live platform UI may still add or rename fields; rules require following the live form when it conflicts with stored templates.
- Session time tracking depends on continuous tool/session access; interruptions still require user confirmation.

---

## 15. Confirmation

**No Sentinel task package and no repository source file outside `Sentinal/` was modified during this setup.**

Only rule/docs/orchestration files inside `/home/piyush/projects/terminal-bench/Sentinal` were created or updated, plus non-empty backups under `legacy_backup/`.
