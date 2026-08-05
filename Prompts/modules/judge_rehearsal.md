# Module — Judge rehearsal (single-model Quality Check panel simulation)

**Stage:** S10.5  
**Inputs:** `task_outputs/<TASK>/judge_prep.json` (+ `.md`), `instruction.md`, `tests/tests.patch`,
`tests/config.json`, `solution/` listing, optional `judge_prep_decisions.json`  
**Outputs:**
- `task_outputs/<TASK>/judge_rehearsal.md` (human narrative)
- `task_outputs/<TASK>/judge_rehearsal.json` (machine triage — **required for preflight**)

**Patterns:** P-010 (Judge before Difficulty), P-011 (overreach / ≥3.5), P-006 (no filler f2p)

You are **not** the real two-model platform panel. Label every deliverable as a
**single-model rehearsal**. Still simulate disagreement: run **two** scoring passes with
different adversarial framings, then reconcile.

## Preconditions

1. `judge_prep.json` exists. If `hard_stopped: true`, stop — fix hard-stop inputs first.
2. Read §0 banner: open FIXABLE static-check ids block packaging but the map may still be useful.
3. If `map_stats.low_confidence`, treat scores as provisional and require human review notes.
4. Never invent filler fail-to-pass tests to raise counts (P-006). Prefer trimming untested
   instruction claims or adding real assertions tied to an R#.
5. Compute `judge_prep_fingerprint` = sha256 hex of the raw `judge_prep.json` bytes. Preflight
   rejects a stale rehearsal when this fingerprint no longer matches.

## Step 0 — P-011 semantic triage (before scoring)

`judge_prep` emits **lexical candidates only**:

| Prep status | Meaning |
|-------------|---------|
| `no_graded_link` | No graded assertion with strong token overlap to this R# |
| `unlinked_lexically` | Assertion has no shared tokens with any R# |
| `weak_link` | Only a single strong identifier or weak-only overlap (e.g. `cell_map`) — **not** green |

These are **not** confirmed defects. Adjudicate every such row. Only status `ok`
(strong overlap: ≥2 strong tokens) bypasses triage.

### Coverage (`no_graded_link` / `weak_link`)

- **NOT_A_GAP** — requirement is tested by graded asserts that merely use different wording, **or** the R# is non-agent hygiene (e.g. “do not modify tests”) that should not be graded.
- **CONFIRMED_GAP** — a real observable requirement has no graded enforcement.
- **UNDECIDED** — cannot tell without human input (blocks preflight until resolved).

### Faithfulness (`unlinked_lexically` / `weak_link`) — P-011 three-way

For each triage-bound assertion (GRADED = high severity; UNGRADED = medium — both still scored).
`weak_link` is the same uncertainty as a single-token UNRESOLVED — do not treat it as covered.

1. **(a)** Stated or reasonably implied in `instruction.md` → **NOT_OVERREACH** (`bucket: a`)
2. **(b)** Public/API contract derivable from codebase symbols the instruction already points at → **NOT_OVERREACH** (`bucket: b`)
3. **(c)** Neither → **CONFIRMED_OVERREACH** (`bucket: c`)

Only **(c)** / **CONFIRMED_*** rows block preflight. Prep alone never blocks on lexical unlink.

### Linked-row spot check (`status=ok` sample)

Strong-linked rows normally bypass triage (that is how eb599683’s path-suffix miss escaped).
`judge_prep.json` → `linked_spot_check` samples **max(5, ceil(10% of linked))** assertion ids
with a recorded **seed** (reproducible). Apply the same P-011 three-way to every sampled id.

- **(a)/(b)** → `NOT_OVERREACH`
- **(c)** → **`SAMPLE_HIT`** (not `CONFIRMED_OVERREACH`) — signal that the matcher is
  over-confident; recommend widening triage for this task. Does **not** alone hard-block
  packaging, but must be recorded in `judge_rehearsal.json`.

Copy `linked_spot_check.seed` and `assertion_ids` into the rehearsal output unchanged.

## Pass A — adversarial coverage (“stub solution”)

Assume a stub / minimal implementation that barely touches the instruction surface.
Ask: **which graded tests still pass?** Weight **CONFIRMED_GAP** rows (not raw `no_graded_link`
candidates). Score with a **coverage-hostile** lens.

## Pass B — adversarial faithfulness (“instruction-only engineer”)

Assume a competent engineer who read **only** `instruction.md` (plus public codebase
contracts named there). Weight **CONFIRMED_OVERREACH** rows (not raw `unlinked_lexically`
candidates). Score with a **faithfulness-hostile** lens. Include medium-severity (UNGRADED)
confirmed overreach — the judge reads every test file.

## Reconcile (adjudicator simulation)

For each of the 10 axes, take Pass A and Pass B scores (1–5).

- If |A − B| ≥ 2 on an axis → mark **NEEDS_HUMAN_REVIEW** for that axis (do not silently average away the disagreement).
- Otherwise use the midpoint rounded to one decimal (or the more conservative score if midpoint is ambiguous).

### Axes (score all)

| Axis | Group |
|------|--------|
| realism, clarity, self_containedness, prescriptiveness | Instruction |
| test_coverage, test_faithfulness | Tests (verdict drivers) |
| spec_faithfulness, no_gaming, robustness | Oracle |
| packaging | Packaging |

One-line justification per axis citing `file:line` or `R#`/`A#` from judge_prep.

### Platform verdict logic (test axes ONLY)

- **REMOVE** (NEEDS_REVISION): reconciled score on either test axis ≤ 2.0, OR either pass
  scored an axis ≤ 2 matching an essential auto-REMOVE pattern (cite `auto_remove` HIT with
  static ids), OR any high-severity CONFIRMED_OVERREACH.
- **DISCUSS** (NEEDS_REVISION): either pass scored either test axis ≤ 2, OR reconciled
  score on either test axis ≤ 3.0, OR any CONFIRMED_GAP / CONFIRMED_OVERREACH remains.
- **OK:** both test axes > 3.0 with no pass at ≤ 2 and zero CONFIRMED_* rows.

### Operational bar (P-010 / P-011) — stricter than OK

Refuse to package while **any** of the 10 reconciled axes is **below 3.5**, or while any
CONFIRMED_GAP / CONFIRMED_OVERREACH / UNDECIDED triage row remains.
“3 with reservations” is not shippable.

## Minimal edits (axes below 4)

For each axis &lt; 4, give **one** concrete minimal edit:

- Coverage gap → exact assertion sketch tied to the R# (not a filler suite).
- Faithfulness / overreach → **either** add an observable requirement to the instruction
  **or** relax/ungrade the A# — never both in one step; never PR spoilers / hidden test names.
- Packaging hard-cap → delete the listed stray path; if `tracked=true`, also realign `base_commit_sha`.

## Output template (`judge_rehearsal.md`)

```markdown
# Judge rehearsal — <TASK>
Model: single-model rehearsal (not the live Opus/GPT panel)
Generated: <ISO8601>
judge_prep_fingerprint: <sha256>

## P-011 triage
### Coverage
| R | verdict | rationale |
...
### Faithfulness
| A | grade | severity | bucket | verdict | rationale |
...

## Pass A (coverage-hostile) scores
| axis | score | cite |
...

## Pass B (faithfulness-hostile) scores
| axis | score | cite |
...

## Reconciled
| axis | A | B | final | Δ≥2 human review? |
...

## Verdict
platform_logic: REMOVE | DISCUSS | OK
operational_bar_3_5: PASS | REFUSE_PACKAGE
confirmed_gaps: N
confirmed_overreach: N
notes: ...

## Minimal edits
1. ...
```

## Machine output (`judge_rehearsal.json`) — required

```json
{
  "schema_version": 1,
  "task_name": "<TASK>",
  "generated_at": "<ISO8601>",
  "judge_prep_fingerprint": "<sha256 of judge_prep.json bytes>",
  "triage": {
    "coverage": [
      {
        "requirement_id": "R1",
        "prep_status": "no_graded_link",
        "verdict": "CONFIRMED_GAP|NOT_A_GAP|UNDECIDED",
        "rationale": "..."
      }
    ],
    "faithfulness": [
      {
        "assertion_id": "A1",
        "prep_status": "unlinked_lexically|weak_link",
        "grade": "GRADED|UNGRADED|UNRESOLVED",
        "severity": "high|medium",
        "bucket": "a|b|c",
        "verdict": "CONFIRMED_OVERREACH|NOT_OVERREACH|UNDECIDED",
        "rationale": "..."
      }
    ]
  },
  "confirmed_gaps": ["R…"],
  "confirmed_overreach": ["A…"],
  "linked_spot_check": {
    "seed": "<from judge_prep.linked_spot_check.seed>",
    "assertion_ids": ["A…"],
    "triage": [
      {
        "assertion_id": "A23",
        "prep_status": "ok",
        "bucket": "a|b|c",
        "verdict": "NOT_OVERREACH|SAMPLE_HIT|UNDECIDED",
        "rationale": "..."
      }
    ],
    "sample_hits": []
  },
  "platform_logic": "REMOVE|DISCUSS|OK",
  "operational_bar_3_5": "PASS|REFUSE_PACKAGE"
}
```

Triage **every** prep candidate row (`unlinked_lexically` **and** `weak_link`) **and** every
`linked_spot_check.assertion_ids` entry. Do not omit medium-severity UNGRADED asserts.
A single shared identifier is never a free pass. Record any `SAMPLE_HIT` and recommend
widening triage when the sample finds overreach in “green” rows.

## Do not

- Claim the live platform already scored this task
- Skip Pass B or collapse to one pass
- Treat `unlinked_lexically` / `no_graded_link` / `weak_link` as confirmed without P-011 triage
- Add filler f2p only to raise counts
- Overwrite `judge_prep_decisions.json`
- Dump implementation spoilers into the instruction to “fix” overreach
