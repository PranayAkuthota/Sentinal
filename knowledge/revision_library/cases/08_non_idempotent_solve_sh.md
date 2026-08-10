# Case 08 · Non-idempotent solve.sh (reverse-apply)

**Status:** CONFIRMED (n≥2 in ledger+catalogue; FC015 peer-sourced)

`solve.sh` treats reverse-apply as a success fallback and undoes the golden on a later run.

## Recognise it

- `solve.sh reverse applies golden.patch when both forward paths fail; remove fallback`
- Catalogue F-015: pattern `git apply "$PATCH" || git apply --3way "$PATCH" || git apply -R "$PATCH"`

## Read first

- `knowledge/failures/F-015_non_idempotent_solve_sh_reverse_apply_second_oracle.json`
- Solution Harbor layout (`solution/solve.sh`, `golden.patch`)

## Diagnose before editing

1. Open `solution/solve.sh`; search for `apply -R`, `--reverse` as success path.
2. Confirm whether reverse is only used after failed forward applies.
3. Written finding: non-idempotent yes/no.

## Fix — pick ONE direction per defect

Make idempotent:

1. If `git apply --reverse --check` succeeds → already applied → exit 0.
2. Else forward-apply (optional `--3way`).
3. **Never** use `git apply -R` / `--reverse` as a success fallback.

**Recorded applied fix:** JF053 eb599683 07 — forward-only solve.sh. Next **unknown**.
FC015 notes peer-ported — treat independent verification as incomplete.

## Verify before repackaging

- [ ] No reverse success fallback in solve.sh
- [ ] Oracle run twice locally when Docker available — both 1.0 (do not invent)
- [ ] NOP still 0.0

## Do not

- Keep `|| git apply -R` “just in case.”
- Claim oracle idempotent without a second run when Docker works.

## Instances

- JF053 eb599683 · reverse applies golden · **applied** forward-only · next **unknown**
- FC015 F-015 · peer catalogue same pattern · recovery stated · **unverified** independently
