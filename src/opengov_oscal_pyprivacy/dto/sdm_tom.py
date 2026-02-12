from __future__ import annotations

from typing import List, Optional

from .common import DtoBaseModel


class SdmTomControlSummary(DtoBaseModel):
    id: str
    title: str
    sdm_module: Optional[str] = None
    sdm_goals: List[str] = []
    dsgvo_articles: List[str] = []


class SdmTomControlDetail(SdmTomControlSummary):
    description: Optional[str] = None
    implementation_hints: Optional[str] = None
