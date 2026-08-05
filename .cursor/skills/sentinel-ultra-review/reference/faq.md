# FAQ — edge cases that change a verdict

Source: Sentinel Ultra FAQ.

## Throughput

No daily cap on tasks completed (as of July 1, 2026). **One throughput rule: at most two tasks
in "pending revision" at once.** While at that limit the platform won't let you claim a new
task — keep in-revision tasks moving.

## Deciding the verdict

- **Valid as-is** — the task already meets every requirement; no changes needed.
- **Fixable** — issues in the instructions, tests, and/or oracle, but you can correct all of
  them yourself.
- **Not Fixable** — the only way to make the task valid would be to reduce or replace the PR
  scope, or the environment has issues you're not allowed to fix.

## "A task won't build / the environment looks broken"

Check the fixable-vs-not env tables in `environment-and-git.md`. If it's on the fixable list,
correct it; if not, mark Not Fixable and explain why.

## Git problems are fixable

Leaked fix history, a remote, a HEAD/base-commit mismatch, a reflog, or an oversized `.git`
**do not** make a task Not Fixable. Do the git work inside `environment/repo`, re-zip, and
realign `task.toml` to HEAD if needed (**the shipped repo is the source of truth**). You still
may not edit the repo's tracked source files.

## Nonzero exit-code agent error

1. Work the Before-You-Upload checks (build the Dockerfile locally; confirm `tests.patch`
   applies to the base commit).
2. Raise `[agent] timeout_sec` if runs are timing out.
3. Confirm `network_mode` is set correctly **per block**.
4. **Still failing? Try removing `curl` from the package installs in `environment/Dockerfile`
   and rebuild.** Known Harbor edge-case bug; dropping the curl install is the current
   workaround and affects a small subset of tasks. If that doesn't fix it — or the task
   genuinely needs curl — flag it on Slack with the task/submission UID.

## Which `network_mode`?

Per block; **don't strip these fields** (older guidance to remove them is outdated):

- `[environment]` → `"public"`
- `[agent]` → `"allowlist"` with `allowed_hosts = ["api.portkey.ai"]`
- `[verifier]` → `"no-network"`

Also remove `network_mode = "none"` entirely from `docker_compose.yaml` if present.

## Agent timeout

Set the timeout **generously rather than tight** — a low ceiling fails tasks that would
otherwise pass.

1. Raise `[agent] timeout_sec`, up to the maximum **7200**.
2. Still timing out at 7200? Open `runs/` to see where the agent spends its time — it's often
   one slow step or a harness issue, not the task as a whole.
3. Only if it genuinely can't finish within 7200 **and** the only fix would be reducing or
   replacing PR scope → **Not Fixable / Invalid**, noting where it was timing out.

## Checking submission status

`stb submissions list` from the CLI is the **source of truth**. If a task intermittently
disappears/reappears in the GUI, trust the CLI. If CLI and GUI disagree, or a submission is
stuck, flag it on Slack with the submission UID.

## Infra / platform errors are NOT task defects

`DaytonaRateLimitError`, `ApiRateLimitError`, sandbox auth/connection errors, a one-off
`NonZeroAgentExitCode`, blank feedback / "No evaluation information available".

**The tell is inconsistency** — the same task passes on one run and errors on another, or only
1 of N agent runs fails while the rest are clean.

- **Don't mark the task Not Fixable over it.** Infra failures never make a task unfixable —
  that verdict is for genuine task defects only.
- **Don't burn a revision slot resubmitting blindly.** Blank feedback usually means the eval
  output didn't come through, not that your task failed.
- **Retry later.** Most clear on their own.
- If it persists, flag on Slack with the UID, the exact error, and whether it's intermittent.

## The "easy" linter conflict after a difficulty downgrade

Known issue. If measured difficulty comes back harder than the metadata, **do not hand-edit the
pass-rate/difficulty fields in `task.toml`** to satisfy a reviewer — the linter rejects tasks it
reads as "easy" outright, so matching metadata to measurement and satisfying the linter pull in
opposite directions. **Don't fight the linter by tweaking metadata back and forth.** Flag it on
Slack with the UID and the two disagreeing values. It's a process/tooling gap, not something you
can resolve by editing the task.

## Do I need to run the oracle and NOP locally?

- **Valid as-is — yes.** Those tasks aren't re-run by the platform's difficulty evals, so your
  local run is the only check.
- **Fixable — optional.** The platform's evals run them on submission; a local run is for your
  own confidence (and saves a round-trip).

## Scope change vs added complexity

You may **add complexity** — build on what the PR already does. You may not **change scope** —
turn it into a different task or shrink it.

Source PR adds CSV export to a reports page:

- ✅ **Adding complexity:** let the user pick which columns to export; handle edge cases the PR
  missed (empty results, commas and quotes inside cell values, very large exports).
- ❌ **Changing scope:** PDF export instead of CSV; something unrelated; export only the current
  page instead of the full dataset.

**Rule of thumb:** still clearly maps back to the original PR, just bigger or more thorough →
adding complexity. No longer resembles the PR, or does **less** than the PR → changed scope →
Not Fixable.
