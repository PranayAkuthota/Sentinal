# P-003: Fixable packaging hygiene

**Status:** superseded-and-corrected (2026-08-05)  
**Reusable:** yes (corrected guidance only)

## Supersession note (2026-08-05)

Earlier versions of this pattern encoded **outdated** guidance to strip `network_mode` / `allowed_hosts` from `task.toml`. Corrected packages produced under that guidance shipped `task.toml` files with the Harbor network fields removed. That is wrong under the 29 July 2026 Harbor Framework / FAQ / What's New pages.

**Corrected rule:** ensure the required per-block network settings (do not remove them):

- `[environment]` → `network_mode = "public"`
- `[agent]` → `network_mode = "allowlist"`, `allowed_hosts = ["api.portkey.ai"]`
- `[verifier]` → `network_mode = "no-network"`

Separately remove `network_mode = "none"` from `docker_compose.yaml` if present. Also ensure sibling `grade.py` when embedded in `test.sh`, and prefer `golden.patch`.

## What to do

Run `ensure-packaging-hygiene` on `working_copy/` before preflight (calls `ensure_network_blocks_in_task_toml` + `strip_compose_network_none`).
