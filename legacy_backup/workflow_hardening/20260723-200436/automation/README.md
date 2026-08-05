# Sentinel Submitter Automation

File-management helpers for the branch-aware Sentinel Ultra submitter workflow.

**This script does not decide verdicts and does not modify task logic.**

## Commands

```bash
python automation/sentinel_submitter.py intake [--zip PATH] [--task-name NAME] [--platform-input PATH|TEXT] [--force]
python automation/sentinel_submitter.py status [--task-name NAME]
python automation/sentinel_submitter.py set-verdicts --public-analysis ... --internal-validity ... --duplicate-analysis ... [--reason ...]
python automation/sentinel_submitter.py package-fixable [--task-name NAME]
python automation/sentinel_submitter.py package-invalid [--task-name NAME] [--summary-file PATH]
python automation/sentinel_submitter.py archive [--task-name NAME]
```

Works on Windows, Linux, and macOS with Python 3 standard library only.

## Layout produced by intake

```text
work/<task-name>/
├── original/<original-task-zip>
├── extracted_original/          # never mutate
├── working_copy/                # Fixable edits only
├── session/
│   ├── platform_input.txt
│   ├── session.json
│   └── validation_logs/
└── analysis/

task_outputs/<task-name>/
├── platform_answers.txt
├── submitter_audit.md
├── findings_and_changes.md
├── validation_summary.md
├── updated_zip_file/<task-name>__corrected.zip      # Fixable only
└── invalid_evidence/<task-name>__unfixable_evidence.zip  # Invalid only
```

## Safety rules

- Original ZIP is copied into `original/` and never overwritten.
- `extracted_original/` is never used for mutation-producing commands.
- Corrected ZIPs are flat task contents (no outer `task/`, no `runs/`, no reports/session/caches).
- Invalid evidence ZIPs are manual-review packages, not valid corrected submissions.
- ZIPs inside `legacy_backup/`, `workspace_archive/`, `work/`, `task_outputs/`, and `completed_tasks/` are ignored during intake discovery.
