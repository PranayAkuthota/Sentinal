# Module: Source Alignment (S3)

Load during Execution **02** / stage S3.

## Do
1. Open `task.toml` source + base commit; fetch PR/commit/issue.
2. Summarize upstream change intent in plain language.
3. Compare instruction asks vs upstream scope (preserve / natural expand / replaced).
4. Flag wrong or unreachable source URLs.

## Do not
- Replace the PR with a different feature to “save” the task
- Leak spoilers into agent-facing instruction rewrites later

## Handoff must include
Source URL, alignment verdict (aligned / expandable / mismatched), concrete file/area references.
