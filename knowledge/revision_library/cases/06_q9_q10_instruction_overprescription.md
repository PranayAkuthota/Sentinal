# Case 06 · Q9/Q10 & instruction over-prescription

**Status:** CONFIRMED (n≥2)

⚠ **Contradicts Case 05.** Getting leaks out of the instruction can recreate faithfulness
gaps. JF004 is the only Part A instance with next_round=**no**.

## Recognise it

- `Static Q9/Q10 FAIL: instruction lists exact NVT/NPT required fields and values that mirror NVT_REQUIRED_KEYS / NVT_REQUIRED_VALUES — leaking internal test logic`
- Must-haves failed: `Q9`, `Q10`
- `Q10: instruction leaks BoolMap</FloatMap</BytesMap< assertion substrings…`
- `instruction names src/style/ directory for Q9 styles`
- `instruction says because the suite calls that helper / called directly by the suite`
- `prescriptiveness 3.5: exact keyword/stdlib lists and edge-case carve-outs telegraph the fix`
- `prompt dictates kerid_t/uint32_t and enumerates surfaces to migrate — mechanical propagation`
- `exact Foyer import statements pinned` / private helper ordering described
- `trait_alias/RCFFloat/num_traits how-to` / `Prefer Rc RefCell is how-to`

## Read first

- Official Ultra must-haves Q9/Q10 (instruction must not navigate by path or leak match= words)
- `knowledge/patterns/P-012_faithfulness_fixture_dump_flips_q9_q10_state_contract_not_instance.md`
- `docs/SUBMITTER_BLOCKERS.md` 16m / 16n
- This library: `05_test_faithfulness_overreach.md`

## Diagnose before editing

1. Quote the leaking sentence(s).
2. Classify: path-as-navigation (Q9), error/token literals (Q10), how-to, suite-leak, import pin.
3. Ask what **outcome** remains if the leak is removed.
4. If removing values that tests still require, open Case 05 — pick soften test vs outcome-level contract.

## Fix — pick ONE direction per defect

| Shape | Fix |
|-------|-----|
| Exact fields/values mirroring test constants | Reframe as outcome/state **contract**, not fixture instance (P-012) — or soften test |
| Path “update src/…” | Require behaviour; drop filesystem navigation |
| “suite calls that helper” | Describe public behaviour only |
| How-to / import pins / algorithm | Cut; keep stable public requirements |
| Error message must contain words ‘X’ and ‘Y’ | Public failure mode without match= literals |

**Never** “fix faithfulness” by pasting the test’s key list back in.

## Verify before repackaging

- [ ] Q9/Q10 static / judge_prep clear of blocking literals/paths
- [ ] Faithfulness cites still coherent (Case 05)
- [ ] instruction ≡ problem_statement
- [ ] Prescriptiveness not telegraphing Difficulty (Case 03)

## Do not

- Oscillate: round1 dump values → round2 Q9/Q10 (JF004).
- Leave suite-leak phrases.
- Ignore Case 05 cross-warn.

## Instances

- JF004 0cf2e9a3 · Static Q9/Q10 FAIL NVT/NPT mirrors test keys · round1 stated values · **next=no**
- JF012–013 0cf2e9a3 · must-have Q9/Q10 · unknown · unknown
- JF001, JF003 004e50af · Q10 BoolMap leak; keyword lists · unknown · unknown
- JF008–010 0cf2e9a3 · mechanism / imports / private helper · unknown · unknown
- JF017 7b88ff8e · dictates types + surfaces · unknown · unknown
- JF024–025 826cb164 · how-to · unknown · unknown
- JF038–039 a8d30c64 · src/style path; location/ctor/algorithm · unknown · unknown
- JF041–042 c6889dd0 · suite calls helper; design steer keys · unknown · unknown
- JF051 d41a2c3a · telegraphs enable flag / masked-alias path · unknown · unknown
