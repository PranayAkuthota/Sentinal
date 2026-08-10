# Case 09 · Judge-first misread

**Status:** CONFIRMED (n≥2)

Operator hunts Difficulty/Oracle logs while the platform blocked at Agentic Judge.
Later stages did not run — that is not evidence they passed.

## Recognise it

- Catalogue F-010 symptom: `Blocked at the agentic judge. Not run: difficulty screen (cheap single-arm rollout).`
- Feedback: `Blocked at agentic judge. Verdict: discuss (coverage_gap). Oracle check not run.`
- Notes that Difficulty is “missing” while verdict is DISCUSS/REMOVE on Judge

## Read first

- `knowledge/patterns/P-010_agent_judge_before_difficulty.md`
- `knowledge/failures/F-010_waited_for_difficulty_while_agent_judge_blocked_the_screen.json`
- Eval order: Review Gate → Agentic Judge → Difficulty → Oracle → …

## Diagnose before editing

1. Read platform stage line: what ran / what did not.
2. If Judge blocked: list Judge citations only.
3. Explicitly write: “Difficulty/Oracle not run → no difficulty/oracle evidence.”
4. Route citations to Cases 04–06 (etc.) — this case is the workflow gate.

## Fix — pick ONE direction per defect

There is no task edit unique to this case. Fix the **Judge** citations (coverage,
faithfulness, Q9/Q10, …). Re-upload until Judge clears. Only then interpret Difficulty.

## Verify before repackaging

- [ ] Every Judge citation mapped to a task case and addressed (intent recorded)
- [ ] No invented Difficulty/Oracle results
- [ ] Prediction/feedback capture updated

## Do not

- Debug Difficulty FAIL EASY playbooks while Judge is blocked (Case 03 is after Judge OK).
- Treat “Oracle check not run” as oracle failure.

## Instances

- FC010 F-010 · waited for Difficulty while Judge blocked · fix Judge first · unknown
- JF031 a8d30c64 · Blocked at agentic judge … Oracle check not run · unknown · unknown
