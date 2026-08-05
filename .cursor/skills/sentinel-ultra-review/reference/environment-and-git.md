# Environment and Git — what you may fix, what makes a task Not Fixable

Source: Sentinel Ultra Guidelines § "⚠️ Environment — limited fixes" and "✅ Git — fixable in
the repo"; Tasking Guide § "Before You Upload"; FAQ.

---

## Environment ground rules

- **`problem_statement.md` must be an exact copy of `instruction.md`.** Check before
  submitting that the two files are identical — if you edit the instruction, copy the same
  content into `problem_statement.md`.
- You may make **only specific, allowed fixes** to the environment (chiefly
  `environment/Dockerfile`). Use the tables below. If the issue isn't on the fixable list,
  the task is **Not Fixable**.
- **Network model:** the Dockerfile **may** use the network at *build* time, but the sandbox
  is network-restricted at *run* time — the solving agent reaches only the model gateway
  (`api.portkey.ai`), and **the verifier runs fully airgapped**. So: run `apt-get update`
  before installs, use packages that exist in the base image's distro, pin the base image to
  a concrete tag (never `:latest`), and **bake test dependencies into the image** instead of
  fetching them when the tests run.

## Fixable environment issues

| Issue | What's happening | Fix |
|---|---|---|
| Alpine image missing bash | `solve.sh`/`test.sh` use a bash shebang but Alpine ships only `ash` (seen 55×) | `apk add --no-cache bash`. Has autocorrect: `alpine_bash_autocorrect`. |
| Missing `environment/frozen-requirements.txt` | Dockerfile `COPY`s it but it's absent (seen 683×) | Generate it. Has autocorrect: `frozen_requirements_autocorrect`. |
| `tmux` not installed in the task image | Harbor drives the agent/verifier inside a tmux pane; no tmux → the session never starts and the run errors before tests | `apt-get install -y tmux` / `apk add --no-cache tmux` |
| `asciinema` not installed | Harbor records the terminal session with asciinema; a missing binary breaks the run | `apt-get install -y asciinema` / `pip install asciinema` / `apk add asciinema` |
| Unpinned base image (`FROM ...:latest`) | Reproducibility failure | Pin to a concrete tag |
| `DownloadVerifierDirError` / verifier-output-not-found | When caused by the above (bash/sh mismatch, missing artifact path, missing tmux/asciinema) | Fix the upstream cause |
| Resource limits too low | Build OOM / disk-full from undersized `cpus`/`memory_mb`/`storage_mb` | Bump limits (within the published maxima) |
| Bad shell/shebang, CRLF line endings, non-executable scripts | Script fails to exec | Normalize / `chmod +x` |
| Stray pipeline artifacts / wrong metadata blocking build prep | e.g. `metadata.json` in root, `cpp` vs `c++`, missing language. Strictly metadata, but they gate the task before it builds. | Clean up |

## Not-Fixable environment issues

| Issue | When it's defensible |
|---|---|
| Image/dependency build failures | apt/pip/npm/cargo install errors, missing system libs, compiler flags. **Adding a missing dev package or flag is *fixable*;** a tangled toolchain/version conflict is not. |
| Oracle timeout | `harbor run` timed out after n seconds. **Can try bumping the timeout first.** |
| External-network dependency at build/solve time | curl/wget/HF/model pulls against a restricted or flaky sandbox. **Vendoring one small file is *fixable*;** a multi-GB model pull or a live external service is not. |

## Known Harbor edge case (FAQ)

If a task fails with a **nonzero exit-code agent error** after you've done the usual
troubleshooting (local Dockerfile build, `tests.patch` applies to base, raised `[agent]
timeout_sec`, correct `network_mode` per block): **try removing `curl` from the package
installs in `environment/Dockerfile` and rebuild.** This is a known Harbor bug; dropping the
`curl` install is the current workaround and affects only a small subset of tasks. If that
doesn't resolve it — or the task genuinely needs curl — flag it to the team on Slack with the
task/submission UID.

---

## Git — fixable in the repo

The shipped repo (`environment/repo/`) is a **real git checkout, and its HEAD is the source of
truth for the task.** Git problems are fixable: do the git work inside `environment/repo`,
then re-zip. You may clean git metadata (remotes, stray branches/tags, reflog, `.git` size)
and realign `task.toml` to HEAD — but **you must still never edit the repo's tracked source
files**, since that's what anchors the task to the real PR.

> When HEAD and the `base_commit_sha` declared in `task.toml` disagree, **the shipped repo
> (HEAD) wins** — realign the declared commit to HEAD. This misalignment mostly shows up on
> older tasks authored before a static-asset-generation fix; newer tasks generate the two in
> sync.

### Common git issues and how to fix them

| Issue | Why it matters | Fix |
|---|---|---|
| `.git` missing | No `.git` means there's no repo for the agent to work in — usually a zip tool that dropped dotfiles | Make sure `environment/repo/` is a real repo and `.git/` is in the zip |
| HEAD doesn't resolve | A detached, empty, or corrupt HEAD can't be checked out | Ensure the repo has ≥1 commit and HEAD points at it (`git rev-parse --verify HEAD`) |
| HEAD ≠ declared base commit | The agent must start from the commit `task.toml` declares; the shipped repo (HEAD) is the source of truth | `git checkout <base_commit_sha>`, **or** edit `task.toml` so its base commit equals HEAD |
| Commits / branches / tags beyond HEAD | Any ref past HEAD can carry the fix history and **leak the answer**, making the difficulty signal worthless | Delete them so `git rev-list --all --not HEAD` is empty; ship a single branch at the base commit with no stray tags |
| Remote configured | An escape hatch to external history and an untrusted-config surface; tasks must be self-contained and offline | `git remote remove <name>` for each remote |
| Filter drivers (`filter.*`) | clean/smudge drivers are arbitrary commands git can run (e.g. on `git status`) — a security risk and non-reproducible | Remove every `filter.*` section from `.git/config` |
| Dirty working tree | Uncommitted or untracked changes make the start non-reproducible, and an uncommitted solution **leaks the answer** | Commit or discard until `git status --porcelain` prints nothing |
| Reflog present (`.git/logs`) | Records rewound commits (like your solution) and bloats the repo | `git reflog expire --expire=now --all && git gc --prune=now`, then remove `.git/logs` |
| `.git` over 100 MB | Almost always accidental large blobs; slows every trial and wastes storage | `git gc --aggressive --prune=now`; if still large, strip big blobs or ship a fresh single-commit base history (then reset the base commit in `task.toml`) |
| `tests/tests.patch` won't apply | A patch cut against a different base fails on every trial and invalidates the run | Fix HEAD == base commit first, then regenerate the patch against the shipped repo state |

### Pre-submission git checklist

Run inside `environment/repo` before you re-zip. **Every line should be clean or empty.**

```bash
cd environment/repo

git rev-parse --verify HEAD                   # HEAD resolves
git rev-parse HEAD                            # == base_commit_sha in task.toml?
git rev-list --all --not HEAD                 # MUST be empty (no leaked commits)
git remote                                    # MUST be empty
git config --local --get-regexp '^filter\.'   # MUST be empty
git status --porcelain                        # MUST be empty (clean tree)
ls .git/logs 2>/dev/null                      # MUST NOT exist / be empty
du -sh .git                                   # MUST be < 100 MB
git apply --check ../../tests/tests.patch     # MUST apply cleanly
```

`scripts/git_hygiene.sh` runs exactly this and reports each line pass/fail.

---

## `tests.patch` must apply cleanly to the base commit

**The most common infra failure.** The fail-to-pass tests are injected by applying
`tests/tests.patch` onto `environment/repo` at `base_commit_sha`. If the repo drifted, the
patch was cut against a different base, or the f2p tests are **already baked into the repo**,
every trial fails before any evidence is collected.

Verify locally:

```bash
unzip <your_task>.zip -d task && cd task
cd environment/repo
git stash -u 2>/dev/null
git checkout $(grep base_commit_sha ../../task.toml | cut -d'"' -f2)
git apply --check ../../tests/tests.patch      # must succeed with no output
```

If it fails (`Hunk #N FAILED` / `does not match index`), **regenerate the patch**:

1. From the repo at `base_commit_sha`, confirm the target test files are in their original
   state — **they must not already contain the new f2p tests**; the patch is what adds them.
2. Apply your fail-to-pass test additions by hand.
3. `git add -A && git diff --cached -- <test paths> > ../../tests/tests.patch`
4. `git checkout .` to restore the repo to base.
5. Re-verify with `git apply --check`, then run the oracle + tests end to end.

**Common traps:** the repo copy already includes your new tests (patch re-adds them →
conflict); the patch touches a non-test file (e.g. `CMakeLists.txt`) that has since changed.

### Never modify pre-existing (regression / pass-to-pass) test files

The harness checks that pre-existing test files are **byte-identical** to the base commit. If
your fix seems to require changing an existing test, **add a new test through
`tests/tests.patch` instead** (new functions or new files only), and revert the existing file
to its `base_commit_sha` content.

---

## Stray artifacts and leakage sweep

Before zipping:

```bash
find . -name '__pycache__' -o -name '*.pyc' -o -name '.DS_Store' \
  -o -name '.pytest_cache' -o -name '.mypy_cache' -o -name '.ruff_cache' \
  -o -name '.venv' -o -name 'node_modules' -o -name '.idea' -o -name '.vscode' \
  -o -name '*.swp' -o -name '*~' -o -name '*.orig' -o -name '*.bak'
```

**Delete everything the sweep finds** — any one of these shipping into the container hard-caps
the packaging score at 1.

Confirm **no solution material** (golden patch content, expected outputs, `ground_truth.*`
files) is readable from agent paths in the built image.

**Intentional dotfiles are fine:** `.gitignore`, `.dockerignore`, `.gitattributes`, `.gitkeep`,
`.github/`, `.env` when the task warrants them.

If `solution/solution.patch` is present, **rename it to `golden.patch`** — `solution.patch`
was a short-lived draft name and shouldn't ship.
