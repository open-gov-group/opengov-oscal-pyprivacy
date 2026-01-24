from __future__ import annotations
from pydantic import BaseModel

class TextItemCreate(BaseModel):
    prose: str

class TextItemUpdate(BaseModel):
    prose: str

class TextItem(BaseModel):
    id: str
    prose: str
