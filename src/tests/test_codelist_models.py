from __future__ import annotations

import json
from datetime import date

import pytest
from pydantic import ValidationError

from opengov_oscal_pyprivacy.codelist.models import (
    CodeLabel,
    CodeEntryMetadata,
    CodeEntry,
    CascadeEffect,
    CascadeRule,
    Codelist,
    CodelistBaseModel,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(
    code: str,
    en: str,
    *,
    de: str | None = None,
    deprecated: bool = False,
) -> CodeEntry:
    """Shorthand factory for tests."""
    return CodeEntry(code=code, labels=CodeLabel(en=en, de=de), deprecated=deprecated)


def _make_codelist(entries: list[CodeEntry] | None = None) -> Codelist:
    """Shorthand factory for a minimal Codelist."""
    if entries is None:
        entries = [
            _make_entry("A", "Alpha", de="Alpha-de"),
            _make_entry("B", "Beta"),
            _make_entry("C", "Charlie", deprecated=True),
        ]
    return Codelist(
        list_id="test-list",
        version="1.0",
        namespace_uri="urn:example:test",
        title=CodeLabel(en="Test List"),
        entries=entries,
    )


# ===========================================================================
# TestCodeLabel
# ===========================================================================


class TestCodeLabel:
    """Tests for CodeLabel multilingual label model."""

    def test_create_minimal(self) -> None:
        """Only 'en' is required."""
        label = CodeLabel(en="Hello")
        assert label.en == "Hello"
        assert label.de is None
        assert label.fr is None

    def test_create_full(self) -> None:
        """All locales populated."""
        label = CodeLabel(en="Hello", de="Hallo", fr="Bonjour")
        assert label.en == "Hello"
        assert label.de == "Hallo"
        assert label.fr == "Bonjour"

    def test_get_locale_en(self) -> None:
        """Requesting 'en' returns the English label."""
        label = CodeLabel(en="Hello")
        assert label.get("en") == "Hello"

    def test_get_locale_de(self) -> None:
        """Requesting 'de' returns the German label when present."""
        label = CodeLabel(en="Hello", de="Hallo")
        assert label.get("de") == "Hallo"

    def test_get_locale_fallback_to_en(self) -> None:
        """Requesting an absent locale falls back to 'en'."""
        label = CodeLabel(en="Hello")
        assert label.get("fr") == "Hello"

    def test_get_locale_with_fallback_code(self) -> None:
        """When locale is missing, falls back to en (en is always present)."""
        label = CodeLabel(en="Hello")
        result = label.get("it", fallback_code="FALLBACK")
        # en is present and non-empty, so it returns en, not fallback_code
        assert result == "Hello"

    def test_get_locale_with_fallback_code_empty_en(self) -> None:
        """When en is empty string, fallback_code should be used."""
        label = CodeLabel(en="")
        result = label.get("fr", fallback_code="MY_CODE")
        # en is "", which is falsy, so fallback_code is returned
        assert result == "MY_CODE"

    def test_extra_field_forbidden(self) -> None:
        """CodeLabel rejects unknown fields (extra='forbid')."""
        with pytest.raises(ValidationError):
            CodeLabel(en="X", unknown="Y")


# ===========================================================================
# TestCodeEntry
# ===========================================================================


class TestCodeEntry:
    """Tests for CodeEntry model."""

    def test_create_minimal(self) -> None:
        """Only code and labels are required."""
        entry = _make_entry("A", "Alpha")
        assert entry.code == "A"
        assert entry.labels.en == "Alpha"
        assert entry.deprecated is False
        assert entry.sort_order == 0
        assert entry.metadata.group is None

    def test_create_full(self) -> None:
        """All fields populated."""
        entry = CodeEntry(
            code="FULL",
            labels=CodeLabel(en="Full Entry", de="Voller Eintrag"),
            definition=CodeLabel(en="A fully populated entry"),
            metadata=CodeEntryMetadata(
                group="test-group",
                gdpr_article="Art. 6",
                extra={"custom": "value"},
            ),
            xoev_code="XOV-001",
            deprecated=True,
            valid_from=date(2024, 1, 1),
            valid_until=date(2025, 12, 31),
            sort_order=5,
        )
        assert entry.code == "FULL"
        assert entry.xoev_code == "XOV-001"
        assert entry.deprecated is True
        assert entry.valid_from == date(2024, 1, 1)
        assert entry.valid_until == date(2025, 12, 31)
        assert entry.sort_order == 5
        assert entry.metadata.group == "test-group"
        assert entry.metadata.gdpr_article == "Art. 6"
        assert entry.metadata.extra == {"custom": "value"}

    def test_get_label_en(self) -> None:
        """get_label returns English label by default."""
        entry = _make_entry("A", "Alpha")
        assert entry.get_label("en") == "Alpha"

    def test_get_label_de(self) -> None:
        """get_label returns German label when present."""
        entry = _make_entry("A", "Alpha", de="Alpha-de")
        assert entry.get_label("de") == "Alpha-de"

    def test_get_label_fallback_to_code(self) -> None:
        """When requesting missing locale, falls back to en (not code, since en is present)."""
        entry = _make_entry("A", "Alpha")
        # "fr" is missing -> falls back to en
        assert entry.get_label("fr") == "Alpha"

    def test_get_definition_none(self) -> None:
        """get_definition returns None when definition is absent."""
        entry = _make_entry("A", "Alpha")
        assert entry.get_definition("en") is None

    def test_get_definition_present(self) -> None:
        """get_definition returns the definition text."""
        entry = CodeEntry(
            code="A",
            labels=CodeLabel(en="Alpha"),
            definition=CodeLabel(en="First letter of the alphabet"),
        )
        assert entry.get_definition("en") == "First letter of the alphabet"

    def test_extra_field_forbidden(self) -> None:
        """CodeEntry rejects unknown fields."""
        with pytest.raises(ValidationError):
            CodeEntry(
                code="A",
                labels=CodeLabel(en="Alpha"),
                unknown_field="bad",
            )


# ===========================================================================
# TestCodeEntryMetadata
# ===========================================================================


class TestCodeEntryMetadata:
    """Tests for CodeEntryMetadata model."""

    def test_create_empty(self) -> None:
        """All fields have sensible defaults."""
        meta = CodeEntryMetadata()
        assert meta.group is None
        assert meta.gdpr_article is None
        assert meta.legal_basis is None
        assert meta.iso_reference is None
        assert meta.protection_level_min is None
        assert meta.extra == {}

    def test_create_full(self) -> None:
        """All fields populated."""
        meta = CodeEntryMetadata(
            group="privacy",
            gdpr_article="Art. 5",
            legal_basis="Consent",
            iso_reference="ISO 27001:A.8",
            protection_level_min="high",
            extra={"custom_key": "custom_val"},
        )
        assert meta.group == "privacy"
        assert meta.gdpr_article == "Art. 5"
        assert meta.legal_basis == "Consent"
        assert meta.iso_reference == "ISO 27001:A.8"
        assert meta.protection_level_min == "high"
        assert meta.extra == {"custom_key": "custom_val"}

    def test_extra_dict(self) -> None:
        """The 'extra' dict field works correctly."""
        meta = CodeEntryMetadata(extra={"a": "1", "b": "2"})
        assert meta.extra["a"] == "1"
        assert len(meta.extra) == 2


# ===========================================================================
# TestCascadeRule
# ===========================================================================


class TestCascadeRule:
    """Tests for CascadeRule and CascadeEffect models."""

    def test_create_rule(self) -> None:
        """Full rule with effects."""
        effect = CascadeEffect(
            target_list="protection_levels",
            target_field="level",
            operator="set_minimum",
            value="high",
            description=CodeLabel(en="Set minimum protection to high"),
        )
        rule = CascadeRule(
            rule_id="R-001",
            source_list="data_categories",
            source_field="category",
            condition="== 'special'",
            effects=[effect],
            priority=50,
            description=CodeLabel(en="Special category rule"),
        )
        assert rule.rule_id == "R-001"
        assert rule.source_list == "data_categories"
        assert rule.condition == "== 'special'"
        assert len(rule.effects) == 1
        assert rule.effects[0].operator == "set_minimum"
        assert rule.priority == 50

    def test_priority_default(self) -> None:
        """Default priority is 100."""
        rule = CascadeRule(
            rule_id="R-002",
            source_list="src",
            source_field="fld",
            condition="== 'x'",
            effects=[],
            description=CodeLabel(en="Test rule"),
        )
        assert rule.priority == 100


# ===========================================================================
# TestCodelist
# ===========================================================================


class TestCodelist:
    """Tests for Codelist model."""

    def test_create_minimal(self) -> None:
        """Minimal codelist with required fields."""
        cl = _make_codelist()
        assert cl.list_id == "test-list"
        assert cl.version == "1.0"
        assert cl.namespace_uri == "urn:example:test"
        assert cl.title.en == "Test List"
        assert len(cl.entries) == 3
        assert cl.cascade_rules == []

    def test_get_entry_found(self) -> None:
        """get_entry returns the matching entry."""
        cl = _make_codelist()
        entry = cl.get_entry("A")
        assert entry is not None
        assert entry.code == "A"
        assert entry.labels.en == "Alpha"

    def test_get_entry_not_found(self) -> None:
        """get_entry returns None for non-existent code."""
        cl = _make_codelist()
        assert cl.get_entry("Z") is None

    def test_get_codes(self) -> None:
        """get_codes returns only non-deprecated codes by default."""
        cl = _make_codelist()
        codes = cl.get_codes()
        assert codes == ["A", "B"]
        assert "C" not in codes  # C is deprecated

    def test_get_codes_include_deprecated(self) -> None:
        """get_codes with include_deprecated=True returns all codes."""
        cl = _make_codelist()
        codes = cl.get_codes(include_deprecated=True)
        assert codes == ["A", "B", "C"]

    def test_validate_code_valid(self) -> None:
        """validate_code returns True for existing non-deprecated code."""
        cl = _make_codelist()
        assert cl.validate_code("A") is True

    def test_validate_code_invalid(self) -> None:
        """validate_code returns False for non-existent code."""
        cl = _make_codelist()
        assert cl.validate_code("Z") is False

    def test_validate_code_deprecated(self) -> None:
        """validate_code returns False for deprecated code."""
        cl = _make_codelist()
        assert cl.validate_code("C") is False


# ===========================================================================
# TestJsonRoundtrip
# ===========================================================================


class TestJsonRoundtrip:
    """Tests for JSON serialization / deserialization round-trips."""

    def test_codelist_json_roundtrip(self) -> None:
        """Create Codelist, dump to JSON, parse back, compare."""
        original = Codelist(
            list_id="roundtrip-list",
            version="2.0",
            namespace_uri="urn:example:roundtrip",
            title=CodeLabel(en="Roundtrip Test", de="Roundtrip-Test"),
            description=CodeLabel(en="A test for roundtrip"),
            source="internal",
            entries=[
                CodeEntry(
                    code="RT1",
                    labels=CodeLabel(en="Roundtrip One", de="Roundtrip Eins"),
                    definition=CodeLabel(en="First roundtrip entry"),
                    metadata=CodeEntryMetadata(
                        group="test",
                        gdpr_article="Art. 6(1)(a)",
                        extra={"custom": "value"},
                    ),
                    xoev_code="XOV-RT1",
                    deprecated=False,
                    valid_from=date(2024, 1, 1),
                    sort_order=1,
                ),
                CodeEntry(
                    code="RT2",
                    labels=CodeLabel(en="Roundtrip Two"),
                    deprecated=True,
                    sort_order=2,
                ),
            ],
            cascade_rules=[
                CascadeRule(
                    rule_id="CR-001",
                    source_list="test-list",
                    source_field="category",
                    condition="== 'special'",
                    effects=[
                        CascadeEffect(
                            target_list="protection_levels",
                            target_field="level",
                            operator="set_minimum",
                            value="high",
                            description=CodeLabel(en="Raise protection"),
                        ),
                    ],
                    priority=50,
                    description=CodeLabel(en="Special handling"),
                ),
            ],
        )

        json_str = original.model_dump_json()
        restored = Codelist.model_validate_json(json_str)

        assert restored.list_id == original.list_id
        assert restored.version == original.version
        assert restored.namespace_uri == original.namespace_uri
        assert restored.title.en == original.title.en
        assert restored.title.de == original.title.de
        assert restored.description is not None
        assert restored.description.en == "A test for roundtrip"
        assert restored.source == "internal"
        assert len(restored.entries) == 2
        assert restored.entries[0].code == "RT1"
        assert restored.entries[0].xoev_code == "XOV-RT1"
        assert restored.entries[0].valid_from == date(2024, 1, 1)
        assert restored.entries[0].metadata.gdpr_article == "Art. 6(1)(a)"
        assert restored.entries[0].metadata.extra == {"custom": "value"}
        assert restored.entries[1].deprecated is True
        assert len(restored.cascade_rules) == 1
        assert restored.cascade_rules[0].rule_id == "CR-001"
        assert restored.cascade_rules[0].priority == 50

    def test_codelist_from_json_string(self) -> None:
        """Parse a Codelist from a raw JSON string."""
        raw = json.dumps(
            {
                "list_id": "json-test",
                "version": "1.0",
                "namespace_uri": "urn:example:json",
                "title": {"en": "JSON Test"},
                "entries": [
                    {
                        "code": "J1",
                        "labels": {"en": "JSON One"},
                    },
                ],
            }
        )
        cl = Codelist.model_validate_json(raw)
        assert cl.list_id == "json-test"
        assert cl.version == "1.0"
        assert len(cl.entries) == 1
        assert cl.entries[0].code == "J1"
        assert cl.entries[0].labels.en == "JSON One"
        assert cl.entries[0].deprecated is False
        assert cl.cascade_rules == []
