# Case 01 · Manual Reviewer — packaging & harness

**Status:** CONFIRMED (n≥2)

Human reviewer free-text Needs Revision while Judge often OK (Difficulty sometimes PASS HARD).

## Recognise it

- `Every network setting is gone from task.toml`
- `Delete tests/grade.py; test.sh says no sibling`
- `Files Changed mismatched 36 f2p vs 20…`
- `environment/repo/lib/kotlin/.gradle and build/reports ship…` (ledger)
- Catalogue F-011 network blocks stripped

## Read first

- `.cursor/rules/Review_Guidelines.mdc` (Harbor network blocks)
- `knowledge/patterns/P-003_*` (corrected)
- `OUTCOMES.md`

## Diagnose before editing

1. Confirm Judge/Difficulty already green — do not rewrite axes.
2. Tag packaging vs Case 02 editing-boundary vs test/instruction.
3. Written finding on blocks / grade.py / Files Changed.

## Fix — pick ONE direction per defect

| Shape | Do this | Evidence |
|-------|---------|----------|
| Build caches / source-scan junk in agent FS (`.gradle`, `build/reports`) | Delete from package; keep out of agent-readable tree | **EVIDENCED WORKING** — `.gradle`/`build/reports` cite **resolved** on `004e50af` (`08-06`→`08-07`). |
| Unrelated-suite / packaging hard-cap noise adjacent to harness | Scope suites (see also Case 04 V16); strip caches | **EVIDENCED WORKING** for unrelated-suite cite on `965e30ce` (pair with Case 04). |
| Network settings gone | Restore env/agent/verifier blocks | **UNTESTED** next-round (JF020); policy-required regardless (F-011). |
| grade.py / Files Changed / difficulty_explanation | Align harness + narrative | Mostly **UNTESTED**; JF059 hard+explanation **applied**, next unknown. |

## Verify before repackaging

- [ ] Network blocks present
- [ ] No `.gradle` / `build/reports` / outputs junk
- [ ] grade.py ↔ test.sh; Files Changed matches f2p
- [ ] Not Case 02 (repo/git illegal edits)

## Do not

- Strip Harbor network blocks.
- Treat as Judge coverage rewrite when Judge OK.

## Instances

- JF020 JF021 JF023 826cb164 · network/apply/grade · unknown
- JF045 JF046 JF047 c6889dd0 · Files Changed/grade/difficulty_explanation · unknown
- JF057 JF059 eb599683 · grade.py / hard · JF059 **applied** · next unknown
- FC011 F-011 · network strip · unknown
- Chain 004e50af · `.gradle`/`build/reports` · **resolved**
