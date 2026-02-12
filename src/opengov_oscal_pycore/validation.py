"""
Validation helpers for OSCAL catalog objects.

Design: Non-raising validation returning a list of ValidationIssue objects.
Each issue has a severity ("error" or "warning"), a path string, and a message.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Catalog, Control, OscalMetadata


@dataclass
class ValidationIssue:
    """A single validation finding."""
    severity: str   # "error" | "warning"
    path: str       # e.g. "metadata.title", "groups[0].controls[1].id"
    message: str


def validate_metadata(metadata: OscalMetadata) -> list[ValidationIssue]:
    """Validate metadata fields."""
    issues: list[ValidationIssue] = []

    if not metadata.title or not metadata.title.strip():
        issues.append(ValidationIssue("error", "metadata.title", "Title is required"))

    if not metadata.oscal_version:
        issues.append(ValidationIssue("warning", "metadata.oscal-version", "OSCAL version not specified"))

    if not metadata.version:
        issues.append(ValidationIssue("warning", "metadata.version", "Catalog version not specified"))

    return issues


def validate_control(control: Control, path: str = "control") -> list[ValidationIssue]:
    """Validate a single control."""
    issues: list[ValidationIssue] = []

    if not control.title:
        issues.append(ValidationIssue("warning", f"{path}.title", f"Control {control.id!r} has no title"))

    return issues


def validate_unique_ids(cat: Catalog) -> list[ValidationIssue]:
    """Check for duplicate control IDs and group IDs."""
    issues: list[ValidationIssue] = []

    # Check group IDs
    group_ids: dict[str, int] = {}

    def _collect_group_ids(groups: list, prefix: str = "groups") -> None:
        for i, g in enumerate(groups):
            gpath = f"{prefix}[{i}]"
            if g.id in group_ids:
                issues.append(ValidationIssue(
                    "error", f"{gpath}.id",
                    f"Duplicate group ID {g.id!r}"
                ))
            else:
                group_ids[g.id] = i
            _collect_group_ids(g.groups, f"{gpath}.groups")

    _collect_group_ids(cat.groups)

    # Check control IDs
    control_ids: dict[str, str] = {}  # id -> first path

    def _collect_control_ids(groups: list, prefix: str = "groups") -> None:
        for i, g in enumerate(groups):
            gpath = f"{prefix}[{i}]"
            for j, c in enumerate(g.controls):
                cpath = f"{gpath}.controls[{j}]"
                if c.id in control_ids:
                    issues.append(ValidationIssue(
                        "error", f"{cpath}.id",
                        f"Duplicate control ID {c.id!r} (first seen at {control_ids[c.id]})"
                    ))
                else:
                    control_ids[c.id] = cpath
                # Handle nested controls
                for k, nested in enumerate(c.controls):
                    npath = f"{cpath}.controls[{k}]"
                    if nested.id in control_ids:
                        issues.append(ValidationIssue(
                            "error", f"{npath}.id",
                            f"Duplicate control ID {nested.id!r} (first seen at {control_ids[nested.id]})"
                        ))
                    else:
                        control_ids[nested.id] = npath
            _collect_control_ids(g.groups, f"{gpath}.groups")

    _collect_control_ids(cat.groups)

    return issues


def validate_catalog(cat: Catalog) -> list[ValidationIssue]:
    """Run all validations on a catalog. Returns combined list of issues."""
    issues: list[ValidationIssue] = []
    issues.extend(validate_metadata(cat.metadata))
    issues.extend(validate_unique_ids(cat))

    # Validate individual controls
    def _validate_controls(groups: list, prefix: str = "groups") -> None:
        for i, g in enumerate(groups):
            gpath = f"{prefix}[{i}]"
            for j, c in enumerate(g.controls):
                issues.extend(validate_control(c, f"{gpath}.controls[{j}]"))
            _validate_controls(g.groups, f"{gpath}.groups")

    _validate_controls(cat.groups)

    return issues


def validate_oscal(model: object) -> None:
    """Legacy stub -- kept for backward compatibility."""
    return
