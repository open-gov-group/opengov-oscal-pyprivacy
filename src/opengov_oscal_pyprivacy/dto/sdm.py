from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel

from .mapping import MappingRef as RelatedMapping

class SdmControlSummaryProps(BaseModel):
    sdmModule: Optional[str] = None
    sdmGoals: List[str] = []
    dsgvoArticles: List[str] = []

class SdmControlSummary(BaseModel):
    id: str
    title: str
    groupId: Optional[str] = None
    props: SdmControlSummaryProps

class SdmControlDetailProps(SdmControlSummaryProps):
    implementationLevel: Optional[str] = None
    dpRiskImpact: Optional[str] = None
    relatedMappings: List[RelatedMapping] = []

class SdmControlDetail(BaseModel):
    id: str
    title: str
    class_: Optional[str] = None
    groupId: Optional[str] = None
    props: SdmControlDetailProps

class SdmControlUpdateProps(BaseModel):
    implementationLevel: Optional[str] = None
    dpRiskImpact: Optional[str] = None
    relatedMappings: Optional[List[RelatedMapping]] = None

class SdmControlUpdateRequest(BaseModel):
    props: SdmControlUpdateProps
