from __future__ import annotations

"""
Resilience Converter (#16).

Compose domain extract functions into a SecurityControl DTO.
"""

from opengov_oscal_pycore.models import Control

from ..dto.resilience import SecurityControl
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
