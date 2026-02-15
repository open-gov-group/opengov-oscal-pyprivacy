from __future__ import annotations
from typing import List, Optional
from pydantic import Field

from .common import DtoBaseModel
from .mapping import MappingRef as RelatedMapping

class SdmControlSummaryProps(DtoBaseModel):
    sdm_module: Optional[str] = Field(default=None, alias="sdmModule")
    sdm_goals: List[str] = Field(default=[], alias="sdmGoals")
    dsgvo_articles: List[str] = Field(default=[], alias="dsgvoArticles")

class SdmControlSummary(DtoBaseModel):
    id: str
    title: str
    group_id: Optional[str] = Field(default=None, alias="groupId")
    props: SdmControlSummaryProps

class SdmControlDetailProps(SdmControlSummaryProps):
    implementation_level: Optional[str] = Field(default=None, alias="implementationLevel")
    dp_risk_impact: Optional[str] = Field(default=None, alias="dpRiskImpact")
    related_mappings: List[RelatedMapping] = Field(default=[], alias="relatedMappings")

class SdmControlDetail(DtoBaseModel):
    id: str
    title: str
    class_: Optional[str] = None
    group_id: Optional[str] = Field(default=None, alias="groupId")
    props: SdmControlDetailProps

class SdmControlUpdateProps(DtoBaseModel):
    implementation_level: Optional[str] = Field(default=None, alias="implementationLevel")
    dp_risk_impact: Optional[str] = Field(default=None, alias="dpRiskImpact")
    related_mappings: Optional[List[RelatedMapping]] = Field(default=None, alias="relatedMappings")

class SdmControlUpdateRequest(DtoBaseModel):
    props: SdmControlUpdateProps


class SdmGroupSummary(DtoBaseModel):
    id: str
    title: str
    control_count: int = Field(default=0, alias="controlCount")


class SdmGroupDetail(SdmGroupSummary):
    controls: List[SdmControlDetail] = Field(default_factory=list)
