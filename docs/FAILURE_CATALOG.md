# Sentinel Failure Catalog

Closed-loop memory for recurring submitter failures. Records live under `knowledge/failures/` and must validate against `knowledge/failures/catalog.schema.json`.

## Loop

1. End of task: `capture_learning.py` writes a proposal  
2. Human reviews reusable items  
3. `promote_learning.py --failure …` (or manual JSON) adds a catalog record  
4. Later tasks consult failures + `knowledge/patterns/INDEX.md` before repeating mistakes  

## Rules

- `reusable: true` only for patterns that help future tasks  
- Do not put task UUIDs in titles when avoidable  
- No golden patches, hidden test bodies, or agent spoilers  
- Prefer `seen_count` ≥ 2 before promoting into Operational Patterns  
- Never auto-edit `Review_Guidelines.mdc` from failure records  

## Categories

`packaging`, `tests_patch`, `grading`, `instruction`, `oracle`, `environment`, `metadata`, `validation`, `workflow`, `other`

## Commands

```bash
python3 automation/capture_learning.py --task-name TASK
python3 automation/promote_learning.py --failure \
  --id F-00N --title "…" --category tests_patch \
  --symptom "…" --root-cause-class "…" --recovery "…"
```
