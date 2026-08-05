"""Verdict label normalization — recording helpers only (never auto-assign)."""

from __future__ import annotations


def norm_analysis(value: str) -> str:
    mapping = {
        "Valid as-is": "Valid-as-is",
        "Valid-as-is": "Valid-as-is",
        "Fixable": "Fixable",
        "Invalid/Not Fixable": "Invalid/Not Fixable",
        "Invalid-Not Fixable": "Invalid/Not Fixable",
    }
    return mapping.get(value.strip(), value.strip())


def public_matches_duplicate(public: str, duplicate: str) -> bool:
    return norm_analysis(public) == norm_analysis(duplicate)
