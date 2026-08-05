# Repo conventions (Sentinel Submitter)

Intentional conventions for reviewers and new engineers.

## Harbor required vs dialect-optional paths

Official Harbor Framework task structure (blocking / REQUIRED):

| Path | Role |
|------|------|
| `task.toml` | Metadata / resources / timeouts / network blocks |
| `instruction.md` | Agent-facing problem statement |
| `environment/Dockerfile` | Image build |
| `environment/repo/` | Pinned codebase |
| `environment/problem_statement.md` | Exact copy of `instruction.md` |
| `solution/solve.sh` | Oracle driver |
| `solution/golden.patch` | Canonical solution patch |
| `tests/test.sh` | Verifier entry; writes reward |
| `tests/tests.patch` | Fail-to-pass test additions |
| `tests/config.json` | Suite config / f2p / p2p ids |

Dialect-optional (informational only — never a packaging blocker by itself):

| Path | Notes |
|------|------|
| `tests/grade.py` | Some packages embed the grader only in `test.sh`; absence alone is not a defect. Mention in `dialect_notes` when `test.sh` embeds a grader and the sibling file is missing. |
| `tests/files/` | Legacy optional test assets |
| `docker_compose.yaml` / `docker-compose.yaml` (task root or under `environment/`) | If present, must not set `network_mode = "none"` |

## Official Ultra policy wins

If anything here conflicts with `.cursor/rules/Review_Guidelines.mdc` or official Ultra docs (`document 1/2/3.txt`), follow policy.

## Workspaces vs framework

| Path | Mutable during submitter work? |
|------|--------------------------------|
| `incoming_tasks/` | Drop ZIPs |
| `work/<task>/original/` | Never |
| `work/<task>/extracted_original/` | Never |
| `work/<task>/working_copy/` | Fixable only |
| `work/<task>/session/execution/` | Handoffs (`NN__handoff.md`) |
| `work/task ready_to_submit/` | Fixable corrected upload ZIPs only (delete-first refresh) |
| `task_outputs/` | Reports + ZIP mirrors / invalid evidence |
| `completed_tasks/` | Archive only |
| `knowledge/proposals/` | Append proposals |
| `knowledge/patterns/`, `knowledge/failures/` | Human promotion only |
| `docs/history/` | Historical audits only |
| `.cursor/rules/Review_Guidelines.mdc` | Policy change only with explicit authority |

## Naming

- Task folders: preserve platform ZIP stem (`*_submission`)
- Handoffs: `01__handoff.md` … `06__handoff.md` with `status: complete|blocked|partial`
- Corrected ZIP (upload): `work/task ready_to_submit/<task>__corrected.zip`
- Corrected ZIP (mirror): `task_outputs/<task>/updated_zip_file/<task>__corrected.zip`
- Evidence ZIP: `.../invalid_evidence/<task>__unfixable_evidence.zip`
- Patterns: `P-NNN_slug.md`; Failures: `F-NNN_slug.json`

## Python / paths

- Prefer `python3`
- Prefer absolute paths
- Always `--task-name` when multiple sessions exist
- Framework tests: `python3 -m pytest repo_tests/ -q`

## Prompts

- Execution `01–06` are the daily path; modules hold stage detail
- Orchestrators stay thin; do not grow a single mega-prompt
- Stage contracts live in `workflows/stages/`

## Automation boundaries

- Deterministic only: intake, audit structure, hygiene, packaging, checkpoint readiness, learning proposals
- Never: Public/Internal/Duplicate, instruction quality, coverage semantics, difficulty judgement

## Learning

- Capture after every task (S12)
- Promote patterns/failures with human review (`promote_learning.py`)
- Prefer ≥2 sightings before Operational Patterns updates
- Never rewrite historical submissions from learning scripts
