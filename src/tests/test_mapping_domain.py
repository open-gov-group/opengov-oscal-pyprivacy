"""
Tests for the mapping domain module (Issue #43).

Covers CRUD operations, coverage calculation, and transitive mapping resolution.
"""

from __future__ import annotations

import json
import copy
from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Control, Group, Property
from opengov_oscal_pycore.crud_catalog import iter_controls

from opengov_oscal_pyprivacy.domain.mapping import (
    list_mappings,
    get_mapping,
    upsert_mapping,
    delete_mapping,
    calculate_mapping_coverage,
    resolve_transitive_mappings,
)
from opengov_oscal_pyprivacy.dto.mapping_workbench import (
    SdmSecurityMapping,
    SecurityControlRef,
    MappingStandards,
)
from opengov_oscal_pyprivacy.dto.mapping_coverage import (
    MappingCoverageResult,
    TransitiveMappingPath,
)


DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def mapping_data():
    """Load the test mapping fixture as a mutable list of dicts."""
    raw = (DATA_DIR / "test_mapping_data.json").read_text(encoding="utf-8")
    return json.loads(raw)


@pytest.fixture
def catalog():
    """Load the full privacy catalog from the test fixture."""
    raw = (DATA_DIR / "open_privacy_catalog_risk.json").read_text(encoding="utf-8")
    return Catalog.model_validate(json.loads(raw))


# ---------------------------------------------------------------------------
# list_mappings
# ---------------------------------------------------------------------------

def test_list_mappings(mapping_data):
    """Parse all mappings from fixture into typed DTOs."""
    result = list_mappings(mapping_data)
    assert len(result) == 5
    assert all(isinstance(m, SdmSecurityMapping) for m in result)
    assert result[0].sdm_control_id == "GOV-01"
    assert result[0].sdm_title == "Governance Framework"


# ---------------------------------------------------------------------------
# get_mapping
# ---------------------------------------------------------------------------

def test_get_mapping_found(mapping_data):
    """Find GOV-01 in the fixture."""
    m = get_mapping(mapping_data, "GOV-01")
    assert m is not None
    assert m.sdm_control_id == "GOV-01"
    assert m.sdm_title == "Governance Framework"
    assert len(m.security_controls) == 1
    assert m.security_controls[0].control_id == "A.5.1"
    assert m.notes == "Core governance control"


def test_get_mapping_not_found(mapping_data):
    """Returns None for unknown control ID."""
    result = get_mapping(mapping_data, "UNKNOWN-99")
    assert result is None


# ---------------------------------------------------------------------------
# upsert_mapping
# ---------------------------------------------------------------------------

def test_upsert_mapping_update(mapping_data):
    """Update existing GOV-01 mapping."""
    original_len = len(mapping_data)
    updated = SdmSecurityMapping(
        sdm_control_id="GOV-01",
        sdm_title="Updated Governance Framework",
        security_controls=[],
        standards=MappingStandards(bsi=["NEW.1"]),
        notes="Updated notes",
    )
    result = upsert_mapping(mapping_data, updated)
    assert result.sdm_title == "Updated Governance Framework"
    assert len(mapping_data) == original_len  # no new entry added

    # Verify the data was actually updated in the list
    found = get_mapping(mapping_data, "GOV-01")
    assert found is not None
    assert found.sdm_title == "Updated Governance Framework"
    assert found.standards.bsi == ["NEW.1"]


def test_upsert_mapping_insert(mapping_data):
    """Insert a new mapping that doesn't exist yet."""
    original_len = len(mapping_data)
    new_mapping = SdmSecurityMapping(
        sdm_control_id="NEW-01",
        sdm_title="Brand New Control",
        security_controls=[
            SecurityControlRef(catalog_id="bsi", control_id="OPS.2.1")
        ],
    )
    result = upsert_mapping(mapping_data, new_mapping)
    assert result.sdm_control_id == "NEW-01"
    assert len(mapping_data) == original_len + 1

    # Verify the data can be retrieved
    found = get_mapping(mapping_data, "NEW-01")
    assert found is not None
    assert found.sdm_title == "Brand New Control"


# ---------------------------------------------------------------------------
# delete_mapping
# ---------------------------------------------------------------------------

def test_delete_mapping(mapping_data):
    """Remove GOV-03 and verify it's gone."""
    original_len = len(mapping_data)
    delete_mapping(mapping_data, "GOV-03")
    assert len(mapping_data) == original_len - 1
    assert get_mapping(mapping_data, "GOV-03") is None


def test_delete_mapping_not_found(mapping_data):
    """No-op for unknown control ID."""
    original_len = len(mapping_data)
    delete_mapping(mapping_data, "UNKNOWN-99")
    assert len(mapping_data) == original_len


# ---------------------------------------------------------------------------
# calculate_mapping_coverage
# ---------------------------------------------------------------------------

def test_calculate_mapping_coverage_basic(catalog, mapping_data):
    """Coverage calculation with the fixture data against the real catalog.

    The fixture has GOV-01, GOV-02, GOV-03 as mapped (they have standards/security controls).
    GOV-04 is unmapped (all standards null, no security controls).
    A.5.1 is mapped but doesn't exist as a catalog control.
    So 3 out of 61 catalog controls are mapped.
    """
    result = calculate_mapping_coverage(catalog, mapping_data)
    assert isinstance(result, MappingCoverageResult)
    assert result.total_controls == 61
    assert result.mapped_controls == 3
    assert result.coverage_percent == round(3 / 61 * 100, 1)
    assert "GOV-04" in result.unmapped_control_ids
    # GOV-01, GOV-02, GOV-03 should NOT be in unmapped
    assert "GOV-01" not in result.unmapped_control_ids
    assert "GOV-02" not in result.unmapped_control_ids
    assert "GOV-03" not in result.unmapped_control_ids


def test_calculate_mapping_coverage_all_mapped(catalog):
    """All controls mapped -> 100% coverage."""
    all_ids = [c.id for c in iter_controls(catalog)]
    mapping_data = [
        {
            "sdmControlId": cid,
            "sdmTitle": f"Title for {cid}",
            "securityControls": [{"catalogId": "test", "controlId": "T.1"}],
            "standards": {"bsi": None, "iso27001": None, "iso27701": None},
        }
        for cid in all_ids
    ]
    result = calculate_mapping_coverage(catalog, mapping_data)
    assert result.total_controls == 61
    assert result.mapped_controls == 61
    assert result.coverage_percent == 100.0
    assert result.unmapped_control_ids == []


def test_calculate_mapping_coverage_none_mapped(catalog):
    """Empty mapping data -> 0% coverage."""
    result = calculate_mapping_coverage(catalog, [])
    assert result.total_controls == 61
    assert result.mapped_controls == 0
    assert result.coverage_percent == 0.0
    assert len(result.unmapped_control_ids) == 61


def test_calculate_mapping_coverage_per_group(catalog, mapping_data):
    """Verify per-group coverage percentages.

    GOV group has 6 controls, 3 are mapped (GOV-01, GOV-02, GOV-03).
    All other groups should be 0%.
    """
    result = calculate_mapping_coverage(catalog, mapping_data)
    assert "GOV" in result.per_group_coverage
    assert result.per_group_coverage["GOV"] == 50.0  # 3 out of 6
    # All other groups should be 0%
    for gid, pct in result.per_group_coverage.items():
        if gid != "GOV":
            assert pct == 0.0, f"Group {gid} should be 0%, got {pct}%"


# ---------------------------------------------------------------------------
# resolve_transitive_mappings
# ---------------------------------------------------------------------------

def test_resolve_transitive_mappings(mapping_data):
    """GOV-01 has security control ref to A.5.1. A.5.1 has standards bsi + iso27001."""
    paths = resolve_transitive_mappings(mapping_data, "GOV-01")
    assert len(paths) == 1
    path = paths[0]
    assert isinstance(path, TransitiveMappingPath)
    assert path.source_id == "GOV-01"
    assert path.path == ["GOV-01", "A.5.1"]
    # A.5.1 has bsi=["ORP.1"] and iso27001=["A.5.1"]
    assert "bsi:ORP.1" in path.target_standards
    assert "iso27001:A.5.1" in path.target_standards


def test_resolve_transitive_mappings_not_found(mapping_data):
    """Unknown source returns empty list."""
    paths = resolve_transitive_mappings(mapping_data, "UNKNOWN-99")
    assert paths == []


# ---------------------------------------------------------------------------
# DTO alias serialization
# ---------------------------------------------------------------------------

def test_mapping_coverage_result_aliases():
    """MappingCoverageResult serializes with camelCase aliases."""
    result = MappingCoverageResult(
        total_controls=10,
        mapped_controls=5,
        coverage_percent=50.0,
        unmapped_control_ids=["C-1", "C-2"],
        per_group_coverage={"G1": 100.0, "G2": 0.0},
    )
    data = result.model_dump(by_alias=True)
    assert "totalControls" in data
    assert "mappedControls" in data
    assert "coveragePercent" in data
    assert "unmappedControlIds" in data
    assert "perGroupCoverage" in data
    assert data["totalControls"] == 10
    assert data["mappedControls"] == 5
    assert data["coveragePercent"] == 50.0


def test_transitive_mapping_path_aliases():
    """TransitiveMappingPath serializes with camelCase aliases."""
    path = TransitiveMappingPath(
        source_id="SRC-01",
        path=["SRC-01", "TGT-01"],
        target_standards=["bsi:ORP.1"],
    )
    data = path.model_dump(by_alias=True)
    assert "sourceId" in data
    assert "targetStandards" in data
    assert data["sourceId"] == "SRC-01"
    assert data["path"] == ["SRC-01", "TGT-01"]
    assert data["targetStandards"] == ["bsi:ORP.1"]
