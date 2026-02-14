from __future__ import annotations

"""
OSCAL Component Definition models (Pydantic v2).

Covers the component-definition model layer from the OSCAL specification,
including Component, Capability, ControlImplementation, and
ImplementedRequirement.
"""

from typing import Any, Optional, List
from pydantic import Field, model_validator
from .models import OscalBaseModel, OscalMetadata, BackMatter, Property, Link


class ImplementedRequirement(OscalBaseModel):
    uuid: str
    control_id: str = Field(alias="control-id")
    description: Optional[str] = None
    props: List[Property] = Field(default_factory=list)
    links: List[Link] = Field(default_factory=list)


class ControlImplementation(OscalBaseModel):
    uuid: str
    source: str
    description: Optional[str] = None
    implemented_requirements: List[ImplementedRequirement] = Field(
        default_factory=list, alias="implemented-requirements"
    )


class Component(OscalBaseModel):
    uuid: str
    type: str
    title: str
    description: Optional[str] = None
    props: List[Property] = Field(default_factory=list)
    links: List[Link] = Field(default_factory=list)
    control_implementations: List[ControlImplementation] = Field(
        default_factory=list, alias="control-implementations"
    )


class Capability(OscalBaseModel):
    uuid: str
    name: str
    description: Optional[str] = None
    props: List[Property] = Field(default_factory=list)
    links: List[Link] = Field(default_factory=list)
    control_implementations: List[ControlImplementation] = Field(
        default_factory=list, alias="control-implementations"
    )


class ComponentDefinition(OscalBaseModel):
    uuid: str
    metadata: OscalMetadata
    components: List[Component] = Field(default_factory=list)
    capabilities: List[Capability] = Field(default_factory=list)
    back_matter: Optional[BackMatter] = Field(default=None, alias="back-matter")

    @model_validator(mode="before")
    @classmethod
    def _unwrap_component_definition_root(cls, data: Any) -> Any:
        """Accept both bare and {"component-definition": {...}} root form."""
        if isinstance(data, dict) and "component-definition" in data and "uuid" not in data:
            return data["component-definition"]
        return data
