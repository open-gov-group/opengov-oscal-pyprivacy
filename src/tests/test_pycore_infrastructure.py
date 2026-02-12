"""
Tests for opengov_oscal_pycore infrastructure modules: repo.py and versioning.py
"""

from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Group, Control, OscalMetadata, Role, Party
from opengov_oscal_pycore.repo import OscalRepository
from opengov_oscal_pycore.versioning import touch_metadata, bump_version

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_DATA_DIR = Path(__file__).parent / "data"
FIXTURE_FILE = TEST_DATA_DIR / "open_privacy_catalog_risk.json"


def _minimal_catalog() -> Catalog:
    return Catalog(
        uuid="infra-test-uuid",
        metadata={
            "title": "Infra Test Catalog",
            "version": "1.0.0",
            "oscal-version": "1.1.2",
        },
        groups=[
            Group(id="g1", title="Group 1", controls=[
                Control(id="c1", title="Control 1"),
            ]),
        ],
    )


# ---------------------------------------------------------------------------
# OscalRepository tests
# ---------------------------------------------------------------------------

class TestOscalRepositoryLoad:
    """Tests for OscalRepository.load()."""

    def test_repo_load_valid_catalog(self):
        """Load the test fixture via OscalRepository and verify basic fields."""
        repo = OscalRepository[Catalog](TEST_DATA_DIR)
        cat = repo.load("open_privacy_catalog_risk.json", Catalog)

        assert isinstance(cat, Catalog)
        assert cat.uuid == "0b431870-7f9d-440f-ac7d-d42bb92e3acb"
        assert cat.metadata.title == "OSCAL-Datenschutzkatalog nach DSGVO"
        assert len(cat.groups) > 0

    def test_repo_load_nonexistent_raises(self, tmp_path: Path):
        """Loading a non-existent file must raise an appropriate error."""
        repo = OscalRepository[Catalog](tmp_path)
        with pytest.raises((FileNotFoundError, OSError)):
            repo.load("does_not_exist.json", Catalog)


class TestOscalRepositorySave:
    """Tests for OscalRepository.save() round-trip."""

    def test_repo_save_and_reload(self, tmp_path: Path):
        """Save a catalog to tmp_path, reload it, and verify contents match."""
        repo = OscalRepository[Catalog](tmp_path)
        original = _minimal_catalog()

        repo.save("test_catalog.json", original)

        # File should exist on disk
        saved_path = tmp_path / "test_catalog.json"
        assert saved_path.exists()

        # Reload and verify
        reloaded = repo.load("test_catalog.json", Catalog)
        assert reloaded.uuid == original.uuid
        assert reloaded.metadata.title == original.metadata.title
        assert reloaded.metadata.version == original.metadata.version
        assert len(reloaded.groups) == 1
        assert reloaded.groups[0].id == "g1"
        assert len(reloaded.groups[0].controls) == 1
        assert reloaded.groups[0].controls[0].id == "c1"

    def test_repo_save_creates_subdirectories(self, tmp_path: Path):
        """Save to a nested path; intermediate directories are auto-created."""
        repo = OscalRepository[Catalog](tmp_path)
        cat = _minimal_catalog()

        repo.save("sub/dir/catalog.json", cat)
        assert (tmp_path / "sub" / "dir" / "catalog.json").exists()


class TestOscalRepositoryResolve:
    """Tests for OscalRepository.resolve()."""

    def test_repo_resolve_path(self, tmp_path: Path):
        """resolve() joins the base path with the relative path."""
        repo = OscalRepository[Catalog](tmp_path)
        result = repo.resolve("catalogs/privacy.json")

        assert result == tmp_path / "catalogs" / "privacy.json"

    def test_repo_resolve_path_object(self, tmp_path: Path):
        """resolve() also accepts a Path object."""
        repo = OscalRepository[Catalog](tmp_path)
        result = repo.resolve(Path("catalogs") / "privacy.json")

        assert result == tmp_path / "catalogs" / "privacy.json"


# ---------------------------------------------------------------------------
# versioning.py tests
# ---------------------------------------------------------------------------

class TestTouchMetadata:
    """Tests for touch_metadata()."""

    def test_touch_metadata_sets_last_modified(self):
        """touch_metadata sets last_modified to an ISO datetime string."""
        metadata = OscalMetadata(title="T", version="0.1")
        touch_metadata(metadata)

        assert metadata.last_modified is not None
        ts = metadata.last_modified
        # Must look like an ISO 8601 datetime (starts with a year, contains 'T')
        assert isinstance(ts, str)
        assert "T" in ts
        # Should contain UTC offset info ('+00:00' or 'Z')
        assert "+00:00" in ts or "Z" in ts

    def test_touch_metadata_overwrites_existing(self):
        """Calling touch_metadata again overwrites the previous value."""
        metadata = OscalMetadata(title="T", last_modified="2000-01-01T00:00:00+00:00")
        touch_metadata(metadata)

        assert metadata.last_modified != "2000-01-01T00:00:00+00:00"


class TestBumpVersion:
    """Tests for bump_version()."""

    def test_bump_version(self):
        """bump_version sets the version string and updates last_modified."""
        metadata = OscalMetadata(title="T", version="0.1")
        bump_version(metadata, "2.0.0")

        assert metadata.version == "2.0.0"
        assert metadata.last_modified is not None

    def test_bump_version_preserves_other_metadata(self):
        """bump_version must not discard other metadata fields (round-trip safety)."""
        metadata = OscalMetadata(
            title="Test Catalog",
            version="1.0.0",
            oscal_version="1.1.2",
            custom_field="should survive",
        )
        bump_version(metadata, "1.1.0")

        assert metadata.version == "1.1.0"
        assert metadata.title == "Test Catalog"
        assert metadata.oscal_version == "1.1.2"
        assert metadata.custom_field == "should survive"
        assert metadata.last_modified is not None


# ---------------------------------------------------------------------------
# OscalMetadata model tests
# ---------------------------------------------------------------------------

class TestOscalMetadataModel:
    """Tests for OscalMetadata, Role, and Party models."""

    def test_fixture_parses_metadata_fields(self):
        """Loading the fixture correctly parses core metadata fields."""
        repo = OscalRepository[Catalog](TEST_DATA_DIR)
        cat = repo.load("open_privacy_catalog_risk.json", Catalog)

        assert cat.metadata.title == "OSCAL-Datenschutzkatalog nach DSGVO"
        assert cat.metadata.version == "0.5.0"
        assert cat.metadata.oscal_version == "1.1.2"
        assert cat.metadata.last_modified == "2025-11-27T00:00:00Z"

    def test_fixture_roles_are_role_objects(self):
        """metadata.roles is a list of Role objects."""
        repo = OscalRepository[Catalog](TEST_DATA_DIR)
        cat = repo.load("open_privacy_catalog_risk.json", Catalog)

        assert isinstance(cat.metadata.roles, list)
        assert len(cat.metadata.roles) >= 2
        assert all(isinstance(r, Role) for r in cat.metadata.roles)
        # Verify specific role data
        owner_roles = [r for r in cat.metadata.roles if r.id == "owner"]
        assert len(owner_roles) == 1
        assert owner_roles[0].title == "Katalogverantwortliche Stelle"

    def test_fixture_parties_are_party_objects(self):
        """metadata.parties is a list of Party objects."""
        repo = OscalRepository[Catalog](TEST_DATA_DIR)
        cat = repo.load("open_privacy_catalog_risk.json", Catalog)

        assert isinstance(cat.metadata.parties, list)
        assert len(cat.metadata.parties) >= 1
        assert all(isinstance(p, Party) for p in cat.metadata.parties)
        # Verify specific party data
        assert cat.metadata.parties[0].uuid == "f4bbcac7-5491-4314-a1d7-63c4166b43dc"
        assert cat.metadata.parties[0].type == "organization"
        assert cat.metadata.parties[0].name == "Beispielorganisation"

    def test_alias_roundtrip_by_alias(self):
        """model_dump(by_alias=True) produces hyphenated keys."""
        metadata = OscalMetadata(
            title="Test",
            last_modified="2025-01-01T00:00:00Z",
            oscal_version="1.1.2",
        )
        dumped = metadata.model_dump(by_alias=True, exclude_none=True)

        assert "last-modified" in dumped
        assert "oscal-version" in dumped
        # Python attribute names should NOT appear as keys
        assert "last_modified" not in dumped
        assert "oscal_version" not in dumped

    def test_extra_fields_survive_roundtrip(self):
        """Extra fields in metadata survive load/dump (extra='allow')."""
        metadata = OscalMetadata.model_validate({
            "title": "Test",
            "version": "1.0",
            "custom-extension": "should survive",
            "another_field": 42,
        })

        # Extra fields accessible via model_extra
        assert metadata.model_extra["custom-extension"] == "should survive"
        assert metadata.model_extra["another_field"] == 42

        # Round-trip through dump/validate
        dumped = metadata.model_dump(by_alias=True, exclude_none=True)
        assert dumped["custom-extension"] == "should survive"
        assert dumped["another_field"] == 42

        reloaded = OscalMetadata.model_validate(dumped)
        assert reloaded.title == "Test"
        assert reloaded.model_extra["custom-extension"] == "should survive"
        assert reloaded.model_extra["another_field"] == 42
