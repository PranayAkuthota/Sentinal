# Case 10 · Difficulty metadata lies

**Status:** CONFIRMED (n≥2)

`task.toml` difficulty fields contradict each other or invent irregular `pass_at_k`
baselines while Judge is still the blocker (or packaging axis cites them). Not Case 03
FAIL EASY after Judge OK.

## Recognise it

- `model_difficulty medium supported only by irregular /3 baseline denominators`
- `model_difficulty medium contradicts difficulty hard; pass_at_k 0/3 irregular`

## Read first

- Harbor `task.toml` difficulty / model_difficulty fields
- `docs/SUBMITTER_BLOCKERS.md`
- Case 03 (FAIL EASY after Judge OK) — different stage and fix order

## Diagnose before editing

1. Read `difficulty`, `model_difficulty`, any `pass_at_k_*`.
2. Note whether Difficulty screen actually ran.
3. Written finding: metadata honesty vs need to change agent hardness.

## Fix — pick ONE direction per defect

| Shape | Fix |
|-------|-----|
| Irregular / invented pass_at_k | Delete those fields; do not invent replacements |
| medium vs hard contradiction | Align labels to one honest story |
| Explanation text | Soften to match reality |

**Recorded applied fix:** JF015 1e6ecbbd 07 — deleted irregular pass_at_k_*; kept medium. Next **unknown**.

Do not use Case 03 “expand PR hardness” as the first move when the cite is irregular baselines.

## Verify before repackaging

- [ ] No irregular pass_at_k left
- [ ] difficulty / model_difficulty agree
- [ ] Judge citations still handled if Judge blocked

## Do not

- Invent pass rates.
- Confuse with Case 03 FAIL EASY after Judge OK.

## Instances

- JF015 1e6ecbbd · irregular /3 denominators · **applied** delete fields · next **unknown**
- JF018 7b88ff8e · medium contradicts hard; pass_at_k 0/3 · unknown · unknown
