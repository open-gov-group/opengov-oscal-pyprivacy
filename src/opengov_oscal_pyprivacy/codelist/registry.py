from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from .models import Codelist, CodeEntry
from .loader import load_codelist_dir


class CodelistRegistry:
    """Central registry for all codelists. Thread-safe singleton via load_defaults()."""

    def __init__(self) -> None:
        self._lists: Dict[str, Codelist] = {}

    def register(self, codelist: Codelist) -> None:
        """Register a codelist. Overwrites existing with same list_id."""
        self._lists[codelist.list_id] = codelist

    def get_list(self, list_id: str) -> Codelist:
        """Get a codelist by ID. Raises KeyError if not found."""
        return self._lists[list_id]

    def get_label(self, list_id: str, code: str, locale: str = "en") -> str:
        """Get the display label for a code. Raises KeyError if list/code not found."""
        entry = self.resolve_code(list_id, code)
        return entry.get_label(locale)

    def get_definition(
        self, list_id: str, code: str, locale: str = "en"
    ) -> Optional[str]:
        """Get the definition for a code. Returns None if no definition."""
        entry = self.resolve_code(list_id, code)
        return entry.get_definition(locale)

    def resolve_code(self, list_id: str, code: str) -> CodeEntry:
        """Resolve a code to its CodeEntry. Raises KeyError if not found."""
        cl = self.get_list(list_id)
        entry = cl.get_entry(code)
        if entry is None:
            raise KeyError(f"Code '{code}' not found in codelist '{list_id}'")
        return entry

    def validate_code(self, list_id: str, code: str) -> bool:
        """Check if a code is valid in a codelist."""
        try:
            cl = self.get_list(list_id)
        except KeyError:
            return False
        return cl.validate_code(code)

    def search(
        self, list_id: str, query: str, locale: str = "en"
    ) -> List[CodeEntry]:
        """Search entries by label substring (case-insensitive)."""
        cl = self.get_list(list_id)
        query_lower = query.lower()
        results = []
        for entry in cl.entries:
            label = entry.get_label(locale)
            if query_lower in label.lower():
                results.append(entry)
        return results

    def list_codes(
        self,
        list_id: str,
        *,
        group: Optional[str] = None,
        include_deprecated: bool = False,
    ) -> List[str]:
        """List all codes, optionally filtered by group."""
        cl = self.get_list(list_id)
        codes = []
        for entry in cl.entries:
            if not include_deprecated and entry.deprecated:
                continue
            if group is not None and entry.metadata.group != group:
                continue
            codes.append(entry.code)
        return codes

    def list_ids(self) -> List[str]:
        """Return all registered codelist IDs."""
        return sorted(self._lists.keys())

    @classmethod
    def load_defaults(cls) -> CodelistRegistry:
        """Load all default codelists from the packaged data directory."""
        from importlib.resources import files

        data_dir = (
            Path(str(files("opengov_oscal_pyprivacy"))) / "data" / "codelists"
        )
        registry = cls()
        if data_dir.exists():
            for cl in load_codelist_dir(data_dir):
                registry.register(cl)
        return registry
