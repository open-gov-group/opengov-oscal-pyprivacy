"""Tests for the validation layer."""

import pytest

from opengov_oscal_pycore.models import Catalog, Group, Control, OscalMetadata
from opengov_oscal_pycore.validation import (
    ValidationIssue,
    validate_catalog,
    validate_metadata,
    validate_unique_ids,
    validate_control,
)


def _make_metadata(**overrides):
    defaults = {"title": "Test Catalog", "version": "1.0", "oscal-version": "1.1.2"}
    defaults.update(overrides)
    return OscalMetadata.model_validate(defaults)


def _make_catalog(**overrides):
    defaults = {
        "uuid": "test-uuid",
        "metadata": _make_metadata(),
        "groups": [
            Group(id="g1", title="Group 1", controls=[
                Control(id="c1", title="Control 1"),
                Control(id="c2", title="Control 2"),
            ]),
        ],
    }
    defaults.update(overrides)
    return Catalog.model_validate(defaults)


class TestValidateMetadata:
    def test_valid_metadata_no_issues(self):
        m = _make_metadata()
        issues = validate_metadata(m)
        assert len(issues) == 0

    def test_empty_title_is_error(self):
        m = _make_metadata(title="  ")
        issues = validate_metadata(m)
        assert any(i.severity == "error" and "title" in i.path for i in issues)

    def test_missing_oscal_version_is_warning(self):
        m = OscalMetadata(title="T", version="1.0")
        issues = validate_metadata(m)
        assert any(i.severity == "warning" and "oscal-version" in i.path for i in issues)

    def test_missing_version_is_warning(self):
        m = OscalMetadata(title="T")
        issues = validate_metadata(m)
        assert any(i.severity == "warning" and "version" in i.path for i in issues)


class TestValidateControl:
    def test_control_with_title_no_issues(self):
        c = Control(id="c1", title="Some Title")
        assert len(validate_control(c)) == 0

    def test_control_without_title_is_warning(self):
        c = Control(id="c1")
        issues = validate_control(c)
        assert any(i.severity == "warning" and "title" in i.path for i in issues)


class TestValidateUniqueIds:
    def test_unique_ids_no_issues(self):
        cat = _make_catalog()
        assert len(validate_unique_ids(cat)) == 0

    def test_duplicate_control_id_is_error(self):
        cat = _make_catalog(groups=[
            Group(id="g1", title="G1", controls=[
                Control(id="dup", title="C1"),
            ]),
            Group(id="g2", title="G2", controls=[
                Control(id="dup", title="C2"),
            ]),
        ])
        issues = validate_unique_ids(cat)
        assert any(i.severity == "error" and "dup" in i.message for i in issues)

    def test_duplicate_group_id_is_error(self):
        cat = _make_catalog(groups=[
            Group(id="dup", title="G1"),
            Group(id="dup", title="G2"),
        ])
        issues = validate_unique_ids(cat)
        assert any(i.severity == "error" and "dup" in i.message for i in issues)


class TestValidateCatalog:
    def test_valid_catalog_no_issues(self):
        cat = _make_catalog()
        assert len(validate_catalog(cat)) == 0

    def test_combines_metadata_and_id_issues(self):
        cat = _make_catalog(
            metadata=OscalMetadata(title="T"),
            groups=[
                Group(id="g1", title="G1", controls=[
                    Control(id="dup", title="C1"),
                    Control(id="dup", title="C2"),
                ]),
            ],
        )
        issues = validate_catalog(cat)
        # Should have metadata warnings + duplicate ID error
        assert len(issues) >= 2
