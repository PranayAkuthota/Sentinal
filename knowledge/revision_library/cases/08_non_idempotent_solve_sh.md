# Case 08 · Non-idempotent solve.sh (reverse-apply)

**Status:** CONFIRMED (n≥2 ledger+catalogue; FC015 peer-sourced)

`solve.sh` uses reverse-apply as a success fallback and undoes the golden on a later run.

## Recognise it

- `solve.sh reverse applies golden.patch when both forward paths fail; remove fallback`
- F-015: `git apply … \|\| … \|\| git apply -R`

## Read first

- `knowledge/failures/F-015_*.json`
- `OUTCOMES.md`

## Diagnose before editing

1. Search solve.sh for `apply -R` / `--reverse` as success path.
2. Written finding: non-idempotent yes/no.

## Fix — pick ONE direction per defect

| Action | Evidence |
|--------|----------|
| Idempotent: reverse `--check` → exit 0 if applied; else forward-apply; **never** `-R` as success | **EVIDENCED WORKING** — reverse-apply cites **resolved** next round on **3** tasks: `0cf2e9a3`, `1e6ecbbd`, `d41a2c3a`. |
| Keep `\|\| git apply -R` “just in case” | **EVIDENCED FAILING** pattern (the defect itself). |

JF053 eb599683: forward-only applied in handoff; **next-round UNTESTED** (no following response yet).

## Verify before repackaging

- [ ] No reverse success fallback
- [ ] Oracle twice when Docker available (do not invent)
- [ ] NOP 0.0

## Do not

- Leave reverse fallback.
- Claim idempotent without a second oracle run when Docker works.

## Instances

- Chain · 0cf2e9a3 / 1e6ecbbd / d41a2c3a · reverse-apply · **resolved** next round
- JF053 eb599683 · forward-only **applied** · next **unknown**
- FC015 F-015 · peer · unverified independently
