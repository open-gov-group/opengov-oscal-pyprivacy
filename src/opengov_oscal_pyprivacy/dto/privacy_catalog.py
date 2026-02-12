from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import Field

from .common import DtoBaseModel, TextItem

ImpactLevel = Literal["normal", "moderate", "high"]

class PrivacyGroupSummary(DtoBaseModel):
    id: str
    class_: Optional[str] = None
    title: str

class PrivacyControlSummary(DtoBaseModel):
    id: str
    title: str
    group_id: Optional[str] = None
    tom_id: Optional[str] = None
    dsgvo_articles: List[str] = []
    dp_goals: List[str] = []

class PrivacyGroupDetail(PrivacyGroupSummary):
    description: Optional[str] = None
    control_count: int = Field(alias="controlCount")
    controls: List[PrivacyControlSummary] = []

class PrivacyRiskScenario(DtoBaseModel):
    title: Optional[str] = None
    description: str

class PrivacyRiskImpactScenario(DtoBaseModel):
    id: str
    level: ImpactLevel
    prose: str
    data_category_example: Optional[str] = None

class PrivacyControlDetail(DtoBaseModel):
    id: str
    ctrl_class: str = Field(alias="ctrlClass")
    title: str
    group_id: Optional[str] = None
    tom_id: Optional[str] = None
    dsgvo_articles: List[str] = []
    dp_goals: List[str] = []

    statement: Optional[str] = None
    maturity_hints: Optional[str] = None
    maturity_level_1: Optional[str] = None
    maturity_level_3: Optional[str] = None
    maturity_level_5: Optional[str] = None

    # CRUD-ready (IDs sind wichtig!)
    typical_measures: List[TextItem] = []
    assessment_questions: List[TextItem] = []

    risk_hint: Optional[str] = None
    risk_scenarios: List[PrivacyRiskScenario] = []

    # Risk impact guidance: drei feste Felder (UI-freundlich)
    risk_impact_normal: Optional[PrivacyRiskImpactScenario] = None
    risk_impact_moderate: Optional[PrivacyRiskImpactScenario] = None
    risk_impact_high: Optional[PrivacyRiskImpactScenario] = None
