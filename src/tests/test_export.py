"""
Tests for OSCAL export helpers (Issue #55).

Covers:
  - to_dict with alias handling, root key wrapping, exclude_none, by_alias
  - to_json with indentation, ensure_ascii, root key
  - Roundtrip serialisation for Catalog, Profile, SSP, ComponentDefinition
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog
from opengov_oscal_pycore.models_profile import Profile
from opengov_oscal_pycore.models_ssp import SystemSecurityPlan
from opengov_oscal_pycore.models_component import ComponentDefinition
from opengov_oscal_pycore.export import to_dict, to_json

DATA_DIR = Path(__file__).parent / "data"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def catalog() -> Catalog:
    """Load the privacy catalog fixture."""
    with open(DATA_DIR / "open_privacy_catalog_risk.json") as f:
        return Catalog(**json.load(f))


@pytest.fixture(scope="module")
def catalog_raw() -> dict:
    """Load the raw catalog JSON dict (for comparison)."""
    with open(DATA_DIR / "open_privacy_catalog_risk.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def profile() -> Profile:
    """Load the test profile fixture."""
    with open(DATA_DIR / "test_profile.json") as f:
        return Profile(**json.load(f))


@pytest.fixture(scope="module")
def ssp() -> SystemSecurityPlan:
    """Load the test SSP fixture."""
    with open(DATA_DIR / "test_ssp.json") as f:
        return SystemSecurityPlan(**json.load(f))


@pytest.fixture(scope="module")
def component_def() -> ComponentDefinition:
    """Load the test component definition fixture."""
    with open(DATA_DIR / "test_component_definition.json") as f:
        return ComponentDefinition(**json.load(f))


# ============================================================================
# to_dict tests
# ============================================================================


class TestToDict:
    """Tests for the to_dict export helper."""

    def test_catalog_alias_keys(self, catalog: Catalog) -> None:
        """to_dict uses OSCAL alias keys (e.g. 'back-matter' not 'back_matter')."""
        data = to_dict(catalog)
        # Metadata must use hyphenated aliases
        assert "last-modified" in data["metadata"]
        assert "oscal-version" in data["metadata"]
        assert "last_modified" not in data["metadata"]
        assert "oscal_version" not in data["metadata"]

    def test_with_root_key(self, catalog: Catalog) -> None:
        """to_dict wraps output in root key when oscal_root_key is set."""
        data = to_dict(catalog, oscal_root_key="catalog")
        assert "catalog" in data
        assert "uuid" in data["catalog"]
        assert "metadata" in data["catalog"]

    def test_without_root_key(self, catalog: Catalog) -> None:
        """to_dict returns flat dict when oscal_root_key is not set."""
        data = to_dict(catalog)
        assert "catalog" not in data
        assert "uuid" in data
        assert "metadata" in data

    def test_exclude_none_default(self, catalog: Catalog) -> None:
        """to_dict excludes None fields by default."""
        data = to_dict(catalog)
        data_json = json.dumps(data)
        assert "null" not in data_json

    def test_include_none(self, catalog: Catalog) -> None:
        """to_dict keeps None fields when exclude_none=False."""
        data = to_dict(catalog, exclude_none=False)
        # back-matter or other optional fields should appear even if None
        # At minimum, the output should contain some None values
        data_json = json.dumps(data)
        # The catalog fixture has back-matter set, so let's check another model
        # We construct a minimal catalog with a None back_matter
        from opengov_oscal_pycore.models import OscalMetadata
        minimal = Catalog(
            uuid="test-uuid",
            metadata=OscalMetadata(title="Test"),
            back_matter=None,
        )
        minimal_data = to_dict(minimal, exclude_none=False)
        assert "back-matter" in minimal_data
        assert minimal_data["back-matter"] is None

    def test_by_alias_false(self, catalog: Catalog) -> None:
        """to_dict uses Python field names when by_alias=False."""
        data = to_dict(catalog, by_alias=False)
        # Python names should appear instead of OSCAL aliases
        assert "last_modified" in data["metadata"]
        assert "oscal_version" in data["metadata"]
        assert "last-modified" not in data["metadata"]
        assert "oscal-version" not in data["metadata"]


# ============================================================================
# to_json tests
# ============================================================================


class TestToJson:
    """Tests for the to_json export helper."""

    def test_valid_json(self, catalog: Catalog) -> None:
        """to_json produces a valid, parseable JSON string."""
        text = to_json(catalog)
        parsed = json.loads(text)
        assert isinstance(parsed, dict)
        assert "uuid" in parsed

    def test_with_root_key(self, catalog: Catalog) -> None:
        """to_json wraps output in root key."""
        text = to_json(catalog, oscal_root_key="catalog")
        parsed = json.loads(text)
        assert "catalog" in parsed
        assert "uuid" in parsed["catalog"]

    def test_indent(self, catalog: Catalog) -> None:
        """to_json respects indent parameter."""
        text_2 = to_json(catalog, indent=2)
        text_4 = to_json(catalog, indent=4)
        # 4-space indent produces longer output than 2-space
        assert len(text_4) > len(text_2)
        # Verify actual indentation in output
        assert "\n    " in text_4  # 4-space indent present
        assert "\n  " in text_2   # 2-space indent present

    def test_ensure_ascii(self, catalog: Catalog) -> None:
        """to_json escapes non-ASCII when ensure_ascii=True."""
        # The catalog fixture contains German text (e.g. "DSGVO", umlauts)
        text_unicode = to_json(catalog, ensure_ascii=False)
        text_ascii = to_json(catalog, ensure_ascii=True)
        # If the fixture has non-ASCII chars, the ascii version will be longer
        # due to \\uXXXX escapes. Both must be valid JSON.
        json.loads(text_unicode)
        json.loads(text_ascii)
        # Check that non-ASCII chars present in unicode version
        # are escaped in ascii version
        has_non_ascii = any(ord(c) > 127 for c in text_unicode)
        if has_non_ascii:
            assert len(text_ascii) > len(text_unicode)
            # ASCII version should contain no high-byte chars
            assert all(ord(c) < 128 for c in text_ascii)


# ============================================================================
# Roundtrip tests
# ============================================================================


class TestRoundtrip:
    """Roundtrip tests: load -> to_json -> parse -> model_validate -> compare."""

    def test_roundtrip_catalog(self, catalog: Catalog) -> None:
        """Catalog survives a full serialisation roundtrip."""
        text = to_json(catalog, oscal_root_key="catalog")
        parsed = json.loads(text)
        restored = Catalog(**parsed)
        assert restored.uuid == catalog.uuid
        assert restored.metadata.title == catalog.metadata.title
        assert restored.metadata.version == catalog.metadata.version
        # Deep equality via model_dump
        assert to_dict(restored) == to_dict(catalog)

    def test_roundtrip_profile(self, profile: Profile) -> None:
        """Profile survives a full serialisation roundtrip."""
        text = to_json(profile, oscal_root_key="profile")
        parsed = json.loads(text)
        restored = Profile(**parsed)
        assert restored.uuid == profile.uuid
        assert restored.metadata.title == profile.metadata.title
        assert to_dict(restored) == to_dict(profile)

    def test_roundtrip_ssp(self, ssp: SystemSecurityPlan) -> None:
        """SystemSecurityPlan survives a full serialisation roundtrip."""
        text = to_json(ssp, oscal_root_key="system-security-plan")
        parsed = json.loads(text)
        restored = SystemSecurityPlan(**parsed)
        assert restored.uuid == ssp.uuid
        assert restored.metadata.title == ssp.metadata.title
        assert to_dict(restored) == to_dict(ssp)

    def test_roundtrip_component_definition(
        self, component_def: ComponentDefinition
    ) -> None:
        """ComponentDefinition survives a full serialisation roundtrip."""
        text = to_json(component_def, oscal_root_key="component-definition")
        parsed = json.loads(text)
        restored = ComponentDefinition(**parsed)
        assert restored.uuid == component_def.uuid
        assert restored.metadata.title == component_def.metadata.title
        assert to_dict(restored) == to_dict(component_def)
