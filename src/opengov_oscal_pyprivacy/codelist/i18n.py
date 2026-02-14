from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class TranslationOverlay:
    """Loads and applies i18n overlays to codelists.

    Overlay format (per locale file, e.g. fr.json):
    {
        "data-categories": {
            "health-data": {
                "label": "Données de santé",
                "definition": "Données relatives à la santé..."
            }
        }
    }
    """

    def __init__(self, i18n_dir: Optional[Path] = None) -> None:
        self._overlays: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {}
        if i18n_dir is not None and i18n_dir.exists():
            self._load_dir(i18n_dir)

    def _load_dir(self, i18n_dir: Path) -> None:
        """Load all locale JSON files from directory."""
        for path in sorted(i18n_dir.glob("*.json")):
            locale = path.stem  # e.g. "fr" from "fr.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            self._overlays[locale] = data

    def get_label(self, list_id: str, code: str, locale: str) -> Optional[str]:
        """Get a translated label. Returns None if not found."""
        locale_data = self._overlays.get(locale)
        if locale_data is None:
            return None
        list_data = locale_data.get(list_id)
        if list_data is None:
            return None
        entry_data = list_data.get(code)
        if entry_data is None:
            return None
        return entry_data.get("label")

    def get_definition(self, list_id: str, code: str, locale: str) -> Optional[str]:
        """Get a translated definition. Returns None if not found."""
        locale_data = self._overlays.get(locale)
        if locale_data is None:
            return None
        list_data = locale_data.get(list_id)
        if list_data is None:
            return None
        entry_data = list_data.get(code)
        if entry_data is None:
            return None
        return entry_data.get("definition")

    def available_locales(self) -> List[str]:
        """Return all loaded locale codes."""
        return sorted(self._overlays.keys())

    def coverage(self, list_id: str, locale: str) -> float:
        """Return translation coverage (0.0-1.0) for a list in a locale.

        Returns 0.0 if the locale or list is not found.
        """
        locale_data = self._overlays.get(locale)
        if locale_data is None:
            return 0.0
        list_data = locale_data.get(list_id)
        if list_data is None:
            return 0.0
        # Count entries that have a "label" key.
        translated = sum(1 for v in list_data.values() if isinstance(v, dict) and "label" in v)
        total = len(list_data) if list_data else 1
        return translated / total if total > 0 else 0.0

    @classmethod
    def load_defaults(cls) -> TranslationOverlay:
        """Load overlays from the packaged i18n directory."""
        from importlib.resources import files

        i18n_dir = Path(str(files("opengov_oscal_pyprivacy"))) / "data" / "i18n"
        return cls(i18n_dir)
