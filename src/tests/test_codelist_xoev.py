"""Tests for XÖV-VVT codelist JSON files (Issue #35).

Verifies that all 13 new codelist JSON files load correctly via the
CodelistRegistry and contain valid, well-formed entries with proper
bilingual labels.
"""

from __future__ import annotations

import pytest

from opengov_oscal_pyprivacy.codelist.registry import CodelistRegistry


@pytest.fixture(scope="module")
def registry() -> CodelistRegistry:
    return CodelistRegistry.load_defaults()


# ---------------------------------------------------------------------------
# TestXoevListsLoad — verify all 13 new lists are discoverable
# ---------------------------------------------------------------------------


class TestXoevListsLoad:
    """Verify that all new XÖV-VVT lists load into the registry."""

    def test_all_lists_loaded(self, registry: CodelistRegistry) -> None:
        """At least 19 lists total (6 migrated + 13 new)."""
        assert len(registry.list_ids()) >= 19

    def test_data_categories_loaded(self, registry: CodelistRegistry) -> None:
        assert "data-categories" in registry.list_ids()

    def test_data_subjects_loaded(self, registry: CodelistRegistry) -> None:
        assert "data-subjects" in registry.list_ids()

    def test_recipients_loaded(self, registry: CodelistRegistry) -> None:
        assert "recipients" in registry.list_ids()

    def test_legal_instruments_loaded(self, registry: CodelistRegistry) -> None:
        assert "legal-instruments" in registry.list_ids()

    def test_protection_levels_loaded(self, registry: CodelistRegistry) -> None:
        assert "protection-levels" in registry.list_ids()


# ---------------------------------------------------------------------------
# TestDataCategories — detailed validation of the data-categories list
# ---------------------------------------------------------------------------


class TestDataCategories:
    """Validate the data-categories codelist content."""

    def test_has_entries(self, registry: CodelistRegistry) -> None:
        cl = registry.get_list("data-categories")
        assert len(cl.entries) >= 10

    def test_health_data_present(self, registry: CodelistRegistry) -> None:
        cl = registry.get_list("data-categories")
        assert cl.validate_code("health-data") is True

    def test_health_data_german_label(self, registry: CodelistRegistry) -> None:
        label = registry.get_label("data-categories", "health-data", "de")
        assert label == "Gesundheitsdaten"

    def test_xoev_code_mapped(self, registry: CodelistRegistry) -> None:
        entry = registry.resolve_code("data-categories", "health-data")
        assert entry.xoev_code == "gesundheit"

    def test_special_category_group(self, registry: CodelistRegistry) -> None:
        entry = registry.resolve_code("data-categories", "health-data")
        assert entry.metadata.group == "special"

    def test_criminal_data_group(self, registry: CodelistRegistry) -> None:
        entry = registry.resolve_code("data-categories", "criminal-data")
        assert entry.metadata.group == "criminal"


# ---------------------------------------------------------------------------
# TestProtectionLevels — validate the non-XÖV protection-levels list
# ---------------------------------------------------------------------------


class TestProtectionLevels:
    """Validate the protection-levels codelist."""

    def test_three_levels(self, registry: CodelistRegistry) -> None:
        cl = registry.get_list("protection-levels")
        assert len(cl.entries) == 3

    def test_enhanced_present(self, registry: CodelistRegistry) -> None:
        cl = registry.get_list("protection-levels")
        assert cl.validate_code("enhanced") is True


# ---------------------------------------------------------------------------
# TestAllListsValid — cross-cutting validation for every registered list
# ---------------------------------------------------------------------------


class TestAllListsValid:
    """Cross-cutting validation across all registered codelists."""

    def test_all_lists_have_entries(self, registry: CodelistRegistry) -> None:
        for list_id in registry.list_ids():
            cl = registry.get_list(list_id)
            assert len(cl.entries) >= 1, f"{list_id} has no entries"

    def test_all_entries_have_en_labels(self, registry: CodelistRegistry) -> None:
        for list_id in registry.list_ids():
            cl = registry.get_list(list_id)
            for entry in cl.entries:
                assert entry.labels.en, (
                    f"{list_id}/{entry.code} missing English label"
                )
