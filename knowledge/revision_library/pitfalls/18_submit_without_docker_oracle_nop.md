# Pitfall 18 · Submit without Docker oracle/NOP

**Status:** PROVISIONAL (peer-ported; not independently verified in this repo)

**Not a task defect.** Check **before** claiming ready / uploading.
Never invent reward numbers.

## Recognise it

F-016: package marked ready / uploaded while local Docker build + oracle 1.0 + NOP 0.0
were never executed (“ready with caveat”, Docker NOT RUN, or invented rewards).

## Read first

- `knowledge/failures/F-016_submit_without_docker_oracle_nop.json`
- `AGENTS.md` / `CLAUDE.md` — never invent oracle/NOP
- Case 08 if solve.sh non-idempotent

## Diagnose before editing

1. Locate real `reward.txt` / validation log paths for docker_build, oracle, nop.
2. If missing: not ready — say so.

## Fix — pick ONE direction per defect

Run Docker build, oracle (ideally twice — Case 08), and NOP; record real paths.
If Docker cannot run: do not claim validated; do not invent 1.0/0.0.

## Verify before repackaging

- [ ] Real oracle 1.0 and NOP 0.0 paths recorded — or honest “not run”
- [ ] preflight refuses invented rewards

## Do not

- Route Judge feedback here.
- Paste “1.0 / 0.0” from memory.

## Instances

- FC016 F-016 · peer catalogue · run Docker oracle/NOP · **unverified** in this repo
