from __future__ import annotations

from typing import Optional

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
