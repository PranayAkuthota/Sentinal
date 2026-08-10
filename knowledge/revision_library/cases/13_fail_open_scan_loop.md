# Case 13 · Fail-open scan-loop

**Status:** CONFIRMED-BY-RULE

Official Ultra / skill docs name **Fail-open** as one of the six auto-REMOVE patterns.
A missing or malformed artifact must fail the suite, never pass it.
Our FC012 records ~23 scan-loop `else: pass` idioms in one package that V9 missed.

## Recognise it

Doc pattern (skill): `if not output.exists(): return`, `try/except: pass`, assertions gated
behind preconditions that may not hold.

Our history (F-012): graded writer tests loop file lines with if/elif header matches and
end in `else: pass`, with **no** assertion that any required header was ever seen — empty
files can pass. Platform Judge cited coverage / fail-open REMOVE; check_task V9 stayed CLEAR.

## Read first

- `.cursor/skills/sentinel-ultra-review/reference/test-quality.md` (Fail-open row)
- `.cursor/skills/sentinel-ultra-review/reference/fix-playbooks.md` § F6
- `.cursor/skills/sentinel-ultra-review/reference/definition-of-fixed.md` (six auto-REMOVE)
- `knowledge/failures/F-012_v9_fail_open_misses_scan_loop_else_pass.json`

## Diagnose before editing

1. Search new tests for `else: pass` after header scans; `exists(): return`; bare except pass.
2. For each writer/parser test: is there a post-loop `saw_*` / required-key assert?
3. Written finding: which tests fail-open.

## Fix — pick ONE direction per defect

- Remove fail-open gates.
- Require presence: build required set from **instruction**, assert after scan.
- Missing/malformed artifact must fail.

Do not rely on V9 alone (F-012 detector gap).

## Verify before repackaging

- [ ] Empty/missing artifact fails the graded tests
- [ ] No else:pass header scans without presence assert
- [ ] Auto-REMOVE fail-open clear in judge_prep / static-check where implemented

## Do not

- Mark this provisional — platform treats fail-open as customer-essential REMOVE.
- “Fix” only by hoping V9 catches scan-loops.

## Instances

- FC012 F-012 · 0cf2e9a3 · ~23 scan-loop else:pass; V9 miss · recovery: post-loop guards · next unknown
