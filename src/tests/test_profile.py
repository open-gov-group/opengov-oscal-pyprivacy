"""
Tests for OSCAL Profile model and domain operations (Issue #42).

Covers:
  - Profile / ImportRef / Modify model creation and round-trip
  - Root-unwrapping validator
  - Alias handling for hyphenated OSCAL keys
  - resolve_profile_imports with include/exclude filtering
  - build_profile_from_controls
  - add_profile_import
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Control, Group, OscalMetadata
from opengov_oscal_pycore.models_profile import ImportRef, Modify, Profile

from opengov_oscal_pyprivacy.domain.profile import (
    add_profile_import,
    build_profile_from_controls,
    resolve_profile_imports,
)

DATA_DIR = Path(__file__).parent / "data"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def profile_json() -> dict:
    """Load the test profile JSON fixture."""
    with open(DATA_DIR / "test_profile.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def catalog() -> Catalog:
    """Load the privacy catalog fixture."""
    with open(DATA_DIR / "open_privacy_catalog_risk.json") as f:
        return Catalog(**json.load(f))


@pytest.fixture()
def profile(profile_json: dict) -> Profile:
    """Parse profile from the JSON fixture."""
    return Profile(**profile_json)


# ============================================================================
# Model Tests
# ============================================================================


class TestProfileModel:
    """Profile model parsing, round-trip, and root unwrapping."""

    def test_load_profile_from_json(self, profile: Profile) -> None:
        """Profile loads correctly from the test fixture."""
        assert profile.uuid == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert profile.metadata.title == "Test Privacy Profile"
        assert len(profile.imports) == 1
        assert profile.imports[0].href == "catalogs/privacy.json"

    def test_round_trip(self, profile: Profile) -> None:
        """Dump to dict with aliases, reload, compare."""
        dumped = profile.model_dump(by_alias=True)
        json_str = json.dumps(dumped)
        reloaded = Profile(**json.loads(json_str))
        assert reloaded.uuid == profile.uuid
        assert reloaded.metadata.title == profile.metadata.title
        assert len(reloaded.imports) == len(profile.imports)
        assert reloaded.merge == profile.merge
        assert reloaded.modify is not None
        assert len(reloaded.modify.alters) == len(profile.modify.alters)

    def test_unwrap_root(self, profile_json: dict) -> None:
        """Profile model accepts {'profile': {...}} wrapper."""
        assert "profile" in profile_json
        p = Profile(**profile_json)
        assert p.uuid == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    def test_bare_dict_also_works(self, profile_json: dict) -> None:
        """Profile model also accepts bare dict without 'profile' wrapper."""
        bare = profile_json["profile"]
        p = Profile(**bare)
        assert p.uuid == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    def test_metadata_is_typed(self, profile: Profile) -> None:
        """Metadata is OscalMetadata, not a plain dict."""
        assert isinstance(profile.metadata, OscalMetadata)
        assert profile.metadata.oscal_version == "1.1.2"
        assert profile.metadata.last_modified == "2026-01-01T00:00:00Z"


# ============================================================================
# Alias Tests
# ============================================================================


class TestProfileAliases:
    """Verify that hyphenated OSCAL aliases work correctly."""

    def test_include_controls_alias(self, profile: Profile) -> None:
        """include-controls alias round-trips correctly."""
        dumped = profile.model_dump(by_alias=True)
        imp = dumped["imports"][0]
        assert "include-controls" in imp
        assert "include_controls" not in imp

    def test_exclude_controls_alias(self) -> None:
        """exclude-controls alias serializes correctly."""
        imp = ImportRef(
            href="test.json",
            exclude_controls=[{"with-ids": ["X-01"]}],
        )
        dumped = imp.model_dump(by_alias=True)
        assert "exclude-controls" in dumped
        assert dumped["exclude-controls"] == [{"with-ids": ["X-01"]}]

    def test_set_parameters_alias(self, profile: Profile) -> None:
        """set-parameters alias round-trips correctly."""
        assert profile.modify is not None
        dumped = profile.modify.model_dump(by_alias=True)
        assert "set-parameters" in dumped
        assert "set_parameters" not in dumped

    def test_back_matter_alias(self) -> None:
        """back-matter alias serializes correctly."""
        p = Profile(
            uuid="test-uuid",
            metadata=OscalMetadata(title="T"),
        )
        dumped = p.model_dump(by_alias=True, exclude_none=True)
        # back_matter is None by default, should be excluded
        assert "back-matter" not in dumped
        assert "back_matter" not in dumped


# ============================================================================
# resolve_profile_imports Tests
# ============================================================================


class TestResolveProfileImports:
    """Tests for resolve_profile_imports."""

    def test_resolve_include_controls(self, catalog: Catalog) -> None:
        """Resolved catalog contains only the included controls."""
        profile = Profile(
            uuid="resolve-test",
            metadata=OscalMetadata(title="Resolve Test"),
            imports=[
                ImportRef(
                    href="catalog.json",
                    include_controls=[{"with-ids": ["GOV-01", "GOV-02"]}],
                )
            ],
        )

        def loader(href: str) -> Catalog:
            return catalog

        resolved = resolve_profile_imports(profile, loader)

        all_ids = [c.id for g in resolved.groups for c in g.controls]
        assert "GOV-01" in all_ids
        assert "GOV-02" in all_ids
        assert "GOV-03" not in all_ids
        # Only GOV group should be present (the one containing matched controls)
        assert any(g.id == "GOV" for g in resolved.groups)

    def test_resolve_exclude_controls(self, catalog: Catalog) -> None:
        """Excluded controls are not in the resolved catalog."""
        profile = Profile(
            uuid="exclude-test",
            metadata=OscalMetadata(title="Exclude Test"),
            imports=[
                ImportRef(
                    href="catalog.json",
                    exclude_controls=[{"with-ids": ["GOV-01"]}],
                )
            ],
        )

        def loader(href: str) -> Catalog:
            return catalog

        resolved = resolve_profile_imports(profile, loader)

        all_ids = [c.id for g in resolved.groups for c in g.controls]
        assert "GOV-01" not in all_ids
        assert "GOV-02" in all_ids
        assert "ACC-01" in all_ids  # Controls from other groups still present

    def test_resolve_empty_imports(self) -> None:
        """Profile with no imports yields an empty catalog."""
        profile = Profile(
            uuid="empty-test",
            metadata=OscalMetadata(title="Empty"),
            imports=[],
        )

        resolved = resolve_profile_imports(profile, lambda _: None)  # type: ignore[arg-type]

        assert len(resolved.groups) == 0

    def test_resolve_preserves_metadata(self, catalog: Catalog) -> None:
        """Resolved catalog uses the profile's metadata."""
        meta = OscalMetadata(
            title="My Custom Profile",
            version="2.0.0",
            oscal_version="1.1.2",
        )
        profile = Profile(
            uuid="meta-test",
            metadata=meta,
            imports=[
                ImportRef(
                    href="x.json",
                    include_controls=[{"with-ids": ["GOV-01"]}],
                )
            ],
        )

        resolved = resolve_profile_imports(profile, lambda _: catalog)

        assert resolved.metadata.title == "My Custom Profile"
        assert resolved.metadata.version == "2.0.0"

    def test_resolve_generates_new_uuid(self, catalog: Catalog) -> None:
        """Resolved catalog gets a new UUID different from the profile's."""
        profile = Profile(
            uuid="uuid-test",
            metadata=OscalMetadata(title="UUID Test"),
            imports=[
                ImportRef(
                    href="x.json",
                    include_controls=[{"with-ids": ["GOV-01"]}],
                )
            ],
        )

        resolved = resolve_profile_imports(profile, lambda _: catalog)

        assert resolved.uuid != profile.uuid
        assert len(resolved.uuid) > 0


# ============================================================================
# build_profile_from_controls Tests
# ============================================================================


class TestBuildProfileFromControls:
    """Tests for build_profile_from_controls."""

    def test_build_basic(self, catalog: Catalog) -> None:
        """Build a profile selecting specific controls."""
        profile = build_profile_from_controls(
            catalog,
            ["GOV-01", "ACC-01"],
            title="My Custom Profile",
            version="1.0.0",
        )

        assert profile.metadata.title == "My Custom Profile"
        assert profile.metadata.version == "1.0.0"
        assert profile.metadata.oscal_version == "1.1.2"
        assert len(profile.imports) == 1
        assert profile.imports[0].href == "#"

        with_ids = profile.imports[0].include_controls[0]["with-ids"]
        assert "GOV-01" in with_ids
        assert "ACC-01" in with_ids

    def test_build_deterministic_uuid(self, catalog: Catalog) -> None:
        """Same title produces same UUID."""
        p1 = build_profile_from_controls(
            catalog, ["GOV-01"], title="Deterministic", version="1.0"
        )
        p2 = build_profile_from_controls(
            catalog, ["GOV-02"], title="Deterministic", version="2.0"
        )
        assert p1.uuid == p2.uuid  # same title -> same uuid

    def test_build_different_title_different_uuid(self, catalog: Catalog) -> None:
        """Different titles produce different UUIDs."""
        p1 = build_profile_from_controls(
            catalog, ["GOV-01"], title="Title A", version="1.0"
        )
        p2 = build_profile_from_controls(
            catalog, ["GOV-01"], title="Title B", version="1.0"
        )
        assert p1.uuid != p2.uuid


# ============================================================================
# add_profile_import Tests
# ============================================================================


class TestAddProfileImport:
    """Tests for add_profile_import."""

    def test_add_import(self, profile: Profile) -> None:
        """Adding an import appends to profile.imports."""
        original_count = len(profile.imports)
        add_profile_import(profile, "other-catalog.json", ["LAW-01", "LAW-02"])
        assert len(profile.imports) == original_count + 1

        new_imp = profile.imports[-1]
        assert new_imp.href == "other-catalog.json"
        ids = new_imp.include_controls[0]["with-ids"]
        assert "LAW-01" in ids
        assert "LAW-02" in ids

    def test_add_multiple_imports(self) -> None:
        """Multiple imports can be added sequentially."""
        profile = Profile(
            uuid="multi-test",
            metadata=OscalMetadata(title="Multi"),
            imports=[],
        )
        add_profile_import(profile, "a.json", ["A-01"])
        add_profile_import(profile, "b.json", ["B-01"])
        assert len(profile.imports) == 2
        assert profile.imports[0].href == "a.json"
        assert profile.imports[1].href == "b.json"


# ============================================================================
# Extra-field Preservation (round-trip safety)
# ============================================================================


class TestExtraFieldPreservation:
    """OscalBaseModel extra='allow' preserves unknown fields."""

    def test_profile_extra_fields(self) -> None:
        """Unknown fields on Profile survive round-trip."""
        data = {
            "uuid": "extra-test",
            "metadata": {"title": "Extra Test"},
            "imports": [],
            "custom-extension": {"foo": "bar"},
        }
        p = Profile(**data)
        dumped = p.model_dump(by_alias=True)
        assert dumped["custom-extension"] == {"foo": "bar"}

    def test_import_ref_extra_fields(self) -> None:
        """Unknown fields on ImportRef survive round-trip."""
        data = {
            "href": "test.json",
            "include-controls": [],
            "custom-flag": True,
        }
        imp = ImportRef(**data)
        dumped = imp.model_dump(by_alias=True)
        assert dumped["custom-flag"] is True
