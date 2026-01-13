from __future__ import annotations

import json
from pathlib import Path
from typing import Generic, TypeVar, Type

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class OscalRepository(Generic[T]):
    """
    Kapselt das Lesen/Schreiben von OSCAL-JSON-Dateien in einem Basis-Repo.

    Beispiel:
        repo = OscalRepository[Catalog](Path("/path/to/oscal-repo"))
        catalog = repo.load("catalogs/privacy.json", Catalog)
        # ... Änderungen ...
        repo.save("catalogs/privacy.json", catalog)
    """
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def resolve(self, rel_path: str | Path) -> Path:
        return self.base_path / Path(rel_path)

    def load(self, rel_path: str | Path, model: Type[T]) -> T:
        full_path = self.resolve(rel_path)
        with full_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return model.model_validate(data)

    def save(self, rel_path: str | Path, obj: T) -> None:
        full_path = self.resolve(rel_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        text = obj.model_dump_json(by_alias=True, exclude_none=True, indent=2)
        full_path.write_text(text, encoding="utf-8")




