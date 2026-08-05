# Module: Verifier Alignment (S5)

Load during Execution **03** / stage S5.

## Do
1. Map instruction → graded assertions (coverage gaps).
2. Map graded assertions → stated/implied requirements (faithfulness).
3. State meaningful f2p count vs ≥10 guideline and live “more than 10” (≥11).
4. Treat `allow_extra_failures=true` as coverage risk; promote real patch tests into f2p over filler.
5. Require git-applyable `tests.patch` for any corrected package.

## Do not
- Edit existing pass-to-pass sources
- Add shallow duplicate tests only to inflate counts
- Claim “More than 10” when count is exactly 10

## Handoff must include
Coverage/faithfulness gaps; f2p count; proposed Fixable test actions (notes only).
