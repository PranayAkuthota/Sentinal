# Harbor format — task layout and `task.toml`

Source: The Harbor Framework page.

Tasks follow the Harbor format and are evaluated internally using terminal-based execution:
Docker environments, `solution/solve.sh` as the oracle, `tests/test.sh` for verification, and
a reward written by the verifier (e.g. to `/logs/verifier/reward.txt`).

## How tasks are evaluated

- **Terminal-based execution** — tasks run in isolated container environments.
- **Oracle solution** — the reference solution is `solution/solve.sh`, which applies
  `solution/golden.patch` (a self-contained patch of all the solution's changes).
- **Test execution** — `tests/test.sh` runs the suite and records the reward outcome.
- **Verification** — pass/fail is determined from the test run and the reward file.
- **Platform-level evals** — the platform runs automated checks before tasks reach a
  reviewer: structure check, Dockerfile check, oracle eval, difficulty eval, general quality.

> **Note on oracle solutions:** task solutions may be larger than strictly necessary or
> include extra functionality not asked for in the instruction. **This is okay** as long as
> the solution does what the instruction requires and tests enforce that. The point of the
> oracle is to show that the task is solvable.

## Task structure

```
<task-id>/
├── task/
│   ├── task.toml              # Metadata + pinned image URI, timeouts, resources
│   ├── instruction.md         # Problem statement + measurable success criteria
│   ├── environment/
│   │   ├── Dockerfile         # Container build (base image + setup)
│   │   ├── repo/              # Cloned base repository (agent + verifier run against this)
│   │   └── problem_statement.md  # Restatement of the instruction, set in the environment
│   ├── solution/
│   │   ├── solve.sh           # Applies golden.patch to restore the solved state
│   │   └── golden.patch       # The golden patch — self-contained (all solution changes)
│   └── tests/
│       ├── test.sh            # Runs tests, writes reward to /logs/verifier/reward.txt
│       ├── tests.patch        # Contains the fail-to-pass tests
│       └── config.json        # How to run the suite + which test ids are f2p / p2p
└── runs/                      # Execution runs from LLMs/agents (logs, episodes, outcomes)
```

- If `solution/` contains **`solution.patch`** instead of `golden.patch`, **rename it to
  `golden.patch`.** That was a short-lived draft name and shouldn't ship.
- `runs/` sits **alongside** `task/` at the top level. Each subfolder is typically named by
  model or agent and contains logs, episodes, and outcomes for that run. Use it to understand
  how models run on the task and to identify task issues. **`runs/` is never included in your
  re-upload zip.**
- Your re-upload zip must unpack **directly** to `instruction.md`, `task.toml`,
  `environment/`, `solution/`, `tests/` — not to a wrapping `task/` folder.

---

## `task.toml`

Opens with `schema_version` (the **Harbor format version**, not the task version), then
`[environment]`, `[agent]`, `[verifier]`, `[metadata]`. **Check these fields on every task** —
resource and timeout values must stay within the limits below.

### `[environment]` — resources

| Field | Requirement |
|---|---|
| `os` | the container OS (e.g. `linux`) |
| `cpus` | **2 or 4** |
| `memory_mb` | min **2048**, max **16384** |
| `storage_mb` | min **5120**, max **10240** |
| `gpus` | **always 0** |
| `build_timeout_sec` | max **1800** |
| `network_mode` | `"public"` |

### `[agent]`

| Field | Requirement |
|---|---|
| `network_mode` | `"allowlist"` |
| `allowed_hosts` | `["api.portkey.ai"]` |
| `timeout_sec` | per-episode limit; max **7200**. Raise it if you see agent-timeout failures. |

### `[verifier]`

| Field | Requirement |
|---|---|
| `network_mode` | `"no-network"` |
| `timeout_sec` | verifier run limit; max **1800** |

### `[metadata]` — free-form

| Field | Meaning |
|---|---|
| `category` (and `subcategory`) | the task's primary classification; edit if needed |
| `difficulty_explanation` | why the task warrants its difficulty tier; edit if needed |
| `source` | URL of the source PR / commit / issue the task derives from |

> The judge's **packaging axis cross-checks metadata against the actual task content** — so
> `category`, `difficulty_explanation`, and the source URL must be accurate.

### Network access is set per block — don't strip these fields

Older guidance to remove `network_mode`/`allowed_hosts` is **outdated**. Use:

- `[environment]` → `"public"`
- `[agent]` → `"allowlist"` with `allowed_hosts = ["api.portkey.ai"]`
- `[verifier]` → `"no-network"`

Separately, in **`docker_compose.yaml`, remove `network_mode = "none"` entirely if present.**

A few tasks in certain programming languages may still hit edge cases — flag details to the
team on Slack.

### Example `task.toml`

```toml
schema_version = "1.3"            # Harbor format version (NOT the task version)

# ── [environment] ── resources ───────────────────────────────────────
[environment]
os                = "linux"
cpus              = 2          # 2 or 4
memory_mb         = 2048       # min shown; max 16384
storage_mb        = 5120       # min shown; max 10240
gpus              = 0          # always 0
build_timeout_sec = 600        # max 1800
network_mode      = "public"

# ── [agent] ── per-episode ceiling ───────────────────────────────────
[agent]
network_mode  = "allowlist"
allowed_hosts = ["api.portkey.ai"]
timeout_sec   = 300            # max 7200 — raise if you see agent-timeout failures

# ── [verifier] ───────────────────────────────────────────────────────
[verifier]
network_mode = "no-network"
timeout_sec  = 120             # max 1800

# ── [metadata] ── free-form ──────────────────────────────────────────
[metadata]
category               = "security"                            # edit if needed
difficulty_explanation = "expert-level cybersecurity problem"  # edit if needed
source                 = "https://github.com/org/repo/pull/1234"
```

> Reviewer note (Tasking Guide): "only the **source, verifier, agent, and environment
> timeouts** affect validity."

---

## Layout variants you may encounter

Some authoring pipelines emit slightly different names. Normalize to the Harbor names above
before submitting, and record the rename in your Files Changed list:

| Seen | Normalize to | Why |
|---|---|---|
| `solution/solution.patch` | `solution/golden.patch` | Explicitly required by the Harbor Framework page |
| `tests/test.patch` | `tests/tests.patch` | Harbor names the f2p patch `tests.patch`; `test.sh` and the guidelines both reference that path |
| `environment/config.json` | `tests/config.json` | `config.json` belongs to the tests component per the structure diagram |
| `metadata.json` in the task root | delete | Listed as a "stray pipeline artifact / wrong metadata blocking build prep" — fixable cleanup |

If a variant is load-bearing for a task that otherwise works end-to-end, keep the working
wiring but make sure `test.sh` and `config.json` agree with wherever the files actually live —
and say so in your reviewer comments.

---

## Legacy artifacts (compatibility inputs)

| Legacy artifact | Current treatment |
| --- | ----- |
| `solution/init_state.patch` | Read when supplied in a legacy task. Do **not** automatically treat its absence as a defect. For current uploads use `golden.patch`. |
| `solution/solution.patch` | Rename to `golden.patch` for current Sentinel Ultra upload. |
| `tests/files/` | Read when present in older tasks but do **not** treat it as the replacement for current `tests.patch`, `config.json`, or `grade.py`. |
| Missing `problem_statement.md` | Current task packaging issue. It should exactly match `instruction.md`. |
| Old Valid/Invalid form | Use only when the actual platform still presents that form. |
| Current Sentinel Ultra form | Use **Valid as-is**, **Fixable**, or **Not Fixable**. |

How reverse `init_state.patch` worked (older packages): lines added (`+`) in the patch = code removed from the solution (broken state); lines removed (`-`) = code added by the solution. Missing `init_state.patch` alone is not a defect. Current uploads use forward `golden.patch`.

---

## Metadata validity — not a four-field filter

Some legacy Cursor/automation notes claimed only `source` and the three timeouts could make a task Invalid. That rule is **not** the current Ultra controlling policy. Check **all** metadata fields; verdict and fixability follow the current form and July 22, 2026 guidelines. Timeouts and source remain important, but they are not an exclusive validity filter.

---

## License options (platform forms)

Identify the project license when the platform asks. Check `environment/repo/LICENSE` (or similar), README, then upstream via `source` if needed.

Common listed options: GPL-2.0, GPL-3.0, AGPL-3.0, LGPL-2.1, LGPL-3.0, MPL-2.0, EPL-1.0, EPL-2.0, CPL-1.0, OSL-3.0, RPL-1.5, **Other** (multi-license, unlicensed, or not listed).

Licenses often mapped to **Other** when not listed: MIT, Apache 2.0, BSD 2-Clause, BSD 3-Clause, ISC, Unlicense, CC0.

---

## Category values (reference)

| Category | Description |
|----------|-------------|
| Fix | Fixing known bugs or faults within the codebase |
| Feature | Introducing new internal or user-oriented features |
| Refactor | Restructuring for maintainability |
| Documentation | Docs, comments, README, API docs |
| Build | Build configuration changes |
| Performance | Performance improvements |
| Chore | Housekeeping, dependency bumps, version increments |
| (Ultra free-form) | Current `task.toml` may also use other category labels (e.g. security); edit if needed for accuracy |

Prefer labels on the **current** platform form and in the task’s `task.toml`.
