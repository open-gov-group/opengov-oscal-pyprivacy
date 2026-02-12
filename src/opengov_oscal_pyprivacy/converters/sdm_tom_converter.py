from __future__ import annotations

"""
SDM-TOM Converter (#16).

Compose domain extract functions into SDM-TOM DTOs (summary and detail).
"""

from opengov_oscal_pycore.models import Control

from ..dto.sdm_tom import SdmTomControlSummary, SdmTomControlDetail
from ..domain.sdm_catalog import (
    extract_sdm_module, extract_sdm_goals, extract_dsgvo_articles,
    extract_sdm_tom_description, extract_sdm_tom_implementation_hints,
)


def control_to_sdm_tom_summary(control: Control) -> SdmTomControlSummary:
    """Convert a Control to an SdmTomControlSummary DTO."""
    return SdmTomControlSummary(
        id=control.id,
        title=control.title or "",
        sdm_module=extract_sdm_module(control),
        sdm_goals=extract_sdm_goals(control),
        dsgvo_articles=extract_dsgvo_articles(control),
    )


def control_to_sdm_tom_detail(control: Control) -> SdmTomControlDetail:
    """Convert a Control to an SdmTomControlDetail DTO."""
    return SdmTomControlDetail(
        id=control.id,
        title=control.title or "",
        sdm_module=extract_sdm_module(control),
        sdm_goals=extract_sdm_goals(control),
        dsgvo_articles=extract_dsgvo_articles(control),
        description=extract_sdm_tom_description(control),
        implementation_hints=extract_sdm_tom_implementation_hints(control),
    )
