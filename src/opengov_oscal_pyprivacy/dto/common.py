from __future__ import annotations
from pydantic import BaseModel, ConfigDict

class DtoBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

class TextItemCreate(DtoBaseModel):
    prose: str

class TextItemUpdate(DtoBaseModel):
    prose: str

class TextItem(DtoBaseModel):
    id: str
    prose: str
