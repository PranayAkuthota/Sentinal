# Case 13 · Fail-open scan-loop

**Status:** CONFIRMED-BY-RULE

Official Ultra docs name **Fail-open** as auto-REMOVE. FC012: ~23 scan-loop `else: pass`
idioms in one package; V9 missed them.

## Recognise it

Doc: `if not output.exists(): return`, `try/except: pass`, precondition-gated asserts.

History (F-012): line loops with if/elif headers ending `else: pass` and **no** post-loop
presence assert — empty files pass.

## Read first

- `.cursor/skills/sentinel-ultra-review/reference/test-quality.md` (Fail-open)
- `.cursor/skills/sentinel-ultra-review/reference/fix-playbooks.md` § F6
- `knowledge/failures/F-012_*.json`
- `OUTCOMES.md`

## Diagnose before editing

1. Search for `else: pass` after header scans; `exists(): return`; bare except pass.
2. Post-loop `saw_*` / required-key assert present?
3. Written finding.

## Fix — pick ONE direction per defect

| Action | Evidence |
|--------|----------|
| Remove fail-open gates; assert presence after scan (required set from **instruction**) | **EVIDENCED WORKING** — **5** fail-open scan citations on `0cf2e9a3` **resolved** next round (`2026-08-05`→`08-06`). |
| Rely on V9 alone | **EVIDENCED FAILING** as detection — V9 stayed CLEAR while Judge cited fail-open (F-012). |

## Verify before repackaging

- [ ] Empty/missing artifact fails graded tests
- [ ] No else:pass scans without presence assert
- [ ] Auto-REMOVE fail-open clear where implemented

## Do not

- Mark provisional — named auto-REMOVE.
- Ship hoping V9 catches scan-loops.

## Instances

- FC012 F-012 · 0cf2e9a3 · ~23 loops · next round fail-open cites **resolved** (×5 family)
