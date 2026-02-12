from __future__ import annotations

"""
ROPA Converter (#28).

Compose domain extract functions into ROPA DTOs.
"""

from typing import Optional

from opengov_oscal_pycore.models import Control, Group
from opengov_oscal_pycore.crud.parts import parts_ref, find_part, _get

from ..dto.common import TextItem
from ..dto.ropa import (
    RopaControlSummary, RopaControlDetail,
    RopaGroupSummary, RopaGroupDetail,
)
from ..domain.privacy_control import (
    extract_legal_articles, extract_evidence_artifacts,
    extract_maturity_domain, extract_maturity_requirement,
    extract_measure_category, extract_statement,
    extract_maturity_level_texts, list_dp_goals,
    list_typical_measures, list_assessment_questions,
)


def _extract_maturity_hints_prose(control: Control) -> Optional[str]:
    """Return the maturity-hints container prose, or None."""
    parts = parts_ref(control)
    part = find_part(parts, name="maturity-hints")
    if part is None:
        return None
    return _get(part, "prose")


def control_to_ropa_summary(
    control: Control,
    *,
    group_id: Optional[str] = None,
) -> RopaControlSummary:
    """Convert a Control to a RopaControlSummary DTO."""
    return RopaControlSummary(
        id=control.id,
        title=control.title or "",
        group_id=group_id,
        legal_articles=extract_legal_articles(control),
        evidence_artifacts=extract_evidence_artifacts(control),
        maturity_domain=extract_maturity_domain(control),
        maturity_requirement=extract_maturity_requirement(control),
    )


def control_to_ropa_detail(
    control: Control,
    *,
    group_id: Optional[str] = None,
) -> RopaControlDetail:
    """Convert a Control to a RopaControlDetail DTO."""
    maturity = extract_maturity_level_texts(control)

    return RopaControlDetail(
        id=control.id,
        ctrl_class=control.class_ or "",
        title=control.title or "",
        group_id=group_id,
        legal_articles=extract_legal_articles(control),
        evidence_artifacts=extract_evidence_artifacts(control),
        maturity_domain=extract_maturity_domain(control),
        maturity_requirement=extract_maturity_requirement(control),
        dp_goals=list_dp_goals(control),
        statement=extract_statement(control),
        maturity_hints=_extract_maturity_hints_prose(control),
        maturity_level_1=maturity.get(1),
        maturity_level_3=maturity.get(3),
        maturity_level_5=maturity.get(5),
        typical_measures=[
            TextItem(id=m["id"], prose=m["prose"])
            for m in list_typical_measures(control)
        ],
        assessment_questions=[
            TextItem(id=q["id"], prose=q["prose"])
            for q in list_assessment_questions(control)
        ],
        measure_category=extract_measure_category(control),
    )


def group_to_ropa_summary(group: Group) -> RopaGroupSummary:
    """Convert a Group to a RopaGroupSummary DTO."""
    return RopaGroupSummary(
        id=group.id,
        title=group.title or "",
        control_count=len(group.controls),
    )


def group_to_ropa_detail(
    group: Group,
    *,
    include_controls: bool = True,
) -> RopaGroupDetail:
    """Convert a Group to a RopaGroupDetail DTO."""
    controls = []
    if include_controls:
        controls = [
            control_to_ropa_summary(c, group_id=group.id)
            for c in group.controls
        ]
    return RopaGroupDetail(
        id=group.id,
        title=group.title or "",
        control_count=len(group.controls),
        controls=controls,
    )
