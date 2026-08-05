# Review report — what you hand back to the contributor

This is the human-facing summary. It comes *before* the platform-form templates and tells the
contributor what happened and what to do next.

---

# Sentinel Ultra review — `<task-id>`

**Verdict: [VALID AS-IS | FIXABLE | NOT FIXABLE]**

Source PR: [`task.toml` `source`]
Bundle: [N] files · f2p [N] · p2p [N] · oracle [N] lines / [M] files

## One-paragraph rationale

[Why this verdict and not the adjacent one. For Fixable, name the count and classes of issues.
For Not Fixable, name the single blocking cause and note that every allowed repair was ruled
out. For Valid as-is, state that all seven confirmations hold and the local oracle/NOP run
passed.]

---

## Findings

| # | Severity | Category | Where | Finding | Rule | Fix |
|---|---|---|---|---|---|---|
| 1 | BLOCKER/FIXABLE/ADVISORY | Instructions / Tests / Oracle / Environment / Git / Metadata | `file:line` | [what is wrong] | [Guidelines § …] | [playbook F#] |

**Severity meanings**
- `NOT_FIXABLE` — forces the Not-Fixable verdict (PR scope, or a listed env issue).
- `FIXABLE` — must be corrected before submission; drives the Fixable verdict.
- `ADVISORY` — scored by the judge and read by the reviewer, but doesn't flip the verdict on
  its own. Fix anyway if cheap.

---

## Requirement ↔ assertion map

**Coverage (Instruction → Tests)**

| # | Requirement | Enforcing test(s) | Enforcing? |
|---|---|---|---|
| R1 | | | ✓ / **GAP** |

**Faithfulness (Tests → Instruction)**

| Test | Asserts | Traces to | Derivable? |
|---|---|---|---|
| | | R# / **nothing** | ✓ / **OVERREACH** |

Gaps → coverage defect. Overreach → faithfulness defect. Both are **blocking** axes.

---

## What I checked and how

| Area | Method | Result |
|---|---|---|
| Instruction | read | |
| Source PR cross-check | `task.toml` `source` vs instruction vs golden.patch | |
| `task.toml` fields | limits + `network_mode` per block | |
| Environment | Dockerfile read [+ `docker build`] | |
| Oracle | `golden.patch` read [+ oracle run] | |
| Tests | `tests.patch` + `config.json` + `test.sh` read | |
| Git hygiene | 9-check script | |
| Packaging | stray-artifact sweep, `problem_statement` sync | |
| `runs/` | [reviewed / not present] | |

State plainly what was **not** run (e.g. "no Docker on this machine — oracle/NOP not
executed") rather than implying coverage you don't have.

---

## Next steps

**If FIXABLE:**
1. Apply fixes [list playbooks].
2. Re-run `check_task.py` + `git_hygiene.sh` — both must be clean.
3. Re-verify the coverage and faithfulness maps end to end.
4. Re-zip with `package.sh`; confirm `refs/` entries survived.
5. Oracle → 1.0, NOP → 0.0.
6. Fill `templates/fixable.md`; upload; run evals with *Send to reviewer* **unchecked** until
   Difficulty, Oracle, and Quality checks pass; then check the box and submit.

**If VALID AS-IS:** run oracle + NOP locally (mandatory — these tasks aren't re-run by the
platform), then fill `templates/valid-as-is.md`.

**If NOT FIXABLE:** fill `templates/not-fixable.md` with the ruled-out repairs documented.

---

## Status

`[ NEEDS FIXES | READY TO SUBMIT | FIXED ]`

> Only declare **FIXED** when every gate in `reference/definition-of-fixed.md` passes. List any
> gate you could not verify and why.
