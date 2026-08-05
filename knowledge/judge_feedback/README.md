# Agent Judge feedback ledger

Canonical JSON records of live (or carefully backfilled) Agent Judge results.

- **Schema:** [`schema.json`](schema.json)
- **Writer:** `automation/capture_judge_feedback.py`
- **Stats:** `automation/judge_stats.py` (reads this directory + optional prediction joins)
- **Policy:** `docs/VALIDATION_STRATEGY.md`

Do not invent axis scores, citations, or must-haves. Missing evidence → `null`.
