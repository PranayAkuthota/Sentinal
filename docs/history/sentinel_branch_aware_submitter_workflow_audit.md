# Sentinel Branch-Aware Submitter Workflow Audit

**Date:** July 23, 2026  
**Workspace:** `/home/piyush/projects/terminal-bench/Sentinal`  
**Purpose:** One-time alignment to the final branch-aware submitter system.

---

## Files created

| Path | Purpose |
|------|---------|
| `automation/sentinel_submitter.py` | Cross-platform intake / status / package-fixable / package-invalid / archive / set-verdicts |
| `automation/README.md` | Automation usage notes |
| `automation/config_test_branch_aware.py` | Configuration test harness (mocks only) |
| `automation/config_test_results.txt` | Last config-test results (63 PASS / 0 FAIL) |
| `incoming_tasks/` | Drop zone for new task ZIPs |
| `work/` | Active task sessions (clean) |
| `task_outputs/` | Platform answers, reports, corrected/evidence ZIPs |
| `completed_tasks/` | Explicit archive destination for finished sessions |
| `workspace_archive/legacy_work/` | Preserved old work material |
| `legacy_backup/branch_aware_submitter_setup/20260723-172014/` | Pre-change rule backups |
| `sentinel_branch_aware_submitter_workflow_audit.md` | This audit |

---

## Files modified

| Path | Change |
|------|--------|
| `CLAUDE.md` | Rebuilt for branch-aware Submitter Mode routing (removed permanent read-only / auto-modify-everything) |
| `AGENTS.md` | Concise branch-aware entry point |
| `.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc` | Full branch-aware workflow (Duplicate-controlled branches) |
| `.cursor/rules/Sentinel_Expert_Contributor_Reference.mdc` | Branch table, common fields, Fixable working_copy matrix |
| `.cursor/rules/Review_Guidelines.mdc` | Restored Ultra policy from pre-read-only backup; added short branch-aware cross-ref only |
| `.cursor/rules/Sentinel_Reviewer_Step_by_Step.mdc` | Unchanged (Reviewer Mode remains independent/read-only) |

Official docs unchanged: `document 1.txt`, `document 2.txt`, `document 3.txt`.

---

## Backup paths

All non-empty backups under:

`legacy_backup/branch_aware_submitter_setup/20260723-172014/`

Containing:

- `CLAUDE.md` (23812 bytes)
- `AGENTS.md` (2072 bytes)
- `Review_Guidelines.mdc` (37384 bytes)
- `Sentinel_Submitter_Platform_Workflow.mdc` (26957 bytes)
- `Sentinel_Expert_Contributor_Reference.mdc` (26907 bytes)
- `Sentinel_Reviewer_Step_by_Step.mdc` (22126 bytes)

Additional historical references remain in `legacy_backup/` (including `*.before-read-only*` and `*.before-submitter-platform-workflow*`).

---

## Old work folder archive path

`workspace_archive/legacy_work/fc3ad565_unimport/`

Extracted from parent `Sentinal.zip` (was not present as a live `work/` tree in the unpacked workspace). Contents preserved unmodified (~16M). Clean empty `work/` recreated for future sessions.

---

## Final workspace structure

```text
Sentinal/
├── CLAUDE.md
├── AGENTS.md
├── document 1.txt
├── document 2.txt
├── document 3.txt
├── incoming_tasks/
├── work/
├── task_outputs/
├── completed_tasks/
├── workspace_archive/legacy_work/fc3ad565_unimport/
├── automation/
│   ├── sentinel_submitter.py
│   ├── README.md
│   ├── config_test_branch_aware.py
│   └── config_test_results.txt
├── .cursor/rules/
│   ├── Review_Guidelines.mdc
│   ├── Sentinel_Submitter_Platform_Workflow.mdc
│   ├── Sentinel_Expert_Contributor_Reference.mdc
│   └── Sentinel_Reviewer_Step_by_Step.mdc
└── legacy_backup/
    └── branch_aware_submitter_setup/20260723-172014/
```

Session layout:

```text
work/<task-name>/
├── original/
├── extracted_original/
├── working_copy/
├── session/{platform_input.txt,session.json,validation_logs/}
└── analysis/

task_outputs/<task-name>/
├── platform_answers.txt
├── submitter_audit.md
├── findings_and_changes.md
├── validation_summary.md
├── updated_zip_file/
└── invalid_evidence/
```

---

## Active submitter rule

`.cursor/rules/Sentinel_Submitter_Platform_Workflow.mdc`

Frontmatter:

- `description: Apply when the user provides a Sentinel task ZIP and platform metadata and asks for submitter analysis, correction, validation, packaging, or platform answers`
- `alwaysApply: false`

Flow:

ZIP + platform info → preserve original → complete audit → Public + Internal verdicts → Duplicate matches Public → branch on Duplicate → branch actions → chat answers + `task_outputs/`.

---

## Nine-case support

Internal Validity ∈ {Invalid, Fixable, Valid-as-is}  
Duplicate Analysis ∈ {Fixable, Invalid/Not Fixable, Valid-as-is}

All **nine** combinations are recordable. Public Main Analysis must match Duplicate Analysis semantically. Internal Validity remains separately recordable with a reason. Automation `set-verdicts` stores combinations; it does not invent them.

---

## Duplicate branch logic

| Duplicate Analysis | Branch opened |
| ------------------ | ------------- |
| Fixable | Fixable |
| Invalid/Not Fixable | Invalid/Not Fixable |
| Valid-as-is | Valid-as-is |

Internal Validity does **not** select the branch.

---

## Fixable correction behavior

- Audit original first (`extracted_original/` never mutated).
- Edit only `working_copy/`.
- Permitted components only; never edit tracked `environment/repo/` source; never mutate existing p2p tests.
- Validate corrected copy; package flat ZIP only when ready:

`task_outputs/<task>/updated_zip_file/<task>__corrected.zip`

- Excludes `runs/`, outer `task/` wrapper, reports, session/backups/caches.

---

## Invalid evidence behavior

- Diagnose blocker; do not claim success.
- Always prepare evidence package when technically possible:

`task_outputs/<task>/invalid_evidence/<task>__unfixable_evidence.zip`

- Manual-review package only — **not** a corrected valid submission ZIP.
- Include diagnostics, logs, reproduction notes, evidence summary; do not fabricate fix attempts.

---

## Valid-as-is behavior

- Confirm seven platform confirmations with evidence.
- Do not modify the task.
- Do not create corrected or evidence ZIPs.
- Preserve original ZIP unchanged.

---

## Common fields

Always answered for every branch:

- What makes this task difficult?
- Senior engineer estimate
- Comments for Reviewer
- Initial review time
- Entire submission time

---

## Time tracking

Recorded in `work/<task>/session/session.json` with real timestamps for intake, audit, fix, validation, packaging, final response, pauses, and user adjustments. Never invent times; use `User confirmation required` when unreliable.

---

## Chat output behavior

All platform answers are returned **directly in Cursor chat** and also saved to `task_outputs/<task>/platform_answers.txt` using the required A–N structure. Supporting reports: `submitter_audit.md`, `findings_and_changes.md`, `validation_summary.md`.

---

## Corrected ZIP behavior

Path: `task_outputs/<task-name>/updated_zip_file/<task-name>__corrected.zip`  
Created only on Fixable when ready. Never overwrites original.

---

## Evidence ZIP behavior

Path: `task_outputs/<task-name>/invalid_evidence/<task-name>__unfixable_evidence.zip`  
Created on Invalid/Not Fixable. Not a valid corrected submission.

---

## Configuration test results

Command:

```bash
python3 automation/config_test_branch_aware.py
```

Result: **TOTAL PASS=63 FAIL=0** (re-run confirmed).

Verified:

- Mock Fixable: original preserved, working_copy used, corrected flat ZIP without `runs/`, branch answers
- Mock Invalid: original preserved, evidence ZIP, no corrected-valid ZIP, unfixable explanation included
- Mock Valid-as-is: original preserved, no modification, no new ZIPs, seven confirmations, common fields, times not invented
- All nine Internal×Duplicate combinations route with Duplicate controlling branch; Public matches Duplicate; Internal separately recordable
- Archived / backup ZIPs ignored during intake discovery
- Real archived task `fc3ad565_unimport` unmodified
- Temporary mock data deleted after tests

---

## Remaining limitations

1. Automation performs **file management only** — humans/agents still perform the audit, verdict selection, and allowed content edits.
2. Local Docker/oracle/NOP execution is environment-dependent; workflow requires honest “not executed” labeling when unavailable.
3. Source PR browsing may be unavailable offline; mark PR comparison unverified rather than inventing conclusions.
4. Live platform form wording can still change; live form outranks stored templates.
5. `package-fixable` packages whatever is currently in `working_copy/` — readiness is a workflow responsibility, not auto-proven by the script.
6. Reviewer Mode files were not redesigned beyond reference consistency; reviewer remains independent.

---

## Confirmation: no real Sentinel task modified during setup

- No edits under `workspace_archive/legacy_work/fc3ad565_unimport/`.
- No real task ZIP was corrected or overwritten.
- Configuration tests used temporary mock ZIPs only; mocks deleted afterward.
- Official `document 1/2/3.txt` unchanged.
- Active changes limited to rule/orchestration/automation/workspace layout files listed above.
