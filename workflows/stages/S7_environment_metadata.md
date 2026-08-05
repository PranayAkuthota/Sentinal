# S7 — Environment & Metadata Gates

## Purpose
Classify environment/metadata/git issues as Fixable vs Not Fixable; record limits and hygiene.

## Inputs
- `environment/Dockerfile`, `task.toml`
- Git report from audit
- Policy limits (cpus, memory, timeouts, gpus=0, etc.)

## Outputs
- Env class: Fixable tweaks vs tangled/unrecoverable
- Metadata limit violations list
- Harbor network blocks correct / issues (`network_mode` / `allowed_hosts` per block)
- Git hygiene summary (HEAD, remotes, reflog, size, clean tree)

## Validation
- Resources/timeouts within Ultra limits
- Offline build realism for sandbox
- HEAD vs `base_commit_sha` noted (shipped repo HEAD wins on Fixable realign)
- `.git` size / remotes / filter drivers reviewed

## Failure
Tangled toolchain; required live external service; unrecoverable git corruption; limits blocking packaging.

## Recovery
Most Dockerfile/metadata/git issues → Fixable. Unrecoverable env → Invalid/Not Fixable at S8.

## Automation
`audit` metadata/git reports; Fixable hygiene later ensures Harbor network blocks (does not strip them).
