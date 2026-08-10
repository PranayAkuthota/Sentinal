# Case 09 · Blocked at the agentic judge (Difficulty not run)

**Status:** CONFIRMED (n≥2)

**This is the main platform block you will see most often.** The cheap Difficulty
screen never ran. Do not hunt Difficulty logs. Fix the Judge until every axis is
**≥ 3.5** (blocking: `test_coverage` and `test_faithfulness`), then resubmit.

## Recognise it

Exact / near-exact platform wording:

```text
Blocked at the agentic judge. Not run: difficulty screen (cheap single-arm rollout).

This eval runs two checks in order — the agentic judge, then the difficulty screen —
and the screen runs only if the judge passed. The full difficulty rollout is a
separate check that runs after a reviewer accepts the task.

Agentic judge verdict: discuss (coverage_gap). See the agentic judge report for
what to fix, then resubmit.
```

Also: `discuss (overreach)`, `REMOVE`, or any Judge DISCUSS/REMOVE with
`Oracle check not run` / Difficulty not run.

Any axis score **≤ 3.5** (especially coverage / faithfulness) is a **block**.
Ship only when **all** Agent Judge axes are **≥ 3.5**.

## Read first

- `knowledge/patterns/P-010_agent_judge_before_difficulty.md`
- `knowledge/patterns/P-013_gpt_binding_judge_on_test_axes.md`
- `knowledge/failures/F-010_waited_for_difficulty_while_agent_judge_blocked_the_screen.json`
- Then open citation cases from the Judge report (below)
- `.cursor/skills/sentinel-ultra-review/reference/judge-axis-playbook.md`

## Diagnose before editing

1. Confirm the banner: Judge blocked; Difficulty/Oracle **did not run** → no evidence from them.
2. Open the **agentic judge report**. List every citation and every axis **≤ 3.5**.
3. Map each citation:
   - coverage / ungraded / weak sample → Case **04**
   - faithfulness / overreach / private / undeclared → Case **05** ⚠ Case 06
   - Q9/Q10 / how-to / suite-leak → Case **06** ⚠ Case 05
   - fail-open / silent skip → Case **13** / **14**
4. Written finding: “Difficulty not run; fixing Judge axes to ≥ 3.5 via cases …”

## Fix — pick ONE direction per defect

This case has **no unique zip edit**. It is the **gate**:

1. Fix citations via Cases 04–06 (etc.), one direction each.
2. Re-run static-check → judge-prep → rehearsal.
3. Re-upload only when rehearsal / expected live axes are **≥ 3.5** on **all** axes
   (especially blocking `test_coverage` and `test_faithfulness`).
4. Only after Judge passes will the cheap Difficulty screen run (Case 03 if it FAIL EASYs).

**Evidence:** F-010 / JF031 — operators wasted rounds on Difficulty while Judge blocked.
**UNTESTED** as a “score-only” fix without citation work — raising scores means fixing cites.

## Verify before repackaging

- [ ] Every Judge citation mapped to a case and addressed (intent recorded)
- [ ] Every axis targeted to **≥ 3.5** (blocking pair especially)
- [ ] No invented Difficulty / Oracle results
- [ ] Capture + `record_revision_fixes` planned for packaging

## Do not

- Open Case 03 (FAIL EASY) while this banner is present.
- Treat “Difficulty not run” / “Oracle check not run” as infra failure.
- Resubmit with any axis still ≤ 3.5 “to see Difficulty.”

## Instances

- FC010 F-010 · waited for Difficulty while Judge blocked · fix Judge first
- JF031 a8d30c64 · `Blocked at agentic judge… Oracle check not run` · unknown
- Common live banner · `discuss (coverage_gap)` + cheap screen not run · route 04 first
