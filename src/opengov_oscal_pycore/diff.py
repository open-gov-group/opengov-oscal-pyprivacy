from __future__ import annotations

"""
OSCAL-aware diff utilities.

Provides structural diff for OSCAL documents (as dicts or Pydantic models).
Uses deepdiff when available; falls back to a simple recursive comparison.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Optional, List, Literal


@dataclass
class DiffChange:
    """A single change between two OSCAL structures."""

    path: str  # e.g. "groups[0].controls[2].props[1].value"
    change_type: Literal["added", "changed", "removed"]
    old_value: Any = None
    new_value: Any = None


@dataclass
class DiffSummary:
    """Aggregate counts of changes."""

    added: int = 0
    changed: int = 0
    removed: int = 0


@dataclass
class OscalDiffResult:
    """Result of diffing two OSCAL structures."""

    summary: DiffSummary = field(default_factory=DiffSummary)
    changes: List[DiffChange] = field(default_factory=list)


def _normalize_deepdiff_path(path: str) -> str:
    """Convert deepdiff paths like root['groups'][0] to groups[0].

    Examples:
        root['groups'][0]          -> groups[0]
        root['metadata']['title']  -> metadata.title
        root['groups'][0]['controls'][1]['props'][2]['value']
            -> groups[0].controls[1].props[2].value
    """
    # Strip the "root" prefix
    if path.startswith("root"):
        path = path[4:]

    # Convert ['key'] to .key  and [N] stays as [N]
    result_parts: list[str] = []
    i = 0
    while i < len(path):
        if path[i] == "[":
            end = path.index("]", i)
            inner = path[i + 1 : end]
            if inner.startswith("'") or inner.startswith('"'):
                # Dictionary key like ['groups'] -> .groups
                key = inner.strip("'\"")
                if result_parts:
                    result_parts.append(f".{key}")
                else:
                    result_parts.append(key)
            else:
                # Numeric index like [0] -> [0]
                result_parts.append(f"[{inner}]")
            i = end + 1
        else:
            result_parts.append(path[i])
            i += 1

    return "".join(result_parts)


def diff_oscal(
    old: dict,
    new: dict,
    *,
    ignore_paths: Optional[List[str]] = None,
) -> OscalDiffResult:
    """Diff two OSCAL documents (as dicts).

    Uses deepdiff if available, falls back to simple dict comparison.

    Args:
        old: The original OSCAL dict.
        new: The modified OSCAL dict.
        ignore_paths: List of dot-separated paths to exclude
                      (e.g. ``["metadata.last-modified"]``).

    Returns:
        An :class:`OscalDiffResult` with summary counts and individual changes.
    """
    try:
        from deepdiff import DeepDiff  # noqa: F401

        return _diff_with_deepdiff(old, new, ignore_paths=ignore_paths)
    except ImportError:
        return _diff_simple(old, new, ignore_paths=ignore_paths)


def _diff_with_deepdiff(
    old: dict,
    new: dict,
    *,
    ignore_paths: Optional[List[str]] = None,
) -> OscalDiffResult:
    """Use deepdiff for structural diff."""
    from deepdiff import DeepDiff

    exclude_regex: Optional[List[str]] = None
    if ignore_paths:
        patterns: list[str] = []
        for p in ignore_paths:
            # Convert dot-path like "metadata.last-modified" to a regex
            # that matches the deepdiff root-based path format.
            # E.g. "metadata.last-modified" -> root\['metadata'\]\['last\-modified'\]
            parts = p.split(".")
            regex_parts = [re.escape(f"['{part}']") for part in parts]
            patterns.append("root" + "".join(regex_parts) + ".*")
        exclude_regex = patterns

    dd = DeepDiff(
        old,
        new,
        ignore_order=False,
        verbose_level=2,
        exclude_regex_paths=exclude_regex,
    )

    changes: List[DiffChange] = []

    # Values changed
    for path, detail in dd.get("values_changed", {}).items():
        old_val = detail.get("old_value") if isinstance(detail, dict) else detail.old_value
        new_val = detail.get("new_value") if isinstance(detail, dict) else detail.new_value
        changes.append(
            DiffChange(
                path=_normalize_deepdiff_path(path),
                change_type="changed",
                old_value=old_val,
                new_value=new_val,
            )
        )

    # Type changes
    for path, detail in dd.get("type_changes", {}).items():
        old_val = detail.get("old_value") if isinstance(detail, dict) else detail.old_value
        new_val = detail.get("new_value") if isinstance(detail, dict) else detail.new_value
        changes.append(
            DiffChange(
                path=_normalize_deepdiff_path(path),
                change_type="changed",
                old_value=old_val,
                new_value=new_val,
            )
        )

    # Dictionary items added
    for path, value in dd.get("dictionary_item_added", {}).items():
        changes.append(
            DiffChange(
                path=_normalize_deepdiff_path(path),
                change_type="added",
                new_value=value,
            )
        )

    # Dictionary items removed
    for path, value in dd.get("dictionary_item_removed", {}).items():
        changes.append(
            DiffChange(
                path=_normalize_deepdiff_path(path),
                change_type="removed",
                old_value=value,
            )
        )

    # Iterable items added
    for path, value in dd.get("iterable_item_added", {}).items():
        changes.append(
            DiffChange(
                path=_normalize_deepdiff_path(path),
                change_type="added",
                new_value=value,
            )
        )

    # Iterable items removed
    for path, value in dd.get("iterable_item_removed", {}).items():
        changes.append(
            DiffChange(
                path=_normalize_deepdiff_path(path),
                change_type="removed",
                old_value=value,
            )
        )

    summary = DiffSummary(
        added=sum(1 for c in changes if c.change_type == "added"),
        changed=sum(1 for c in changes if c.change_type == "changed"),
        removed=sum(1 for c in changes if c.change_type == "removed"),
    )

    return OscalDiffResult(summary=summary, changes=changes)


def _diff_simple(
    old: dict,
    new: dict,
    *,
    ignore_paths: Optional[List[str]] = None,
) -> OscalDiffResult:
    """Simple fallback diff without deepdiff."""
    changes: List[DiffChange] = []

    def _should_ignore(path: str) -> bool:
        if not ignore_paths:
            return False
        return any(ip in path for ip in ignore_paths)

    def _compare(a: Any, b: Any, path: str = "") -> None:
        if _should_ignore(path):
            return
        if isinstance(a, dict) and isinstance(b, dict):
            all_keys = set(a.keys()) | set(b.keys())
            for key in sorted(all_keys):
                child_path = f"{path}.{key}" if path else key
                if key not in a:
                    changes.append(
                        DiffChange(path=child_path, change_type="added", new_value=b[key])
                    )
                elif key not in b:
                    changes.append(
                        DiffChange(path=child_path, change_type="removed", old_value=a[key])
                    )
                else:
                    _compare(a[key], b[key], child_path)
        elif isinstance(a, list) and isinstance(b, list):
            for i in range(max(len(a), len(b))):
                child_path = f"{path}[{i}]"
                if i >= len(a):
                    changes.append(
                        DiffChange(path=child_path, change_type="added", new_value=b[i])
                    )
                elif i >= len(b):
                    changes.append(
                        DiffChange(path=child_path, change_type="removed", old_value=a[i])
                    )
                else:
                    _compare(a[i], b[i], child_path)
        elif a != b:
            changes.append(
                DiffChange(path=path, change_type="changed", old_value=a, new_value=b)
            )

    _compare(old, new)

    summary = DiffSummary(
        added=sum(1 for c in changes if c.change_type == "added"),
        changed=sum(1 for c in changes if c.change_type == "changed"),
        removed=sum(1 for c in changes if c.change_type == "removed"),
    )

    return OscalDiffResult(summary=summary, changes=changes)


def diff_catalogs(old: Any, new: Any) -> OscalDiffResult:
    """Diff two Catalog objects.

    Args:
        old: The original Catalog (Pydantic model).
        new: The modified Catalog (Pydantic model).

    Returns:
        An :class:`OscalDiffResult`.
    """
    old_dict = old.model_dump(by_alias=True, exclude_none=True)
    new_dict = new.model_dump(by_alias=True, exclude_none=True)
    return diff_oscal(old_dict, new_dict)


def diff_controls(old: Any, new: Any) -> OscalDiffResult:
    """Diff two Control objects.

    Args:
        old: The original Control (Pydantic model).
        new: The modified Control (Pydantic model).

    Returns:
        An :class:`OscalDiffResult`.
    """
    old_dict = old.model_dump(by_alias=True, exclude_none=True)
    new_dict = new.model_dump(by_alias=True, exclude_none=True)
    return diff_oscal(old_dict, new_dict)
