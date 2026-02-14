from __future__ import annotations

"""
SSP domain operations.

Provides helpers for generating implemented-requirement stubs from a resolved
catalog, attaching evidence resources, and accessing the import-profile href.
"""

import uuid as _uuid
from typing import Optional, List

from opengov_oscal_pycore.models import BackMatter, Link, Resource
from opengov_oscal_pycore.models_ssp import (
    SystemSecurityPlan,
    SspImplementedRequirement,
)
from opengov_oscal_pycore.crud_catalog import iter_controls
from opengov_oscal_pycore.crud.back_matter import add_resource
from opengov_oscal_pycore.models import Catalog


def generate_implemented_requirements(
    resolved_catalog: Catalog,
) -> List[SspImplementedRequirement]:
    """Generate implemented-requirement stubs for all controls in a resolved catalog.

    Each control becomes an SspImplementedRequirement with:
    - uuid: generated UUID5 from control.id
    - control_id: the control's ID
    - description: empty string (to be filled by implementer)
    """
    requirements: List[SspImplementedRequirement] = []
    namespace = _uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # URL namespace

    for ctrl in iter_controls(resolved_catalog):
        req_uuid = str(_uuid.uuid5(namespace, f"ir-{ctrl.id}"))
        requirements.append(
            SspImplementedRequirement(
                uuid=req_uuid,
                control_id=ctrl.id,  # will use alias "control-id" on export
                description="",
            )
        )

    return requirements


def attach_evidence_to_ssp(
    ssp: SystemSecurityPlan,
    resource: Resource,
    statement_control_id: Optional[str] = None,
) -> None:
    """Attach an evidence resource to an SSP.

    - Adds the resource to SSP's back_matter
    - If statement_control_id is given, adds a link to the matching implemented-requirement
    """
    # Ensure back_matter exists
    if ssp.back_matter is None:
        ssp.back_matter = BackMatter()

    # Add resource to back_matter
    add_resource(ssp.back_matter, resource)

    # If a control ID is specified, link the resource to the matching IR
    if statement_control_id and ssp.control_implementation:
        for ir in ssp.control_implementation.implemented_requirements:
            if ir.control_id == statement_control_id:
                ir.links.append(
                    Link(
                        href=f"#{resource.uuid}",
                        rel="evidence",
                    )
                )
                break


def get_import_profile_href(ssp: SystemSecurityPlan) -> Optional[str]:
    """Get the profile href from an SSP's import-profile."""
    if ssp.import_profile:
        return ssp.import_profile.href
    return None
