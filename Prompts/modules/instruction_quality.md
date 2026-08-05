# Module: Instruction quality (Quality Check axes)

Load during Execution **02** (step 5). Detail lives here so `02_source_and_instruction.md` stays scannable.

These axes are the instruction half of the Agent Judge Quality Check. Prescriptiveness
scoring ~2.5 has driven known bounces — work this checklist carefully.

**Crux:** a task needs enough context to be solvable, but not so much that it becomes
instructional.

---

## PERSONA (realism)

Classify which **single** persona the instruction matches:

| Persona | Looks like |
|---------|------------|
| Casual / Slack | Short ask from a teammate; informal |
| Structured ticket | Summary / Steps to Reproduce / Expected Behavior |
| Technical memo | Focused note from eng to eng |
| Prose / email | Peer or tech-lead request in paragraphs |
| Acceptance criteria | “When X, the system should Y” |

- If it matches **none**, or **mixes several**, that is a realism defect — say which persona it **should** be.
- **Red flags:** robotic phrasing (“The system shall…”, “It is required that…”); tone mismatched to the chosen persona; structure identical across many tasks; writing that reads like code documentation rather than a task assignment.

---

## PRESCRIPTIVENESS

Flag **each** hit as a numbered issue with a **file:line** cite:

1. “Where to look:” followed by a file list
2. Naming the exact hidden test, fixture, mock endpoint, cassette, or harness file
3. Explaining how the verifier proves success instead of describing visible behaviour
4. Identifying exact internal functions, branches, comprehensions, or callbacks to edit
5. Root-cause analysis that removes the need to inspect the code
6. “the tests reference this name” / “this file validates the fix”
7. Copied assertion strings, state paths, or fixture values from tests — **unless** they are a genuine public/API contract

---

## CLARITY and SELF-CONTAINEDNESS

These pull the **opposite** direction — do **not** strip them when de-prescribing:

1. Required output formats, schemas, and API response shapes **must** be stated in the instruction or a clearly referenced environment file. Documenting the shape is **not** leakage; leaving it to guesswork breaks solvability and makes format assertions hidden rather than faithful.
2. The instruction may only reference behaviours, APIs, files, and repo structure that **actually exist** in the pinned repo.
3. Detailed schemas and conventions score **well**. Ordered how-to steps, file localization hints, and pre-answered edge cases score **badly**.

---

## Output for the 02 handoff

- Chosen persona (or defect)
- Numbered prescriptiveness issues (or “none material”) with cites
- Clarity/self-contained gaps (missing schemas, nonexistent refs)
- One-line crux statement for this task
