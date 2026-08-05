# S3 — Source Alignment

## Purpose
Confirm the task remains recognizably grounded in the cited PR, commit, or issue. Scope may expand naturally later; it must not be replaced.

## Inputs
- `task.toml` source URL / base commit
- Instruction claims
- Upstream PR/commit/issue (fetch with `gh`/`curl` as needed)
- Repo at pinned base (read-only)

## Outputs
- Source summary: what changed upstream vs what the task asks
- Scope notes: preserved / expandable / tangled
- Flags if source URL wrong or unreachable

## Validation
- Source resolves to the correct change set
- Instruction requirements map to upstream intent (plus allowed expansions)
- No requirement to invent an unrelated feature to make the task “work”

## Failure
Wrong PR; unreachable source with no local evidence; task scope already replaced relative to source.

## Recovery
Correct metadata/source citation if Fixable; if validity requires replacing the PR with a different feature → Invalid/Not Fixable (expert at S8).

## Automation
Assist only (fetch PR, list files). Alignment judgement is expert.
