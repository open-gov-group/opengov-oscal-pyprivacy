from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class SecurityControl(BaseModel):
    id: str
    title: str
    class_: Optional[str] = None
    domain: Optional[str] = None
    objective: Optional[str] = None
    description: Optional[str] = None


class SecurityControlUpdateRequest(BaseModel):
    title: Optional[str] = None
    domain: Optional[str] = None
    objective: Optional[str] = None
    description: Optional[str] = None
