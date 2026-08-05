# Sentinel Submitter Blockers

Walk this list before claiming a Fixable package is ready to upload (Execution **06** / S11).  
Any open blocker → stop, fix, re-validate. Live platform form wording still wins when it conflicts.

Policy details: `.cursor/rules/Review_Guidelines.mdc`. Operational traps: `Sentinel_Submitter_Operational_Patterns.mdc`.

---

## A. Verdict & branch

1. Public Main Analysis missing or not recorded via `set-verdicts`
2. Public ≠ Duplicate Analysis
3. Fixable edits started before Execution **04** / S8 complete
4. Valid-as-is claimed but instruction/tests/oracle still need rewrites
5. Invalid path producing a “corrected valid” ZIP (evidence only)

## B. Instruction & leakage

6. `instruction.md` ≠ `environment/problem_statement.md` on corrected package
7. PR URLs, commit SHAs, hidden test names, or solution spoilers in instruction
8. Required public schemas/formats enforced by tests but missing from instruction
9. Over-prescriptive “where to edit” walkthrough that removes exploration

## C. Tests & grading

10. Fewer than **10** meaningful fail-to-pass tests (Fixable defect)
11. Claiming live “More than 10” when f2p count is ≤10
12. Critical patch tests ungraded while `allow_extra_failures=true`
13. `tests.patch` fails `git apply --check` (patch(1)-only green is insufficient)
14. Existing pass-to-pass sources modified (must stay byte-identical)
15. Filler/duplicate tests added only to inflate counts
16. Silent skips / fail-open missing-deps patterns in new tests
16b. Graded asserts (or reward-gating asserts under `allow_extra_failures: false`) not stated/implied in instruction → **overreach** / faithfulness fail (P-011)
16c. Coverage-only test chase without instruction sync (next Judge often flips to overreach)

## D. Oracle & solution

17. Legacy `solution.patch` not renamed to `golden.patch` on corrected current upload
18. Oracle does not satisfy instruction or games fixtures/hidden goldens
19. Solution material left in agent-readable paths

## E. Environment & metadata

20. Missing/wrong Harbor network blocks on Fixable corrected `task.toml` (require `[environment]=public`, `[agent]=allowlist`+`allowed_hosts=["api.portkey.ai"]`, `[verifier]=no-network`); or `network_mode="none"` still in `docker_compose.yaml`
21. Resource/timeout/gpu limits outside Ultra bounds
22. Dockerfile cannot build offline / tangled unrecoverable deps (then Invalid, not upload)
23. `tests/grade.py` absent while `test.sh` embeds a grader — **informational dialect note only** (optional extract via hygiene; never blocks packaging)

## F. Git hygiene

24. HEAD missing or commits after HEAD
25. Remotes or filter drivers remain
26. Dirty tree / reflog present / `.git` ≥ 100MB when avoidable
27. `base_commit_sha` disagrees with shipped repo HEAD and was not realigned

## G. Runtime evidence

28. Valid-as-is without Executed oracle `1.0` and NOP `0.0`
29. Invented rewards or missing evidence paths in `record-validation`
30. Claiming platform checks passed when the five-minute platform limit stopped the run
30b. Claiming Difficulty results when platform says Agent Judge blocked Difficulty (`Not run: difficulty screen`)
30c. Re-uploading for Difficulty while Agent Judge axes (esp. coverage/faithfulness) still fail — fix Judge first (P-010)
30d. Any Agent Judge axis below **3.5** (or “3 with reservations”) on a revision upload — revise Judge before expecting Difficulty (P-010 / P-011)
30e. Leaving `discuss (overreach)` unresolved — map Tests→Instruction and fix before re-check (P-011)

## H. Packaging

31. Preflight not `ready_to_package`
32. ZIP includes outer `task/` directory, `runs/`, reports, caches, or junk artifacts
33. Upload path not refreshed delete-first at `work/task ready_to_submit/<task>__corrected.zip`
34. Files Changed omits edited paths (Fixable)
35. Snorkel narrative fields written in LLM/audit-bot tone (workflow §13)

## I. Learning & archives

36. Mutating `extracted_original/` or overwriting `original/*.zip`
37. Learning scripts editing Ultra policy or rewriting historical ZIPs

---

**Clearance line (paste into 06 handoff):**  
`SUBMITTER_BLOCKERS: walked A–I; open=[none|list]; upload_path=…`
