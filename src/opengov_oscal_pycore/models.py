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


class Control(OscalBaseModel):
    id: str
    class_: Optional[str] = Field(default=None, alias="class")
    title: Optional[str] = None
    props: List[Property] = Field(default_factory=list)


class Group(OscalBaseModel):
    id: str
    class_: Optional[str] = Field(default=None, alias="class")
    title: Optional[str] = None
    controls: List[Control] = Field(default_factory=list)


class Catalog(OscalBaseModel):
    uuid: str
    metadata: Dict[str, Any]
    groups: List[Group] = Field(default_factory=list)

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
