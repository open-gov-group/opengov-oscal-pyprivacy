"""Tests for the multilingual translation overlay (i18n) layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from opengov_oscal_pyprivacy.codelist.i18n import TranslationOverlay


@pytest.fixture
def overlay() -> TranslationOverlay:
    """Load the default i18n overlays."""
    return TranslationOverlay.load_defaults()


@pytest.fixture
def empty_overlay() -> TranslationOverlay:
    """An overlay with no files loaded."""
    return TranslationOverlay()


# ===========================================================================
# Loading
# ===========================================================================


class TestTranslationOverlayLoad:
    """Tests for loading translation overlays."""

    def test_load_defaults(self, overlay: TranslationOverlay) -> None:
        """load_defaults loads without error and returns an overlay."""
        assert isinstance(overlay, TranslationOverlay)

    def test_available_locales(self, overlay: TranslationOverlay) -> None:
        """The default overlays include French."""
        assert "fr" in overlay.available_locales()

    def test_empty_overlay_locales(self, empty_overlay: TranslationOverlay) -> None:
        """An empty overlay has no locales."""
        assert empty_overlay.available_locales() == []


# ===========================================================================
# get_label
# ===========================================================================


class TestGetLabel:
    """Tests for TranslationOverlay.get_label()."""

    def test_get_label_fr_found(self, overlay: TranslationOverlay) -> None:
        """French label for health-data in data-categories is found."""
        label = overlay.get_label("data-categories", "health-data", "fr")
        assert label == "Donn\u00e9es de sant\u00e9"

    def test_get_label_fr_not_found(self, overlay: TranslationOverlay) -> None:
        """A code not in the overlay returns None."""
        label = overlay.get_label("data-categories", "employment-data", "fr")
        assert label is None

    def test_get_label_unknown_locale(self, overlay: TranslationOverlay) -> None:
        """Requesting a locale that has no overlay returns None."""
        label = overlay.get_label("data-categories", "health-data", "es")
        assert label is None

    def test_get_label_unknown_list(self, overlay: TranslationOverlay) -> None:
        """Requesting an unknown list_id returns None."""
        label = overlay.get_label("no-such-list", "health-data", "fr")
        assert label is None

    def test_get_label_unknown_code(self, overlay: TranslationOverlay) -> None:
        """Requesting an unknown code returns None."""
        label = overlay.get_label("data-categories", "no-such-code", "fr")
        assert label is None


# ===========================================================================
# get_definition
# ===========================================================================


class TestGetDefinition:
    """Tests for TranslationOverlay.get_definition()."""

    def test_get_definition_present(self, overlay: TranslationOverlay) -> None:
        """French definition for health-data is present."""
        defn = overlay.get_definition("data-categories", "health-data", "fr")
        assert defn is not None
        assert "sant\u00e9" in defn

    def test_get_definition_absent(self, overlay: TranslationOverlay) -> None:
        """contact-data has a label but no definition in French."""
        defn = overlay.get_definition("data-categories", "contact-data", "fr")
        assert defn is None

    def test_get_definition_unknown(self, overlay: TranslationOverlay) -> None:
        """Unknown code returns None for definition."""
        defn = overlay.get_definition("data-categories", "nonexistent", "fr")
        assert defn is None


# ===========================================================================
# coverage
# ===========================================================================


class TestCoverage:
    """Tests for TranslationOverlay.coverage()."""

    def test_coverage_fr_data_categories(self, overlay: TranslationOverlay) -> None:
        """French data-categories has some translated entries (> 0.0)."""
        cov = overlay.coverage("data-categories", "fr")
        assert cov > 0.0

    def test_coverage_fr_protection_levels(self, overlay: TranslationOverlay) -> None:
        """French protection-levels has all 3 entries translated (1.0)."""
        cov = overlay.coverage("protection-levels", "fr")
        assert cov == 1.0

    def test_coverage_unknown_locale(self, overlay: TranslationOverlay) -> None:
        """Unknown locale returns 0.0 coverage."""
        cov = overlay.coverage("data-categories", "es")
        assert cov == 0.0

    def test_coverage_unknown_list(self, overlay: TranslationOverlay) -> None:
        """Unknown list returns 0.0 coverage."""
        cov = overlay.coverage("no-such-list", "fr")
        assert cov == 0.0


# ===========================================================================
# Empty overlay
# ===========================================================================


class TestEmptyOverlay:
    """Tests for an overlay with no files loaded."""

    def test_empty_get_label(self, empty_overlay: TranslationOverlay) -> None:
        """get_label returns None on an empty overlay."""
        assert empty_overlay.get_label("data-categories", "health-data", "fr") is None

    def test_empty_coverage(self, empty_overlay: TranslationOverlay) -> None:
        """coverage returns 0.0 on an empty overlay."""
        assert empty_overlay.coverage("data-categories", "fr") == 0.0
