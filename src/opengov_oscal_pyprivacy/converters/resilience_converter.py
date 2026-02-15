from __future__ import annotations

"""
Resilience Converter (#16).

Compose domain extract functions into a SecurityControl DTO.
"""

from opengov_oscal_pycore.models import Control, Group

from ..dto.resilience import SecurityControl, ResilienceGroupSummary, ResilienceGroupDetail
from ..domain.resilience_catalog import (
    extract_domain, extract_objective, extract_description,
)


def control_to_security_control(control: Control) -> SecurityControl:
    """Convert a Control to a SecurityControl DTO."""
    return SecurityControl(
        id=control.id,
        title=control.title or "",
        class_=control.class_,
        domain=extract_domain(control),
        objective=extract_objective(control),
        description=extract_description(control),
    )


def group_to_resilience_summary(group: Group) -> ResilienceGroupSummary:
    """Convert a Group to a ResilienceGroupSummary DTO."""
    return ResilienceGroupSummary(
        id=group.id,
        title=group.title or "",
        control_count=len(group.controls),
    )


def group_to_resilience_detail(group: Group) -> ResilienceGroupDetail:
    """Convert a Group to a ResilienceGroupDetail DTO with all controls."""
    return ResilienceGroupDetail(
        id=group.id,
        title=group.title or "",
        control_count=len(group.controls),
        controls=[
            control_to_security_control(ctrl) for ctrl in group.controls
        ],
    )
