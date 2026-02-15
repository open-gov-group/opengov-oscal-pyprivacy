from __future__ import annotations

"""
Minimal OSCAL subset models (Pydantic v2).

Design goals:
- Round-trip safety for Workbench JSON exports (extra fields must not be lost)
- Stable Python-facing field names (e.g. class_ for OSCAL "class")
- Keep the surface intentionally small; extend as needed.
"""

from typing import Any, Optional, Dict, List
from pydantic import BaseModel, Field, ConfigDict, model_validator


class OscalBaseModel(BaseModel):
    # Allow unknown OSCAL fields to survive load/save cycles
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Property(OscalBaseModel):
    name: str
    value: str

    # OSCAL JSON uses "class"
    class_: Optional[str] = Field(default=None, alias="class")

    # frequently used in Workbench exports
    ns: Optional[str] = None
    group: Optional[str] = None
    remarks: Optional[str] = None


class Link(OscalBaseModel):
    href: str
    rel: Optional[str] = None
    text: Optional[str] = None


class Part(OscalBaseModel):
    id: Optional[str] = None
    name: str
    class_: Optional[str] = Field(default=None, alias="class")
    title: Optional[str] = None
    prose: Optional[str] = None
    props: List[Property] = Field(default_factory=list)
    links: List[Link] = Field(default_factory=list)
    parts: List[Part] = Field(default_factory=list)


class Parameter(OscalBaseModel):
    id: str
    label: Optional[str] = None
    class_: Optional[str] = Field(default=None, alias="class")
    usage: Optional[str] = None
    values: List[str] = Field(default_factory=list)
    select: Optional[Dict[str, Any]] = None
    constraints: List[Dict[str, Any]] = Field(default_factory=list)
    guidelines: List[Dict[str, Any]] = Field(default_factory=list)
    props: List[Property] = Field(default_factory=list)
    links: List[Link] = Field(default_factory=list)


class Control(OscalBaseModel):
    id: str
    class_: Optional[str] = Field(default=None, alias="class")
    title: Optional[str] = None
    props: List[Property] = Field(default_factory=list)
    parts: List[Part] = Field(default_factory=list)
    links: List[Link] = Field(default_factory=list)
    params: List[Parameter] = Field(default_factory=list)
    controls: List[Control] = Field(default_factory=list)


class Group(OscalBaseModel):
    id: str
    class_: Optional[str] = Field(default=None, alias="class")
    title: Optional[str] = None
    controls: List[Control] = Field(default_factory=list)
    parts: List[Part] = Field(default_factory=list)
    props: List[Property] = Field(default_factory=list)
    groups: List[Group] = Field(default_factory=list)


class Role(OscalBaseModel):
    id: str
    title: Optional[str] = None


class Party(OscalBaseModel):
    uuid: str
    type: Optional[str] = None
    name: Optional[str] = None


class OscalMetadata(OscalBaseModel):
    title: str
    last_modified: Optional[str] = Field(default=None, alias="last-modified")
    version: Optional[str] = None
    oscal_version: Optional[str] = Field(default=None, alias="oscal-version")
    roles: List[Role] = Field(default_factory=list)
    parties: List[Party] = Field(default_factory=list)


class Rlink(OscalBaseModel):
    href: str
    media_type: Optional[str] = Field(default=None, alias="media-type")


class Resource(OscalBaseModel):
    uuid: str
    title: Optional[str] = None
    rlinks: List[Rlink] = Field(default_factory=list)
    props: List[Property] = Field(default_factory=list)


class BackMatter(OscalBaseModel):
    resources: List[Resource] = Field(default_factory=list)


class Catalog(OscalBaseModel):
    uuid: str
    metadata: OscalMetadata
    groups: List[Group] = Field(default_factory=list)
    back_matter: Optional[BackMatter] = Field(default=None, alias="back-matter")

    @model_validator(mode="before")
    @classmethod
    def _unwrap_catalog_root(cls, data: Any) -> Any:
        """
        Accept both:
          - {"uuid": ..., "metadata": ..., "groups": ...}
          - {"catalog": {...}}   (common OSCAL JSON root form)
        """
        if isinstance(data, dict) and "catalog" in data and ("uuid" not in data and "metadata" not in data):
            return data["catalog"]
        return data


# Rebuild models to resolve recursive forward references
Part.model_rebuild()
Control.model_rebuild()
Group.model_rebuild()
