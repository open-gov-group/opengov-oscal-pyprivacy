from __future__ import annotations

from typing import List, Optional
from pydantic import Field

from .common import DtoBaseModel


class SecurityControlRef(DtoBaseModel):
    catalog_id: str = Field(alias="catalogId")
    control_id: str = Field(alias="controlId")


class MappingStandards(DtoBaseModel):
    bsi: Optional[List[str]] = None
    iso27001: Optional[List[str]] = None
    iso27701: Optional[List[str]] = None


class SdmSecurityMapping(DtoBaseModel):
    sdm_control_id: str = Field(alias="sdmControlId")
    sdm_title: str = Field(alias="sdmTitle")
    security_controls: List[SecurityControlRef] = Field(default=[], alias="securityControls")
    standards: MappingStandards = MappingStandards()
    notes: Optional[str] = None
