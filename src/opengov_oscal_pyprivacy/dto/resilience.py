from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from .common import DtoBaseModel


class SecurityControl(DtoBaseModel):
    id: str
    title: str
    class_: Optional[str] = None
    domain: Optional[str] = None
    objective: Optional[str] = None
    description: Optional[str] = None


class SecurityControlUpdateRequest(DtoBaseModel):
    title: Optional[str] = None
    domain: Optional[str] = None
    objective: Optional[str] = None
    description: Optional[str] = None


class ResilienceGroupSummary(DtoBaseModel):
    id: str
    title: str
    control_count: int = Field(default=0, alias="controlCount")


class ResilienceGroupDetail(ResilienceGroupSummary):
    controls: List[SecurityControl] = Field(default_factory=list)
