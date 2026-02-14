from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import Codelist


def load_codelist_json(path: Path) -> Codelist:
    """Load a single codelist from a JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return Codelist.model_validate(data)


def load_codelist_dir(directory: Path) -> List[Codelist]:
    """Load all codelists from JSON files in a directory."""
    codelists = []
    for path in sorted(directory.glob("*.json")):
        codelists.append(load_codelist_json(path))
    return codelists
