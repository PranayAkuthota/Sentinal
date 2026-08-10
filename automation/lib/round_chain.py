"""Citation matching and next-round outcome chaining for judge feedback rounds."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple


def _tokens(s: str) -> set:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9_./]+", " ", s)
    return {w for w in s.split() if len(w) >= 4}


def citation_similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, min(len(ta), len(tb)))


# New-next citations that look like over-prescription after a "state it in instruction" fix.
_REGRESSION_MARKERS = re.compile(
    r"(?i)q9|q10|leaking internal|mirror\w* (?:test|nvt|npt|required)|"
    r"suite calls that helper|called directly by the suite|"
    r"exact (?:keyword|import|fields?|values?)"
)


def classify_pair(
    prior_citations: Sequence[str],
    next_citations: Sequence[str],
    *,
    threshold: float = 0.45,
) -> Dict[str, Any]:
    """Per-citation outcomes for round N given round N+1 citation texts."""
    prior = [c for c in prior_citations if c]
    nxt = [c for c in next_citations if c]
    used: set = set()
    per: List[Dict[str, Any]] = []
    for c in prior:
        best_j, best_sc = -1, -1.0
        for j, d in enumerate(nxt):
            if j in used:
                continue
            sc = citation_similarity(c, d)
            if sc > best_sc:
                best_sc, best_j = sc, j
        if best_j >= 0 and best_sc >= threshold:
            used.add(best_j)
            per.append(
                {
                    "quoted_text": c,
                    "outcome": "not_resolved",
                    "similarity": round(best_sc, 3),
                    "matched_in_next": nxt[best_j],
                }
            )
        else:
            # Check whether a NEW next cite looks like a regression from stating contracts.
            regression_hit = None
            for j, d in enumerate(nxt):
                if j in used:
                    continue
                if _REGRESSION_MARKERS.search(d) and (
                    "instruction" in c.lower()
                    or "unstated" in c.lower()
                    or "not listed" in c.lower()
                    or "not in instruction" in c.lower()
                    or "never documented" in c.lower()
                ):
                    regression_hit = d
                    break
            if regression_hit:
                per.append(
                    {
                        "quoted_text": c,
                        "outcome": "regressed",
                        "similarity": None,
                        "matched_in_next": None,
                        "regression_appeared_as": regression_hit,
                        "note": "Prior faithfulness/unstated cite cleared; next round shows "
                        "Q9/Q10 or instruction-leak shape — likely oscillation (Case 05↔06).",
                    }
                )
            else:
                per.append(
                    {
                        "quoted_text": c,
                        "outcome": "resolved",
                        "similarity": None,
                        "matched_in_next": None,
                    }
                )

    new_cites = [d for j, d in enumerate(nxt) if j not in used]
    return {
        "per_citation": per,
        "new_citations_in_next": new_cites,
        "counts": {
            "resolved": sum(1 for x in per if x["outcome"] == "resolved"),
            "not_resolved": sum(1 for x in per if x["outcome"] == "not_resolved"),
            "regressed": sum(1 for x in per if x["outcome"] == "regressed"),
            "new_in_next": len(new_cites),
        },
    }


def cites_from_ledger_row(row: Dict[str, Any]) -> List[str]:
    return list(row.get("cited_overreach") or []) + list(row.get("cited_gaps") or [])


def cites_from_feedback_record(rec: Dict[str, Any]) -> List[str]:
    out = []
    for c in rec.get("citations") or []:
        qt = (c or {}).get("quoted_text")
        if qt:
            out.append(qt)
    return out
