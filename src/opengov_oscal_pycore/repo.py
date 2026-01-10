from __future__ import annotations

from pathlib import Path
from typing import Generic, TypeVar, Type

import json
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
        return model.parse_obj(data)

    def save(self, rel_path: str | Path, obj: T) -> None:
        full_path = self.resolve(rel_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # obj.json() liefert bereits korrektes OSCAL-JSON (by_alias etc.), je nach oscal-pydantic-Version ggf. anpassen
        text = obj.json(by_alias=True, exclude_none=True, indent=2, ensure_ascii=False)
        with full_path.open("w", encoding="utf-8") as f:
            f.write(text)
