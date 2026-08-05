"""Session / workflow_state path helpers (thin; CLI remains in sentinel_submitter)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from .paths import WORKSPACE_ROOT


def session_paths(task_name: str) -> Dict[str, Path]:
    work = WORKSPACE_ROOT / "work" / task_name
    outputs = WORKSPACE_ROOT / "task_outputs" / task_name
    return {
        "work": work,
        "original": work / "original",
        "extracted_original": work / "extracted_original",
        "working_copy": work / "working_copy",
        "session": work / "session",
        "validation_logs": work / "session" / "validation_logs",
        "analysis": work / "analysis",
        "session_json": work / "session" / "session.json",
        "platform_input": work / "session" / "platform_input.txt",
        "outputs": outputs,
        "workflow_state": outputs / "workflow_state.json",
    }
