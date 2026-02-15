"""Tests for OSCAL JSON Schema validation (schema_validation module).

All tests use local mock schemas via the *schema_path* parameter so that
no network access is required.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from opengov_oscal_pycore.schema_validation import (
    validate_against_oscal_schema,
    SchemaValidationResult,
    SchemaValidationIssue,
    OSCAL_SCHEMA_FILES,
    _get_cache_dir,
    _load_schema,
)

# ---------------------------------------------------------------------------
# Mock schemas
# ---------------------------------------------------------------------------

MOCK_CATALOG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "mock-oscal-catalog-1.0.0",
    "type": "object",
    "required": ["catalog"],
    "properties": {
        "catalog": {
            "type": "object",
            "required": ["uuid", "metadata"],
            "properties": {
                "uuid": {"type": "string"},
                "metadata": {
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {"type": "string"},
                        "version": {"type": "string"},
                    },
                },
                "groups": {
                    "type": "array",
                    "items": {"type": "object"},
                },
                "controls": {
                    "type": "array",
                    "items": {"type": "object"},
                },
            },
        },
    },
}

MOCK_PROFILE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "mock-oscal-profile-1.0.0",
    "type": "object",
    "required": ["profile"],
    "properties": {
        "profile": {
            "type": "object",
            "required": ["uuid", "metadata", "imports"],
            "properties": {
                "uuid": {"type": "string"},
                "metadata": {
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {"type": "string"},
                    },
                },
                "imports": {
                    "type": "array",
                    "items": {"type": "object"},
                },
            },
        },
    },
}

MOCK_SSP_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "mock-oscal-ssp-1.0.0",
    "type": "object",
    "required": ["system-security-plan"],
    "properties": {
        "system-security-plan": {
            "type": "object",
            "required": ["uuid", "metadata"],
            "properties": {
                "uuid": {"type": "string"},
                "metadata": {
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {"type": "string"},
                    },
                },
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def catalog_schema_path(tmp_path: Path) -> Path:
    """Write the mock catalog schema to a temp file and return its path."""
    p = tmp_path / "mock_catalog_schema.json"
    p.write_text(json.dumps(MOCK_CATALOG_SCHEMA), encoding="utf-8")
    return p


@pytest.fixture()
def profile_schema_path(tmp_path: Path) -> Path:
    p = tmp_path / "mock_profile_schema.json"
    p.write_text(json.dumps(MOCK_PROFILE_SCHEMA), encoding="utf-8")
    return p


@pytest.fixture()
def ssp_schema_path(tmp_path: Path) -> Path:
    p = tmp_path / "mock_ssp_schema.json"
    p.write_text(json.dumps(MOCK_SSP_SCHEMA), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _valid_catalog_doc() -> dict:
    """Return a minimal valid catalog document (with root wrapper)."""
    return {
        "catalog": {
            "uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "metadata": {
                "title": "Test Catalog",
                "version": "1.0",
            },
            "groups": [],
        },
    }


# ---------------------------------------------------------------------------
# Tests -- valid documents
# ---------------------------------------------------------------------------

class TestValidCatalog:
    """A well-formed catalog document passes schema validation."""

    def test_valid_catalog(self, catalog_schema_path: Path):
        result = validate_against_oscal_schema(
            _valid_catalog_doc(), "catalog", schema_path=catalog_schema_path
        )
        assert result.valid is True
        assert result.issues == []
        assert result.schema_version == "mock-oscal-catalog-1.0.0"

    def test_valid_catalog_with_groups(self, catalog_schema_path: Path):
        doc = _valid_catalog_doc()
        doc["catalog"]["groups"] = [{"id": "g1", "title": "Group 1"}]
        result = validate_against_oscal_schema(
            doc, "catalog", schema_path=catalog_schema_path
        )
        assert result.valid is True


class TestValidProfile:
    """Minimal profile documents pass validation."""

    def test_valid_profile(self, profile_schema_path: Path):
        doc = {
            "profile": {
                "uuid": "11111111-2222-3333-4444-555555555555",
                "metadata": {"title": "Test Profile"},
                "imports": [{"href": "#catalog-uuid"}],
            },
        }
        result = validate_against_oscal_schema(
            doc, "profile", schema_path=profile_schema_path
        )
        assert result.valid is True
        assert result.schema_version == "mock-oscal-profile-1.0.0"


class TestValidSSP:
    """Minimal SSP documents pass validation."""

    def test_valid_ssp(self, ssp_schema_path: Path):
        doc = {
            "system-security-plan": {
                "uuid": "11111111-2222-3333-4444-555555555555",
                "metadata": {"title": "Test SSP"},
            },
        }
        result = validate_against_oscal_schema(
            doc, "system-security-plan", schema_path=ssp_schema_path
        )
        assert result.valid is True
        assert result.schema_version == "mock-oscal-ssp-1.0.0"


# ---------------------------------------------------------------------------
# Tests -- invalid documents
# ---------------------------------------------------------------------------

class TestInvalidCatalog:
    """Documents with missing or wrong-typed fields produce issues."""

    def test_missing_uuid(self, catalog_schema_path: Path):
        doc = _valid_catalog_doc()
        del doc["catalog"]["uuid"]
        result = validate_against_oscal_schema(
            doc, "catalog", schema_path=catalog_schema_path
        )
        assert result.valid is False
        assert len(result.issues) >= 1
        assert any("uuid" in issue.message for issue in result.issues)

    def test_missing_metadata(self, catalog_schema_path: Path):
        doc = _valid_catalog_doc()
        del doc["catalog"]["metadata"]
        result = validate_against_oscal_schema(
            doc, "catalog", schema_path=catalog_schema_path
        )
        assert result.valid is False
        assert any("metadata" in issue.message for issue in result.issues)

    def test_wrong_type_for_uuid(self, catalog_schema_path: Path):
        doc = _valid_catalog_doc()
        doc["catalog"]["uuid"] = 12345  # should be string
        result = validate_against_oscal_schema(
            doc, "catalog", schema_path=catalog_schema_path
        )
        assert result.valid is False
        assert any("type" in issue.schema_path for issue in result.issues)

    def test_wrong_type_for_groups(self, catalog_schema_path: Path):
        doc = _valid_catalog_doc()
        doc["catalog"]["groups"] = "not-an-array"
        result = validate_against_oscal_schema(
            doc, "catalog", schema_path=catalog_schema_path
        )
        assert result.valid is False

    def test_empty_document(self, catalog_schema_path: Path):
        result = validate_against_oscal_schema(
            {}, "catalog", schema_path=catalog_schema_path
        )
        assert result.valid is False
        assert len(result.issues) >= 1
        # Root-level "catalog" key is required
        assert any("catalog" in issue.message for issue in result.issues)

    def test_missing_metadata_title(self, catalog_schema_path: Path):
        doc = _valid_catalog_doc()
        del doc["catalog"]["metadata"]["title"]
        result = validate_against_oscal_schema(
            doc, "catalog", schema_path=catalog_schema_path
        )
        assert result.valid is False
        assert any("title" in issue.message for issue in result.issues)


class TestMultipleIssues:
    """A document with several problems reports all of them."""

    def test_multiple_issues(self, catalog_schema_path: Path):
        doc = {
            "catalog": {
                # missing uuid AND metadata
                "groups": "not-an-array",  # wrong type too
            },
        }
        result = validate_against_oscal_schema(
            doc, "catalog", schema_path=catalog_schema_path
        )
        assert result.valid is False
        assert len(result.issues) >= 3  # uuid, metadata, groups type


# ---------------------------------------------------------------------------
# Tests -- dataclass fields
# ---------------------------------------------------------------------------

class TestResultFields:
    """Verify that result and issue dataclass fields are populated."""

    def test_schema_validation_result_fields(self, catalog_schema_path: Path):
        result = validate_against_oscal_schema(
            _valid_catalog_doc(), "catalog", schema_path=catalog_schema_path
        )
        assert isinstance(result, SchemaValidationResult)
        assert isinstance(result.valid, bool)
        assert isinstance(result.issues, list)
        assert isinstance(result.schema_version, str)
        assert result.schema_version != ""

    def test_schema_validation_issue_fields(self, catalog_schema_path: Path):
        result = validate_against_oscal_schema(
            {}, "catalog", schema_path=catalog_schema_path
        )
        assert len(result.issues) >= 1
        issue = result.issues[0]
        assert isinstance(issue, SchemaValidationIssue)
        assert isinstance(issue.path, str)
        assert isinstance(issue.message, str)
        assert isinstance(issue.schema_path, str)
        # path should be "$" for root-level issues
        assert issue.path == "$"
        assert len(issue.message) > 0


# ---------------------------------------------------------------------------
# Tests -- schema file mapping
# ---------------------------------------------------------------------------

class TestSchemaFilesMapping:
    """The OSCAL_SCHEMA_FILES dict has entries for all four types."""

    def test_all_four_types_present(self):
        expected = {"catalog", "profile", "component-definition", "system-security-plan"}
        assert set(OSCAL_SCHEMA_FILES.keys()) == expected

    def test_all_values_are_json_filenames(self):
        for name in OSCAL_SCHEMA_FILES.values():
            assert name.endswith(".json"), f"{name} does not end with .json"


# ---------------------------------------------------------------------------
# Tests -- schema_path parameter and _load_schema
# ---------------------------------------------------------------------------

class TestSchemaPathParameter:
    """The schema_path parameter loads a schema from a local file."""

    def test_local_schema_path(self, tmp_path: Path):
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "custom-local-schema",
            "type": "object",
            "required": ["catalog"],
            "properties": {
                "catalog": {"type": "object"},
            },
        }
        schema_file = tmp_path / "custom_schema.json"
        schema_file.write_text(json.dumps(schema), encoding="utf-8")

        result = validate_against_oscal_schema(
            {"catalog": {}}, "catalog", schema_path=schema_file
        )
        assert result.valid is True
        assert result.schema_version == "custom-local-schema"

    def test_load_schema_from_path(self, tmp_path: Path):
        schema = {"$id": "test-schema", "type": "object"}
        schema_file = tmp_path / "test.json"
        schema_file.write_text(json.dumps(schema), encoding="utf-8")

        loaded = _load_schema("catalog", schema_path=schema_file)
        assert loaded["$id"] == "test-schema"


# ---------------------------------------------------------------------------
# Tests -- cache directory
# ---------------------------------------------------------------------------

class TestCacheDir:
    """_get_cache_dir creates and returns the expected path."""

    def test_cache_dir_exists(self):
        cache = _get_cache_dir()
        assert cache.exists()
        assert cache.is_dir()
        assert cache.name == "schemas"
        assert "opengov-oscal" in str(cache)


# ---------------------------------------------------------------------------
# Tests -- fixture-based catalog validation
# ---------------------------------------------------------------------------

class TestFixtureCatalog:
    """Validate the project's test fixture against the mock schema."""

    def test_fixture_catalog_valid(self, catalog_schema_path: Path):
        fixture = Path(__file__).parent / "data" / "open_privacy_catalog_risk.json"
        if not fixture.exists():
            pytest.skip("Fixture file not available")

        data = json.loads(fixture.read_text(encoding="utf-8"))
        result = validate_against_oscal_schema(
            data, "catalog", schema_path=catalog_schema_path
        )
        # The fixture has a "catalog" root with uuid and metadata.title
        assert result.valid is True
