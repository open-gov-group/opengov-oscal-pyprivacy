from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CodelistBaseModel(BaseModel):
    """Base for all codelist models. Strict: no extra fields allowed."""

    model_config = ConfigDict(extra="forbid")


class CodeLabel(CodelistBaseModel):
    """Multilingual label. English required, others optional."""

    en: str
    de: Optional[str] = None
    fr: Optional[str] = None

    def get(self, locale: str = "en", fallback_code: Optional[str] = None) -> str:
        """Get label for locale with fallback chain: locale -> en -> fallback_code -> en."""
        value = getattr(self, locale, None)
        if value is not None:
            return value
        if self.en:
            return self.en
        if fallback_code is not None:
            return fallback_code
        return self.en


class CodeEntryMetadata(CodelistBaseModel):
    """Domain-specific metadata for a code entry."""

    group: Optional[str] = None
    gdpr_article: Optional[str] = None
    legal_basis: Optional[str] = None
    iso_reference: Optional[str] = None
    protection_level_min: Optional[str] = None
    extra: Dict[str, str] = Field(default_factory=dict)


class CodeEntry(CodelistBaseModel):
    """Single entry in a codelist."""

    code: str
    labels: CodeLabel
    definition: Optional[CodeLabel] = None
    metadata: CodeEntryMetadata = Field(default_factory=CodeEntryMetadata)
    xoev_code: Optional[str] = None
    deprecated: bool = False
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    sort_order: int = 0

    def get_label(self, locale: str = "en") -> str:
        """Get the display label for this entry in the given locale."""
        return self.labels.get(locale, fallback_code=self.code)

    def get_definition(self, locale: str = "en") -> Optional[str]:
        """Get the definition text for this entry in the given locale."""
        if self.definition is None:
            return None
        return self.definition.get(locale, fallback_code=None)


class CascadeEffect(CodelistBaseModel):
    """A single effect triggered by a cascade rule."""

    target_list: str
    target_field: str
    operator: str  # "set_minimum", "require", "flag"
    value: str
    description: CodeLabel


class CascadeRule(CodelistBaseModel):
    """Declarative rule that triggers cascade effects based on conditions."""

    rule_id: str
    source_list: str
    source_field: str
    condition: str  # e.g. "== 'special'"
    effects: List[CascadeEffect]
    priority: int = 100
    description: CodeLabel


class Codelist(CodelistBaseModel):
    """Complete codelist with entries and optional cascade rules."""

    list_id: str
    version: str
    namespace_uri: str
    title: CodeLabel
    description: Optional[CodeLabel] = None
    source: Optional[str] = None
    entries: List[CodeEntry]
    cascade_rules: List[CascadeRule] = Field(default_factory=list)

    def get_entry(self, code: str) -> Optional[CodeEntry]:
        """Find an entry by code. Returns None if not found."""
        for entry in self.entries:
            if entry.code == code:
                return entry
        return None

    def get_codes(self, *, include_deprecated: bool = False) -> List[str]:
        """Return all codes in this codelist."""
        return [
            e.code
            for e in self.entries
            if include_deprecated or not e.deprecated
        ]

    def validate_code(self, code: str) -> bool:
        """Check if a code exists in this codelist (non-deprecated)."""
        return any(e.code == code and not e.deprecated for e in self.entries)
