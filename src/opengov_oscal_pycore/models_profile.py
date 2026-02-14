from __future__ import annotations

"""
OSCAL Profile model (Pydantic v2).

A Profile selects and tailors controls from one or more catalogs via imports,
optional merge strategy, and parameter/control modifications.
"""

from typing import Any, Optional, Dict, List

from pydantic import Field, model_validator

from .models import OscalBaseModel, OscalMetadata, BackMatter


class ImportRef(OscalBaseModel):
    """Reference to an imported catalog with optional control filtering."""

    href: str
    include_controls: List[Dict[str, Any]] = Field(
        default_factory=list, alias="include-controls"
    )
    exclude_controls: List[Dict[str, Any]] = Field(
        default_factory=list, alias="exclude-controls"
    )


class Modify(OscalBaseModel):
    """Parameter overrides and control alterations."""

    set_parameters: List[Dict[str, Any]] = Field(
        default_factory=list, alias="set-parameters"
    )
    alters: List[Dict[str, Any]] = Field(default_factory=list)


class Profile(OscalBaseModel):
    """OSCAL Profile: selects and tailors controls from source catalogs."""

    uuid: str
    metadata: OscalMetadata
    imports: List[ImportRef] = Field(default_factory=list)
    merge: Optional[Dict[str, Any]] = None
    modify: Optional[Modify] = None
    back_matter: Optional[BackMatter] = Field(default=None, alias="back-matter")

    @model_validator(mode="before")
    @classmethod
    def _unwrap_profile_root(cls, data: Any) -> Any:
        """Accept both bare and {"profile": {...}} root form."""
        if isinstance(data, dict) and "profile" in data and "uuid" not in data:
            return data["profile"]
        return data
