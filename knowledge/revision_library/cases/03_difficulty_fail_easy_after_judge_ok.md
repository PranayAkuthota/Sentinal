# Case 03 · Difficulty FAIL EASY after Judge OK

**Status:** CONFIRMED (n≥2)

Difficulty screen failed easy after Agentic Judge cleared. Not a Judge-blocked task.

## Recognise it

- `Difficulty FAIL EASY: Opus 75% GPT 100%; need worse model <=50%`
- `Difficulty: FAIL EASY - Requires at least MEDIUM; opus 4/4 gpt 4/4`
- Ledger: `FAIL EASY - Requires at least MEDIUM; claude-opus-4-8 100% (4/4)…`

## Read first

- `knowledge/patterns/P-010_agent_judge_before_difficulty.md` (order only)
- `docs/SUBMITTER_BLOCKERS.md`
- `OUTCOMES.md` (004e50af FAIL EASY not_resolved)

## Diagnose before editing

1. Confirm Judge OK and Difficulty ran (unlike Case 09).
2. Quote pass rates / FAIL EASY line.
3. List telegraphing how-to / keyword lists (Case 06-shaped).
4. Written finding: trim-first vs expand-second.

## Fix — pick ONE direction per defect

| Step | Action | Evidence |
|------|--------|----------|
| 1. Trim over-prescription | Cut how-to / keyword lists that telegraph the patch | **EVIDENCED FAILING** as a complete cure on `004e50af`: FAIL EASY **recurred** across pairs (`04:36→09:10` and again `14:55→16:24` with Opus 75%/GPT 100%). Trim alone has **not** cleared Difficulty on that task. |
| 2. Expand PR-natural hardness | Only inside source PR; never invent pass_at_k | **UNTESTED** as a proven next-round clear. Still the only remaining lever after trim — treat as experimental, not a known fix. |

**Honesty:** our current approach (trim ± light harden) has **not** cleared FAIL EASY on `004e50af`. Do not tell yourself this case is solved. Not Case 10 (metadata lies while Judge blocked).

## Verify before repackaging

- [ ] Less telegraphing; problem_statement sync
- [ ] No fake pass_at_k
- [ ] Expect Difficulty may still FAIL EASY — plan another round if it does
- [ ] oracle/NOP honest (pitfall 18)

## Do not

- Claim “we fixed Difficulty” after one trim pass on a recurring FAIL EASY task.
- Fold into Judge coverage cases.
- Debug Difficulty while Judge is blocked (Case 09).

## Instances

- JF002 004e50af · Opus 75% GPT 100% · **EVIDENCED FAILING** recurred in chain · open
- JF048 d41a2c3a · opus 4/4 gpt 4/4 · unknown next · open
