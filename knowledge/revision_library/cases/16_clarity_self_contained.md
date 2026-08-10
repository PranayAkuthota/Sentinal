# Case 16 · Clarity / self-contained under-spec

**Status:** PROVISIONAL-THIN (n=2, thin shared wording)

Instruction leaves critical behaviour vague or schema/endpoint under-specified so agents
must guess.

## Recognise it

- `at least one well-formed atom row vague for UA psf/pdb`
- `RiskModelRequest schema/endpoint under-specified`

## Read first

- Ultra clarity / self-containedness expectations
- Case 06 — clarifying must not become Q9/Q10 dumps
- Case 04 — if “vague” hides missing tests, coverage may also apply

## Diagnose before editing

1. Quote the vague phrase.
2. Decide minimum outcome language that removes guessing.
3. Check whether tests already pin a secret schema (Case 05 risk).

## Fix — pick ONE direction per defect

Add precise **behaviour/outcome** language. Do not paste test constants (Case 06).
If tests require fields not stated, resolve with Case 05 (one direction).

## Verify before repackaging

- [ ] Vague cite addressed in instruction + problem_statement sync
- [ ] No new Q9/Q10 leaks
- [ ] Coverage still aligned

## Do not

- “Clarify” by dumping fixture keys.
- Split into two provisional files unless a third distinct shape appears.

## Instances

- JF011 0cf2e9a3 · well-formed atom row vague · unknown · unknown
- JF030 965e30ce · RiskModelRequest under-specified · unknown · unknown
