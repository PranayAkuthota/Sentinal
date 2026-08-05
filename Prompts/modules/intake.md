# Module: Intake & Preserve (S1)

Load during Execution **01** / stage S1.

## Do
1. Run `intake --zip /ABS/PATH.zip` then `prepare --task-name TASK`.
2. Confirm `work/<TASK>/original/` and `extracted_original/` exist.
3. Record SHA; never overwrite the preserved ZIP.
4. Store platform metadata under `session/` if provided.

## Do not
- Mutate `extracted_original/`
- Treat `task_outputs/` historical ZIPs as the intake source when a new ZIP was supplied
- Assign verdicts

## Handoff must include
Task name, original ZIP path, SHA, resolved task root, format dialect note.
