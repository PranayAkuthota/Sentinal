# Structural preflight checklist

Use after audit / before Fixable packaging. Automation assists; expert confirms.

## Preserve
- [ ] `extracted_original/` untouched; original ZIP SHA recorded
- [ ] Mutations (if any) only under `working_copy/`

## Harbor shape
- [ ] Required files present (`instruction.md`, `task.toml`, `environment/`, `solution/`, `tests/`)
- [ ] Format dialect noted (current vs legacy naming)
- [ ] `problem_statement.md` sync status recorded (must match on corrected packages)

## Tests / patches
- [ ] f2p count recorded; meaningful ≥10 guideline checked
- [ ] Live “more than 10” only if count ≥11
- [ ] Ungraded patch tests reviewed when `allow_extra_failures`
- [ ] `tests.patch` **git apply --check** clean (not patch-only)
- [ ] Patch hunk/rename health acceptable
- [ ] Existing p2p sources unchanged on corrected branch

## Metadata / env / git
- [ ] Metadata limits reviewed (cpus, memory, storage, gpus, timeouts; agent ≤7200)
- [ ] Harbor network blocks correct on Fixable corrected package (`[environment]=public`, `[agent]=allowlist` + `allowed_hosts=["api.portkey.ai"]`, `[verifier]=no-network`); compose `network_mode="none"` removed if present
- [ ] Git hygiene reviewed (HEAD, remotes, reflog, size, clean tree)
- [ ] Dockerfile offline / Fixable-vs-Invalid class noted

## Packaging readiness
- [ ] `grade.py` present when required
- [ ] `golden.patch` naming on corrected current uploads
- [ ] Preflight `ready_to_package` before `package-fixable`
