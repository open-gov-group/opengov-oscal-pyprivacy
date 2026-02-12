"""
Tests for opengov_oscal_pycore infrastructure modules: repo.py and versioning.py
"""

from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Group, Control
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
            "oscal_version": "1.1.2",
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
        assert cat.metadata["title"] == "OSCAL-Datenschutzkatalog nach DSGVO"
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
        assert reloaded.metadata["title"] == original.metadata["title"]
        assert reloaded.metadata["version"] == original.metadata["version"]
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
        metadata = {"title": "T", "version": "0.1"}
        touch_metadata(metadata)

        assert "last_modified" in metadata
        ts = metadata["last_modified"]
        # Must look like an ISO 8601 datetime (starts with a year, contains 'T')
        assert isinstance(ts, str)
        assert "T" in ts
        # Should contain UTC offset info ('+00:00' or 'Z')
        assert "+00:00" in ts or "Z" in ts

    def test_touch_metadata_overwrites_existing(self):
        """Calling touch_metadata again overwrites the previous value."""
        metadata = {"last_modified": "2000-01-01T00:00:00+00:00"}
        touch_metadata(metadata)

        assert metadata["last_modified"] != "2000-01-01T00:00:00+00:00"


class TestBumpVersion:
    """Tests for bump_version()."""

    def test_bump_version(self):
        """bump_version sets the version string and updates last_modified."""
        metadata = {"title": "T", "version": "0.1"}
        bump_version(metadata, "2.0.0")

        assert metadata["version"] == "2.0.0"
        assert "last_modified" in metadata

    def test_bump_version_preserves_other_metadata(self):
        """bump_version must not discard other metadata fields (round-trip safety)."""
        metadata = {
            "title": "Test Catalog",
            "version": "1.0.0",
            "oscal_version": "1.1.2",
            "custom_field": "should survive",
        }
        bump_version(metadata, "1.1.0")

        assert metadata["version"] == "1.1.0"
        assert metadata["title"] == "Test Catalog"
        assert metadata["oscal_version"] == "1.1.2"
        assert metadata["custom_field"] == "should survive"
        assert "last_modified" in metadata
