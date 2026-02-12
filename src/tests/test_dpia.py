"""
Tests for the DPIA Catalog Converter (#29).

Covers:
- control_to_dpia_summary (minimal, from fixture, with group_id)
- control_to_dpia_detail (minimal, from fixture, serialization)
- group_to_dpia_summary
- group_to_dpia_detail (with and without controls)
- All DPIA controls convert without error
- Inheritance between summary and detail
- Alias field names
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opengov_oscal_pycore.models import Catalog, Control, Group

from opengov_oscal_pyprivacy.converters.dpia_converter import (
    control_to_dpia_summary,
    control_to_dpia_detail,
    group_to_dpia_summary,
    group_to_dpia_detail,
)
from opengov_oscal_pyprivacy.dto.dpia import (
    DpiaControlSummary,
    DpiaControlDetail,
    DpiaGroupSummary,
    DpiaGroupDetail,
)


# =====================================================================
# Fixtures
# =====================================================================

FIXTURE_FILE = Path(__file__).parent / "data" / "open_privacy_catalog_risk.json"


@pytest.fixture
def catalog() -> Catalog:
    """Load the full test catalog."""
    data = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
    return Catalog.model_validate(data)


@pytest.fixture
def dpia_group(catalog: Catalog) -> Group:
    """DPIA group from the fixture."""
    return catalog.groups[6]


@pytest.fixture
def dpia01(catalog: Catalog) -> Control:
    """DPIA-01 from the fixture."""
    return catalog.groups[6].controls[0]


@pytest.fixture
def empty_control() -> Control:
    """A fresh, empty control."""
    return Control(id="EMPTY-01", title="Empty Control")


# =====================================================================
# 1. test_control_to_dpia_summary_minimal
# =====================================================================

def test_control_to_dpia_summary_minimal(empty_control: Control):
    """An empty control produces a summary with defaults."""
    result = control_to_dpia_summary(empty_control)

    assert isinstance(result, DpiaControlSummary)
    assert result.id == "EMPTY-01"
    assert result.title == "Empty Control"
    assert result.group_id is None
    assert result.legal_articles == []
    assert result.evidence_artifacts == []
    assert result.maturity_domain is None
    assert result.maturity_requirement is None


# =====================================================================
# 2. test_control_to_dpia_summary_from_fixture
# =====================================================================

def test_control_to_dpia_summary_from_fixture(dpia01: Control):
    """DPIA-01 from the fixture populates summary fields."""
    result = control_to_dpia_summary(dpia01)

    assert result.id == "DPIA-01"
    assert result.title != ""
    assert len(result.legal_articles) >= 2
    assert "EU:REG:GDPR:ART-35" in result.legal_articles
    assert "EU:REG:GDPR:ART-36" in result.legal_articles
    assert len(result.evidence_artifacts) >= 2
    assert "dpia-report" in result.evidence_artifacts
    assert "risk-register" in result.evidence_artifacts
    assert result.maturity_domain == "risk-management"
    assert result.maturity_requirement == 3


# =====================================================================
# 3. test_control_to_dpia_summary_with_group_id
# =====================================================================

def test_control_to_dpia_summary_with_group_id(dpia01: Control):
    """group_id kwarg is passed through to the DTO."""
    result = control_to_dpia_summary(dpia01, group_id="DPIA")

    assert result.group_id == "DPIA"
    assert result.id == "DPIA-01"


# =====================================================================
# 4. test_control_to_dpia_detail_minimal
# =====================================================================

def test_control_to_dpia_detail_minimal(empty_control: Control):
    """An empty control produces a detail DTO with all defaults."""
    result = control_to_dpia_detail(empty_control)

    assert isinstance(result, DpiaControlDetail)
    assert result.id == "EMPTY-01"
    assert result.title == "Empty Control"
    assert result.group_id is None
    assert result.ctrl_class == ""
    assert result.legal_articles == []
    assert result.evidence_artifacts == []
    assert result.maturity_domain is None
    assert result.maturity_requirement is None
    assert result.dp_goals == []
    assert result.statement is None
    assert result.maturity_hints is None
    assert result.maturity_level_1 is None
    assert result.maturity_level_3 is None
    assert result.maturity_level_5 is None
    assert result.typical_measures == []
    assert result.assessment_questions == []
    assert result.measure_category is None


# =====================================================================
# 5. test_control_to_dpia_detail_from_fixture
# =====================================================================

def test_control_to_dpia_detail_from_fixture(dpia01: Control):
    """DPIA-01 from the fixture populates key detail fields."""
    result = control_to_dpia_detail(dpia01, group_id="DPIA")

    assert result.id == "DPIA-01"
    assert result.ctrl_class == "process"
    assert result.group_id == "DPIA"

    # Legal articles
    assert len(result.legal_articles) >= 2

    # Evidence artifacts
    assert len(result.evidence_artifacts) >= 2

    # Maturity domain and requirement
    assert result.maturity_domain == "risk-management"
    assert result.maturity_requirement == 3

    # DP goals
    assert len(result.dp_goals) > 0

    # Statement
    assert result.statement is not None
    assert len(result.statement) > 0

    # Maturity
    assert result.maturity_hints is not None
    assert result.maturity_level_1 is not None
    assert result.maturity_level_3 is not None
    assert result.maturity_level_5 is not None

    # Typical measures
    assert len(result.typical_measures) >= 3
    assert all(m.id != "" for m in result.typical_measures)
    assert all(m.prose != "" for m in result.typical_measures)

    # Measure category
    assert result.measure_category == "process"


# =====================================================================
# 6. test_control_to_dpia_detail_serialization
# =====================================================================

def test_control_to_dpia_detail_serialization(dpia01: Control):
    """model_dump produces a dict with aliased keys."""
    detail = control_to_dpia_detail(dpia01, group_id="DPIA")
    data = detail.model_dump(by_alias=True)

    assert isinstance(data, dict)
    # Aliased fields
    assert "ctrlClass" in data
    assert data["ctrlClass"] == "process"
    assert "groupId" in data
    assert data["groupId"] == "DPIA"
    assert "dsgvoArticles" in data
    assert "evidenceArtifacts" in data
    assert "maturityDomain" in data
    assert "maturityRequirement" in data
    assert "dpGoals" in data
    assert "maturityHints" in data
    assert "maturityLevel1" in data
    assert "maturityLevel3" in data
    assert "maturityLevel5" in data
    assert "typicalMeasures" in data
    assert "assessmentQuestions" in data
    assert "measureCategory" in data
    # Standard fields
    assert "id" in data
    assert data["id"] == "DPIA-01"


# =====================================================================
# 7. test_group_to_dpia_summary
# =====================================================================

def test_group_to_dpia_summary(dpia_group: Group):
    """Basic group summary conversion."""
    result = group_to_dpia_summary(dpia_group)

    assert isinstance(result, DpiaGroupSummary)
    assert result.id == "DPIA"
    assert result.title != ""
    assert result.control_count == 6


# =====================================================================
# 8. test_group_to_dpia_detail_with_controls
# =====================================================================

def test_group_to_dpia_detail_with_controls(dpia_group: Group):
    """Group detail includes controls by default."""
    result = group_to_dpia_detail(dpia_group)

    assert isinstance(result, DpiaGroupDetail)
    assert result.id == "DPIA"
    assert result.title != ""
    assert result.control_count == 6
    assert len(result.controls) == 6

    # Each control should be a DpiaControlSummary with group_id set
    for ctrl_summary in result.controls:
        assert isinstance(ctrl_summary, DpiaControlSummary)
        assert ctrl_summary.group_id == "DPIA"


# =====================================================================
# 9. test_group_to_dpia_detail_no_controls
# =====================================================================

def test_group_to_dpia_detail_no_controls(dpia_group: Group):
    """include_controls=False produces an empty controls list but correct count."""
    result = group_to_dpia_detail(dpia_group, include_controls=False)

    assert result.control_count == 6
    assert result.controls == []


# =====================================================================
# 10. test_all_dpia_controls_convert
# =====================================================================

def test_all_dpia_controls_convert(dpia_group: Group):
    """All 6 DPIA controls convert to both summary and detail without error."""
    assert len(dpia_group.controls) == 6
    for ctrl in dpia_group.controls:
        summary = control_to_dpia_summary(ctrl, group_id="DPIA")
        assert isinstance(summary, DpiaControlSummary)
        assert summary.id.startswith("DPIA-")

        detail = control_to_dpia_detail(ctrl, group_id="DPIA")
        assert isinstance(detail, DpiaControlDetail)
        assert detail.id.startswith("DPIA-")


# =====================================================================
# 11. test_dpia_detail_inherits_summary_fields
# =====================================================================

def test_dpia_detail_inherits_summary_fields(dpia01: Control):
    """DpiaControlDetail inherits all DpiaControlSummary fields."""
    summary = control_to_dpia_summary(dpia01, group_id="DPIA")
    detail = control_to_dpia_detail(dpia01, group_id="DPIA")

    # All summary fields must be present and equal in detail
    assert detail.id == summary.id
    assert detail.title == summary.title
    assert detail.group_id == summary.group_id
    assert detail.legal_articles == summary.legal_articles
    assert detail.evidence_artifacts == summary.evidence_artifacts
    assert detail.maturity_domain == summary.maturity_domain
    assert detail.maturity_requirement == summary.maturity_requirement

    # Detail is a subclass of Summary
    assert isinstance(detail, DpiaControlSummary)


# =====================================================================
# 12. test_dpia_summary_camel_case_aliases
# =====================================================================

def test_dpia_summary_camel_case_aliases(dpia01: Control):
    """Verify alias field names on DpiaControlSummary."""
    summary = control_to_dpia_summary(dpia01, group_id="DPIA")
    data = summary.model_dump(by_alias=True)

    # Aliased field names should be camelCase
    assert "groupId" in data
    assert "dsgvoArticles" in data
    assert "evidenceArtifacts" in data
    assert "maturityDomain" in data
    assert "maturityRequirement" in data

    # Non-aliased fields
    assert "id" in data
    assert "title" in data

    # Snake-case names should NOT be present when serialized by alias
    assert "group_id" not in data
    assert "legal_articles" not in data
    assert "evidence_artifacts" not in data
    assert "maturity_domain" not in data
    assert "maturity_requirement" not in data
