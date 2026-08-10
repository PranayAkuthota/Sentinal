# Case 03 · Difficulty FAIL EASY after Judge OK

**Status:** CONFIRMED (n≥2)

Difficulty screen failed easy after Agentic Judge cleared. Not a Judge-blocked task.

## Recognise it

- `Difficulty FAIL EASY: Opus 75% GPT 100%; need worse model <=50%`
- `Difficulty: FAIL EASY - Requires at least MEDIUM; opus 4/4 gpt 4/4`

Judge was OK (or OK-enough to reach Difficulty). Do not open a coverage DISCUSS playbook first.

## Read first

- `knowledge/patterns/P-010_agent_judge_before_difficulty.md` (order only)
- `docs/SUBMITTER_BLOCKERS.md` difficulty / model_difficulty
- Task’s `instruction.md` for telegraphing / over-prescription

## Diagnose before editing

1. Confirm Judge OK and Difficulty actually ran (unlike Case 09).
2. Quote pass rates / FAIL EASY line.
3. List instruction how-to / keyword lists that telegraph the fix (often Case 06-shaped).
4. Ask: is the PR naturally harder if we stop spoon-feeding, or must scope expand?
5. Written finding: trim-first vs expand-second choice.

## Fix — pick ONE direction per defect

**Order matters:**

1. **Trim over-prescription first** — remove how-to, exact keyword lists, edge carve-outs that telegraph the patch (align with Case 06 instincts).
2. **Expand PR-natural difficulty second** — only if trim is insufficient; stay inside source PR (never replace scope).

Do not invent `pass_at_k` numbers. Do not weaken graded tests solely to “make it hard.”

Not the same as Case 10 (irregular metadata while Judge still failing).

## Verify before repackaging

- [ ] Instruction less telegraphing; problem_statement sync
- [ ] Graded tests still cover stated requirements (Case 04/05 not regressed)
- [ ] No fake difficulty fields
- [ ] Local oracle/NOP still honest (pitfall 18)

## Do not

- Fold into Judge coverage/faithfulness cases.
- Reintroduce source-regex suites that nuke agents (d41a2c3a notes).
- “Fix Difficulty” while Judge is still blocked (Case 09).

## Instances

- 2026-08 · JF002 004e50af · Opus 75% GPT 100% FAIL EASY · fix unknown · next unknown
- 2026-08 · JF048 d41a2c3a · opus 4/4 gpt 4/4 Requires MEDIUM · fix unknown · next unknown
