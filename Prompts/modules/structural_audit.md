# Module: Structural Audit (S2)

Load during Execution **01** / stage S2.

## Do
1. `audit --task-name TASK`
2. Record: required files, f2p/p2p counts, instruction sync, metadata limits, git hygiene, network fields
3. Treat `tests.patch` **git apply --check** as authoritative; note hunk/rename health
4. List ungraded `+def test_*` when `allow_extra_failures` is true

## Do not
- Decide Valid/Fixable/Invalid from structure alone
- Skip patch health because `patch(1)` looked green

## Handoff must include
Paths to audit artifacts; top warnings; f2p count; git-apply status.
