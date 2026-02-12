from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class SecurityControlRef(BaseModel):
    catalogId: str
    controlId: str


class MappingStandards(BaseModel):
    bsi: Optional[List[str]] = None
    iso27001: Optional[List[str]] = None
    iso27701: Optional[List[str]] = None


class SdmSecurityMapping(BaseModel):
    sdmControlId: str
    sdmTitle: str
    securityControls: List[SecurityControlRef] = []
    standards: MappingStandards = MappingStandards()
    notes: Optional[str] = None
