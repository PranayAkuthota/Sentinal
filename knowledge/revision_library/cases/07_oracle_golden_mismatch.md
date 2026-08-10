# Case 07 · Oracle / golden mismatch

**Status:** CONFIRMED (n≥2)

Golden patch or oracle behaviour disagrees with what instruction/tests require or claim.

## Recognise it

- `get_l3_sup_handler still takes opid_t rather than fixed-width identifier type`
- `golden doctests use brace patterns; cargo test claim`
- `MarketDataCoordinate __str__ uses assetId when marketDataAsset missing`
- `GIF/MP4 must decode under atypical suffixes; golden _is_gif treats .gif before payload; MP4-as-.gif fails`

## Read first

- Harbor solution / `golden.patch` / `solve.sh` expectations
- `.cursor/skills/sentinel-ultra-review/reference/` oracle notes if present
- Related: Case 08 if reverse-apply is involved

## Diagnose before editing

1. Quote the mismatch (symbol, claim, or file behaviour).
2. Decide: golden wrong, instruction/tests wrong, or both out of sync.
3. Confirm not Case 08 (idempotency) alone.

## Fix — pick ONE direction per defect

| Direction | When |
|-----------|------|
| Fix golden | Implementation must match stated/tested behaviour |
| Fix instruction/tests | Claim overstated; align to true golden behaviour |
| Both | Only when PR scope requires — keep one coherent contract |

Do not leave “cargo test claim” while doctests use forbidden patterns.

## Verify before repackaging

- [ ] Oracle applies clean; behaviour matches graded asserts
- [ ] instruction sync; no contradictory claims
- [ ] Local oracle reward recorded honestly (pitfall 18)

## Do not

- Patch only the narrative Files Changed without touching golden.
- Confuse with Case 08 reverse-apply.

## Instances

- JF019 7b88ff8e · get_l3_sup_handler still opid_t · unknown · unknown
- JF026 826cb164 · golden doctests brace patterns · unknown · unknown
- JF029 965e30ce · __str__ uses assetId · unknown · unknown
- JF054 eb599683 · GIF/MP4 suffix vs payload · unknown · unknown
