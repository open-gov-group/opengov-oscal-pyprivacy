from __future__ import annotations

"""
Privacy Catalog Converter (#14).

Compose domain extract functions into Privacy DTOs.
"""

from typing import Optional

from opengov_oscal_pycore.models import Control, Group
from opengov_oscal_pycore.crud.parts import parts_ref, find_part, _get

from ..dto.common import TextItem
from ..dto.privacy_catalog import (
    PrivacyControlSummary, PrivacyControlDetail,
    PrivacyGroupSummary, PrivacyGroupDetail,
    PrivacyRiskScenario, PrivacyRiskImpactScenario,
)
from ..domain.privacy_control import (
    extract_tom_id, extract_legal_articles,
    list_dp_goals, extract_statement,
    extract_risk_hint, extract_risk_scenarios,
    extract_maturity_level_texts,
    list_typical_measures, list_assessment_questions,
)
from ..domain.risk_guidance import get_risk_impact_scenarios, RiskImpactScenario


def _extract_maturity_hints_prose(control: Control) -> Optional[str]:
    """Return the maturity-hints container prose, or None."""
    parts = parts_ref(control)
    part = find_part(parts, name="maturity-hints")
    if part is None:
        return None
    return _get(part, "prose")


def _to_risk_impact_dto(scenario: Optional[RiskImpactScenario]) -> Optional[PrivacyRiskImpactScenario]:
    """Convert a domain RiskImpactScenario to a PrivacyRiskImpactScenario DTO."""
    if scenario is None:
        return None
    return PrivacyRiskImpactScenario(
        id=scenario.id,
        level=scenario.level,
        prose=scenario.prose,
        data_category_example=scenario.data_category_example,
    )


def control_to_privacy_summary(
    control: Control,
    *,
    group_id: Optional[str] = None,
) -> PrivacyControlSummary:
    """Convert a Control to a PrivacyControlSummary DTO."""
    return PrivacyControlSummary(
        id=control.id,
        title=control.title or "",
        group_id=group_id,
        tom_id=extract_tom_id(control),
        dsgvo_articles=extract_legal_articles(control),
        dp_goals=list_dp_goals(control),
    )


def control_to_privacy_detail(
    control: Control,
    *,
    group_id: Optional[str] = None,
) -> PrivacyControlDetail:
    """Convert a Control to a PrivacyControlDetail DTO."""
    risk_impacts = get_risk_impact_scenarios(control)
    maturity = extract_maturity_level_texts(control)

    return PrivacyControlDetail(
        id=control.id,
        ctrl_class=control.class_ or "",
        title=control.title or "",
        group_id=group_id,
        tom_id=extract_tom_id(control),
        dsgvo_articles=extract_legal_articles(control),
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
        risk_hint=extract_risk_hint(control),
        risk_scenarios=[
            PrivacyRiskScenario(
                title=s.get("title"),
                description=s.get("description", s.get("prose", "")),
            )
            for s in extract_risk_scenarios(control)
        ],
        risk_impact_normal=_to_risk_impact_dto(risk_impacts.get("normal")),
        risk_impact_moderate=_to_risk_impact_dto(risk_impacts.get("moderate")),
        risk_impact_high=_to_risk_impact_dto(risk_impacts.get("high")),
    )


def group_to_privacy_summary(group: Group) -> PrivacyGroupSummary:
    """Convert a Group to a PrivacyGroupSummary DTO."""
    return PrivacyGroupSummary(
        id=group.id,
        class_=group.class_,
        title=group.title or "",
    )


def group_to_privacy_detail(
    group: Group,
    *,
    include_controls: bool = True,
) -> PrivacyGroupDetail:
    """Convert a Group to a PrivacyGroupDetail DTO."""
    controls = []
    if include_controls:
        controls = [
            control_to_privacy_summary(c, group_id=group.id)
            for c in group.controls
        ]
    return PrivacyGroupDetail(
        id=group.id,
        class_=group.class_,
        title=group.title or "",
        control_count=len(group.controls),
        controls=controls,
    )
