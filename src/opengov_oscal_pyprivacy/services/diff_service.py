from __future__ import annotations

"""
High-level OSCAL diff service.

Wraps the core :mod:`opengov_oscal_pycore.diff` functions with convenience
methods for file-based diffing and human-readable summaries.
"""

import json
from pathlib import Path
from typing import Optional, List

from opengov_oscal_pycore.models import Catalog, Control
from opengov_oscal_pycore.diff import (
    OscalDiffResult,
    DiffChange,
    DiffSummary,
    diff_oscal,
    diff_catalogs,
    diff_controls,
)

# Re-export core types so service consumers need only one import
__all__ = [
    "OscalDiffService",
    "OscalDiffResult",
    "DiffChange",
    "DiffSummary",
]


class OscalDiffService:
    """High-level service for diffing OSCAL documents."""

    def __init__(self, *, ignore_paths: Optional[List[str]] = None) -> None:
        self._ignore_paths = ignore_paths or []

    def diff_files(self, old_path: Path, new_path: Path) -> OscalDiffResult:
        """Diff two OSCAL JSON files.

        Args:
            old_path: Path to the original JSON file.
            new_path: Path to the modified JSON file.

        Returns:
            An :class:`OscalDiffResult`.
        """
        old_data = json.loads(old_path.read_text(encoding="utf-8"))
        new_data = json.loads(new_path.read_text(encoding="utf-8"))
        return diff_oscal(old_data, new_data, ignore_paths=self._ignore_paths)

    def diff_catalogs(self, old: Catalog, new: Catalog) -> OscalDiffResult:
        """Diff two Catalog objects.

        Args:
            old: The original Catalog.
            new: The modified Catalog.

        Returns:
            An :class:`OscalDiffResult`.
        """
        return diff_catalogs(old, new)

    def diff_controls(self, old: Control, new: Control) -> OscalDiffResult:
        """Diff two Control objects.

        Args:
            old: The original Control.
            new: The modified Control.

        Returns:
            An :class:`OscalDiffResult`.
        """
        return diff_controls(old, new)

    def format_diff_summary(self, result: OscalDiffResult) -> str:
        """Format a human-readable summary of a diff result.

        Args:
            result: The diff result to format.

        Returns:
            A multi-line string summary.
        """
        s = result.summary
        lines = [f"Changes: +{s.added} ~{s.changed} -{s.removed}"]
        for change in result.changes:
            prefix = {"added": "+", "changed": "~", "removed": "-"}[change.change_type]
            lines.append(f"  {prefix} {change.path}")
            if change.change_type == "changed":
                lines.append(f"    old: {change.old_value}")
                lines.append(f"    new: {change.new_value}")
        return "\n".join(lines)
