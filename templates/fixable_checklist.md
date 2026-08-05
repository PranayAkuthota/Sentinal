# Fixable working_copy checklist (structural)

Use after semantic edits; does **not** replace expert coverage/faithfulness review.

- [ ] Edits only under `work/<task>/working_copy/`
- [ ] `extracted_original/` and `original/*.zip` untouched
- [ ] `instruction.md` == `environment/problem_statement.md` (byte-identical)
- [ ] `task.toml`: Harbor network blocks present (`env=public`, `agent=allowlist`+`api.portkey.ai`, `verifier=no-network`); compose `network_mode="none"` removed if present
- [ ] `solution/golden.patch` present (not only `solution.patch`)
- [ ] `solution/solve.sh` executable; container runs via `bash solve.sh` if needed
- [ ] `tests/grade.py` present when desired (dialect-optional; extract from embedded `test.sh` if useful — never blocking alone)
- [ ] `tests/tests.patch`: `git apply --check` passes on clean repo (not patch-only)
- [ ] No hunk line-count mismatches / empty context lines without leading space
- [ ] `fail_to_pass` ≥10 meaningful; ≥11 if claiming live “more than 10”
- [ ] Reviewed ungraded `+def test_*` names in patch vs `fail_to_pass`
- [ ] If `allow_extra_failures: true`, confirmed instruction-critical tests are graded
- [ ] Faithfulness: every graded / reward-gating assert is stated or implied in instruction (no overreach; P-011)
- [ ] Platform revision: Agent Judge axes targeted ≥ 3.5 before expecting Difficulty (P-010)
- [ ] Did not edit tracked `environment/repo/` sources or existing p2p tests
- [ ] Local oracle 1.0 / NOP 0.0 recorded with evidence (or explicitly Not verified)
- [ ] `preflight` → `ready_to_package` before `package-fixable`
- [ ] Upload ZIP is flat task contents only (no `runs/`, no reports)
- [ ] Upload path exists: `work/task ready_to_submit/<task>__corrected.zip`

Commands:

```bash
python3 automation/sentinel_submitter.py ensure-packaging-hygiene --task-name TASK
python3 automation/sentinel_submitter.py sync-problem-statement --task-name TASK
python3 automation/local_oracle_nop.py --task-name TASK --mode both
python3 automation/sentinel_submitter.py preflight --task-name TASK
python3 automation/sentinel_submitter.py package-fixable --task-name TASK
# upload: work/task ready_to_submit/<TASK>__corrected.zip
```
