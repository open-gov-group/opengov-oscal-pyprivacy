from __future__ import annotations

from typing import List, Optional
from pydantic import Field

from .common import DtoBaseModel, TextItem


class DpiaControlSummary(DtoBaseModel):
    id: str
    title: str
    group_id: Optional[str] = Field(default=None, alias="groupId")
    legal_articles: List[str] = Field(default_factory=list, alias="dsgvoArticles")
    evidence_artifacts: List[str] = Field(default_factory=list, alias="evidenceArtifacts")
    maturity_domain: Optional[str] = Field(default=None, alias="maturityDomain")
    maturity_requirement: Optional[int] = Field(default=None, alias="maturityRequirement")


class DpiaControlDetail(DpiaControlSummary):
    ctrl_class: str = Field(default="", alias="ctrlClass")
    dp_goals: List[str] = Field(default_factory=list, alias="dpGoals")
    statement: Optional[str] = None
    maturity_hints: Optional[str] = Field(default=None, alias="maturityHints")
    maturity_level_1: Optional[str] = Field(default=None, alias="maturityLevel1")
    maturity_level_3: Optional[str] = Field(default=None, alias="maturityLevel3")
    maturity_level_5: Optional[str] = Field(default=None, alias="maturityLevel5")
    typical_measures: List[TextItem] = Field(default_factory=list, alias="typicalMeasures")
    assessment_questions: List[TextItem] = Field(default_factory=list, alias="assessmentQuestions")
    measure_category: Optional[str] = Field(default=None, alias="measureCategory")


class DpiaGroupSummary(DtoBaseModel):
    id: str
    title: str
    control_count: int = Field(default=0, alias="controlCount")


class DpiaGroupDetail(DpiaGroupSummary):
    controls: List[DpiaControlSummary] = Field(default_factory=list)
