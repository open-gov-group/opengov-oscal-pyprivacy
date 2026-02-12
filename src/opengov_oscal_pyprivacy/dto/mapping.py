from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import Field, field_validator
from opengov_oscal_pyprivacy.vocab import load_default_privacy_vocabs

from .common import DtoBaseModel

_VOCABS = None

def _vocabs():
    global _VOCABS
    if _VOCABS is None:
        _VOCABS = load_default_privacy_vocabs()
    return _VOCABS

class MappingRef(DtoBaseModel):
    scheme: str
    value: str
    remarks: str | None = None

    @field_validator("scheme")
    @classmethod
    def validate_scheme(cls, v: str) -> str:
        v = (v or "").strip()
        if v not in _vocabs().mapping_schemes.keys:
            raise ValueError(f"Unknown mapping scheme: {v}")
        return v

class MappingRule(DtoBaseModel):
    """
    A single mapping statement, e.g.:
    privacy_control_id -> [ {scheme: "sdm", value:"TOM-03"} ]
    """
    source_id: str
    targets: List[MappingRef] = []
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    rationale: Optional[str] = None

class MappingSetMeta(DtoBaseModel):
    id: str
    title: str
    version: str
    description: Optional[str] = None

class MappingSet(DtoBaseModel):
    meta: MappingSetMeta
    rules: List[MappingRule] = []

class MappingHit(DtoBaseModel):
    source_id: str
    target: MappingRef
    rule_confidence: Optional[float] = None
    rule_rationale: Optional[str] = None
