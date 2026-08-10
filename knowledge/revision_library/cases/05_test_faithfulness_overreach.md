# Case 05 · Test faithfulness / overreach

**Status:** CONFIRMED (n≥2)

⚠ **Contradicts Case 06.** State public contracts carefully — dumping fixture/test keys into
the instruction is how JF004 oscillated (next_round=no).

Tests demand undeclared API, private structure, or literal tokens not in the instruction.

## Recognise it

- `bead_to_atom_name_dict required in UA Charmm constructor but never documented…`
- `UA atom-type letter assignment A->15.035 … pinned … instruction only names masses…`
- `ImageContext tests use manager[contextTray][containerEl] private access`
- `masked test enforces DMASKED_ALIAS regex / SLEEF_SUPPORTED_GNUABI_EXTENSIONS unstated`
- `test_read_sample_frames_reuses_info asserts probe never called; instruction only says info may be VideoInfo`
- `test_run_batch_consumes_stubbed_cli 0/4; stub couples to internal shape`
- `uses_catalog_sql_api requires catalog_sql_prepare plus catalog_sql_execute[_once] specifically`
- `fork-safety tests require literal tokens catalog_close before and catalog_open after…`
- REMOVE / `overreach` on faithfulness axis (f2478b33)

## Read first

- `.cursor/skills/sentinel-ultra-review/reference/test-quality.md` (overreach)
- `.cursor/skills/sentinel-ultra-review/reference/judge-axis-playbook.md` (test_faithfulness)
- `knowledge/patterns/P-011_agent_judge_overreach_sync_instruction_tests_target_axis_sco.md`
- `knowledge/patterns/P-012_faithfulness_fixture_dump_flips_q9_q10_state_contract_not_instance.md`
- This library: `06_q9_q10_instruction_overprescription.md`

## Diagnose before editing

1. For each cite: name the undeclared symbol / private path / literal token.
2. Is it a **public behaviour** the PR needs, or a **test implementation detail**?
3. Choose direction **before** editing. Write it down.
4. If direction = expand instruction, plan a Case 06 re-check (Q9/Q10 / how-to).

## Fix — pick ONE direction per defect

| Direction | When | How |
|-----------|------|-----|
| **A — State contract** | Requirement is real public API/behaviour | Describe behaviour/outcomes — **not** fixture instance dumps / exact test key lists (P-012) |
| **B — Soften test** | Assert is private / token / order overreach | Assert outcomes; drop private access / literal token requirements |

**Doing A as a raw dump of test constants causes Case 06.** JF004 is the proof.

No recorded `fixes_applied` for JF060–063 family beyond notes (“state catalog_sql_* … soften file-location”). Next unknown.

## Verify before repackaging

- [ ] Each faithfulness cite resolved by A **or** B, not both blindly
- [ ] Re-scan instruction for Q9/Q10 / path / suite-leak (Case 06)
- [ ] judge-prep overreach / private_internals candidates
- [ ] oracle/NOP if tests or golden changed

## Do not

- Copy `NVT_REQUIRED_KEYS`-style lists into the instruction.
- Leave private `manager[contextTray]` asserts and call it fixed.
- Ignore the Case 06 cross-warn.

## Instances

- JF006 JF007 0cf2e9a3 · undocumented ctor / pinned letters · unknown · unknown
- JF037 a8d30c64 · private contextTray access · unknown · unknown
- JF043 c6889dd0 · stub couples internal shape · unknown · unknown
- JF050 d41a2c3a · DMASKED_ALIAS unstated · unknown · unknown
- JF055 eb599683 · probe never called overreach · unknown · unknown
- JF060 JF061 JF062 JF063 f2478b33 · catalog_sql_* / catalog_close-open tokens · notes only · unknown
