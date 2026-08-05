"""Deterministic helpers for Sentinel submitter automation.

Never assigns Public/Internal/Duplicate. Never mutates extracted_original/.
"""

from .verdicts import norm_analysis, public_matches_duplicate
from .paths import WORKSPACE_ROOT, ensure_workspace, safe_task_name, sha256_file
from .toml_util import parse_task_toml_simple
from .sync import check_instruction_sync
from .package import (
    package_flat_task_zip,
    verify_corrected_zip,
    should_exclude_member,
)
from .hygiene import (
    ensure_network_blocks_in_task_toml,
    extract_grade_py_from_test_sh,
    strip_compose_network_none,
    validate_network_blocks,
)

__all__ = [
    "WORKSPACE_ROOT",
    "norm_analysis",
    "public_matches_duplicate",
    "ensure_workspace",
    "safe_task_name",
    "sha256_file",
    "parse_task_toml_simple",
    "check_instruction_sync",
    "package_flat_task_zip",
    "verify_corrected_zip",
    "should_exclude_member",
    "ensure_network_blocks_in_task_toml",
    "extract_grade_py_from_test_sh",
    "strip_compose_network_none",
    "validate_network_blocks",
]
