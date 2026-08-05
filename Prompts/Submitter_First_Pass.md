# Submitter First Pass (single-shot orchestrator)

**Prefer the daily path for quality:** `Prompts/Execution/README.md` → **01…06** (pauseable, less context loss).

Use this file only when you intentionally run a full first pass in one conversation. Still follow S0–S12; still never auto-assign verdicts.

## Load
1. `docs/WORKFLOW.md` + `docs/EXECUTION_LAYER.md`
2. `Prompts/Execution/01`…`06` in order (treat each section as a hard checkpoint; write handoffs)
3. `docs/SUBMITTER_BLOCKERS.md` before packaging
4. `.cursor/skills/sentinel-submitter/SKILL.md`
5. Policy: `.cursor/rules/Review_Guidelines.mdc` (reference, don’t dump)

## Non-negotiables
- `checkpoint_ready` before advancing past 01
- Public == Duplicate before edits (**04** before **05**)
- Fixable ZIP only at `work/task ready_to_submit/<task>__corrected.zip` via step **06**
- Absolute paths; `python3`; `--task-name` with multiple sessions
- Never mutate `extracted_original/`; never invent rewards
- Automation never assigns Public/Internal/Duplicate
- Snorkel narrative fields: human paragraph voice (workflow §13)

## Commands
`docs/COMMANDS.md`
