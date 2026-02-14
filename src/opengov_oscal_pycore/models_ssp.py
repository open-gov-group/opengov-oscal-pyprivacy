from __future__ import annotations

"""
OSCAL System Security Plan (SSP) models (Pydantic v2).

Covers the system-security-plan model layer from the OSCAL specification,
including SystemSecurityPlan, SystemCharacteristics, ImportProfile,
SspControlImplementation, and SspImplementedRequirement.
"""

from typing import Any, Optional, Dict, List
from pydantic import Field, model_validator
from .models import OscalBaseModel, OscalMetadata, BackMatter, Property, Link


class SspImplementedRequirement(OscalBaseModel):
    """An implemented-requirement within an SSP control-implementation."""

    uuid: str
    control_id: str = Field(alias="control-id")
    description: Optional[str] = None
    props: List[Property] = Field(default_factory=list)
    links: List[Link] = Field(default_factory=list)
    statements: List[Dict[str, Any]] = Field(default_factory=list)


class SspControlImplementation(OscalBaseModel):
    """Control implementation section of an SSP."""

    description: Optional[str] = None
    implemented_requirements: List[SspImplementedRequirement] = Field(
        default_factory=list, alias="implemented-requirements"
    )


class SystemCharacteristics(OscalBaseModel):
    """System characteristics section of an SSP."""

    system_name: Optional[str] = Field(default=None, alias="system-name")
    description: Optional[str] = None
    security_sensitivity_level: Optional[str] = Field(
        default=None, alias="security-sensitivity-level"
    )
    system_ids: List[Dict[str, Any]] = Field(
        default_factory=list, alias="system-ids"
    )
    props: List[Property] = Field(default_factory=list)


class ImportProfile(OscalBaseModel):
    """Reference to the profile imported by an SSP."""

    href: str


class SystemSecurityPlan(OscalBaseModel):
    """OSCAL System Security Plan: describes how a system implements controls."""

    uuid: str
    metadata: OscalMetadata
    import_profile: ImportProfile = Field(alias="import-profile")
    system_characteristics: Optional[SystemCharacteristics] = Field(
        default=None, alias="system-characteristics"
    )
    control_implementation: Optional[SspControlImplementation] = Field(
        default=None, alias="control-implementation"
    )
    back_matter: Optional[BackMatter] = Field(default=None, alias="back-matter")

    @model_validator(mode="before")
    @classmethod
    def _unwrap_ssp_root(cls, data: Any) -> Any:
        """Accept both bare and {"system-security-plan": {...}} root form."""
        if isinstance(data, dict) and "system-security-plan" in data and "uuid" not in data:
            return data["system-security-plan"]
        return data
