"""Tests for BackMatter models and CRUD."""
import json
from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, BackMatter, Resource, Rlink
from opengov_oscal_pycore.crud.back_matter import find_resource, add_resource, remove_resource

TEST_DATA_DIR = Path(__file__).parent / "data"
FIXTURE_FILE = TEST_DATA_DIR / "open_privacy_catalog_risk.json"


class TestBackMatterModels:
    """Tests for BackMatter/Resource/Rlink Pydantic models."""

    def test_fixture_has_back_matter(self):
        data = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
        cat = Catalog.model_validate(data)
        assert cat.back_matter is not None
        assert len(cat.back_matter.resources) == 3

    def test_resource_fields(self):
        data = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
        cat = Catalog.model_validate(data)
        sdm = cat.back_matter.resources[0]
        assert sdm.title == "Standard-Datenschutzmodell (SDM)"
        assert len(sdm.rlinks) == 1
        assert "datenschutzkonferenz" in sdm.rlinks[0].href

    def test_back_matter_roundtrip(self, tmp_path):
        """BackMatter survives save/load via OscalRepository."""
        from opengov_oscal_pycore.repo import OscalRepository
        data = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
        cat = Catalog.model_validate(data)

        repo = OscalRepository[Catalog](tmp_path)
        repo.save("test.json", cat)
        reloaded = repo.load("test.json", Catalog)

        assert reloaded.back_matter is not None
        assert len(reloaded.back_matter.resources) == 3

    def test_catalog_without_back_matter(self):
        """Catalog without back-matter should have None."""
        cat = Catalog.model_validate({
            "uuid": "test-uuid",
            "metadata": {"title": "Test"}
        })
        assert cat.back_matter is None


class TestBackMatterCrud:
    """Tests for back_matter CRUD functions."""

    def _make_back_matter(self):
        return BackMatter(resources=[
            Resource(uuid="res-1", title="Res 1"),
            Resource(uuid="res-2", title="Res 2"),
        ])

    def test_find_resource_found(self):
        bm = self._make_back_matter()
        r = find_resource(bm, "res-1")
        assert r is not None
        assert r.title == "Res 1"

    def test_find_resource_not_found(self):
        bm = self._make_back_matter()
        assert find_resource(bm, "nonexistent") is None

    def test_add_resource(self):
        bm = self._make_back_matter()
        add_resource(bm, Resource(uuid="res-3", title="Res 3"))
        assert len(bm.resources) == 3
        assert find_resource(bm, "res-3") is not None

    def test_add_resource_duplicate_raises(self):
        bm = self._make_back_matter()
        with pytest.raises(ValueError):
            add_resource(bm, Resource(uuid="res-1", title="Duplicate"))

    def test_remove_resource(self):
        bm = self._make_back_matter()
        assert remove_resource(bm, "res-1") is True
        assert len(bm.resources) == 1
        assert find_resource(bm, "res-1") is None

    def test_remove_resource_not_found(self):
        bm = self._make_back_matter()
        assert remove_resource(bm, "nonexistent") is False
        assert len(bm.resources) == 2
