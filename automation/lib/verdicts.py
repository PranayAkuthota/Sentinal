"""Verdict label normalization — recording helpers only (never auto-assign)."""

from __future__ import annotations


def norm_analysis(value: str) -> str:
    """Map live-form aliases to one semantic branch label.

    Internal Validity uses ``Invalid``; Public/Duplicate use ``Invalid/Not Fixable``.
    Both normalize to ``Invalid/Not Fixable`` for agreement checks.
    """
    mapping = {
        "Valid as-is": "Valid-as-is",
        "Valid-as-is": "Valid-as-is",
        "Fixable": "Fixable",
        "Invalid/Not Fixable": "Invalid/Not Fixable",
        "Invalid-Not Fixable": "Invalid/Not Fixable",
        "Invalid": "Invalid/Not Fixable",
    }
    return mapping.get(value.strip(), value.strip())


def public_matches_duplicate(public: str, duplicate: str) -> bool:
    return norm_analysis(public) == norm_analysis(duplicate)


def all_validity_fields_agree(public: str, internal: str, duplicate: str) -> bool:
    """Public, Internal, and Duplicate must share the same semantic branch.

    Platform automation rejects splits such as Public/Duplicate=Fixable with
    Internal=Invalid. Live Internal label ``Invalid`` still pairs with Public
    / Duplicate ``Invalid/Not Fixable`` via ``norm_analysis``.
    """
    return (
        norm_analysis(public)
        == norm_analysis(internal)
        == norm_analysis(duplicate)
    )
