"""Tests for the OSCAL diff module and DiffService."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Control, Group, OscalMetadata, Property
from opengov_oscal_pycore.diff import (
    DiffChange,
    DiffSummary,
    OscalDiffResult,
    diff_oscal,
    diff_catalogs,
    diff_controls,
    _normalize_deepdiff_path,
    _diff_simple,
)
from opengov_oscal_pyprivacy.services.diff_service import OscalDiffService


FIXTURE = Path(__file__).parent / "data" / "open_privacy_catalog_risk.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _make_catalog(**overrides) -> Catalog:
    defaults = {
        "uuid": "test-uuid",
        "metadata": OscalMetadata.model_validate(
            {"title": "Test", "version": "1.0", "oscal-version": "1.1.2"}
        ),
        "groups": [
            Group(
                id="g1",
                title="Group 1",
                controls=[
                    Control(id="c1", title="Control 1"),
                    Control(id="c2", title="Control 2"),
                ],
            )
        ],
    }
    defaults.update(overrides)
    return Catalog.model_validate(defaults)


# ---------------------------------------------------------------------------
# Core diff_oscal tests
# ---------------------------------------------------------------------------


class TestDiffOscalBasic:
    """Tests for diff_oscal with simple dicts."""

    def test_identical_dicts_no_changes(self):
        d = {"a": 1, "b": "hello"}
        result = diff_oscal(d, d.copy())
        assert result.summary.added == 0
        assert result.summary.changed == 0
        assert result.summary.removed == 0
        assert len(result.changes) == 0

    def test_changed_value_detected(self):
        old = {"title": "Old Title"}
        new = {"title": "New Title"}
        result = diff_oscal(old, new)
        assert result.summary.changed == 1
        assert result.summary.added == 0
        assert result.summary.removed == 0
        changed = [c for c in result.changes if c.change_type == "changed"]
        assert len(changed) == 1
        assert changed[0].old_value == "Old Title"
        assert changed[0].new_value == "New Title"

    def test_added_key_detected(self):
        old = {"a": 1}
        new = {"a": 1, "b": 2}
        result = diff_oscal(old, new)
        assert result.summary.added == 1
        added = [c for c in result.changes if c.change_type == "added"]
        assert len(added) == 1
        assert added[0].new_value == 2

    def test_removed_key_detected(self):
        old = {"a": 1, "b": 2}
        new = {"a": 1}
        result = diff_oscal(old, new)
        assert result.summary.removed == 1
        removed = [c for c in result.changes if c.change_type == "removed"]
        assert len(removed) == 1
        assert removed[0].old_value == 2

    def test_nested_dict_changes(self):
        old = {"metadata": {"title": "A", "version": "1.0"}}
        new = {"metadata": {"title": "B", "version": "1.0"}}
        result = diff_oscal(old, new)
        assert result.summary.changed == 1
        assert any("title" in c.path for c in result.changes)

    def test_list_item_added(self):
        old = {"items": [1, 2]}
        new = {"items": [1, 2, 3]}
        result = diff_oscal(old, new)
        assert result.summary.added == 1
        added = [c for c in result.changes if c.change_type == "added"]
        assert len(added) == 1
        assert added[0].new_value == 3

    def test_list_item_removed(self):
        old = {"items": [1, 2, 3]}
        new = {"items": [1, 2]}
        result = diff_oscal(old, new)
        assert result.summary.removed == 1
        removed = [c for c in result.changes if c.change_type == "removed"]
        assert len(removed) == 1
        assert removed[0].old_value == 3


class TestIgnorePaths:
    """Tests for the ignore_paths parameter."""

    def test_ignore_paths_skips_changes(self):
        old = {"metadata": {"title": "A", "last-modified": "2024-01-01"}}
        new = {"metadata": {"title": "A", "last-modified": "2024-06-15"}}
        result = diff_oscal(old, new, ignore_paths=["metadata.last-modified"])
        assert result.summary.changed == 0
        assert len(result.changes) == 0

    def test_ignore_paths_does_not_affect_other_changes(self):
        old = {"metadata": {"title": "A", "last-modified": "2024-01-01"}}
        new = {"metadata": {"title": "B", "last-modified": "2024-06-15"}}
        result = diff_oscal(old, new, ignore_paths=["metadata.last-modified"])
        assert result.summary.changed == 1
        # Only the title change should be reported
        assert any("title" in c.path for c in result.changes)
        assert not any("last-modified" in c.path for c in result.changes)


class TestDiffSummaryCounts:
    """Tests for DiffSummary counting."""

    def test_summary_counts_correct(self):
        old = {"a": 1, "b": 2, "c": 3}
        new = {"a": 10, "c": 3, "d": 4}
        result = diff_oscal(old, new)
        assert result.summary.changed == 1  # a: 1 -> 10
        assert result.summary.removed == 1  # b removed
        assert result.summary.added == 1  # d added
        assert len(result.changes) == 3


# ---------------------------------------------------------------------------
# Catalog and Control diffs
# ---------------------------------------------------------------------------


class TestDiffCatalogs:
    """Tests for diff_catalogs with Pydantic models."""

    def test_identical_catalogs_no_changes(self):
        cat = _make_catalog()
        result = diff_catalogs(cat, cat)
        assert result.summary.added == 0
        assert result.summary.changed == 0
        assert result.summary.removed == 0

    def test_catalog_title_change(self):
        old = _make_catalog()
        new_meta = OscalMetadata.model_validate(
            {"title": "Changed Title", "version": "1.0", "oscal-version": "1.1.2"}
        )
        new = _make_catalog(metadata=new_meta)
        result = diff_catalogs(old, new)
        assert result.summary.changed >= 1
        assert any("title" in c.path for c in result.changes)

    def test_catalog_with_fixture(self):
        """Load the real fixture, modify a control title, and verify the diff."""
        data = _load_fixture()
        cat_old = Catalog.model_validate(data)
        cat_new = Catalog.model_validate(data)
        # Modify the title of the first control in the first group
        if cat_new.groups and cat_new.groups[0].controls:
            cat_new.groups[0].controls[0].title = "Modified Title"
        result = diff_catalogs(cat_old, cat_new)
        assert result.summary.changed >= 1
        assert any("title" in c.path for c in result.changes)


class TestDiffControls:
    """Tests for diff_controls with Pydantic models."""

    def test_control_prop_added(self):
        old = Control(id="c1", title="Control 1")
        new = Control(
            id="c1",
            title="Control 1",
            props=[Property(name="status", value="active")],
        )
        result = diff_controls(old, new)
        assert result.summary.added >= 1

    def test_control_title_changed(self):
        old = Control(id="c1", title="Old Title")
        new = Control(id="c1", title="New Title")
        result = diff_controls(old, new)
        assert result.summary.changed >= 1
        changed = [c for c in result.changes if c.change_type == "changed"]
        assert any(c.old_value == "Old Title" for c in changed)


# ---------------------------------------------------------------------------
# Path normalization
# ---------------------------------------------------------------------------


class TestNormalizeDeepDiffPath:
    """Tests for _normalize_deepdiff_path."""

    def test_simple_key(self):
        assert _normalize_deepdiff_path("root['title']") == "title"

    def test_nested_keys(self):
        assert _normalize_deepdiff_path("root['metadata']['title']") == "metadata.title"

    def test_array_index(self):
        assert _normalize_deepdiff_path("root['groups'][0]") == "groups[0]"

    def test_complex_path(self):
        path = "root['groups'][0]['controls'][1]['props'][2]['value']"
        expected = "groups[0].controls[1].props[2].value"
        assert _normalize_deepdiff_path(path) == expected

    def test_root_only(self):
        assert _normalize_deepdiff_path("root") == ""


# ---------------------------------------------------------------------------
# Fallback (_diff_simple) direct tests
# ---------------------------------------------------------------------------


class TestDiffSimpleFallback:
    """Test the simple fallback diff directly."""

    def test_simple_identical(self):
        d = {"x": 1}
        result = _diff_simple(d, d.copy())
        assert len(result.changes) == 0

    def test_simple_change(self):
        result = _diff_simple({"x": 1}, {"x": 2})
        assert result.summary.changed == 1

    def test_simple_nested(self):
        old = {"a": {"b": {"c": 1}}}
        new = {"a": {"b": {"c": 2}}}
        result = _diff_simple(old, new)
        assert result.summary.changed == 1
        assert result.changes[0].path == "a.b.c"

    def test_simple_ignore_paths(self):
        old = {"m": {"ts": "old"}}
        new = {"m": {"ts": "new"}}
        result = _diff_simple(old, new, ignore_paths=["m.ts"])
        assert len(result.changes) == 0


# ---------------------------------------------------------------------------
# DiffService tests
# ---------------------------------------------------------------------------


class TestOscalDiffService:
    """Tests for the high-level OscalDiffService."""

    def test_service_diff_catalogs(self):
        svc = OscalDiffService()
        old = _make_catalog()
        new_meta = OscalMetadata.model_validate(
            {"title": "Updated", "version": "1.0", "oscal-version": "1.1.2"}
        )
        new = _make_catalog(metadata=new_meta)
        result = svc.diff_catalogs(old, new)
        assert isinstance(result, OscalDiffResult)
        assert result.summary.changed >= 1

    def test_service_diff_controls(self):
        svc = OscalDiffService()
        old = Control(id="c1", title="A")
        new = Control(id="c1", title="B")
        result = svc.diff_controls(old, new)
        assert result.summary.changed >= 1

    def test_service_format_diff_summary(self):
        svc = OscalDiffService()
        result = OscalDiffResult(
            summary=DiffSummary(added=1, changed=2, removed=0),
            changes=[
                DiffChange(path="metadata.title", change_type="changed",
                           old_value="A", new_value="B"),
                DiffChange(path="metadata.version", change_type="changed",
                           old_value="1.0", new_value="2.0"),
                DiffChange(path="groups[0].controls[1]", change_type="added",
                           new_value={"id": "c3"}),
            ],
        )
        text = svc.format_diff_summary(result)
        assert "Changes: +1 ~2 -0" in text
        assert "~ metadata.title" in text
        assert "old: A" in text
        assert "new: B" in text
        assert "+ groups[0].controls[1]" in text

    def test_service_diff_files(self, tmp_path):
        old_data = {"catalog": {"uuid": "u1", "metadata": {"title": "A"}}}
        new_data = {"catalog": {"uuid": "u1", "metadata": {"title": "B"}}}
        old_file = tmp_path / "old.json"
        new_file = tmp_path / "new.json"
        old_file.write_text(json.dumps(old_data), encoding="utf-8")
        new_file.write_text(json.dumps(new_data), encoding="utf-8")
        svc = OscalDiffService()
        result = svc.diff_files(old_file, new_file)
        assert result.summary.changed == 1

    def test_service_with_ignore_paths(self):
        svc = OscalDiffService(ignore_paths=["metadata.last-modified"])
        old = {"metadata": {"title": "A", "last-modified": "2024-01-01"}}
        new = {"metadata": {"title": "A", "last-modified": "2024-12-31"}}
        result = diff_oscal(old, new, ignore_paths=svc._ignore_paths)
        assert len(result.changes) == 0


# ---------------------------------------------------------------------------
# Export verification
# ---------------------------------------------------------------------------


class TestDiffExports:
    """Verify diff types are importable from opengov_oscal_pycore."""

    def test_pycore_exports_diff_types(self):
        import opengov_oscal_pycore as pycore

        assert hasattr(pycore, "DiffChange")
        assert hasattr(pycore, "DiffSummary")
        assert hasattr(pycore, "OscalDiffResult")
        assert hasattr(pycore, "diff_oscal")
        assert hasattr(pycore, "diff_catalogs")
        assert hasattr(pycore, "diff_controls")

    def test_diff_types_in_all(self):
        import opengov_oscal_pycore as pycore

        for name in [
            "DiffChange", "DiffSummary", "OscalDiffResult",
            "diff_oscal", "diff_catalogs", "diff_controls",
        ]:
            assert name in pycore.__all__, f"{name} not in pycore.__all__"
