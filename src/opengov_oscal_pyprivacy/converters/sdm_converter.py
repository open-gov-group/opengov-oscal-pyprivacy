from __future__ import annotations

"""
SDM Catalog Converter (#15).

Compose domain extract functions into SDM DTOs.
"""

from typing import Optional

from opengov_oscal_pycore.models import Control

from ..dto.sdm import (
    SdmControlSummary, SdmControlSummaryProps,
    SdmControlDetail, SdmControlDetailProps,
)
from ..domain.sdm_catalog import (
    extract_sdm_module, extract_sdm_goals, extract_dsgvo_articles,
    extract_implementation_level, extract_dp_risk_impact, extract_related_mappings,
)


def control_to_sdm_summary(
    control: Control,
    *,
    group_id: Optional[str] = None,
) -> SdmControlSummary:
    """Convert a Control to an SdmControlSummary DTO."""
    return SdmControlSummary(
        id=control.id,
        title=control.title or "",
        group_id=group_id,
        props=SdmControlSummaryProps(
            sdm_module=extract_sdm_module(control),
            sdm_goals=extract_sdm_goals(control),
            dsgvo_articles=extract_dsgvo_articles(control),
        ),
    )


def control_to_sdm_detail(
    control: Control,
    *,
    group_id: Optional[str] = None,
) -> SdmControlDetail:
    """Convert a Control to an SdmControlDetail DTO."""
    return SdmControlDetail(
        id=control.id,
        title=control.title or "",
        class_=control.class_,
        group_id=group_id,
        props=SdmControlDetailProps(
            sdm_module=extract_sdm_module(control),
            sdm_goals=extract_sdm_goals(control),
            dsgvo_articles=extract_dsgvo_articles(control),
            implementation_level=extract_implementation_level(control),
            dp_risk_impact=extract_dp_risk_impact(control),
            related_mappings=extract_related_mappings(control),
        ),
    )
