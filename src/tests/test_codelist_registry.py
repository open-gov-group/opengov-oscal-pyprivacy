"""
Tests for codelist loader, registry, and CSV->JSON migration.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opengov_oscal_pyprivacy.codelist.models import Codelist, CodeEntry, CodeLabel
from opengov_oscal_pyprivacy.codelist.loader import load_codelist_json, load_codelist_dir
from opengov_oscal_pyprivacy.codelist.registry import CodelistRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _codelists_dir() -> Path:
    """Return the packaged codelists directory."""
    from importlib.resources import files

    return Path(str(files("opengov_oscal_pyprivacy"))) / "data" / "codelists"


def _make_codelist(list_id: str = "test-list", codes: list[str] | None = None) -> Codelist:
    """Create a minimal Codelist for testing."""
    if codes is None:
        codes = ["a", "b", "c"]
    entries = [
        {
            "code": c,
            "labels": {"en": c.upper(), "de": f"{c.upper()}_DE"},
            "sort_order": i + 1,
        }
        for i, c in enumerate(codes)
    ]
    return Codelist.model_validate(
        {
            "list_id": list_id,
            "version": "1.0.0",
            "namespace_uri": f"urn:test:{list_id}",
            "title": {"en": "Test List", "de": "Testliste"},
            "entries": entries,
        }
    )


# ===========================================================================
# Loader tests
# ===========================================================================


class TestLoader:
    """Tests for load_codelist_json and load_codelist_dir."""

    def test_load_codelist_json(self) -> None:
        """Load one of the JSON files and verify it parses to a Codelist."""
        path = _codelists_dir() / "assurance_goals.json"
        cl = load_codelist_json(path)
        assert isinstance(cl, Codelist)
        assert cl.list_id == "assurance-goals"
        assert len(cl.entries) >= 6

    def test_load_codelist_dir(self) -> None:
        """Load all JSON files from the codelists directory."""
        codelists = load_codelist_dir(_codelists_dir())
        assert len(codelists) >= 6
        ids = [cl.list_id for cl in codelists]
        assert "assurance-goals" in ids
        assert "measure-types" in ids

    def test_load_codelist_json_invalid_path(self) -> None:
        """Loading from a non-existent path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_codelist_json(Path("/nonexistent/does_not_exist.json"))


# ===========================================================================
# Registry basics
# ===========================================================================


class TestRegistryBasics:
    """Tests for CodelistRegistry core operations."""

    def test_register_and_get(self) -> None:
        """Register a codelist and retrieve it by ID."""
        reg = CodelistRegistry()
        cl = _make_codelist("my-list")
        reg.register(cl)
        result = reg.get_list("my-list")
        assert result is cl

    def test_get_list_not_found(self) -> None:
        """Getting a non-existent list raises KeyError."""
        reg = CodelistRegistry()
        with pytest.raises(KeyError):
            reg.get_list("nonexistent")

    def test_list_ids(self) -> None:
        """list_ids returns a sorted list of all registered IDs."""
        reg = CodelistRegistry()
        reg.register(_make_codelist("zebra"))
        reg.register(_make_codelist("alpha"))
        reg.register(_make_codelist("mid"))
        assert reg.list_ids() == ["alpha", "mid", "zebra"]

    def test_register_overwrites(self) -> None:
        """Registering the same list_id again overwrites the previous."""
        reg = CodelistRegistry()
        cl1 = _make_codelist("dup", codes=["x"])
        cl2 = _make_codelist("dup", codes=["y", "z"])
        reg.register(cl1)
        reg.register(cl2)
        result = reg.get_list("dup")
        assert result is cl2
        assert len(result.entries) == 2


# ===========================================================================
# load_defaults
# ===========================================================================


class TestRegistryLoadDefaults:
    """Tests for CodelistRegistry.load_defaults()."""

    @pytest.fixture(scope="class")
    def registry(self) -> CodelistRegistry:
        return CodelistRegistry.load_defaults()

    def test_load_defaults(self, registry: CodelistRegistry) -> None:
        """load_defaults returns a registry with codelists loaded."""
        assert len(registry.list_ids()) >= 6

    def test_load_defaults_has_assurance_goals(self, registry: CodelistRegistry) -> None:
        """assurance-goals list is present."""
        assert "assurance-goals" in registry.list_ids()

    def test_load_defaults_has_measure_types(self, registry: CodelistRegistry) -> None:
        """measure-types list is present."""
        assert "measure-types" in registry.list_ids()

    def test_load_defaults_has_all_six(self, registry: CodelistRegistry) -> None:
        """All 6 migrated codelists are present."""
        expected = {
            "assurance-goals",
            "measure-types",
            "evidence-types",
            "maturity-domains",
            "maturity-levels",
            "mapping-schemes",
        }
        assert expected.issubset(set(registry.list_ids()))


# ===========================================================================
# Registry queries
# ===========================================================================


class TestRegistryQueries:
    """Tests for registry query methods (get_label, resolve_code, etc.)."""

    @pytest.fixture(scope="class")
    def registry(self) -> CodelistRegistry:
        return CodelistRegistry.load_defaults()

    def test_get_label_en(self, registry: CodelistRegistry) -> None:
        """Get English label for a known code."""
        label = registry.get_label("assurance-goals", "transparency", locale="en")
        assert label == "Transparency"

    def test_get_label_de(self, registry: CodelistRegistry) -> None:
        """Get German label for a known code."""
        label = registry.get_label("assurance-goals", "transparency", locale="de")
        assert label == "Transparenz"

    def test_get_label_fallback(self, registry: CodelistRegistry) -> None:
        """Requesting a locale that doesn't exist falls back to English."""
        label = registry.get_label("assurance-goals", "transparency", locale="fr")
        assert label == "Transparency"

    def test_resolve_code(self, registry: CodelistRegistry) -> None:
        """resolve_code returns a CodeEntry object."""
        entry = registry.resolve_code("measure-types", "technical")
        assert isinstance(entry, CodeEntry)
        assert entry.code == "technical"

    def test_resolve_code_not_found(self, registry: CodelistRegistry) -> None:
        """resolve_code raises KeyError for unknown code."""
        with pytest.raises(KeyError, match="not found"):
            registry.resolve_code("measure-types", "nonexistent")

    def test_validate_code_valid(self, registry: CodelistRegistry) -> None:
        """validate_code returns True for a valid code."""
        assert registry.validate_code("assurance-goals", "integrity") is True

    def test_validate_code_invalid(self, registry: CodelistRegistry) -> None:
        """validate_code returns False for a code that does not exist."""
        assert registry.validate_code("assurance-goals", "nonexistent") is False

    def test_validate_code_unknown_list(self, registry: CodelistRegistry) -> None:
        """validate_code returns False (not KeyError) for an unknown list."""
        assert registry.validate_code("no-such-list", "anything") is False

    def test_search(self, registry: CodelistRegistry) -> None:
        """search returns entries matching a substring."""
        results = registry.search("assurance-goals", "abil")
        codes = [e.code for e in results]
        assert "intervenability" in codes
        assert "availability" in codes
        # "transparency" does NOT contain "abil"
        assert "transparency" not in codes

    def test_list_codes(self, registry: CodelistRegistry) -> None:
        """list_codes returns all codes from a codelist."""
        codes = registry.list_codes("maturity-levels")
        assert codes == ["1", "2", "3", "4", "5"]

    def test_get_definition_none(self, registry: CodelistRegistry) -> None:
        """get_definition returns None when no definition is set."""
        defn = registry.get_definition("assurance-goals", "transparency")
        assert defn is None


# ===========================================================================
# Backward compatibility
# ===========================================================================


class TestBackwardCompat:
    """Ensure old vocab API still works alongside the new registry."""

    def test_existing_vocab_still_works(self) -> None:
        """load_default_privacy_vocabs() still loads vocabs (via codelist)."""
        import warnings
        from opengov_oscal_pyprivacy.vocab import load_default_privacy_vocabs, PrivacyVocabs

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            vocabs = load_default_privacy_vocabs()
        assert isinstance(vocabs, PrivacyVocabs)
        assert len(vocabs.assurance_goals.keys) > 0
        assert "transparency" in vocabs.assurance_goals.keys

    def test_registry_covers_vocab_keys(self) -> None:
        """Registry assurance-goals codes are a superset of the old vocab keys."""
        import warnings
        from opengov_oscal_pyprivacy.vocab import load_default_privacy_vocabs

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            vocabs = load_default_privacy_vocabs()
        old_keys = vocabs.assurance_goals.keys

        registry = CodelistRegistry.load_defaults()
        new_codes = set(registry.list_codes("assurance-goals"))

        # New registry should cover all old keys
        assert old_keys.issubset(new_codes)
